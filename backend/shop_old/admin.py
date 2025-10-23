from django.contrib import admin
from .models import (
    Category, ShopProduct, DeliveryZone, Order, OrderItem,
    CustomerAddress, Review
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ShopProduct)
class ShopProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'price', 'stock_quantity', 'is_active', 'is_featured', 'created_at']
    list_filter = ['is_active', 'is_featured', 'category', 'is_exchange', 'created_at']
    search_fields = ['name', 'sku', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'description', 'short_description', 'sku')
        }),
        ('Pricing', {
            'fields': ('price', 'compare_at_price', 'cost_price', 'vat_rate')
        }),
        ('Product Details', {
            'fields': ('weight', 'is_exchange', 'requires_empty_cylinder')
        }),
        ('Images', {
            'fields': ('main_image', 'image_2', 'image_3', 'image_4')
        }),
        ('Inventory', {
            'fields': ('track_inventory', 'stock_quantity', 'low_stock_threshold')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured', 'order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'delivery_fee', 'free_delivery_threshold', 'estimated_delivery_time', 'is_active', 'order']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'areas']
    readonly_fields = ['created_at', 'updated_at']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'product_sku', 'unit_price', 'vat_rate', 'subtotal', 'vat_amount', 'total']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'customer_name', 'customer_phone', 'status',
        'payment_status', 'total_amount', 'preferred_delivery_date', 'created_at'
    ]
    list_filter = ['status', 'payment_status', 'preferred_delivery_date', 'created_at']
    search_fields = ['order_number', 'customer_name', 'customer_email', 'customer_phone']
    readonly_fields = [
        'order_number', 'subtotal', 'vat_amount', 'total_amount',
        'created_at', 'updated_at', 'confirmed_at', 'delivered_at'
    ]
    inlines = [OrderItemInline]
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'created_at', 'updated_at')
        }),
        ('Customer Details', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('Delivery Information', {
            'fields': (
                'delivery_address', 'delivery_city', 'delivery_postal_code',
                'delivery_zone', 'delivery_instructions',
                'preferred_delivery_date', 'preferred_delivery_time'
            )
        }),
        ('Order Totals', {
            'fields': ('subtotal', 'vat_amount', 'delivery_fee', 'total_amount')
        }),
        ('Payment', {
            'fields': ('payment_method', 'payment_status', 'payment_reference', 'yoco_payment_id')
        }),
        ('Notes', {
            'fields': ('notes', 'admin_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('confirmed_at', 'delivered_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CustomerAddress)
class CustomerAddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'label', 'city', 'is_default', 'created_at']
    list_filter = ['is_default', 'city', 'created_at']
    search_fields = ['user__username', 'user__email', 'label', 'address']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'is_verified_purchase', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_verified_purchase', 'is_approved', 'created_at']
    search_fields = ['product__name', 'user__username', 'title', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['approve_reviews', 'unapprove_reviews']
    
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = "Approve selected reviews"
    
    def unapprove_reviews(self, request, queryset):
        queryset.update(is_approved=False)
    unapprove_reviews.short_description = "Unapprove selected reviews"
