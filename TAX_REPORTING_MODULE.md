# Tax Reporting & Financial Statements Module

## Overview

This module provides comprehensive tax reporting and financial statement automation for South African businesses, benchmarked against Sage Intacct. It handles:

- **VAT Returns (VAT201)** - Automated VAT calculation and SARS submission preparation
- **SARS Company Tax Returns (ITR14)** - Corporate income tax calculation and filing
- **CIPC Annual Returns (CoR14.3)** - Company registration compliance
- **Financial Statements** - Balance Sheet, Income Statement, Cash Flow Statement
- **Chart of Accounts** - Proper double-entry bookkeeping structure

## Features

### 1. Chart of Accounts

A comprehensive South African chart of accounts with proper categorization:

**Account Categories:**
- **Assets** (1000-1999): Current assets, fixed assets, intangible assets
- **Liabilities** (2000-2999): Current liabilities, long-term liabilities
- **Equity** (3000-3999): Share capital, retained earnings, drawings
- **Revenue** (4000-4999): Sales revenue, service revenue, other income
- **Expenses** (5000-5999): Cost of sales, operating expenses, administrative expenses, finance costs

**Setup:**
```bash
python manage.py setup_chart_of_accounts
```

This creates 60+ pre-configured accounts suitable for an LPG gas distribution business.

### 2. VAT Returns (VAT201)

**Features:**
- Automated VAT calculation from invoices and expenses
- Proper separation of output tax (sales) and input tax (purchases)
- Capital goods vs. other purchases classification
- Bad debts and imported services handling
- Status tracking: Draft → Calculated → Submitted → Paid

**Workflow:**
1. Create a new VAT Return for the period
2. Click "Calculate VAT from transactions" action
3. Review the calculated amounts (all VAT201 boxes)
4. Mark as submitted when filed with SARS
5. Mark as paid when payment is made

**VAT201 Boxes Covered:**
- Box 1-3: Output tax (standard rate and other rates)
- Box 4-6: Input tax (capital goods and other)
- Box 7-12: Net VAT calculation and final payable amount

**Access:** Accounting → Tax & Compliance → VAT Returns (VAT201)

### 3. SARS Tax Returns (ITR14)

**Features:**
- Corporate income tax calculation at 27% (configurable)
- Income and deductions tracking
- Assessed loss brought forward
- Provisional tax and credits management
- Status tracking: Draft → Calculated → Submitted → Assessed → Paid

**Workflow:**
1. Create a new tax return for the assessment year
2. Enter or auto-populate income and deductions
3. Click "Calculate tax from financial data" action
4. Review taxable income and tax payable
5. Upload supporting documents (financial statements, computations)
6. Mark as submitted when filed with SARS
7. Track assessment and payment

**Tax Calculation:**
- Gross income - Exempt income = Total income
- Total income - Total deductions = Taxable income
- Taxable income - Assessed loss = Taxable income after loss
- Tax = Taxable income after loss × 27%
- Tax payable = Tax - Credits (provisional tax, etc.)

**Access:** Accounting → Tax & Compliance → SARS Tax Returns (ITR14)

### 4. CIPC Annual Returns (CoR14.3)

**Features:**
- Annual return preparation for company registration compliance
- Financial summary from statements
- Directors and officers information
- Share capital details
- Auditor/accountant information
- Document attachment support

**Workflow:**
1. Create annual return for the financial year
2. Enter company details and financial summary
3. Add directors information (JSON format)
4. Upload financial statements and supporting documents
5. Mark as ready for submission
6. Submit to CIPC and track approval

**Access:** Accounting → Tax & Compliance → CIPC Annual Returns

### 5. Financial Statements

**Statement Types:**
- **Balance Sheet** - Statement of Financial Position
- **Income Statement** - Statement of Comprehensive Income
- **Cash Flow Statement** - Cash flow analysis
- **Statement of Changes in Equity**
- **Notes to Financial Statements**

**Features:**
- Automated generation from chart of accounts
- Comparative period support
- JSON data structure for flexibility
- PDF and Excel export capability
- Approval workflow: Draft → Generated → Reviewed → Approved → Published

**Workflow:**
1. Create a new financial statement
2. Select statement type and period
3. Click "Generate Balance Sheet" or "Generate Income Statement" action
4. Review the generated data
5. Approve and publish

**Balance Sheet Structure:**
```
ASSETS
  Current Assets
  Fixed Assets
  Intangible Assets
  Other Assets
  = Total Assets

LIABILITIES
  Current Liabilities
  Long-term Liabilities
  = Total Liabilities

EQUITY
  Share Capital
  Retained Earnings
  = Total Equity

Total Liabilities + Equity = Total Assets
```

**Income Statement Structure:**
```
REVENUE
  Sales Revenue
  Service Revenue
  Other Income
  = Total Revenue

EXPENSES
  Cost of Sales
  Operating Expenses
  Administrative Expenses
  Finance Costs
  = Total Expenses

Gross Profit = Revenue - Cost of Sales
Operating Profit = Revenue - Total Expenses
Net Profit = Operating Profit
```

**Access:** Accounting → Financial Statements → Financial Statements

### 6. Tax Configuration

Central configuration for all tax settings:

**VAT Settings:**
- VAT vendor number
- Registration date
- Filing frequency (monthly/bi-monthly)
- Standard VAT rate (15%)

**SARS Settings:**
- Tax reference number
- Company registration number
- Financial year end (month and day)
- Corporate tax rate (27%)
- Small business corporation flag

**CIPC Settings:**
- Company name
- Registration number

**Accountant/Auditor:**
- Name and practice number
- Contact details

**Access:** Accounting → Tax Configuration

## Navigation

The Accounting menu is organized into sections:

**General Ledger:**
- Chart of Accounts
- Journal Entries

**Tax & Compliance:**
- VAT Returns (VAT201)
- SARS Tax Returns (ITR14)
- CIPC Annual Returns

**Financial Statements:**
- Financial Statements

**Configuration:**
- Tax Configuration

## Integration with Existing System

The tax reporting module integrates seamlessly with existing features:

### From Invoices:
- Output VAT automatically calculated
- Revenue accounts credited
- Accounts receivable debited

### From Expenses:
- Input VAT automatically calculated
- Expense accounts debited
- Accounts payable credited

### From Journal Entries:
- Double-entry bookkeeping maintained
- Account balances updated
- Financial statements reflect all transactions

## Best Practices

### 1. Initial Setup

1. **Configure Tax Settings:**
   - Go to Tax Configuration
   - Enter VAT vendor number, SARS tax reference
   - Set financial year end
   - Configure tax rates

2. **Set Up Chart of Accounts:**
   ```bash
   python manage.py setup_chart_of_accounts
   ```
   - Review and customize accounts as needed
   - Add industry-specific accounts if required

3. **Create Opening Balances:**
   - Create journal entries for opening balances
   - Ensure debits = credits
   - Post the entries

### 2. Monthly Workflow

**Week 1-4: Transaction Recording**
- Record all sales (invoices)
- Record all purchases (expenses)
- Reconcile bank accounts
- Post journal entries

**Week 4: Month End**
- Review all transactions
- Calculate depreciation
- Make adjusting entries
- Close the period

**Week 5: VAT Return (if monthly filer)**
- Create VAT return for the period
- Calculate VAT automatically
- Review and adjust if needed
- Submit to SARS
- Record payment

### 3. Quarterly Workflow

- Generate financial statements
- Review profit/loss
- Calculate provisional tax
- Make tax payments

### 4. Annual Workflow

**Before Year End:**
- Stock take and adjustments
- Fixed asset register update
- Depreciation calculations
- Accruals and prepayments

**After Year End:**
- Generate annual financial statements
- Prepare SARS tax return (ITR14)
- Prepare CIPC annual return
- Submit to accountant/auditor
- File with SARS and CIPC

## Data Model

### AccountType
- Chart of accounts structure
- Account categorization
- VAT applicability
- Balance calculation methods

### VATReturn
- VAT201 form fields
- Automated calculation from transactions
- Submission tracking

### SARSTaxReturn
- ITR14 form fields
- Tax calculation logic
- Assessment tracking

### CIPCAnnualReturn
- CoR14.3 form fields
- Company information
- Financial summary

### FinancialStatement
- Statement generation
- JSON data storage
- Comparative periods
- File exports

### TaxConfiguration
- Centralized tax settings
- VAT and SARS configuration
- Accountant details

## Admin Actions

### VAT Returns
- **Calculate VAT** - Auto-calculate from transactions
- **Mark as Submitted** - Update submission status
- **Mark as Paid** - Record payment

### Tax Returns
- **Calculate Tax** - Auto-calculate tax liability
- **Mark as Submitted** - Update submission status
- **Mark as Assessed** - Record SARS assessment
- **Mark as Paid** - Record payment

### Financial Statements
- **Generate Balance Sheet** - Auto-generate from accounts
- **Generate Income Statement** - Auto-generate from accounts
- **Approve Statements** - Mark as approved

## Compliance Notes

### VAT (Value-Added Tax)
- Standard rate: 15%
- Filing frequency: Monthly or bi-monthly
- Payment deadline: 25th of following month
- Form: VAT201

### Company Tax
- Corporate tax rate: 27%
- Small business corporation: Graduated rates
- Assessment year: Based on financial year end
- Form: ITR14

### CIPC Annual Returns
- Due date: Within 30 business days of anniversary
- Required: Financial statements
- Form: CoR14.3

## Comparison with Sage Intacct

This module provides similar functionality to Sage Intacct:

| Feature | Sage Intacct | This Module |
|---------|--------------|-------------|
| Chart of Accounts | ✓ | ✓ |
| General Ledger | ✓ | ✓ |
| Financial Statements | ✓ | ✓ |
| Multi-period Reporting | ✓ | ✓ |
| Tax Management | ✓ | ✓ (SA-specific) |
| Automated Calculations | ✓ | ✓ |
| Compliance Reporting | ✓ | ✓ (VAT201, ITR14, CIPC) |
| Document Management | ✓ | ✓ |
| Approval Workflows | ✓ | ✓ |

**Key Advantages:**
- Specifically designed for South African tax compliance
- Integrated with existing LPG gas business operations
- No additional subscription costs
- Full customization capability

## Future Enhancements

Potential additions:
- PDF generation for financial statements
- Excel export for all reports
- Email submission to SARS/CIPC
- Bank reconciliation module
- Fixed asset register
- Payroll integration
- Multi-currency support
- Budgeting and forecasting
- Cash flow forecasting
- Audit trail enhancements

## Support

For issues or questions:
1. Check this documentation
2. Review the admin interface help text
3. Consult with your accountant
4. Contact system administrator

## Technical Notes

**Models:** `backend/core/models_tax_reporting.py`
**Admin:** `backend/core/admin.py` (Tax Reporting section)
**Management Commands:** `backend/core/management/commands/setup_chart_of_accounts.py`
**Templates:** Navigation updated in `base.html` and `dashboard.html`

**Database Tables:**
- `core_accounttype` - Chart of accounts
- `core_vatreturn` - VAT returns
- `core_sarstaxreturn` - Tax returns
- `core_cipcannualreturn` - CIPC returns
- `core_financialstatement` - Financial statements
- `core_taxconfiguration` - Tax settings
