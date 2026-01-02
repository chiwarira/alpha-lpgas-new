from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Sum
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import date, timedelta
from .models import Client, Product, Quote, QuoteItem, Invoice, InvoiceItem, Payment, CreditNote, Order, Driver
from .forms import (
    ClientForm, ProductForm, QuoteForm, QuoteItemFormSet,
    InvoiceForm, InvoiceItemFormSet, PaymentForm,
    CreditNoteForm, CreditNoteItemFormSet, CompanySettingsForm
)


# Client Views
@login_required
def client_list(request):
    """List all clients with search and sort functionality"""
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', '-created_at')
    
    # Valid sort fields
    valid_sorts = ['customer_id', '-customer_id', 'name', '-name', 'email', '-email', 
                   'phone', '-phone', 'city', '-city', 'is_active', '-is_active',
                   'created_at', '-created_at']
    if sort_by not in valid_sorts:
        sort_by = '-created_at'
    
    clients = Client.objects.all()
    
    if search_query:
        from django.db.models import Q
        clients = clients.filter(
            Q(name__icontains=search_query) |
            Q(customer_id__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(address__icontains=search_query)
        )
    
    clients = clients.order_by(sort_by)
    
    return render(request, 'core/client_list.html', {
        'clients': clients,
        'search_query': search_query,
        'sort_by': sort_by,
    })


@login_required
def client_create(request):
    """Create a new client"""
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            messages.success(request, f'Client "{client.name}" created successfully!')
            return redirect('accounting_forms:client_detail', pk=client.pk)
    else:
        form = ClientForm()
    
    return render(request, 'core/client_form.html', {
        'form': form,
        'title': 'Create Client'
    })


@login_required
def client_edit(request, pk):
    """Edit an existing client"""
    client = get_object_or_404(Client, pk=pk)
    
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            client = form.save()
            messages.success(request, f'Client "{client.name}" updated successfully!')
            return redirect('accounting_forms:client_detail', pk=client.pk)
    else:
        form = ClientForm(instance=client)
    
    return render(request, 'core/client_form.html', {
        'form': form,
        'title': f'Edit Client: {client.name}',
        'client': client
    })


@login_required
def client_detail(request, pk):
    """View client details"""
    client = get_object_or_404(Client, pk=pk)
    quotes = client.quotes.all().order_by('-issue_date')[:5]
    invoices = client.invoices.all().order_by('-issue_date')[:5]
    
    return render(request, 'core/client_detail.html', {
        'client': client,
        'quotes': quotes,
        'invoices': invoices
    })


@login_required
def client_statement(request, pk):
    """Generate client statement for a date range"""
    client = get_object_or_404(Client, pk=pk)
    
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        action = request.POST.get('action', 'preview')
        
        if start_date and end_date:
            from datetime import datetime
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            if action == 'download':
                # Generate PDF statement
                from .pdf_generator import generate_client_statement_pdf
                pdf = generate_client_statement_pdf(client, start_date, end_date)
                
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="statement_{client.customer_id}_{start_date}_{end_date}.pdf"'
                return response
            else:
                # Preview statement
                return redirect('accounting_forms:client_statement_preview', pk=pk, start_date=start_date.strftime('%Y-%m-%d'), end_date=end_date.strftime('%Y-%m-%d'))
    
    # Default date range: current month
    from datetime import date
    today = date.today()
    start_of_month = date(today.year, today.month, 1)
    
    return render(request, 'core/client_statement_form.html', {
        'client': client,
        'default_start': start_of_month,
        'default_end': today
    })


@login_required
def client_statement_preview(request, pk, start_date, end_date):
    """Preview client statement before downloading"""
    from datetime import datetime
    from decimal import Decimal
    
    client = get_object_or_404(Client, pk=pk)
    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Calculate balance brought forward
    balance_bf_invoices = Invoice.objects.filter(
        client=client,
        issue_date__lt=start_date
    )
    
    balance_bf = Decimal('0.00')
    for inv in balance_bf_invoices:
        balance_bf += inv.balance
    
    # Get all transactions in the period
    invoices = Invoice.objects.filter(
        client=client,
        issue_date__gte=start_date,
        issue_date__lte=end_date
    ).order_by('issue_date')
    
    payments = Payment.objects.filter(
        invoice__client=client,
        payment_date__gte=start_date,
        payment_date__lte=end_date
    ).order_by('payment_date')
    
    credit_notes = CreditNote.objects.filter(
        client=client,
        issue_date__gte=start_date,
        issue_date__lte=end_date
    ).order_by('issue_date')
    
    # Combine and sort all transactions
    transactions = []
    
    for inv in invoices:
        transactions.append({
            'date': inv.issue_date,
            'type': 'invoice',
            'description': 'Invoice',
            'reference': inv.invoice_number,
            'debit': inv.total_amount,
            'credit': Decimal('0.00'),
            'object': inv
        })
    
    for pmt in payments:
        transactions.append({
            'date': pmt.payment_date,
            'type': 'payment',
            'description': f'Payment - {pmt.get_payment_method_display()}',
            'reference': pmt.payment_number,
            'debit': Decimal('0.00'),
            'credit': pmt.amount,
            'object': pmt
        })
    
    for cn in credit_notes:
        transactions.append({
            'date': cn.issue_date,
            'type': 'credit_note',
            'description': 'Credit Note',
            'reference': cn.credit_note_number,
            'debit': Decimal('0.00'),
            'credit': cn.total_amount,
            'object': cn
        })
    
    # Sort by date
    transactions.sort(key=lambda x: x['date'])
    
    # Calculate running balance
    running_balance = balance_bf
    for trans in transactions:
        running_balance += trans['debit'] - trans['credit']
        trans['balance'] = running_balance
    
    # Calculate totals
    total_invoices = sum(t['debit'] for t in transactions)
    total_credits = sum(t['credit'] for t in transactions)
    
    # Calculate aging buckets
    from datetime import date, timedelta
    today = date.today()
    
    aging = {
        'current': Decimal('0.00'),
        'days_1_30': Decimal('0.00'),
        'days_31_60': Decimal('0.00'),
        'days_61_90': Decimal('0.00'),
        'over_90': Decimal('0.00'),
        'credit': Decimal('0.00')
    }
    
    # Get all unpaid/partially paid invoices for this client
    unpaid_invoices = Invoice.objects.filter(
        client=client
    ).exclude(status__in=['paid', 'cancelled', 'draft'])
    
    for invoice in unpaid_invoices:
        balance = invoice.balance
        if balance > 0:
            # Use due_date for aging calculation
            reference_date = invoice.due_date
            days_overdue = (today - reference_date).days
            
            if days_overdue < 0:
                # Not yet due
                aging['current'] += balance
            elif days_overdue >= 1 and days_overdue <= 30:
                # 1-30 days overdue
                aging['days_1_30'] += balance
            elif days_overdue >= 31 and days_overdue <= 60:
                # 31-60 days overdue
                aging['days_31_60'] += balance
            elif days_overdue >= 61 and days_overdue <= 90:
                # 61-90 days overdue
                aging['days_61_90'] += balance
            else:
                # Over 90 days overdue
                aging['over_90'] += balance
        elif balance < 0:
            # Credit balance
            aging['credit'] += abs(balance)
    
    # Calculate total from aging buckets
    aging_total = (aging['current'] + aging['days_1_30'] + aging['days_31_60'] + 
                   aging['days_61_90'] + aging['over_90'] - aging['credit'])
    
    return render(request, 'core/client_statement_preview.html', {
        'client': client,
        'start_date': start_date,
        'end_date': end_date,
        'balance_bf': balance_bf,
        'transactions': transactions,
        'total_invoices': total_invoices,
        'total_credits': total_credits,
        'current_balance': running_balance,
        'aging': aging
    })


@login_required
def client_delete(request, pk):
    """Delete a client"""
    client = get_object_or_404(Client, pk=pk)
    
    if request.method == 'POST':
        client_name = client.name
        client.delete()
        messages.success(request, f'Client "{client_name}" deleted successfully!')
        return redirect('accounting_forms:client_list')
    
    return render(request, 'core/client_confirm_delete.html', {
        'client': client
    })


@login_required
@require_http_methods(["POST"])
def client_bulk_delete(request):
    """Bulk delete clients"""
    client_ids = request.POST.getlist('client_ids')
    
    if client_ids:
        count = Client.objects.filter(id__in=client_ids).count()
        Client.objects.filter(id__in=client_ids).delete()
        messages.success(request, f'{count} client(s) deleted successfully!')
    else:
        messages.warning(request, 'No clients selected for deletion.')
    
    return redirect('accounting_forms:client_list')


# Product Views
@login_required
def product_list(request):
    """List all products"""
    products = Product.objects.all().order_by('name')
    return render(request, 'core/product_list.html', {'products': products})


@login_required
def product_create(request):
    """Create a new product"""
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product "{product.name}" created successfully!')
            return redirect('accounting_forms:product_list')
    else:
        form = ProductForm()
    
    return render(request, 'core/product_form.html', {
        'form': form,
        'title': 'Create Product'
    })


@login_required
def product_edit(request, pk):
    """Edit an existing product"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product "{product.name}" updated successfully!')
            return redirect('accounting_forms:product_list')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'core/product_form.html', {
        'form': form,
        'title': f'Edit Product: {product.name}',
        'product': product
    })


# Quote Views
@login_required
def quote_list(request):
    """List all quotes with search and sort functionality"""
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', '-issue_date')
    
    # Valid sort fields
    valid_sorts = ['quote_number', '-quote_number', 'client__name', '-client__name',
                   'issue_date', '-issue_date', 'expiry_date', '-expiry_date',
                   'status', '-status', 'total_amount', '-total_amount', 'created_at', '-created_at']
    if sort_by not in valid_sorts:
        sort_by = '-issue_date'
    
    quotes = Quote.objects.all().select_related('client')
    
    if search_query:
        from django.db.models import Q
        quotes = quotes.filter(
            Q(quote_number__icontains=search_query) |
            Q(client__name__icontains=search_query) |
            Q(client__customer_id__icontains=search_query) |
            Q(status__icontains=search_query)
        )
    
    quotes = quotes.order_by(sort_by)
    
    return render(request, 'core/quote_list.html', {
        'quotes': quotes,
        'search_query': search_query,
        'sort_by': sort_by,
    })


@login_required
@transaction.atomic
def quote_create(request):
    """Create a new quote with items"""
    if request.method == 'POST':
        form = QuoteForm(request.POST)
        formset = QuoteItemFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            quote = form.save(commit=False)
            quote.created_by = request.user
            quote.save()
            
            # Save items and populate from product
            for item_form in formset:
                if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE', False):
                    item = item_form.save(commit=False)
                    item.quote = quote
                    if item.product:
                        # Auto-populate from product
                        item.description = item.product.description
                        item.unit_price = item.product.unit_price
                        item.tax_rate = item.product.tax_rate
                    item.save()
            
            quote.calculate_totals()
            
            messages.success(request, f'Quote {quote.quote_number} for {quote.client.name} created successfully!')
            return redirect('accounting_forms:quote_detail', pk=quote.pk)
    else:
        # Set default dates
        initial_data = {
            'issue_date': date.today(),
            'expiry_date': date.today() + timedelta(days=7)
        }
        form = QuoteForm(initial=initial_data)
        formset = QuoteItemFormSet(queryset=QuoteItem.objects.none())
    
    return render(request, 'core/quote_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Quote'
    })


@login_required
@transaction.atomic
def quote_edit(request, pk):
    """Edit an existing quote"""
    quote = get_object_or_404(Quote, pk=pk)
    
    if request.method == 'POST':
        form = QuoteForm(request.POST, instance=quote)
        formset = QuoteItemFormSet(request.POST, instance=quote)
        
        if form.is_valid() and formset.is_valid():
            quote = form.save()
            formset.save()
            quote.calculate_totals()
            
            messages.success(request, f'Quote {quote.quote_number} updated successfully!')
            return redirect('accounting_forms:quote_detail', pk=quote.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = QuoteForm(instance=quote)
        formset = QuoteItemFormSet(instance=quote)
    
    return render(request, 'core/quote_form.html', {
        'form': form,
        'formset': formset,
        'title': f'Edit Quote: {quote.quote_number}',
        'quote': quote
    })


@login_required
def quote_detail(request, pk):
    """View quote details"""
    quote = get_object_or_404(Quote, pk=pk)
    return render(request, 'core/quote_detail.html', {'quote': quote})


# Invoice Views
@login_required
def invoice_list(request):
    """List all invoices with search and sort functionality"""
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', '-issue_date')
    
    # Valid sort fields
    valid_sorts = ['invoice_number', '-invoice_number', 'client__name', '-client__name',
                   'issue_date', '-issue_date', 'due_date', '-due_date',
                   'status', '-status', 'total_amount', '-total_amount', 
                   'paid_amount', '-paid_amount', 'created_at', '-created_at']
    if sort_by not in valid_sorts:
        sort_by = '-issue_date'
    
    invoices = Invoice.objects.all().select_related('client')
    
    if search_query:
        from django.db.models import Q
        invoices = invoices.filter(
            Q(invoice_number__icontains=search_query) |
            Q(client__name__icontains=search_query) |
            Q(client__customer_id__icontains=search_query) |
            Q(status__icontains=search_query)
        )
    
    invoices = invoices.order_by(sort_by)
    
    return render(request, 'core/invoice_list.html', {
        'invoices': invoices,
        'search_query': search_query,
        'sort_by': sort_by,
    })


@login_required
@transaction.atomic
def invoice_create(request):
    """Create a new invoice with items"""
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        formset = InvoiceItemFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            invoice.created_by = request.user
            invoice.save()
            
            # Save items and populate from product
            for item_form in formset:
                if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE', False):
                    item = item_form.save(commit=False)
                    item.invoice = invoice
                    if item.product:
                        # Auto-populate from product
                        item.description = item.product.description
                        item.unit_price = item.product.unit_price
                        item.tax_rate = item.product.tax_rate
                    item.save()
            
            invoice.calculate_totals()
            
            messages.success(request, f'Invoice {invoice.invoice_number} for {invoice.client.name} created successfully!')
            return redirect('accounting_forms:invoice_detail', pk=invoice.pk)
    else:
        # Set default dates
        initial_data = {
            'issue_date': date.today(),
            'due_date': date.today() + timedelta(days=30)
        }
        form = InvoiceForm(initial=initial_data)
        formset = InvoiceItemFormSet(queryset=InvoiceItem.objects.none())
    
    return render(request, 'core/invoice_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Invoice'
    })


@login_required
@transaction.atomic
def invoice_edit(request, invoice_number):
    """Edit an existing invoice"""
    invoice = get_object_or_404(Invoice, invoice_number=invoice_number)
    
    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        formset = InvoiceItemFormSet(request.POST, instance=invoice)
        
        if form.is_valid() and formset.is_valid():
            invoice = form.save()
            formset.save()
            invoice.calculate_totals()
            
            messages.success(request, f'Invoice {invoice.invoice_number} updated successfully!')
            return redirect('accounting_forms:invoice_detail', pk=invoice.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = InvoiceForm(instance=invoice)
        formset = InvoiceItemFormSet(instance=invoice)
    
    return render(request, 'core/invoice_form.html', {
        'form': form,
        'formset': formset,
        'title': f'Edit Invoice: {invoice.invoice_number}',
        'invoice': invoice
    })


@login_required
def invoice_detail(request, invoice_number):
    """View invoice details"""
    from .models import CompanySettings
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        invoice = get_object_or_404(Invoice, invoice_number=invoice_number)
        payments = invoice.payments.all().order_by('-payment_date')
        company_settings = CompanySettings.load()
        
        return render(request, 'core/invoice_detail.html', {
            'invoice': invoice,
            'payments': payments,
            'company_settings': company_settings
        })
    except Exception as e:
        logger.error(f"Error in invoice_detail for {invoice_number}: {str(e)}", exc_info=True)
        raise


@login_required
@require_http_methods(["POST"])
def invoice_mark_whatsapp_sent(request, invoice_number):
    """Mark invoice as sent via WhatsApp"""
    invoice = get_object_or_404(Invoice, invoice_number=invoice_number)
    
    invoice.whatsapp_sent = True
    invoice.whatsapp_sent_at = timezone.now()
    invoice.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Invoice marked as sent via WhatsApp',
        'sent_at': invoice.whatsapp_sent_at.strftime('%Y-%m-%d %H:%M')
    })


# Payment Views
@login_required
def payment_create(request, invoice_pk=None):
    """Record a new payment"""
    initial = {}
    if invoice_pk:
        invoice = get_object_or_404(Invoice, pk=invoice_pk)
        initial['invoice'] = invoice
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save()
            messages.success(request, f'Payment of R{payment.amount} recorded successfully!')
            return redirect('accounting_forms:invoice_detail', pk=payment.invoice.pk)
    else:
        form = PaymentForm(initial=initial)
    
    return render(request, 'core/payment_form.html', {
        'form': form,
        'title': 'Record Payment'
    })


# Credit Note Views
@login_required
@transaction.atomic
def credit_note_create(request, invoice_pk=None):
    """Create a new credit note"""
    initial = {}
    if invoice_pk:
        invoice = get_object_or_404(Invoice, pk=invoice_pk)
        initial['invoice'] = invoice
    
    if request.method == 'POST':
        form = CreditNoteForm(request.POST)
        formset = CreditNoteItemFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            credit_note = form.save(commit=False)
            credit_note.created_by = request.user
            credit_note.save()
            
            formset.instance = credit_note
            formset.save()
            
            credit_note.calculate_totals()
            
            messages.success(request, f'Credit Note {credit_note.credit_note_number} created successfully!')
            return redirect('accounting_forms:credit_note_detail', pk=credit_note.pk)
    else:
        form = CreditNoteForm(initial=initial)
        formset = CreditNoteItemFormSet()
    
    return render(request, 'core/credit_note_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Credit Note'
    })


@login_required
def credit_note_detail(request, pk):
    """View credit note details"""
    credit_note = get_object_or_404(CreditNote, pk=pk)
    return render(request, 'core/credit_note_detail.html', {'credit_note': credit_note})


# Daily Sales Report
@login_required
def daily_sales_report(request):
    """Daily sales overview with payment type and product breakdown"""
    from django.db.models import Sum, Count, Q, F
    from datetime import datetime, date
    
    # Get selected date from query params or use today
    selected_date_str = request.GET.get('date')
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()
    
    # Get all payments for the selected date
    payments = Payment.objects.filter(payment_date=selected_date).select_related('invoice', 'invoice__client')
    
    # Calculate totals by payment method
    payment_summary = payments.values('payment_method').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('payment_method')
    
    # Calculate overall totals
    total_sales = payments.aggregate(total=Sum('amount'))['total'] or 0
    total_transactions = payments.count()
    
    # Get invoices created on selected date
    invoices_created = Invoice.objects.filter(issue_date=selected_date)
    invoices_created_total = invoices_created.aggregate(total=Sum('total_amount'))['total'] or 0
    invoices_created_count = invoices_created.count()
    
    # Get invoices paid on selected date (different from payments - shows invoice totals)
    invoices_paid = Invoice.objects.filter(
        payments__payment_date=selected_date
    ).distinct()
    
    # Get product sales breakdown for invoices paid on this date
    product_summary = InvoiceItem.objects.filter(
        invoice__payments__payment_date=selected_date
    ).values(
        'product__name'
    ).annotate(
        quantity_sold=Sum('quantity'),
        total_sales=Sum('total'),
        total_vat=Sum('tax_amount')
    ).order_by('-total_sales')
    
    # Calculate product totals
    product_total_quantity = sum(p['quantity_sold'] or 0 for p in product_summary)
    product_total_sales = sum(p['total_sales'] or 0 for p in product_summary)
    product_total_vat = sum(p['total_vat'] or 0 for p in product_summary)
    
    context = {
        'selected_date': selected_date,
        'payments': payments.order_by('-payment_date', '-created_at'),
        'payment_summary': payment_summary,
        'total_sales': total_sales,
        'total_transactions': total_transactions,
        'invoices_created': invoices_created,
        'invoices_created_total': invoices_created_total,
        'invoices_created_count': invoices_created_count,
        'invoices_paid': invoices_paid,
        'product_summary': product_summary,
        'product_total_quantity': product_total_quantity,
        'product_total_sales': product_total_sales,
        'product_total_vat': product_total_vat,
    }
    
    return render(request, 'core/daily_sales_report.html', context)


# Dashboard
@login_required
def accounting_dashboard(request):
    """Accounting dashboard with overview"""
    from django.db.models import Sum, Count, Q
    from datetime import datetime, timedelta
    
    # Get current month data
    today = datetime.now()
    first_day = today.replace(day=1)
    
    stats = {
        'total_clients': Client.objects.filter(is_active=True).count(),
        'pending_quotes': Quote.objects.filter(status='draft').count(),
        'unpaid_invoices': Invoice.objects.filter(status__in=['draft', 'sent']).count(),
        'overdue_invoices': Invoice.objects.filter(
            status__in=['draft', 'sent'],
            due_date__lt=today
        ).count(),
        'monthly_revenue': Invoice.objects.filter(
            issue_date__gte=first_day,
            status='paid'
        ).aggregate(total=Sum('total_amount'))['total'] or 0,
        'outstanding_amount': Invoice.objects.filter(
            status__in=['draft', 'sent']
        ).aggregate(total=Sum('total_amount'))['total'] or 0,
    }
    
    recent_invoices = Invoice.objects.all().order_by('-issue_date')[:5]
    recent_quotes = Quote.objects.all().order_by('-issue_date')[:5]
    recent_payments = Payment.objects.all().order_by('-payment_date')[:5]
    
    return render(request, 'core/dashboard.html', {
        'stats': stats,
        'recent_invoices': recent_invoices,
        'recent_quotes': recent_quotes,
        'recent_payments': recent_payments,
    })


# Orders Views
@login_required
def order_list(request):
    """List all orders with filtering and sorting"""
    from django.db.models import Q
    
    # Filters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    payment_status_filter = request.GET.get('payment_status', '')
    sort_by = request.GET.get('sort', '-created_at')
    
    # Valid sort fields
    valid_sorts = ['order_number', '-order_number', 'customer_name', '-customer_name',
                   'status', '-status', 'payment_status', '-payment_status',
                   'payment_method', '-payment_method', 'total', '-total', 'created_at', '-created_at']
    if sort_by not in valid_sorts:
        sort_by = '-created_at'
    
    orders = Order.objects.all().select_related('delivery_zone', 'assigned_driver__user').prefetch_related('items__product', 'items__variant')
    
    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(customer_name__icontains=search_query) |
            Q(customer_phone__icontains=search_query)
        )
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if payment_status_filter:
        orders = orders.filter(payment_status=payment_status_filter)
    
    orders = orders.order_by(sort_by)
    
    # Calculate stats
    pending_count = Order.objects.filter(status='pending').count()
    delivered_count = Order.objects.filter(status='delivered').count()
    total_revenue = Order.objects.filter(payment_status='paid').aggregate(
        total=Sum('total')
    )['total'] or 0
    
    return render(request, 'core/orders_list.html', {
        'orders': orders,
        'pending_count': pending_count,
        'delivered_count': delivered_count,
        'total_revenue': total_revenue,
        'sort_by': sort_by,
    })


@login_required
def order_detail(request, pk):
    """View order details"""
    order = get_object_or_404(Order.objects.prefetch_related('items__product'), pk=pk)
    
    return render(request, 'core/order_detail.html', {
        'order': order,
    })


@login_required
def order_assign_driver(request, pk):
    """Assign driver to order"""
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        driver_id = request.POST.get('driver_id')
        
        if driver_id:
            try:
                driver = Driver.objects.get(pk=driver_id, is_active=True)
                order.assigned_driver = driver
                order.save()
                
                messages.success(request, f'Order #{order.order_number} assigned to {driver.user.get_full_name()}')
            except Driver.DoesNotExist:
                messages.error(request, 'Invalid driver selected')
        else:
            # Unassign driver
            order.assigned_driver = None
            order.save()
            messages.success(request, f'Driver unassigned from order #{order.order_number}')
        
        return redirect('accounting_forms:order_detail', pk=pk)
    
    # Get available drivers
    available_drivers = Driver.objects.filter(is_active=True).select_related('user').order_by('user__first_name')
    
    return render(request, 'core/order_assign_driver.html', {
        'order': order,
        'available_drivers': available_drivers,
    })


# Driver Views
@login_required
def driver_list(request):
    """List all drivers with filtering"""
    from django.db.models import Q, Count
    
    drivers = Driver.objects.select_related('user').annotate(
        active_deliveries=Count('assigned_orders', filter=Q(assigned_orders__status__in=['confirmed', 'preparing', 'out_for_delivery']))
    )
    
    # Filters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    if search_query:
        drivers = drivers.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(vehicle_registration__icontains=search_query)
        )
    
    if status_filter:
        drivers = drivers.filter(status=status_filter)
    
    drivers = drivers.order_by('-is_active', 'user__first_name')
    
    # Calculate stats
    total_drivers = Driver.objects.count()
    available_count = Driver.objects.filter(status='available', is_active=True).count()
    on_delivery_count = Driver.objects.filter(status='on_delivery').count()
    
    return render(request, 'core/driver_list.html', {
        'drivers': drivers,
        'total_drivers': total_drivers,
        'available_count': available_count,
        'on_delivery_count': on_delivery_count,
        'search_query': search_query,
        'status_filter': status_filter,
    })


@login_required
def driver_detail(request, pk):
    """View driver details and assigned orders"""
    driver = get_object_or_404(Driver.objects.select_related('user'), pk=pk)
    
    # Get all orders assigned to this driver
    orders = driver.assigned_orders.all().order_by('-created_at')[:20]
    
    # Get active deliveries
    active_deliveries = driver.get_active_deliveries()
    
    # Calculate statistics
    total_deliveries = driver.total_deliveries
    completed_deliveries = driver.assigned_orders.filter(status='delivered').count()
    
    return render(request, 'core/driver_detail.html', {
        'driver': driver,
        'orders': orders,
        'active_deliveries': active_deliveries,
        'total_deliveries': total_deliveries,
        'completed_deliveries': completed_deliveries,
    })


@login_required
def driver_create(request):
    """Create a new driver"""
    from django.contrib.auth.models import User
    
    if request.method == 'POST':
        # Get user data
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Get driver data
        phone = request.POST.get('phone')
        id_number = request.POST.get('id_number', '')
        address = request.POST.get('address', '')
        vehicle_type = request.POST.get('vehicle_type')
        vehicle_registration = request.POST.get('vehicle_registration')
        vehicle_make_model = request.POST.get('vehicle_make_model', '')
        drivers_license_number = request.POST.get('drivers_license_number', '')
        license_expiry_date = request.POST.get('license_expiry_date') or None
        
        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Create driver profile
            driver = Driver.objects.create(
                user=user,
                phone=phone,
                id_number=id_number,
                address=address,
                vehicle_type=vehicle_type,
                vehicle_registration=vehicle_registration,
                vehicle_make_model=vehicle_make_model,
                drivers_license_number=drivers_license_number,
                license_expiry_date=license_expiry_date,
                status='available',
                is_active=True
            )
            
            messages.success(request, f'Driver {driver.user.get_full_name()} created successfully!')
            return redirect('accounting_forms:driver_detail', pk=driver.pk)
            
        except Exception as e:
            messages.error(request, f'Error creating driver: {str(e)}')
    
    return render(request, 'core/driver_form.html', {
        'title': 'Create Driver',
        'is_edit': False,
    })


@login_required
def driver_edit(request, pk):
    """Edit an existing driver"""
    driver = get_object_or_404(Driver.objects.select_related('user'), pk=pk)
    
    if request.method == 'POST':
        # Update user data
        driver.user.first_name = request.POST.get('first_name')
        driver.user.last_name = request.POST.get('last_name')
        driver.user.email = request.POST.get('email')
        driver.user.save()
        
        # Update driver data
        driver.phone = request.POST.get('phone')
        driver.id_number = request.POST.get('id_number', '')
        driver.address = request.POST.get('address', '')
        driver.vehicle_type = request.POST.get('vehicle_type')
        driver.vehicle_registration = request.POST.get('vehicle_registration')
        driver.vehicle_make_model = request.POST.get('vehicle_make_model', '')
        driver.drivers_license_number = request.POST.get('drivers_license_number', '')
        license_expiry = request.POST.get('license_expiry_date')
        driver.license_expiry_date = license_expiry if license_expiry else None
        driver.status = request.POST.get('status')
        driver.is_active = request.POST.get('is_active') == 'on'
        driver.notes = request.POST.get('notes', '')
        
        try:
            driver.save()
            messages.success(request, f'Driver {driver.user.get_full_name()} updated successfully!')
            return redirect('accounting_forms:driver_detail', pk=driver.pk)
        except Exception as e:
            messages.error(request, f'Error updating driver: {str(e)}')
    
    return render(request, 'core/driver_form.html', {
        'title': 'Edit Driver',
        'driver': driver,
        'is_edit': True,
    })


@login_required
def driver_delete(request, pk):
    """Delete a driver"""
    driver = get_object_or_404(Driver, pk=pk)
    
    if request.method == 'POST':
        driver_name = driver.user.get_full_name() or driver.user.username
        driver.delete()
        messages.success(request, f'Driver {driver_name} deleted successfully!')
        return redirect('accounting_forms:driver_list')
    
    return render(request, 'core/driver_confirm_delete.html', {
        'driver': driver,
    })
