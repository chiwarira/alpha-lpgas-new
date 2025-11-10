# 🎨 Logo & Favicon Setup Guide

## Overview

You can now upload your company logo and favicon through the Django admin panel. They will automatically appear on both the backend (accounting system) and frontend (customer website).

---

## How to Upload Logo & Favicon

### Step 1: Access Django Admin

**Local Development:**
```
http://localhost:8000/admin/
```

**Production:**
```
https://api.alphalpgas.co.za/admin/
```

Login with your superuser credentials.

### Step 2: Go to Company Settings

1. In the admin panel, find **"Core"** section
2. Click on **"Company Settings"**
3. Click on the existing settings entry (there should be only one)

### Step 3: Upload Your Files

Scroll down to the **"Branding"** section:

#### Upload Logo:
- Click **"Choose File"** next to **Logo**
- Select your logo file
- **Recommended:**
  - Format: PNG with transparent background
  - Size: 200x200px (square) or 300x100px (horizontal)
  - File size: Under 500KB
  - Should look good on dark background (for navbar)

#### Upload Favicon:
- Click **"Choose File"** next to **Favicon**
- Select your favicon file
- **Recommended:**
  - Format: PNG or ICO
  - Size: 32x32px or 64x64px
  - File size: Under 100KB
  - Simple, recognizable design

### Step 4: Save

Click **"Save"** button at the bottom of the page.

### Step 5: Verify

**Backend (Accounting System):**
- Refresh the accounting dashboard
- Logo should appear in the navigation bar (top left)
- Favicon should appear in browser tab

**Frontend (Customer Website):**
- Visit your website
- Favicon should load automatically
- Logo available via API for future use

---

## Where They Appear

### Logo Appears:
✅ **Backend Navigation Bar** - Replaces calculator icon  
✅ **API Endpoint** - Available at `/api/accounting/settings/`  
✅ **Future Use** - Can be added to invoices, emails, etc.

### Favicon Appears:
✅ **Backend Browser Tab** - When viewing accounting system  
✅ **Frontend Browser Tab** - When viewing customer website  
✅ **Bookmarks** - When users save your site  
✅ **Browser History**  
✅ **Mobile Home Screen** - When added to phone

---

## Technical Details

### How It Works:

1. **Upload via Admin** → Files saved to `/media/branding/`
2. **Backend** → Context processor makes settings available to all templates
3. **Frontend** → `FaviconLoader` component fetches from API and updates favicon dynamically
4. **API** → Settings available at `/api/accounting/settings/`

### API Response:
```json
{
  "id": 1,
  "company_name": "Alpha LPGas",
  "logo": "/media/branding/logo.png",
  "logo_url": "https://api.alphalpgas.co.za/media/branding/logo.png",
  "favicon": "/media/branding/favicon.png",
  "favicon_url": "https://api.alphalpgas.co.za/media/branding/favicon.png",
  "phone": "074 454 5665",
  "email": "info@alphalpgas.co.za",
  ...
}
```

### Using Logo in Frontend:
```typescript
import { useCompanySettings } from '@/hooks/useCompanySettings'

function MyComponent() {
  const { settings, loading } = useCompanySettings()
  
  if (loading) return <div>Loading...</div>
  
  return (
    <img 
      src={settings?.logo_url || '/default-logo.png'} 
      alt={settings?.company_name}
    />
  )
}
```

---

## Creating Your Files

### Quick Favicon Creation:

**Option 1: Online Generator (Easiest)**
1. Go to https://favicon.io/favicon-generator/
2. Enter text: "AL" or your initials
3. Choose colors (orange/blue recommended)
4. Download and upload via admin

**Option 2: Convert Logo**
1. Go to https://favicon.io/favicon-converter/
2. Upload your logo
3. Download 32x32px version
4. Upload via admin

**Option 3: Use Canva**
1. Create 32x32px design
2. Export as PNG
3. Upload via admin

### Logo Design Tips:

**Good Logo Characteristics:**
- ✅ Transparent background (PNG format)
- ✅ Works on dark backgrounds
- ✅ Clear and readable
- ✅ Not too tall (40-50px height ideal for navbar)
- ✅ Professional appearance

