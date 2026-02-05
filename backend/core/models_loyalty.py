from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class LoyaltyCard(models.Model):
    """Loyalty card tracking for clients"""
    CYLINDER_SIZE_CHOICES = [
        ('5kg', '5kg Cylinder'),
        ('9kg', '9kg Cylinder'),
        ('19kg', '19kg Cylinder'),
        ('48kg', '48kg Cylinder'),
    ]
    
    client = models.ForeignKey('Client', on_delete=models.CASCADE, related_name='loyalty_cards')
    cylinder_size = models.CharField(max_length=10, choices=CYLINDER_SIZE_CHOICES)
    stamps = models.IntegerField(default=0, help_text="Number of stamps (purchases) on this card")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['client', 'cylinder_size', 'is_active']
    
    def __str__(self):
        return f"{self.client.name} - {self.cylinder_size} ({self.stamps}/9 stamps)"
    
    def add_stamp(self):
        """Add a stamp to the card"""
        self.stamps += 1
        self.save()
        return self.stamps
    
    def is_reward_eligible(self):
        """Check if card is eligible for reward (9 stamps)"""
        return self.stamps >= 9
    
    def get_reward_type(self):
        """Get the type of reward based on cylinder size"""
        if self.cylinder_size in ['5kg', '9kg']:
            return 'free'  # Free cylinder on 10th purchase
        else:  # 19kg, 48kg
            return '50_percent'  # 50% off on 10th purchase
    
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
    ]
    
    loyalty_card = models.ForeignKey(LoyaltyCard, on_delete=models.CASCADE, related_name='transactions')
    invoice = models.ForeignKey('Invoice', on_delete=models.SET_NULL, null=True, blank=True, related_name='loyalty_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    stamps_before = models.IntegerField()
    stamps_after = models.IntegerField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.loyalty_card.client.name} - {self.transaction_type} ({self.created_at.strftime('%Y-%m-%d')})"
