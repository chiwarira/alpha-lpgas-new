# Run Migration in Production

## What changed

The latest code adds `Invoice.order`, `Order.client`, and `OrderItem.invoice_item` fields, plus auto-generated delivery orders for invoices.

Required migrations:

- `0041_invoice_order_order_client`
- `0042_orderitem_invoice_item`

After migrating, run the backfill command so existing invoices get their corresponding delivery orders:

```bash
python manage.py backfill_order_invoices
```

## Option 1: Vercel CLI (recommended)

Assumes the backend is deployed on Vercel and the production `DATABASE_URL` is available.

1. **Install Vercel CLI**:
```bash
npm install -g vercel
```

2. **Login**:
```bash
vercel login
```

3. **Link your project**:
```bash
vercel link
```

4. **Pull environment variables**:
```bash
vercel env pull .env.production
```

5. **Run migrations**:
```bash
vercel --prod
# Or run a one-off command against the production DB with the pulled env:
DATABASE_URL="<production_database_url>" python manage.py migrate
DATABASE_URL="<production_database_url>" python manage.py backfill_order_invoices
```

## Option 2: Local shell with production `DATABASE_URL`

If you have direct access to the production database URL:

```bash
export DATABASE_URL="postgresql://..."
python manage.py migrate
python manage.py backfill_order_invoices
```

## Verify Migration

After running, check the migrations were applied:
```bash
python manage.py showmigrations core
```

Look for:
```
[X] 0041_invoice_order_order_client
[X] 0042_orderitem_invoice_item
```

The `[X]` means it's been applied.

## Why the production API was returning 500

If you see `GET https://api.alphalpgas.co.za/accounting/ 500 (Internal Server Error)` after the code was deployed, it is almost certainly because the production database is missing the new `order`/`client`/`invoice_item` columns. Running `migrate` (and optionally the backfill) resolves it.
