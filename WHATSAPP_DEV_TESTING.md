# WhatsApp AI Agent - Testing on Railway Dev/Staging

## ✅ Better Approach - Test on Railway Dev Environment

Testing on Railway dev/staging is better because:
- ✅ **Stable URL** - No need to update webhook on every restart
- ✅ **Real environment** - Same setup as production
- ✅ **No ngrok needed** - Direct HTTPS access
- ✅ **Shared testing** - Team can test together
- ✅ **Separate database** - Won't affect production data

---

## Setup Steps

### Step 1: Add Environment Variables to Railway Dev

1. Go to https://railway.app
2. Select **Alpha LPGas** project
3. Select **dev/staging** environment (top dropdown)
4. Click **backend** service
5. Go to **"Variables"** tab
6. Add these variables:

```bash
# WhatsApp Configuration
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id_from_meta
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id
WHATSAPP_ACCESS_TOKEN=your_permanent_access_token
WHATSAPP_VERIFY_TOKEN=dev_verify_token_secure_123
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

7. Click **"Deploy"** to restart with new variables

### Step 2: Configure WhatsApp Webhook

1. Go to https://developers.facebook.com/
2. Open your WhatsApp Business API app
3. Go to **WhatsApp** → **Configuration**
4. Click **"Edit"** next to Webhook
5. Enter:
   - **Callback URL**: `https://alpha-lpgas-backend-dev.up.railway.app/api/whatsapp/webhook/`
   - **Verify Token**: `dev_verify_token_secure_123` (same as in Railway variables)
6. Click **"Verify and Save"**

**Expected:** Green checkmark = Webhook verified successfully

7. Subscribe to webhook fields:
   - ✅ `messages`
   - ✅ `message_status` (optional)

### Step 3: Test the Integration

#### Send Test Message

Send a WhatsApp message to your business number:

```
Hi, I'd like to order 2x 9kg gas cylinders for delivery to 123 Main Street, Johannesburg
```

#### Monitor Railway Logs

**Option 1: Railway Dashboard**
1. Go to Railway dashboard
2. Select **backend** service in dev environment
3. Click **"Deployments"** tab
4. Click on latest deployment
5. View logs in real-time

**Option 2: Railway CLI**
```bash
railway link
# Select: dev/staging environment
railway logs --service backend
```

You should see:
```
INFO: Received WhatsApp webhook
INFO: Processing message from +27...
INFO: AI extracted order: 2x 9kg cylinders
INFO: Creating invoice for client...
INFO: Invoice INV-XXXXX created
INFO: Assigning driver...
```

#### Check the Database

1. Go to your dev frontend: `https://alpha-lpgas-frontend-dev.up.railway.app/`
2. Login to admin
3. Check:
   - **Invoices** - New invoice should be created
   - **WhatsApp Messages** - Message logged
   - **Orders** - Order created with driver assigned

---

## Testing Checklist

### Basic Webhook Test
- [ ] Webhook verified in Meta dashboard (green checkmark)
- [ ] Send simple message: "Hello"
- [ ] Check Railway logs show webhook received
- [ ] Check WhatsApp message saved in database

### Order Processing Test
- [ ] Send order message with product and address
- [ ] AI extracts order details correctly
- [ ] Invoice created automatically
- [ ] Client matched or created
- [ ] Products added to invoice
- [ ] Delivery address captured

### Driver Assignment Test
- [ ] Order assigned to available driver
- [ ] Driver receives notification (if configured)
- [ ] Order status updated

### Error Handling Test
- [ ] Send unclear message
- [ ] AI requests clarification
- [ ] Human escalation triggered if needed

---

## Debugging on Railway Dev

### View Logs
```bash
railway logs --service backend --environment dev/staging
```

### Check Environment Variables
```bash
railway variables --service backend --environment dev/staging
```

### Access Django Shell
```bash
railway run --service backend --environment dev/staging python manage.py shell
```

### Check Database
```bash
railway run --service backend --environment dev/staging python manage.py dbshell
```

---

## Common Issues

### 1. Webhook Verification Fails

**Symptoms:**
- Red X in Meta dashboard
- Error: "Webhook verification failed"

