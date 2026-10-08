# Run Migration on Railway Production

## What changed

The latest code adds `Invoice.order`, `Order.client`, and `OrderItem.invoice_item` fields, plus auto-generated delivery orders for invoices.

Required migrations:

- `0041_invoice_order_order_client`
- `0042_orderitem_invoice_item`

After migrating, run the backfill command so existing invoices get their corresponding delivery orders:

```bash
python manage.py backfill_order_invoices
```

## Option 1: Using Railway CLI

1. **Install Railway CLI** (if not already installed):
```bash
npm install -g @railway/cli
```

2. **Login to Railway**:
```bash
railway login
```

3. **Link to your project**:
```bash
railway link
```

4. **Run the migration**:
```bash
railway run python manage.py migrate
```

5. **Backfill historical invoices**:
```bash
railway run python manage.py backfill_order_invoices
```

## Option 2: Using Railway Dashboard

1. Go to your Railway project dashboard
2. Click on your Django service
3. Go to the **"Settings"** tab
4. Scroll to **"Deploy"** section
5. Add a **one-off command**:
   ```
   python manage.py migrate && python manage.py backfill_order_invoices
   ```
6. Click **"Run"**

## Option 3: Add to Deployment Process

Update your Railway deployment to always run migrations and the invoice backfill:

1. In Railway dashboard, go to **Settings** → **Deploy**
2. Set **"Build Command"**:
   ```
   pip install -r requirements.txt
   ```
3. Set **"Start Command"**:
   ```
   python manage.py migrate && python manage.py backfill_order_invoices && gunicorn alphalpgas.wsgi:application
   ```

This will automatically run migrations and backfill on every deployment.

## Verify Migration

After running, check the migrations were applied:
```bash
railway run python manage.py showmigrations core
```

Look for:
```
[X] 0041_invoice_order_order_client
[X] 0042_orderitem_invoice_item
```

The `[X]` means it's been applied.

## Why the production API was returning 500

If you see `GET https://api.alphalpgas.co.za/accounting/ 500 (Internal Server Error)` after the code was deployed, it is almost certainly because the production database is missing the new `order`/`client`/`invoice_item` columns. Running `migrate` (and optionally the backfill) resolves it.
