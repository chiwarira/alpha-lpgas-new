from django.contrib import admin
from django.utils.html import format_html
from .models_whatsapp import (
    WhatsAppConversation, WhatsAppMessage, WhatsAppOrderIntent, WhatsAppConfig
)


class WhatsAppMessageInline(admin.TabularInline):
    """Inline display of messages in conversation"""
    model = WhatsAppMessage
    extra = 0
    readonly_fields = ['direction', 'message_type', 'content', 'ai_intent', 'created_at', 'delivered', 'read']
    fields = ['direction', 'message_type', 'content', 'ai_intent', 'created_at', 'delivered', 'read']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(WhatsAppConversation)
class WhatsAppConversationAdmin(admin.ModelAdmin):
    list_display = [
        'phone_number', 'client_name', 'status', 'requires_human_badge', 
        'ai_confidence_score', 'last_message_at', 'created_invoice_link', 'created_order_link'
    ]
    list_filter = ['status', 'requires_human', 'created_at', 'last_message_at']
    search_fields = ['phone_number', 'client__name', 'escalation_reason']
    readonly_fields = [
        'phone_number', 'last_message_at', 'created_at', 'updated_at',
        'conversation_context_display', 'message_preview'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('phone_number', 'client', 'status')
        }),
        ('AI Processing', {
            'fields': ('ai_confidence_score', 'requires_human', 'escalation_reason', 'conversation_context_display')
        }),
        ('Created Records', {
            'fields': ('created_invoice', 'created_order')
        }),
        ('Assignment', {
            'fields': ('assigned_to',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_message_at'),
            'classes': ('collapse',)
        }),
        ('Recent Messages', {
            'fields': ('message_preview',)
        })
    )
    
    inlines = [WhatsAppMessageInline]
    
    def client_name(self, obj):
        return obj.client.name if obj.client else 'Unknown'
    client_name.short_description = 'Client'
    
    def requires_human_badge(self, obj):
        if obj.requires_human:
            return format_html('<span style="color: red; font-weight: bold;">⚠️ YES</span>')
        return format_html('<span style="color: green;">✓ No</span>')
    requires_human_badge.short_description = 'Needs Human'
    
    def created_invoice_link(self, obj):
        if obj.created_invoice:
            return format_html(
                '<a href="/admin/core/invoice/{}/change/">{}</a>',
                obj.created_invoice.id,
                obj.created_invoice.invoice_number
            )
        return '-'
    created_invoice_link.short_description = 'Invoice'
    
    def created_order_link(self, obj):
        if obj.created_order:
            return format_html(
                '<a href="/admin/core/order/{}/change/">{}</a>',
                obj.created_order.id,
                obj.created_order.order_number
            )
        return '-'
    created_order_link.short_description = 'Order'
    
    def conversation_context_display(self, obj):
        import json
        return format_html('<pre>{}</pre>', json.dumps(obj.conversation_context, indent=2))
    conversation_context_display.short_description = 'Conversation Context'
    
    def message_preview(self, obj):
        messages = obj.messages.order_by('-created_at')[:5]
        html = '<div style="max-height: 300px; overflow-y: auto;">'
        for msg in reversed(messages):
            direction_color = '#007bff' if msg.direction == 'inbound' else '#28a745'
            html += f'''
            <div style="margin: 10px 0; padding: 10px; background: #f8f9fa; border-left: 3px solid {direction_color};">
                <strong>{msg.get_direction_display()}</strong> - {msg.created_at.strftime('%Y-%m-%d %H:%M')}
                <br>{msg.content}
                {f"<br><small>Intent: {msg.ai_intent}</small>" if msg.ai_intent else ""}
            </div>
            '''
        html += '</div>'
        return format_html(html)
    message_preview.short_description = 'Recent Messages'
    
    actions = ['mark_as_resolved', 'escalate_to_human']
    
    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(status='resolved', requires_human=False)
        self.message_user(request, f'{updated} conversation(s) marked as resolved.')
    mark_as_resolved.short_description = 'Mark as resolved'
    
    def escalate_to_human(self, request, queryset):
        updated = queryset.update(status='escalated', requires_human=True)
        self.message_user(request, f'{updated} conversation(s) escalated to human.')
    escalate_to_human.short_description = 'Escalate to human'


