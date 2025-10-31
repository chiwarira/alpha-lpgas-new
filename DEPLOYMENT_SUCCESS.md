# 🎉 Alpha LPGas - Successfully Deployed on Railway!

## ✅ Deployment Status

**Backend:** ✅ Deployed  
**Frontend:** ✅ Deployed  
**Database:** ✅ Connected  

---

## 🌐 Your Application URLs

### Backend (Django + Wagtail)
- **Django Admin:** https://alpha-lpgas-new-production.up.railway.app/admin/
- **Wagtail CMS:** https://alpha-lpgas-new-production.up.railway.app/cms/
- **API Endpoint:** https://alpha-lpgas-new-production.up.railway.app/api/

### Frontend (Next.js Shop)
- **Shop URL:** https://your-frontend-url.up.railway.app/

---

## 🔐 Create Superuser (First Time Setup)

### Using Railway CLI:

```bash
# 1. Login to Railway
railway login

# 2. Link to your project
railway link

# 3. Select your backend service when prompted
# Then create superuser:
railway run python manage.py createsuperuser

# Follow the prompts:
# - Username: admin (or your choice)
# - Email: info@alphalpgas.co.za
# - Password: (create a strong password)
```

---

## 📝 Post-Deployment Tasks

### 1. Configure Wagtail Site Settings
1. Login to Wagtail CMS: https://alpha-lpgas-new-production.up.railway.app/cms/
2. Go to **Settings** → **Sites**
3. Edit the default site:
   - **Hostname:** `alpha-lpgas-new-production.up.railway.app`
   - **Port:** `443`
   - **Site name:** `Alpha LPGas`
4. Save

### 2. Add Products
1. Go to Django Admin: https://alpha-lpgas-new-production.up.railway.app/admin/
2. Navigate to **Products** → **Add Product**
3. Add your LPG products:
   - 9kg Gas Cylinder
   - 19kg Gas Cylinder
   - 48kg Gas Cylinder
   - Accessories (regulators, hoses, etc.)

### 3. Configure Delivery Zones
1. In Django Admin → **Delivery Zones**
2. Add zones for Fish Hoek and surrounding areas:
   - Fish Hoek (7975)
   - Kalk Bay (7975)
   - Simon's Town (7995)
   - Etc.

### 4. Test Checkout Flow
1. Visit your frontend shop
2. Add products to cart
3. Test checkout process
4. Verify Yoco payment integration

### 5. Configure Hero Banner
1. Login to Wagtail CMS
2. Create/edit home page
3. Add hero banner content
4. Publish

---

## 🔧 Environment Variables Reference

### Backend Variables (Already Set)
```env
SECRET_KEY=your-secret-key
DEBUG=False
DATABASE_URL=(auto-provided by Railway)
ALLOWED_HOSTS=.railway.app,.up.railway.app,alpha-lpgas-new-production.up.railway.app
CORS_ALLOWED_ORIGINS=https://alpha-lpgas-new-production.up.railway.app,https://alphalpgas.co.za
YOCO_SECRET_KEY=your-yoco-secret-key
YOCO_PUBLIC_KEY=your-yoco-public-key
EMAIL_HOST_USER=info@alphalpgas.co.za
EMAIL_HOST_PASSWORD=your-email-password
```

### Frontend Variables (Already Set)
```env
NEXT_PUBLIC_API_URL=https://alpha-lpgas-new-production.up.railway.app
NEXT_PUBLIC_YOCO_PUBLIC_KEY=your-yoco-public-key
```

---

## 🚀 Continuous Deployment

Railway automatically deploys when you push to GitHub:

```bash
# Make changes to your code
git add .
git commit -m "Your changes"
git push origin dev

# Railway will automatically:
# 1. Detect the push
# 2. Build your application
# 3. Deploy the new version
```

---

## 📊 Monitoring & Logs

### View Logs:
1. Railway Dashboard → Select service
2. Click **"Deploy Logs"** or **"Observability"**
3. Monitor real-time logs

### Check Metrics:
1. Railway Dashboard → Service → **"Metrics"**
2. View CPU, Memory, Network usage

---

## 🔗 Connect Custom Domain (Optional)

### When you're ready to use alphalpgas.co.za:

1. **In Railway (Frontend):**
   - Go to Settings → Networking → Custom Domain
   - Add: `alphalpgas.co.za`
   - Railway will provide DNS records

2. **In Railway (Backend):**
   - Add: `api.alphalpgas.co.za` (or use subdomain)
   - Or keep using the Railway URL

3. **Update DNS:**
   - Add CNAME records as shown by Railway
   - Wait for DNS propagation (5-60 minutes)

4. **Update Environment Variables:**
   - Backend: Update `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`
   - Frontend: Update `NEXT_PUBLIC_API_URL` if using custom backend domain

---

## 💰 Cost Estimate

**Railway Pricing:**
- Backend: ~$5-10/month
- Frontend: ~$5/month
- PostgreSQL: ~$5/month
- **Total: ~$15-20/month**

**Free tier includes $5 credit/month**

---

## 🆘 Troubleshooting

### Backend Issues:
- Check Deploy Logs in Railway
- Verify DATABASE_URL is set
- Check ALLOWED_HOSTS includes your domain

### Frontend Issues:
- Verify NEXT_PUBLIC_API_URL is correct
- Check CORS settings in backend
- Review build logs for errors

### Database Issues:
- Ensure Postgres service is running
- Verify DATABASE_URL connection string
- Check if migrations ran successfully

---

## 📞 Support Resources

- **Railway Docs:** https://docs.railway.app
- **Django Docs:** https://docs.djangoproject.com
- **Next.js Docs:** https://nextjs.org/docs
- **Yoco Docs:** https://developer.yoco.com

---

## ✅ Deployment Checklist

- [x] Backend deployed to Railway
- [x] Frontend deployed to Railway
- [x] PostgreSQL database connected
- [x] Environment variables configured
- [ ] Superuser created
- [ ] Wagtail site configured
- [ ] Products added
- [ ] Delivery zones configured
- [ ] Hero banner configured
- [ ] Checkout flow tested
- [ ] Payment integration tested
- [ ] Custom domain configured (optional)

---

**Congratulations! Your Alpha LPGas e-commerce system is live! 🎉**

Next step: Create your superuser account and start adding products!
