# Favicon Setup Instructions

## Current Status
The site is currently using `alpha-lpgas-logo.svg` as the favicon.

## To Add a Proper Favicon

### Option 1: Quick Fix - Use Online Converter
1. Go to https://favicon.io/favicon-converter/
2. Upload your `alpha-lpgas-logo.svg` file
3. Download the generated files
4. Copy `favicon.ico` to this folder (`frontend/public/`)
5. Restart the Next.js dev server

### Option 2: Create Custom Favicon
1. Go to https://favicon.io/favicon-generator/
2. Design your favicon (text or icon)
3. Download the generated files
4. Copy `favicon.ico` to this folder
5. Restart the Next.js dev server

### Option 3: Manual Creation
1. Create a 32x32px or 64x64px PNG image
2. Save it as `favicon.png` in this folder
3. Update `app/layout.tsx` to use `favicon.png` instead of SVG

## Files Needed
Place these files in `frontend/public/`:
- `favicon.ico` (standard favicon)
- `favicon-16x16.png` (optional)
- `favicon-32x32.png` (optional)
- `apple-touch-icon.png` (optional, for iOS)

## After Adding Favicon
1. Restart dev server: `npm run dev`
2. Clear browser cache (Ctrl+Shift+Delete)
3. Hard refresh (Ctrl+F5)
4. Check in incognito mode

The favicon should now appear in browser tabs!
