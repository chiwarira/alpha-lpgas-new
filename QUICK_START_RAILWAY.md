# ⚡ Quick Start: Deploy to Railway in 10 Minutes

## 🎯 What You'll Deploy
- **Backend:** Django API + Wagtail CMS
- **Frontend:** Next.js Shop
- **Database:** PostgreSQL
- **Cost:** ~$15-20/month (Free tier available for testing)

---

## 📝 Pre-Deployment Checklist

### 1. Push Code to GitHub
```bash
cd c:\Users\Chiwarira\CascadeProjects\alpha-lpgas-new
git add .
git commit -m "Prepare for Railway deployment"
git push origin dev
```

### 2. Get Your API Keys Ready
- **Yoco Secret Key** (from https://portal.yoco.com)
- **Yoco Public Key** (from https://portal.yoco.com)
- **Email Password** (Gmail App Password)

---

## 🚀 Deploy in 5 Steps

### **Step 1: Create Railway Account** (2 min)
1. Go to https://railway.app
2. Click "Login" → "Login with GitHub"
3. Authorize Railway

### **Step 2: Create New Project** (1 min)
1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose `chiwarira/alpha-lpgas-new`
4. Select branch: `dev`

### **Step 3: Add PostgreSQL** (1 min)
1. In your project, click "+ New"
2. Select "Database" → "PostgreSQL"
3. Done! Railway auto-connects it

### **Step 4: Configure Backend** (3 min)

Click on **Django service** → **Variables** → **RAW Editor** → Paste:

```env
SECRET_KEY=django-insecure-CHANGE-THIS-TO-RANDOM-STRING
DEBUG=False
ALLOWED_HOSTS=.railway.app,.up.railway.app
RAILWAY_ENVIRONMENT=production
CORS_ALLOWED_ORIGINS=https://alpha-lpgas-new-production.up.railway.app
YOCO_SECRET_KEY=your-yoco-secret-key
YOCO_PUBLIC_KEY=your-yoco-public-key
EMAIL_HOST_USER=info@alphalpgas.co.za
EMAIL_HOST_PASSWORD=your-gmail-app-password
```

**Generate SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### **Step 5: Configure Frontend** (2 min)

Click on **Next.js service** → **Variables** → **RAW Editor** → Paste:

```env
NEXT_PUBLIC_API_URL=https://your-backend-url.up.railway.app
NEXT_PUBLIC_YOCO_PUBLIC_KEY=your-yoco-public-key
```

**Note:** Replace `your-backend-url` with actual URL from Railway (see backend service URL)

---

## ✅ Verify Deployment (1 min)

1. Wait for builds to complete (~5 min)
2. Click on services to see generated URLs
3. Visit frontend URL - shop should load!

---

## 🔧 Post-Deployment Setup (5 min)

### Create Superuser

**Option A: Using Railway CLI**
```bash
# Install CLI
npm install -g @railway/cli

# Login
railway login

# Link project
railway link

# Create superuser
railway run python manage.py createsuperuser
```

**Option B: Using Railway Dashboard**
1. Go to backend service → "Settings" → "Deploy Logs"
2. You'll see Django running
3. Use CLI method above

### Access Admin Panels
- **Django Admin:** `https://your-backend.up.railway.app/admin/`
- **Wagtail CMS:** `https://your-backend.up.railway.app/cms/`
- **Shop Frontend:** `https://your-frontend.up.railway.app/`

### Add Initial Data
1. Login to Django admin
2. Add Products
3. Add Delivery Zones
4. Configure Hero Banner in Wagtail

---

## 🎉 You're Live!

Your Alpha LPGas system is now deployed and accessible worldwide!

**Next Steps:**
- [ ] Add your products
- [ ] Test checkout flow
- [ ] Test Yoco payments
- [ ] Configure custom domain (optional)
- [ ] Set up email notifications

---

## 💡 Tips

### Auto-Deploy on Push
Railway automatically deploys when you push to GitHub:
```bash
git add .
git commit -m "Update products"
git push origin dev
```

### View Logs
- Railway Dashboard → Service → "Deploy Logs"
- Or: `railway logs`

### Database Access
- Railway provides connection string in Variables
- Use pgAdmin or DBeaver to connect

---

## 🆘 Need Help?

**Common Issues:**

1. **Build fails:** Check Deploy Logs for errors
2. **Database error:** Ensure PostgreSQL service is running
3. **CORS error:** Update `CORS_ALLOWED_ORIGINS` with frontend URL
4. **Static files missing:** Check if `collectstatic` ran in logs

**Support:**
- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway

---

## 📊 What's Deployed?

```
┌─────────────────────────────────────┐
│  Railway Project: alpha-lpgas-new   │
├─────────────────────────────────────┤
│                                     │
│  ✅ Frontend (Next.js)              │
│     - Shop interface                │
│     - Product catalog               │
│     - Checkout system               │
│                                     │
│  ✅ Backend (Django)                │
│     - REST API                      │
│     - Admin panel                   │
│     - Wagtail CMS                   │
│     - Order management              │
│                                     │
│  ✅ Database (PostgreSQL)           │
│     - Products                      │
│     - Orders                        │
│     - Customers                     │
│                                     │
└─────────────────────────────────────┘
```

---

**Congratulations! Your system is live! 🚀**
