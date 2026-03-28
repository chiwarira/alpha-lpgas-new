from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Sum
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import date, timedelta
from .models import Client, Product, Quote, QuoteItem, Invoice, InvoiceItem, Payment, CreditNote, CreditNoteItem, Order, Driver, DeliveryZone, ContactSubmission
from .models_accounting import Supplier, Expense, ExpenseCategory, JournalEntry, TaxPeriod
from .forms import (
    ClientForm, ProductForm, QuoteForm, QuoteItemFormSet,
    InvoiceForm, InvoiceItemFormSet, PaymentForm, MultiPaymentForm,
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
@require_http_methods(["POST"])
def client_create_ajax(request):
    """Create a new client via AJAX (from invoice form modal)"""
    import json
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'Client name is required.'})
        
        client = Client.objects.create(
            name=name,
            company_name=data.get('company_name', '').strip(),
            company_reg=data.get('company_reg', '').strip(),
            phone=data.get('phone', '').strip(),
            email=data.get('email', '').strip(),
            address=data.get('address', '').strip(),
            city=data.get('city', '').strip(),
        )
        return JsonResponse({
            'success': True,
            'client': {
                'id': client.pk,
                'name': client.name,
                'phone': client.phone,
                'address': client.address,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def client_last_invoice_ajax(request, client_id):
    """Get client's last invoice data for auto-population"""
    try:
        client = get_object_or_404(Client, pk=client_id)
        
        # Get the most recent invoice for this client
        last_invoice = Invoice.objects.filter(client=client).order_by('-created_at').first()
        
        if not last_invoice:
            return JsonResponse({
                'success': True,
                'has_previous_invoice': False
            })
        
        # Get invoice items (excluding delivery fees)
        items = []
        for item in last_invoice.items.exclude(product__name='Delivery Fee'):
            items.append({
                'product_id': item.product.id if item.product else None,
                'product_name': item.product.name if item.product else item.description,
                'quantity': str(item.quantity),
            })
        
        return JsonResponse({
            'success': True,
            'has_previous_invoice': True,
            'data': {
                'delivery_zone_id': last_invoice.delivery_zone.id if last_invoice.delivery_zone else None,
                'payment_terms': last_invoice.payment_terms,
                'items': items
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


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
    search_query = request.GET.get('search', '')
    
    products = Product.objects.all()
    
    if search_query:
        from django.db.models import Q
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(sku__icontains=search_query)
        )
    
    products = products.order_by('name')
    
    return render(request, 'core/product_list.html', {
        'products': products,
        'search_query': search_query
    })


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


@login_required
def quote_delete(request, pk):
    """Delete a quote"""
    quote = get_object_or_404(Quote, pk=pk)
    
    if request.method == 'POST':
        quote_id = quote.pk
        quote.delete()
        messages.success(request, f'Quote #{quote_id} deleted successfully!')
        return redirect('accounting_forms:quote_list')
    
    return render(request, 'core/quote_confirm_delete.html', {
        'quote': quote
    })


# Invoice Views
@login_required
def invoice_list(request):
    """List all invoices with search, sort, filter, and pagination"""
    from django.core.paginator import Paginator
    from django.db.models import Q
    from datetime import date, timedelta
    
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', '-issue_date')
    status_filter = request.GET.get('status', '')
    
    # Default to current day if no date filters provided
    today = date.today()
    default_date = today.strftime('%Y-%m-%d')
    
    date_from = request.GET.get('date_from', default_date)
    date_to = request.GET.get('date_to', default_date)
    per_page = request.GET.get('per_page', '50')
    
    # Valid sort fields
    valid_sorts = ['invoice_number', '-invoice_number', 'client__name', '-client__name',
                   'client__address', '-client__address',
                   'issue_date', '-issue_date', 'due_date', '-due_date',
                   'status', '-status', 'total_amount', '-total_amount', 
                   'paid_amount', '-paid_amount', 'created_at', '-created_at']
    if sort_by not in valid_sorts:
        sort_by = '-issue_date'
    
    try:
        per_page = int(per_page)
        if per_page not in [25, 50, 100, 200]:
            per_page = 50
    except (ValueError, TypeError):
        per_page = 50
    
    invoices = Invoice.objects.all().select_related('client')
    
    # Search filter
    if search_query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search_query) |
            Q(client__name__icontains=search_query) |
            Q(client__customer_id__icontains=search_query) |
            Q(client__address__icontains=search_query) |
            Q(status__icontains=search_query)
        )
    
    # Status filter
    if status_filter:
        invoices = invoices.filter(status=status_filter)
    
    # Date range filter
    if date_from:
        try:
            invoices = invoices.filter(issue_date__gte=date_from)
        except (ValueError, TypeError):
            pass
    if date_to:
        try:
            invoices = invoices.filter(issue_date__lte=date_to)
        except (ValueError, TypeError):
            pass
    
    # Get counts for status tabs (before pagination, after search/date filters)
    status_counts = {
        'all': invoices.count(),
        'unpaid': invoices.filter(status='unpaid').count(),
        'partially_paid': invoices.filter(status='partially_paid').count(),
        'paid': invoices.filter(status='paid').count(),
    }
    
    invoices = invoices.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(invoices, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/invoice_list.html', {
        'invoices': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'search_query': search_query,
        'sort_by': sort_by,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'per_page': per_page,
        'status_counts': status_counts,
    })


@login_required
@require_http_methods(["POST"])
def invoice_bulk_action(request):
    """Handle bulk actions on invoices"""
    import csv
    from io import StringIO
    
    action = request.POST.get('action', '')
    invoice_ids = request.POST.getlist('invoice_ids')
    
    if not invoice_ids:
        messages.warning(request, 'No invoices selected.')
        return redirect('accounting_forms:invoice_list')
    
    invoices = Invoice.objects.filter(pk__in=invoice_ids).select_related('client')
    
    if action == 'delete':
        count = invoices.count()
        invoices.delete()
        messages.success(request, f'Successfully deleted {count} invoice(s).')
        return redirect('accounting_forms:invoice_list')
    
    elif action == 'export_csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="invoices_export_{date.today().isoformat()}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Invoice #', 'Client', 'Address', 'Issue Date', 'Due Date', 'Total', 'Paid', 'Balance', 'Status', 'WhatsApp Sent'])
        for inv in invoices.order_by('-issue_date'):
            writer.writerow([
                inv.invoice_number,
                inv.client.name,
                inv.client.address or '',
                inv.issue_date,
                inv.due_date,
                inv.total_amount,
                inv.paid_amount,
                inv.balance,
                inv.get_status_display(),
                'Yes' if inv.whatsapp_sent else 'No',
            ])
        return response
    
    elif action == 'mark_whatsapp_sent':
        now = timezone.now()
        updated = invoices.update(whatsapp_sent=True, whatsapp_sent_at=now)
        messages.success(request, f'Marked {updated} invoice(s) as sent via WhatsApp.')
        return redirect('accounting_forms:invoice_list')
    
    else:
        messages.error(request, 'Invalid action.')
        return redirect('accounting_forms:invoice_list')


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
            
            # Add delivery fee as line item if delivery zone selected
            if invoice.delivery_zone and invoice.delivery_zone.delivery_fee > 0:
                from decimal import Decimal
                # Get or create a Delivery Fee product
                delivery_product, _ = Product.objects.get_or_create(
                    name='Delivery Fee',
                    defaults={
                        'description': 'Delivery service charge',
                        'unit_price': invoice.delivery_zone.delivery_fee,
                        'tax_rate': Decimal('15'),
                        'is_active': True
                    }
                )
                # Add delivery fee line item
                InvoiceItem.objects.create(
                    invoice=invoice,
                    product=delivery_product,
                    description=f'Delivery to {invoice.delivery_zone.name}',
                    quantity=1,
                    unit_price=invoice.delivery_zone.delivery_fee,
                    tax_rate=Decimal('15')
                )
            
            invoice.calculate_totals()
            
            # Process loyalty stamp for every invoice created
            from .utils_loyalty import process_loyalty_stamp
            try:
                loyalty_card = process_loyalty_stamp(invoice)
                if loyalty_card:
                    messages.info(request, f'Loyalty card updated: {loyalty_card.stamps}/9 stamps')
            except Exception as e:
                # Log the error but don't fail the invoice creation
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Error processing loyalty stamp for invoice {invoice.invoice_number}: {str(e)}')
                messages.warning(request, 'Invoice created successfully, but loyalty stamp could not be processed.')
            
            messages.success(request, f'Invoice {invoice.invoice_number} for {invoice.client.name} created successfully!')
            return redirect('accounting_forms:invoice_detail', invoice_number=invoice.invoice_number)
    else:
        # Set default dates and payment terms
        initial_data = {
            'issue_date': date.today(),
            'due_date': date.today() + timedelta(days=30),
            'payment_terms': 'immediate'
        }
        # Pre-select client if passed via query param (e.g. from client detail page)
        client_id = request.GET.get('client')
        if client_id:
            initial_data['client'] = client_id
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
    old_delivery_zone = invoice.delivery_zone
    old_client = invoice.client  # Track old client for loyalty stamp reassignment
    
    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        formset = InvoiceItemFormSet(
            request.POST,
            instance=invoice,
        )
        
        if form.is_valid() and formset.is_valid():
            invoice = form.save()
            
            # Save items and populate from product for new items
            for item_form in formset:
                if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE', False):
                    item = item_form.save(commit=False)
                    item.invoice = invoice
                    if item.product and not item.unit_price:
                        # Auto-populate from product for new items
                        item.description = item.product.description
                        item.unit_price = item.product.unit_price
                        item.tax_rate = item.product.tax_rate
                    item.save()
            
            # Delete items marked for deletion
            for item_form in formset.deleted_forms:
                if item_form.instance.pk:
                    item_form.instance.delete()
            
            # Handle delivery zone changes
            new_delivery_zone = invoice.delivery_zone
            if new_delivery_zone != old_delivery_zone:
                # Remove old delivery fee line item if exists
                invoice.items.filter(product__name='Delivery Fee').delete()
                
                # Add new delivery fee if zone selected
                if new_delivery_zone and new_delivery_zone.delivery_fee > 0:
                    from decimal import Decimal
                    delivery_product, _ = Product.objects.get_or_create(
                        name='Delivery Fee',
                        defaults={
                            'description': 'Delivery service charge',
                            'unit_price': new_delivery_zone.delivery_fee,
                            'tax_rate': Decimal('15'),
                            'is_active': True
                        }
                    )
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        product=delivery_product,
                        description=f'Delivery to {new_delivery_zone.name}',
                        quantity=1,
                        unit_price=new_delivery_zone.delivery_fee,
                        tax_rate=Decimal('15')
                    )
            
            invoice.calculate_totals()
            
            # Reprocess loyalty stamps for edited invoice
            from .utils_loyalty import reprocess_loyalty_stamp
            try:
                loyalty_card = reprocess_loyalty_stamp(invoice, old_client=old_client)
                if loyalty_card:
                    if old_client != invoice.client:
                        messages.info(request, f'Loyalty stamps transferred from {old_client.name} to {invoice.client.name}')
                    else:
                        messages.info(request, f'Loyalty card updated: {loyalty_card.stamps}/9 stamps')
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Error reprocessing loyalty stamp for invoice {invoice.invoice_number}: {str(e)}')
                messages.warning(request, 'Invoice updated successfully, but loyalty stamp could not be reprocessed.')
            
            messages.success(request, f'Invoice {invoice.invoice_number} updated successfully!')
            return redirect('accounting_forms:invoice_detail', invoice_number=invoice.invoice_number)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = InvoiceForm(instance=invoice)
        # Exclude delivery fee items from the formset - they're managed automatically
        formset = InvoiceItemFormSet(
            instance=invoice,
            queryset=invoice.items.exclude(product__name='Delivery Fee')
        )
    
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
        
        # Order items so delivery fee is always last
        from django.db.models import Case, When, Value, IntegerField
        ordered_items = invoice.items.all().annotate(
            is_delivery=Case(
                When(product__name='Delivery Fee', then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by('is_delivery', 'id')
        
        return render(request, 'core/invoice_detail.html', {
            'invoice': invoice,
            'payments': payments,
            'company_settings': company_settings,
            'ordered_items': ordered_items
        })
    except Exception as e:
        logger.error(f"Error in invoice_detail for {invoice_number}: {str(e)}", exc_info=True)
        raise


@login_required
def invoice_delete(request, invoice_number):
    """Delete an invoice"""
    invoice = get_object_or_404(Invoice, invoice_number=invoice_number)
    
    if request.method == 'POST':
        invoice_num = invoice.invoice_number
        client_name = invoice.client.name
        
        # Remove loyalty stamps before deleting invoice
        from .utils_loyalty import remove_loyalty_stamp
        try:
            loyalty_card = remove_loyalty_stamp(invoice)
            if loyalty_card:
                messages.info(request, f'Loyalty stamps removed from {client_name}\'s card')
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error removing loyalty stamp for invoice {invoice_num}: {str(e)}')
        
        invoice.delete()
        messages.success(request, f'Invoice "{invoice_num}" deleted successfully!')
        return redirect('accounting_forms:invoice_list')
    
    return render(request, 'core/invoice_confirm_delete.html', {
        'invoice': invoice
    })


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
    # Get invoice_id from URL parameter or path parameter
    invoice_id = request.GET.get('invoice') or invoice_pk
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, invoice_id=invoice_id)
        if form.is_valid():
            payment = form.save()
            messages.success(request, f'Payment of R{payment.amount} recorded successfully!')
            return redirect('accounting_forms:invoice_detail', invoice_number=payment.invoice.invoice_number)
    else:
        form = PaymentForm(invoice_id=invoice_id)
    
    return render(request, 'core/payment_form.html', {
        'form': form,
        'title': 'Add Payment'
    })


@login_required
@require_http_methods(["POST"])
def quick_payment(request, pk):
    """One-click full balance payment from the invoice list."""
    invoice = get_object_or_404(Invoice, pk=pk)
    balance = invoice.total_amount - invoice.paid_amount
    
    # Get payment method from POST data, default to 'eft' for backwards compatibility
    payment_method = request.POST.get('payment_method', 'eft')
    
    # Validate payment method
    valid_methods = ['cash', 'card', 'eft']
    if payment_method not in valid_methods:
        payment_method = 'eft'

    if balance > 0:
        from datetime import date
        payment = Payment(
            invoice=invoice,
            amount=balance,
            payment_date=date.today(),
            payment_method=payment_method,
            reference_number=f'Quick payment for {invoice.invoice_number}',
            notes=f'Payment applied from invoice list via {payment_method.upper()}',
            created_by=request.user,
        )
        payment.save()
        
        # Refresh invoice from database to get updated values
        invoice.refresh_from_db()
        
        # Check if AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Payment of R{balance:,.2f} ({payment_method.upper()}) applied to {invoice.invoice_number}.',
                'invoice': {
                    'paid_amount': float(invoice.paid_amount),
                    'balance': float(invoice.balance),
                    'status': invoice.status,
                    'status_display': invoice.get_status_display()
                }
            })
        
        messages.success(request, f'Payment of R{balance:,.2f} ({payment_method.upper()}) applied to {invoice.invoice_number}.')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f'{invoice.invoice_number} has no balance due.'
            })
        messages.info(request, f'{invoice.invoice_number} has no balance due.')

    referer = request.META.get('HTTP_REFERER')
    if referer and 'invoices' in referer:
        return redirect(referer)
    return redirect('accounting_forms:invoice_list')


