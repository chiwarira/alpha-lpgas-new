# 🚀 Oscar Gas - Railway Deployment Guide

Complete step-by-step guide for deploying the backend application to Railway for **api.oscargas.co.za**

---

## 📋 Prerequisites

Before starting, ensure you have:
- [ ] Railway account (https://railway.app)
- [ ] Client's company information (name, address, contact details, VAT number)
- [ ] Client's branding assets (logo, colors)
- [ ] Domain name: **api.oscargas.co.za**
- [ ] Cloudinary account for media storage (free tier available)
- [ ] Git repository access

**Not Required:**
- ❌ Wagtail CMS module
- ❌ Email credentials (using console backend)
- ❌ Payment gateway (YOCO)
- ❌ Contact submissions
- ❌ Hero banners
- ❌ Gas stock levels
- ❌ Loyalty cards
- ❌ Tax reporting modules

---

## 🎯 Deployment Overview

**Total Time:** ~45-60 minutes

1. **Prepare Codebase** (15 min)
2. **Setup Railway Project** (10 min)
3. **Configure Database** (5 min)
4. **Set Environment Variables** (10 min)
5. **Deploy Application** (5 min)
6. **Configure Domain** (10 min)
7. **Initialize Database & Admin** (5 min)

---

## 📦 Step 1: Prepare Codebase (15 minutes)

### 1.1 Clone/Copy Project

```bash
# Option A: Clone from repository
git clone <repository-url> oscargas-backend
cd oscargas-backend

# Option B: Copy existing project
cp -r alpha-lpgas-new oscargas-backend
cd oscargas-backend
```

### 1.2 Remove Unnecessary Modules

**Files/Directories to Remove or Disable:**

```bash
# Navigate to backend directory
cd backend

# Remove tax reporting templates (if they exist)
rm -rf templates/core/tax_reports/
rm -rf templates/core/tax_*.html

# Remove loyalty card templates
rm -rf templates/core/loyalty/

# Remove contact submission templates
rm -rf templates/core/contact_submissions/

# Remove hero banner templates
rm -rf templates/core/hero_banners/

# Remove stock level templates
rm -rf templates/core/stock_levels/
```

### 1.3 Update `settings.py` for Oscar Gas

Edit `backend/alphalpgas/settings.py`:

```python
# Line 27: Update domain
ALLOWED_HOSTS.append('api.oscargas.co.za')

# Line 32: Update CSRF trusted origins
CSRF_TRUSTED_ORIGINS = [
    'https://*.railway.app',
    'https://*.up.railway.app',
    'https://api.oscargas.co.za',
]

# Line 169: Update CORS origins (add your frontend domain)
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', 
    default='http://localhost:3000,https://oscargas.co.za,https://www.oscargas.co.za').split(',')

# Line 247: Update default email
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='info@oscargas.co.za')

# Line 258: Update Wagtail site name (or remove if not using)
WAGTAIL_SITE_NAME = 'Oscar Gas'

# Line 263: Update API title
SPECTACULAR_SETTINGS = {
    'TITLE': 'Oscar Gas API',
    'DESCRIPTION': 'API for Oscar Gas delivery and accounting system',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}
```

### 1.4 Update `requirements.txt` (Remove Wagtail)

Edit `backend/requirements.txt` - **Remove these lines:**

```txt
# CMS
wagtail==5.2
wagtail-localize==1.7
```

**Remove payment processing (since YOCO not needed):**

```txt
# Payment processing (YOCO)
stripe==7.8.0
```

**Remove Celery (if not using async tasks):**

```txt
# Celery for async tasks
celery==5.3.4
redis==5.0.1
```

### 1.5 Commit Changes

```bash
git add .
git commit -m "Configure for Oscar Gas deployment"
git push origin main
```

---

## 🚂 Step 2: Setup Railway Project (10 minutes)

### 2.1 Create New Project

1. Go to https://railway.app
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub
5. Select your repository: `oscargas-backend`
6. Railway will detect the project automatically

### 2.2 Add PostgreSQL Database

1. In your Railway project, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway will provision a PostgreSQL database
4. Wait for database to be ready (~30 seconds)

### 2.3 Configure Build Settings

Railway should auto-detect your `railway.toml`, but verify:

1. Click on your service (not the database)
2. Go to **"Settings"** tab
3. Verify:
   - **Root Directory:** Leave empty (or set to `/`)
   - **Build Command:** Auto-detected from `railway.toml`
   - **Start Command:** `cd backend && bash start.sh`

---

## 🔐 Step 3: Configure Environment Variables (10 minutes)

### 3.1 Get Database Connection String

1. Click on your **PostgreSQL** service
2. Go to **"Variables"** tab
3. Copy the **`DATABASE_URL`** value (starts with `postgresql://`)

### 3.2 Setup Cloudinary (Media Storage)

1. Go to https://cloudinary.com (sign up for free)
2. From dashboard, get:
   - **Cloud Name**
   - **API Key**
   - **API Secret**

### 3.3 Add Environment Variables to Railway

Click on your **web service** → **"Variables"** tab → Add these:

```bash
# Django Settings
SECRET_KEY=<generate-random-50-char-string>
DEBUG=False
ALLOWED_HOSTS=api.oscargas.co.za,.railway.app,.up.railway.app
RAILWAY_ENVIRONMENT=production

# Database (automatically added by Railway, verify it exists)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Cloudinary
CLOUDINARY_CLOUD_NAME=<your-cloud-name>
CLOUDINARY_API_KEY=<your-api-key>
CLOUDINARY_API_SECRET=<your-api-secret>

# CORS Origins (add your frontend domain)
CORS_ALLOWED_ORIGINS=https://oscargas.co.za,https://www.oscargas.co.za

# Site URLs
SITE_URL=https://api.oscargas.co.za
FRONTEND_URL=https://oscargas.co.za

# Email (Console backend - no credentials needed)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=info@oscargas.co.za

# JWT Token Lifetimes (in minutes)
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440

# Optional: Google OAuth (if using social login)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

**Generate SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 🚀 Step 4: Deploy Application (5 minutes)

### 4.1 Trigger Deployment

Railway will automatically deploy when you:
- Push to your GitHub repository
- Or click **"Deploy"** in Railway dashboard

### 4.2 Monitor Deployment

1. Go to **"Deployments"** tab
2. Click on the latest deployment
3. Watch the build logs
4. Wait for status: **"Success"** (takes 3-5 minutes)

### 4.3 Verify Deployment

1. Click on your service
2. Go to **"Settings"** → **"Domains"**
3. You'll see a Railway-generated domain like: `oscargas-backend-production.up.railway.app`
4. Click the domain to open your app
5. You should see the home page

---

## 🌐 Step 5: Configure Custom Domain (10 minutes)

### 5.1 Add Domain in Railway

1. In Railway, click your service
2. Go to **"Settings"** → **"Domains"**
3. Click **"+ Custom Domain"**
4. Enter: `api.oscargas.co.za`
5. Railway will show you DNS records to add

### 5.2 Configure DNS

Railway will provide CNAME record details. Add to your DNS provider:

```
Type: CNAME
Name: api
Value: <railway-provided-value>.railway.app
TTL: 3600 (or Auto)
```

**Common DNS Providers:**
- **Cloudflare:** DNS → Add record
- **GoDaddy:** DNS Management → Add CNAME
- **Namecheap:** Advanced DNS → Add record

### 5.3 Wait for DNS Propagation

- Usually takes 5-15 minutes
- Can take up to 48 hours in rare cases
- Check status: https://dnschecker.org

### 5.4 Verify SSL Certificate

Railway automatically provisions SSL certificates:
- Wait 2-3 minutes after DNS propagates
- Visit: https://api.oscargas.co.za
- You should see a valid SSL certificate (🔒)

---

## 🗄️ Step 6: Initialize Database & Create Admin (5 minutes)

### 6.1 Access Railway Shell

1. In Railway, click your web service
2. Click **"..."** (three dots) → **"Shell"**
3. Or use Railway CLI:

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link to project
railway link

# Open shell
railway run bash
```

### 6.2 Run Migrations

Migrations should have run automatically via `start.sh`, but verify:

```bash
cd backend
python manage.py migrate
```

### 6.3 Create Superuser

The `start.sh` script calls `create_initial_superuser`. Check if it exists:

```bash
python manage.py shell
```

In Python shell:
```python
from django.contrib.auth import get_user_model
User = get_user_model()
print(User.objects.filter(is_superuser=True).count())
exit()
```

If no superuser exists, create one:

```bash
python manage.py createsuperuser
# Email: admin@oscargas.co.za
# Password: <secure-password>
```

### 6.4 Setup Company Settings

1. Visit: https://api.oscargas.co.za/admin/
2. Login with superuser credentials
3. Navigate to **Core → Company Settings**
4. Click **"Add Company Settings"** (if not exists)
5. Fill in:
   - **Company Name:** Oscar Gas
   - **Email:** info@oscargas.co.za
   - **Phone:** <client-phone>
   - **Address:** <client-address>
   - **VAT Number:** <client-vat>
   - **Logo:** Upload client logo
   - **Favicon:** Upload favicon
   - **Primary Color:** <brand-color>
6. Save

---

## ✅ Step 7: Post-Deployment Verification

### 7.1 Test API Endpoints

```bash
# Health check
curl https://api.oscargas.co.za/

# API root
curl https://api.oscargas.co.za/api/

# API documentation
# Visit: https://api.oscargas.co.za/api/docs/
```

### 7.2 Test Authentication

```bash
# Register a test user
curl -X POST https://api.oscargas.co.za/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@oscargas.co.za",
    "password": "testpass123",
    "first_name": "Test",
    "last_name": "User"
  }'

# Login
curl -X POST https://api.oscargas.co.za/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@oscargas.co.za",
    "password": "testpass123"
  }'
```

### 7.3 Test Admin Panel

1. Visit: https://api.oscargas.co.za/admin/
2. Login with superuser
3. Verify all models are accessible:
   - ✅ Clients
   - ✅ Suppliers
   - ✅ Products
   - ✅ Invoices
   - ✅ Quotes
   - ✅ Payments
   - ✅ Credit Notes
   - ✅ Orders
   - ✅ Delivery Zones
   - ✅ Drivers
   - ✅ Journal Entries

### 7.4 Test Accounting Features

1. Go to: https://api.oscargas.co.za/accounting/
2. Login with superuser
3. Test creating:
   - New client
   - New invoice
   - New payment
   - Journal entry

---

## 🔧 Troubleshooting

### Issue: Build Fails

**Check build logs:**
1. Railway → Deployments → Click failed deployment
2. Look for error messages

**Common fixes:**
- Verify `requirements.txt` has no syntax errors
- Check Python version compatibility
- Ensure `start.sh` has execute permissions

### Issue: Database Connection Error

**Verify DATABASE_URL:**
```bash
# In Railway shell
echo $DATABASE_URL
```

**Should start with:** `postgresql://`

### Issue: Static Files Not Loading

**Check collectstatic:**
```bash
python manage.py collectstatic --noinput
```

**Verify STATIC_ROOT in settings:**
```python
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

### Issue: Domain Not Working

**Check DNS:**
```bash
nslookup api.oscargas.co.za
```

**Should return Railway's IP address**

**Check ALLOWED_HOSTS:**
```python
ALLOWED_HOSTS = ['api.oscargas.co.za', '.railway.app']
```

### Issue: CORS Errors

**Update CORS_ALLOWED_ORIGINS:**
```bash
# In Railway variables
CORS_ALLOWED_ORIGINS=https://oscargas.co.za,https://www.oscargas.co.za
```

---

## 📊 Monitoring & Maintenance

### View Logs

**In Railway:**
1. Click your service
2. Go to **"Logs"** tab
3. Real-time logs appear here

**Using CLI:**
```bash
railway logs
```

### Database Backups

**Railway Pro Plan includes automatic backups**

**Manual backup:**
1. Click PostgreSQL service
2. Go to **"Data"** tab
3. Click **"Backup"**

**Or use pg_dump:**
```bash
# Get DATABASE_URL from Railway
pg_dump $DATABASE_URL > backup.sql
```

### Scaling

**Vertical Scaling (Railway Settings):**
1. Service → Settings → Resources
2. Adjust memory/CPU as needed

**Horizontal Scaling:**
- Railway supports multiple instances
- Configure in Settings → Instances

---

## 🎉 Deployment Complete!

Your Oscar Gas backend is now live at:
- **API:** https://api.oscargas.co.za
- **Admin:** https://api.oscargas.co.za/admin/
- **Accounting:** https://api.oscargas.co.za/accounting/
- **API Docs:** https://api.oscargas.co.za/api/docs/

---

## 📝 Next Steps

1. **Connect Frontend:**
   - Update frontend API URL to `https://api.oscargas.co.za`
   - Test all frontend features

2. **Add Initial Data:**
   - Import clients (if migrating)
   - Add products
   - Configure delivery zones
   - Add drivers

3. **User Training:**
   - Create user accounts for staff
   - Assign appropriate permissions
   - Provide training on accounting features

4. **Monitoring:**
   - Set up error monitoring (Sentry)
   - Configure uptime monitoring
   - Set up alerts

---

## 🔗 Useful Links

- **Railway Dashboard:** https://railway.app/dashboard
- **Railway Docs:** https://docs.railway.app
- **Django Docs:** https://docs.djangoproject.com
- **DRF Docs:** https://www.django-rest-framework.org

---

## 📞 Support

For issues or questions:
- Check Railway logs first
- Review Django error messages
- Consult this guide's troubleshooting section

**Common Commands:**
```bash
# View logs
railway logs

# Run migrations
railway run python backend/manage.py migrate

# Create superuser
railway run python backend/manage.py createsuperuser

# Open shell
railway run bash

# Restart service
# Railway → Service → Settings → Restart
```
