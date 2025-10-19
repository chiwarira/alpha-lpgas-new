from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    CompanySettings, Client, Product, Quote, QuoteItem, Invoice, InvoiceItem,
    Payment, CreditNote, CreditNoteItem
)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff']
        read_only_fields = ['id']


class CompanySettingsSerializer(serializers.ModelSerializer):
    """Serializer for CompanySettings model"""
    class Meta:
        model = CompanySettings
        fields = [
            'id', 'company_name', 'registration_number', 'vat_number', 'phone', 'email', 'address',
            'bank_name', 'account_name', 'account_number', 'account_type', 'branch_code',
            'payment_reference_note', 'statement_footer_text', 
            'whatsapp_invoice_message', 'whatsapp_quote_message', 'whatsapp_statement_message',
            'updated_at'
        ]
        read_only_fields = ['id', 'updated_at']


class ClientSerializer(serializers.ModelSerializer):
    """Serializer for Client model"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Client
        fields = [
            'id', 'customer_id', 'name', 'email', 'phone', 'address', 'city', 'state',
            'postal_code', 'country', 'tax_id', 'notes', 'is_active',
            'created_at', 'updated_at', 'created_by', 'created_by_name'
        ]
        read_only_fields = ['id', 'customer_id', 'created_at', 'updated_at', 'created_by']


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model"""
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'sku', 'unit_price', 'cost_price',
            'tax_rate', 'unit', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class QuoteItemSerializer(serializers.ModelSerializer):
    """Serializer for QuoteItem model"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    
    class Meta:
        model = QuoteItem
        fields = [
            'id', 'quote', 'product', 'product_name', 'product_sku',
            'description', 'quantity', 'unit_price', 'tax_rate',
            'total', 'tax_amount'
        ]
        read_only_fields = ['id', 'total', 'tax_amount']


class QuoteSerializer(serializers.ModelSerializer):
    """Serializer for Quote model"""
    items = QuoteItemSerializer(many=True, read_only=True)
    client_name = serializers.CharField(source='client.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Quote
        fields = [
            'id', 'quote_number', 'client', 'client_name', 'issue_date',
            'expiry_date', 'status', 'subtotal', 'tax_amount', 'total_amount',
            'notes', 'terms', 'items', 'created_at', 'updated_at',
            'created_by', 'created_by_name'
        ]
        read_only_fields = ['id', 'subtotal', 'tax_amount', 'total_amount', 'created_at', 'updated_at', 'created_by']


class InvoiceItemSerializer(serializers.ModelSerializer):
    """Serializer for InvoiceItem model"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    product_code = serializers.CharField(source='product.sku', read_only=True)
    
    class Meta:
        model = InvoiceItem
        fields = [
            'id', 'invoice', 'product', 'product_name', 'product_sku', 'product_code',
            'description', 'quantity', 'unit_price', 'tax_rate',
            'total', 'tax_amount'
        ]
        read_only_fields = ['id', 'total', 'tax_amount']


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for Invoice model"""
    items = InvoiceItemSerializer(many=True, read_only=True)
    client_name = serializers.CharField(source='client.name', read_only=True)
    client_email = serializers.EmailField(source='client.email', read_only=True)
    client_phone = serializers.CharField(source='client.phone', read_only=True)
    client_address = serializers.CharField(source='client.address', read_only=True)
    client_city = serializers.CharField(source='client.city', read_only=True)
    client_state = serializers.CharField(source='client.state', read_only=True)
    client_postal_code = serializers.CharField(source='client.postal_code', read_only=True)
    client_country = serializers.CharField(source='client.country', read_only=True)
    client_tax_id = serializers.CharField(source='client.tax_id', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    quote_number = serializers.CharField(source='quote.quote_number', read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'client', 'client_name', 'client_email',
            'client_phone', 'client_address', 'client_city', 'client_state',
            'client_postal_code', 'client_country', 'client_tax_id', 'quote',
            'quote_number', 'issue_date', 'due_date', 'status', 'subtotal',
            'tax_amount', 'total_amount', 'paid_amount', 'balance',
            'notes', 'terms', 'items', 'created_at', 'updated_at',
            'created_by', 'created_by_name'
        ]
        read_only_fields = ['id', 'subtotal', 'tax_amount', 'total_amount', 'balance', 'created_at', 'updated_at', 'created_by']


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    client_name = serializers.CharField(source='invoice.client.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_number', 'invoice', 'invoice_number', 'client_name',
            'payment_date', 'amount', 'payment_method', 'reference_number',
            'notes', 'created_at', 'updated_at', 'created_by', 'created_by_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


class CreditNoteItemSerializer(serializers.ModelSerializer):
    """Serializer for CreditNoteItem model"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    
    class Meta:
        model = CreditNoteItem
        fields = [
            'id', 'credit_note', 'product', 'product_name', 'product_sku',
            'description', 'quantity', 'unit_price', 'tax_rate',
            'total', 'tax_amount'
        ]
        read_only_fields = ['id', 'total', 'tax_amount']


class CreditNoteSerializer(serializers.ModelSerializer):
    """Serializer for CreditNote model"""
    items = CreditNoteItemSerializer(many=True, read_only=True)
    client_name = serializers.CharField(source='client.name', read_only=True)
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = CreditNote
        fields = [
            'id', 'credit_note_number', 'invoice', 'invoice_number',
            'client', 'client_name', 'issue_date', 'status', 'subtotal',
            'tax_amount', 'total_amount', 'reason', 'notes', 'items',
            'created_at', 'updated_at', 'created_by', 'created_by_name'
        ]
        read_only_fields = ['id', 'subtotal', 'tax_amount', 'total_amount', 'created_at', 'updated_at', 'created_by']
