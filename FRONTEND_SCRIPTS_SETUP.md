# Frontend Custom Scripts Setup Guide

## Overview
Custom scripts (like GTM, Facebook Pixel, analytics) are now injected into your **Next.js frontend** via the Django backend API. Scripts are managed through the Django admin and automatically fetched and rendered on the frontend.

## Architecture

### Backend (Django)
- **Model**: `CustomScript` in `core/models.py`
- **Admin**: Manage scripts at `http://127.0.0.1:8000/admin/core/customscript/`
- **API Endpoint**: `http://127.0.0.1:8000/api/public/custom-scripts/`
- **Serializer**: `CustomScriptSerializer` in `core/serializers.py`
- **View**: `CustomScriptsView` in `core/views.py`

### Frontend (Next.js)
- **Layout**: `app/layout.tsx` - Fetches scripts on server-side
- **Components**:
  - `ScriptInjector.tsx` - Injects head scripts (head_start, head_end)
  - `CustomScripts.tsx` - Injects body scripts (body_start, body_end, footer)

## How It Works

1. **Django Admin**: You add/edit scripts via the admin interface
2. **API Call**: Next.js layout fetches scripts from Django API on each page load
3. **Server-Side Rendering**: Head scripts are injected during SSR
4. **Client-Side Injection**: Body scripts are injected after page hydration
5. **Page Targeting**: Scripts can be filtered by URL path

## Script Positions

### 1. Head Start
- **Location**: Beginning of `<head>` tag
- **Strategy**: `beforeInteractive` (loads before page becomes interactive)
- **Use for**: Critical scripts that must load first

### 2. Head End
- **Location**: End of `<head>` tag, before closing `</head>`
- **Strategy**: `afterInteractive` (loads after page becomes interactive)
- **Use for**: GTM head snippet, analytics, tracking pixels

### 3. Body Start
- **Location**: Beginning of `<body>` tag
- **Use for**: GTM noscript tag, above-the-fold tracking

### 4. Body End
- **Location**: End of `<body>` tag, after main content
- **Use for**: Non-critical scripts, deferred loading

### 5. Footer
- **Location**: Just before closing `</body>` tag
- **Use for**: Footer scripts, chat widgets

## Adding Scripts

### Method 1: Django Admin (Recommended for Editing)
1. Go to `http://127.0.0.1:8000/admin/core/customscript/`
2. Click "Add Custom Script"
3. Fill in the form:
   - **Name**: Descriptive name (e.g., "Google Tag Manager - Head")
   - **Description**: What the script does
   - **Script Code**: Paste your complete script (including `<script>` tags)
   - **Position**: Choose from dropdown
   - **Is Active**: Check to enable
   - **Order**: Lower numbers load first (0, 1, 2, etc.)
   - **Apply to all pages**: Check for site-wide scripts
4. Click "Save"

### Method 2: Python Script (Recommended for Initial Setup)
Use the provided script to add GTM:

```bash
cd backend
python add_custom_script.py
```

This creates both GTM head and body scripts automatically.

## Current Scripts in Database

Based on the API response, you currently have:

1. **Google Tag Manager - Head** (ID: 1)
   - Position: `head_end`
   - Status: Active
   - Contains: GTM initialization script

2. **Google Tag Manager - Body** (ID: 2)
   - Position: `body_start`
   - Status: Active
   - Contains: GTM noscript fallback

## Updating GTM Container ID

To use your actual GTM container ID:

1. Go to `http://127.0.0.1:8000/admin/core/customscript/`
2. Click on "Google Tag Manager - Head"
3. Find `GTM-XXXXXXX` in the script code
4. Replace with your actual GTM ID (e.g., `GTM-ABC1234`)
5. Click "Save"
6. Repeat for "Google Tag Manager - Body"

## Testing & Verification

### 1. Check API Response
```bash
curl http://127.0.0.1:8000/api/public/custom-scripts/?path=/
```

Should return JSON with scripts grouped by position.

