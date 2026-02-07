# Invoice Numbering System Migration Guide

## Overview
This guide covers migrating from date-based invoice numbering (`INV-YYYYMMDD-XXX`) to sequential numbering (`INV-XXXXXX`) to align with the GitHub repository system.

**Latest invoice from old system:** `INV-004240`  
**New system starts at:** `INV-004241`

---

## Changes Made

### 1. Invoice Model Update (`backend/core/models.py`)
- Changed from date-based format: `INV-20260207-001`
- To sequential format: `INV-004241`, `INV-004242`, etc.
- Auto-increments from the highest existing invoice number
- Maintains backward compatibility with existing invoices

### 2. Management Command Created
- File: `backend/core/management/commands/update_invoice_numbers.py`
- Converts existing date-based invoices to sequential format
- Supports dry-run mode for testing
- Configurable starting number

---

## Deployment Instructions

### LOCAL Environment (Current)

#### Step 1: Test with Dry Run
```bash
cd backend
python manage.py update_invoice_numbers --dry-run
```

**Expected Output:**
```
Found 18 invoices with date-based format
DRY RUN - No changes will be made
Would update: INV-20260207-001 -> INV-004254
...
Next invoice number would be: INV-004259
```

#### Step 2: Execute Migration
```bash
python manage.py update_invoice_numbers
```

#### Step 3: Test New Invoice Creation
```bash
# Create a test invoice through the UI or shell
python manage.py shell -c "from core.models import Invoice; print('Next invoice will be:', Invoice.objects.order_by('-invoice_number').first().invoice_number if Invoice.objects.exists() else 'INV-004241')"
```

#### Step 4: Verify
- Create a new invoice via UI at `/accounting/invoices/create/`
- Confirm it gets number `INV-004259` (or next sequential)

---

### DEV Environment

#### Prerequisites
- Backup database before migration
- Ensure no active invoice creation during migration

#### Step 1: Deploy Code
```bash
# Pull latest code
git pull origin main

# Install dependencies (if any new)
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput
```

#### Step 2: Run Dry-Run Test
```bash
python manage.py update_invoice_numbers --dry-run
```

#### Step 3: Execute Migration
```bash
python manage.py update_invoice_numbers
```

#### Step 4: Restart Application
```bash
# Restart your Django application server
# Example for gunicorn:
sudo systemctl restart gunicorn
# Or for development server:
# Kill and restart: python manage.py runserver
```

#### Step 5: Verify
- Check invoice list page
- Create a test invoice
- Confirm sequential numbering works

---

### PRODUCTION Environment

#### Prerequisites
- **CRITICAL:** Backup database before migration
- Schedule maintenance window (5-10 minutes)
- Notify users of brief downtime
- Have rollback plan ready

#### Step 1: Database Backup
```bash
# PostgreSQL example
pg_dump -U your_user -d your_database > backup_$(date +%Y%m%d_%H%M%S).sql

# Or use your hosting provider's backup tool
```

#### Step 2: Deploy Code
```bash
# Pull latest code
git pull origin main

# Activate virtual environment
source venv/bin/activate  # or your venv path

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput
```

#### Step 3: Run Migration (Dry-Run First)
```bash
# Test first
python manage.py update_invoice_numbers --dry-run

# Review output carefully
# Verify the starting number and count match expectations
```

#### Step 4: Execute Migration
```bash
# Run actual migration
python manage.py update_invoice_numbers

# Expected output:
# Successfully updated X invoices
# Next invoice number will be: INV-XXXXXX
```

#### Step 5: Restart Application
```bash
# For gunicorn
sudo systemctl restart gunicorn

# For supervisor
sudo supervisorctl restart your_app

# For systemd service
sudo systemctl restart your-django-app
```

#### Step 6: Verify Production
1. Check invoice list page loads correctly
2. Verify existing invoices display with new numbers
3. Create a test invoice
4. Confirm sequential numbering (should be next in sequence)
5. Test invoice PDF generation
6. Test invoice sending via WhatsApp
7. Verify loyalty card stamping still works

---

## Rollback Plan

If issues occur, rollback using database backup:

```bash
# Stop application
sudo systemctl stop gunicorn

# Restore database
psql -U your_user -d your_database < backup_YYYYMMDD_HHMMSS.sql

# Revert code changes
git checkout HEAD~1 backend/core/models.py
git checkout HEAD~1 backend/core/management/commands/update_invoice_numbers.py

# Restart application
sudo systemctl start gunicorn
```

---

## Testing Checklist

### After Migration
- [ ] Invoice list page loads correctly
- [ ] Existing invoices show new sequential numbers
- [ ] Can view invoice detail pages
- [ ] Can create new invoice with sequential number
- [ ] Invoice PDF generates correctly
- [ ] Invoice WhatsApp sending works
- [ ] Loyalty card stamping works on new invoices
- [ ] Payment recording works
- [ ] Invoice editing works
- [ ] Invoice search/filter works

---

## Important Notes

1. **Starting Number:** The migration starts at `INV-004241` to continue from the old system's `INV-004240`

2. **Existing Invoices:** All existing date-based invoices will be converted to sequential format in chronological order

3. **No Duplicates:** The system checks for existing invoice numbers and auto-increments

4. **Thread Safety:** The migration uses Django's transaction.atomic() for data integrity

5. **Related Records:** Invoice numbers in related tables (payments, loyalty transactions) are automatically updated via foreign key relationships

---

## Troubleshooting

### Issue: Migration shows 0 invoices
**Solution:** System already using sequential format, no action needed

### Issue: Duplicate invoice numbers
**Solution:** Run migration again with higher --start-number:
```bash
python manage.py update_invoice_numbers --start-number 5000
```

### Issue: New invoices still using date format
**Solution:** 
1. Verify code changes deployed
2. Restart application server
3. Clear any application cache

### Issue: Invoice number gaps
**Solution:** This is normal if invoices were deleted. Sequential numbering continues from highest existing number.

---

## Support

If you encounter issues:
1. Check application logs
2. Verify database backup is available
3. Test in dev environment first
4. Contact development team before production deployment

---

## Migration Status

- [x] Local environment - Ready to migrate
- [ ] Dev environment - Pending
- [ ] Production environment - Pending

**Last Updated:** 2026-02-07
