from rest_framework import serializers
from .models_whatsapp import (
    WhatsAppConversation, WhatsAppMessage, WhatsAppOrderIntent, WhatsAppConfig
)
from .models import Client, Invoice, Order


class WhatsAppMessageSerializer(serializers.ModelSerializer):
    """Serializer for WhatsApp messages"""
    
    class Meta:
        model = WhatsAppMessage
        fields = '__all__'
        read_only_fields = ['created_at']


class WhatsAppConversationSerializer(serializers.ModelSerializer):
    """Serializer for WhatsApp conversations"""
    
    client_name = serializers.CharField(source='client.name', read_only=True, allow_null=True)
    recent_messages = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = WhatsAppConversation
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'last_message_at']
    
    def get_recent_messages(self, obj):
        """Get 5 most recent messages"""
        messages = obj.messages.order_by('-created_at')[:5]
        return WhatsAppMessageSerializer(messages, many=True).data
    
    def get_message_count(self, obj):
        """Get total message count"""
        return obj.messages.count()


class WhatsAppOrderIntentSerializer(serializers.ModelSerializer):
    """Serializer for order intents"""
    
    conversation_phone = serializers.CharField(source='conversation.phone_number', read_only=True)
    invoice_number = serializers.CharField(source='created_invoice.invoice_number', read_only=True, allow_null=True)
    order_number = serializers.CharField(source='created_order.order_number', read_only=True, allow_null=True)
    
    class Meta:
        model = WhatsAppOrderIntent
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class WhatsAppConfigSerializer(serializers.ModelSerializer):
    """Serializer for WhatsApp configuration"""
    
    class Meta:
        model = WhatsAppConfig
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'access_token': {'write_only': True},
            'ai_api_key': {'write_only': True},
        }
