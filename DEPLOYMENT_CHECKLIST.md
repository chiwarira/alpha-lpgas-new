# 🚀 Deployment Checklist - Alpha LPGas

Use this checklist to ensure smooth deployment with custom domains.

---

## Pre-Deployment

- [ ] All code committed and pushed to GitHub (`dev` branch)
- [ ] `.env.railway` file reviewed and ready
- [ ] Domain registered (`alphalpgas.co.za`)
- [ ] Access to domain DNS settings
- [ ] Railway account created
- [ ] Yoco account set up (live keys ready)
- [ ] Gmail app password generated for emails

---

## Railway Setup

### Initial Project
- [ ] Railway project created
- [ ] GitHub repository connected
- [ ] Both services detected (Django + Next.js)

### Database
- [ ] PostgreSQL database added to project
- [ ] Database linked to Django service
- [ ] `DATABASE_URL` auto-provided

---

## Backend (Django) Configuration

### Environment Variables
- [ ] `SECRET_KEY` generated and added
- [ ] `DEBUG=False` set
- [ ] `ALLOWED_HOSTS` includes Railway and custom domain
- [ ] `CORS_ALLOWED_ORIGINS` configured
- [ ] `CSRF_TRUSTED_ORIGINS` configured
- [ ] `SITE_URL` set to `https://api.alphalpgas.co.za`
- [ ] `FRONTEND_URL` set to `https://alphalpgas.co.za`
- [ ] Email settings configured
- [ ] Yoco live keys added

### Build Settings
- [ ] Root directory set to `backend`
- [ ] Start command: `gunicorn alphalpgas.wsgi:application`

### Deployment
- [ ] Backend deployed successfully
- [ ] No errors in deploy logs
- [ ] Railway URL noted

---

## Frontend (Next.js) Configuration

### Environment Variables
- [ ] `NEXT_PUBLIC_API_URL` set to backend URL
- [ ] `NEXT_PUBLIC_YOCO_PUBLIC_KEY` added
- [ ] Company information variables added

### Build Settings
- [ ] Root directory set to `frontend`
- [ ] Build command: `npm run build`
- [ ] Start command: `npm start`

### Deployment
- [ ] Frontend deployed successfully
- [ ] No errors in deploy logs
- [ ] Railway URL noted

---

## Custom Domain Setup

### Backend Domain (api.alphalpgas.co.za)
- [ ] Custom domain added in Railway
- [ ] CNAME record added in DNS:
  - Type: `CNAME`
  - Name: `api`
  - Value: `[Railway backend URL]`
- [ ] DNS propagated (check: https://dnschecker.org)
- [ ] SSL certificate active
- [ ] `ALLOWED_HOSTS` updated with custom domain

### Frontend Domain (alphalpgas.co.za)
- [ ] Custom domain added in Railway
- [ ] Root domain record added in DNS:
  - Type: `A` or `CNAME`
  - Name: `@`
  - Value: `[Railway provides]`
- [ ] WWW subdomain added:
  - Type: `CNAME`
  - Name: `www`
  - Value: `alphalpgas.co.za`
- [ ] DNS propagated
- [ ] SSL certificate active
- [ ] `NEXT_PUBLIC_API_URL` updated to `https://api.alphalpgas.co.za`
- [ ] Backend `CORS_ALLOWED_ORIGINS` updated with frontend domains

---

## Post-Deployment Setup

### Database & Admin
- [ ] Railway CLI installed: `npm install -g @railway/cli`
- [ ] Logged in: `railway login`
- [ ] Project linked: `railway link`
- [ ] Migrations run: `railway run python manage.py migrate`
- [ ] Static files collected: `railway run python manage.py collectstatic --noinput`
- [ ] Superuser created: `railway run python manage.py createsuperuser`

### Wagtail Configuration
- [ ] Accessed CMS: `https://api.alphalpgas.co.za/cms/`
- [ ] Site settings updated:
  - Hostname: `alphalpgas.co.za`
  - Port: `443`
  - Site name: `Alpha LPGas`

### Initial Data
- [ ] Company settings added (Systems section)
- [ ] Delivery zones created
- [ ] Products added with images
- [ ] Categories created
- [ ] Hero banners uploaded (optional)
- [ ] Testimonials added (optional)

---

## Testing

### Backend Testing
- [ ] Admin panel accessible: `https://api.alphalpgas.co.za/admin/`
- [ ] CMS accessible: `https://api.alphalpgas.co.za/cms/`
- [ ] API endpoints working: `https://api.alphalpgas.co.za/api/accounting/products/`
- [ ] No CORS errors in browser console

### Frontend Testing
- [ ] Homepage loads: `https://alphalpgas.co.za`
- [ ] WWW redirect works: `https://www.alphalpgas.co.za`
- [ ] Products display correctly
- [ ] Images loading
- [ ] Add to cart works
- [ ] Checkout page loads
- [ ] Delivery zones populate
- [ ] Payment gateway initializes

### Payment Testing
- [ ] Test payment with test card (if available)
- [ ] Switch to live keys after successful test
- [ ] Webhook URL configured in Yoco portal
- [ ] Test live payment with small amount

### Domain Testing
- [ ] `https://alphalpgas.co.za` - ✅ Working
- [ ] `https://www.alphalpgas.co.za` - ✅ Working
- [ ] `https://api.alphalpgas.co.za` - ✅ Working
- [ ] All have valid SSL (🔒 padlock)
- [ ] No mixed content warnings

---

## Security Verification

- [ ] `DEBUG=False` confirmed
- [ ] Strong `SECRET_KEY` in use
- [ ] HTTPS working on all domains
- [ ] CORS properly restricted
- [ ] Admin password is strong
- [ ] Database credentials secure
- [ ] Email credentials secure
- [ ] Yoco live keys secure (not in git)

---

## Monitoring Setup

- [ ] Railway logs accessible
- [ ] Database backup strategy in place
- [ ] Error monitoring configured (optional)
- [ ] Uptime monitoring (optional)

---

## Documentation

- [ ] Admin credentials documented securely
- [ ] Environment variables documented
- [ ] Deployment process documented
- [ ] Team members have access

---

## Go Live

- [ ] All checklist items completed
- [ ] Final testing done
- [ ] Stakeholders notified
- [ ] Social media/marketing updated with new URL
- [ ] Old site redirected (if applicable)

---

## Post-Launch

- [ ] Monitor logs for first 24 hours
- [ ] Check for any errors
- [ ] Verify orders are processing
- [ ] Test email notifications
- [ ] Backup database
- [ ] Document any issues

---

## Quick Commands Reference

```bash
# View logs
railway logs

# Run migrations
railway run python manage.py migrate

# Create superuser
railway run python manage.py createsuperuser

# Collect static files
railway run python manage.py collectstatic --noinput

# Django shell
railway run python manage.py shell

# Check deployment
curl https://api.alphalpgas.co.za/api/accounting/products/
```

---

## Important URLs

- **Frontend**: https://alphalpgas.co.za
- **Admin**: https://api.alphalpgas.co.za/admin/
- **CMS**: https://api.alphalpgas.co.za/cms/
- **API**: https://api.alphalpgas.co.za/api/
- **Railway Dashboard**: https://railway.app/dashboard

---

## Support Contacts

- **Railway Support**: https://discord.gg/railway
- **Yoco Support**: https://support.yoco.com
- **Domain Registrar**: [Your registrar support]

---

**Status**: ⬜ Not Started | 🟡 In Progress | ✅ Complete

**Deployment Date**: _______________

**Deployed By**: _______________

**Notes**:
_______________________________________
_______________________________________
_______________________________________
