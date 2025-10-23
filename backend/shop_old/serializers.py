from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Category, ShopProduct, DeliveryZone, Order, OrderItem,
    CustomerAddress, Review
)


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image', 'is_active', 'order', 'product_count']
        read_only_fields = ['id']
    
    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


class ShopProductSerializer(serializers.ModelSerializer):
    """Serializer for ShopProduct model"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_on_sale = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    in_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = ShopProduct
        fields = [
            'id', 'name', 'slug', 'category', 'category_name', 'description',
            'short_description', 'sku', 'price', 'compare_at_price', 'vat_rate',
            'weight', 'is_exchange', 'requires_empty_cylinder',
            'main_image', 'image_2', 'image_3', 'image_4',
            'track_inventory', 'stock_quantity', 'low_stock_threshold',
            'meta_title', 'meta_description', 'is_active', 'is_featured',
            'is_on_sale', 'discount_percentage', 'average_rating', 'review_count',
            'in_stock', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_average_rating(self, obj):
        reviews = obj.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return 0
    
    def get_review_count(self, obj):
        return obj.reviews.filter(is_approved=True).count()
    
    def get_in_stock(self, obj):
        if not obj.track_inventory:
            return True
        return obj.stock_quantity > 0


class DeliveryZoneSerializer(serializers.ModelSerializer):
    """Serializer for DeliveryZone model"""
    areas_list = serializers.SerializerMethodField()
    
    class Meta:
        model = DeliveryZone
        fields = [
            'id', 'name', 'areas', 'areas_list', 'delivery_fee',
            'free_delivery_threshold', 'estimated_delivery_time',
            'is_active', 'order'
        ]
        read_only_fields = ['id']
    
    def get_areas_list(self, obj):
        return [area.strip() for area in obj.areas.split(',')]


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for OrderItem model"""
    product_image = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'product_image',
            'quantity', 'unit_price', 'vat_rate', 'subtotal', 'vat_amount', 'total'
        ]
        read_only_fields = ['id', 'subtotal', 'vat_amount', 'total']
    
    def get_product_image(self, obj):
        if obj.product and obj.product.main_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.product.main_image.url)
        return None


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model"""
    items = OrderItemSerializer(many=True, read_only=True)
    delivery_zone_name = serializers.CharField(source='delivery_zone.name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'user_email',
            'customer_name', 'customer_email', 'customer_phone',
            'delivery_address', 'delivery_city', 'delivery_postal_code',
            'delivery_zone', 'delivery_zone_name', 'delivery_instructions',
            'preferred_delivery_date', 'preferred_delivery_time',
            'subtotal', 'vat_amount', 'delivery_fee', 'total_amount',
            'payment_method', 'payment_status', 'payment_reference',
            'status', 'notes', 'items',
            'created_at', 'updated_at', 'confirmed_at', 'delivered_at'
        ]
        read_only_fields = [
            'id', 'order_number', 'subtotal', 'vat_amount', 'total_amount',
            'created_at', 'updated_at', 'confirmed_at', 'delivered_at'
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating orders"""
    items = serializers.ListField(child=serializers.DictField(), write_only=True)
    
    class Meta:
        model = Order
        fields = [
            'customer_name', 'customer_email', 'customer_phone',
            'delivery_address', 'delivery_city', 'delivery_postal_code',
            'delivery_zone', 'delivery_instructions',
            'preferred_delivery_date', 'preferred_delivery_time',
            'payment_method', 'notes', 'items'
        ]
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        # Generate order number
        import datetime
        order_count = Order.objects.filter(
            created_at__date=datetime.date.today()
        ).count() + 1
        order_number = f"ORD-{datetime.date.today().strftime('%Y%m%d')}-{order_count:04d}"
        
        # Get delivery fee
        delivery_zone = validated_data.get('delivery_zone')
        delivery_fee = delivery_zone.delivery_fee if delivery_zone else 0
        
        # Create order
        order = Order.objects.create(
            order_number=order_number,
            delivery_fee=delivery_fee,
            **validated_data
        )
        
        # Create order items
        for item_data in items_data:
            product = ShopProduct.objects.get(id=item_data['product_id'])
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                product_sku=product.sku,
                quantity=item_data['quantity'],
                unit_price=product.price,
                vat_rate=product.vat_rate
            )
        
        # Calculate totals
        order.calculate_totals()
        
        return order


class CustomerAddressSerializer(serializers.ModelSerializer):
    """Serializer for CustomerAddress model"""
    class Meta:
        model = CustomerAddress
        fields = [
            'id', 'user', 'label', 'address', 'city', 'postal_code',
            'is_default', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review model"""
    user_name = serializers.SerializerMethodField()
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'product', 'product_name', 'user', 'user_name', 'order',
            'rating', 'title', 'comment', 'is_verified_purchase',
            'is_approved', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'is_verified_purchase', 'is_approved', 'created_at', 'updated_at']
    
    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
