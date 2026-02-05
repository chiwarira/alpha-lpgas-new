from django.contrib import admin
from .models_loyalty import LoyaltyCard, LoyaltyTransaction


class LoyaltyTransactionInline(admin.TabularInline):
    model = LoyaltyTransaction
    extra = 0
    readonly_fields = ['transaction_type', 'stamps_before', 'stamps_after', 'invoice', 'notes', 'created_at', 'created_by']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(LoyaltyCard)
class LoyaltyCardAdmin(admin.ModelAdmin):
    list_display = ['client', 'cylinder_size', 'stamps', 'reward_status', 'is_active', 'created_at']
    list_filter = ['cylinder_size', 'is_active', 'stamps']
    search_fields = ['client__name', 'client__phone', 'client__customer_id']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [LoyaltyTransactionInline]
    
    fieldsets = (
        ('Card Information', {
            'fields': ('client', 'cylinder_size', 'stamps', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def reward_status(self, obj):
        if obj.stamps >= 9:
            reward_type = obj.get_reward_type()
            if reward_type == 'free':
                return '🎁 Free Cylinder'
            else:
                return '🎁 50% Off'
        else:
            remaining = 9 - obj.stamps
            return f'{remaining} more needed'
    reward_status.short_description = 'Reward Status'
    
    actions = ['reset_cards', 'generate_loyalty_cards']
    
    def reset_cards(self, request, queryset):
        for card in queryset:
            card.reset_card()
            LoyaltyTransaction.objects.create(
                loyalty_card=card,
                transaction_type='card_reset',
                stamps_before=card.stamps,
                stamps_after=0,
                notes='Card reset by admin',
                created_by=request.user
            )
        self.message_user(request, f'{queryset.count()} loyalty cards reset successfully.')
    reset_cards.short_description = 'Reset selected loyalty cards'
    
    def generate_loyalty_cards(self, request, queryset):
        """Generate and send loyalty card images"""
        from .utils_loyalty import send_loyalty_card_whatsapp
        success_count = 0
        for card in queryset:
            try:
                result = send_loyalty_card_whatsapp(card)
                if result and result.get('success'):
                    success_count += 1
            except Exception as e:
                pass
        self.message_user(request, f'Generated {success_count} loyalty card images.')
    generate_loyalty_cards.short_description = 'Generate and send loyalty cards'


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(admin.ModelAdmin):
    list_display = ['loyalty_card', 'transaction_type', 'stamps_before', 'stamps_after', 'invoice', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['loyalty_card__client__name', 'invoice__invoice_number', 'notes']
    readonly_fields = ['loyalty_card', 'invoice', 'transaction_type', 'stamps_before', 'stamps_after', 'notes', 'created_at', 'created_by']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
