from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    HeroBanner, CompanySettings, Client, Category, Product, ProductVariant,
    Quote, QuoteItem, Invoice, InvoiceItem, Payment, CreditNote, CreditNoteItem,
    DeliveryZone, PromoCode, Driver, Order, OrderItem, OrderStatusHistory, ContactSubmission, Testimonial, CustomScript
)


class HeroBannerSerializer(serializers.ModelSerializer):
    """Serializer for HeroBanner model"""
    overlay_rgba = serializers.SerializerMethodField()
    
    class Meta:
        model = HeroBanner
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_overlay_rgba(self, obj):
        """Get the RGBA color string for the overlay"""
        return obj.get_overlay_rgba()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff']
        read_only_fields = ['id']


class CompanySettingsSerializer(serializers.ModelSerializer):
    """Serializer for CompanySettings model"""
    logo_url = serializers.SerializerMethodField()
    favicon_url = serializers.SerializerMethodField()
    
    class Meta:
        model = CompanySettings
        fields = [
            'id', 'company_name', 'registration_number', 'vat_number', 'phone', 'email', 'address',
            'logo', 'logo_url', 'favicon', 'favicon_url',
            'bank_name', 'account_name', 'account_number', 'account_type', 'branch_code',
            'payment_reference_note', 'statement_footer_text', 
            'whatsapp_invoice_message', 'whatsapp_quote_message', 'whatsapp_statement_message',
            'updated_at'
        ]
        read_only_fields = ['id', 'updated_at', 'logo_url', 'favicon_url']
    
    def get_logo_url(self, obj):
        """Get full URL for logo"""
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None
    
    def get_favicon_url(self, obj):
        """Get full URL for favicon"""
        if obj.favicon:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.favicon.url)
            return obj.favicon.url
        return None


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


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_on_sale = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()
    is_out_of_stock = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'slug']


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


# E-commerce Serializers

class DeliveryZoneSerializer(serializers.ModelSerializer):
    """Serializer for DeliveryZone model"""
    class Meta:
        model = DeliveryZone
        fields = '__all__'


class DriverSerializer(serializers.ModelSerializer):
    """Serializer for Driver model"""
    user_details = UserSerializer(source='user', read_only=True)
    full_name = serializers.SerializerMethodField()
    active_deliveries_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Driver
        fields = '__all__'
        read_only_fields = ['id', 'total_deliveries', 'rating', 'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    
    def get_active_deliveries_count(self, obj):
        return obj.get_active_deliveries().count()


class PromoCodeSerializer(serializers.ModelSerializer):
    """Serializer for PromoCode model"""
    is_valid_now = serializers.SerializerMethodField()
    
    class Meta:
        model = PromoCode
        fields = '__all__'
    
    def get_is_valid_now(self, obj):
        return obj.is_valid()


class ProductVariantSerializer(serializers.ModelSerializer):
    """Serializer for ProductVariant model"""
    price = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductVariant
        fields = '__all__'
    
    def get_price(self, obj):
        return str(obj.get_price())


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for OrderItem model"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    variant_name = serializers.CharField(source='variant.name', read_only=True, allow_null=True)
    
    class Meta:
        model = OrderItem
        fields = '__all__'


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer for OrderStatusHistory model"""
    class Meta:
        model = OrderStatusHistory
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model"""
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    delivery_zone_name = serializers.CharField(source='delivery_zone.name', read_only=True, allow_null=True)
    driver_name = serializers.SerializerMethodField()
    driver_phone = serializers.CharField(source='assigned_driver.phone', read_only=True, allow_null=True)
    driver_vehicle = serializers.CharField(source='assigned_driver.vehicle_registration', read_only=True, allow_null=True)
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['order_number', 'created_at', 'updated_at']
    
    def get_driver_name(self, obj):
        if obj.assigned_driver:
            return obj.assigned_driver.user.get_full_name() or obj.assigned_driver.user.username
        return None


class ContactSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for ContactSubmission model"""
    
    class Meta:
        model = ContactSubmission
        fields = ['id', 'name', 'email', 'phone', 'subject', 'message', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']
    
    def create(self, validated_data):
        # Get IP address and user agent from request context
        request = self.context.get('request')
        if request:
            validated_data['ip_address'] = self.get_client_ip(request)
            validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        return super().create(validated_data)
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class TestimonialSerializer(serializers.ModelSerializer):
    """Serializer for Testimonial model"""
    initials = serializers.SerializerMethodField()
    
    class Meta:
        model = Testimonial
        fields = ['id', 'customer_name', 'location', 'company_name', 'review', 'rating', 'avatar_color', 'initials', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_initials(self, obj):
        """Get customer initials"""
        return obj.get_initials()


class CustomScriptSerializer(serializers.ModelSerializer):
    """Serializer for CustomScript model - for frontend script injection"""
    class Meta:
        model = CustomScript
        fields = ['id', 'name', 'script_code', 'position', 'order']
