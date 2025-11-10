"""Context processors for making data available to all templates"""
from .models import CompanySettings


def company_settings(request):
    """Make company settings available to all templates"""
    try:
        settings = CompanySettings.load()
        return {'company_settings': settings}
    except:
        return {'company_settings': None}
