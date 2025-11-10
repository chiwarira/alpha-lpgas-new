from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal

# Import contact submission model
from .models_contact import ContactSubmission

# Import testimonial model
from .models_testimonial import Testimonial


class HeroBanner(models.Model):
    """Hero banner for the website homepage"""
    title = models.CharField(max_length=255, default='Door to Door LPG Gas Delivery')
    subtitle = models.TextField(default='Fast, reliable gas delivery to your doorstep in Fish Hoek and surrounding areas. Order online and get same-day delivery!')
    background_image = models.ImageField(upload_to='banners/', blank=True, null=True, help_text='Hero section background image')
    
    # Overlay settings
    OVERLAY_CHOICES = [
        ('blue', 'Blue (Default)'),
        ('rose', 'Rose/Red'),
        ('green', 'Green'),
        ('purple', 'Purple'),
        ('gray', 'Gray'),
        ('black', 'Black'),
        ('none', 'No Overlay'),
    ]
    overlay_color = models.CharField(
        max_length=20, 
        choices=OVERLAY_CHOICES, 
        default='blue',
        help_text='Background overlay color (only applies if background image is set)'
    )
    overlay_opacity = models.IntegerField(
        default=85,
        help_text='Overlay opacity percentage (0-100). Higher = more opaque'
    )
    
    cta_text = models.CharField(max_length=100, default='Order Now', help_text='Call-to-action button text')
    cta_link = models.CharField(max_length=255, default='#order', help_text='Call-to-action button link')
    secondary_cta_text = models.CharField(max_length=100, default='View Products', blank=True, help_text='Secondary button text')
    secondary_cta_link = models.CharField(max_length=255, default='#products', blank=True, help_text='Secondary button link')
    is_active = models.BooleanField(default=True, help_text='Display this banner on the website')
    order = models.IntegerField(default=0, help_text='Display order (lower numbers first)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_overlay_rgba(self):
        """Get RGBA color for overlay based on selected color"""
        opacity = self.overlay_opacity / 100
        color_map = {
            'blue': f'rgba(37, 99, 235, {opacity})',
            'rose': f'rgba(225, 29, 72, {opacity})',
            'green': f'rgba(34, 197, 94, {opacity})',
            'purple': f'rgba(168, 85, 247, {opacity})',
            'gray': f'rgba(75, 85, 99, {opacity})',
            'black': f'rgba(0, 0, 0, {opacity})',
            'none': 'rgba(0, 0, 0, 0)',
        }
        return color_map.get(self.overlay_color, color_map['blue'])

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'Hero Banner'
        verbose_name_plural = 'Hero Banners'

    def __str__(self):
        return self.title


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


class Category(models.Model):
    """Product categories"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Display order")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """Unified product model for accounting & e-commerce"""
    
    # Basic Info
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    sku = models.CharField(max_length=100, unique=True, help_text="Stock Keeping Unit")
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=500, blank=True)
    
    # Pricing
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))], help_text="Selling price")
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Original price for showing discounts")
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))], blank=True, null=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=15.00, help_text="Tax/VAT rate in percentage")
    
    # E-commerce Features
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    main_image = models.ImageField(upload_to='products/', blank=True, null=True)
    image_2 = models.ImageField(upload_to='products/', blank=True, null=True)
    image_3 = models.ImageField(upload_to='products/', blank=True, null=True)
    image_4 = models.ImageField(upload_to='products/', blank=True, null=True)
    
    # Inventory Management
    track_inventory = models.BooleanField(default=False, help_text="Track stock levels")
    stock_quantity = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=10)
    
    # LPG Specific Fields
    weight = models.CharField(max_length=50, blank=True, help_text="e.g., 9kg, 14kg, 19kg")
    is_exchange = models.BooleanField(default=False, help_text="Is this an exchange product?")
    requires_empty_cylinder = models.BooleanField(default=False)
    
    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    
    # Status & Visibility
    is_active = models.BooleanField(default=True, help_text="Product is active")
    is_featured = models.BooleanField(default=False, help_text="Show on homepage")
    show_on_website = models.BooleanField(default=True, help_text="Display on e-commerce site")
    available_for_invoicing = models.BooleanField(default=True, help_text="Available for invoices/quotes")
    
    # Accounting
    unit = models.CharField(max_length=50, default='unit', help_text="Unit of measurement (e.g., piece, hour, kg, cylinder)")
    
    # Display Order
    order = models.IntegerField(default=0, help_text="Display order")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    def save(self, *args, **kwargs):
        # Auto-generate slug if not provided
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    @property
    def is_on_sale(self):
        """Check if product is on sale"""
        return self.compare_at_price and self.compare_at_price > self.unit_price
    
    @property
    def discount_percentage(self):
        """Calculate discount percentage"""
        if self.is_on_sale:
            return int(((self.compare_at_price - self.unit_price) / self.compare_at_price) * 100)
        return 0
    
    @property
    def is_low_stock(self):
        """Check if stock is low"""
        if self.track_inventory:
            return self.stock_quantity <= self.low_stock_threshold
        return False
    
    @property
    def is_out_of_stock(self):
        """Check if out of stock"""
        if self.track_inventory:
            return self.stock_quantity <= 0
        return False


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
    whatsapp_invoice_message = models.TextField(blank=True, help_text="Pre-populated WhatsApp message for sending invoice to client")
    whatsapp_sent = models.BooleanField(default=False, help_text="Whether invoice has been sent via WhatsApp")
    whatsapp_sent_at = models.DateTimeField(null=True, blank=True, help_text="When invoice was sent via WhatsApp")
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
            last_credit_note = CreditNote.objects.filter(
                credit_note_number__startswith=prefix
            ).order_by('credit_note_number').last()
            
            if last_credit_note:
                # Extract the sequence number and increment
                try:
                    last_seq = int(last_credit_note.credit_note_number.split('-')[-1])
                    new_seq = last_seq + 1
                except (ValueError, IndexError):
                    new_seq = 1
            else:
                new_seq = 1
            
            self.credit_note_number = f"{prefix}-{new_seq:03d}"
        
        # Set client from invoice if not set
        if self.invoice and not self.client_id:
            self.client = self.invoice.client
        
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculate subtotal, VAT, and total from line items (VAT-inclusive)"""
        items = self.items.all()
        self.total_amount = sum(item.total for item in items)
        self.tax_amount = sum(item.tax_amount for item in items)
        self.subtotal = self.total_amount - self.tax_amount
        self.save()


# E-commerce Models

class DeliveryZone(models.Model):
    """Delivery zones with pricing"""
    name = models.CharField(max_length=100, help_text="e.g., Fish Hoek, Kommetjie")
    postal_codes = models.TextField(help_text="Comma-separated postal codes")
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    minimum_order = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Minimum order amount for delivery")
    estimated_delivery_time = models.CharField(max_length=100, default="Same day", help_text="e.g., Same day, 2-3 hours")
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.name} - R{self.delivery_fee}"


