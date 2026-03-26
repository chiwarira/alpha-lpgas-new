# Tax Reporting Module - Quick Start Guide

## Installation & Setup

### Step 1: Run Migrations

```bash
cd backend
python manage.py migrate
```

This creates all the necessary database tables for tax reporting.

### Step 2: Set Up Chart of Accounts

```bash
python manage.py setup_chart_of_accounts
```

This creates 60+ pre-configured accounts for your LPG gas business.

### Step 3: Configure Tax Settings

1. Log in to Django Admin
2. Navigate to **Accounting → Tax Configuration**
3. Click "Add Tax Configuration"
4. Fill in:
   - **VAT vendor number** (from SARS)
   - **VAT registration date**
   - **SARS tax reference number**
   - **Company registration number**
   - **Financial year end** (month and day)
   - Accountant details (optional)
5. Save

## Quick Workflows

### Creating a VAT Return (Monthly)

1. **Navigate:** Accounting → Tax & Compliance → VAT Returns (VAT201)
2. **Click:** "Add VAT Return"
3. **Fill in:**
   - Period start date (e.g., 2024-01-01)
   - Period end date (e.g., 2024-01-31)
   - Filing period (e.g., 202401)
4. **Save**
5. **Select** the return and choose action: **"Calculate VAT from transactions"**
6. **Review** the calculated amounts
7. **Mark as submitted** when filed with SARS
8. **Mark as paid** when payment is made

### Creating a Tax Return (Annual)

1. **Navigate:** Accounting → Tax & Compliance → SARS Tax Returns (ITR14)
2. **Click:** "Add SARS Tax Return"
3. **Fill in:**
   - Tax year start/end dates
   - Assessment year
   - Tax reference number
   - Company registration
4. **Enter financial data:**
   - Gross income
   - Deductions (cost of sales, expenses, etc.)
   - Provisional tax paid
5. **Select** and choose action: **"Calculate tax from financial data"**
6. **Review** tax payable
7. **Upload** supporting documents
8. **Mark as submitted** when filed

### Generating Financial Statements

1. **Navigate:** Accounting → Financial Statements → Financial Statements
2. **Click:** "Add Financial Statement"
3. **Select:**
   - Statement type (Balance Sheet or Income Statement)
   - Period start/end dates
4. **Save**
5. **Select** and choose action:
   - **"Generate Balance Sheet"** or
   - **"Generate Income Statement"**
6. **Review** the generated data
7. **Mark as approved** when ready

### Creating CIPC Annual Return

1. **Navigate:** Accounting → Tax & Compliance → CIPC Annual Returns
2. **Click:** "Add CIPC Annual Return"
3. **Fill in:**
   - Financial year end
   - Filing year
   - Company details
   - Financial summary (from financial statements)
   - Directors information
4. **Upload** financial statements
5. **Mark as ready** for submission
6. **Submit** to CIPC

## Common Tasks

### Viewing Chart of Accounts

**Navigate:** Accounting → General Ledger → Chart of Accounts

Here you can:
- View all accounts
- Filter by category (Asset, Liability, Equity, Revenue, Expense)
- Add custom accounts
- Configure VAT settings per account

### Recording Journal Entries

**Navigate:** Accounting → General Ledger → Journal Entries

Standard double-entry bookkeeping:
- Debits must equal credits
- Link to invoices, expenses, or payments
- Post entries to update account balances

## Monthly Checklist

- [ ] Record all sales invoices
- [ ] Record all expenses
- [ ] Post journal entries
- [ ] Reconcile bank accounts
- [ ] Calculate depreciation
- [ ] Create VAT return
- [ ] Submit VAT return to SARS
- [ ] Pay VAT

## Quarterly Checklist

- [ ] Generate financial statements
- [ ] Review profit/loss
- [ ] Calculate provisional tax
- [ ] Pay provisional tax

## Annual Checklist

- [ ] Year-end stock take
- [ ] Fixed asset register update
- [ ] Generate annual financial statements
- [ ] Prepare SARS tax return (ITR14)
- [ ] Prepare CIPC annual return
- [ ] Submit to accountant/auditor
- [ ] File with SARS
- [ ] File with CIPC

## Tips

1. **Set up tax configuration first** - This ensures correct rates and settings
2. **Use the chart of accounts** - Proper categorization makes reporting easier
3. **Regular reconciliation** - Reconcile bank accounts monthly
4. **Keep documentation** - Upload receipts and supporting documents
5. **Review before submitting** - Always review calculated amounts
6. **Consult your accountant** - For complex transactions or year-end

## Navigation Quick Reference

```
Accounting Menu
├── General Ledger
│   ├── Chart of Accounts
│   └── Journal Entries
├── Tax & Compliance
│   ├── VAT Returns (VAT201)
│   ├── SARS Tax Returns (ITR14)
│   └── CIPC Annual Returns
├── Financial Statements
│   └── Financial Statements
└── Tax Configuration
```

## Support

For detailed information, see `TAX_REPORTING_MODULE.md`

## Troubleshooting

**Q: VAT calculation shows zero**
- Ensure invoices and expenses are in the correct date range
- Check that VAT amounts are properly recorded
- Verify invoice/expense status is 'paid' or 'sent'

**Q: Financial statements are empty**
- Run the chart of accounts setup command
- Ensure journal entries are posted (status = 'posted')
- Check that accounts are properly categorized

**Q: Can't find tax configuration**
- Only one configuration is allowed
- If it exists, edit the existing one
- If missing, create a new one

**Q: Account balances seem wrong**
- Verify all journal entries are posted
- Check debit/credit amounts are correct
- Ensure opening balances are recorded
