# WhatsApp AI Agent - Quick Start Guide

## 🚀 Quick Setup (5 Minutes)

### Step 1: Install Dependencies
```bash
cd backend
pip install openai==1.12.0 anthropic==0.18.1
```

### Step 2: Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 3: Configure in Django Admin

1. Start your server:
   ```bash
   python manage.py runserver
   ```

2. Go to: `http://localhost:8000/admin/`

3. Navigate to: **Core → WhatsApp Configuration**

4. Fill in the required fields:

   **WhatsApp Business API:**
   - Phone Number ID: `[from Meta Developer Console]`
   - Business Account ID: `[from Meta Developer Console]`
   - Access Token: `[from Meta Developer Console]`
   - Webhook Verify Token: `[generate random string]`
   - Is Active: ✓

   **AI Configuration:**
   - AI Provider: `OpenAI (GPT-4)`
   - AI API Key: `sk-...` (your OpenAI key)
   - AI Model: `gpt-4o`
   - Min Confidence Threshold: `80`

   **Automation:**
   - Auto Create Invoices: ✓
   - Auto Assign Drivers: ✓

5. Click **Save**

### Step 4: Set Up Webhook

1. Deploy your app to a public HTTPS URL (Railway, Heroku, etc.)

2. In Meta Developer Console:
   - Go to WhatsApp → Configuration
   - Webhook URL: `https://yourdomain.com/api/whatsapp/webhook/`
   - Verify Token: [same as in Django admin]
   - Subscribe to: `messages`

### Step 5: Test!

Send a WhatsApp message to your business number:

```
Hi! I need 2x 9kg gas cylinders
delivered to 123 Main St, Fish Hoek
```

Check Django Admin → WhatsApp Conversations to see the AI processing!

## 📱 How It Works

```
Customer sends WhatsApp → AI understands request → Creates invoice & order → Assigns driver → Sends confirmation
```

## 🎯 What the AI Can Do

✅ **Understand orders** in natural language  
✅ **Extract** products, quantities, addresses  
✅ **Create** invoices automatically  
✅ **Assign** available drivers  
✅ **Escalate** unclear requests to humans  
✅ **Track** conversation history  

## 🔧 Common Issues

**Webhook not working?**
- Ensure URL is HTTPS
- Check verify token matches
- Test: `curl "https://yourdomain.com/api/whatsapp/webhook/?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=test"`

**AI not responding?**
- Verify API key is correct
- Check Django logs for errors
- Ensure "Is Active" is checked

**Orders not creating?**
- Check products exist and are active
- Verify client phone number format
- Review WhatsApp Order Intents in admin

## 📊 Monitor Performance

**Django Admin Sections:**
- **WhatsApp Conversations** - All customer chats
- **WhatsApp Messages** - Individual messages
- **WhatsApp Order Intents** - Extracted orders
- **WhatsApp Configuration** - Settings

**Filter conversations by:**
- Status (Active, Resolved, Escalated)
- Requires Human (Yes/No)
- Date range

## 💡 Tips

1. **Start with high confidence threshold (80)** - Reduces errors
2. **Monitor first week closely** - Adjust settings as needed
3. **Train staff on escalations** - Some requests need human touch
4. **Customize welcome message** - Match your brand voice
5. **Review AI responses** - Improve system prompt if needed

## 📖 Full Documentation

See `WHATSAPP_AI_AGENT_SETUP.md` for complete setup guide and troubleshooting.

## 🎉 You're Ready!

Your WhatsApp AI agent is now automating sales 24/7!
