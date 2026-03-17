"""
Management command to fix invoice statuses based on balance amounts.
Sets status to 'paid' if balance is 0, 'partially_paid' if 0 < balance < total, 'unpaid' if balance = total.
"""
from django.core.management.base import BaseCommand
from django.db.models import Q
from core.models import Invoice
from decimal import Decimal


class Command(BaseCommand):
    help = 'Fix invoice statuses based on balance amounts (paid_amount and total_amount)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--fix-null-status',
            action='store_true',
            help='Only fix invoices with null/empty status',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        fix_null_only = options['fix_null_status']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Get invoices that need fixing
        if fix_null_only:
            # Only fix invoices with null, empty, or '-' status
            invoices = Invoice.objects.filter(
                Q(status__isnull=True) | Q(status='') | Q(status='-')
            )
            self.stdout.write(f'Finding invoices with null/empty status...')
        else:
            # Fix all invoices (recalculate all statuses)
            invoices = Invoice.objects.all()
            self.stdout.write(f'Recalculating status for all invoices...')
        
        total_count = invoices.count()
        self.stdout.write(f'Found {total_count} invoices to process')
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('No invoices need fixing!'))
            return
        
        updated_count = 0
        paid_count = 0
        partially_paid_count = 0
        unpaid_count = 0
        
        for invoice in invoices:
            old_status = invoice.status
            
            # Recalculate balance to ensure it's correct
            invoice.balance = invoice.total_amount - invoice.paid_amount
            
            # Determine correct status based on balance
            if invoice.balance <= Decimal('0.00'):
                # Fully paid (balance is 0 or negative)
                new_status = 'paid'
                paid_count += 1
            elif invoice.paid_amount > Decimal('0.00') and invoice.balance > Decimal('0.00'):
                # Partially paid (some payment made but balance remains)
                new_status = 'partially_paid'
                partially_paid_count += 1
            else:
                # Unpaid (no payment made, balance equals total)
                new_status = 'unpaid'
                unpaid_count += 1
            
            # Check if status needs updating
            if old_status != new_status or old_status in [None, '', '-']:
                if not dry_run:
                    invoice.status = new_status
                    invoice.save(update_fields=['status', 'balance'])
                
                updated_count += 1
                
                # Show details for changed invoices
                status_display = old_status if old_status else '(empty)'
                self.stdout.write(
                    f'  {invoice.invoice_number}: {status_display} → {new_status} '
                    f'(Total: R{invoice.total_amount}, Paid: R{invoice.paid_amount}, Balance: R{invoice.balance})'
                )
        
        # Summary
        self.stdout.write('\n' + '='*80)
        if dry_run:
            self.stdout.write(self.style.WARNING(f'DRY RUN: Would update {updated_count} of {total_count} invoices'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ Updated {updated_count} of {total_count} invoices'))
        
        self.stdout.write(f'\nStatus breakdown:')
        self.stdout.write(f'  Paid: {paid_count}')
        self.stdout.write(f'  Partially Paid: {partially_paid_count}')
        self.stdout.write(f'  Unpaid: {unpaid_count}')
        self.stdout.write('='*80)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nRun without --dry-run to apply changes'))