### 2. Check Frontend Source
1. Open `http://localhost:3001` (or your frontend URL)
2. Right-click → "View Page Source"
3. Search for "Google Tag Manager"
4. Verify scripts appear in correct positions:
   - GTM head script in `<head>` section
   - GTM noscript in `<body>` section

### 3. Check Browser Console
1. Open DevTools (F12)
2. Go to Console tab
3. Look for any errors related to script loading
4. Check Network tab for API call to `/api/public/custom-scripts/`

### 4. Test GTM (if using Google Tag Manager)
1. Open Google Tag Manager
2. Click "Preview" mode
3. Enter your site URL
4. Verify container connects and tags fire

## Page Targeting

Scripts can be targeted to specific pages or excluded from certain pages:

### Apply to All Pages
- **Apply to all pages**: ✅ Checked
- **Specific pages**: Leave blank
- **Exclude pages**: Leave blank

### Specific Pages Only
- **Apply to all pages**: ❌ Unchecked
- **Specific pages**: `/products/, /checkout/, /cart/`
- **Exclude pages**: Leave blank

### Exclude Admin/Driver Pages
- **Apply to all pages**: ✅ Checked
- **Specific pages**: Leave blank
- **Exclude pages**: `/admin/, /driver/, /accounting/`

## API Endpoint Details

### Endpoint
```
GET /api/public/custom-scripts/
```

### Query Parameters
- `path` (optional): Current page path for filtering (e.g., `?path=/products/`)

### Response Format
```json
{
  "head_start": [
    {
      "id": 1,
      "name": "Script Name",
      "script_code": "<script>...</script>",
      "position": "head_start",
      "order": 0
    }
  ],
  "head_end": [...],
  "body_start": [...],
  "body_end": [...],
  "footer": [...]
}
```

### CORS Configuration
The endpoint is publicly accessible (no authentication required) and CORS is configured in Django settings.

## Frontend Components

### ScriptInjector Component
**File**: `components/ScriptInjector.tsx`

Handles head scripts (`head_start`, `head_end`):
- Uses Next.js `<Script>` component
- Applies appropriate loading strategy
- Extracts script content from HTML tags
- Handles both inline and external scripts

### CustomScripts Component
**File**: `components/CustomScripts.tsx`

Handles body scripts (`body_start`, `body_end`, `footer`):
- Client-side component (uses `'use client'`)
- Fetches scripts based on current pathname
- Dynamically injects scripts into DOM
- Re-executes scripts on route changes

### Layout Integration
**File**: `app/layout.tsx`

- Fetches scripts server-side via `getCustomScripts()`
- Passes head scripts to `ScriptInjector`
- Renders `CustomScripts` component in body
- Caching disabled for fresh script data

## Common Scripts Examples

### Google Tag Manager
Already added via `add_custom_script.py`. Just update the GTM ID.

### Facebook Pixel
**Position**: `head_end`
```html
<!-- Facebook Pixel Code -->
<script>
!function(f,b,e,v,n,t,s)
{if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};
if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];
s.parentNode.insertBefore(t,s)}(window, document,'script',
'https://connect.facebook.net/en_US/fbevents.js');
fbq('init', 'YOUR_PIXEL_ID');
fbq('track', 'PageView');
</script>
<noscript><img height="1" width="1" style="display:none"
src="https://www.facebook.com/tr?id=YOUR_PIXEL_ID&ev=PageView&noscript=1"
/></noscript>
```

### Google Analytics 4
**Position**: `head_end`
```html
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

### Hotjar
**Position**: `head_end`
```html
<!-- Hotjar Tracking Code -->
<script>
    (function(h,o,t,j,a,r){
        h.hj=h.hj||function(){(h.hj.q=h.hj.q||[]).push(arguments)};
        h._hjSettings={hjid:YOUR_HOTJAR_ID,hjsv:6};
        a=o.getElementsByTagName('head')[0];
        r=o.createElement('script');r.async=1;
        r.src=t+h._hjSettings.hjid+j+h._hjSettings.hjsv;
        a.appendChild(r);
    })(window,document,'https://static.hotjar.com/c/hotjar-','.js?sv=');
