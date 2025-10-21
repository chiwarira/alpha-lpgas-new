from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db import transaction
from django.db.models import Sum
from django.views.decorators.http import require_http_methods
from datetime import date, timedelta
from .models import Client, Product, Quote, QuoteItem, Invoice, InvoiceItem, Payment, CreditNote
from .forms import (
    ClientForm, ProductForm, QuoteForm, QuoteItemFormSet,
    InvoiceForm, InvoiceItemFormSet, PaymentForm,
    CreditNoteForm, CreditNoteItemFormSet, CompanySettingsForm
)


# Client Views
@login_required
def client_list(request):
    """List all clients with search functionality"""
    search_query = request.GET.get('search', '')
    
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
    
    clients = clients.order_by('-created_at')
    
    return render(request, 'core/client_list.html', {
        'clients': clients,
        'search_query': search_query
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
    """List all quotes with search functionality"""
    search_query = request.GET.get('search', '')
    
    quotes = Quote.objects.all()
    
    if search_query:
        from django.db.models import Q
        quotes = quotes.filter(
            Q(quote_number__icontains=search_query) |
            Q(client__name__icontains=search_query) |
            Q(client__customer_id__icontains=search_query) |
            Q(status__icontains=search_query)
        )
    
    quotes = quotes.order_by('-issue_date')
    
    return render(request, 'core/quote_list.html', {
        'quotes': quotes,
        'search_query': search_query
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
    """List all invoices with search functionality"""
    search_query = request.GET.get('search', '')
    
    invoices = Invoice.objects.all()
    
    if search_query:
        from django.db.models import Q
        invoices = invoices.filter(
            Q(invoice_number__icontains=search_query) |
            Q(client__name__icontains=search_query) |
            Q(client__customer_id__icontains=search_query) |
            Q(status__icontains=search_query)
        )
    
    invoices = invoices.order_by('-issue_date')
    
    return render(request, 'core/invoice_list.html', {
        'invoices': invoices,
        'search_query': search_query
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
def invoice_edit(request, pk):
    """Edit an existing invoice"""
    invoice = get_object_or_404(Invoice, pk=pk)
    
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
def invoice_detail(request, pk):
    """View invoice details"""
    invoice = get_object_or_404(Invoice, pk=pk)
    payments = invoice.payments.all().order_by('-payment_date')
    
    return render(request, 'core/invoice_detail.html', {
        'invoice': invoice,
        'payments': payments
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