@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = [
        'conversation_phone', 'direction', 'message_type', 'content_preview', 
        'ai_intent', 'ai_processed', 'created_at'
    ]
    list_filter = ['direction', 'message_type', 'ai_processed', 'created_at']
    search_fields = ['content', 'conversation__phone_number', 'ai_intent']
    readonly_fields = [
        'conversation', 'direction', 'message_type', 'content', 'media_url',
        'whatsapp_message_id', 'whatsapp_timestamp', 'ai_processed', 'ai_intent',
        'ai_extracted_data_display', 'ai_response', 'delivered', 'read', 'created_at'
    ]
    
    fieldsets = (
        ('Message Info', {
            'fields': ('conversation', 'direction', 'message_type', 'content', 'media_url')
        }),
        ('WhatsApp Metadata', {
            'fields': ('whatsapp_message_id', 'whatsapp_timestamp', 'delivered', 'read')
        }),
        ('AI Processing', {
            'fields': ('ai_processed', 'ai_intent', 'ai_extracted_data_display', 'ai_response')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        })
    )
    
    def conversation_phone(self, obj):
        return obj.conversation.phone_number
    conversation_phone.short_description = 'Phone Number'
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
    
    def ai_extracted_data_display(self, obj):
        import json
        return format_html('<pre>{}</pre>', json.dumps(obj.ai_extracted_data, indent=2))
    ai_extracted_data_display.short_description = 'Extracted Data'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(WhatsAppOrderIntent)
class WhatsAppOrderIntentAdmin(admin.ModelAdmin):
    list_display = [
        'conversation_phone', 'status', 'total', 'confidence_score',
        'created_invoice_link', 'created_order_link', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['conversation__phone_number', 'delivery_address']
    readonly_fields = [
        'conversation', 'message', 'products_data_display', 'delivery_address',
        'delivery_zone', 'delivery_notes', 'subtotal', 'delivery_fee', 'total',
        'confidence_score', 'created_invoice', 'created_order', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Order Details', {
            'fields': ('conversation', 'message', 'status', 'confidence_score')
        }),
        ('Products', {
            'fields': ('products_data_display',)
        }),
        ('Delivery', {
            'fields': ('delivery_address', 'delivery_zone', 'delivery_notes')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'delivery_fee', 'total')
        }),
        ('Created Records', {
            'fields': ('created_invoice', 'created_order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    def conversation_phone(self, obj):
        return obj.conversation.phone_number
    conversation_phone.short_description = 'Phone Number'
    
    def products_data_display(self, obj):
        import json
        return format_html('<pre>{}</pre>', json.dumps(obj.products_data, indent=2))
    products_data_display.short_description = 'Products'
    
    def created_invoice_link(self, obj):
        if obj.created_invoice:
            return format_html(
                '<a href="/admin/core/invoice/{}/change/">{}</a>',
                obj.created_invoice.id,
                obj.created_invoice.invoice_number
            )
        return '-'
    created_invoice_link.short_description = 'Invoice'
    
    def created_order_link(self, obj):
        if obj.created_order:
            return format_html(
                '<a href="/admin/core/order/{}/change/">{}</a>',
                obj.created_order.id,
                obj.created_order.order_number
            )
        return '-'
    created_order_link.short_description = 'Order'
    
    def has_add_permission(self, request):
        return False


@admin.register(WhatsAppConfig)
class WhatsAppConfigAdmin(admin.ModelAdmin):
    fieldsets = (
        ('WhatsApp Business API', {
            'fields': (
                'is_active',
                'phone_number_id',
                'business_account_id',
                'access_token',
                'webhook_verify_token'
            )
        }),
        ('AI Configuration', {
            'fields': (
                'ai_provider',
                'ai_api_key',
                'ai_model',
                'min_confidence_threshold'
            )
        }),
        ('Automation Settings', {
            'fields': (
                'auto_create_invoices',
                'auto_assign_drivers'
            )
        }),
        ('Business Hours', {
            'fields': (
                'business_hours_start',
                'business_hours_end',
                'auto_respond_outside_hours',
                'outside_hours_message'
            )
        }),
        ('Messages', {
            'fields': (
                'welcome_message',
                'system_prompt'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        # Singleton - only one config allowed
        return not WhatsAppConfig.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
