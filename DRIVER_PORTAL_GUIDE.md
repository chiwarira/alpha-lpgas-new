# Driver Portal - Complete Guide

## 🚀 Overview

A dedicated mobile-friendly portal for drivers to manage their deliveries. Drivers can log in, view assigned orders, update delivery status, and manage their profile.

## 📍 Access URLs

- **Driver Login**: `http://localhost:8000/driver/login/`
- **Driver Dashboard**: `http://localhost:8000/driver/`
- **My Deliveries**: `http://localhost:8000/driver/deliveries/`
- **My Profile**: `http://localhost:8000/driver/profile/`

## 🔐 Security Features

### Driver-Only Access
- Custom `@driver_required` decorator
- Ensures user has an active driver profile
- Redirects non-drivers to login
- Automatic logout for inactive drivers

### Login Credentials
Use the test driver account:
- **Username**: `test_driver`
- **Password**: `testpass123`

## 🎯 Features

### 1. **Driver Dashboard** (`/driver/`)

**What Drivers See:**
- Welcome message with current date
- Current status badge (Available, On Delivery, On Break, Off Duty)
- Quick status change button
- Statistics cards:
  - Pending deliveries
  - Out for delivery count
  - Today's completed deliveries
- Active deliveries list with:
  - Customer name
  - Order number
  - Delivery address
  - Customer phone
  - Current status
  - Quick "View Details" button

**Actions:**
- Change status (Available, On Break, Off Duty)
- View delivery details
- Navigate to all deliveries

### 2. **My Deliveries** (`/driver/deliveries/`)

**Filter Tabs:**
- **Active**: Confirmed, Preparing, Out for Delivery
- **Completed**: Delivered orders
- **All**: All assigned orders

**Delivery Cards Show:**
- Customer name and phone
- Order number
- Delivery address
- Delivery zone
- Order total
- Created date/time
- Current status badge
- "View Details" button

### 3. **Delivery Detail** (`/driver/deliveries/{id}/`)

**Complete Order Information:**

**Status Section:**
- Current status with color-coded badge
- "Update Status" button (for active deliveries)

**Customer Information:**
- Name
- Phone (clickable to call)
- Email

**Delivery Address:**
- Full address
- Delivery zone
- "Open in Maps" button (Google Maps integration)
- Delivery notes (if any)

**Order Items:**
- Product name and variant
- Quantity
- Individual prices
- Subtotal, delivery fee, discount
- Total amount

**Payment Information:**
- Payment method
- Payment status (Paid/Pending)

**Timeline:**
- Status history with timestamps
- Notes for each status change

**Status Update Actions:**
- **Mark as Out for Delivery** (from Confirmed/Preparing)
- **Mark as Delivered** (from Out for Delivery)

### 4. **My Profile** (`/driver/profile/`)

**Statistics:**
- Total deliveries completed
- Today's completed deliveries

**Editable Information:**
- Email address
- Phone number
- Home address

**Read-Only Information:**
- Full name
- Username
- Vehicle type
- Vehicle registration
- Vehicle make/model
- Performance rating
- Member since date

**Actions:**
- Update profile
- Logout

## 🎨 UI/UX Features

### Mobile-First Design
- Optimized for smartphones
- Large touch-friendly buttons
- Bottom navigation bar (mobile)
- Responsive cards and layouts

### Visual Elements
- **Color-Coded Status Badges:**
  - 🟢 Green: Available, Delivered
  - 🟡 Yellow: Preparing, On Delivery
  - 🔵 Blue: Confirmed, Out for Delivery
  - ⚪ Gray: Off Duty
  - 🔵 Light Blue: On Break

- **Icons:** Bootstrap Icons throughout
- **Cards:** Clean, modern card design
- **Bottom Nav:** Fixed navigation (mobile)
- **Modals:** For status updates

### User Experience
- One-tap phone calling
- One-tap map navigation
- Quick status changes
- Real-time updates
- Clear visual feedback
- Success/error messages

## 🔄 Workflow

### Typical Driver Day

1. **Login** → Driver logs in at `/driver/login/`
2. **Check Dashboard** → See pending deliveries
3. **Change Status** → Set to "Available"
4. **View Delivery** → Click on assigned delivery
5. **Start Delivery** → Mark as "Out for Delivery"
6. **Navigate** → Use "Open in Maps" button
7. **Call Customer** → Tap phone number if needed
8. **Complete** → Mark as "Delivered"
9. **Repeat** → Next delivery
10. **End Day** → Set status to "Off Duty"

### Status Flow

```
Confirmed → Preparing → Out for Delivery → Delivered
                ↓
            (Driver can update from here)
```

## 🔧 Technical Details

### Views (`core/views_driver_portal.py`)
- `driver_login` - Custom login for drivers only
- `driver_logout` - Logout handler
- `driver_dashboard` - Main dashboard
- `driver_deliveries` - Delivery list with filters
- `driver_delivery_detail` - Full delivery details
- `driver_update_status` - AJAX status updates
- `driver_profile` - Profile view/edit
- `driver_update_location` - Status change handler

