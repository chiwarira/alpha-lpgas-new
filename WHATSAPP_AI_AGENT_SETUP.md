# WhatsApp AI Agent Setup Guide

## Overview

The WhatsApp AI Agent automates the Alpha LPGas sales process by:
- **Receiving** WhatsApp messages from clients
- **Understanding** order requests using AI (OpenAI GPT-4 or Anthropic Claude)
- **Extracting** product details, quantities, and delivery addresses
- **Creating** invoices and orders automatically
- **Assigning** drivers for delivery
- **Escalating** to human agents when needed

## Architecture

```
WhatsApp Message → Webhook → AI Processing → Order Creation → Driver Assignment
                                    ↓
                              Human Escalation (if needed)
```

## Prerequisites

1. **WhatsApp Business Account**
   - WhatsApp Business API access
   - Meta Business Manager account
   - Verified business phone number

2. **AI Provider Account**
   - OpenAI account with API access (recommended: GPT-4)
   - OR Anthropic account with Claude API access

3. **Server Requirements**
   - Public HTTPS endpoint for webhook
   - SSL certificate (required by WhatsApp)

## Installation Steps

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

New dependencies added:
- `openai==1.12.0` - OpenAI API client
- `anthropic==0.18.1` - Anthropic API client

### 2. Run Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

This creates the following tables:
- `WhatsAppConversation` - Tracks conversations with clients
- `WhatsAppMessage` - Stores individual messages
- `WhatsAppOrderIntent` - Tracks order extraction attempts
- `WhatsAppConfig` - System configuration (singleton)

### 3. Configure WhatsApp Business API

#### Step 3.1: Get WhatsApp Credentials

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create or select your app
3. Add "WhatsApp" product
4. Navigate to WhatsApp → Getting Started
5. Note down:
   - **Phone Number ID**
   - **Business Account ID**
   - **Access Token** (generate a permanent token)

#### Step 3.2: Set Up Webhook

1. In Django admin, go to **WhatsApp Configuration**
2. Generate a random webhook verify token:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
3. Save this token in WhatsApp Config

4. In Meta Developer Console:
   - Go to WhatsApp → Configuration
   - Click "Edit" on Webhook
   - Set Callback URL: `https://yourdomain.com/api/whatsapp/webhook/`
   - Set Verify Token: (use the token from step 2)
   - Subscribe to: `messages`
   - Click "Verify and Save"

### 4. Configure AI Provider

#### Option A: OpenAI (Recommended)

1. Get API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. In Django admin → WhatsApp Configuration:
   - AI Provider: `OpenAI (GPT-4)`
   - AI API Key: `sk-...` (your OpenAI key)
   - AI Model: `gpt-4o` or `gpt-4-turbo`

#### Option B: Anthropic Claude

