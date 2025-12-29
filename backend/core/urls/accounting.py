from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ..views import (
    HeroBannerViewSet, CompanySettingsView, UserViewSet, ClientViewSet, CategoryViewSet, ProductViewSet,
    QuoteViewSet, QuoteItemViewSet, InvoiceViewSet, InvoiceItemViewSet,
    PaymentViewSet, CreditNoteViewSet, CreditNoteItemViewSet,
    DeliveryZoneViewSet, PromoCodeViewSet, DriverViewSet, ProductVariantViewSet, OrderViewSet, ContactSubmissionViewSet, TestimonialViewSet,
    CustomScriptView
)

router = DefaultRouter()
router.register(r'hero-banners', HeroBannerViewSet, basename='hero-banner')
router.register(r'users', UserViewSet, basename='user')
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'quotes', QuoteViewSet, basename='quote')
router.register(r'quote-items', QuoteItemViewSet, basename='quote-item')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'invoice-items', InvoiceItemViewSet, basename='invoice-item')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'credit-notes', CreditNoteViewSet, basename='credit-note')
router.register(r'delivery-zones', DeliveryZoneViewSet, basename='delivery-zone')
router.register(r'promo-codes', PromoCodeViewSet, basename='promo-code')
router.register(r'drivers', DriverViewSet, basename='driver')
router.register(r'product-variants', ProductVariantViewSet, basename='product-variant')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'credit-note-items', CreditNoteItemViewSet, basename='credit-note-item')
router.register(r'contact', ContactSubmissionViewSet, basename='contact')
router.register(r'testimonials', TestimonialViewSet, basename='testimonial')

urlpatterns = [
    path('settings/', CompanySettingsView.as_view(), name='company-settings'),
    path('custom-scripts/', CustomScriptView.as_view(), name='custom-scripts'),
    path('', include(router.urls)),
]
