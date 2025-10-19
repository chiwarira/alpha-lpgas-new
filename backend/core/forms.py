from django import forms
from django.core.exceptions import ValidationError
from .models import (
    Client, Product, Quote, QuoteItem, Invoice, InvoiceItem,
    Payment, CreditNote, CreditNoteItem, CompanySettings
)


class ClientForm(forms.ModelForm):
    """Form for creating and updating clients"""
    
    class Meta:
        model = Client
        fields = [
            'name', 'email', 'phone', 'address', 'city', 
            'postal_code', 'tax_id', 'is_active', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Client Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '074 454 5665'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Street address'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cape Town'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '7975'
            }),
            'tax_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tax ID / VAT Number (optional)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check for duplicate email (excluding current instance)
            qs = Client.objects.filter(email=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError('A client with this email already exists.')
        return email


class ProductForm(forms.ModelForm):
    """Form for creating and updating products/services"""
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'sku', 'unit', 'unit_price',
            'cost_price', 'tax_rate', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Product/Service Name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Product description'
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'SKU/Code'
            }),
            'unit': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Unit (e.g., kg, piece, hour)'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'cost_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00 (optional)',
                'step': '0.01'
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': '15.00',
                'step': '0.01'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        
    def clean_sku(self):
        sku = self.cleaned_data.get('sku')
        if sku:
            # Check for duplicate SKU (excluding current instance)
            qs = Product.objects.filter(sku=sku)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError('A product with this SKU already exists.')
        return sku


class QuoteForm(forms.ModelForm):
    """Form for creating and updating quotes"""
    
    class Meta:
        model = Quote
        fields = [
            'client', 'issue_date', 'expiry_date', 'status',
            'terms', 'notes'
        ]
        widgets = {
            'client': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'issue_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'terms': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Payment terms and conditions'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes'
            }),
        }


class QuoteItemForm(forms.ModelForm):
    """Form for quote line items"""
    
    class Meta:
        model = QuoteItem
        fields = ['product', 'description', 'quantity', 'unit_price', 'tax_rate']
        widgets = {
            'product': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Item description'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '1',
                'step': '0.01',
                'min': '0.01'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': '15.00',
                'step': '0.01'
            }),
        }


class InvoiceForm(forms.ModelForm):
    """Form for creating and updating invoices"""
    
    class Meta:
        model = Invoice
        fields = [
            'client', 'issue_date', 'due_date', 'status',
            'terms', 'notes'
        ]
        widgets = {
            'client': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'issue_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'terms': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Payment terms and conditions'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes'
            }),
        }


class InvoiceItemForm(forms.ModelForm):
    """Form for invoice line items"""
    
    class Meta:
        model = InvoiceItem
        fields = ['product', 'description', 'quantity', 'unit_price', 'tax_rate']
        widgets = {
            'product': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Item description'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '1',
                'step': '0.01',
                'min': '0.01'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': '15.00',
                'step': '0.01'
            }),
        }


class PaymentForm(forms.ModelForm):
    """Form for recording payments"""
    
    class Meta:
        model = Payment
        fields = [
            'invoice', 'payment_date', 'amount', 'payment_method',
            'reference_number', 'notes'
        ]
        widgets = {
            'invoice': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-select'
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Payment reference/transaction ID'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional notes'
            }),
        }
        
    def clean(self):
        cleaned_data = super().clean()
        invoice = cleaned_data.get('invoice')
        amount = cleaned_data.get('amount')
        
        if invoice and amount:
            # Check if payment amount doesn't exceed remaining balance
            remaining = invoice.total_amount - invoice.paid_amount
            if amount > remaining:
                raise ValidationError(
                    f'Payment amount (R{amount}) exceeds remaining balance (R{remaining})'
                )
        
        return cleaned_data


class CreditNoteForm(forms.ModelForm):
    """Form for creating credit notes"""
    
    class Meta:
        model = CreditNote
        fields = [
            'invoice', 'issue_date', 'reason', 'notes'
        ]
        widgets = {
            'invoice': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'issue_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Reason for credit note',
                'required': True
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional notes'
            }),
        }


class CreditNoteItemForm(forms.ModelForm):
    """Form for credit note line items"""
    
    class Meta:
        model = CreditNoteItem
        fields = ['product', 'description', 'quantity', 'unit_price', 'tax_rate']
        widgets = {
            'product': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Item description'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '1',
                'step': '0.01',
                'min': '0.01'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': '15.00',
                'step': '0.01'
            }),
        }


class CompanySettingsForm(forms.ModelForm):
    """Form for company settings"""
    
    class Meta:
        model = CompanySettings
        fields = [
            'company_name', 'email', 'phone', 'address',
            'vat_number', 'registration_number',
            'bank_name', 'account_name', 'account_number',
            'account_type', 'branch_code', 'payment_reference_note'
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Alpha LPGas'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'info@alphalpgas.co.za'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '074 454 5665'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Sunnyacres Shopping Centre, Fish Hoek'
            }),
            'vat_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '9415233222'
            }),
            'registration_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '2023/822513/07'
            }),
            'bank_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nedbank'
            }),
            'account_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Alpha LPGas'
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Account Number'
            }),
            'account_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Current'
            }),
            'branch_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Branch Code'
            }),
            'payment_reference_note': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Please use your address as reference'
            }),
        }


# Formsets for handling multiple items
from django.forms import inlineformset_factory

QuoteItemFormSet = inlineformset_factory(
    Quote,
    QuoteItem,
    form=QuoteItemForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)

InvoiceItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)

CreditNoteItemFormSet = inlineformset_factory(
    CreditNote,
    CreditNoteItem,
    form=CreditNoteItemForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)
