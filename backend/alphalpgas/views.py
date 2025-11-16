from django.http import HttpResponse
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


def home(request):
    """
    Simple home view for root URL
    """
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Alpha LPGas - Backend API</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 { color: #333; }
            a {
                color: #007bff;
                text-decoration: none;
            }
            a:hover { text-decoration: underline; }
            .links {
                margin-top: 30px;
            }
            .links a {
                display: block;
                margin: 10px 0;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 5px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Alpha LPGas Backend API</h1>
            <p>Welcome to the Alpha LPGas backend server. This is the API backend for the Alpha LPGas e-commerce platform.</p>
            
            <div class="links">
                <h3>Available Services:</h3>
                <a href="/api/">📡 API Root</a>
                <a href="/api/docs/">📚 API Documentation (Swagger)</a>
                <a href="/admin/">🔧 Django Admin</a>
                <a href="/accounting/">💼 Accounting Dashboard</a>
                <a href="/driver/">🚚 Driver Portal</a>
                <a href="/cms/">📝 CMS Admin (Wagtail)</a>
            </div>
            
            <p style="margin-top: 30px; color: #666;">
                Frontend: <a href="https://front-end-production-b210.up.railway.app" target="_blank">https://front-end-production-b210.up.railway.app</a>
            </p>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)
