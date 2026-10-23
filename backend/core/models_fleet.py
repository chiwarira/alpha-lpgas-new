"""
Fleet management models: vehicles, service history, daily driver assignments
and driver cylinder stock counts.
"""
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User


class Vehicle(models.Model):
    """A delivery vehicle in the company fleet"""
    VEHICLE_TYPE_CHOICES = [
        ('bakkie', 'Bakkie'),
        ('van', 'Van'),
        ('truck', 'Truck'),
        ('motorcycle', 'Motorcycle'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('in_maintenance', 'In Maintenance'),
        ('decommissioned', 'Decommissioned'),
    ]

    registration_number = models.CharField(max_length=50, unique=True, help_text="License plate number")
    vin_number = models.CharField(max_length=50, blank=True, help_text="Vehicle Identification Number (VIN)")
    engine_number = models.CharField(max_length=50, blank=True)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPE_CHOICES, default='bakkie')
    make_model = models.CharField(max_length=100, blank=True, help_text="e.g., Toyota Hilux")
    year = models.PositiveIntegerField(null=True, blank=True)
    first_registration_date = models.DateField(null=True, blank=True, help_text="Date the vehicle was first registered")

    last_service_date = models.DateField(null=True, blank=True, help_text="Date of the most recent service (auto-updated from service records)")
    next_service_due_date = models.DateField(null=True, blank=True, help_text="When the next service is due (auto-updated from service records)")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['registration_number']

    def __str__(self):
        return f"{self.registration_number} ({self.make_model or self.get_vehicle_type_display()})"

    @property
    def service_overdue(self):
        from datetime import date
        return bool(self.next_service_due_date and self.next_service_due_date <= date.today())

    def update_service_dates(self):
        """Refresh cached service dates from the latest service record."""
        latest = self.service_records.order_by('-service_date', '-created_at').first()
        self.last_service_date = latest.service_date if latest else None
        self.next_service_due_date = latest.next_service_due_date if latest else None
        self.save(update_fields=['last_service_date', 'next_service_due_date'])


class VehicleServiceRecord(models.Model):
    """A service or maintenance event for a vehicle"""
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='service_records')
    service_date = models.DateField()
    description = models.TextField(help_text="Work carried out")
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    next_service_due_date = models.DateField(null=True, blank=True, help_text="When the next service is due after this one")
    serviced_by = models.CharField(max_length=100, blank=True, help_text="Workshop or mechanic name")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-service_date']

    def __str__(self):
        return f"{self.vehicle.registration_number} serviced on {self.service_date}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.vehicle.update_service_dates()

    def delete(self, *args, **kwargs):
        vehicle = self.vehicle
        super().delete(*args, **kwargs)
        vehicle.update_service_dates()


class VehicleAssignment(models.Model):
    """Daily assignment of a vehicle to a driver.
    A driver uses at most one vehicle per day and a vehicle goes to at most
    one driver per day."""
    date = models.DateField(db_index=True)
    driver = models.ForeignKey('Driver', on_delete=models.CASCADE, related_name='vehicle_assignments')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='driver_assignments')
    notes = models.CharField(max_length=255, blank=True, help_text="e.g., route or delivery area")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', 'driver__user__first_name']
        constraints = [
            models.UniqueConstraint(fields=['date', 'driver'], name='unique_driver_per_day'),
            models.UniqueConstraint(fields=['date', 'vehicle'], name='unique_vehicle_per_day'),
        ]
        verbose_name = 'Daily Vehicle Assignment'

    def __str__(self):
        return f"{self.date}: {self.driver} -> {self.vehicle.registration_number}"


class DriverStockCount(models.Model):
    """A cylinder stock count captured by a driver for a given day.
    'opening' and 'closing' happen at most once per day; 'restock' entries
    record stock added during the day."""
    COUNT_TYPE_CHOICES = [
        ('opening', 'Opening count'),
        ('restock', 'Restock'),
        ('closing', 'Closing count'),
    ]

    driver = models.ForeignKey('Driver', on_delete=models.CASCADE, related_name='stock_counts')
    date = models.DateField(db_index=True)
    count_type = models.CharField(max_length=10, choices=COUNT_TYPE_CHOICES)
    notes = models.CharField(max_length=255, blank=True, help_text="e.g., where the extra stock was loaded")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'count_type', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['driver', 'date', 'count_type'],
                condition=Q(count_type__in=['opening', 'closing']),
                name='unique_opening_closing_per_driver_day',
            ),
        ]
        verbose_name = 'Driver Stock Count'

    def __str__(self):
        return f"{self.date} {self.driver} - {self.get_count_type_display()}"


class DriverStockCountItem(models.Model):
    """Full/empty cylinder quantities for one size in a stock count"""
    count = models.ForeignKey(DriverStockCount, on_delete=models.CASCADE, related_name='items')
    cylinder_size = models.ForeignKey('CylinderSize', on_delete=models.PROTECT, related_name='driver_count_items')
    full = models.PositiveIntegerField(default=0, help_text="Number of full cylinders")
    empty = models.PositiveIntegerField(default=0, help_text="Number of empty cylinders")

    class Meta:
        ordering = ['cylinder_size__weight_kg']
        unique_together = ['count', 'cylinder_size']

    def __str__(self):
        return f"{self.cylinder_size.name}: {self.full} full / {self.empty} empty"
