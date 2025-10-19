# Alpha LPGas - Production Deployment Guide

Complete guide for deploying Alpha LPGas to DigitalOcean.

## Overview

This guide covers:
- DigitalOcean Droplet setup
- PostgreSQL database configuration
- Django backend deployment
- Next.js frontend deployment
- Nginx configuration
- SSL certificate setup
- Domain configuration

## Prerequisites

- DigitalOcean account
- Domain name (e.g., alphalpgas.co.za)
- SSH key configured
- Production credentials (YOCO, Google OAuth)

## Architecture

```
┌─────────────────┐
│   CloudFlare    │  (Optional CDN/DNS)
└────────┬────────┘
         │
┌────────▼────────┐
│     Nginx       │  (Reverse Proxy + SSL)
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼──────┐
│Django │ │ Next.js │
│+Gunic.│ │         │
└───┬───┘ └─────────┘
    │
┌───▼────────────┐
│  PostgreSQL    │  (Managed Database)
│  + Redis       │
└────────────────┘
```

## Step 1: Create DigitalOcean Resources

### 1.1 Create Managed PostgreSQL Database

1. Log in to DigitalOcean
2. Create > Databases > PostgreSQL
3. Choose plan: Basic ($15/month minimum)
4. Region: Choose closest to users
5. Database name: `alphalpgas`
6. Note connection details

### 1.2 Create Droplet

1. Create > Droplets
2. Choose image: Ubuntu 22.04 LTS
3. Plan: Basic ($12/month, 2GB RAM minimum)
4. Add SSH key
5. Hostname: `alphalpgas-prod`
6. Create Droplet
7. Note IP address

### 1.3 Configure Firewall

1. Networking > Firewalls > Create Firewall
2. Inbound Rules:
   - SSH (22) from your IP
   - HTTP (80) from all
   - HTTPS (443) from all
3. Apply to droplet

## Step 2: Initial Server Setup

### 2.1 Connect to Server

```bash
ssh root@your-droplet-ip
```

### 2.2 Create Non-Root User

```bash
adduser alphalpgas
usermod -aG sudo alphalpgas
su - alphalpgas
```

### 2.3 Update System

```bash
sudo apt update
sudo apt upgrade -y
```

### 2.4 Install Dependencies

```bash
# Python and tools
sudo apt install -y python3-pip python3-venv python3-dev

# PostgreSQL client
sudo apt install -y postgresql-client libpq-dev

# Nginx
sudo apt install -y nginx

# Redis
sudo apt install -y redis-server

# Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Git
sudo apt install -y git

# Supervisor (for process management)
sudo apt install -y supervisor

# Certbot (for SSL)
sudo apt install -y certbot python3-certbot-nginx
```

## Step 3: Deploy Backend

### 3.1 Clone Repository

```bash
cd /home/alphalpgas
git clone <your-repository-url> app
cd app/backend
```

### 3.2 Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3.3 Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

### 3.4 Configure Environment

```bash
nano .env
```

Add production settings:

```env
SECRET_KEY=<generate-new-secret-key>
DEBUG=False
ALLOWED_HOSTS=alphalpgas.co.za,www.alphalpgas.co.za,your-droplet-ip

DATABASE_URL=postgresql://user:password@db-host:25060/alphalpgas?sslmode=require
# Use connection string from DigitalOcean database

CORS_ALLOWED_ORIGINS=https://alphalpgas.co.za,https://www.alphalpgas.co.za

GOOGLE_CLIENT_ID=your-production-google-client-id
GOOGLE_CLIENT_SECRET=your-production-google-secret

YOCO_SECRET_KEY=your-production-yoco-secret
YOCO_PUBLIC_KEY=your-production-yoco-public

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=info@alphalpgas.co.za
EMAIL_HOST_PASSWORD=your-app-password

CELERY_BROKER_URL=redis://localhost:6379/0
SITE_URL=https://alphalpgas.co.za
FRONTEND_URL=https://alphalpgas.co.za
```

