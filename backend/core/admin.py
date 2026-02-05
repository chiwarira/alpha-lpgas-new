from django.contrib import admin
from .models import (
    HeroBanner, CompanySettings, Client, Category, Product, ProductVariant,
    Quote, QuoteItem, Invoice, InvoiceItem, Payment, CreditNote, CreditNoteItem,
    DeliveryZone, PromoCode, Driver, Order, OrderItem, OrderStatusHistory, ContactSubmission, Testimonial,
    CustomScript, Supplier, ExpenseCategory, Expense, JournalEntry, TaxPeriod,
    CylinderSize, GasStock, StockMovement, StockPurchase, StockPurchaseItem,
    LoyaltyCard, LoyaltyTransaction
)
from .admin_loyalty import LoyaltyCardAdmin, LoyaltyTransactionAdmin


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
        ('Branding', {
            'fields': ('logo', 'favicon'),
            'description': 'Upload company logo and favicon. Logo will appear on invoices and website. Favicon appears in browser tabs.'
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
    ordering = ['-created_at']
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
    list_display = ['quote_number', 'client_name', 'issue_date', 'expiry_date', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'issue_date', 'created_at']
    search_fields = ['quote_number', 'client__name']
    readonly_fields = ['subtotal', 'tax_amount', 'total_amount', 'created_at', 'updated_at']
    ordering = ['-created_at']
    inlines = [QuoteItemInline]
    
    @admin.display(description='Client', ordering='client__name')
    def client_name(self, obj):
        return obj.client.name if obj.client else '-'


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'client_name', 'delivery_zone', 'issue_date', 'due_date', 'status', 'total_amount', 'paid_amount', 'balance_display', 'created_at']
    list_filter = ['status', 'delivery_zone', 'issue_date', 'due_date', 'created_at']
    search_fields = ['invoice_number', 'client__name']
    autocomplete_fields = ['client', 'delivery_zone']
    readonly_fields = ['subtotal', 'tax_amount', 'total_amount', 'paid_amount', 'balance', 'created_at', 'updated_at']
    ordering = ['-created_at']
    inlines = [InvoiceItemInline]
    
    @admin.display(description='Client', ordering='client__name')
    def client_name(self, obj):
        return obj.client.name if obj.client else '-'
    
    @admin.display(description='Balance', ordering='total_amount')
    def balance_display(self, obj):
        return obj.balance


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
    ordering = ['order', 'name']


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'phone', 'vehicle_registration', 'status', 'total_deliveries', 'rating', 'is_active']
    list_filter = ['status', 'is_active', 'vehicle_type']
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'phone', 'vehicle_registration', 'id_number']
    readonly_fields = ['total_deliveries', 'created_at', 'updated_at']
    list_editable = ['status', 'is_active']
    
    fieldsets = (
        ('User Account', {
            'fields': ('user',)
        }),
        ('Personal Information', {
            'fields': ('phone', 'id_number', 'address')
        }),
        ('Vehicle Information', {
            'fields': ('vehicle_type', 'vehicle_registration', 'vehicle_make_model')
        }),
        ('License Information', {
            'fields': ('drivers_license_number', 'license_expiry_date')
        }),
        ('Status & Performance', {
            'fields': ('status', 'is_active', 'total_deliveries', 'rating')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_full_name.short_description = 'Driver Name'
    get_full_name.admin_order_field = 'user__first_name'


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
    list_display = ['order_number', 'customer_name', 'driver_name', 'status', 'payment_status', 'payment_method', 'total', 'created_at']
    list_filter = ['status', 'payment_status', 'payment_method', 'delivery_zone', 'assigned_driver', 'created_at']
    search_fields = ['order_number', 'customer_name', 'customer_email', 'customer_phone']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    ordering = ['-created_at']
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    list_editable = ['status']
    
    @admin.display(description='Driver', ordering='assigned_driver__user__first_name')
    def driver_name(self, obj):
        return obj.assigned_driver.user.get_full_name() if obj.assigned_driver else '-'
    
    fieldsets = (
        ('Order Info', {
            'fields': ('order_number', 'status', 'created_at', 'updated_at')
        }),
        ('Customer', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('Delivery', {
            'fields': ('delivery_address', 'delivery_zone', 'assigned_driver', 'delivery_notes', 'estimated_delivery', 'delivered_at')
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


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at', 'ip_address', 'user_agent']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Message', {
            'fields': ('subject', 'message')
        }),
        ('Management', {
            'fields': ('status', 'assigned_to', 'notes', 'resolved_at')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Disable adding submissions through admin (only through API)
        return False


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'location', 'rating', 'is_active', 'order', 'created_at']
    list_filter = ['is_active', 'rating', 'created_at']
    search_fields = ['customer_name', 'location', 'review', 'company_name']
    list_editable = ['is_active', 'order']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('customer_name', 'location', 'company_name')
        }),
        ('Review', {
            'fields': ('review', 'rating')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'order', 'avatar_color')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CustomScript)
class CustomScriptAdmin(admin.ModelAdmin):
    list_display = ['name', 'placement', 'is_active', 'apply_to_frontend', 'apply_to_backend', 'order', 'updated_at']
    list_filter = ['is_active', 'placement', 'apply_to_frontend', 'apply_to_backend']
    search_fields = ['name', 'script_code', 'notes']
    list_editable = ['is_active', 'order']
    readonly_fields = ['created_at', 'updated_at']
    fields = ['name', 'placement', 'script_code', 'is_active', 'order', 'apply_to_frontend', 'apply_to_backend', 'notes', 'created_at', 'updated_at']


# ============================================
# ACCOUNTING / JOURNAL ENTRIES ADMIN
# ============================================

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'phone', 'email', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'contact_person', 'email', 'phone']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'contact_person', 'email', 'phone', 'address')
        }),
        ('Tax Information', {
            'fields': ('tax_number',)
        }),
        ('Banking Details', {
            'fields': ('bank_name', 'bank_account_number', 'bank_branch_code'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes', 'is_active'),
        }),
    )


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'tax_deductible', 'is_active', 'order']
    list_filter = ['is_active', 'tax_deductible', 'parent']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'order', 'tax_deductible']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['expense_number', 'date', 'supplier', 'category', 'description_short', 'total_amount', 'vat_amount', 'payment_status', 'is_tax_deductible']
    list_filter = ['payment_status', 'category', 'is_tax_deductible', 'date', 'supplier']
    search_fields = ['expense_number', 'description', 'invoice_number', 'supplier__name']
    date_hierarchy = 'date'
    readonly_fields = ['expense_number', 'subtotal', 'vat_amount', 'created_at', 'updated_at']
    autocomplete_fields = ['supplier', 'category']
    
    fieldsets = (
        ('Expense Details', {
            'fields': ('expense_number', 'date', 'supplier', 'category', 'description')
        }),
        ('Amounts', {
            'fields': ('total_amount', 'vat_rate', 'vat_amount', 'subtotal'),
            'description': 'Enter total amount (VAT inclusive). VAT will be calculated automatically.'
        }),
        ('Payment', {
            'fields': ('payment_status', 'payment_method', 'payment_date', 'payment_reference')
        }),
        ('Receipt/Invoice', {
            'fields': ('invoice_number', 'receipt_image')
        }),
        ('Tax', {
            'fields': ('is_tax_deductible', 'tax_period')
        }),
        ('Notes & Metadata', {
            'fields': ('notes', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ['entry_number', 'date', 'entry_type', 'description_short', 'debit_amount', 'credit_amount', 'status']
    list_filter = ['status', 'entry_type', 'date']
    search_fields = ['entry_number', 'description', 'reference']
    date_hierarchy = 'date'
    readonly_fields = ['entry_number', 'created_at', 'updated_at', 'posted_at', 'posted_by']
    
    fieldsets = (
        ('Entry Details', {
            'fields': ('entry_number', 'date', 'entry_type', 'description', 'reference')
        }),
        ('Related Records', {
            'fields': ('invoice', 'expense', 'payment'),
            'classes': ('collapse',)
        }),
        ('Amounts', {
            'fields': ('debit_amount', 'credit_amount')
        }),
        ('Status', {
            'fields': ('status', 'notes')
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at', 'posted_at', 'posted_by'),
            'classes': ('collapse',)
        }),
    )
    
    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['post_entries', 'void_entries']
    
    def post_entries(self, request, queryset):
        count = 0
        for entry in queryset.filter(status='draft'):
            entry.post(request.user)
            count += 1
        self.message_user(request, f'{count} journal entries posted.')
    post_entries.short_description = 'Post selected entries'
    
    def void_entries(self, request, queryset):
        count = queryset.filter(status='posted').update(status='void')
        self.message_user(request, f'{count} journal entries voided.')
    void_entries.short_description = 'Void selected entries'


@admin.register(TaxPeriod)
class TaxPeriodAdmin(admin.ModelAdmin):
    list_display = ['name', 'period_type', 'start_date', 'end_date', 'status', 'total_income', 'total_expenses', 'vat_payable']
    list_filter = ['status', 'period_type']
    search_fields = ['name']
    readonly_fields = ['total_income', 'total_expenses', 'output_vat', 'input_vat', 'vat_payable', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Period Details', {
            'fields': ('name', 'period_type', 'start_date', 'end_date', 'status')
        }),
        ('Calculated Totals', {
            'fields': ('total_income', 'total_expenses', 'output_vat', 'input_vat', 'vat_payable'),
            'description': 'These values are calculated from invoices and expenses within this period.'
        }),
        ('Filing', {
            'fields': ('filed_date', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['calculate_totals']
    
    def calculate_totals(self, request, queryset):
        for period in queryset:
            period.calculate_totals()
        self.message_user(request, f'Totals calculated for {queryset.count()} periods.')
    calculate_totals.short_description = 'Calculate totals for selected periods'


# ============================================
# STOCK MANAGEMENT ADMIN
# ============================================

@admin.register(CylinderSize)
class CylinderSizeAdmin(admin.ModelAdmin):
    list_display = ['name', 'weight_kg', 'is_active', 'order']
    list_editable = ['is_active', 'order']
    search_fields = ['name']


@admin.register(GasStock)
class GasStockAdmin(admin.ModelAdmin):
    list_display = ['cylinder_size', 'quantity', 'total_volume_display', 'reorder_level', 'stock_status', 'updated_at']
    list_filter = ['cylinder_size']
    readonly_fields = ['updated_at']
    
    def total_volume_display(self, obj):
        return f"{obj.total_volume_kg} kg"
    total_volume_display.short_description = 'Total Volume'
    
    def stock_status(self, obj):
        if obj.is_low_stock:
            return '⚠️ Low Stock'
        return '✅ OK'
    stock_status.short_description = 'Status'


class StockPurchaseItemInline(admin.TabularInline):
    model = StockPurchaseItem
    extra = 1
    fields = ['cylinder_size', 'quantity', 'unit_cost', 'total_cost', 'volume_kg_display']
    readonly_fields = ['total_cost', 'volume_kg_display']
    
    def volume_kg_display(self, obj):
        if obj.pk:
            return f"{obj.volume_kg} kg"
        return "-"
    volume_kg_display.short_description = 'Volume (kg)'


@admin.register(StockPurchase)
class StockPurchaseAdmin(admin.ModelAdmin):
    list_display = ['purchase_number', 'date', 'supplier', 'total_cylinders', 'total_volume_kg', 'total_cost', 'created_at']
    list_filter = ['date', 'supplier']
    search_fields = ['purchase_number', 'invoice_number', 'supplier__name']
    date_hierarchy = 'date'
    readonly_fields = ['purchase_number', 'total_cylinders', 'total_volume_kg', 'total_cost', 'created_at', 'updated_at']
    autocomplete_fields = ['supplier', 'expense']
    inlines = [StockPurchaseItemInline]
    
    fieldsets = (
        ('Purchase Details', {
            'fields': ('purchase_number', 'date', 'supplier', 'invoice_number')
        }),
        ('Linked Records', {
            'fields': ('expense',),
            'classes': ('collapse',)
        }),
        ('Totals', {
            'fields': ('total_cylinders', 'total_volume_kg', 'total_cost'),
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['movement_number', 'date', 'movement_type', 'cylinder_size', 'quantity', 'volume_kg_display', 'reference', 'created_at']
    list_filter = ['movement_type', 'cylinder_size', 'date']
    search_fields = ['movement_number', 'reference', 'notes']
    date_hierarchy = 'date'
    readonly_fields = ['movement_number', 'created_at']
    
    fieldsets = (
        ('Movement Details', {
            'fields': ('movement_number', 'date', 'movement_type', 'cylinder_size', 'quantity')
        }),
        ('Reference', {
            'fields': ('reference', 'supplier', 'expense', 'invoice', 'invoice_item'),
            'classes': ('collapse',)
        }),
        ('Cost', {
            'fields': ('unit_cost',)
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def volume_kg_display(self, obj):
        return f"{obj.volume_kg} kg"
    volume_kg_display.short_description = 'Volume'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
