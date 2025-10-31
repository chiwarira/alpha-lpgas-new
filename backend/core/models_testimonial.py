from django.db import models


class Testimonial(models.Model):
    """Customer testimonials/reviews"""
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    # Customer Information
    customer_name = models.CharField(max_length=255, help_text="Customer's name")
    location = models.CharField(max_length=255, help_text="e.g., Fish Hoek, Kommetjie, Simon's Town")
    
    # Review Content
    review = models.TextField(help_text="Customer's testimonial")
    rating = models.IntegerField(choices=RATING_CHOICES, default=5, help_text="Star rating (1-5)")
    
    # Display Settings
    is_active = models.BooleanField(default=True, help_text="Show this testimonial on the website")
    order = models.IntegerField(default=0, help_text="Display order (lower numbers appear first)")
    
    # Optional Fields
    company_name = models.CharField(max_length=255, blank=True, help_text="Company name (for business customers)")
    avatar_color = models.CharField(
        max_length=20, 
        default='blue',
        choices=[
            ('blue', 'Blue'),
            ('rose', 'Rose'),
            ('green', 'Green'),
            ('purple', 'Purple'),
            ('yellow', 'Yellow'),
            ('red', 'Red'),
        ],
        help_text="Avatar background color"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'Testimonial'
        verbose_name_plural = 'Testimonials'
    
    def __str__(self):
        return f"{self.customer_name} - {self.rating} stars"
    
    def get_initials(self):
        """Get customer initials for avatar"""
        names = self.customer_name.split()
        if len(names) >= 2:
            return f"{names[0][0]}{names[1][0]}".upper()
        elif len(names) == 1:
            return names[0][0].upper()
        return "C"
