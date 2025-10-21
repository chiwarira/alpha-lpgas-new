from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class CompanySettings(models.Model):
    """Singleton model for company and banking details"""
    # Company Information
    company_name = models.CharField(max_length=255, default='Alpha LPGas')
    registration_number = models.CharField(max_length=100, default='2023/822513/07', help_text='Company Registration Number')
    vat_number = models.CharField(max_length=100, default='9415233222', help_text='VAT Registration Number')
    phone = models.CharField(max_length=50, default='074 454 5665')
    email = models.EmailField(default='info@alphalpgas.co.za')
    address = models.TextField(blank=True, help_text='Company physical address')
    
    # Banking Details
    bank_name = models.CharField(max_length=100, default='Nedbank')
    account_name = models.CharField(max_length=255, default='Alpha LPGas')
    account_number = models.CharField(max_length=50, default='1101466707')
    account_type = models.CharField(max_length=50, default='Current')
    branch_code = models.CharField(max_length=20, default='125009')
    payment_reference_note = models.CharField(max_length=255, default='Please use your address as reference', blank=True)
    
    # Statement Settings
    statement_footer_text = models.TextField(
        default='Make all EFTs payable to Alpha LPGas\n\nThank you for your business!\n\nShould you have any enquiries concerning this statement, please contact Grace on 074 454 5665',
        blank=True,
        help_text='Footer text displayed at the bottom of client statements'
    )
    
    # WhatsApp Message Templates
    whatsapp_invoice_message = models.TextField(
        default='Hi {client_name}, Thank you for your support and partnership with {company_name}. Please find attached the invoice #{invoice_number}, Total: R{total_amount}, for your reference. To ensure accurate allocation of your payment, please use your address as the payment reference. Should you have any questions or require further assistance, please do not hesitate to contact us. Best regards, {company_name} Team Website: www.alphalpgas.co.za Facebook: www.facebook.com/alphalpgas',
        blank=True,
        help_text='WhatsApp message template for invoices. Available variables: {client_name}, {company_name}, {invoice_number}, {total_amount}'
    )
    whatsapp_quote_message = models.TextField(
        default='Hi {client_name}, Thank you for your interest in {company_name}. Please find attached the quotation #{quote_number}, Total: R{total_amount}, for your reference. This quote is valid until {expiry_date}. Should you have any questions or require further assistance, please do not hesitate to contact us. Best regards, {company_name} Team Website: www.alphalpgas.co.za Facebook: www.facebook.com/alphalpgas',
        blank=True,
        help_text='WhatsApp message template for quotes. Available variables: {client_name}, {company_name}, {quote_number}, {total_amount}, {expiry_date}'
    )
    whatsapp_statement_message = models.TextField(
        default='Hi {client_name}, Please find attached your account statement for the period {start_date} to {end_date}. Current balance: R{total_balance}. Should you have any questions regarding your statement, please do not hesitate to contact us. Best regards, {company_name} Team Website: www.alphalpgas.co.za Facebook: www.facebook.com/alphalpgas',
        blank=True,
        help_text='WhatsApp message template for statements. Available variables: {client_name}, {company_name}, {start_date}, {end_date}, {total_balance}'
    )
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Company Settings'
        verbose_name_plural = 'Company Settings'
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists (singleton pattern)
        self.pk = 1
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Prevent deletion
        pass
    
    @classmethod
    def load(cls):
        """Load the singleton instance"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
    
    def __str__(self):
        return f"{self.company_name} Settings"


class Client(models.Model):
    """Model for managing clients/customers"""
    customer_id = models.CharField(max_length=100, blank=True, help_text="Auto-generated from name and phone")
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    tax_id = models.CharField(max_length=50, blank=True, help_text="Tax ID or VAT number")
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='clients_created')

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Auto-generate customer_id from first name and phone number
        if not self.customer_id:
            # Extract first name (first word)
            first_name = self.name.split()[0] if self.name else 'Customer'
            # Clean phone number (remove spaces, dashes, parentheses)
            clean_phone = ''.join(filter(str.isdigit, self.phone)) if self.phone else '000'
            # Create customer_id
            self.customer_id = f"{first_name}_{clean_phone}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    """Model for managing products/services"""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sku = models.CharField(max_length=100, unique=True, help_text="Stock Keeping Unit")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))], blank=True, null=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Tax rate in percentage")
    unit = models.CharField(max_length=50, default='unit', help_text="Unit of measurement (e.g., piece, hour, kg)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sku})"


class Quote(models.Model):
    """Model for managing quotes/estimates"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]

    quote_number = models.CharField(max_length=50, unique=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='quotes')
    issue_date = models.DateField()
    expiry_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    terms = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='quotes_created')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Quote {self.quote_number} - {self.client.name}"

    def save(self, *args, **kwargs):
        """Override save to auto-generate quote number"""
        if not self.quote_number:
            # Generate quote number: QT-YYYYMMDD-XXX
            from datetime import date
            today = date.today()
            prefix = f"QT-{today.strftime('%Y%m%d')}"
            
            # Get the last quote number for today
            last_quote = Quote.objects.filter(
                quote_number__startswith=prefix
            ).order_by('quote_number').last()
            
            if last_quote:
                # Extract the sequence number and increment
                try:
                    last_seq = int(last_quote.quote_number.split('-')[-1])
                    new_seq = last_seq + 1
                except (ValueError, IndexError):
                    new_seq = 1
            else:
                new_seq = 1
            
            self.quote_number = f"{prefix}-{new_seq:03d}"
        
        super().save(*args, **kwargs)

    def calculate_totals(self):
        """Calculate subtotal, VAT, and total from line items (VAT-inclusive)"""
        items = self.items.all()
        self.total_amount = sum(item.total for item in items)
        self.tax_amount = sum(item.tax_amount for item in items)
        self.subtotal = self.total_amount - self.tax_amount
        self.save()


