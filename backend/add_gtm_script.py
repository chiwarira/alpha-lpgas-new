"""
Quick script to add GTM via Django shell
Run with: python manage.py shell < add_gtm_script.py
"""

from core.models import CustomScript

# Add GTM Head Script
gtm_head = CustomScript.objects.create(
    name="Google Tag Manager - Head",
    description="GTM head snippet for tracking",
    script_code="""<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-XXXXXXX');</script>
<!-- End Google Tag Manager -->""",
    position="head_end",
    is_active=True,
    order=0,
    apply_to_all_pages=True
)

print(f"✅ Created: {gtm_head.name}")

# Add GTM Body Script
gtm_body = CustomScript.objects.create(
    name="Google Tag Manager - Body",
    description="GTM body snippet (noscript)",
    script_code="""<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-XXXXXXX"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->""",
    position="body_start",
    is_active=True,
    order=0,
    apply_to_all_pages=True
)

print(f"✅ Created: {gtm_body.name}")
print("\n🎉 GTM scripts added successfully!")
print("⚠️  Remember to replace 'GTM-XXXXXXX' with your actual GTM ID")
print("\nYou can edit these scripts in the admin at:")
print("http://127.0.0.1:8000/admin/core/customscript/")
