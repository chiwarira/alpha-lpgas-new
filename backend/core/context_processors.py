"""Context processors for making data available to all templates"""
from .models import CompanySettings, CustomScript


def company_settings(request):
    """Make company settings available to all templates"""
    try:
        settings = CompanySettings.load()
        return {'company_settings': settings}
    except:
        return {'company_settings': None}


def custom_scripts(request):
    """Make custom scripts available to all templates, grouped by placement"""
    try:
        scripts = CustomScript.objects.filter(is_active=True, apply_to_backend=True)
        return {
            'custom_scripts_head': scripts.filter(placement='head'),
            'custom_scripts_body_start': scripts.filter(placement='body_start'),
            'custom_scripts_body_end': scripts.filter(placement='body_end'),
        }
    except:
        return {
            'custom_scripts_head': [],
            'custom_scripts_body_start': [],
            'custom_scripts_body_end': [],
        }