### URLs (`core/urls/driver_portal.py`)
```python
/driver/login/                          # Login
/driver/                                # Dashboard
/driver/deliveries/                     # All deliveries
/driver/deliveries/{id}/                # Delivery detail
/driver/deliveries/{id}/update-status/  # Update status
/driver/profile/                        # Profile
/driver/update-location/                # Change driver status
```

### Templates
- `driver_portal/base.html` - Base template with bottom nav
- `driver_portal/login.html` - Beautiful login page
- `driver_portal/dashboard.html` - Dashboard with stats
- `driver_portal/deliveries.html` - Delivery list
- `driver_portal/delivery_detail.html` - Full delivery info
- `driver_portal/profile.html` - Profile management

### Permissions
- `@driver_required` decorator on all views
- Checks for active driver profile
- Ensures orders belong to logged-in driver
- Validates status transitions

## 📱 Mobile Features

### Bottom Navigation
- **Home**: Dashboard
- **Deliveries**: All deliveries
- **Profile**: Driver profile
- **Logout**: Sign out

### Touch-Optimized
- Large buttons (min 44x44px)
- Adequate spacing
- Easy-to-tap links
- Swipe-friendly cards

### Responsive Design
- Works on all screen sizes
- Adapts to portrait/landscape
- Tables scroll horizontally
- Cards stack vertically

## 🎯 Driver Capabilities

### What Drivers CAN Do:
✅ View assigned deliveries only
✅ See customer contact information
✅ Update delivery status
✅ View order items and totals
✅ Access delivery addresses
✅ Open addresses in maps
✅ Call customers directly
✅ Change their availability status
✅ Update their profile (email, phone, address)
✅ View their performance stats

### What Drivers CANNOT Do:
❌ See other drivers' deliveries
❌ Access admin panel
❌ View all orders
❌ Change order details
❌ Access accounting section
❌ Modify pricing
❌ Delete orders
❌ Assign themselves to orders

## 🧪 Testing Guide

### 1. Test Login
```
URL: http://localhost:8000/driver/login/
Username: test_driver
Password: testpass123
```

### 2. Test Dashboard
- Verify statistics display
- Check status badge
- Try changing status
- View active deliveries

### 3. Test Deliveries
- Click "View All" or bottom nav "Deliveries"
- Try different filter tabs
- Click on a delivery

### 4. Test Delivery Detail
- Verify all information displays
- Try "Open in Maps" button
- Try calling customer (if on mobile)
- Update delivery status

### 5. Test Profile
- Update email/phone
- Verify information saves
- Check statistics

### 6. Test Logout
- Click logout
- Verify redirect to login
- Try accessing dashboard (should redirect)

## 🔒 Security Considerations

1. **Authentication Required**: All pages require login
2. **Driver Verification**: Must have active driver profile
3. **Order Ownership**: Can only see own deliveries
4. **Status Validation**: Only valid status transitions allowed
5. **CSRF Protection**: All forms protected
6. **Session Management**: Automatic logout for inactive drivers

## 📊 Integration Points

### With Order System
- Orders assigned via admin `/accounting/orders/`
- Driver sees orders in real-time
- Status updates reflect in admin
- History tracked automatically

### With Driver Management
- Driver info from `/accounting/drivers/`
- Performance metrics updated
- Delivery count incremented
- Rating displayed

## 🚀 Deployment Notes

### Production Checklist
- [ ] Change test driver password
- [ ] Set up SSL/HTTPS
- [ ] Configure session timeout
- [ ] Enable rate limiting
- [ ] Set up monitoring
- [ ] Test on actual mobile devices

### Environment Variables
No additional environment variables needed. Uses existing Django settings.

## 📈 Future Enhancements (Optional)

- [ ] Push notifications for new deliveries
- [ ] GPS tracking integration
- [ ] Photo proof of delivery
- [ ] Customer signature capture
- [ ] Earnings calculator
- [ ] Route optimization
- [ ] Offline mode
- [ ] Delivery history export
- [ ] Performance analytics
- [ ] Multi-language support

## 🎉 Benefits

### For Drivers:
- Simple, focused interface
- Mobile-optimized
- Easy status updates
- Quick access to customer info
- Performance tracking

### For Business:
- Real-time delivery tracking
- Better driver accountability
- Improved customer service
- Automated status updates
- Performance monitoring

### For Customers:
- Accurate delivery status
- Driver can easily contact them
- Faster deliveries
- Better communication

## 📞 Support

### Common Issues:

**Can't login?**
- Verify username/password
- Check if driver profile is active
- Contact admin

**Don't see deliveries?**
- Check if orders are assigned to you
- Try different filter tabs
- Refresh the page

**Can't update status?**
- Ensure delivery is in correct state
- Check internet connection
- Verify you're assigned to the order

## ✅ Ready to Use!

The driver portal is:
- ✅ Fully functional
- ✅ Mobile-optimized
- ✅ Secure
- ✅ User-friendly
- ✅ Integrated with existing system
- ✅ Ready for production

Test it now at: **http://localhost:8000/driver/login/**
