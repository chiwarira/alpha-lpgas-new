from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Client


@login_required
def client_analytics(request, pk):
    """Comprehensive analytics dashboard for a specific client"""
    client = get_object_or_404(Client, pk=pk)
    analytics = client.get_analytics()
    
    return render(request, 'core/client_analytics.html', {
        'client': client,
        'analytics': analytics,
        'title': f'Analytics - {client.name}'
    })


@login_required
def client_analytics_api(request, pk):
    """API endpoint for client analytics data (for AJAX/charts)"""
    client = get_object_or_404(Client, pk=pk)
    analytics = client.get_analytics()
    
    # Convert Decimal to float for JSON serialization
    analytics['total_spent'] = float(analytics['total_spent'])
    analytics['total_paid'] = float(analytics['total_paid'])
    analytics['outstanding_balance'] = float(analytics['outstanding_balance'])
    analytics['avg_order_value'] = float(analytics['avg_order_value'])
    
    # Convert dates to strings
    if analytics['last_order_date']:
        analytics['last_order_date'] = analytics['last_order_date'].isoformat()
    if analytics['customer_since']:
        analytics['customer_since'] = analytics['customer_since'].isoformat()
    
    # Convert favorite products
    for product in analytics['favorite_products']:
        product['total_spent'] = float(product['total_spent'])
    
    return JsonResponse(analytics)