class PromoCode(models.Model):
    """Promotional discount codes"""
    code = models.CharField(max_length=50, unique=True, help_text="Promo code (e.g., WELCOME10)")
    description = models.TextField(blank=True)
    
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Percentage or fixed amount")
    
    minimum_order = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Minimum order amount")
    max_uses = models.IntegerField(null=True, blank=True, help_text="Maximum number of uses (null = unlimited)")
    times_used = models.IntegerField(default=0)
    
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} - {self.discount_value}{'%' if self.discount_type == 'percentage' else ' ZAR'}"
    
    def is_valid(self):
        from django.utils import timezone
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.valid_from or now > self.valid_until:
            return False
        if self.max_uses and self.times_used >= self.max_uses:
            return False
        return True


class ProductVariant(models.Model):
    """Product variants (e.g., different sizes, types)"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=100, help_text="e.g., Full Cylinder, Exchange Only")
    sku = models.CharField(max_length=100, unique=True)
    price_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Price difference from base product")
    stock_quantity = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'name']
        unique_together = ['product', 'name']
    
    def __str__(self):
        return f"{self.product.name} - {self.name}"
    
    def get_price(self):
        return self.product.unit_price + self.price_adjustment


class Order(models.Model):
    """Customer orders"""
    order_number = models.CharField(max_length=50, unique=True, editable=False)
    
    # Customer Info
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=50)
    
    # Delivery Info
    delivery_address = models.TextField()
    delivery_zone = models.ForeignKey(DeliveryZone, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    delivery_notes = models.TextField(blank=True)
    
    # Order Details
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    promo_code = models.ForeignKey(PromoCode, on_delete=models.SET_NULL, null=True, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash on Delivery'),
        ('eft', 'EFT'),
        ('card', 'Card Payment'),
        ('yoco', 'Yoco Online Payment'),
    ]
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    payment_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ], default='pending')
    yoco_payment_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Order Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Tracking
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order {self.order_number} - {self.customer_name}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            from django.utils import timezone
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            self.order_number = f"ORD-{timestamp}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """Items in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name}"
    
    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    """Track order status changes"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Order Status Histories'
    
    def __str__(self):
        return f"{self.order.order_number} - {self.status}"


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
