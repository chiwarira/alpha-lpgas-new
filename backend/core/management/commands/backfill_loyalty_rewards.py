"""
Record historical 100% (free) loyalty rewards.

Before rewards were applied automatically, a free refill was invoiced as a Gas
Exchange / Gas Refill line priced at R0. This creates a 'reward_claimed'
transaction (100%) for each such bottle so the reward counts include history.
Safe to re-run: lines that already have a reward record are skipped.

    python manage.py backfill_loyalty_rewards --dry-run
    python manage.py backfill_loyalty_rewards
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from core.models import InvoiceItem
from core.models_loyalty import LoyaltyCard, LoyaltyTransaction
from core.utils_loyalty import LOYALTY_REWARD_SKU, _size_from_name


class Command(BaseCommand):
    help = 'Record historical free (R0) gas exchange lines as 100% loyalty rewards'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show what would be recorded without saving')

    @transaction.atomic
    def handle(self, *args, dry_run=False, **options):
        lines = (
            InvoiceItem.objects
            .filter(Q(product__name__icontains='gas exchange') | Q(product__name__icontains='gas refill'), unit_price=0, quantity__gt=0)
            .exclude(product__sku=LOYALTY_REWARD_SKU)
            .select_related('invoice__client', 'product')
            .order_by('invoice__issue_date', 'pk')
        )
        already = set(LoyaltyTransaction.objects.filter(
            transaction_type='reward_claimed', reward_item__isnull=False
        ).values_list('reward_item_id', flat=True))

        created = 0
        for line in lines:
            if line.pk in already:
                continue
            invoice = line.invoice
            bottles = int(line.quantity)
            self.stdout.write(f'{invoice.issue_date} {invoice.invoice_number} {invoice.client.name}: {bottles} x {line.product.name} (R{line.product.unit_price} each)')
            created += bottles
            if dry_run:
                continue
            card, _ = LoyaltyCard.objects.get_or_create(
                client=invoice.client, is_active=True,
                defaults={'stamps': 0, 'cylinder_size': _size_from_name(line.product.name)},
            )
            for _ in range(bottles):
                LoyaltyTransaction.objects.create(
                    loyalty_card=card,
                    invoice=invoice,
                    transaction_type='reward_claimed',
                    stamps_before=card.stamps,
                    stamps_after=card.stamps,
                    reward_percent=100,
                    reward_amount=line.product.unit_price,
                    reward_item=line,
                    notes=f'Backfilled: free 1 x {line.product.name} on invoice {invoice.invoice_number} (value at current price)',
                    created_by=invoice.created_by,
                )

        verb = 'Would record' if dry_run else 'Recorded'
        self.stdout.write(self.style.SUCCESS(f'{verb} {created} historical 100% reward(s).'))
