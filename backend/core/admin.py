from django.contrib import admin
from .models import (
    CompanySettings, Client, Product, Quote, QuoteItem, Invoice, InvoiceItem,
    Payment, CreditNote, CreditNoteItem
)


@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Company Information', {
            'fields': ('company_name', 'registration_number', 'vat_number', 'phone', 'email', 'address')
        }),
        ('Banking Details', {
            'fields': ('bank_name', 'account_name', 'account_number', 'account_type', 'branch_code', 'payment_reference_note')
        }),
        ('Statement Settings', {
            'fields': ('statement_footer_text',)
        }),
        ('WhatsApp Message Templates', {
            'fields': ('whatsapp_invoice_message', 'whatsapp_quote_message', 'whatsapp_statement_message'),
            'description': 'Customize WhatsApp message templates. Available variables will be replaced automatically.'
        }),
        ('System', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['updated_at']
    
    def has_add_permission(self, request):
        # Prevent adding more than one instance
        return not CompanySettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion
        return False


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['customer_id', 'name', 'email', 'phone', 'city', 'country', 'is_active', 'created_at']
    list_filter = ['is_active', 'country', 'created_at']
    search_fields = ['customer_id', 'name', 'email', 'phone', 'tax_id']
    readonly_fields = ['customer_id', 'created_at', 'updated_at']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'unit_price', 'tax_rate', 'unit', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'sku', 'description']
    readonly_fields = ['created_at', 'updated_at']


class QuoteItemInline(admin.TabularInline):
    model = QuoteItem
    extra = 1


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ['quote_number', 'client', 'issue_date', 'expiry_date', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'issue_date', 'created_at']
    search_fields = ['quote_number', 'client__name']
    readonly_fields = ['subtotal', 'tax_amount', 'total_amount', 'created_at', 'updated_at']
    inlines = [QuoteItemInline]


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'client', 'issue_date', 'due_date', 'status', 'total_amount', 'paid_amount', 'balance', 'created_at']
    list_filter = ['status', 'issue_date', 'due_date', 'created_at']
    search_fields = ['invoice_number', 'client__name']
    readonly_fields = ['subtotal', 'tax_amount', 'total_amount', 'paid_amount', 'balance', 'created_at', 'updated_at']
    inlines = [InvoiceItemInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_number', 'invoice', 'payment_date', 'amount', 'payment_method', 'created_at']
    list_filter = ['payment_method', 'payment_date', 'created_at']
    search_fields = ['payment_number', 'reference_number', 'invoice__invoice_number']
    readonly_fields = ['created_at', 'updated_at']


class CreditNoteItemInline(admin.TabularInline):
    model = CreditNoteItem
    extra = 1


@admin.register(CreditNote)
class CreditNoteAdmin(admin.ModelAdmin):
    list_display = ['credit_note_number', 'client', 'invoice', 'issue_date', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'issue_date', 'created_at']
    search_fields = ['credit_note_number', 'client__name', 'invoice__invoice_number']
    readonly_fields = ['subtotal', 'tax_amount', 'total_amount', 'created_at', 'updated_at']
    inlines = [CreditNoteItemInline]
