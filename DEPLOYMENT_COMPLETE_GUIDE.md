# 🚀 Complete Deployment Guide - Alpha LPGas with Custom Domains

## Overview
This guide will help you deploy both frontend and backend to Railway with custom domains:
- **Backend**: `api.alphalpgas.co.za`
- **Frontend**: `alphalpgas.co.za` and `www.alphalpgas.co.za`

---

## Part 1: Initial Railway Setup

### Step 1: Prepare Repository
```bash
# Make sure all changes are committed
git add .
git commit -m "Prepare for production deployment"
git push origin dev
```

### Step 2: Create Railway Project

1. Go to https://railway.app and sign in
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub
5. Select repository: `chiwarira/alpha-lpgas-new`
6. Railway will detect both Django and Next.js and create two services

---

## Part 2: Backend (Django) Setup

### Step 1: Add PostgreSQL Database

1. In your Railway project, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway will automatically create and link the database
4. The `DATABASE_URL` variable will be auto-provided

### Step 2: Configure Backend Environment Variables

Click on your **Django service** → **"Variables"** tab → Add these:

#### Required Variables:

```env
# Django Core
SECRET_KEY=django-insecure-GENERATE_NEW_KEY_HERE
DEBUG=False
ALLOWED_HOSTS=.railway.app,.up.railway.app,api.alphalpgas.co.za
RAILWAY_ENVIRONMENT=production

# CORS Settings (Update after frontend is deployed)
CORS_ALLOWED_ORIGINS=https://alphalpgas.co.za,https://www.alphalpgas.co.za
CORS_ALLOW_CREDENTIALS=True
CSRF_TRUSTED_ORIGINS=https://alphalpgas.co.za,https://www.alphalpgas.co.za,https://api.alphalpgas.co.za

# Site URLs
SITE_URL=https://api.alphalpgas.co.za
FRONTEND_URL=https://alphalpgas.co.za

# Static & Media
STATIC_URL=/static/
MEDIA_URL=/media/

# Wagtail
WAGTAIL_SITE_NAME=Alpha LPGas

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=info@alphalpgas.co.za
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=info@alphalpgas.co.za

# Yoco Payment (Get from https://portal.yoco.com)
YOCO_SECRET_KEY=sk_live_YOUR_SECRET_KEY
YOCO_PUBLIC_KEY=pk_live_YOUR_PUBLIC_KEY
YOCO_WEBHOOK_SECRET=your_webhook_secret
```

#### Generate SECRET_KEY:
Run this command locally:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Step 3: Configure Build Settings

1. Go to your Django service → **"Settings"** tab
2. Under **"Build"**, ensure:
   - **Root Directory**: `backend`
   - **Build Command**: (Railway auto-detects)
   - **Start Command**: `gunicorn alphalpgas.wsgi:application`

### Step 4: Deploy Backend

1. Railway will automatically deploy
2. Wait for build to complete (5-10 minutes)
3. Check **"Deploy Logs"** for any errors
4. Once deployed, note your Railway URL (e.g., `https://backend-production-xxxx.up.railway.app`)

---

## Part 3: Frontend (Next.js) Setup

### Step 1: Configure Frontend Environment Variables

Click on your **Next.js service** → **"Variables"** tab → Add these:

```env
# Backend API URL (use your Railway backend URL for now)
NEXT_PUBLIC_API_URL=https://api.alphalpgas.co.za

# Yoco Public Key
NEXT_PUBLIC_YOCO_PUBLIC_KEY=pk_live_YOUR_PUBLIC_KEY

# Company Information
NEXT_PUBLIC_COMPANY_NAME=Alpha LPGas
NEXT_PUBLIC_COMPANY_PHONE=074 454 5665
NEXT_PUBLIC_COMPANY_EMAIL=info@alphalpgas.co.za
NEXT_PUBLIC_COMPANY_ADDRESS=Sunnyacres Shopping Centre, Fish Hoek, Cape Town
```

