# Driver Management System - Testing Guide

## ✅ Automated Tests Completed

All automated tests passed successfully:
- ✓ Driver model created and accessible
- ✓ Order model has assigned_driver field
- ✓ Test driver created (John Driver - TEST-123-GP)
- ✓ DriverSerializer working
- ✓ DriverViewSet working
- ✓ Driver admin registered

## 🧪 Manual Testing Checklist

### 1. Admin Interface Testing

#### Test Driver Management
1. Go to: http://localhost:8000/admin/core/driver/
2. You should see the test driver: "John Driver - TEST-123-GP"
3. Click to edit and verify all fields are present:
   - User account
   - Personal info (phone, ID, address)
   - Vehicle info (type, registration, make/model)
   - License info
   - Status & Performance
   - Notes

#### Test Order Assignment
1. Go to: http://localhost:8000/admin/core/order/
2. Click on any order to edit
3. In the "Delivery" section, you should see "Assigned driver" dropdown
4. Select "John Driver - TEST-123-GP" from the dropdown
5. Save the order
6. Verify the driver appears in the order list

### 2. API Endpoint Testing

#### Test Driver List API
```bash
# Get all drivers
curl http://localhost:8000/api/accounting/drivers/

# Expected: JSON list of drivers with full details
```

#### Test Available Drivers API
```bash
# Get only available drivers
curl http://localhost:8000/api/accounting/drivers/available/

# Expected: JSON list of drivers with status='available'
```

#### Test Driver Detail API
```bash
# Get specific driver (replace {id} with actual driver ID)
curl http://localhost:8000/api/accounting/drivers/1/

# Expected: Full driver details including user info and active deliveries count
```

#### Test Driver Active Deliveries
```bash
# Get active deliveries for a driver
curl http://localhost:8000/api/accounting/drivers/1/active_deliveries/

# Expected: List of orders assigned to this driver
```

#### Test Driver Status Update
```bash
# Update driver status (requires authentication)
curl -X POST http://localhost:8000/api/accounting/drivers/1/update_status/ \
  -H "Content-Type: application/json" \
  -d '{"status": "on_delivery"}'

# Expected: Success message with new status
```

### 3. Order API Testing

#### Test Order with Driver Info
```bash
# Get order details (should include driver info)
curl http://localhost:8000/api/accounting/orders/

# Expected: Orders with driver_name, driver_phone, driver_vehicle fields
```

### 4. Browser Testing

1. **Admin Dashboard**
   - Navigate to: http://localhost:8000/admin/
   - Login with your superuser credentials
   - Check "Drivers" appears in the Core section
   - Check "Orders" shows assigned driver column

2. **API Documentation**
   - Navigate to: http://localhost:8000/api/docs/
   - Look for `/api/accounting/drivers/` endpoints
   - Test the endpoints directly from Swagger UI

3. **Driver List View** (if implemented)
   - Navigate to: http://localhost:8000/accounting/drivers/
   - Should show list of all drivers

## 🔍 What to Look For

### Success Indicators
- ✅ Driver model appears in admin
- ✅ Can create/edit drivers
- ✅ Can assign drivers to orders
- ✅ API returns driver data correctly
- ✅ Driver status can be updated
- ✅ Orders show assigned driver information

### Potential Issues
- ❌ Migration errors (already applied successfully)
- ❌ Import errors (all tests passed)
- ❌ API 500 errors (check server logs)
- ❌ Missing fields in admin
- ❌ Permission errors on API endpoints

## 📊 Test Data Created

**Test Driver:**
- Username: test_driver
- Name: John Driver
- Phone: 0123456789
- Vehicle: Toyota Hilux (TEST-123-GP)
- Status: Available
- Type: Bakkie

## 🚀 Next Steps After Testing

1. If all tests pass, commit changes to git
2. Push to GitHub
3. Deploy to Railway (will auto-deploy)
4. Test on production environment
5. Create additional drivers as needed

## 🐛 Troubleshooting

If you encounter issues:

1. **Check migrations:**
   ```bash
   python manage.py showmigrations core
   ```

2. **Check server logs:**
   - Look at the terminal where Django is running
   - Check for any error messages

3. **Verify imports:**
   ```bash
   python manage.py shell
   >>> from core.models import Driver
   >>> from core.serializers import DriverSerializer
   >>> from core.views import DriverViewSet
   ```

4. **Check database:**
   ```bash
   python manage.py dbshell
   SELECT * FROM core_driver;
   ```

## 📝 Notes

- The test driver has password: `testpass123`
- Driver status options: available, on_delivery, off_duty, on_break
- Drivers can be filtered by status in the API
- Orders can be filtered by assigned driver in admin
