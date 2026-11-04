from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


STAMPS_REQUIRED = 9  # stamps collected before the next bottle is rewarded (i.e. 10th purchase)
REWARD_PERCENT_CHOICES = [
    (50, '50% off one bottle'),
    (100, '100% off one bottle (free)'),
]


class LoyaltyCard(models.Model):
    """Loyalty card tracking for clients"""
    CYLINDER_SIZE_CHOICES = [
        ('5kg', '5kg Cylinder'),
        ('9kg', '9kg Cylinder'),
        ('14kg', '14kg Cylinder'),
        ('19kg', '19kg Cylinder'),
        ('48kg', '48kg Cylinder'),
    ]
    
    client = models.ForeignKey('Client', on_delete=models.CASCADE, related_name='loyalty_cards')
    cylinder_size = models.CharField(max_length=10, choices=CYLINDER_SIZE_CHOICES, null=True, blank=True, help_text="Smallest cylinder size purchased (determines reward type)")
    stamps = models.IntegerField(default=0, help_text="Number of stamps (purchases) on this card")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['client', 'is_active']  # Only one active card per client
    
    def __str__(self):
        size_display = f" - {self.cylinder_size}" if self.cylinder_size else ""
        return f"{self.client.name}{size_display} ({self.stamps}/9 stamps)"
    
    def add_stamp(self):
        """Add a stamp to the card"""
        self.stamps += 1
        self.save()
        return self.stamps
    
    def is_reward_eligible(self):
        """Check if card is eligible for reward (9 stamps)"""
        return self.stamps >= STAMPS_REQUIRED

    @property
    def reward_percent(self):
        """Current reward percentage (configured in Company Settings)"""
        from .models import CompanySettings
        return CompanySettings.load().loyalty_reward_percent

    @property
    def remaining_stamps(self):
        return max(0, STAMPS_REQUIRED - self.stamps)

    def get_reward_type(self):
        """'free' when the configured reward is 100%, otherwise 'discount'"""
        return 'free' if self.reward_percent >= 100 else 'discount'

    def reward_transactions(self):
        return self.transactions.filter(transaction_type='reward_claimed')

    @property
    def full_rewards_count(self):
        return self.reward_transactions().filter(reward_percent=100).count()

    @property
    def half_rewards_count(self):
        return self.reward_transactions().filter(reward_percent=50).count()
    
    def reset_card(self):
        """Reset the card after reward is claimed"""
        self.stamps = 0
        self.save()


class LoyaltyTransaction(models.Model):
    """Track loyalty card transactions"""
    TRANSACTION_TYPES = [
        ('stamp', 'Stamp Added'),
        ('reward_claimed', 'Reward Claimed'),
        ('card_reset', 'Card Reset'),
        ('reversal', 'Stamp Reversal'),
    ]
    
    loyalty_card = models.ForeignKey(LoyaltyCard, on_delete=models.CASCADE, related_name='transactions')
    invoice = models.ForeignKey('Invoice', on_delete=models.SET_NULL, null=True, blank=True, related_name='loyalty_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    stamps_before = models.IntegerField()
    stamps_after = models.IntegerField()
    reward_percent = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Discount percentage given (reward_claimed only)")
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Rand value of the reward (reward_claimed only)")
    reward_item = models.ForeignKey('InvoiceItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='+', help_text="Invoice line that carries the reward")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.loyalty_card.client.name} - {self.transaction_type} ({self.created_at.strftime('%Y-%m-%d')})"
