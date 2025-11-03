# Production Environment Setup Guide

## Overview
This guide will help you set up a separate production environment while keeping the current setup as dev/staging.

## Current Setup (Dev/Staging)
- **Branch**: `dev`
- **Frontend**: https://front-end-production-b210.up.railway.app
- **Backend**: https://alpha-lpgas-new-production.up.railway.app
- **Database**: Railway PostgreSQL (staging)
- **Yoco Keys**: Test keys

## Production Setup Steps

### 1. Create Production Environment in Railway

Railway's environment feature allows you to create separate environments (dev/staging/production) within the same project, which is much cleaner than creating separate projects.

#### Benefits of Using Environments:
- ✅ **Single Project**: All environments in one place
- ✅ **Easy Switching**: Toggle between environments with dropdown
- ✅ **Shared Configuration**: Copy settings from existing environment
- ✅ **Isolated Resources**: Each environment has its own database and services
- ✅ **Cost Effective**: Better resource management
- ✅ **Simpler Management**: No need to duplicate project setup

#### Steps:
1. Go to your existing Railway project
2. Click on **"Settings"** (or the project name at the top)
3. Go to **"Environments"** tab
4. Click **"New Environment"**
5. Name it: **"production"**
6. Select **"Copy from existing environment"**
7. Choose your current environment (staging/dev)
8. Click **"Create"**

This will:
- ✅ Copy all services (backend, frontend, database)
- ✅ Copy all environment variables
- ✅ Create a new isolated database
- ✅ Keep the same project structure

### 2. Configure Production Environment

#### Switch to Production Environment:
1. In Railway, use the environment dropdown (top left)
2. Select **"production"**

#### Update Backend Service:

##### Change Branch to Main:
1. Click on **backend service**
2. Go to **"Settings"** → **"Source"**
3. Change branch from `dev` to `main`
4. Click **"Update"**

##### Update Backend Environment Variables:

```bash
# Django Core
SECRET_KEY=<generate-new-secret-key>
DEBUG=False
ALLOWED_HOSTS=.railway.app,.up.railway.app,alphalpgas.co.za,www.alphalpgas.co.za
RAILWAY_ENVIRONMENT=production

# CORS (update after frontend is deployed)
CORS_ALLOWED_ORIGINS=https://your-production-frontend.up.railway.app,https://alphalpgas.co.za,https://www.alphalpgas.co.za
CORS_ALLOW_CREDENTIALS=True

# Static & Media
STATIC_URL=/static/
MEDIA_URL=/media/

# Site URLs (update after deployment)
SITE_URL=https://api.alphalpgas.co.za
FRONTEND_URL=https://alphalpgas.co.za

# Wagtail
WAGTAIL_SITE_NAME=Alpha LPGas

# Email (Gmail)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=info@alphalpgas.co.za
EMAIL_HOST_PASSWORD=<your-gmail-app-password>
DEFAULT_FROM_EMAIL=info@alphalpgas.co.za

# Yoco Payment (LIVE KEYS)
YOCO_SECRET_KEY=sk_live_<your-live-secret-key>
YOCO_PUBLIC_KEY=pk_live_<your-live-public-key>
YOCO_WEBHOOK_SECRET=<your-webhook-secret>

# Cloudinary (if using)
CLOUDINARY_CLOUD_NAME=<your-cloud-name>
CLOUDINARY_API_KEY=<your-api-key>
CLOUDINARY_API_SECRET=<your-api-secret>
```

#### Generate New SECRET_KEY:
Run locally:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. Update Frontend Service

#### Change Branch to Main:
1. Click on **frontend service**
2. Go to **"Settings"** → **"Source"**
3. Change branch from `dev` to `main`
4. Click **"Update"**

#### Update Frontend Environment Variables:

```bash
# API URL (your production backend URL)
NEXT_PUBLIC_API_URL=https://your-backend-production.up.railway.app

# Yoco Public Key (LIVE KEY)
NEXT_PUBLIC_YOCO_PUBLIC_KEY=pk_live_<your-live-public-key>

# Company Information
NEXT_PUBLIC_COMPANY_NAME=Alpha LPGas
NEXT_PUBLIC_COMPANY_PHONE=074 454 5665
NEXT_PUBLIC_COMPANY_EMAIL=info@alphalpgas.co.za
NEXT_PUBLIC_COMPANY_ADDRESS=Sunnyacres Shopping Centre, Fish Hoek, Cape Town
```

### 4. Update CORS After Deployment

Once both services are deployed:
1. Note the frontend URL
2. Go to backend service → Variables
3. Update `CORS_ALLOWED_ORIGINS` with the actual frontend URL

### 5. Run Migrations

After backend is deployed:
1. Go to backend service
2. Click **"..."** menu → **"Run Command"**
3. Run: `python manage.py migrate`
4. Run: `python manage.py createsuperuser` (if needed)

### 6. Set Up Custom Domains (Optional)

#### Backend Domain:
1. Go to backend service → **Settings** → **Domains**
2. Add custom domain: `api.alphalpgas.co.za`
3. Update DNS records as instructed by Railway

#### Frontend Domain:
1. Go to frontend service → **Settings** → **Domains**
2. Add custom domain: `alphalpgas.co.za` and `www.alphalpgas.co.za`
3. Update DNS records as instructed by Railway

### 7. Update Environment Variables with Custom Domains

After domains are set up, update:

**Backend:**
```bash
SITE_URL=https://api.alphalpgas.co.za
FRONTEND_URL=https://alphalpgas.co.za
CORS_ALLOWED_ORIGINS=https://alphalpgas.co.za,https://www.alphalpgas.co.za
```

**Frontend:**
```bash
NEXT_PUBLIC_API_URL=https://api.alphalpgas.co.za
```

## Deployment Workflow

### Development Workflow:
1. Make changes locally
2. Test locally
3. Commit and push to `dev` branch
4. Railway auto-deploys to staging
5. Test on staging

### Production Deployment:
1. Merge `dev` into `main`:
   ```bash
   git checkout main
   git merge dev
   git push origin main
   ```
2. Railway auto-deploys to production
3. Test on production

## Environment Comparison

| Feature | Dev/Staging | Production |
|---------|-------------|------------|
| Branch | `dev` | `main` |
| Yoco Keys | Test | Live |
| Domain | Railway subdomain | Custom domain |
| Database | Staging DB | Production DB |
| Debug Mode | Can be True | False |
| Error Logging | Verbose | Production-level |

## Important Notes

1. **Never use test Yoco keys in production**
2. **Keep SECRET_KEY different between environments**
3. **Always test on staging before deploying to production**
4. **Set up database backups for production**
5. **Monitor production logs regularly**
6. **Keep production environment variables secure**

## Rollback Procedure

If production deployment fails:
1. Go to Railway → Production Backend/Frontend
2. Click **"Deployments"**
3. Find the last working deployment
4. Click **"..."** → **"Redeploy"**

Or revert the main branch:
```bash
git checkout main
git revert HEAD
git push origin main
```

## Support

For issues:
- Check Railway logs
- Review environment variables
- Verify database migrations
- Check CORS settings
- Verify Yoco keys are correct (live vs test)