</script>
```

## Troubleshooting

### Scripts Not Appearing on Frontend

1. **Check API Response**
   ```bash
   curl http://127.0.0.1:8000/api/public/custom-scripts/?path=/
   ```
   - Verify scripts are returned in JSON
   - Check if scripts are active (`is_active: true`)

2. **Check Browser Console**
   - Open DevTools (F12) → Console
   - Look for errors related to script fetching
   - Check Network tab for API call status

3. **Check Page Source**
   - Right-click → View Page Source
   - Search for your script name or GTM
   - If not found, check if frontend is fetching from correct API URL

4. **Verify Environment Variables**
   - Check `frontend/.env.local`
   - Ensure `NEXT_PUBLIC_API_URL=http://localhost:8000/api`

5. **Clear Next.js Cache**
   ```bash
   cd frontend
   rm -rf .next
   npm run dev
   ```

### Scripts Loading in Wrong Order

- Adjust the **Order** field in Django admin
- Lower numbers = higher priority (0 loads before 1, etc.)
- Scripts with same order are sorted alphabetically

### Scripts Not Executing

1. **Check Browser Console** for JavaScript errors
2. **Verify Script Syntax** in Django admin
3. **Test Script Independently** in browser console
4. **Check CSP Headers** if using Content Security Policy

### API Returning 404

1. **Verify URL**: Should be `/api/public/custom-scripts/`
2. **Check Django URLs**: Ensure `core.urls.public` is included
3. **Restart Django Server**:
   ```bash
   cd backend
   python manage.py runserver
   ```

### Frontend Not Updating

1. **Hard Refresh**: Ctrl + Shift + R (Windows) or Cmd + Shift + R (Mac)
2. **Clear Browser Cache**
3. **Restart Next.js Dev Server**:
   ```bash
   cd frontend
   npm run dev
   ```

## Production Deployment

### Environment Variables
Ensure production environment has:
```env
NEXT_PUBLIC_API_URL=https://your-api-domain.com/api
```

### Caching Strategy
Current setup uses `cache: 'no-store'` for fresh data. For production, consider:
- Implementing revalidation intervals
- Using ISR (Incremental Static Regeneration)
- Adding cache headers on API endpoint

### Security Considerations
- Scripts are fetched server-side (secure)
- API endpoint is public but read-only
- Validate script content before adding to admin
- Use HTTPS in production

## Files Modified/Created

### Backend
- ✅ `core/models.py` - Added `CustomScript` model
- ✅ `core/admin.py` - Added `CustomScriptAdmin`
- ✅ `core/serializers.py` - Added `CustomScriptSerializer`
- ✅ `core/views.py` - Added `CustomScriptsView`
- ✅ `core/urls/public.py` - Created public API routes
- ✅ `alphalpgas/urls.py` - Added public API path
- ✅ `add_custom_script.py` - Helper script to add GTM

### Frontend
- ✅ `app/layout.tsx` - Updated to fetch and inject scripts
- ✅ `components/ScriptInjector.tsx` - Head script injection
- ✅ `components/CustomScripts.tsx` - Body script injection

### Documentation
- ✅ `CUSTOM_SCRIPTS_GUIDE.md` - General guide
- ✅ `FRONTEND_SCRIPTS_SETUP.md` - This file

## Quick Start Checklist

- [x] Django model created and migrated
- [x] GTM scripts added to database
- [x] API endpoint created and tested
- [x] Frontend components created
- [x] Layout updated to use components
- [ ] Update GTM container ID with your actual ID
- [ ] Test on frontend (`http://localhost:3001`)
- [ ] Verify scripts in page source
- [ ] Test GTM preview mode (if using GTM)

## Support & Next Steps

1. **Update GTM ID**: Replace `GTM-XXXXXXX` with your actual container ID
2. **Test Frontend**: Visit `http://localhost:3001` and check page source
3. **Add More Scripts**: Use Django admin to add Facebook Pixel, GA4, etc.
4. **Configure Page Targeting**: Set specific pages or exclusions as needed

---

**Last Updated**: December 29, 2025  
**Version**: 1.0  
**Status**: ✅ Fully Implemented and Ready for Testing
