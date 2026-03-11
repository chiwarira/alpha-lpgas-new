"""
Management command to set up default Chart of Accounts for South African businesses
"""
from django.core.management.base import BaseCommand
from core.models import AccountType


class Command(BaseCommand):
    help = 'Sets up default Chart of Accounts for South African businesses'

    def handle(self, *args, **options):
        self.stdout.write('Setting up Chart of Accounts...')
        
        accounts = [
            # ASSETS (1000-1999)
            # Current Assets (1000-1299)
            {'code': '1000', 'name': 'Cash on Hand', 'category': 'asset', 'subcategory': 'current_asset', 
             'description': 'Physical cash in the business', 'is_vat_applicable': False},
            {'code': '1010', 'name': 'Bank - Current Account', 'category': 'asset', 'subcategory': 'current_asset',
             'description': 'Main business bank account', 'is_vat_applicable': False},
            {'code': '1020', 'name': 'Bank - Savings Account', 'category': 'asset', 'subcategory': 'current_asset',
             'description': 'Business savings account', 'is_vat_applicable': False},
            {'code': '1100', 'name': 'Accounts Receivable', 'category': 'asset', 'subcategory': 'current_asset',
             'description': 'Money owed by customers', 'is_vat_applicable': False},
            {'code': '1200', 'name': 'Inventory - Gas Cylinders', 'category': 'asset', 'subcategory': 'current_asset',
             'description': 'Gas cylinder stock', 'is_vat_applicable': False},
            {'code': '1210', 'name': 'Inventory - Gas Stock', 'category': 'asset', 'subcategory': 'current_asset',
             'description': 'LPG gas stock', 'is_vat_applicable': False},
            {'code': '1250', 'name': 'Prepaid Expenses', 'category': 'asset', 'subcategory': 'current_asset',
             'description': 'Expenses paid in advance', 'is_vat_applicable': False},
            {'code': '1260', 'name': 'VAT Input (Reclaimable)', 'category': 'asset', 'subcategory': 'current_asset',
             'description': 'VAT paid on purchases to be reclaimed', 'is_vat_applicable': False},
            
            # Fixed Assets (1300-1599)
            {'code': '1300', 'name': 'Land and Buildings', 'category': 'asset', 'subcategory': 'fixed_asset',
             'description': 'Property owned by the business', 'is_vat_applicable': False},
            {'code': '1310', 'name': 'Vehicles', 'category': 'asset', 'subcategory': 'fixed_asset',
             'description': 'Delivery vehicles and trucks', 'is_vat_applicable': False},
            {'code': '1320', 'name': 'Equipment', 'category': 'asset', 'subcategory': 'fixed_asset',
             'description': 'Business equipment', 'is_vat_applicable': False},
            {'code': '1330', 'name': 'Furniture and Fixtures', 'category': 'asset', 'subcategory': 'fixed_asset',
             'description': 'Office furniture', 'is_vat_applicable': False},
            {'code': '1340', 'name': 'Computer Equipment', 'category': 'asset', 'subcategory': 'fixed_asset',
             'description': 'Computers and IT equipment', 'is_vat_applicable': False},
            {'code': '1350', 'name': 'Accumulated Depreciation - Vehicles', 'category': 'asset', 'subcategory': 'fixed_asset',
             'description': 'Depreciation on vehicles', 'is_vat_applicable': False},
            {'code': '1360', 'name': 'Accumulated Depreciation - Equipment', 'category': 'asset', 'subcategory': 'fixed_asset',
             'description': 'Depreciation on equipment', 'is_vat_applicable': False},
            
            # LIABILITIES (2000-2999)
            # Current Liabilities (2000-2299)
            {'code': '2000', 'name': 'Accounts Payable', 'category': 'liability', 'subcategory': 'current_liability',
             'description': 'Money owed to suppliers', 'is_vat_applicable': False},
            {'code': '2100', 'name': 'VAT Output (Payable)', 'category': 'liability', 'subcategory': 'current_liability',
             'description': 'VAT collected on sales to be paid to SARS', 'is_vat_applicable': False},
            {'code': '2110', 'name': 'PAYE Payable', 'category': 'liability', 'subcategory': 'current_liability',
             'description': 'Employee tax payable to SARS', 'is_vat_applicable': False},
            {'code': '2120', 'name': 'UIF Payable', 'category': 'liability', 'subcategory': 'current_liability',
             'description': 'Unemployment Insurance Fund payable', 'is_vat_applicable': False},
            {'code': '2130', 'name': 'SDL Payable', 'category': 'liability', 'subcategory': 'current_liability',
             'description': 'Skills Development Levy payable', 'is_vat_applicable': False},
            {'code': '2150', 'name': 'Short-term Loans', 'category': 'liability', 'subcategory': 'current_liability',
             'description': 'Loans due within 12 months', 'is_vat_applicable': False},
            {'code': '2160', 'name': 'Credit Card Payable', 'category': 'liability', 'subcategory': 'current_liability',
             'description': 'Business credit card balance', 'is_vat_applicable': False},
            
            # Long-term Liabilities (2300-2599)
            {'code': '2300', 'name': 'Long-term Loans', 'category': 'liability', 'subcategory': 'long_term_liability',
             'description': 'Loans due after 12 months', 'is_vat_applicable': False},
            {'code': '2310', 'name': 'Vehicle Finance', 'category': 'liability', 'subcategory': 'long_term_liability',
             'description': 'Vehicle financing', 'is_vat_applicable': False},
            {'code': '2320', 'name': 'Mortgage Payable', 'category': 'liability', 'subcategory': 'long_term_liability',
             'description': 'Property mortgage', 'is_vat_applicable': False},
            
            # EQUITY (3000-3999)
            {'code': '3000', 'name': 'Share Capital', 'category': 'equity', 'subcategory': 'capital',
             'description': 'Issued share capital', 'is_vat_applicable': False},
            {'code': '3100', 'name': 'Retained Earnings', 'category': 'equity', 'subcategory': 'retained_earnings',
             'description': 'Accumulated profits', 'is_vat_applicable': False},
            {'code': '3200', 'name': 'Current Year Earnings', 'category': 'equity', 'subcategory': 'retained_earnings',
             'description': 'Profit/loss for current year', 'is_vat_applicable': False},
            {'code': '3300', 'name': 'Drawings', 'category': 'equity', 'subcategory': 'drawings',
             'description': 'Owner withdrawals', 'is_vat_applicable': False},
            
            # REVENUE (4000-4999)
            {'code': '4000', 'name': 'Gas Sales - 9kg', 'category': 'revenue', 'subcategory': 'sales_revenue',
             'description': '9kg cylinder sales', 'is_vat_applicable': True, 'default_vat_rate': 15.00},
            {'code': '4010', 'name': 'Gas Sales - 19kg', 'category': 'revenue', 'subcategory': 'sales_revenue',
             'description': '19kg cylinder sales', 'is_vat_applicable': True, 'default_vat_rate': 15.00},
            {'code': '4020', 'name': 'Gas Sales - 48kg', 'category': 'revenue', 'subcategory': 'sales_revenue',
             'description': '48kg cylinder sales', 'is_vat_applicable': True, 'default_vat_rate': 15.00},
            {'code': '4100', 'name': 'Delivery Fees', 'category': 'revenue', 'subcategory': 'service_revenue',
             'description': 'Delivery service income', 'is_vat_applicable': True, 'default_vat_rate': 15.00},
            {'code': '4200', 'name': 'Installation Fees', 'category': 'revenue', 'subcategory': 'service_revenue',
             'description': 'Installation service income', 'is_vat_applicable': True, 'default_vat_rate': 15.00},
            {'code': '4900', 'name': 'Other Income', 'category': 'revenue', 'subcategory': 'other_income',
             'description': 'Miscellaneous income', 'is_vat_applicable': True, 'default_vat_rate': 15.00},
            {'code': '4910', 'name': 'Interest Income', 'category': 'revenue', 'subcategory': 'other_income',
             'description': 'Interest earned', 'is_vat_applicable': False},
            
            # EXPENSES (5000-5999)
            # Cost of Sales (5000-5299)
            {'code': '5000', 'name': 'Cost of Gas Purchased', 'category': 'expense', 'subcategory': 'cost_of_sales',
             'description': 'Cost of LPG gas purchased', 'is_vat_applicable': True, 'default_vat_rate': 15.00},
            {'code': '5010', 'name': 'Cost of Cylinders', 'category': 'expense', 'subcategory': 'cost_of_sales',
             'description': 'Cost of gas cylinders', 'is_vat_applicable': True, 'default_vat_rate': 15.00},
            {'code': '5020', 'name': 'Freight and Delivery Costs', 'category': 'expense', 'subcategory': 'cost_of_sales',
             'description': 'Transport costs for stock', 'is_vat_applicable': True, 'default_vat_rate': 15.00},
            
            # Operating Expenses (5300-5699)
            {'code': '5300', 'name': 'Salaries and Wages', 'category': 'expense', 'subcategory': 'operating_expense',
             'description': 'Employee salaries', 'is_vat_applicable': False},
            {'code': '5310', 'name': 'Driver Commissions', 'category': 'expense', 'subcategory': 'operating_expense',
             'description': 'Driver commission payments', 'is_vat_applicable': False},
            {'code': '5320', 'name': 'Employer UIF', 'category': 'expense', 'subcategory': 'operating_expense',
             'description': 'Employer UIF contributions', 'is_vat_applicable': False},
            {'code': '5330', 'name': 'Skills Development Levy', 'category': 'expense', 'subcategory': 'operating_expense',
             'description': 'SDL contributions', 'is_vat_applicable': False},
            {'code': '5400', 'name': 'Rent Expense', 'category': 'expense', 'subcategory': 'operating_expense',
             'description': 'Premises rental', 'is_vat_applicable': True, 'default_vat_rate': 15.00},
            {'code': '5410', 'name': 'Utilities - Electricity', 'category': 'expense', 'subcategory': 'operating_expense',
             'description': 'Electricity costs', 'is_vat_applicable': True, 'default_vat_rate': 15.00},
            {'code': '5420', 'name': 'Utilities - Water', 'category': 'expense', 'subcategory': 'operating_expense',
             'description': 'Water costs', 'is_vat_applicable': True, 'default_vat_rate': 15.00},
            {'code': '5430', 'name': 'Telephone and Internet', 'category': 'expense', 'subcategory': 'operating_expense',
             'description': 'Communication costs', 'is_vat_applicable': True, 'default_vat_rate': 15.00},
            {'code': '5500', 'name': 'Vehicle Fuel', 'category': 'expense', 'subcategory': 'operating_expense',
             'description': 'Fuel for delivery vehicles', 'is_vat_applicable': True, 'default_vat_rate': 15.00},
            {'code': '5510', 'name': 'Vehicle Maintenance', 'category': 'expense', 'subcategory': 'operating_expense',
             'description': 'Vehicle repairs and maintenance', 'is_vat_applicable': True, 'default_vat_rate': 15.00},
            {'code': '5520', 'name': 'Vehicle Insurance', 'category': 'expense', 'subcategory': 'operating_expense',
             'description': 'Vehicle insurance premiums', 'is_vat_applicable': True, 'default_vat_rate': 15.00},
            {'code': '5530', 'name': 'Vehicle Licenses', 'category': 'expense', 'subcategory': 'operating_expense',
             'description': 'Vehicle license fees', 'is_vat_applicable': False},
            
            # Administrative Expenses (5700-5899)
            {'code': '5700', 'name': 'Office Supplies', 'category': 'expense', 'subcategory': 'administrative_expense',
             'description': 'Stationery and office supplies', 'is_vat_applicable': True, 'default_vat_rate': 15.00},
            {'code': '5710', 'name': 'Computer and Software', 'category': 'expense', 'subcategory': 'administrative_expense',
             'description': 'IT and software costs', 'is_vat_applicable': True, 'default_vat_rate': 15.00},
            {'code': '5720', 'name': 'Professional Fees', 'category': 'expense', 'subcategory': 'administrative_expense',
             'description': 'Accounting, legal fees', 'is_vat_applicable': True, 'default_vat_rate': 15.00},
            {'code': '5730', 'name': 'Bank Charges', 'category': 'expense', 'subcategory': 'administrative_expense',
             'description': 'Bank fees and charges', 'is_vat_applicable': True, 'default_vat_rate': 15.00},
            {'code': '5740', 'name': 'Insurance - General', 'category': 'expense', 'subcategory': 'administrative_expense',
             'description': 'General business insurance', 'is_vat_applicable': True, 'default_vat_rate': 15.00},
            {'code': '5750', 'name': 'Marketing and Advertising', 'category': 'expense', 'subcategory': 'administrative_expense',
             'description': 'Marketing costs', 'is_vat_applicable': True, 'default_vat_rate': 15.00},
            {'code': '5760', 'name': 'Training and Development', 'category': 'expense', 'subcategory': 'administrative_expense',
             'description': 'Staff training', 'is_vat_applicable': True, 'default_vat_rate': 15.00},
            {'code': '5770', 'name': 'Subscriptions and Memberships', 'category': 'expense', 'subcategory': 'administrative_expense',
             'description': 'Professional subscriptions', 'is_vat_applicable': True, 'default_vat_rate': 15.00},
            
            # Finance Costs (5900-5999)
            {'code': '5900', 'name': 'Interest Expense - Loans', 'category': 'expense', 'subcategory': 'finance_cost',
             'description': 'Interest on loans', 'is_vat_applicable': False},
            {'code': '5910', 'name': 'Interest Expense - Credit Card', 'category': 'expense', 'subcategory': 'finance_cost',
             'description': 'Credit card interest', 'is_vat_applicable': False},
            {'code': '5920', 'name': 'Depreciation Expense', 'category': 'expense', 'subcategory': 'finance_cost',
             'description': 'Asset depreciation', 'is_vat_applicable': False},
        ]
        
        created_count = 0
        updated_count = 0
        
        for account_data in accounts:
            account, created = AccountType.objects.update_or_create(
                code=account_data['code'],
                defaults=account_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created: {account.code} - {account.name}'))
            else:
                updated_count += 1
                self.stdout.write(f'  Updated: {account.code} - {account.name}')
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Chart of Accounts setup complete!'))
        self.stdout.write(f'  Created: {created_count} accounts')
        self.stdout.write(f'  Updated: {updated_count} accounts')
        self.stdout.write(f'  Total: {len(accounts)} accounts')
