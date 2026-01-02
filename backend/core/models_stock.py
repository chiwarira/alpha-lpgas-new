"""
Stock Management models for tracking gas cylinder inventory.
Tracks gas volume in kg across different cylinder sizes.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class CylinderSize(models.Model):
    """Standard cylinder sizes available (5kg, 9kg, 14kg, 19kg, 48kg)"""
    name = models.CharField(max_length=50, help_text="e.g., 5kg, 9kg, 14kg, 19kg, 48kg")
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, help_text="Weight in kilograms")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['weight_kg']
        verbose_name = 'Cylinder Size'
        verbose_name_plural = 'Cylinder Sizes'
    
    def __str__(self):
        return self.name


class GasStock(models.Model):
    """
    Current gas stock levels by cylinder size.
    Tracks quantity of cylinders and total gas volume.
    """
    cylinder_size = models.OneToOneField(CylinderSize, on_delete=models.CASCADE, related_name='stock')
    quantity = models.IntegerField(default=0, help_text="Number of full cylinders in stock")
    reorder_level = models.IntegerField(default=10, help_text="Minimum stock before reorder alert")
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Gas Stock'
        verbose_name_plural = 'Gas Stock Levels'
    
    def __str__(self):
        return f"{self.cylinder_size.name}: {self.quantity} cylinders"
    
    @property
    def total_volume_kg(self):
        """Total gas volume in kg for this cylinder size"""
        return self.quantity * self.cylinder_size.weight_kg
    
    @property
    def is_low_stock(self):
        """Check if stock is below reorder level"""
        return self.quantity <= self.reorder_level
    
    @classmethod
    def get_total_gas_volume(cls):
        """Get total gas volume across all cylinder sizes"""
        total = Decimal('0.00')
        for stock in cls.objects.select_related('cylinder_size').all():
            total += stock.total_volume_kg
        return total


class StockMovement(models.Model):
    """
    Track all stock movements (purchases and sales).
    """
    MOVEMENT_TYPE_CHOICES = [
        ('purchase', 'Purchase (Stock In)'),
        ('sale', 'Sale/Exchange (Stock Out)'),
        ('adjustment', 'Manual Adjustment'),
        ('transfer', 'Transfer'),
        ('return', 'Customer Return'),
        ('damage', 'Damaged/Write-off'),
    ]
    
    movement_number = models.CharField(max_length=50, unique=True, blank=True)
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)
    date = models.DateField()
    cylinder_size = models.ForeignKey(CylinderSize, on_delete=models.PROTECT, related_name='movements')
    quantity = models.IntegerField(help_text="Positive for stock in, negative for stock out")
    
    # Reference to related records
    supplier = models.ForeignKey('Supplier', on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements')
    expense = models.ForeignKey('Expense', on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements')
    invoice = models.ForeignKey('Invoice', on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements')
    invoice_item = models.ForeignKey('InvoiceItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements')
    
    # Additional details
    reference = models.CharField(max_length=100, blank=True, help_text="Invoice/PO number, etc.")
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Cost per cylinder")
    notes = models.TextField(blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='stock_movements_created')
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Stock Movement'
        verbose_name_plural = 'Stock Movements'
    
    def __str__(self):
        direction = "+" if self.quantity > 0 else ""
        return f"{self.movement_number}: {direction}{self.quantity} x {self.cylinder_size.name}"
    
    def save(self, *args, **kwargs):
        # Auto-generate movement number
        if not self.movement_number:
            from datetime import date
            today = date.today()
            prefix = f"SM-{today.strftime('%Y%m%d')}"
            
            last_movement = StockMovement.objects.filter(
                movement_number__startswith=prefix
            ).order_by('movement_number').last()
            
            if last_movement:
                try:
                    last_seq = int(last_movement.movement_number.split('-')[-1])
                    new_seq = last_seq + 1
                except (ValueError, IndexError):
                    new_seq = 1
            else:
                new_seq = 1
            
            self.movement_number = f"{prefix}-{new_seq:03d}"
        
        # Update stock levels
        is_new = self.pk is None
        if is_new:
            self._update_stock()
        
        super().save(*args, **kwargs)
    
    def _update_stock(self):
        """Update GasStock levels based on movement"""
        stock, created = GasStock.objects.get_or_create(
            cylinder_size=self.cylinder_size,
            defaults={'quantity': 0}
        )
        stock.quantity += self.quantity
        if stock.quantity < 0:
            stock.quantity = 0  # Prevent negative stock
        stock.save()
    
    @property
    def volume_kg(self):
        """Total gas volume moved in kg"""
        return abs(self.quantity) * self.cylinder_size.weight_kg


class StockPurchase(models.Model):
    """
    Bulk purchase entry for receiving gas cylinders from suppliers.
    Creates individual StockMovement records for each cylinder size.
    """
    purchase_number = models.CharField(max_length=50, unique=True, blank=True)
    date = models.DateField()
    supplier = models.ForeignKey('Supplier', on_delete=models.SET_NULL, null=True, related_name='stock_purchases')
    
    # Link to expense record if applicable
    expense = models.ForeignKey('Expense', on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_purchases')
    
    # Totals
    total_cylinders = models.IntegerField(default=0)
    total_volume_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    invoice_number = models.CharField(max_length=100, blank=True, help_text="Supplier invoice number")
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='stock_purchases_created')
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Stock Purchase'
        verbose_name_plural = 'Stock Purchases'
    
    def __str__(self):
        return f"{self.purchase_number} - {self.supplier.name if self.supplier else 'Unknown'}"
    
    def save(self, *args, **kwargs):
        # Auto-generate purchase number
        if not self.purchase_number:
            from datetime import date
            today = date.today()
            prefix = f"PO-{today.strftime('%Y%m%d')}"
            
            last_purchase = StockPurchase.objects.filter(
                purchase_number__startswith=prefix
            ).order_by('purchase_number').last()
            
            if last_purchase:
                try:
                    last_seq = int(last_purchase.purchase_number.split('-')[-1])
                    new_seq = last_seq + 1
                except (ValueError, IndexError):
                    new_seq = 1
            else:
                new_seq = 1
            
            self.purchase_number = f"{prefix}-{new_seq:03d}"
        
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculate totals from purchase items"""
        items = self.items.all()
        self.total_cylinders = sum(item.quantity for item in items)
        self.total_volume_kg = sum(item.quantity * item.cylinder_size.weight_kg for item in items)
        self.total_cost = sum(item.total_cost for item in items)
        self.save()


class StockPurchaseItem(models.Model):
    """Individual line items in a stock purchase"""
    purchase = models.ForeignKey(StockPurchase, on_delete=models.CASCADE, related_name='items')
    cylinder_size = models.ForeignKey(CylinderSize, on_delete=models.PROTECT)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        verbose_name = 'Purchase Item'
        verbose_name_plural = 'Purchase Items'
    
    def __str__(self):
        return f"{self.quantity} x {self.cylinder_size.name}"
    
    def save(self, *args, **kwargs):
        self.total_cost = self.quantity * self.unit_cost
        
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Create stock movement for new items
        if is_new:
            StockMovement.objects.create(
                movement_type='purchase',
                date=self.purchase.date,
                cylinder_size=self.cylinder_size,
                quantity=self.quantity,  # Positive for purchase
                supplier=self.purchase.supplier,
                expense=self.purchase.expense,
                reference=self.purchase.invoice_number,
                unit_cost=self.unit_cost,
                notes=f"Purchase: {self.purchase.purchase_number}",
                created_by=self.purchase.created_by
            )
        
        # Update purchase totals
        self.purchase.calculate_totals()
    
    @property
    def volume_kg(self):
        """Total gas volume in kg"""
        return self.quantity * self.cylinder_size.weight_kg