@login_required
def invoice_balance_api(request, pk):
    """Return invoice balance as JSON for payment form auto-populate."""
    invoice = get_object_or_404(Invoice, pk=pk)
    return JsonResponse({
        'total_amount': float(invoice.total_amount),
        'paid_amount': float(invoice.paid_amount),
        'balance': float(invoice.total_amount - invoice.paid_amount),
    })


@login_required
def client_unpaid_invoices(request, client_id):
    """API endpoint to get unpaid invoices for a client"""
    try:
        client = get_object_or_404(Client, pk=client_id)
        
        # Get unpaid and partially paid invoices
        unpaid_invoices = client.invoices.filter(status__in=['unpaid', 'partially_paid'])
        
        # Format invoice data
        invoices_data = []
        for invoice in unpaid_invoices:
            status_display = invoice.get_status_display()
            balance = invoice.total_amount - invoice.paid_amount
            
            invoice_data = {
                'id': invoice.pk,
                'number': invoice.invoice_number,
                'issue_date': invoice.issue_date.strftime('%Y-%m-%d'),
                'due_date': invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else '',
                'total_amount': "{:.2f}".format(float(invoice.total_amount)),
                'balance_due': "{:.2f}".format(float(balance)),
                'status': invoice.status,
                'status_display': status_display
            }
            invoices_data.append(invoice_data)
        
        return JsonResponse({
            'success': True,
            'invoices': invoices_data,
            'count': len(invoices_data)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Server error',
            'message': str(e)
        }, status=500)


