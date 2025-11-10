# 🎨 Branding Guide - Logo & Favicon Setup

## Overview

You can now customize your site's branding by uploading:
- **Company Logo** - Appears in the navigation bar and can be used on invoices
- **Favicon** - Small icon that appears in browser tabs

---

## How to Upload Logo & Favicon

### Step 1: Access Company Settings

1. Log in to Django admin: `http://localhost:8000/admin/` (or your production URL)
2. Go to **Core** → **Company Settings**
3. Click on the existing Company Settings entry

### Step 2: Upload Branding Assets

Scroll to the **"Branding"** section:

#### Upload Logo:
1. Click **"Choose File"** next to **Logo**
2. Select your logo file (PNG recommended)
3. **Recommended specs:**
   - Format: PNG with transparent background
   - Size: 200x200px or similar square/rectangular
   - File size: Under 500KB
   - Colors: Should work on dark background (navbar is dark)

#### Upload Favicon:
1. Click **"Choose File"** next to **Favicon**
2. Select your favicon file
3. **Recommended specs:**
   - Format: PNG or ICO
   - Size: 32x32px or 64x64px
   - File size: Under 100KB
   - Simple design (looks good when small)

### Step 3: Save

Click **"Save"** at the bottom of the page.

---

## Where Logo & Favicon Appear

### Logo Appears:
- ✅ **Navigation bar** (top left) - Replaces the calculator icon
- ✅ **API responses** - Available via `/api/accounting/settings/`
- ✅ Can be used in **invoices** and **quotes** (future enhancement)

### Favicon Appears:
- ✅ **Browser tabs** - Next to page title
- ✅ **Bookmarks** - When users bookmark your site
- ✅ **Browser history**
- ✅ **Mobile home screen** - When added to phone

---

## Creating Your Favicon

### Option 1: Online Favicon Generator

Use free online tools:
- https://favicon.io/favicon-converter/
- https://realfavicongenerator.net/
- https://www.favicon-generator.org/

**Steps:**
1. Upload your logo
2. Tool generates multiple sizes
3. Download the 32x32px or 64x64px version
4. Upload to Django admin

### Option 2: Use Existing Logo

If you have a square logo:
1. Resize to 32x32px or 64x64px
2. Save as PNG
3. Upload to Django admin

### Option 3: Design Custom Favicon

Use tools like:
- **Canva** (free, easy)
- **Figma** (free, professional)
- **Photoshop** (professional)

**Tips:**
- Keep it simple (looks good when small)
- Use 1-2 colors
- Make it recognizable
- Test how it looks at small size

---

## Logo Design Tips

### For Navigation Bar:

**Good Logo Characteristics:**
- ✅ Works on dark background
- ✅ Horizontal or square shape
- ✅ Clear and readable
- ✅ Not too tall (40px height is ideal)
- ✅ Transparent background (PNG)

**Avoid:**
- ❌ Very tall/vertical logos (will be too big)
- ❌ White background (clashes with dark navbar)
- ❌ Too much detail (hard to see when small)
- ❌ Very wide logos (takes too much space)

---

## File Formats

### Recommended:
- **PNG** - Best for logos with transparency
- **ICO** - Traditional favicon format
- **SVG** - Scalable, but PNG is safer

### Supported:
- PNG ✅
- JPG ✅ (but no transparency)
- ICO ✅
- GIF ✅
- WEBP ✅

---

## API Access

Logo and favicon are available via API:

### Endpoint:
```
GET /api/accounting/settings/
```

### Response:
```json
{
  "id": 1,
  "company_name": "Alpha LPGas",
  "logo": "/media/branding/logo.png",
  "logo_url": "https://api.alphalpgas.co.za/media/branding/logo.png",
  "favicon": "/media/branding/favicon.png",
  "favicon_url": "https://api.alphalpgas.co.za/media/branding/favicon.png",
  ...
}
```

### Usage in Frontend:
```javascript
// Fetch company settings
const response = await fetch('https://api.alphalpgas.co.za/api/accounting/settings/');
const settings = await response.json();

// Use logo
<img src={settings.logo_url} alt={settings.company_name} />

// Use favicon
<link rel="icon" href={settings.favicon_url} />
```

---

## Troubleshooting

### Logo not showing in navbar:
- Check file was uploaded successfully
- Verify file format is supported
- Clear browser cache (Ctrl+F5)
- Check file permissions on server

### Favicon not showing:
- Clear browser cache completely
- Try hard refresh (Ctrl+Shift+R)
- Check in incognito/private mode
- Wait a few minutes (browsers cache favicons)

### File upload error:
- Check file size (should be under 5MB)
- Verify file format is image
- Check media folder permissions
- Ensure `MEDIA_ROOT` and `MEDIA_URL` configured

### Logo too big/small:
- Resize image before uploading
- Recommended height: 40-50px for navbar
- Use image editing tool to resize

---

## Production Deployment

### Railway Setup:

When deploying to Railway, ensure:

1. **Media files are configured:**
   ```env
   MEDIA_URL=/media/
   ```

2. **Static files collected:**
   ```bash
   railway run python manage.py collectstatic
   ```

3. **Upload logo/favicon via admin:**
   - Go to `https://api.alphalpgas.co.za/admin/`
   - Upload branding assets
   - Files stored in Railway's persistent storage

### Media Storage:

For production, consider:
- **Railway** - Built-in storage (simple, good for small files)
- **AWS S3** - Scalable cloud storage (for larger sites)
- **Cloudinary** - Image optimization + CDN (recommended)

---

## Example Logo Sizes

### For Different Uses:

```
Navbar Logo:        200x50px  (horizontal)
                    or 100x100px (square)

Favicon:            32x32px   (standard)
                    64x64px   (high-res)
                    
Invoice Header:     300x100px (future use)

Email Header:       600x200px (future use)
```

---

## Quick Checklist

Before uploading:

- [ ] Logo is PNG with transparent background
- [ ] Logo dimensions are appropriate (not too big)
- [ ] Logo works on dark background
- [ ] Favicon is 32x32px or 64x64px
- [ ] Favicon is simple and recognizable
- [ ] Files are under 1MB each
- [ ] Tested how they look at actual size

---

## Need Help?

### Creating Logo:
- Hire designer on Fiverr ($5-50)
- Use Canva templates (free)
- Ask AI (DALL-E, Midjourney)

### Converting Formats:
- https://cloudconvert.com/
- https://convertio.co/
- Photoshop/GIMP

### Optimizing Images:
- https://tinypng.com/ (compress PNG)
- https://squoosh.app/ (Google's tool)
- https://imageoptim.com/ (Mac app)

---

**Your branding is now customizable! 🎨**

Upload your logo and favicon to make the site truly yours.
