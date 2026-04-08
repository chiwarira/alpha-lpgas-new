# WhatsApp AI Agent - Complete Setup Guide

## 1. WhatsApp Business API Setup

### Option A: Meta Cloud API (Recommended - Free Tier Available)

#### Step 1: Create Meta Business Account
1. Go to https://business.facebook.com/
2. Click **"Create Account"**
3. Enter your business details:
   - Business name: **Alpha LPGas**
   - Your name
   - Business email
4. Complete verification

#### Step 2: Set Up WhatsApp Business API
1. Go to https://developers.facebook.com/
2. Click **"My Apps"** → **"Create App"**
3. Select **"Business"** as app type
4. Fill in app details:
   - App name: `Alpha LPGas WhatsApp`
   - Contact email: Your business email
   - Business account: Select your Meta Business account
5. Click **"Create App"**

#### Step 3: Add WhatsApp Product
1. In your app dashboard, find **"WhatsApp"** in the products list
2. Click **"Set Up"**
3. Select your **Meta Business Account**
4. Click **"Continue"**

#### Step 4: Get Phone Number
You have two options:

**Option 1: Use Meta's Test Number (Quick Start)**
- Meta provides a test number for development
- Limited to 5 recipient numbers
- Good for testing before going live

**Option 2: Add Your Own Number (Production)**
1. Click **"Add Phone Number"**
2. Enter your business phone number: `+27...`
3. Verify via SMS code
4. Accept WhatsApp Business Terms

**Important:** The phone number:
- Cannot be used on regular WhatsApp
- Must be a mobile number (not landline)
- Should be dedicated to business use

#### Step 5: Get API Credentials
1. In WhatsApp dashboard, go to **"API Setup"**
2. Copy these values:
   - **Phone Number ID**: `123456789012345`
   - **WhatsApp Business Account ID**: `123456789012345`
   - **Access Token** (temporary - 24 hours)

3. Generate **Permanent Access Token**:
   - Go to **"System Users"** in Business Settings
   - Create new system user: `whatsapp-api-user`
   - Assign **WhatsApp Business Management** permission
   - Generate token with these permissions:
     - `whatsapp_business_management`
     - `whatsapp_business_messaging`
   - **Save this token securely** - you won't see it again!

