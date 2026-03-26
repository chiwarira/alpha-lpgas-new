"""
Tax Reporting and Financial Statements Models
Handles VAT returns, SARS tax returns, CIPC annual returns, and financial statements.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import date


class AccountType(models.Model):
    """Chart of Accounts - Account Types"""
    CATEGORY_CHOICES = [
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('revenue', 'Revenue'),
        ('expense', 'Expense'),
    ]
    
    SUBCATEGORY_CHOICES = [
        # Assets
        ('current_asset', 'Current Asset'),
        ('fixed_asset', 'Fixed Asset'),
        ('intangible_asset', 'Intangible Asset'),
        ('other_asset', 'Other Asset'),
        
        # Liabilities
        ('current_liability', 'Current Liability'),
        ('long_term_liability', 'Long-term Liability'),
        
        # Equity
        ('capital', 'Capital'),
        ('retained_earnings', 'Retained Earnings'),
        ('drawings', 'Drawings'),
        
        # Revenue
        ('sales_revenue', 'Sales Revenue'),
        ('service_revenue', 'Service Revenue'),
        ('other_income', 'Other Income'),
        
        # Expenses
        ('cost_of_sales', 'Cost of Sales'),
        ('operating_expense', 'Operating Expense'),
        ('administrative_expense', 'Administrative Expense'),
        ('finance_cost', 'Finance Cost'),
    ]
    
    code = models.CharField(max_length=20, unique=True, help_text="Account code (e.g., 1000, 2000)")
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    subcategory = models.CharField(max_length=30, choices=SUBCATEGORY_CHOICES)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_accounts')
    
    # Flags
    is_active = models.BooleanField(default=True)
    is_system_account = models.BooleanField(default=False, help_text="System-managed account")
    allow_manual_entries = models.BooleanField(default=True)
    
    # Tax related
    is_vat_applicable = models.BooleanField(default=False)
    default_vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['code']
        verbose_name = 'Account Type'
        verbose_name_plural = 'Chart of Accounts'
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_balance(self, start_date=None, end_date=None):
        """Calculate account balance for a period"""
        from django.db.models import Sum
        from .models_accounting import JournalEntry
        
        entries = JournalEntry.objects.filter(status='posted')
        
        if start_date:
            entries = entries.filter(date__gte=start_date)
        if end_date:
            entries = entries.filter(date__lte=end_date)
        
        # Calculate based on account category
        if self.category in ['asset', 'expense']:
            # Debit increases, credit decreases
            debits = entries.aggregate(total=Sum('debit_amount'))['total'] or 0
            credits = entries.aggregate(total=Sum('credit_amount'))['total'] or 0
            return debits - credits
        else:
            # Credit increases, debit decreases (liability, equity, revenue)
            debits = entries.aggregate(total=Sum('debit_amount'))['total'] or 0
            credits = entries.aggregate(total=Sum('credit_amount'))['total'] or 0
            return credits - debits


class VATReturn(models.Model):
    """VAT201 Return for SARS submission"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('submitted', 'Submitted to SARS'),
        ('paid', 'Paid'),
    ]
    
    return_number = models.CharField(max_length=50, unique=True, blank=True)
    period_start = models.DateField()
    period_end = models.DateField()
    filing_period = models.CharField(max_length=20, help_text="e.g., 202401 for Jan 2024")
    
    # VAT201 Fields (Standard-rated supplies)
    box1_output_tax = models.DecimalField(max_digits=14, decimal_places=2, default=0, 
                                          help_text="Output tax at standard rate (15%)")
    box2_output_tax_other = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                                help_text="Output tax at other rates")
    box3_total_output_tax = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    # Input tax
    box4_capital_goods = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                            help_text="Input tax on capital goods")
    box5_other_input_tax = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                              help_text="Input tax on other goods/services")
    box6_total_input_tax = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    # Net VAT
    box7_net_vat = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                      help_text="Net VAT payable/(refundable)")
    
    # Additional fields
    box8_bad_debts = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    box9_imported_services = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    box10_total_deductible = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    # Adjustments
    box11_refund_claimed = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    box12_vat_payable = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                           help_text="Final VAT payable")
    
    # Totals for information
    total_sales_incl_vat = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_purchases_incl_vat = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    submission_date = models.DateField(null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='vat_returns_created')
    
    class Meta:
        ordering = ['-period_end']
        verbose_name = 'VAT Return (VAT201)'
        verbose_name_plural = 'VAT Returns (VAT201)'
    
    def __str__(self):
        return f"VAT201 - {self.filing_period} ({self.period_start} to {self.period_end})"
    
    def save(self, *args, **kwargs):
        if not self.return_number:
            prefix = f"VAT-{self.filing_period}"
            last_return = VATReturn.objects.filter(
                return_number__startswith=prefix
            ).order_by('return_number').last()
            
            if last_return:
                try:
                    last_seq = int(last_return.return_number.split('-')[-1])
                    new_seq = last_seq + 1
                except (ValueError, IndexError):
                    new_seq = 1
            else:
                new_seq = 1
            
            self.return_number = f"{prefix}-{new_seq:02d}"
        
        super().save(*args, **kwargs)
    
    def calculate_vat(self):
        """Auto-calculate VAT from invoices and expenses"""
        from .models import Invoice
        from .models_accounting import Expense
        
        # Output tax (sales)
        invoices = Invoice.objects.filter(
            issue_date__gte=self.period_start,
            issue_date__lte=self.period_end,
            status__in=['paid', 'partially_paid', 'sent']
        )
        
        self.box1_output_tax = sum(inv.tax_amount for inv in invoices)
        self.total_sales_incl_vat = sum(inv.total_amount for inv in invoices)
        
        # Input tax (purchases)
        expenses = Expense.objects.filter(
            date__gte=self.period_start,
            date__lte=self.period_end,
            payment_status__in=['paid', 'partial']
        )
        
        # Separate capital goods from other expenses
        capital_expenses = expenses.filter(category__name__icontains='capital')
        other_expenses = expenses.exclude(category__name__icontains='capital')
        
        self.box4_capital_goods = sum(exp.vat_amount for exp in capital_expenses)
        self.box5_other_input_tax = sum(exp.vat_amount for exp in other_expenses)
        self.total_purchases_incl_vat = sum(exp.total_amount for exp in expenses)
        
        # Calculate totals
        self.box3_total_output_tax = self.box1_output_tax + self.box2_output_tax_other
        self.box6_total_input_tax = self.box4_capital_goods + self.box5_other_input_tax
        self.box7_net_vat = self.box3_total_output_tax - self.box6_total_input_tax
        
        # Calculate final payable
        self.box10_total_deductible = self.box6_total_input_tax + self.box8_bad_debts + self.box9_imported_services
        self.box12_vat_payable = self.box3_total_output_tax - self.box10_total_deductible - self.box11_refund_claimed
        
        self.status = 'calculated'
        self.save()