### Step 2: Configure Build Settings

1. Go to your Next.js service → **"Settings"** tab
2. Under **"Build"**, ensure:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Start Command**: `npm start`

### Step 3: Deploy Frontend

1. Railway will automatically deploy
2. Wait for build to complete
3. Check **"Deploy Logs"** for any errors
4. Once deployed, note your Railway URL (e.g., `https://frontend-production-xxxx.up.railway.app`)

---

## Part 4: Custom Domain Setup

### Step 1: Backend Domain (api.alphalpgas.co.za)

#### In Railway:
1. Go to your **Django service**
2. Click **"Settings"** → **"Domains"**
3. Click **"Custom Domain"**
4. Enter: `api.alphalpgas.co.za`
5. Railway will provide CNAME records

#### In Your DNS Provider (e.g., Cloudflare, GoDaddy):
1. Log in to your domain registrar
2. Go to DNS settings for `alphalpgas.co.za`
3. Add a **CNAME record**:
   ```
   Type: CNAME
   Name: api
   Value: [Railway provides this, e.g., backend-production-xxxx.up.railway.app]
   TTL: Auto or 3600
   ```
4. Save the record
5. Wait 5-30 minutes for DNS propagation

#### Update Backend Environment Variables:
Go back to Django service → Variables → Update:
```env
ALLOWED_HOSTS=.railway.app,.up.railway.app,api.alphalpgas.co.za
SITE_URL=https://api.alphalpgas.co.za
```

### Step 2: Frontend Domain (alphalpgas.co.za)

#### In Railway:
1. Go to your **Next.js service**
2. Click **"Settings"** → **"Domains"**
3. Click **"Custom Domain"**
4. Enter: `alphalpgas.co.za`
5. Railway will provide DNS records

#### In Your DNS Provider:
1. Add an **A record** or **CNAME** (Railway will specify):
   ```
   Type: A or CNAME
   Name: @ (root domain)
   Value: [Railway provides this]
   TTL: Auto or 3600
   ```

2. Add **www subdomain**:
   ```
   Type: CNAME
   Name: www
   Value: alphalpgas.co.za (or Railway's value)
   TTL: Auto or 3600
   ```

#### Update Frontend Environment Variables:
Go to Next.js service → Variables → Update:
```env
NEXT_PUBLIC_API_URL=https://api.alphalpgas.co.za
```

#### Update Backend CORS:
Go to Django service → Variables → Update:
```env
CORS_ALLOWED_ORIGINS=https://alphalpgas.co.za,https://www.alphalpgas.co.za
CSRF_TRUSTED_ORIGINS=https://alphalpgas.co.za,https://www.alphalpgas.co.za,https://api.alphalpgas.co.za
FRONTEND_URL=https://alphalpgas.co.za
```

---

## Part 5: Post-Deployment Setup

### Step 1: Create Superuser

Install Railway CLI:
```bash
npm install -g @railway/cli
```

Login and link to project:
```bash
railway login
railway link
```

Create superuser:
```bash
# Select your Django service when prompted
railway run python manage.py createsuperuser
```

Enter:
- Username: `admin`
- Email: `info@alphalpgas.co.za`
- Password: (choose a strong password)

### Step 2: Run Migrations

```bash
railway run python manage.py migrate
```

### Step 3: Collect Static Files

```bash
railway run python manage.py collectstatic --noinput
```

### Step 4: Configure Wagtail Site

1. Go to `https://api.alphalpgas.co.za/cms/`
2. Login with superuser credentials
3. Go to **Settings** → **Sites**
4. Edit the default site:
   - Hostname: `alphalpgas.co.za`
   - Port: `443`
   - Site name: `Alpha LPGas`
5. Save

### Step 5: Add Initial Data

1. Go to `https://api.alphalpgas.co.za/admin/`
2. Add:
   - **Company Settings** (Systems section)
   - **Delivery Zones**
   - **Products** with images
   - **Categories**
   - **Promo Codes** (optional)