#### Step 6: Configure Webhook (We'll do this after server setup)
- Callback URL: `https://api.alphalpgas.co.za/api/whatsapp/webhook/`
- Verify Token: (you choose this - we'll set it later)

---

## 2. AI Provider Setup

### Option A: OpenAI (Recommended)

#### Step 1: Create OpenAI Account
1. Go to https://platform.openai.com/signup
2. Sign up with email or Google account
3. Verify your email

#### Step 2: Add Payment Method
1. Go to https://platform.openai.com/account/billing
2. Click **"Add payment method"**
3. Add credit/debit card
4. Set up **auto-recharge** (recommended):
   - Minimum: $5
   - Recharge when balance drops below $5

#### Step 3: Get API Key
1. Go to https://platform.openai.com/api-keys
2. Click **"Create new secret key"**
3. Name it: `Alpha LPGas WhatsApp Agent`
4. **Copy the key** - starts with `sk-...`
5. **Save it securely** - you won't see it again!

#### Pricing (as of 2026)
- **GPT-4o**: ~$2.50 per 1M input tokens, ~$10 per 1M output tokens
- **GPT-4o-mini**: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
- Estimated cost: **$0.01 - 0.05 per customer conversation**

**Recommended Model:** `gpt-4o-mini` (fast, cheap, accurate for order processing)

---

### Option B: Anthropic Claude (Alternative)

#### Step 1: Create Anthropic Account
1. Go to https://console.anthropic.com/
2. Sign up with email
3. Verify your email

#### Step 2: Add Payment Method
1. Go to **"Billing"** in console
2. Add credit/debit card
3. Add initial credits ($5 minimum)

#### Step 3: Get API Key
1. Go to **"API Keys"** section
2. Click **"Create Key"**
3. Name it: `Alpha LPGas WhatsApp`
4. **Copy the key** - starts with `sk-ant-...`
5. **Save it securely**

#### Pricing
- **Claude 3.5 Sonnet**: ~$3 per 1M input tokens, ~$15 per 1M output tokens
- **Claude 3 Haiku**: ~$0.25 per 1M input tokens, ~$1.25 per 1M output tokens

**Recommended Model:** `claude-3-5-sonnet-20241022` (best reasoning)

---

## 3. Server Requirements (Already Done! ✅)

Your Railway deployment already has:

### ✅ Public HTTPS Endpoint
- **Production URL**: `https://api.alphalpgas.co.za`
- **SSL Certificate**: Automatically managed by Railway
- **Webhook endpoint**: Will be at `/whatsapp/webhook/`

### What You Need to Do:

#### Step 1: Add Environment Variables to Railway

1. Go to https://railway.app
2. Select **Alpha LPGas** project
3. Click **backend** service
4. Go to **"Variables"** tab
5. Add these variables:

**WhatsApp Configuration:**
```
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id_from_meta
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id
WHATSAPP_ACCESS_TOKEN=your_permanent_access_token
WHATSAPP_VERIFY_TOKEN=choose_a_random_secure_string
WHATSAPP_API_VERSION=v18.0
```

**AI Provider (Choose ONE):**

For OpenAI:
```
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...your_key_here
OPENAI_MODEL=gpt-4o-mini
```

OR for Anthropic:
```
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...your_key_here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

6. Click **"Deploy"** to restart with new variables

#### Step 2: Configure WhatsApp Webhook

1. Go back to Meta Developers: https://developers.facebook.com/
2. Open your WhatsApp app
3. Go to **WhatsApp** → **"Configuration"**
4. Click **"Edit"** next to Webhook
5. Enter:
   - **Callback URL**: `https://api.alphalpgas.co.za/whatsapp/webhook/`
   - **Verify Token**: (same value you set in `WHATSAPP_VERIFY_TOKEN`)
6. Click **"Verify and Save"**

7. Subscribe to webhook fields:
   - ✅ `messages` (required)
   - ✅ `message_status` (optional - for delivery status)

#### Step 3: Test the Connection

1. Send a WhatsApp message to your business number
2. Check Railway logs:
   ```bash
   railway logs --service backend
   ```
3. You should see webhook events coming in

---

## Quick Start Checklist

- [ ] **Meta Business Account** created
- [ ] **WhatsApp Business API** app created
- [ ] **Business phone number** verified
- [ ] **Permanent access token** generated and saved
- [ ] **OpenAI or Anthropic** account created
- [ ] **AI API key** generated and saved
- [ ] **Environment variables** added to Railway
- [ ] **Webhook configured** in Meta dashboard
- [ ] **Test message** sent and received

---

## Cost Estimates

### Monthly Costs (Estimated)

**WhatsApp (Meta Cloud API):**
- First 1,000 conversations/month: **FREE**
- After that: ~$0.005 - 0.03 per conversation (varies by country)
- South Africa: ~$0.01 per conversation

**AI Processing:**
- OpenAI GPT-4o-mini: ~$0.01 per conversation
- Anthropic Claude Haiku: ~$0.005 per conversation

**Total per conversation:** ~$0.02 - 0.04

**For 500 orders/month:** ~$10 - 20/month

---

## Troubleshooting

### Webhook Not Receiving Messages
1. Check Railway logs for errors
2. Verify webhook URL is accessible: `https://api.alphalpgas.co.za/whatsapp/webhook/`
3. Check verify token matches in both Meta and Railway
4. Ensure webhook fields are subscribed

### AI Not Responding
1. Check AI provider API key is valid
2. Verify sufficient credits/balance
3. Check Railway logs for AI API errors
4. Test API key with curl:
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer YOUR_API_KEY"
   ```

### Phone Number Issues
1. Number must be mobile (not landline)
2. Cannot be registered on regular WhatsApp
3. Must complete business verification for production use

---

## Next Steps

Once setup is complete:
1. Test with a simple order message
2. Monitor logs to see AI processing
3. Check if invoice is created automatically
4. Verify driver assignment works
5. Test escalation to human agent

## Support Resources

- **Meta WhatsApp Docs**: https://developers.facebook.com/docs/whatsapp
- **OpenAI API Docs**: https://platform.openai.com/docs
- **Anthropic Docs**: https://docs.anthropic.com/
- **Railway Docs**: https://docs.railway.app/

---

**Need help?** Let me know which step you're on and I can guide you through it!
