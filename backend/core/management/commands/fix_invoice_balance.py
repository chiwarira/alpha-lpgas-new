from django.core.management.base import BaseCommand
from core.models import Invoice


class Command(BaseCommand):
    help = 'Fix invoice balances and statuses by recalculating from actual payments'

    def handle(self, *args, **options):
        from datetime import date
        
        invoices = Invoice.objects.all()
        fixed_count = 0
        
        self.stdout.write('Checking all invoices for incorrect balances and statuses...')
        
        for invoice in invoices:
            # Recalculate paid_amount from actual payments
            actual_paid = sum(p.amount for p in invoice.payments.all())
            
            # Calculate what balance should be
            correct_balance = invoice.total_amount - actual_paid
            
            # Check if current values are incorrect
            if invoice.paid_amount != actual_paid or invoice.balance != correct_balance:
                old_paid = invoice.paid_amount
                old_balance = invoice.balance
                old_status = invoice.status
                
                # Fix paid_amount and balance
                invoice.paid_amount = actual_paid
                invoice.balance = correct_balance
                
                # Recalculate status
                if invoice.status not in ['draft', 'cancelled']:
                    if invoice.paid_amount >= invoice.total_amount:
                        invoice.status = 'paid'
                    elif invoice.paid_amount > 0:
                        invoice.status = 'partially_paid'
                    elif invoice.due_date and invoice.due_date < date.today():
                        invoice.status = 'overdue'
                    else:
                        invoice.status = 'unpaid'
                
                # Save without triggering calculate_totals to avoid recursion
                invoice.save(update_fields=['paid_amount', 'balance', 'status'])
                
                fixed_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Fixed {invoice.invoice_number}: '
                        f'Paid: R{old_paid} -> R{actual_paid}, '
                        f'Balance: R{old_balance} -> R{correct_balance}, '
                        f'Status: {old_status} -> {invoice.status}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Fixed {fixed_count} invoice(s).'
            )
        )
