from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class WhatsAppConversation(models.Model):
    """Track WhatsApp conversations with clients"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('resolved', 'Resolved'),
        ('escalated', 'Escalated to Human'),
        ('archived', 'Archived'),
    ]
    
    phone_number = models.CharField(max_length=50, help_text="Client's WhatsApp number")
    client = models.ForeignKey('Client', on_delete=models.SET_NULL, null=True, blank=True, related_name='whatsapp_conversations')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Context tracking
    conversation_context = models.JSONField(default=dict, help_text="Stores conversation state and extracted information")
    last_message_at = models.DateTimeField(auto_now=True)
    
    # AI decision tracking
    ai_confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="AI confidence in understanding (0-100)")
    requires_human = models.BooleanField(default=False, help_text="Flag for human intervention needed")
    escalation_reason = models.TextField(blank=True, help_text="Reason for escalation")
    
    # Associated records
    created_invoice = models.ForeignKey('Invoice', on_delete=models.SET_NULL, null=True, blank=True, related_name='whatsapp_conversations')
    created_order = models.ForeignKey('Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='whatsapp_conversations')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, help_text="Staff member handling escalation")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_message_at']
        indexes = [
            models.Index(fields=['phone_number', '-last_message_at']),
            models.Index(fields=['status', '-last_message_at']),
            models.Index(fields=['requires_human', '-last_message_at']),
        ]
    
    def __str__(self):
        client_name = self.client.name if self.client else self.phone_number
        return f"{client_name} - {self.status}"
    
    def get_recent_messages(self, limit=10):
        """Get recent messages in this conversation"""
        return self.messages.order_by('-created_at')[:limit]


class WhatsAppMessage(models.Model):
    """Individual WhatsApp messages"""
    
    DIRECTION_CHOICES = [
        ('inbound', 'Inbound (from client)'),
        ('outbound', 'Outbound (to client)'),
    ]
    
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('document', 'Document'),
        ('audio', 'Audio'),
        ('video', 'Video'),
        ('location', 'Location'),
    ]
    
    conversation = models.ForeignKey(WhatsAppConversation, on_delete=models.CASCADE, related_name='messages')
    
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='text')
    
    # Message content
    content = models.TextField(help_text="Message text content")
    media_url = models.URLField(blank=True, help_text="URL to media file if applicable")
    
    # WhatsApp metadata
    whatsapp_message_id = models.CharField(max_length=255, unique=True, help_text="WhatsApp message ID")
    whatsapp_timestamp = models.DateTimeField(help_text="Timestamp from WhatsApp")
    
    # AI processing
    ai_processed = models.BooleanField(default=False, help_text="Whether AI has processed this message")
    ai_intent = models.CharField(max_length=100, blank=True, help_text="Detected intent (e.g., 'place_order', 'check_status')")
    ai_extracted_data = models.JSONField(default=dict, help_text="Data extracted by AI (products, quantities, etc.)")
    ai_response = models.TextField(blank=True, help_text="AI-generated response")
    
    # Delivery status (for outbound messages)
    delivered = models.BooleanField(default=False)
    read = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['whatsapp_message_id']),
            models.Index(fields=['ai_processed', 'direction']),
        ]
    
    def __str__(self):
        return f"{self.direction} - {self.content[:50]}"


class WhatsAppOrderIntent(models.Model):
    """Tracks order intents extracted from conversations"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Confirmation'),
        ('confirmed', 'Confirmed by Client'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    conversation = models.ForeignKey(WhatsAppConversation, on_delete=models.CASCADE, related_name='order_intents')
    message = models.ForeignKey(WhatsAppMessage, on_delete=models.CASCADE, related_name='order_intents')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Extracted order details
    products_data = models.JSONField(help_text="List of products with quantities and prices")
    delivery_address = models.TextField(blank=True)
    delivery_zone = models.ForeignKey('DeliveryZone', on_delete=models.SET_NULL, null=True, blank=True)
    delivery_notes = models.TextField(blank=True)
    
    # Calculated totals
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # AI confidence
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="AI confidence in order details (0-100)")
    
    # Created records
    created_invoice = models.ForeignKey('Invoice', on_delete=models.SET_NULL, null=True, blank=True)
    created_order = models.ForeignKey('Order', on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order Intent - {self.status} - R{self.total}"


class WhatsAppConfig(models.Model):
    """Configuration for WhatsApp Business API integration"""
    
    # WhatsApp Business API credentials
    phone_number_id = models.CharField(max_length=255, help_text="WhatsApp Business Phone Number ID")
    business_account_id = models.CharField(max_length=255, help_text="WhatsApp Business Account ID")
    access_token = models.CharField(max_length=500, help_text="WhatsApp API Access Token")
    webhook_verify_token = models.CharField(max_length=255, help_text="Webhook verification token")
    
    # AI Configuration
    AI_PROVIDER_CHOICES = [
        ('openai', 'OpenAI (GPT-4)'),
        ('anthropic', 'Anthropic (Claude)'),
    ]
    ai_provider = models.CharField(max_length=20, choices=AI_PROVIDER_CHOICES, default='openai')
    ai_api_key = models.CharField(max_length=500, help_text="API key for AI provider")
    ai_model = models.CharField(max_length=100, default='gpt-4o', help_text="AI model to use")
    
    # Automation settings
    auto_create_invoices = models.BooleanField(default=True, help_text="Automatically create invoices for confirmed orders")
    auto_assign_drivers = models.BooleanField(default=True, help_text="Automatically assign available drivers")
    min_confidence_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=80.0, help_text="Minimum AI confidence to auto-process (0-100)")
    
    # Business hours
    business_hours_start = models.TimeField(default='08:00', help_text="Start of business hours")
    business_hours_end = models.TimeField(default='18:00', help_text="End of business hours")
    auto_respond_outside_hours = models.BooleanField(default=True, help_text="Send automated response outside business hours")
    outside_hours_message = models.TextField(
        default="Thank you for your message! Our business hours are 8 AM - 6 PM. We'll respond to your message as soon as we're back.",
        help_text="Message to send outside business hours"
    )
    
    # Greeting messages
    welcome_message = models.TextField(
        default="Hi! Welcome to Alpha LPGas 🔥\n\nHow can I help you today?\n\n1️⃣ Order gas cylinders\n2️⃣ Check order status\n3️⃣ View products & prices\n4️⃣ Speak to a person\n\nJust type your request!",
        help_text="Welcome message for new conversations"
    )
    
    # System prompts
    system_prompt = models.TextField(
        default="""You are a helpful AI assistant for Alpha LPGas, a gas delivery company in South Africa.

Your role is to:
1. Help customers order gas cylinders (9kg, 14kg, 19kg, 48kg)
2. Extract order details: product type, quantity, delivery address
3. Confirm order details with the customer
4. Be friendly, professional, and efficient

When a customer wants to order:
- Ask for: product type, quantity, and delivery address
- Confirm all details before processing
- Provide estimated delivery time

If you're unsure about anything, ask for clarification or escalate to a human agent.""",
        help_text="System prompt for AI agent"
    )
    
    is_active = models.BooleanField(default=True, help_text="Enable/disable WhatsApp integration")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'WhatsApp Configuration'
        verbose_name_plural = 'WhatsApp Configuration'
    
    def save(self, *args, **kwargs):
        # Singleton pattern
        self.pk = 1
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Prevent deletion
        pass
    
    @classmethod
    def load(cls):
        """Load the singleton instance"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
    
    def __str__(self):
        return f"WhatsApp Config - {'Active' if self.is_active else 'Inactive'}"