**Solutions:**
- Check `WHATSAPP_VERIFY_TOKEN` is set in Railway variables
- Ensure token matches exactly in Meta and Railway
- Check Railway deployment is running
- Test webhook URL is accessible: `https://alpha-lpgas-backend-dev.up.railway.app/api/whatsapp/webhook/`

### 2. Messages Not Received

**Check:**
1. Railway logs for incoming requests
2. Webhook subscriptions include `messages`
3. Phone number is correct in Meta dashboard
4. Access token is valid (not expired)

### 3. AI Not Processing

**Check:**
1. `AI_PROVIDER` is set (`openai` or `anthropic`)
2. API key is valid and has credits
3. Model name is correct
4. Railway logs for AI API errors

### 4. Invoice Not Created

**Check:**
1. Products exist in database
2. Client matching logic works
3. Railway logs for errors
4. Database permissions

---

## Environment Comparison

| Feature | Local (ngrok) | Dev (Railway) | Production (Railway) |
|---------|---------------|---------------|----------------------|
| **URL Stability** | ❌ Changes on restart | ✅ Stable | ✅ Stable |
| **HTTPS** | ✅ Via ngrok | ✅ Native | ✅ Native |
| **Database** | SQLite | PostgreSQL | PostgreSQL |
| **Logs** | Terminal | Railway UI | Railway UI |
| **Team Access** | ❌ Only you | ✅ Shared | ✅ Shared |
| **Cost** | Free | Free | Paid |
| **Best For** | Quick debugging | Feature testing | Real customers |

---

## Testing Workflow

```
Customer Phone → WhatsApp → Meta API → Railway Dev → AI → Dev Database
                                                      ↓
                                                  Dev Frontend
```

---

## Sample Test Messages

### Simple Order
```
Hi, I need 1x 19kg gas cylinder delivered to 45 Oak Street, Sandton
```

### Multiple Products
```
Please deliver:
- 2x 9kg cylinders
- 1x 19kg cylinder
Address: 123 Main Road, Johannesburg
```

### Exchange Order
```
I want to exchange my empty 9kg cylinder for a full one
Delivery to 78 Park Lane, Pretoria
```

### Unclear Message (Test AI Clarification)
```
I need gas
```

Expected AI response: "I'd be happy to help! Could you please specify: 1) How many cylinders? 2) What size (9kg, 19kg, 48kg)? 3) Delivery address?"

---

## Monitoring Tips

### 1. Keep Logs Open
```bash
railway logs --service backend --environment dev/staging --follow
```

### 2. Check WhatsApp Conversation Table
```sql
SELECT * FROM core_whatsappconversation 
ORDER BY created_at DESC 
LIMIT 10;
```

### 3. Check Recent Invoices
```sql
SELECT invoice_number, client_id, total_amount, created_at 
FROM core_invoice 
ORDER BY created_at DESC 
LIMIT 10;
```

### 4. Monitor AI Costs
- Check OpenAI usage: https://platform.openai.com/usage
- Check Anthropic usage: https://console.anthropic.com/settings/billing

---

## Next Steps After Successful Testing

1. **Test all scenarios** - Orders, exchanges, unclear messages
2. **Verify driver assignment** works correctly
3. **Check invoice calculations** are accurate
4. **Test error handling** and escalation
5. **Move to production** when confident

---

## Production Deployment

Once dev testing is successful:

1. Add same environment variables to **production** environment
2. Update webhook URL to: `https://api.alphalpgas.co.za/api/whatsapp/webhook/`
3. Test with a few real orders
4. Monitor closely for first few days
5. Adjust AI prompts based on real usage

---

## Support

**Railway Logs:**
```bash
railway logs --service backend --environment dev/staging --follow
```

**Check Webhook Status:**
https://developers.facebook.com/apps/YOUR_APP_ID/whatsapp-business/wa-settings/

**Test Webhook Manually:**
```bash
curl -X POST https://alpha-lpgas-backend-dev.up.railway.app/api/whatsapp/webhook/ \
  -H "Content-Type: application/json" \
  -d '{"test": "webhook"}'
```

---

**Ready to start testing on Railway dev? Let me know when you've added the environment variables!**
