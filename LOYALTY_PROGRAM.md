# Loyalty Program Documentation

## Overview
The loyalty program rewards customers with stamps for each cylinder purchase. After 9 purchases, customers receive a reward:
- **5kg & 9kg cylinders**: FREE cylinder on 10th purchase
- **19kg & 48kg cylinders**: 50% OFF on 10th purchase

## How It Works

### 1. Automatic Stamp Processing
When an invoice is created with status `paid` or `partially_paid`:
1. System detects cylinder size from invoice items (5kg, 9kg, 19kg, or 48kg)
2. Gets or creates a loyalty card for that client and cylinder size
3. Adds a stamp to the card
4. Records the transaction in `LoyaltyTransaction`
5. Generates a loyalty card image with stamped circles
6. Sends WhatsApp message with the card image (if configured)

### 2. Database Models

#### LoyaltyCard
- `client`: ForeignKey to Client
- `cylinder_size`: Choice field (5kg, 9kg, 19kg, 48kg)
- `stamps`: Integer (0-9+)
- `is_active`: Boolean
- Unique constraint: One active card per client per cylinder size

#### LoyaltyTransaction
- `loyalty_card`: ForeignKey to LoyaltyCard
- `invoice`: ForeignKey to Invoice (optional)
- `transaction_type`: Choice (stamp, reward_claimed, card_reset)
- `stamps_before`: Integer
- `stamps_after`: Integer
- `notes`: Text
- `created_by`: ForeignKey to User

### 3. Loyalty Card Image Generation
The system generates a personalized loyalty card image:
- Uses `Back.png` as the base template
- Stamps circles 1-9 with the company logo
- Includes client name, cylinder size, and date
- Positions are hardcoded based on the template layout

**Circle Positions:**
- Circles 1-9 are arranged in a 2-column grid
- Logo is resized to 80x80 pixels and centered in each circle

### 4. Admin Interface

#### Loyalty Cards Admin
- View all loyalty cards with stamp counts
- Filter by cylinder size, active status, stamps
- Search by client name, phone, customer ID
- See reward status (e.g., "🎁 Free Cylinder" or "3 more needed")
- Actions:
  - **Reset selected cards**: Resets stamps to 0
  - **Generate and send loyalty cards**: Creates and sends card images

#### Loyalty Transactions Admin
- View all stamp transactions
- Filter by transaction type and date
- Read-only (transactions are auto-created)

### 5. Invoice Integration

The loyalty logic is integrated into:
- `invoice_create()` view in `views_forms.py`
- Automatically processes stamps when invoice status is paid/partially_paid
- Shows info message: "Loyalty card updated: X/9 stamps"

### 6. WhatsApp Integration (TODO)

Currently, the `send_loyalty_card_whatsapp()` function returns a dict with:
- `success`: Boolean
- `phone`: Cleaned phone number
- `message`: Personalized message text
- `image`: BytesIO object with PNG image
- `stamps`: Current stamp count

**To complete WhatsApp integration:**
1. Choose a provider (Twilio, WhatsApp Business API, etc.)
2. Update `send_loyalty_card_whatsapp()` in `utils_loyalty.py`
3. Add API credentials to settings
4. Implement actual message sending

### 7. Files Created/Modified

**New Files:**
- `backend/core/models_loyalty.py` - Loyalty models
- `backend/core/utils_loyalty.py` - Loyalty utility functions
- `backend/core/admin_loyalty.py` - Admin configuration
- `backend/core/migrations/0017_loyaltycard_loyaltytransaction.py` - Migration

**Modified Files:**
- `backend/core/models.py` - Import loyalty models
- `backend/core/admin.py` - Import loyalty admin
- `backend/core/views_forms.py` - Add loyalty processing to invoice creation

### 8. Testing the Loyalty Program

1. Create a client in Django admin
2. Create a product with "5kg" or "9kg" in the name
3. Create an invoice for the client with that product
4. Set invoice status to "Paid"
5. Check the loyalty card in admin - should show 1 stamp
6. Repeat 8 more times to see the reward status change

### 9. Reward Redemption (Manual Process)

When a client has 9+ stamps:
1. Admin sees "🎁 Free Cylinder" or "🎁 50% Off" in the loyalty card list
2. Create the reward invoice:
   - For 5kg/9kg: Set price to 0 or create a 100% discount
   - For 19kg/48kg: Apply 50% discount
3. Manually reset the card using the "Reset selected cards" action
4. Or the card can be reset programmatically after reward is claimed

### 10. Future Enhancements

- Automatic reward application on invoice creation
- Email notifications in addition to WhatsApp
- Loyalty points system instead of stamps
- Multiple reward tiers
- Expiry dates for stamps
- Client-facing loyalty card portal
