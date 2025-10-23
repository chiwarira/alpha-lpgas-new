from django.contrib import admin
from .models import (
    HeroBanner, CompanySettings, Client, Category, Product, ProductVariant,
    Quote, QuoteItem, Invoice, InvoiceItem, Payment, CreditNote, CreditNoteItem,
    DeliveryZone, PromoCode, Order, OrderItem, OrderStatusHistory
)


@admin.register(HeroBanner)
class HeroBannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'overlay_color', 'is_active', 'order', 'created_at']
    list_filter = ['is_active', 'overlay_color']
    list_editable = ['is_active', 'order']
    search_fields = ['title', 'subtitle']
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'subtitle')
        }),
        ('Background & Overlay', {
            'fields': ('background_image', 'overlay_color', 'overlay_opacity'),
            'description': 'Upload a background image and customize the overlay color and opacity. The overlay helps ensure text remains readable.'
        }),
        ('Call to Action', {
            'fields': ('cta_text', 'cta_link', 'secondary_cta_text', 'secondary_cta_link')
        }),
        ('Settings', {
            'fields': ('is_active', 'order')
        }),
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
    list_display = ['customer_id', 'name', 'email', 'phone', 'city', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['customer_id', 'name', 'email', 'phone', 'tax_id']
    readonly_fields = ['customer_id', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'email', 'phone', 'is_active')
        }),
        ('Address', {
            'fields': ('address', 'city', 'postal_code')
        }),
        ('Additional', {
            'fields': ('tax_id', 'notes')
        }),
        ('System', {
            'fields': ('customer_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'order', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order', 'is_active']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'unit_price', 'category', 'weight', 'stock_quantity', 'is_active', 'show_on_website', 'is_featured']
    list_filter = ['is_active', 'show_on_website', 'available_for_invoicing', 'is_featured', 'category', 'is_exchange', 'track_inventory']
    search_fields = ['name', 'sku', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'show_on_website', 'is_featured']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'sku', 'category', 'description', 'short_description')
        }),
        ('Pricing', {
            'fields': ('unit_price', 'compare_at_price', 'cost_price', 'tax_rate', 'unit')
        }),
        ('LPG Specific', {
            'fields': ('weight', 'is_exchange', 'requires_empty_cylinder')
        }),
        ('Images', {
            'fields': ('main_image', 'image_2', 'image_3', 'image_4'),
            'classes': ('collapse',)
        }),
        ('Inventory', {
            'fields': ('track_inventory', 'stock_quantity', 'low_stock_threshold')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Status & Visibility', {
            'fields': ('is_active', 'show_on_website', 'available_for_invoicing', 'is_featured', 'order')
        }),
    )
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


# E-commerce Admin

@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'delivery_fee', 'minimum_order', 'estimated_delivery_time', 'is_active', 'order']
    list_editable = ['delivery_fee', 'is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['name', 'postal_codes']


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'times_used', 'max_uses', 'valid_from', 'valid_until', 'is_active']
    list_filter = ['is_active', 'discount_type']
    search_fields = ['code', 'description']
    readonly_fields = ['times_used', 'created_at', 'updated_at']


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'sku', 'price_adjustment', 'stock_quantity', 'is_active', 'order']
    list_editable = ['is_active', 'order']
    list_filter = ['is_active', 'product']
    search_fields = ['name', 'sku']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total_price']


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 1
    readonly_fields = ['created_at', 'created_by']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer_name', 'status', 'payment_status', 'payment_method', 'total', 'created_at']
    list_filter = ['status', 'payment_status', 'payment_method', 'delivery_zone', 'created_at']
    search_fields = ['order_number', 'customer_name', 'customer_email', 'customer_phone']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
    fieldsets = (
        ('Order Info', {
            'fields': ('order_number', 'status', 'created_at', 'updated_at')
        }),
        ('Customer', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('Delivery', {
            'fields': ('delivery_address', 'delivery_zone', 'delivery_notes', 'estimated_delivery', 'delivered_at')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'delivery_fee', 'discount_amount', 'promo_code', 'total')
        }),
        ('Payment', {
            'fields': ('payment_method', 'payment_status', 'yoco_payment_id')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
