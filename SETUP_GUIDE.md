# Alpha LPGas - Complete Setup Guide

This guide will walk you through setting up the Alpha LPGas platform from scratch.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Configuration](#configuration)
4. [Database Setup](#database-setup)
5. [Running the Application](#running-the-application)
6. [Initial Data](#initial-data)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software
- **Python 3.8+**: [Download](https://www.python.org/downloads/)
- **Node.js 16+**: [Download](https://nodejs.org/)
- **PostgreSQL 12+**: [Download](https://www.postgresql.org/download/)
- **Redis**: [Download](https://redis.io/download) (for Celery tasks)
- **Git**: [Download](https://git-scm.com/downloads)

### Accounts Needed
- **Google Cloud Console**: For OAuth (https://console.cloud.google.com/)
- **YOCO Account**: For payment processing (https://www.yoco.com/)
- **DigitalOcean Account**: For production hosting (https://www.digitalocean.com/)

## Local Development Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd alpha-lpgas-new
```

### 2. Backend Setup

#### Create Virtual Environment

```bash
cd backend
python -m venv venv
```

#### Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

#### Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

## Configuration

### Backend Configuration

#### 1. Create Environment File

```bash
cd backend
copy .env.example .env  # Windows
# or
cp .env.example .env    # macOS/Linux
```

#### 2. Edit .env File

Open `.env` and configure:

```env
# Django Settings
SECRET_KEY=your-secret-key-generate-new-one
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL)
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/alphalpgas
DB_NAME=alphalpgas
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# JWT Settings
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# YOCO Payment Gateway
YOCO_SECRET_KEY=your-yoco-secret-key
YOCO_PUBLIC_KEY=your-yoco-public-key
YOCO_WEBHOOK_SECRET=your-yoco-webhook-secret

# Email Settings
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=info@alphalpgas.co.za
EMAIL_HOST_PASSWORD=your-email-app-password
DEFAULT_FROM_EMAIL=info@alphalpgas.co.za

# Celery/Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Site URLs
SITE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

#### 3. Generate Secret Key

```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Frontend Configuration

#### 1. Create Environment File

```bash
cd frontend
copy .env.example .env.local  # Windows
# or
cp .env.example .env.local    # macOS/Linux
```

#### 2. Edit .env.local File

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_SITE_URL=http://localhost:3000
NEXT_PUBLIC_YOCO_PUBLIC_KEY=your-yoco-public-key
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id
```

## Database Setup

### 1. Install PostgreSQL

Download and install PostgreSQL from https://www.postgresql.org/download/

### 2. Create Database

**Using psql:**
```bash
psql -U postgres
CREATE DATABASE alphalpgas;
\q
```

**Using pgAdmin:**
- Open pgAdmin
- Right-click on Databases
- Create > Database
- Name: alphalpgas

### 3. Run Migrations

```bash
cd backend
python manage.py migrate
```

### 4. Create Superuser

```bash
python manage.py createsuperuser
```

Follow prompts to create admin account.

## Google OAuth Setup

### 1. Create Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Create a new project or select existing
3. Enable Google+ API

### 2. Create OAuth Credentials

1. Go to Credentials
2. Create Credentials > OAuth client ID
3. Application type: Web application
4. Authorized JavaScript origins:
   - http://localhost:3000
   - http://localhost:8000
5. Authorized redirect URIs:
   - http://localhost:3000/auth/callback
   - http://localhost:8000/accounts/google/login/callback/
6. Save Client ID and Client Secret

### 3. Configure in Django Admin

1. Start backend server: `python manage.py runserver`
2. Go to http://localhost:8000/admin/
3. Navigate to Sites > Sites
4. Edit example.com to localhost:3000
5. Navigate to Social applications > Add
6. Provider: Google
7. Name: Google OAuth
8. Client ID: (paste from Google Console)
9. Secret key: (paste from Google Console)
10. Sites: Add localhost:3000
11. Save

## YOCO Payment Setup

### 1. Create YOCO Account

1. Go to https://www.yoco.com/
2. Sign up for business account
3. Complete verification

### 2. Get API Keys

1. Log in to YOCO Portal
2. Go to Settings > API Keys
3. Copy Public Key and Secret Key
4. Add to .env files (backend and frontend)

### 3. Setup Webhooks (Production)

1. In YOCO Portal, go to Webhooks
2. Add webhook URL: https://yourdomain.com/api/shop/yoco-webhook/
3. Select events: payment.succeeded, payment.failed
4. Copy webhook secret to .env

## Running the Application

### 1. Start Redis (for Celery)

**Windows:**
```bash
# Download Redis for Windows from https://github.com/microsoftarchive/redis/releases
redis-server
```

**macOS:**
```bash
brew services start redis
```

**Linux:**
```bash
sudo service redis-server start
```

### 2. Start Backend

```bash
cd backend
# Activate venv if not already activated
python manage.py runserver
```

Backend will run on http://localhost:8000

### 3. Start Celery Worker (Optional - for async tasks)

Open new terminal:
```bash
cd backend
# Activate venv
celery -A alphalpgas worker -l info
```

### 4. Start Frontend

Open new terminal:
```bash
cd frontend
npm run dev
```

Frontend will run on http://localhost:3000

## Initial Data

### 1. Create Company Settings

1. Go to http://localhost:8000/admin/
2. Navigate to Core > Company Settings
3. Click on "Alpha LPGas Settings"
4. Update company information
5. Save

### 2. Create Product Categories

1. In admin, go to Shop > Categories
2. Add categories:
   - Gas Cylinders
   - Accessories
   - Regulators

### 3. Create Products

1. Go to Shop > Shop Products
2. Add products:
   - 5kg Gas Exchange (R200)
   - 9kg Gas Exchange (R340)
   - 14kg Gas Exchange (R540)
   - 19kg Gas Exchange (R730)
   - 48kg Gas Exchange (R1830)
   - Bull Nose Regulator (R150)
   - Gas Hose per metre (R30)

### 4. Create Delivery Zones

1. Go to Shop > Delivery Zones
2. Add zones:
   - Fish Hoek (Free delivery over R500)
   - Southern Suburbs (R50 delivery)
   - Cape Town CBD (R80 delivery)

### 5. Create CMS Pages

1. Go to http://localhost:8000/cms/
2. Create Home Page
3. Add content sections
4. Publish

## Testing

### Backend Tests

```bash
cd backend
python manage.py test
```

### Frontend Tests

```bash
cd frontend
npm test
```

### Manual Testing Checklist

- [ ] User registration works
- [ ] Login with email/password works
- [ ] Google OAuth login works
- [ ] Browse products
- [ ] Add products to cart
- [ ] Checkout process
- [ ] YOCO payment (use test card)
- [ ] Order confirmation
- [ ] View order history
- [ ] Admin dashboard access
- [ ] Create invoice
- [ ] Record payment
- [ ] Generate client statement

## Troubleshooting

### Database Connection Error

**Error:** `could not connect to server`

**Solution:**
- Ensure PostgreSQL is running
- Check DATABASE_URL in .env
- Verify database exists: `psql -U postgres -l`

### Port Already in Use

**Error:** `Port 8000 is already in use`

**Solution:**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:8000 | xargs kill -9
```

### Module Not Found Error

**Error:** `ModuleNotFoundError: No module named 'xxx'`

**Solution:**
```bash
# Ensure venv is activated
pip install -r requirements.txt
```

### CORS Error in Frontend

**Error:** `Access to XMLHttpRequest blocked by CORS policy`

**Solution:**
- Check CORS_ALLOWED_ORIGINS in backend .env
- Ensure frontend URL is included
- Restart backend server

### Google OAuth Not Working

**Solution:**
- Verify Client ID and Secret in Django admin
- Check redirect URIs in Google Console
- Ensure Site domain is correct in Django admin

### YOCO Payment Fails

**Solution:**
- Use test card: 4242 4242 4242 4242
- Verify YOCO keys are correct
- Check browser console for errors
- Ensure YOCO script is loaded

## Next Steps

1. **Customize Design**: Update colors, fonts, and branding
2. **Add Content**: Create blog posts, about page, FAQs
3. **Configure Email**: Setup SMTP for order notifications
4. **Setup Analytics**: Add Google Analytics
5. **Prepare for Production**: See DEPLOYMENT_GUIDE.md

## Support

For issues or questions:
- Email: info@alphalpgas.co.za
- Phone: 074 454 5665

## Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Wagtail CMS Documentation](https://docs.wagtail.org/)
- [YOCO API Documentation](https://developer.yoco.com/)