class QuoteItem(models.Model):
    """Line items for quotes"""
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    description = models.TextField(blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        # Calculate total and VAT (VAT is included in unit price)
        self.total = self.quantity * self.unit_price
        # Extract VAT from the total (VAT-inclusive calculation)
        self.tax_amount = self.total - (self.total / (1 + self.tax_rate / 100))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class Invoice(models.Model):
    """Model for managing invoices"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('partially_paid', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    invoice_number = models.CharField(max_length=50, unique=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoices')
    quote = models.ForeignKey(Quote, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    issue_date = models.DateField()
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    terms = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='invoices_created')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.client.name}"

    def save(self, *args, **kwargs):
        """Override save to auto-generate invoice number and calculate balance"""
        if not self.invoice_number:
            # Generate invoice number: INV-YYYYMMDD-XXX
            from datetime import date
            today = date.today()
            prefix = f"INV-{today.strftime('%Y%m%d')}"
            
            # Get the last invoice number for today
            last_invoice = Invoice.objects.filter(
                invoice_number__startswith=prefix
            ).order_by('invoice_number').last()
            
            if last_invoice:
                # Extract the sequence number and increment
                try:
                    last_seq = int(last_invoice.invoice_number.split('-')[-1])
                    new_seq = last_seq + 1
                except (ValueError, IndexError):
                    new_seq = 1
            else:
                new_seq = 1
            
            self.invoice_number = f"{prefix}-{new_seq:03d}"
        
        self.balance = self.total_amount - self.paid_amount
        super().save(*args, **kwargs)

    def calculate_totals(self):
        """Calculate subtotal, VAT, and total from line items (VAT-inclusive)"""
        items = self.items.all()
        self.total_amount = sum(item.total for item in items)
        self.tax_amount = sum(item.tax_amount for item in items)
        self.subtotal = self.total_amount - self.tax_amount
        self.balance = self.total_amount - self.paid_amount
        
        # Update status based on payment
        if self.paid_amount >= self.total_amount:
            self.status = 'paid'
        elif self.paid_amount > 0:
            self.status = 'partially_paid'
        
        self.save()


class InvoiceItem(models.Model):
    """Line items for invoices"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    description = models.TextField(blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        # Calculate total and VAT (VAT is included in unit price)
        self.total = self.quantity * self.unit_price
        # Extract VAT from the total (VAT-inclusive calculation)
        self.tax_amount = self.total - (self.total / (1 + self.tax_rate / 100))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class Payment(models.Model):
    """Model for managing payments"""
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('eft', 'EFT'),
    ]

    payment_number = models.CharField(max_length=50, unique=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    reference_number = models.CharField(max_length=100, blank=True, help_text="Check number, transaction ID, etc.")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='payments_created')

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"Payment {self.payment_number} - {self.amount}"

    def save(self, *args, **kwargs):
        """Override save to auto-generate payment number"""
        if not self.payment_number:
            # Generate payment number: PAY-YYYYMMDD-XXX
            from datetime import date
            today = date.today()
            prefix = f"PAY-{today.strftime('%Y%m%d')}"
            
            # Get the last payment number for today
            last_payment = Payment.objects.filter(
                payment_number__startswith=prefix
            ).order_by('payment_number').last()
            
            if last_payment:
                # Extract the sequence number and increment
                try:
                    last_seq = int(last_payment.payment_number.split('-')[-1])
                    new_seq = last_seq + 1
                except (ValueError, IndexError):
                    new_seq = 1
            else:
                new_seq = 1
            
            self.payment_number = f"{prefix}-{new_seq:03d}"
        
        super().save(*args, **kwargs)
        # Update invoice paid amount and status
        self.invoice.paid_amount = sum(p.amount for p in self.invoice.payments.all())
        self.invoice.calculate_totals()