### 3.5 Run Migrations

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 3.6 Test Gunicorn

```bash
gunicorn alphalpgas.wsgi:application --bind 0.0.0.0:8000
# Press Ctrl+C to stop
```

### 3.7 Create Gunicorn Service

```bash
sudo nano /etc/supervisor/conf.d/gunicorn.conf
```

Add:

```ini
[program:gunicorn]
directory=/home/alphalpgas/app/backend
command=/home/alphalpgas/app/backend/venv/bin/gunicorn alphalpgas.wsgi:application --bind 127.0.0.1:8000 --workers 3
user=alphalpgas
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/alphalpgas/app/backend/logs/gunicorn.log
```

Create log directory:

```bash
mkdir -p /home/alphalpgas/app/backend/logs
```

### 3.8 Create Celery Service

```bash
sudo nano /etc/supervisor/conf.d/celery.conf
```

Add:

```ini
[program:celery]
directory=/home/alphalpgas/app/backend
command=/home/alphalpgas/app/backend/venv/bin/celery -A alphalpgas worker -l info
user=alphalpgas
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/alphalpgas/app/backend/logs/celery.log
```

### 3.9 Start Services

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status
```

## Step 4: Deploy Frontend

### 4.1 Build Frontend

```bash
cd /home/alphalpgas/app/frontend

# Create production .env
nano .env.production
```

Add:

```env
NEXT_PUBLIC_API_URL=https://alphalpgas.co.za/api
NEXT_PUBLIC_SITE_URL=https://alphalpgas.co.za
NEXT_PUBLIC_YOCO_PUBLIC_KEY=your-production-yoco-public
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-production-google-client-id
```

Build:

```bash
npm install
npm run build
```

### 4.2 Create Next.js Service

```bash
sudo nano /etc/supervisor/conf.d/nextjs.conf
```

Add:

```ini
[program:nextjs]
directory=/home/alphalpgas/app/frontend
command=/usr/bin/npm start
user=alphalpgas
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/alphalpgas/app/frontend/logs/nextjs.log
environment=NODE_ENV="production",PORT="3000"
```

Create log directory and start:

```bash
mkdir -p /home/alphalpgas/app/frontend/logs
sudo supervisorctl reread
sudo supervisorctl update
```

## Step 5: Configure Nginx

### 5.1 Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/alphalpgas
```

Add:

```nginx
# Redirect www to non-www
server {
    listen 80;
    server_name www.alphalpgas.co.za;
    return 301 $scheme://alphalpgas.co.za$request_uri;
}

# Main server block
server {
    listen 80;
    server_name alphalpgas.co.za;

    client_max_body_size 20M;

    # Frontend (Next.js)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Django Admin
    location /admin {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Wagtail CMS
    location /cms {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static {
        alias /home/alphalpgas/app/backend/staticfiles;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media {
        alias /home/alphalpgas/app/backend/media;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

### 5.2 Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/alphalpgas /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Step 6: Configure Domain

### 6.1 Add DNS Records

In your domain registrar (or CloudFlare):

1. A Record: `@` → `your-droplet-ip`
2. A Record: `www` → `your-droplet-ip`

Wait for DNS propagation (up to 48 hours, usually minutes).

### 6.2 Verify DNS

```bash
dig alphalpgas.co.za
ping alphalpgas.co.za
```

## Step 7: Setup SSL Certificate

### 7.1 Obtain Certificate

```bash
sudo certbot --nginx -d alphalpgas.co.za -d www.alphalpgas.co.za
```

Follow prompts:
- Enter email
- Agree to terms
- Choose redirect HTTP to HTTPS (option 2)

### 7.2 Test Auto-Renewal

```bash
sudo certbot renew --dry-run
```

### 7.3 Setup Auto-Renewal Cron

```bash
sudo crontab -e
```

Add:

```
0 0 * * * certbot renew --quiet
```

## Step 8: Configure Backups

### 8.1 Database Backups

Create backup script:

```bash
nano /home/alphalpgas/backup-db.sh
```

Add:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/alphalpgas/backups"
mkdir -p $BACKUP_DIR

# Backup database (use DigitalOcean connection string)
PGPASSWORD=your-password pg_dump -h db-host -U user -d alphalpgas > $BACKUP_DIR/db_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -name "db_*.sql" -mtime +7 -delete
```

