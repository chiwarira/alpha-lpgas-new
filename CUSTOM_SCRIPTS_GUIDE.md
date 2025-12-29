# Custom Scripts Management Guide

## Overview
The Custom Scripts feature allows you to inject custom code (like Google Tag Manager, Facebook Pixel, analytics scripts, etc.) into different sections of your Django site without modifying template files.

## Features
- ✅ Inject scripts into 5 different positions: head_start, head_end, body_start, body_end, footer
- ✅ Enable/disable scripts without deleting them
- ✅ Control script order with priority settings
- ✅ Target specific pages or apply to all pages
- ✅ Exclude specific pages from script injection
- ✅ Full admin interface for easy management

## Accessing the Admin Interface

1. Navigate to Django Admin: `http://127.0.0.1:8000/admin/`
2. Look for **Custom Scripts** under the Core section
3. Click to view, add, or edit custom scripts

## Script Positions

### 1. Head Start
- **Position**: Beginning of `<head>` tag
- **Use for**: Critical scripts that must load first (e.g., GTM head snippet)

### 2. Head End
- **Position**: End of `<head>` tag, before closing `</head>`
- **Use for**: Analytics, tracking pixels, SEO scripts

### 3. Body Start
- **Position**: Beginning of `<body>` tag
- **Use for**: GTM body snippet (noscript), above-the-fold tracking

### 4. Body End
- **Position**: End of `<body>` tag, after main content
- **Use for**: Non-critical scripts, chat widgets

### 5. Footer
- **Position**: Just before closing `</body>` tag
- **Use for**: Footer scripts, deferred loading scripts

## Adding Google Tag Manager (GTM)

### Step 1: Add GTM Head Snippet
1. Go to Admin → Custom Scripts → Add Custom Script
2. Fill in the form:
   - **Name**: `Google Tag Manager - Head`
   - **Description**: `GTM head snippet for tracking`
   - **Script Code**: Paste your GTM head code:
     ```html
     <!-- Google Tag Manager -->
     <script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
     new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
     j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
     'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
     })(window,document,'script','dataLayer','GTM-XXXXXXX');</script>
     <!-- End Google Tag Manager -->
     ```
   - **Position**: `Head End (End of <head>)`
   - **Is Active**: ✅ Checked
   - **Order**: `0`
   - **Apply to all pages**: ✅ Checked
3. Click **Save**

### Step 2: Add GTM Body Snippet
1. Add another Custom Script
2. Fill in the form:
   - **Name**: `Google Tag Manager - Body`
   - **Description**: `GTM body snippet (noscript)`
   - **Script Code**: Paste your GTM body code:
     ```html
     <!-- Google Tag Manager (noscript) -->
     <noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-XXXXXXX"
     height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
     <!-- End Google Tag Manager (noscript) -->
     ```
   - **Position**: `Body Start (Beginning of <body>)`
   - **Is Active**: ✅ Checked
   - **Order**: `0`
   - **Apply to all pages**: ✅ Checked
3. Click **Save**

## Page Targeting Examples

### Apply to Specific Pages Only
- **Apply to all pages**: ❌ Unchecked
- **Specific pages**: `/products/, /checkout/, /cart/`
- **Exclude pages**: Leave blank

This will only show the script on product, checkout, and cart pages.

### Apply to All Pages Except Admin
- **Apply to all pages**: ✅ Checked
- **Specific pages**: Leave blank
- **Exclude pages**: `/admin/, /driver/`

This will show the script everywhere except admin and driver portal pages.

### E-commerce Pages Only
- **Apply to all pages**: ❌ Unchecked
- **Specific pages**: `/products/, /checkout/, /cart/, /order/`
- **Exclude pages**: Leave blank

## Other Common Scripts

### Facebook Pixel
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
<!-- End Facebook Pixel Code -->
```
**Position**: Head End

### Google Analytics 4
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
**Position**: Head End

### Hotjar
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
**Position**: Head End

## Best Practices

1. **Test Before Enabling**: Create scripts as inactive first, test them, then enable
2. **Use Descriptive Names**: Make it easy to identify scripts later
3. **Set Proper Order**: Lower numbers load first (0, 1, 2, etc.)
4. **Exclude Admin Pages**: Usually you don't want tracking on admin pages
5. **Monitor Performance**: Too many scripts can slow down your site
6. **Document Your Scripts**: Use the description field to note what each script does

## Troubleshooting

### Scripts Not Appearing
1. Check if the script is **Active** (checkbox enabled)
2. Verify the **Position** is correct
3. Check **Page Targeting** settings
4. Clear browser cache and reload
5. Check browser console for errors

### Scripts Loading in Wrong Order
- Adjust the **Order** field (lower numbers = higher priority)
- Scripts with the same order are sorted alphabetically by name

### Scripts Conflicting
- Try different positions (e.g., move from head_end to body_end)
- Check for JavaScript errors in browser console
- Ensure scripts don't have duplicate IDs

## Technical Details

### Template Tags Used
The system uses Django template tags to render scripts:
```django
{% load custom_scripts %}
{% render_custom_scripts 'head_start' %}
{% render_custom_scripts 'head_end' %}
{% render_custom_scripts 'body_start' %}
{% render_custom_scripts 'body_end' %}
{% render_custom_scripts 'footer' %}
```

### Database Model
Scripts are stored in the `CustomScript` model with fields:
- name, description, script_code
- position, is_active, order
- apply_to_all_pages, specific_pages, exclude_pages
- created_at, updated_at, created_by

### Templates Updated
- `templates/core/base.html` (main accounting interface)
- `templates/core/driver_portal/base.html` (driver portal)

## Support

If you need help or encounter issues:
1. Check the Django admin logs
2. Review browser console for JavaScript errors
3. Verify script syntax is correct
4. Test scripts on a staging environment first

---

**Created**: December 29, 2025  
**Version**: 1.0
