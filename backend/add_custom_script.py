#!/usr/bin/env python
"""
Add custom scripts directly via Python
Usage: python manage.py shell < add_custom_script.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alphalpgas.settings')
django.setup()

from core.models import CustomScript

# Your GTM Head Script
gtm_head_code = """<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-XXXXXXX');</script>
<!-- End Google Tag Manager -->"""

# Your GTM Body Script
gtm_body_code = """<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-XXXXXXX"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->"""

# Create GTM Head Script
try:
    script1 = CustomScript.objects.create(
        name="Google Tag Manager - Head",
        description="GTM head snippet for tracking",
        script_code=gtm_head_code,
        position="head_end",
        is_active=True,
        order=0,
        apply_to_all_pages=True
    )
    print(f"✅ Created: {script1.name} (ID: {script1.id})")
except Exception as e:
    print(f"❌ Error creating head script: {e}")

# Create GTM Body Script
try:
    script2 = CustomScript.objects.create(
        name="Google Tag Manager - Body",
        description="GTM body snippet (noscript)",
        script_code=gtm_body_code,
        position="body_start",
        is_active=True,
        order=0,
        apply_to_all_pages=True
    )
    print(f"✅ Created: {script2.name} (ID: {script2.id})")
except Exception as e:
    print(f"❌ Error creating body script: {e}")

print("\n🎉 Done! GTM scripts have been added.")
print("⚠️  Remember to replace 'GTM-XXXXXXX' with your actual GTM ID")
print("\nView/Edit scripts at: http://127.0.0.1:8000/admin/core/customscript/")
