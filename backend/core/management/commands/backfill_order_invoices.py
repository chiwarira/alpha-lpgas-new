from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Invoice
from core.signals import create_order_from_invoice


class Command(BaseCommand):
    help = 'Create delivery orders for existing invoices that do not have one yet'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show which invoices would get orders without making changes',
        )

    def handle(self, *args, **options):
        invoices = Invoice.objects.filter(order__isnull=True).prefetch_related('items').order_by('issue_date')

        total = invoices.count()
        skipped = 0
        created = 0

        for invoice in invoices:
            if not invoice.items.exists():
                skipped += 1
                self.stdout.write(
                    self.style.WARNING(f'Skipping {invoice.invoice_number}: no line items')
                )
                continue

            if options['dry_run']:
                created += 1
                self.stdout.write(f'Would create order for {invoice.invoice_number}')
                continue

            with transaction.atomic():
                order = create_order_from_invoice(invoice)
                Invoice.objects.filter(pk=invoice.pk).update(order=order)
                created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created {order.order_number} for {invoice.invoice_number}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Done. {created} order(s) {"would be " if options["dry_run"] else ""}created, '
                f'{skipped} invoice(s) skipped (no items), {total} invoice(s) checked.'
            )
        )
