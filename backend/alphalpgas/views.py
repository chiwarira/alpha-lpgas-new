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
    # Determine frontend URL based on environment
    host = request.get_host()
    if 'localhost' in host or '127.0.0.1' in host:
        frontend_url = 'http://localhost:3000'
    elif 'staging' in host or 'dev' in host:
        frontend_url = 'https://alpha-lpgas-frontend-dev.up.railway.app'
    else:
        frontend_url = 'https://www.alphalpgas.co.za'
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Alpha LPGas - Backend API</title>
        <style>
            * {{
                box-sizing: border-box;
            }}
            body {{
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background: #f5f5f5;
            }}
            .container {{
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1 {{ 
                color: #333;
                font-size: 1.8rem;
                margin-bottom: 15px;
            }}
            h3 {{
                font-size: 1.2rem;
                margin-bottom: 15px;
            }}
            p {{
                line-height: 1.6;
                font-size: 0.95rem;
            }}
            a {{
                color: #007bff;
                text-decoration: none;
            }}
            a:hover {{ text-decoration: underline; }}
            .links {{
                margin-top: 25px;
            }}
            .links a {{
                display: block;
                margin: 10px 0;
                padding: 12px 15px;
                background: #f8f9fa;
                border-radius: 5px;
                font-size: 0.95rem;
            }}
            
            /* Mobile responsive */
            @media (max-width: 768px) {{
                body {{
                    padding: 10px;
                }}
                .container {{
                    padding: 20px;
                }}
                h1 {{
                    font-size: 1.5rem;
                }}
                h3 {{
                    font-size: 1.1rem;
                }}
                p {{
                    font-size: 0.9rem;
                }}
                .links a {{
                    padding: 10px 12px;
                    font-size: 0.9rem;
                }}
            }}
            
            @media (max-width: 480px) {{
                body {{
                    padding: 5px;
                }}
                .container {{
                    padding: 15px;
                }}
                h1 {{
                    font-size: 1.3rem;
                }}
                .links a {{
                    padding: 8px 10px;
                    font-size: 0.85rem;
                }}
            }}
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
                Frontend: <a href="{frontend_url}" target="_blank">{frontend_url}</a>
            </p>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)
