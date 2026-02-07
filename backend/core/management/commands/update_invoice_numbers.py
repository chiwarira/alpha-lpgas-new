"""
Management command to update invoice numbering system from date-based to sequential format.
This ensures the latest invoice from the old system (INV-004240) continues sequentially.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Invoice


class Command(BaseCommand):
    help = 'Update invoice numbering from date-based (INV-YYYYMMDD-XXX) to sequential (INV-XXXXXX) format'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )
        parser.add_argument(
            '--start-number',
            type=int,
            default=4241,
            help='Starting number for sequential invoices (default: 4241)',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        start_number = options['start_number']
        
        # Get all invoices with date-based format (INV-YYYYMMDD-XXX)
        date_based_invoices = Invoice.objects.filter(
            invoice_number__regex=r'^INV-\d{8}-\d{3}$'
        ).order_by('created_at')
        
        count = date_based_invoices.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No date-based invoices found. System already using sequential format.'))
            return
        
        self.stdout.write(f'Found {count} invoices with date-based format')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made'))
        
        # Update each invoice
        current_number = start_number
        updated = 0
        
        for invoice in date_based_invoices:
            old_number = invoice.invoice_number
            new_number = f"INV-{current_number:06d}"
            
            if dry_run:
                self.stdout.write(f'Would update: {old_number} -> {new_number}')
            else:
                invoice.invoice_number = new_number
                invoice.save(update_fields=['invoice_number'])
                self.stdout.write(f'Updated: {old_number} -> {new_number}')
                updated += 1
            
            current_number += 1
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'DRY RUN: Would update {count} invoices'))
            self.stdout.write(f'Next invoice number would be: INV-{current_number:06d}')
        else:
            self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated} invoices'))
            self.stdout.write(self.style.SUCCESS(f'Next invoice number will be: INV-{current_number:06d}'))
