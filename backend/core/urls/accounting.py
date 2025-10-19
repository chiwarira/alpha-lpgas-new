from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ..views import (
    CompanySettingsView, UserViewSet, ClientViewSet, ProductViewSet,
    QuoteViewSet, QuoteItemViewSet, InvoiceViewSet, InvoiceItemViewSet,
    PaymentViewSet, CreditNoteViewSet, CreditNoteItemViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'quotes', QuoteViewSet, basename='quote')
router.register(r'quote-items', QuoteItemViewSet, basename='quote-item')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'invoice-items', InvoiceItemViewSet, basename='invoice-item')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'credit-notes', CreditNoteViewSet, basename='credit-note')
router.register(r'credit-note-items', CreditNoteItemViewSet, basename='credit-note-item')

urlpatterns = [
    path('settings/', CompanySettingsView.as_view(), name='company-settings'),
    path('', include(router.urls)),
]
