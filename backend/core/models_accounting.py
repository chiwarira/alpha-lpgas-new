"""
Accounting models for journal entries, expenses, and tax reporting.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class Supplier(models.Model):
    """Supplier/Vendor for tracking purchases and expenses"""
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    tax_number = models.CharField(max_length=50, blank=True, help_text="VAT/Tax registration number")
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    bank_branch_code = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Supplier'
        verbose_name_plural = 'Suppliers'

    def __str__(self):
        return self.name


class ExpenseCategory(models.Model):
    """Categories for expenses (for tax reporting)"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    tax_deductible = models.BooleanField(default=True, help_text="Is this expense tax deductible?")
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subcategories')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Expense Category'
        verbose_name_plural = 'Expense Categories'

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class Expense(models.Model):
    """Expense/Purchase records for tracking business expenses"""
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('eft', 'EFT/Bank Transfer'),
        ('petty_cash', 'Petty Cash'),
    ]

    expense_number = models.CharField(max_length=50, unique=True, blank=True)
    date = models.DateField()
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, related_name='expenses')
    description = models.TextField()
    
    # Amounts (VAT inclusive)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=15.00, help_text="VAT rate percentage")
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    
    # Payment details
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True, help_text="Reference number, cheque number, etc.")
    
    # Receipt/Invoice details
    invoice_number = models.CharField(max_length=100, blank=True, help_text="Supplier invoice/receipt number")
    receipt_image = models.ImageField(upload_to='expenses/receipts/%Y/%m/', blank=True, null=True)
    
    # Tax related
    is_tax_deductible = models.BooleanField(default=True)
    tax_period = models.CharField(max_length=20, blank=True, help_text="e.g., 2024-Q1, 2024-02")
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='expenses_created')

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Expense'
        verbose_name_plural = 'Expenses'

    def __str__(self):
        return f"{self.expense_number} - {self.description[:50]}"

    def save(self, *args, **kwargs):
        # Auto-generate expense number
        if not self.expense_number:
            from datetime import date
            today = date.today()
            prefix = f"EXP-{today.strftime('%Y%m%d')}"
            
            last_expense = Expense.objects.filter(
                expense_number__startswith=prefix
            ).order_by('expense_number').last()
            
            if last_expense:
                try:
                    last_seq = int(last_expense.expense_number.split('-')[-1])
                    new_seq = last_seq + 1
                except (ValueError, IndexError):
                    new_seq = 1
            else:
                new_seq = 1
            
            self.expense_number = f"{prefix}-{new_seq:03d}"
        
        # Calculate VAT from total (VAT inclusive)
        if self.total_amount and self.vat_rate:
            self.vat_amount = self.total_amount - (self.total_amount / (1 + self.vat_rate / 100))
            self.subtotal = self.total_amount - self.vat_amount
        
        # Set tax deductibility from category
        if self.category:
            self.is_tax_deductible = self.category.tax_deductible
        
        super().save(*args, **kwargs)


class JournalEntry(models.Model):
    """General journal entries for double-entry bookkeeping"""
    ENTRY_TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('transfer', 'Transfer'),
        ('adjustment', 'Adjustment'),
        ('opening', 'Opening Balance'),
        ('closing', 'Closing Entry'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('void', 'Void'),
    ]

    entry_number = models.CharField(max_length=50, unique=True, blank=True)
    date = models.DateField()
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPE_CHOICES)
    description = models.TextField()
    reference = models.CharField(max_length=100, blank=True, help_text="Reference to invoice, expense, etc.")
    
    # Link to related records
    invoice = models.ForeignKey('Invoice', on_delete=models.SET_NULL, null=True, blank=True, related_name='journal_entries')
    expense = models.ForeignKey(Expense, on_delete=models.SET_NULL, null=True, blank=True, related_name='journal_entries')
    payment = models.ForeignKey('Payment', on_delete=models.SET_NULL, null=True, blank=True, related_name='journal_entries')
    
    # Amounts
    debit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='journal_entries_created')
    posted_at = models.DateTimeField(null=True, blank=True)
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='journal_entries_posted')

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Journal Entry'
        verbose_name_plural = 'Journal Entries'

    def __str__(self):
        return f"{self.entry_number} - {self.description[:50]}"

    def save(self, *args, **kwargs):
        # Auto-generate entry number
        if not self.entry_number:
            from datetime import date
            today = date.today()
            prefix = f"JE-{today.strftime('%Y%m%d')}"
            
            last_entry = JournalEntry.objects.filter(
                entry_number__startswith=prefix
            ).order_by('entry_number').last()
            
            if last_entry:
                try:
                    last_seq = int(last_entry.entry_number.split('-')[-1])
                    new_seq = last_seq + 1
                except (ValueError, IndexError):
                    new_seq = 1
            else:
                new_seq = 1
            
            self.entry_number = f"{prefix}-{new_seq:03d}"
        
        super().save(*args, **kwargs)

    def post(self, user):
        """Post the journal entry"""
        from django.utils import timezone
        self.status = 'posted'
        self.posted_at = timezone.now()
        self.posted_by = user
        self.save()

    def void(self):
        """Void the journal entry"""
        self.status = 'void'
        self.save()


class TaxPeriod(models.Model):
    """Tax periods for reporting (monthly, quarterly, annually)"""
    PERIOD_TYPE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('filed', 'Filed'),
    ]

    name = models.CharField(max_length=50, help_text="e.g., January 2024, Q1 2024, FY 2024")
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Tax amounts (calculated)
    total_income = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    output_vat = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="VAT collected on sales")
    input_vat = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="VAT paid on purchases")
    vat_payable = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Net VAT to pay/refund")
    
    notes = models.TextField(blank=True)
    filed_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Tax Period'
        verbose_name_plural = 'Tax Periods'

    def __str__(self):
        return self.name

    def calculate_totals(self):
        """Calculate totals from invoices and expenses within this period"""
        from .models import Invoice, Payment
        
        # Income from paid invoices
        invoices = Invoice.objects.filter(
            issue_date__gte=self.start_date,
            issue_date__lte=self.end_date,
            status__in=['paid', 'partially_paid']
        )
        self.total_income = sum(inv.total_amount for inv in invoices)
        self.output_vat = sum(inv.tax_amount for inv in invoices)
        
        # Expenses
        expenses = Expense.objects.filter(
            date__gte=self.start_date,
            date__lte=self.end_date,
            payment_status='paid'
        )
        self.total_expenses = sum(exp.total_amount for exp in expenses)
        self.input_vat = sum(exp.vat_amount for exp in expenses)
        
        # Net VAT payable
        self.vat_payable = self.output_vat - self.input_vat
        
        self.save()