@login_required
def add_payment(request):
    """View for adding a payment that can be allocated to multiple invoices"""
    if request.method == 'POST':
        form = MultiPaymentForm(request.POST)
        if form.is_valid():
            try:
                # Get payment details
                client = form.cleaned_data['client']
                amount = form.cleaned_data['amount']
                selected_invoices = form.cleaned_data.get('selected_invoices', [])
                
                # Create and save payment
                payment = form.save(commit=False)
                payment.client = client  # Store client for multi-invoice payments
                payment.created_by = request.user
                payment.save()
                
                # Allocate payment to selected invoices
                if selected_invoices:
                    # Allocate to specific invoices
                    remaining_amount = amount
                    for invoice in selected_invoices:
                        if remaining_amount <= 0:
                            break
                        
                        balance = invoice.total_amount - invoice.paid_amount
                        allocation_amount = min(remaining_amount, balance)
                        
                        # Update invoice paid amount and recalculate status
                        invoice.paid_amount += allocation_amount
                        invoice.calculate_totals()
                        
                        remaining_amount -= allocation_amount
                    
                    invoice_numbers = ", ".join([inv.invoice_number for inv in selected_invoices])
                    messages.success(request, f'Payment of R{amount:,.2f} recorded and allocated to invoices: {invoice_numbers}')
                    
                    if remaining_amount > 0:
                        messages.info(request, f'R{remaining_amount:,.2f} remains unallocated.')
                else:
                    # Auto-allocate to oldest unpaid invoices
                    unpaid_invoices = Invoice.objects.filter(
                        client=client,
                        status__in=['unpaid', 'partially_paid']
                    ).order_by('issue_date')
                    
                    remaining_amount = amount
                    allocated_invoices = []
                    
                    for invoice in unpaid_invoices:
                        if remaining_amount <= 0:
                            break
                        
                        balance = invoice.total_amount - invoice.paid_amount
                        allocation_amount = min(remaining_amount, balance)
                        
                        # Update invoice paid amount and recalculate status
                        invoice.paid_amount += allocation_amount
                        invoice.calculate_totals()
                        
                        allocated_invoices.append(invoice.invoice_number)
                        remaining_amount -= allocation_amount
                    
                    if allocated_invoices:
                        invoice_numbers = ", ".join(allocated_invoices)
                        messages.success(request, f'Payment of R{amount:,.2f} recorded and auto-allocated to invoices: {invoice_numbers}')
                    else:
                        messages.warning(request, f'Payment of R{amount:,.2f} recorded but no unpaid invoices found for auto-allocation.')
                    
                    if remaining_amount > 0:
                        messages.info(request, f'R{remaining_amount:,.2f} remains unallocated.')
                
                return redirect('accounting_forms:invoice_list')
            
            except Exception as e:
                messages.error(request, f'An error occurred while processing the payment: {str(e)}')
        else:
            # Form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = MultiPaymentForm()
    
    return render(request, 'core/multi_payment_form.html', {
        'form': form,
        'title': 'Add Payment'
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
    
    # Get default tax rate from company settings
    from .models import CompanySettings
    company = CompanySettings.objects.first()
    default_tax_rate = company.default_tax_rate if company else 15.00
    
    if request.method == 'POST':
        form = CreditNoteForm(request.POST)
        formset = CreditNoteItemFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            credit_note = form.save(commit=False)
            credit_note.created_by = request.user
            credit_note.save()
            
            for item_form in formset:
                if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE', False):
                    item = item_form.save(commit=False)
                    item.credit_note = credit_note
                    if item.product and not item.unit_price:
                        item.unit_price = item.product.unit_price
                        item.description = item.product.description
                    if not item.tax_rate:
                        item.tax_rate = default_tax_rate
                    item.save()
            
            credit_note.calculate_totals()
            
            messages.success(request, f'Credit Note {credit_note.credit_note_number} created successfully!')
            return redirect('accounting_forms:credit_note_detail', pk=credit_note.pk)
        else:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Credit note form errors: {form.errors}')
            logger.error(f'Credit note formset errors: {formset.errors}')
            logger.error(f'Credit note formset non_form_errors: {formset.non_form_errors()}')
            if form.errors:
                for field, errors in form.errors.items():
                    messages.error(request, f'{field}: {", ".join(errors)}')
            for i, item_errors in enumerate(formset.errors):
                if item_errors:
                    for field, errors in item_errors.items():
                        messages.error(request, f'Item {i+1} - {field}: {", ".join(errors)}')
            for error in formset.non_form_errors():
                messages.error(request, f'Items: {error}')
    else:
        form = CreditNoteForm(initial=initial)
        formset = CreditNoteItemFormSet()
    
    return render(request, 'core/credit_note_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Credit Note',
        'default_tax_rate': default_tax_rate,
    })


@login_required
def credit_note_detail(request, pk):
    """View credit note details"""
    credit_note = get_object_or_404(CreditNote, pk=pk)
    return render(request, 'core/credit_note_detail.html', {'credit_note': credit_note})


# Sales Report
@login_required
def daily_sales_report(request):
    """Sales overview with payment type and product breakdown - supports daily, weekly, monthly, yearly, and custom ranges"""
    from django.db.models import Sum, Count, Q, F
    from datetime import datetime, date, timedelta
    import calendar
    
    today = date.today()
    range_type = request.GET.get('range', 'daily')
    
    # Determine date range based on range_type
    if range_type == 'weekly':
        date_str = request.GET.get('date')
        if date_str:
            try:
                ref_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                ref_date = today
        else:
            ref_date = today
        start_date = ref_date - timedelta(days=ref_date.weekday())  # Monday
        end_date = start_date + timedelta(days=6)  # Sunday
        range_label = f"Week of {start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
    elif range_type == 'monthly':
        month_str = request.GET.get('month')
        if month_str:
            try:
                ref_date = datetime.strptime(month_str + '-01', '%Y-%m-%d').date()
            except ValueError:
                ref_date = today
        else:
            ref_date = today
        start_date = ref_date.replace(day=1)
        last_day = calendar.monthrange(ref_date.year, ref_date.month)[1]
        end_date = ref_date.replace(day=last_day)
        range_label = start_date.strftime('%B %Y')
    elif range_type == 'yearly':
        year_str = request.GET.get('year')
        if year_str:
            try:
                year = int(year_str)
            except ValueError:
                year = today.year
        else:
            year = today.year
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        range_label = str(year)
    elif range_type == 'custom':
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        try:
            start_date = datetime.strptime(date_from, '%Y-%m-%d').date() if date_from else today
        except ValueError:
            start_date = today
        try:
            end_date = datetime.strptime(date_to, '%Y-%m-%d').date() if date_to else today
        except ValueError:
            end_date = today
        if start_date > end_date:
            start_date, end_date = end_date, start_date
        range_label = f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"
    else:
        # Default: daily
        range_type = 'daily'
        date_str = request.GET.get('date')
        if date_str:
            try:
                start_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                start_date = today
        else:
            start_date = today
        end_date = start_date
        range_label = start_date.strftime('%B %d, %Y')
    
    # Get all payments for the date range
    payments = Payment.objects.filter(
        payment_date__gte=start_date,
        payment_date__lte=end_date
    ).select_related('invoice', 'invoice__client')
    
    # Calculate totals by payment method
    payment_summary = payments.values('payment_method').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('payment_method')
    
    # Calculate overall totals
    total_sales = payments.aggregate(total=Sum('amount'))['total'] or 0
    total_transactions = payments.count()
    
    # Get invoices created in the date range
    invoices_created = Invoice.objects.filter(
        issue_date__gte=start_date,
        issue_date__lte=end_date
    )
    invoices_created_total = invoices_created.aggregate(total=Sum('total_amount'))['total'] or 0
    invoices_created_count = invoices_created.count()
    
    # Get invoices paid in the date range
    invoices_paid = Invoice.objects.filter(
        payments__payment_date__gte=start_date,
        payments__payment_date__lte=end_date
    ).distinct()
    
    # Get product sales breakdown for invoices paid in this range
    product_summary = InvoiceItem.objects.filter(
        invoice__payments__payment_date__gte=start_date,
        invoice__payments__payment_date__lte=end_date
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
    
    # Calculate number of days in range
    num_days = (end_date - start_date).days + 1
    
    # Year choices for yearly dropdown (current year back to 5 years ago)
    year_choices = list(range(today.year, today.year - 6, -1))
    
    # Day of week analysis (for weekly, monthly, yearly, custom ranges)
    day_of_week_data = []
    if num_days > 1:
        # Group payments by day of week
        from django.db.models.functions import ExtractWeekDay
        dow_summary = payments.annotate(
            dow=ExtractWeekDay('payment_date')
        ).values('dow').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('dow')
        
        # Map day numbers to names (1=Sunday, 2=Monday, etc.)
        day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        day_of_week_data = [
            {
                'day': day_names[item['dow'] - 1],
                'total': item['total'],
                'count': item['count']
            }
            for item in dow_summary
        ]
    
    # Detailed breakdowns based on range type
    daily_breakdown = []
    weekly_breakdown = []
    monthly_breakdown = []
    
    # Weekly breakdown by day (for weekly view)
    if range_type == 'weekly':
        current_date = start_date
        while current_date <= end_date:
            day_payments = payments.filter(payment_date=current_date)
            day_total = day_payments.aggregate(total=Sum('amount'))['total'] or 0
            day_count = day_payments.count()
            daily_breakdown.append({
                'date': current_date,
                'day_name': current_date.strftime('%A'),
                'total': day_total,
                'count': day_count
            })
            current_date += timedelta(days=1)
    
    # Monthly breakdown by day and week (for monthly view)
    elif range_type == 'monthly':
        # Daily breakdown
        current_date = start_date
        while current_date <= end_date:
            day_payments = payments.filter(payment_date=current_date)
            day_total = day_payments.aggregate(total=Sum('amount'))['total'] or 0
            day_count = day_payments.count()
            daily_breakdown.append({
                'date': current_date,
                'day_name': current_date.strftime('%a'),
                'total': day_total,
                'count': day_count
            })
            current_date += timedelta(days=1)
        
        # Weekly breakdown
        week_start = start_date - timedelta(days=start_date.weekday())  # Start from Monday
        week_num = 1
        while week_start <= end_date:
            week_end = min(week_start + timedelta(days=6), end_date)
            # Only include weeks that overlap with the month
            if week_end >= start_date:
                actual_start = max(week_start, start_date)
                actual_end = min(week_end, end_date)
                week_payments = payments.filter(
                    payment_date__gte=actual_start,
                    payment_date__lte=actual_end
                )
                week_total = week_payments.aggregate(total=Sum('amount'))['total'] or 0
                week_count = week_payments.count()
                weekly_breakdown.append({
                    'week_num': week_num,
                    'start_date': actual_start,
                    'end_date': actual_end,
                    'total': week_total,
                    'count': week_count
                })
                week_num += 1
            week_start += timedelta(days=7)
    
    # Yearly breakdown by day, week, and month (for yearly view)
    elif range_type == 'yearly':
        # Daily breakdown (aggregated by day of year)
        from django.db.models.functions import TruncDate
        daily_summary = payments.annotate(
            date=TruncDate('payment_date')
        ).values('date').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('date')
        
        daily_breakdown = [
            {
                'date': item['date'],
                'day_name': item['date'].strftime('%a'),
                'total': item['total'],
                'count': item['count']
            }
            for item in daily_summary
        ]
        
        # Weekly breakdown
        week_start = start_date
        week_num = 1
        while week_start <= end_date:
            week_end = min(week_start + timedelta(days=6), end_date)
            week_payments = payments.filter(
                payment_date__gte=week_start,
                payment_date__lte=week_end
            )
            week_total = week_payments.aggregate(total=Sum('amount'))['total'] or 0
            week_count = week_payments.count()
            if week_total > 0 or week_count > 0:  # Only include weeks with data
                weekly_breakdown.append({
                    'week_num': week_num,
                    'start_date': week_start,
                    'end_date': week_end,
                    'total': week_total,
                    'count': week_count
                })
            week_start += timedelta(days=7)
            week_num += 1
        
        # Monthly breakdown
        for month_num in range(1, 13):
            month_start = date(start_date.year, month_num, 1)
            last_day = calendar.monthrange(start_date.year, month_num)[1]
            month_end = date(start_date.year, month_num, last_day)
            month_payments = payments.filter(
                payment_date__gte=month_start,
                payment_date__lte=month_end
            )
            month_total = month_payments.aggregate(total=Sum('amount'))['total'] or 0
            month_count = month_payments.count()
            monthly_breakdown.append({
                'month_num': month_num,
                'month_name': month_start.strftime('%B'),
                'total': month_total,
                'count': month_count
            })
    
    # Lead time analysis - calculate days between orders for each client
    from django.db.models import Min, Max
    lead_time_data = []
    
    # Get all clients who have invoices in the date range
    clients_with_invoices = Invoice.objects.filter(
        issue_date__gte=start_date,
        issue_date__lte=end_date
    ).values_list('client_id', flat=True).distinct()
    
    for client_id in clients_with_invoices:
        client = Client.objects.get(id=client_id)
        client_invoices = Invoice.objects.filter(
            client_id=client_id
        ).order_by('issue_date')
        
        if client_invoices.count() >= 2:
            # Calculate intervals between consecutive invoices
            invoice_dates = list(client_invoices.values_list('issue_date', flat=True))
            intervals = []
            for i in range(1, len(invoice_dates)):
                days_between = (invoice_dates[i] - invoice_dates[i-1]).days
                intervals.append(days_between)
            
            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                min_interval = min(intervals)
                max_interval = max(intervals)
                
                lead_time_data.append({
                    'client': client,
                    'client_id': client_id,
                    'total_orders': client_invoices.count(),
                    'avg_days_between': round(avg_interval, 1),
                    'min_days_between': min_interval,
                    'max_days_between': max_interval,
                    'last_order_date': invoice_dates[-1],
                    'first_order_date': invoice_dates[0],
                })
    
    # Sort by average days between orders
    lead_time_data.sort(key=lambda x: x['avg_days_between'])
    
    context = {
        'range_type': range_type,
        'range_label': range_label,
        'start_date': start_date,
        'end_date': end_date,
        'num_days': num_days,
        'year_choices': year_choices,
        'selected_date': start_date,  # backward compat
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
        'day_of_week_data': day_of_week_data,
        'daily_breakdown': daily_breakdown,
        'weekly_breakdown': weekly_breakdown,
        'monthly_breakdown': monthly_breakdown,
        'lead_time_data': lead_time_data,
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


# Contact Submissions Views
@login_required
def contact_submission_list(request):
    """List all contact submissions"""
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    submissions = ContactSubmission.objects.all()
    
    if status_filter:
        submissions = submissions.filter(status=status_filter)
    if search_query:
        from django.db.models import Q
        submissions = submissions.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(message__icontains=search_query)
        )
    
    return render(request, 'core/contact_submission_list.html', {
        'submissions': submissions,
        'status_filter': status_filter,
        'search_query': search_query,
    })


@login_required
def contact_submission_detail(request, pk):
    """View contact submission details"""
    submission = get_object_or_404(ContactSubmission, pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        if new_status:
            submission.status = new_status
        submission.notes = notes
        if new_status == 'resolved':
            submission.resolved_at = timezone.now()
        submission.save()
        messages.success(request, 'Contact submission updated.')
        return redirect('accounting_forms:contact_submission_detail', pk=pk)
    
    return render(request, 'core/contact_submission_detail.html', {
        'submission': submission,
    })


# Credit Note List View
@login_required
def credit_note_list(request):
    """List all credit notes"""
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    credit_notes = CreditNote.objects.select_related('invoice', 'invoice__client').all()
    
    if status_filter:
        credit_notes = credit_notes.filter(status=status_filter)
    if search_query:
        from django.db.models import Q
        credit_notes = credit_notes.filter(
            Q(credit_note_number__icontains=search_query) |
            Q(invoice__invoice_number__icontains=search_query) |
            Q(invoice__client__name__icontains=search_query) |
            Q(reason__icontains=search_query)
        )
    
    return render(request, 'core/credit_note_list.html', {
        'credit_notes': credit_notes,
        'status_filter': status_filter,
        'search_query': search_query,
    })


# Delivery Zone Views
@login_required
def delivery_zone_list(request):
    """List all delivery zones"""
    search_query = request.GET.get('search', '')
    
    zones = DeliveryZone.objects.all()
    
    if search_query:
        from django.db.models import Q
        zones = zones.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    zones = zones.order_by('name')
    
    return render(request, 'core/delivery_zone_list.html', {
        'zones': zones,
        'search_query': search_query
    })


@login_required
def delivery_zone_create(request):
    """Create a new delivery zone"""
    if request.method == 'POST':
        zone = DeliveryZone(
            name=request.POST.get('name', ''),
            postal_codes=request.POST.get('postal_codes', ''),
            delivery_fee=request.POST.get('delivery_fee', 0),
            estimated_time=request.POST.get('estimated_time', ''),
            is_active=request.POST.get('is_active') == 'on',
        )
        zone.save()
        messages.success(request, f'Delivery zone "{zone.name}" created.')
        return redirect('accounting_forms:delivery_zone_list')
    
    return render(request, 'core/delivery_zone_form.html', {
        'title': 'Create Delivery Zone',
    })


@login_required
def delivery_zone_edit(request, pk):
    """Edit a delivery zone"""
    zone = get_object_or_404(DeliveryZone, pk=pk)
    
    if request.method == 'POST':
        zone.name = request.POST.get('name', '')
        zone.postal_codes = request.POST.get('postal_codes', '')
        zone.delivery_fee = request.POST.get('delivery_fee', 0)
        zone.estimated_time = request.POST.get('estimated_time', '')
        zone.is_active = request.POST.get('is_active') == 'on'
        zone.save()
        messages.success(request, f'Delivery zone "{zone.name}" updated.')
        return redirect('accounting_forms:delivery_zone_list')
    
    return render(request, 'core/delivery_zone_form.html', {
        'title': 'Edit Delivery Zone',
        'zone': zone,
    })


@login_required
def delivery_zone_delete(request, pk):
    """Delete a delivery zone"""
    zone = get_object_or_404(DeliveryZone, pk=pk)
    if request.method == 'POST':
        zone.delete()
        messages.success(request, f'Delivery zone "{zone.name}" deleted.')
        return redirect('accounting_forms:delivery_zone_list')
    return render(request, 'core/delivery_zone_confirm_delete.html', {'zone': zone})


# Payment List View
@login_required
def payment_list(request):
    """List all payments"""
    search_query = request.GET.get('search', '')
    method_filter = request.GET.get('method', '')
    
    payments = Payment.objects.select_related('invoice', 'invoice__client').all().order_by('-payment_date')
    
    if method_filter:
        payments = payments.filter(payment_method=method_filter)
    if search_query:
        from django.db.models import Q
        payments = payments.filter(
            Q(invoice__invoice_number__icontains=search_query) |
            Q(invoice__client__name__icontains=search_query) |
            Q(reference_number__icontains=search_query)
        )
    
    total_amount = payments.aggregate(total=Sum('amount'))['total'] or 0
    
    return render(request, 'core/payment_list.html', {
        'payments': payments,
        'search_query': search_query,
        'method_filter': method_filter,
        'total_amount': total_amount,
    })


@login_required
@require_http_methods(["POST"])
def payment_delete(request, pk):
    """Delete a payment and update the related invoice"""
    payment = get_object_or_404(Payment, pk=pk)
    invoice = payment.invoice
    payment_amount = payment.amount
    payment_number = payment.payment_number
    
    # Delete the payment
    payment.delete()
    
    # Recalculate invoice paid_amount from remaining payments
    invoice.paid_amount = sum(p.amount for p in invoice.payments.all())
    invoice.calculate_totals()
    
    messages.success(request, f'Payment {payment_number} (R{payment_amount:,.2f}) deleted successfully. Invoice updated.')
    
    # Redirect to referring page or payment list
    referer = request.META.get('HTTP_REFERER')
    if referer and 'payments' in referer:
        return redirect(referer)
    return redirect('accounting_forms:payment_list')


# Supplier Views
@login_required
def supplier_list(request):
    """List all suppliers"""
    search_query = request.GET.get('search', '')
    suppliers = Supplier.objects.all()
    
    if search_query:
        from django.db.models import Q
        suppliers = suppliers.filter(
            Q(name__icontains=search_query) |
            Q(contact_person__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    return render(request, 'core/supplier_list.html', {
        'suppliers': suppliers,
        'search_query': search_query,
    })


@login_required
def supplier_create(request):
    """Create a new supplier"""
    if request.method == 'POST':
        supplier = Supplier(
            name=request.POST.get('name', ''),
            contact_person=request.POST.get('contact_person', ''),
            email=request.POST.get('email', ''),
            phone=request.POST.get('phone', ''),
            address=request.POST.get('address', ''),
            tax_number=request.POST.get('tax_number', ''),
            bank_name=request.POST.get('bank_name', ''),
            bank_account_number=request.POST.get('bank_account_number', ''),
            bank_branch_code=request.POST.get('bank_branch_code', ''),
            notes=request.POST.get('notes', ''),
        )
        supplier.save()
        messages.success(request, f'Supplier "{supplier.name}" created.')
        return redirect('accounting_forms:supplier_list')
    
    return render(request, 'core/supplier_form.html', {
        'title': 'Create Supplier',
    })


@login_required
def supplier_edit(request, pk):
    """Edit a supplier"""
    supplier = get_object_or_404(Supplier, pk=pk)
    
    if request.method == 'POST':
        supplier.name = request.POST.get('name', '')
        supplier.contact_person = request.POST.get('contact_person', '')
        supplier.email = request.POST.get('email', '')
        supplier.phone = request.POST.get('phone', '')
        supplier.address = request.POST.get('address', '')
        supplier.tax_number = request.POST.get('tax_number', '')
        supplier.bank_name = request.POST.get('bank_name', '')
        supplier.bank_account_number = request.POST.get('bank_account_number', '')
        supplier.bank_branch_code = request.POST.get('bank_branch_code', '')
        supplier.notes = request.POST.get('notes', '')
        supplier.is_active = request.POST.get('is_active') == 'on'
        supplier.save()
        messages.success(request, f'Supplier "{supplier.name}" updated.')
        return redirect('accounting_forms:supplier_list')
    
    return render(request, 'core/supplier_form.html', {
        'title': 'Edit Supplier',
        'supplier': supplier,
    })


@login_required
def supplier_detail(request, pk):
    """View supplier details"""
    supplier = get_object_or_404(Supplier, pk=pk)
    expenses = supplier.expenses.all()[:20]
    return render(request, 'core/supplier_detail.html', {
        'supplier': supplier,
        'expenses': expenses,
    })


# Journal Entry Views
@login_required
def journal_entry_list(request):
    """List all journal entries"""
    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('type', '')
    search_query = request.GET.get('search', '')
    
    entries = JournalEntry.objects.all()
    
    if status_filter:
        entries = entries.filter(status=status_filter)
    if type_filter:
        entries = entries.filter(entry_type=type_filter)
    if search_query:
        from django.db.models import Q
        entries = entries.filter(
            Q(entry_number__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(reference__icontains=search_query)
        )
    
    return render(request, 'core/journal_entry_list.html', {
        'entries': entries,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'search_query': search_query,
    })


@login_required
def journal_entry_detail(request, pk):
    """View journal entry details"""
    entry = get_object_or_404(JournalEntry, pk=pk)
    return render(request, 'core/journal_entry_detail.html', {
        'entry': entry,
    })