Make executable:

```bash
chmod +x /home/alphalpgas/backup-db.sh
```

Add to crontab:

```bash
crontab -e
# Add: 0 2 * * * /home/alphalpgas/backup-db.sh
```

### 8.2 DigitalOcean Snapshots

1. Enable weekly droplet snapshots in DigitalOcean
2. Enable automated database backups

## Step 9: Monitoring and Logging

### 9.1 Setup Log Rotation

```bash
sudo nano /etc/logrotate.d/alphalpgas
```

Add:

```
/home/alphalpgas/app/backend/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 alphalpgas alphalpgas
    sharedscripts
}
```

### 9.2 Monitor Services

```bash
# Check all services
sudo supervisorctl status

# Check Nginx
sudo systemctl status nginx

# Check logs
tail -f /home/alphalpgas/app/backend/logs/gunicorn.log
tail -f /home/alphalpgas/app/frontend/logs/nextjs.log
tail -f /var/log/nginx/error.log
```

## Step 10: Post-Deployment

### 10.1 Update Google OAuth

1. Go to Google Cloud Console
2. Add production URLs to authorized origins and redirects:
   - https://alphalpgas.co.za
   - https://alphalpgas.co.za/auth/callback

### 10.2 Update YOCO Webhooks

1. Log in to YOCO Portal
2. Update webhook URL to: https://alphalpgas.co.za/api/shop/yoco-webhook/

### 10.3 Test Everything

- [ ] Website loads
- [ ] SSL certificate works
- [ ] User registration
- [ ] Login (email + Google)
- [ ] Browse products
- [ ] Place order
- [ ] YOCO payment
- [ ] Admin access
- [ ] CMS access

## Deployment Checklist

- [ ] Droplet created and configured
- [ ] PostgreSQL database created
- [ ] Backend deployed and running
- [ ] Frontend built and running
- [ ] Nginx configured
- [ ] DNS records added
- [ ] SSL certificate installed
- [ ] Google OAuth configured
- [ ] YOCO webhooks configured
- [ ] Backups configured
- [ ] Monitoring setup
- [ ] All tests passing

## Updating the Application

```bash
# SSH into server
ssh alphalpgas@your-droplet-ip

# Pull latest code
cd /home/alphalpgas/app
git pull origin main

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput

# Update frontend
cd ../frontend
npm install
npm run build

# Restart services
sudo supervisorctl restart gunicorn
sudo supervisorctl restart celery
sudo supervisorctl restart nextjs
```

## Troubleshooting

### 502 Bad Gateway

- Check if Gunicorn is running: `sudo supervisorctl status gunicorn`
- Check logs: `tail -f /home/alphalpgas/app/backend/logs/gunicorn.log`
- Restart: `sudo supervisorctl restart gunicorn`

### Database Connection Error

- Verify DATABASE_URL in .env
- Check database is accessible: `psql "your-connection-string"`
- Check firewall rules in DigitalOcean

### SSL Certificate Issues

- Verify DNS is pointing to droplet
- Check Nginx configuration: `sudo nginx -t`
- Renew certificate: `sudo certbot renew`

## Cost Estimate

- Droplet (2GB): $12/month
- PostgreSQL (Basic): $15/month
- Domain: ~$10/year
- **Total: ~$27/month + domain**

## Support

For deployment issues:
- Email: info@alphalpgas.co.za
- Phone: 074 454 5665
