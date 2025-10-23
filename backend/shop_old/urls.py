from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, ShopProductViewSet, DeliveryZoneViewSet,
    OrderViewSet, CustomerAddressViewSet, ReviewViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ShopProductViewSet, basename='product')
router.register(r'delivery-zones', DeliveryZoneViewSet, basename='delivery-zone')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'addresses', CustomerAddressViewSet, basename='address')
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
]
