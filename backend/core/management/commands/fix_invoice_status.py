from django.core.management.base import BaseCommand
from core.models import Invoice


class Command(BaseCommand):
    help = 'Fix invoice statuses based on paid_amount and due_date'

    def handle(self, *args, **options):
        from datetime import date
        
        invoices = Invoice.objects.all()
        updated_count = 0
        
        self.stdout.write('Checking all invoices...')
        
        for invoice in invoices:
            old_status = invoice.status
            
            # Skip draft and cancelled invoices
            if invoice.status in ['draft', 'cancelled']:
                continue
            
            # Determine correct status
            if invoice.paid_amount >= invoice.total_amount:
                new_status = 'paid'
            elif invoice.paid_amount > 0:
                new_status = 'partially_paid'
            elif invoice.due_date and invoice.due_date < date.today():
                new_status = 'overdue'
            else:
                new_status = 'unpaid'
            
            # Update if status is incorrect
            if old_status != new_status:
                invoice.status = new_status
                invoice.save(update_fields=['status'])
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Invoice {invoice.invoice_number}: {old_status} -> {new_status} '
                        f'(Paid: R{invoice.paid_amount}/{invoice.total_amount})'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Updated {updated_count} invoice(s).'
            )
        )
