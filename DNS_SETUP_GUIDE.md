# 🌐 DNS Setup Guide for Alpha LPGas

This guide shows you exactly how to configure your DNS records for custom domains.

---

## Overview

You need to set up 3 DNS records:
1. **api.alphalpgas.co.za** → Backend (Django)
2. **alphalpgas.co.za** → Frontend (Next.js)
3. **www.alphalpgas.co.za** → Frontend (Next.js)

---

## Step 1: Get Railway URLs

### Backend URL:
1. Go to Railway Dashboard
2. Click on your **Django service**
3. Go to **Settings** → **Domains**
4. Click **"Custom Domain"**
5. Enter: `api.alphalpgas.co.za`
6. Railway will show you a CNAME value like:
   ```
   backend-production-xxxx.up.railway.app
   ```
7. **Copy this value** - you'll need it for DNS

### Frontend URL:
1. Click on your **Next.js service**
2. Go to **Settings** → **Domains**
3. Click **"Custom Domain"**
4. Enter: `alphalpgas.co.za`
5. Railway will show you DNS records (A or CNAME)
6. **Copy these values** - you'll need them for DNS

---

## Step 2: Configure DNS Records

Log in to your domain registrar (where you bought alphalpgas.co.za).

Common registrars:
- **Cloudflare**: https://dash.cloudflare.com
- **GoDaddy**: https://dcc.godaddy.com/domains
- **Namecheap**: https://ap.www.namecheap.com
- **Google Domains**: https://domains.google.com

### Find DNS Settings:
- Look for: "DNS", "DNS Management", "DNS Records", or "Nameservers"
- You need to add/edit DNS records

---

## Step 3: Add DNS Records

### Record 1: Backend API (api.alphalpgas.co.za)

```
Type:     CNAME
Name:     api
Value:    backend-production-xxxx.up.railway.app  (from Railway)
TTL:      Auto or 3600
Proxy:    Off (if using Cloudflare, turn off orange cloud)
```

**Example in Cloudflare:**
```
Type    Name    Content                                  TTL    Proxy
CNAME   api     backend-production-xxxx.up.railway.app   Auto   DNS only
```

**Example in GoDaddy:**
```
Type    Name    Value                                    TTL
CNAME   api     backend-production-xxxx.up.railway.app   1 Hour
```

---

### Record 2: Root Domain (alphalpgas.co.za)

Railway will tell you to use either **A record** or **CNAME**:

#### Option A: If Railway gives you an IP address (A Record):
```
Type:     A
Name:     @  (or leave blank for root)
Value:    [IP address from Railway]
TTL:      Auto or 3600
Proxy:    Off (if using Cloudflare)
```

#### Option B: If Railway gives you a CNAME:
```
Type:     CNAME
Name:     @  (or leave blank for root)
Value:    frontend-production-xxxx.up.railway.app
TTL:      Auto or 3600
Proxy:    Off (if using Cloudflare)
```

**Note**: Some registrars don't allow CNAME on root (@). If you get an error, use the A record option or contact Railway support.

---

### Record 3: WWW Subdomain (www.alphalpgas.co.za)

```
Type:     CNAME
Name:     www
Value:    alphalpgas.co.za  (or the Railway URL)
TTL:      Auto or 3600
Proxy:    Off (if using Cloudflare)
```

**Example:**
```
Type    Name    Content              TTL    Proxy
CNAME   www     alphalpgas.co.za     Auto   DNS only
```

---

## Step 4: Verify DNS Records

After adding records, verify they're correct:

### Using Online Tools:
1. Go to https://dnschecker.org
2. Enter: `api.alphalpgas.co.za`
3. Select: `CNAME`
4. Click **Search**
5. Should show your Railway URL

Repeat for:
- `alphalpgas.co.za` (A or CNAME)
- `www.alphalpgas.co.za` (CNAME)

### Using Command Line:

**Windows (PowerShell):**
```powershell
# Check API subdomain
nslookup api.alphalpgas.co.za

# Check root domain
nslookup alphalpgas.co.za

# Check www subdomain
nslookup www.alphalpgas.co.za
```

**Mac/Linux (Terminal):**
```bash
# Check API subdomain
dig api.alphalpgas.co.za

# Check root domain
dig alphalpgas.co.za

# Check www subdomain
dig www.alphalpgas.co.za
```

---

## Step 5: Wait for DNS Propagation