class CreditNote(models.Model):
    """Model for managing credit notes"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('applied', 'Applied'),
        ('cancelled', 'Cancelled'),
    ]

    credit_note_number = models.CharField(max_length=50, unique=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='credit_notes')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='credit_notes')
    issue_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reason = models.TextField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='credit_notes_created')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Credit Note {self.credit_note_number} - {self.client.name}"

    def save(self, *args, **kwargs):
        """Override save to auto-generate credit note number"""
        if not self.credit_note_number:
            # Generate credit note number: CN-YYYYMMDD-XXX
            from datetime import date
            today = date.today()
            prefix = f"CN-{today.strftime('%Y%m%d')}"
            
            # Get the last credit note number for today
            last_cn = CreditNote.objects.filter(
                credit_note_number__startswith=prefix
            ).order_by('credit_note_number').last()
            
            if last_cn:
                # Extract the sequence number and increment
                try:
                    last_seq = int(last_cn.credit_note_number.split('-')[-1])
                    new_seq = last_seq + 1
                except (ValueError, IndexError):
                    new_seq = 1
            else:
                new_seq = 1
            
            self.credit_note_number = f"{prefix}-{new_seq:03d}"
        
        super().save(*args, **kwargs)

    def calculate_totals(self):
        """Calculate subtotal, VAT, and total from line items (VAT-inclusive)"""
        items = self.items.all()
        self.total_amount = sum(item.total for item in items)
        self.tax_amount = sum(item.tax_amount for item in items)
        self.subtotal = self.total_amount - self.tax_amount
        self.save()


class CreditNoteItem(models.Model):
    """Line items for credit notes"""
    credit_note = models.ForeignKey(CreditNote, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    description = models.TextField(blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        # Calculate total and VAT (VAT is included in unit price)
        self.total = self.quantity * self.unit_price
        # Extract VAT from the total (VAT-inclusive calculation)
        self.tax_amount = self.total - (self.total / (1 + self.tax_rate / 100))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
