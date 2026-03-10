"""Client lead time analysis view"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Client, Invoice
from datetime import timedelta


@login_required
def client_lead_time_analysis(request, client_id):
    """Detailed lead time analysis for a specific client"""
    client = get_object_or_404(Client, id=client_id)
    
    # Get all invoices for this client
    invoices = Invoice.objects.filter(client=client).order_by('issue_date')
    
    # Calculate intervals between consecutive invoices
    invoice_data = []
    previous_date = None
    
    for invoice in invoices:
        days_since_last = None
        if previous_date:
            days_since_last = (invoice.issue_date - previous_date).days
        
        invoice_data.append({
            'invoice': invoice,
            'issue_date': invoice.issue_date,
            'days_since_last': days_since_last,
        })
        
        previous_date = invoice.issue_date
    
    # Calculate statistics
    intervals = [item['days_since_last'] for item in invoice_data if item['days_since_last'] is not None]
    
    stats = {}
    if intervals:
        stats['avg_days'] = round(sum(intervals) / len(intervals), 1)
        stats['min_days'] = min(intervals)
        stats['max_days'] = max(intervals)
        stats['total_orders'] = len(invoices)
        
        # Calculate days since last order
        if invoices:
            from datetime import date
            last_order = invoices.last().issue_date
            stats['days_since_last_order'] = (date.today() - last_order).days
            stats['last_order_date'] = last_order
    
    context = {
        'client': client,
        'invoice_data': invoice_data,
        'stats': stats,
    }
    
    return render(request, 'core/client_lead_time_analysis.html', context)