DNS changes take time to propagate worldwide:
- **Minimum**: 5-30 minutes
- **Average**: 1-4 hours
- **Maximum**: 24-48 hours

**What to expect:**
- ✅ Changes may work immediately for you
- ⏳ Others might see old/no records for a while
- 🌍 Different locations propagate at different speeds

**Check propagation status:**
- https://dnschecker.org
- https://www.whatsmydns.net

---

## Step 6: Verify SSL Certificates

Once DNS propagates, Railway automatically provisions SSL certificates:

1. Visit: `https://api.alphalpgas.co.za`
2. Look for 🔒 padlock in browser
3. Click padlock → Certificate should be valid

Repeat for:
- `https://alphalpgas.co.za`
- `https://www.alphalpgas.co.za`

**If SSL not working:**
- Wait 10-15 more minutes
- Check DNS records are correct
- Clear browser cache
- Try incognito/private mode

---

## Common DNS Configurations

### Cloudflare (Recommended)

**Advantages:**
- Free SSL
- DDoS protection
- CDN (faster loading)
- Analytics

**Settings:**
```
Type    Name    Content                                  Proxy Status
CNAME   api     backend-production-xxxx.up.railway.app   DNS only (grey)
A       @       [Railway IP]                             DNS only (grey)
CNAME   www     alphalpgas.co.za                         DNS only (grey)
```

**Important**: Turn OFF orange cloud (Proxy) for Railway domains!

---

### GoDaddy

```
Type    Name    Value                                    TTL
CNAME   api     backend-production-xxxx.up.railway.app   1 Hour
A       @       [Railway IP]                             1 Hour
CNAME   www     alphalpgas.co.za                         1 Hour
```

---

### Namecheap

```
Type          Host    Value                                    TTL
CNAME Record  api     backend-production-xxxx.up.railway.app   Automatic
A Record      @       [Railway IP]                             Automatic
CNAME Record  www     alphalpgas.co.za                         Automatic
```

---

## Troubleshooting

### "DNS_PROBE_FINISHED_NXDOMAIN" Error
- DNS records not propagated yet
- Wait longer (up to 48 hours)
- Check records are correct
- Clear DNS cache: `ipconfig /flushdns` (Windows) or `sudo dscacheutil -flushcache` (Mac)

### "This site can't provide a secure connection"
- SSL certificate not issued yet
- Wait 10-15 minutes after DNS propagates
- Check DNS records point to Railway
- Contact Railway support if persists

### "CNAME not allowed on root domain"
- Use A record instead
- Or use CNAME flattening (Cloudflare supports this)
- Contact your registrar for help

### Changes not taking effect
- Clear browser cache
- Try incognito/private mode
- Try different browser
- Check on different device/network
- Use https://dnschecker.org to verify

### Cloudflare "Error 1016"
- Turn off orange cloud (Proxy)
- Use "DNS only" (grey cloud)
- Railway needs direct DNS access

---

## Final DNS Configuration Summary

After setup, your DNS should look like this:

```
Record Type    Name/Host    Points To                                Status
-----------    ---------    ---------                                ------
CNAME          api          backend-production-xxxx.up.railway.app   Active
A or CNAME     @            [Railway provides]                       Active
CNAME          www          alphalpgas.co.za                         Active
```

---

## Testing Checklist

Once DNS propagates, test:

- [ ] `https://api.alphalpgas.co.za` loads
- [ ] `https://api.alphalpgas.co.za/admin/` shows Django admin
- [ ] `https://alphalpgas.co.za` loads frontend
- [ ] `https://www.alphalpgas.co.za` redirects to `https://alphalpgas.co.za`
- [ ] All URLs show 🔒 padlock (SSL)
- [ ] No certificate warnings
- [ ] API calls work from frontend
- [ ] No CORS errors in browser console

---

## Quick Reference

### DNS Checker Tools:
- https://dnschecker.org
- https://www.whatsmydns.net
- https://mxtoolbox.com/SuperTool.aspx

### SSL Checker:
- https://www.ssllabs.com/ssltest/

### Railway Support:
- https://discord.gg/railway
- https://docs.railway.app/deploy/custom-domains

---

## Need Help?

1. **Check Railway Docs**: https://docs.railway.app/deploy/custom-domains
2. **Railway Discord**: https://discord.gg/railway
3. **Your Registrar Support**: Contact them for DNS help
4. **DNS Propagation**: Just wait - it takes time!

---

**Your domains should be live within 24 hours! 🎉**
