from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(['GET'])
def api_root(request, format=None):
    """
    API Root - Alpha LPGas Platform
    """
    return Response({
        'message': 'Welcome to Alpha LPGas API',
        'version': '1.0.0',
        'endpoints': {
            'documentation': reverse('swagger-ui', request=request, format=format),
            'schema': reverse('schema', request=request, format=format),
            'authentication': {
                'register': request.build_absolute_uri('/api/auth/register/'),
                'login': request.build_absolute_uri('/api/auth/login/'),
                'google_login': request.build_absolute_uri('/api/auth/google/'),
                'token_refresh': request.build_absolute_uri('/api/auth/token/refresh/'),
            },
            'accounting': {
                'clients': request.build_absolute_uri('/api/accounting/clients/'),
                'products': request.build_absolute_uri('/api/accounting/products/'),
                'quotes': request.build_absolute_uri('/api/accounting/quotes/'),
                'invoices': request.build_absolute_uri('/api/accounting/invoices/'),
                'payments': request.build_absolute_uri('/api/accounting/payments/'),
                'credit_notes': request.build_absolute_uri('/api/accounting/credit-notes/'),
                'settings': request.build_absolute_uri('/api/accounting/settings/'),
            }
        }
    })
