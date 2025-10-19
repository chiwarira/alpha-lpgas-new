# Accounting System Features

## Overview
Complete accounting system with forms, PDF generation, and API endpoints for managing clients, products, quotes, invoices, payments, and credit notes.

## Features Implemented

### 1. Django Forms (`backend/core/forms.py`)

#### Client Management
- **ClientForm**: Create and edit clients
  - Fields: name, email, phone, address, city, postal code, VAT number, notes
  - Validation: Duplicate email detection
  - Bootstrap 5 styling

#### Product Management
- **ProductForm**: Create and edit products/services
  - Fields: name, description, SKU, unit, price, VAT rate, category
  - Validation: Duplicate SKU detection
  - Support for both products and services

#### Quote Management
- **QuoteForm**: Create and edit quotes
  - Fields: client, dates, status, terms, notes, discount
  - **QuoteItemFormSet**: Manage multiple line items
  - Automatic total calculations

#### Invoice Management
- **InvoiceForm**: Create and edit invoices
  - Fields: client, dates, status, terms, notes, discount
  - **InvoiceItemFormSet**: Manage multiple line items
  - Automatic total calculations
  - VAT calculations

#### Payment Management
- **PaymentForm**: Record payments against invoices
  - Fields: invoice, date, amount, method, reference, notes
  - Validation: Ensures payment doesn't exceed balance
  - Automatic balance updates

#### Credit Note Management
- **CreditNoteForm**: Create credit notes
  - Fields: invoice, date, reason, notes
  - **CreditNoteItemFormSet**: Manage multiple line items
  - Linked to original invoices

#### Company Settings
- **CompanySettingsForm**: Configure company details
  - Company information
  - Banking details
  - Logo upload

### 2. Form Views (`backend/core/views_forms.py`)

#### Dashboard
- **accounting_dashboard**: Overview with statistics
  - Total clients
  - Pending quotes
  - Unpaid invoices
  - Overdue invoices
  - Monthly revenue
  - Outstanding amounts
  - Recent activity

#### Client Views
- **client_list**: List all clients
- **client_create**: Create new client
- **client_edit**: Edit existing client
- **client_detail**: View client details with related quotes and invoices

#### Product Views
- **product_list**: List all products
- **product_create**: Create new product
- **product_edit**: Edit existing product

#### Quote Views
- **quote_list**: List all quotes
- **quote_create**: Create quote with line items (uses formsets)
- **quote_edit**: Edit quote and line items
- **quote_detail**: View quote details

#### Invoice Views
- **invoice_list**: List all invoices
- **invoice_create**: Create invoice with line items (uses formsets)
- **invoice_edit**: Edit invoice and line items
- **invoice_detail**: View invoice details with payments

#### Payment Views
- **payment_create**: Record payment for an invoice

#### Credit Note Views
- **credit_note_create**: Create credit note with line items
- **credit_note_detail**: View credit note details

### 3. PDF Generation (`backend/core/pdf_generator.py`)

#### Invoice PDF
- **generate_invoice_pdf**: Professional invoice PDF
  - Company logo and details
  - Client information
  - Line items table
  - VAT calculations
  - Totals with paid amount and balance
  - Terms and conditions
  - Banking details
  - Professional styling with ReportLab

#### Quote PDF
- **generate_quote_pdf**: Professional quote PDF
  - Company logo and details
  - Client information
  - Line items table
  - VAT calculations
  - Totals
  - Terms and conditions
  - Valid until date
  - Professional styling

#### Download Views
- **download_invoice_pdf**: Download invoice as PDF
- **download_quote_pdf**: Download quote as PDF

### 4. URL Patterns (`backend/core/urls/forms.py`)

All accounting features accessible via:
- **Dashboard**: `/accounting/`
- **Clients**: `/accounting/clients/`
- **Products**: `/accounting/products/`
- **Quotes**: `/accounting/quotes/`
- **Invoices**: `/accounting/invoices/`
- **Payments**: `/accounting/payments/`
- **Credit Notes**: `/accounting/credit-notes/`

PDF Downloads:
- **Invoice PDF**: `/accounting/invoices/<id>/pdf/`
- **Quote PDF**: `/accounting/quotes/<id>/pdf/`

## API Endpoints (Already Available)

All features also available via REST API:
- **GET/POST** `/api/accounting/clients/`
- **GET/PUT/DELETE** `/api/accounting/clients/<id>/`
- **GET/POST** `/api/accounting/products/`
- **GET/PUT/DELETE** `/api/accounting/products/<id>/`
- **GET/POST** `/api/accounting/quotes/`
- **GET/PUT/DELETE** `/api/accounting/quotes/<id>/`
- **GET/POST** `/api/accounting/invoices/`
- **GET/PUT/DELETE** `/api/accounting/invoices/<id>/`
- **GET/POST** `/api/accounting/payments/`
- **GET** `/api/accounting/settings/`

## Technical Details

### Form Features
- **Bootstrap 5 Styling**: All forms use Bootstrap classes
- **Validation**: Client-side and server-side validation
- **Formsets**: Dynamic line item management
- **AJAX Ready**: Forms can be submitted via AJAX
- **Error Handling**: Comprehensive error messages

### PDF Features
- **ReportLab**: Professional PDF generation
- **Company Branding**: Logo and company details
- **Professional Layout**: Clean, business-ready design
- **VAT Compliance**: Proper VAT calculations and display
- **Banking Details**: Included for easy payment

### Security
- **Login Required**: All views require authentication
- **Transaction Safety**: Database transactions for multi-model operations
- **Validation**: Comprehensive input validation
- **CSRF Protection**: Django CSRF tokens

## Usage Examples

### Creating an Invoice with Items

```python
# In view
if request.method == 'POST':
    form = InvoiceForm(request.POST)
    formset = InvoiceItemFormSet(request.POST)
    
    if form.is_valid() and formset.is_valid():
        invoice = form.save(commit=False)
        invoice.created_by = request.user
        invoice.save()
        
        formset.instance = invoice
        formset.save()
        
        invoice.calculate_totals()
```

### Generating PDF

```python
from core.pdf_generator import generate_invoice_pdf

pdf = generate_invoice_pdf(invoice)

response = HttpResponse(pdf, content_type='application/pdf')
response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
return response
```

### Recording Payment

```python
form = PaymentForm(request.POST)
if form.is_valid():
    payment = form.save()
    # Invoice balance automatically updated via model signals
```

## Next Steps

### Templates Needed
To complete the UI, create these templates in `backend/templates/core/`:
- `dashboard.html`
- `client_list.html`, `client_form.html`, `client_detail.html`
- `product_list.html`, `product_form.html`
- `quote_list.html`, `quote_form.html`, `quote_detail.html`
- `invoice_list.html`, `invoice_form.html`, `invoice_detail.html`
- `payment_form.html`
- `credit_note_form.html`, `credit_note_detail.html`

### Frontend React Components
Create React components to consume the API:
- Client management interface
- Product catalog
- Quote builder
- Invoice generator
- Payment recorder
- Dashboard with charts

### Additional Features
- Email invoices/quotes to clients
- Recurring invoices
- Invoice reminders
- Payment gateway integration (YOCO)
- Export to Excel
- Financial reports
- Tax reports

## Dependencies Added

```
reportlab==4.0.7  # PDF generation
openpyxl==3.1.5   # Excel exports (already included)
```

Install with:
```bash
pip install reportlab==4.0.7
```