**Avoid:**
- ❌ White/light background (clashes with dark navbar)
- ❌ Too much detail (hard to see when small)
- ❌ Very tall logos (takes too much space)
- ❌ Low resolution (looks pixelated)

---

## File Specifications

### Logo:
```
Format:     PNG (preferred), JPG, SVG
Size:       200x200px (square) or 300x100px (horizontal)
Max Size:   500KB
Background: Transparent (PNG)
Colors:     Should work on dark background
```

### Favicon:
```
Format:     PNG (preferred), ICO
Size:       32x32px or 64x64px
Max Size:   100KB
Design:     Simple, recognizable at small size
```

---

## Troubleshooting

### Logo not showing in navbar:
1. Check file uploaded successfully in admin
2. Clear browser cache (Ctrl+F5)
3. Verify file format is supported (PNG, JPG)
4. Check image isn't corrupted

### Favicon not updating:
1. **Clear browser cache completely:**
   - Chrome: Ctrl+Shift+Delete → Clear cached images
   - Firefox: Ctrl+Shift+Delete → Clear cache
2. **Hard refresh:** Ctrl+F5 or Ctrl+Shift+R
3. **Try incognito/private mode**
4. **Wait 1-2 minutes** (browsers cache favicons aggressively)
5. **Restart browser completely**

### File upload error:
1. Check file size (should be under 5MB)
2. Verify file is an image format
3. Try different image format (PNG instead of JPG)
4. Compress image if too large

### Logo too big/small in navbar:
1. Edit image to resize before uploading
2. Recommended: 40-50px height
3. Use image editor or online tool

---

## Production Deployment

### Railway Configuration:

Ensure these settings in Railway:

```env
# Backend (Django service)
MEDIA_URL=/media/
MEDIA_ROOT=/app/media

# Frontend (Next.js service)
NEXT_PUBLIC_API_URL=https://api.alphalpgas.co.za
```

### After Deployment:

1. Upload logo/favicon via production admin
2. Files stored in Railway's persistent storage
3. Accessible via media URL
4. Frontend fetches automatically

### Media Storage Options:

**Railway (Default):**
- ✅ Simple, built-in
- ✅ Good for small files
- ⚠️ Limited storage

**AWS S3 (Recommended for Production):**
- ✅ Unlimited storage
- ✅ CDN integration
- ✅ Automatic backups
- Requires configuration

**Cloudinary (Best for Images):**
- ✅ Image optimization
- ✅ CDN included
- ✅ Automatic resizing
- ✅ Free tier available

---

## Testing Checklist

After uploading:

- [ ] Logo appears in backend navbar
- [ ] Logo loads without errors
- [ ] Favicon shows in backend browser tab
- [ ] Favicon shows in frontend browser tab
- [ ] Logo accessible via API endpoint
- [ ] Files load on different browsers
- [ ] Files load on mobile devices
- [ ] Images look professional and clear

---

## Quick Reference

### Upload Location:
```
Django Admin → Core → Company Settings → Branding Section
```

### API Endpoint:
```
GET /api/accounting/settings/
```

### File Locations:
```
Backend:  /media/branding/logo.png
          /media/branding/favicon.png

Frontend: Loaded dynamically from API
```

### Frontend Hook:
```typescript
import { useCompanySettings } from '@/hooks/useCompanySettings'
```

---

## Need Help?

### Creating Professional Logo:
- **Fiverr**: $5-50 for custom logo
- **Canva**: Free templates and design tools
- **99designs**: Logo contests
- **Looka**: AI-powered logo maker

### Image Editing:
- **Canva**: https://canva.com (free, easy)
- **Photopea**: https://photopea.com (free Photoshop alternative)
- **GIMP**: Free desktop app

### Image Optimization:
- **TinyPNG**: https://tinypng.com
- **Squoosh**: https://squoosh.app
- **ImageOptim**: Mac app

---

**Your branding is now fully customizable through the admin panel! 🎨**

No need to manually add files to folders - just upload via Django admin and everything updates automatically.
