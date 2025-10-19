from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db import transaction
from .models import Client, Product, Quote, Invoice, Payment, CreditNote
from .forms import (
    ClientForm, ProductForm, QuoteForm, QuoteItemFormSet,
    InvoiceForm, InvoiceItemFormSet, PaymentForm,
    CreditNoteForm, CreditNoteItemFormSet, CompanySettingsForm
)


# Client Views
@login_required
def client_list(request):
    """List all clients"""
    clients = Client.objects.all().order_by('-created_at')
    return render(request, 'core/client_list.html', {'clients': clients})


@login_required
def client_create(request):
    """Create a new client"""
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            messages.success(request, f'Client "{client.name}" created successfully!')
            return redirect('client_detail', pk=client.pk)
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
            return redirect('client_detail', pk=client.pk)
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
    quotes = client.quotes.all().order_by('-quote_date')[:5]
    invoices = client.invoices.all().order_by('-invoice_date')[:5]
    
    return render(request, 'core/client_detail.html', {
        'client': client,
        'quotes': quotes,
        'invoices': invoices
    })


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
            return redirect('product_list')
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
            return redirect('product_list')
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
    """List all quotes"""
    quotes = Quote.objects.all().order_by('-quote_date')
    return render(request, 'core/quote_list.html', {'quotes': quotes})


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
            
            formset.instance = quote
            formset.save()
            
            quote.calculate_totals()
            
            messages.success(request, f'Quote {quote.quote_number} created successfully!')
            return redirect('quote_detail', pk=quote.pk)
    else:
        form = QuoteForm()
        formset = QuoteItemFormSet()
    
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
            return redirect('quote_detail', pk=quote.pk)
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
    """List all invoices"""
    invoices = Invoice.objects.all().order_by('-invoice_date')
    return render(request, 'core/invoice_list.html', {'invoices': invoices})


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
            
            formset.instance = invoice
            formset.save()
            
            invoice.calculate_totals()
            
            messages.success(request, f'Invoice {invoice.invoice_number} created successfully!')
            return redirect('invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceForm()
        formset = InvoiceItemFormSet()
    
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
            return redirect('invoice_detail', pk=invoice.pk)
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
            return redirect('invoice_detail', pk=payment.invoice.pk)
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
            return redirect('credit_note_detail', pk=credit_note.pk)
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
            invoice_date__gte=first_day,
            status='paid'
        ).aggregate(total=Sum('total_amount'))['total'] or 0,
        'outstanding_amount': Invoice.objects.filter(
            status__in=['draft', 'sent']
        ).aggregate(total=Sum('total_amount'))['total'] or 0,
    }
    
    recent_invoices = Invoice.objects.all().order_by('-invoice_date')[:5]
    recent_quotes = Quote.objects.all().order_by('-quote_date')[:5]
    recent_payments = Payment.objects.all().order_by('-payment_date')[:5]
    
    return render(request, 'core/dashboard.html', {
        'stats': stats,
        'recent_invoices': recent_invoices,
        'recent_quotes': recent_quotes,
        'recent_payments': recent_payments,
    })
