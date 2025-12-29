"""
Public API URLs - accessible without authentication
For frontend consumption
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import (
    HeroBannerViewSet, CompanySettingsView, CategoryViewSet, ProductViewSet,
    DeliveryZoneViewSet, PromoCodeViewSet, ContactSubmissionViewSet,
    TestimonialViewSet, CustomScriptsView
)

router = DefaultRouter()
router.register(r'hero-banners', HeroBannerViewSet, basename='herobanner')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'delivery-zones', DeliveryZoneViewSet, basename='deliveryzone')
router.register(r'promo-codes', PromoCodeViewSet, basename='promocode')
router.register(r'contact', ContactSubmissionViewSet, basename='contact')
router.register(r'testimonials', TestimonialViewSet, basename='testimonial')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Custom endpoints
    path('company-settings/', CompanySettingsView.as_view(), name='company-settings'),
    path('custom-scripts/', CustomScriptsView.as_view(), name='custom-scripts'),
]
