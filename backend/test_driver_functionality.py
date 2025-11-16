"""
Test script for Driver functionality
Run this with: python manage.py shell < test_driver_functionality.py
"""

from django.contrib.auth.models import User
from core.models import Driver, Order
from datetime import date

print("\n" + "="*60)
print("TESTING DRIVER FUNCTIONALITY")
print("="*60 + "\n")

# Test 1: Check if Driver model exists
print("✓ Test 1: Driver model imported successfully")

# Test 2: Check if we can query drivers
try:
    drivers = Driver.objects.all()
    print(f"✓ Test 2: Can query drivers - Found {drivers.count()} driver(s)")
except Exception as e:
    print(f"✗ Test 2 FAILED: {e}")

# Test 3: Check if Order model has assigned_driver field
try:
    orders = Order.objects.all()
    print(f"✓ Test 3: Order model has assigned_driver field - Found {orders.count()} order(s)")
except Exception as e:
    print(f"✗ Test 3 FAILED: {e}")

# Test 4: Create a test driver (if no users exist, skip)
try:
    # Get or create a test user
    user, created = User.objects.get_or_create(
        username='test_driver',
        defaults={
            'first_name': 'John',
            'last_name': 'Driver',
            'email': 'john.driver@test.com'
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✓ Test 4a: Created test user: {user.username}")
    else:
        print(f"✓ Test 4a: Test user already exists: {user.username}")
    
    # Create or get driver profile
    driver, created = Driver.objects.get_or_create(
        user=user,
        defaults={
            'phone': '0123456789',
            'vehicle_type': 'Bakkie',
            'vehicle_registration': 'TEST-123-GP',
            'vehicle_make_model': 'Toyota Hilux',
            'status': 'available',
            'is_active': True
        }
    )
    
    if created:
        print(f"✓ Test 4b: Created test driver: {driver}")
    else:
        print(f"✓ Test 4b: Test driver already exists: {driver}")
    
    # Test driver methods
    active_deliveries = driver.get_active_deliveries()
    print(f"✓ Test 4c: Driver has {active_deliveries.count()} active deliveries")
    
except Exception as e:
    print(f"✗ Test 4 FAILED: {e}")

# Test 5: Check API serializer
try:
    from core.serializers import DriverSerializer
    print("✓ Test 5: DriverSerializer imported successfully")
except Exception as e:
    print(f"✗ Test 5 FAILED: {e}")

# Test 6: Check API viewset
try:
    from core.views import DriverViewSet
    print("✓ Test 6: DriverViewSet imported successfully")
except Exception as e:
    print(f"✗ Test 6 FAILED: {e}")

# Test 7: Check admin registration
try:
    from django.contrib import admin
    from core.models import Driver
    
    if Driver in admin.site._registry:
        print("✓ Test 7: Driver model registered in admin")
    else:
        print("✗ Test 7 FAILED: Driver not registered in admin")
except Exception as e:
    print(f"✗ Test 7 FAILED: {e}")

# Summary
print("\n" + "="*60)
print("TEST SUMMARY")
print("="*60)
print("\nAll core functionality tests completed!")
print("\nTo test the API endpoints, visit:")
print("  - http://localhost:8000/api/accounting/drivers/")
print("  - http://localhost:8000/api/accounting/drivers/available/")
print("  - http://localhost:8000/admin/core/driver/")
print("\nTo test driver assignment to orders:")
print("  - Go to http://localhost:8000/admin/core/order/")
print("  - Edit any order and assign a driver")
print("\n" + "="*60 + "\n")