---

## Part 6: Testing

### Test Backend:
```bash
# Health check
curl https://api.alphalpgas.co.za/api/accounting/products/

# Admin panel
https://api.alphalpgas.co.za/admin/

# CMS
https://api.alphalpgas.co.za/cms/
```

### Test Frontend:
1. Visit `https://alphalpgas.co.za`
2. Check if products load
3. Test add to cart
4. Test checkout flow
5. Verify payment gateway (use test mode first)

### Test Custom Domains:
- ✅ `https://alphalpgas.co.za` - Frontend
- ✅ `https://www.alphalpgas.co.za` - Frontend (www)
- ✅ `https://api.alphalpgas.co.za` - Backend API

---

## Part 7: SSL Certificates

Railway automatically provides SSL certificates for custom domains. You should see:
- 🔒 HTTPS enabled automatically
- Valid SSL certificate
- No security warnings

If SSL is not working:
1. Wait 10-15 minutes after DNS propagation
2. Check DNS records are correct
3. Contact Railway support if issues persist

---

## Part 8: Monitoring & Maintenance

### View Logs:
```bash
# Backend logs
railway logs --service backend

# Frontend logs
railway logs --service frontend
```

### Database Backup:
1. Go to Railway → PostgreSQL service
2. Click **"Data"** tab
3. Use **"Backup"** feature or export data

### Update Deployment:
```bash
# Make changes locally
git add .
git commit -m "Update feature"
git push origin dev

# Railway auto-deploys on push
```

---

## Troubleshooting

### CORS Errors:
- Verify `CORS_ALLOWED_ORIGINS` includes your frontend domain
- Check `CSRF_TRUSTED_ORIGINS` includes all domains
- Clear browser cache

### Database Connection Issues:
- Railway auto-provides `DATABASE_URL`
- Check PostgreSQL service is running
- Verify migrations ran successfully

### Static Files Not Loading:
- Run `collectstatic` command
- Check `STATIC_URL` and `STATIC_ROOT` in settings
- Verify Whitenoise is installed

### Domain Not Working:
- Check DNS propagation: https://dnschecker.org
- Verify CNAME/A records are correct
- Wait up to 48 hours for full propagation
- Check Railway domain settings

### Payment Gateway Issues:
- Use test keys first: `pk_test_...` and `sk_test_...`
- Switch to live keys after testing
- Verify webhook URL in Yoco portal

---

## Security Checklist

- ✅ `DEBUG=False` in production
- ✅ Strong `SECRET_KEY` generated
- ✅ HTTPS enabled (SSL certificates)
- ✅ CORS properly configured
- ✅ Database credentials secure
- ✅ Email credentials secure
- ✅ Yoco keys secure (use live keys)
- ✅ Admin panel has strong password
- ✅ Regular backups configured

---

## Cost Estimate

**Railway Pricing:**
- Backend Service: ~$5-10/month
- Frontend Service: ~$5/month
- PostgreSQL Database: ~$5/month
- **Total: ~$15-20/month**

**Domain:**
- Domain registration: ~$10-15/year (from registrar)

---

## Support Resources

- **Railway Docs**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway
- **Django Docs**: https://docs.djangoproject.com
- **Next.js Docs**: https://nextjs.org/docs

---

## Quick Reference

### Important URLs:
- **Frontend**: https://alphalpgas.co.za
- **Backend API**: https://api.alphalpgas.co.za
- **Admin Panel**: https://api.alphalpgas.co.za/admin/
- **CMS**: https://api.alphalpgas.co.za/cms/
- **Railway Dashboard**: https://railway.app/dashboard

### Important Commands:
```bash
# Deploy
git push origin dev

# View logs
railway logs

# Run Django commands
railway run python manage.py [command]

# Create superuser
railway run python manage.py createsuperuser

# Run migrations
railway run python manage.py migrate
```

---

**Your Alpha LPGas system is now live with custom domains! 🎉**

Need help? Check Railway logs or contact support.
