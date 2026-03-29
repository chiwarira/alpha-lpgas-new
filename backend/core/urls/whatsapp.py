from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ..views_whatsapp import (
    WhatsAppWebhookView,
    WhatsAppConversationViewSet,
    WhatsAppMessageViewSet,
    WhatsAppOrderIntentViewSet,
    WhatsAppConfigView
)

router = DefaultRouter()
router.register(r'conversations', WhatsAppConversationViewSet, basename='whatsapp-conversation')
router.register(r'messages', WhatsAppMessageViewSet, basename='whatsapp-message')
router.register(r'order-intents', WhatsAppOrderIntentViewSet, basename='whatsapp-order-intent')

urlpatterns = [
    # Webhook endpoint (public - no auth required)
    path('webhook/', WhatsAppWebhookView.as_view(), name='whatsapp-webhook'),
    
    # Configuration endpoint
    path('config/', WhatsAppConfigView.as_view(), name='whatsapp-config'),
    
    # API endpoints
    path('', include(router.urls)),
]