class CIPCAnnualReturn(models.Model):
    """CIPC Annual Return (CoR14.3)"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('ready', 'Ready for Submission'),
        ('submitted', 'Submitted to CIPC'),
        ('approved', 'Approved'),
    ]
    
    return_number = models.CharField(max_length=50, unique=True, blank=True)
    financial_year_end = models.DateField(help_text="Financial year end date")
    filing_year = models.IntegerField(help_text="Year of filing")
    
    # Company Information
    company_registration_number = models.CharField(max_length=50)
    company_name = models.CharField(max_length=255)
    registered_address = models.TextField()
    postal_address = models.TextField()
    
    # Financial Information
    total_assets = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_liabilities = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_equity = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    profit_loss = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    # Share Capital
    authorized_shares = models.IntegerField(default=0)
    issued_shares = models.IntegerField(default=0)
    share_par_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Directors and Officers
    number_of_directors = models.IntegerField(default=0)
    directors_details = models.JSONField(default=list, blank=True,
                                        help_text="List of director information")
    
    # Auditor/Accountant
    auditor_name = models.CharField(max_length=255, blank=True)
    auditor_registration = models.CharField(max_length=100, blank=True)
    is_audited = models.BooleanField(default=False)
    
    # Filing details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    submission_date = models.DateField(null=True, blank=True)
    approval_date = models.DateField(null=True, blank=True)
    cipc_reference = models.CharField(max_length=100, blank=True)
    
    # Attachments
    financial_statements_file = models.FileField(upload_to='cipc/financial_statements/%Y/', blank=True, null=True)
    supporting_documents = models.FileField(upload_to='cipc/supporting_docs/%Y/', blank=True, null=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='cipc_returns_created')
    
    class Meta:
        ordering = ['-financial_year_end']
        verbose_name = 'CIPC Annual Return'
        verbose_name_plural = 'CIPC Annual Returns'
    
    def __str__(self):
        return f"CIPC Return {self.filing_year} - {self.company_name}"
    
    def save(self, *args, **kwargs):
        if not self.return_number:
            prefix = f"CIPC-{self.filing_year}"
            last_return = CIPCAnnualReturn.objects.filter(
                return_number__startswith=prefix
            ).order_by('return_number').last()
            
            if last_return:
                try:
                    last_seq = int(last_return.return_number.split('-')[-1])
                    new_seq = last_seq + 1
                except (ValueError, IndexError):
                    new_seq = 1
            else:
                new_seq = 1
            
            self.return_number = f"{prefix}-{new_seq:02d}"
        
        super().save(*args, **kwargs)
    
    def populate_from_financial_statements(self):
        """Auto-populate from generated financial statements"""
        from .models import CompanySettings
        
        settings = CompanySettings.objects.first()
        if settings:
            self.company_name = settings.company_name
            self.registered_address = settings.address
            self.postal_address = settings.address
        
        # Get financial data from balance sheet and income statement
        # This will be populated when we generate the statements


class SARSTaxReturn(models.Model):
    """SARS Company Income Tax Return (ITR14)"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('submitted', 'Submitted to SARS'),
        ('assessed', 'Assessed'),
        ('paid', 'Paid'),
    ]
    
    return_number = models.CharField(max_length=50, unique=True, blank=True)
    tax_year_start = models.DateField()
    tax_year_end = models.DateField()
    assessment_year = models.IntegerField(help_text="Tax assessment year")
    
    # Company details
    tax_reference_number = models.CharField(max_length=50, help_text="SARS tax reference")
    company_registration = models.CharField(max_length=50)
    
    # Income
    gross_income = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    exempt_income = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_income = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    # Deductions
    cost_of_sales = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    operating_expenses = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    depreciation = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    interest_expense = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    # Taxable income
    taxable_income = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    assessed_loss_brought_forward = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    taxable_income_after_loss = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    # Tax calculation
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=27.00,
                                   help_text="Corporate tax rate (currently 27%)")
    normal_tax = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    # Credits and payments
    provisional_tax_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    employees_tax_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    foreign_tax_credits = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_credits = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    # Final amount
    tax_payable = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                     help_text="Tax payable/(refundable)")
    
    # Filing details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    submission_date = models.DateField(null=True, blank=True)
    assessment_date = models.DateField(null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    
    # Supporting documents
    financial_statements_file = models.FileField(upload_to='sars/financial_statements/%Y/', blank=True, null=True)
    tax_computation_file = models.FileField(upload_to='sars/computations/%Y/', blank=True, null=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tax_returns_created')
    
    class Meta:
        ordering = ['-tax_year_end']
        verbose_name = 'SARS Tax Return (ITR14)'
        verbose_name_plural = 'SARS Tax Returns (ITR14)'
    
    def __str__(self):
        return f"ITR14 - {self.assessment_year} ({self.tax_year_start} to {self.tax_year_end})"
    
    def save(self, *args, **kwargs):
        if not self.return_number:
            prefix = f"ITR14-{self.assessment_year}"
            last_return = SARSTaxReturn.objects.filter(
                return_number__startswith=prefix
            ).order_by('return_number').last()
            
            if last_return:
                try:
                    last_seq = int(last_return.return_number.split('-')[-1])
                    new_seq = last_seq + 1
                except (ValueError, IndexError):
                    new_seq = 1
            else:
                new_seq = 1
            
            self.return_number = f"{prefix}-{new_seq:02d}"
        
        super().save(*args, **kwargs)
    
    def calculate_tax(self):
        """Auto-calculate tax from financial data"""
        # Calculate total income
        self.total_income = self.gross_income - self.exempt_income
        
        # Calculate total deductions
        self.total_deductions = (
            self.cost_of_sales +
            self.operating_expenses +
            self.depreciation +
            self.interest_expense +
            self.other_deductions
        )
        
        # Calculate taxable income
        self.taxable_income = self.total_income - self.total_deductions
        self.taxable_income_after_loss = max(0, self.taxable_income - self.assessed_loss_brought_forward)
        
        # Calculate tax
        self.normal_tax = self.taxable_income_after_loss * (self.tax_rate / 100)
        
        # Calculate total credits
        self.total_credits = (
            self.provisional_tax_paid +
            self.employees_tax_paid +
            self.foreign_tax_credits
        )
        
        # Calculate final payable
        self.tax_payable = self.normal_tax - self.total_credits
        
        self.status = 'calculated'
        self.save()


class FinancialStatement(models.Model):
    """Generated Financial Statements"""
    STATEMENT_TYPE_CHOICES = [
        ('balance_sheet', 'Balance Sheet / Statement of Financial Position'),
        ('income_statement', 'Income Statement / Statement of Comprehensive Income'),
        ('cash_flow', 'Cash Flow Statement'),
        ('equity_changes', 'Statement of Changes in Equity'),
        ('notes', 'Notes to Financial Statements'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('published', 'Published'),
    ]
    
    statement_number = models.CharField(max_length=50, unique=True, blank=True)
    statement_type = models.CharField(max_length=30, choices=STATEMENT_TYPE_CHOICES)
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Statement data (stored as JSON for flexibility)
    statement_data = models.JSONField(default=dict, help_text="Structured financial data")
    
    # Comparative period
    comparative_period_start = models.DateField(null=True, blank=True)
    comparative_period_end = models.DateField(null=True, blank=True)
    comparative_data = models.JSONField(default=dict, blank=True)
    
    # Generated files
    pdf_file = models.FileField(upload_to='financial_statements/pdf/%Y/', blank=True, null=True)
    excel_file = models.FileField(upload_to='financial_statements/excel/%Y/', blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='statements_created')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='statements_approved')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-period_end', 'statement_type']
        verbose_name = 'Financial Statement'
        verbose_name_plural = 'Financial Statements'
    
    def __str__(self):
        return f"{self.get_statement_type_display()} - {self.period_end}"
    
    def save(self, *args, **kwargs):
        if not self.statement_number:
            type_prefix = {
                'balance_sheet': 'BS',
                'income_statement': 'IS',
                'cash_flow': 'CF',
                'equity_changes': 'EC',
                'notes': 'NT',
            }.get(self.statement_type, 'FS')
            
            year = self.period_end.year
            prefix = f"{type_prefix}-{year}"
            
            last_statement = FinancialStatement.objects.filter(
                statement_number__startswith=prefix
            ).order_by('statement_number').last()
            
            if last_statement:
                try:
                    last_seq = int(last_statement.statement_number.split('-')[-1])
                    new_seq = last_seq + 1
                except (ValueError, IndexError):
                    new_seq = 1
            else:
                new_seq = 1
            
            self.statement_number = f"{prefix}-{new_seq:03d}"
        
        super().save(*args, **kwargs)
    
    def generate_balance_sheet(self):
        """Generate Balance Sheet data"""
        if self.statement_type != 'balance_sheet':
            return
        
        # Get all account balances
        assets = self._get_accounts_by_category('asset')
        liabilities = self._get_accounts_by_category('liability')
        equity = self._get_accounts_by_category('equity')
        
        self.statement_data = {
            'assets': {
                'current_assets': self._get_subcategory_total('asset', 'current_asset'),
                'fixed_assets': self._get_subcategory_total('asset', 'fixed_asset'),
                'intangible_assets': self._get_subcategory_total('asset', 'intangible_asset'),
                'other_assets': self._get_subcategory_total('asset', 'other_asset'),
                'total_assets': sum(acc.get_balance(end_date=self.period_end) for acc in assets),
            },
            'liabilities': {
                'current_liabilities': self._get_subcategory_total('liability', 'current_liability'),
                'long_term_liabilities': self._get_subcategory_total('liability', 'long_term_liability'),
                'total_liabilities': sum(acc.get_balance(end_date=self.period_end) for acc in liabilities),
            },
            'equity': {
                'capital': self._get_subcategory_total('equity', 'capital'),
                'retained_earnings': self._get_subcategory_total('equity', 'retained_earnings'),
                'total_equity': sum(acc.get_balance(end_date=self.period_end) for acc in equity),
            }
        }
        
        self.status = 'generated'
        self.save()
    
    def generate_income_statement(self):
        """Generate Income Statement data"""
        if self.statement_type != 'income_statement':
            return
        
        revenue = self._get_accounts_by_category('revenue')
        expenses = self._get_accounts_by_category('expense')
        
        total_revenue = sum(acc.get_balance(self.period_start, self.period_end) for acc in revenue)
        total_expenses = sum(acc.get_balance(self.period_start, self.period_end) for acc in expenses)
        
        self.statement_data = {
            'revenue': {
                'sales_revenue': self._get_subcategory_total('revenue', 'sales_revenue'),
                'service_revenue': self._get_subcategory_total('revenue', 'service_revenue'),
                'other_income': self._get_subcategory_total('revenue', 'other_income'),
                'total_revenue': total_revenue,
            },
            'expenses': {
                'cost_of_sales': self._get_subcategory_total('expense', 'cost_of_sales'),
                'operating_expenses': self._get_subcategory_total('expense', 'operating_expense'),
                'administrative_expenses': self._get_subcategory_total('expense', 'administrative_expense'),
                'finance_costs': self._get_subcategory_total('expense', 'finance_cost'),
                'total_expenses': total_expenses,
            },
            'profit': {
                'gross_profit': total_revenue - self._get_subcategory_total('expense', 'cost_of_sales'),
                'operating_profit': total_revenue - total_expenses,
                'net_profit': total_revenue - total_expenses,
            }
        }
        
        self.status = 'generated'
        self.save()
    
    def _get_accounts_by_category(self, category):
        """Helper to get accounts by category"""
        return AccountType.objects.filter(category=category, is_active=True)
    
    def _get_subcategory_total(self, category, subcategory):
        """Helper to get total for a subcategory"""
        accounts = AccountType.objects.filter(
            category=category,
            subcategory=subcategory,
            is_active=True
        )
        
        if self.statement_type == 'balance_sheet':
            return sum(acc.get_balance(end_date=self.period_end) for acc in accounts)
        else:
            return sum(acc.get_balance(self.period_start, self.period_end) for acc in accounts)


class TaxConfiguration(models.Model):
    """Tax configuration and settings"""
    # VAT Settings
    vat_vendor_number = models.CharField(max_length=50, blank=True)
    vat_registration_date = models.DateField(null=True, blank=True)
    vat_filing_frequency = models.CharField(max_length=20, choices=[
        ('monthly', 'Monthly'),
        ('bi_monthly', 'Bi-Monthly'),
    ], default='monthly')
    standard_vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=15.00)
    
    # SARS Settings
    sars_tax_reference = models.CharField(max_length=50, blank=True)
    company_registration_number = models.CharField(max_length=50, blank=True)
    financial_year_end_month = models.IntegerField(default=2, help_text="Month number (1-12)")
    financial_year_end_day = models.IntegerField(default=28, help_text="Day of month")
    
    # Tax rates
    corporate_tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=27.00)
    small_business_corporation = models.BooleanField(default=False)
    
    # CIPC Settings
    cipc_company_name = models.CharField(max_length=255, blank=True)
    cipc_registration_number = models.CharField(max_length=50, blank=True)
    
    # Accountant/Auditor
    accountant_name = models.CharField(max_length=255, blank=True)
    accountant_practice_number = models.CharField(max_length=100, blank=True)
    accountant_email = models.EmailField(blank=True)
    accountant_phone = models.CharField(max_length=50, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Tax Configuration'
        verbose_name_plural = 'Tax Configuration'
    
    def __str__(self):
        return f"Tax Configuration - {self.sars_tax_reference or 'Not Set'}"
