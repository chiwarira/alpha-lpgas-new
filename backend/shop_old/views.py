from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import (
    Category, ShopProduct, DeliveryZone, Order, OrderItem,
    CustomerAddress, Review
)
from .serializers import (
    CategorySerializer, ShopProductSerializer, DeliveryZoneSerializer,
    OrderSerializer, OrderCreateSerializer, OrderItemSerializer,
    CustomerAddressSerializer, ReviewSerializer
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing categories"""
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'


class ShopProductViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing shop products"""
    queryset = ShopProduct.objects.filter(is_active=True)
    serializer_class = ShopProductSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_featured', 'is_exchange']
    search_fields = ['name', 'description', 'sku']
    ordering_fields = ['name', 'price', 'created_at', 'order']
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by category slug if provided
        category_slug = self.request.query_params.get('category_slug')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        return queryset

    @action(detail=True, methods=['get'])
    def reviews(self, request, slug=None):
        """Get all approved reviews for a product"""
        product = self.get_object()
        reviews = product.reviews.filter(is_approved=True)
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class DeliveryZoneViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing delivery zones"""
    queryset = DeliveryZone.objects.filter(is_active=True)
    serializer_class = DeliveryZoneSerializer
    permission_classes = [AllowAny]


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for managing orders"""
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_status']
    search_fields = ['order_number', 'customer_name', 'customer_email', 'customer_phone']
    ordering_fields = ['created_at', 'preferred_delivery_date', 'total_amount']

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        # Users can only see their own orders unless they're staff
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        return queryset

    def perform_create(self, serializer):
        # Associate order with user if authenticated
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save()

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm an order"""
        order = self.get_object()
        order.status = 'confirmed'
        order.confirmed_at = timezone.now()
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an order"""
        order = self.get_object()
        if order.status in ['delivered', 'cancelled']:
            return Response(
                {'error': 'Cannot cancel this order'},
                status=status.HTTP_400_BAD_REQUEST
            )
        order.status = 'cancelled'
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_delivered(self, request, pk=None):
        """Mark order as delivered (staff only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        order = self.get_object()
        order.status = 'delivered'
        order.delivered_at = timezone.now()
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)


class CustomerAddressViewSet(viewsets.ModelViewSet):
    """ViewSet for managing customer addresses"""
    queryset = CustomerAddress.objects.all()
    serializer_class = CustomerAddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users can only see their own addresses
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for managing reviews"""
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['product', 'rating', 'is_approved']
    ordering_fields = ['created_at', 'rating']

    def get_queryset(self):
        queryset = super().get_queryset()
        # Non-staff users only see approved reviews
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_approved=True)
        return queryset

    def perform_create(self, serializer):
        # Check if user has purchased the product
        product = serializer.validated_data['product']
        order = serializer.validated_data.get('order')
        
        is_verified = False
        if order and order.user == self.request.user:
            # Check if order contains this product and is delivered
            if order.status == 'delivered' and order.items.filter(product=product).exists():
                is_verified = True
        
        serializer.save(
            user=self.request.user,
            is_verified_purchase=is_verified
        )

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a review (staff only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        review = self.get_object()
        review.is_approved = True
        review.save()
        serializer = self.get_serializer(review)
        return Response(serializer.data)
