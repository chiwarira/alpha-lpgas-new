# 🚀 Railway Deployment Guide for Alpha LPGas

## Prerequisites
- GitHub account
- Railway account (sign up at https://railway.app)
- Your code pushed to GitHub

---

## 📋 Step-by-Step Deployment

### **Step 1: Prepare Your Repository**

Make sure all changes are committed and pushed to GitHub:
```bash
git add .
git commit -m "Prepare for Railway deployment"
git push origin dev
```

---

### **Step 2: Create Railway Project**

1. Go to https://railway.app
2. Click **"Start a New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub
5. Select repository: `chiwarira/alpha-lpgas-new`
6. Railway will detect both Django and Next.js

---

### **Step 3: Set Up Backend (Django)**

Railway will create a service for the backend automatically.

#### **Add PostgreSQL Database:**
1. In your Railway project, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway will create and link the database automatically

#### **Configure Environment Variables:**

Click on your Django service → **"Variables"** tab → Add these:

```env
# Django Settings
SECRET_KEY=your-super-secret-key-here-generate-a-new-one
DEBUG=False
ALLOWED_HOSTS=.railway.app,.up.railway.app
RAILWAY_ENVIRONMENT=production

# Database (Railway provides this automatically as DATABASE_URL)
# No need to add manually

# CORS Settings
CORS_ALLOWED_ORIGINS=https://your-frontend-url.up.railway.app
CORS_ALLOW_CREDENTIALS=True

# Static Files
STATIC_URL=/static/
MEDIA_URL=/media/

# Wagtail
WAGTAIL_SITE_NAME=Alpha LPGas

# Email (Optional - for production)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Yoco Payment
YOCO_SECRET_KEY=your-yoco-secret-key
YOCO_PUBLIC_KEY=your-yoco-public-key
```

#### **Generate SECRET_KEY:**
Run this in Python:
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

---

### **Step 4: Set Up Frontend (Next.js)**

Railway will create a separate service for the frontend.

#### **Configure Environment Variables:**

Click on your Next.js service → **"Variables"** tab → Add these:

```env
# Backend API URL (will be your Django Railway URL)
NEXT_PUBLIC_API_URL=https://your-backend-url.up.railway.app

# Yoco Public Key
NEXT_PUBLIC_YOCO_PUBLIC_KEY=your-yoco-public-key
```

---

### **Step 5: Deploy**

1. Railway will automatically deploy both services
2. Wait for builds to complete (5-10 minutes)
3. Check deployment logs for any errors

---

### **Step 6: Initial Setup**

Once deployed, you need to create a superuser:

1. Go to your Django service in Railway
2. Click on **"Settings"** → **"Deploy Logs"**
3. Or use Railway CLI:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Run Django commands
railway run python manage.py createsuperuser
```

---

### **Step 7: Configure Custom Domain (Optional)**

1. In Railway, click on your service
2. Go to **"Settings"** → **"Domains"**
3. Click **"Generate Domain"** or **"Custom Domain"**
4. Add your domain and update DNS records

Update environment variables:
```env
ALLOWED_HOSTS=yourdomain.com,.railway.app
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

---

## 🔧 Post-Deployment Tasks

### **1. Create Superuser**
```bash
railway run python manage.py createsuperuser
```

### **2. Access Admin Panel**
- Backend Admin: `https://your-backend-url.up.railway.app/admin/`
- Wagtail CMS: `https://your-backend-url.up.railway.app/cms/`

### **3. Configure Wagtail Site**
1. Go to Wagtail admin
2. Settings → Sites
3. Update hostname to your Railway URL

### **4. Upload Products**
1. Go to Django admin
2. Add your products, delivery zones, etc.

---

## 📊 Monitoring & Logs

### **View Logs:**
- In Railway dashboard, click on service → **"Deploy Logs"**
- Or use CLI: `railway logs`

### **Database Access:**
- Railway provides a PostgreSQL connection string
- Use tools like pgAdmin or DBeaver to connect

---

## 💰 Pricing Estimate

Railway pricing (as of 2024):
- **Free Tier:** $5 credit/month (good for testing)
- **Hobby Plan:** $5/month + usage
- **Estimated Monthly Cost:**
  - Backend: ~$5-10
  - Frontend: ~$5
  - Database: ~$5
  - **Total: ~$15-20/month**

---

## 🔄 Continuous Deployment

Railway automatically deploys when you push to GitHub:

```bash
git add .
git commit -m "Update feature"
git push origin dev
```

Railway will detect the push and redeploy automatically!

---

## 🐛 Troubleshooting

### **Build Fails:**
- Check **"Deploy Logs"** for errors
- Ensure `requirements.txt` is up to date
- Verify Python version in `runtime.txt`

### **Database Connection Error:**
- Railway auto-provides `DATABASE_URL`
- Check if PostgreSQL service is running

### **Static Files Not Loading:**
- Ensure `collectstatic` runs in build
- Check `STATIC_URL` and `STATIC_ROOT` settings

### **CORS Errors:**
- Update `CORS_ALLOWED_ORIGINS` with frontend URL
- Add frontend domain to `CSRF_TRUSTED_ORIGINS`

---

## 📞 Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Django Docs: https://docs.djangoproject.com

---

## ✅ Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Railway project created
- [ ] PostgreSQL database added
- [ ] Backend environment variables configured
- [ ] Frontend environment variables configured
- [ ] Both services deployed successfully
- [ ] Superuser created
- [ ] Admin panel accessible
- [ ] Products added
- [ ] Frontend connects to backend
- [ ] Payment gateway tested
- [ ] Custom domain configured (optional)

---

**Your Alpha LPGas system should now be live on Railway! 🎉**

Need help? Check the logs or reach out to Railway support.