1. Get API key from [Anthropic Console](https://console.anthropic.com/)
2. In Django admin → WhatsApp Configuration:
   - AI Provider: `Anthropic (Claude)`
   - AI API Key: `sk-ant-...` (your Anthropic key)
   - AI Model: `claude-3-opus-20240229` or `claude-3-sonnet-20240229`

### 5. Configure System Settings

In Django Admin → **WhatsApp Configuration**, configure:

#### WhatsApp Business API
- **Phone Number ID**: From Meta console
- **Business Account ID**: From Meta console
- **Access Token**: Permanent token from Meta
- **Webhook Verify Token**: Your generated token
- **Is Active**: ✓ (enable the integration)

#### AI Configuration
- **Min Confidence Threshold**: 80 (orders below this confidence are escalated)

#### Automation Settings
- **Auto Create Invoices**: ✓ (automatically create invoices)
- **Auto Assign Drivers**: ✓ (automatically assign available drivers)

#### Business Hours
- **Business Hours Start**: 08:00
- **Business Hours End**: 18:00
- **Auto Respond Outside Hours**: ✓
- **Outside Hours Message**: Customize the message

#### Messages
- **Welcome Message**: Customize greeting for new conversations
- **System Prompt**: Customize AI behavior (advanced)

## Usage

### For Customers

Customers can send WhatsApp messages like:

```
Hi, I need 2x 9kg gas cylinders delivered to 
123 Main Street, Fish Hoek
```

The AI will:
1. Extract: 2x 9kg cylinders
2. Extract: Delivery address
3. Find matching products
4. Calculate pricing
5. Create invoice and order
6. Assign driver
7. Send confirmation with order number

### For Staff

#### Monitor Conversations

1. Go to Django Admin → **WhatsApp Conversations**
2. View all active conversations
3. Filter by:
   - Status (Active, Resolved, Escalated)
   - Requires Human (Yes/No)
   - Client

#### Handle Escalations

When AI confidence is low or encounters issues:

1. Conversation is marked "Escalated"
2. View in Admin → **WhatsApp Conversations**
3. Filter by "Requires Human = Yes"
4. Click conversation to view full history
5. Click "Send Message" to respond manually
6. Click "Resolve" when handled

#### View Order Intents

1. Go to Django Admin → **WhatsApp Order Intents**
2. See all extracted orders with:
   - Products and quantities
   - Confidence scores
   - Created invoices/orders
   - Status

## API Endpoints

### Webhook (Public)
```
GET/POST /api/whatsapp/webhook/
```
- Receives WhatsApp messages
- No authentication required (verified by token)

### Conversations
```
GET /api/whatsapp/conversations/
GET /api/whatsapp/conversations/{id}/
POST /api/whatsapp/conversations/{id}/send_message/
POST /api/whatsapp/conversations/{id}/assign_to_human/
POST /api/whatsapp/conversations/{id}/resolve/
GET /api/whatsapp/conversations/pending_human_review/
```

### Messages
```
GET /api/whatsapp/messages/
GET /api/whatsapp/messages/{id}/
```

### Order Intents
```
GET /api/whatsapp/order-intents/
GET /api/whatsapp/order-intents/{id}/
```

## Testing

### Test Webhook Locally (Development)

Use ngrok to expose local server:

```bash
# Install ngrok
# Start your Django server
python manage.py runserver

# In another terminal
ngrok http 8000

# Use the ngrok HTTPS URL in Meta webhook config
# Example: https://abc123.ngrok.io/api/whatsapp/webhook/
```

### Test Messages

Send test messages to your WhatsApp Business number:

1. **Simple Order**:
   ```
   I need 1x 9kg gas cylinder
   Deliver to 45 Beach Road, Fish Hoek
   ```

2. **Multiple Items**:
   ```
   Hi! Can I order:
   - 2x 9kg cylinders
   - 1x 19kg cylinder
   
   Address: 78 Main Street, Kommetjie
   Gate code: 5678
   ```

3. **Unclear Request** (should escalate):
   ```
   Gas please
   ```

### Monitor Logs

```bash
# View Django logs
tail -f /path/to/logs/django.log

# Check for:
# - Webhook received
# - AI processing
# - Order creation
# - Escalations
```

## Troubleshooting

### Webhook Not Receiving Messages

1. Check webhook URL is HTTPS
2. Verify webhook token matches
3. Check Meta webhook subscriptions include "messages"
4. Test webhook verification:
   ```bash
   curl "https://yourdomain.com/api/whatsapp/webhook/?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=test"
   ```

### AI Not Processing Messages

1. Check AI API key is valid
2. Verify AI provider is selected correctly
3. Check Django logs for AI errors
4. Test AI API directly:
   ```python
   from core.services.whatsapp_ai_service import WhatsAppAIService
   service = WhatsAppAIService()
   # Should initialize without errors
   ```

### Orders Not Being Created

1. Check "Auto Create Invoices" is enabled
2. Verify products exist and are active
3. Check AI confidence threshold (lower if needed)
4. Review WhatsApp Order Intents in admin for errors
5. Check Django logs for exceptions

### Messages Not Sending

1. Verify WhatsApp access token is valid
2. Check phone number ID is correct
3. Test sending via API:
   ```python
   from core.services.whatsapp_service import WhatsAppService
   service = WhatsAppService()
   result = service.send_text_message('+27123456789', 'Test')
   print(result)
   ```

## Security Considerations

1. **API Keys**: Store in environment variables, not in code
2. **Webhook Token**: Use strong random token
3. **HTTPS**: Always use HTTPS for webhook endpoint
4. **Rate Limiting**: Consider adding rate limiting to webhook
5. **Access Control**: Restrict admin access to authorized staff

## Environment Variables

Add to `.env`:

```bash
# WhatsApp Configuration (optional - can use admin instead)
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_verify_token

# AI Configuration
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...
```

## Advanced Configuration

### Custom AI System Prompt

Modify the system prompt in WhatsApp Config to:
- Change AI personality
- Add specific business rules
- Include pricing information
- Add product details

### Confidence Threshold Tuning

- **High (90+)**: Very strict, more escalations
- **Medium (80)**: Balanced (recommended)
- **Low (70)**: More automation, fewer escalations

### Custom Message Templates

Edit in WhatsApp Config:
- Welcome message
- Outside hours message
- Order confirmation format (in code)

## Monitoring & Analytics

### Key Metrics to Track

1. **Conversation Volume**: Total conversations per day
2. **Automation Rate**: % of conversations resolved without human
3. **Escalation Rate**: % requiring human intervention
4. **Order Conversion**: % of conversations resulting in orders
5. **AI Confidence**: Average confidence scores

### Django Admin Reports

View in admin:
- Active conversations
- Pending human review
- Order intents by status
- Message volume by date

## Support

For issues or questions:
1. Check Django logs
2. Review WhatsApp conversations in admin
3. Test individual components (AI, WhatsApp API)
4. Check Meta Developer Console for webhook issues

## Next Steps

1. ✅ Complete setup following this guide
2. ✅ Test with sample messages
3. ✅ Train staff on handling escalations
4. ✅ Monitor first week closely
5. ✅ Adjust confidence threshold based on results
6. ✅ Customize messages and prompts
7. ✅ Set up monitoring and alerts
