# WhatsApp AI Agent - Local Testing Guide

## ✅ Yes! You Can Test Locally

The WhatsApp AI agent is fully testable on your local development environment. You just need a way to expose your local server to the internet so WhatsApp can send webhooks to it.

---

## Requirements for Local Testing

### 1. **Tunneling Service** (Required)
WhatsApp webhooks need a public HTTPS URL. You have two options:

#### Option A: ngrok (Recommended - Free)
- Easy to set up
- Free tier available
- Provides HTTPS automatically

#### Option B: localtunnel
- Open source alternative
- Also free
- Simpler but less stable

---

## Setup Instructions

### Step 1: Install ngrok

**Windows:**
1. Download from https://ngrok.com/download
2. Extract `ngrok.exe` to a folder (e.g., `C:\ngrok\`)
3. Add to PATH or run from that folder

**Or via Chocolatey:**
```powershell
choco install ngrok
```

**Or via npm:**
```bash
npm install -g ngrok
```

### Step 2: Create ngrok Account (Free)
1. Go to https://dashboard.ngrok.com/signup
2. Sign up (free account is fine)
3. Get your auth token from dashboard
4. Run:
   ```bash
   ngrok config add-authtoken YOUR_AUTH_TOKEN
   ```

### Step 3: Start Your Local Django Server
```bash
cd backend
.\venv\Scripts\activate
python manage.py runserver
```

Server runs on: `http://127.0.0.1:8000`

### Step 4: Start ngrok Tunnel
Open a **new terminal** and run:
```bash
ngrok http 8000
```

You'll see output like:
```
Session Status                online
Account                       your@email.com
Version                       3.x.x
Region                        United States (us)
Forwarding                    https://abc123.ngrok-free.app -> http://localhost:8000
```

**Copy the HTTPS URL:** `https://abc123.ngrok-free.app`

### Step 5: Configure Local Environment Variables

Create or update `backend/.env`:

```bash
# Django Settings
DEBUG=True
SECRET_KEY=your-local-secret-key
DATABASE_URL=sqlite:///db.sqlite3

# WhatsApp Configuration
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id_from_meta
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id
WHATSAPP_ACCESS_TOKEN=your_permanent_access_token
WHATSAPP_VERIFY_TOKEN=my_secure_verify_token_123
WHATSAPP_API_VERSION=v18.0

# AI Provider (Choose ONE)
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...your_key_here
OPENAI_MODEL=gpt-4o-mini

# OR for Anthropic
# AI_PROVIDER=anthropic
# ANTHROPIC_API_KEY=sk-ant-...your_key_here
# ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

### Step 6: Update WhatsApp Webhook URL

1. Go to https://developers.facebook.com/
2. Open your WhatsApp app
3. Go to **WhatsApp** → **Configuration**
4. Click **Edit** next to Webhook
5. Enter:
   - **Callback URL**: `https://abc123.ngrok-free.app/api/whatsapp/webhook/`
   - **Verify Token**: `my_secure_verify_token_123` (same as in .env)
6. Click **Verify and Save**

**Important:** Every time you restart ngrok, you get a **new URL**. You'll need to update the webhook URL in Meta dashboard each time.

### Step 7: Test It!

1. Send a WhatsApp message to your business number:
   ```
   Hi, I'd like to order 2x 9kg gas cylinders for delivery to 123 Main St, Johannesburg
   ```

2. Watch your terminal for logs:
   - Django server terminal shows incoming webhook
   - You should see AI processing
   - Invoice creation logs

3. Check the database:
   - New invoice should be created
   - Payment should be pending
   - Order assigned to driver (if configured)

---

## Local Testing Workflow

```
Your Phone → WhatsApp → Meta API → ngrok tunnel → localhost:8000 → Django → AI → Database
                                                                              ↓
                                                                         Response
```

---

## Debugging Local Setup

### Check ngrok is Running
Visit the ngrok web interface: http://127.0.0.1:4040

This shows:
- All incoming requests
- Request/response details
- Useful for debugging webhook issues

### Check Django Logs
Your `runserver` terminal will show:
```
[08/Apr/2026 17:30:15] "POST /whatsapp/webhook/ HTTP/1.1" 200 0
```

### Check WhatsApp Webhook Status
In Meta dashboard:
- Green checkmark = Webhook verified successfully
- Red X = Verification failed (check verify token)

### Common Issues

**1. ngrok URL Changes**
- Free ngrok URLs change on restart
- Solution: Update webhook URL in Meta dashboard
- OR: Get ngrok paid plan for static domain

**2. Webhook Verification Fails**
- Check `WHATSAPP_VERIFY_TOKEN` matches in both .env and Meta
- Ensure ngrok is forwarding to correct port (8000)
- Check Django server is running

**3. Messages Not Received**
- Check ngrok tunnel is active
- Verify webhook URL is correct in Meta
- Check webhook subscriptions include `messages`
- Look at ngrok web interface (http://127.0.0.1:4040) for incoming requests

**4. AI Not Processing**
- Check API key is valid
- Verify sufficient credits
- Look for errors in Django terminal

---

## Environment Variables Comparison

### Local (.env file)
```bash
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1,.ngrok-free.app
```

### Production (Railway)
```bash
DEBUG=False
DATABASE_URL=postgresql://... (provided by Railway)
ALLOWED_HOSTS=api.alphalpgas.co.za
```

**WhatsApp and AI variables are the same for both!**

---

## Tips for Local Testing

### 1. Use ngrok Free Tier
- Sufficient for testing
- 40 connections/minute limit (plenty for testing)
- URL changes on restart (minor inconvenience)

### 2. Keep ngrok Running
- Don't close the ngrok terminal
- If it closes, you need to update webhook URL again

### 3. Test Incrementally
1. First: Test webhook receives messages
2. Then: Test AI processing
3. Then: Test invoice creation
4. Finally: Test driver assignment

### 4. Use Test Phone Numbers
- Meta provides test numbers for development
- Can send to 5 numbers without business verification
- Good for initial testing

### 5. Monitor Both Terminals
- **Terminal 1**: Django runserver (see app logs)
- **Terminal 2**: ngrok (see tunnel status)
- **Browser**: ngrok web UI at http://127.0.0.1:4040

---

## Quick Start Commands

**Terminal 1 - Django:**
```bash
cd backend
.\venv\Scripts\activate
python manage.py runserver
```

**Terminal 2 - ngrok:**
```bash
ngrok http 8000
```

**Then:**
1. Copy ngrok HTTPS URL
2. Update webhook in Meta dashboard
3. Send test WhatsApp message
4. Watch the magic happen! ✨

---

## When to Use Local vs Production

### Use Local Testing For:
- ✅ Development and debugging
- ✅ Testing new features
- ✅ Experimenting with AI prompts
- ✅ Learning how the system works

### Use Production (Railway) For:
- ✅ Real customer orders
- ✅ 24/7 availability
- ✅ Stable webhook URL
- ✅ Production database

---

## Cost of Local Testing

- **ngrok Free**: $0
- **Django local**: $0
- **WhatsApp**: First 1,000 conversations free
- **AI API**: Only pay for what you use (~$0.01 per test)

**Total cost for testing:** ~$0 - $1 for extensive testing

---

## Next Steps

1. Install ngrok
2. Start local server
3. Start ngrok tunnel
4. Update webhook URL
5. Send test message
6. Debug and iterate!

**Ready to start? Let me know if you need help with any step!**
