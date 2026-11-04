"""
Normalise loyalty cards that went past 9 stamps under the old system (cards never reset).

Rewards for those cards were given outside the system, so for each completed cycle
(9 stamps followed by a further purchase) a historical 100% 'reward_claimed'
transaction is recorded and the card keeps only the remainder:
10 -> 1 given, 1/9;  18 -> 1 given, 9/9 (due);  40 -> 4 given, 4/9.
A card at exactly 9/9 is left alone - its reward is still due.
Safe to re-run: normalised cards are at 9 or fewer stamps.

    python manage.py normalize_loyalty_cards --dry-run
    python manage.py normalize_loyalty_cards
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Product
from core.models_loyalty import LoyaltyCard, LoyaltyTransaction, STAMPS_REQUIRED


def split_stamps(stamps):
    """Return (rewards_given, remaining_stamps) for a card with more than STAMPS_REQUIRED stamps."""
    given = (stamps - 1) // STAMPS_REQUIRED
    return given, stamps - given * STAMPS_REQUIRED


class Command(BaseCommand):
    help = 'Record historical 100% rewards for cards over 9 stamps and reduce them to the remainder'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show what would change without saving')

    @transaction.atomic
    def handle(self, *args, dry_run=False, **options):
        cards = LoyaltyCard.objects.filter(stamps__gt=STAMPS_REQUIRED).select_related('client').order_by('-stamps')
        prices = {}
        total_cards = total_rewards = 0
        for card in cards:
            given, remaining = split_stamps(card.stamps)
            size = card.cylinder_size
            if size not in prices:
                product = Product.objects.filter(name__istartswith=size, name__icontains='gas exchange').first() if size else None
                prices[size] = product.unit_price if product else None
            self.stdout.write(f'{card.client.name}: {card.stamps} stamps -> {given} reward(s) given, now {remaining}/{STAMPS_REQUIRED}')
            total_cards += 1
            total_rewards += given
            if dry_run:
                continue
            stamps_before = card.stamps
            for _ in range(given):
                LoyaltyTransaction.objects.create(
                    loyalty_card=card,
                    transaction_type='reward_claimed',
                    stamps_before=stamps_before,
                    stamps_after=remaining,
                    reward_percent=100,
                    reward_amount=prices[size],
                    notes=f'Historical: free {size or ""} refill given outside the system (card had {stamps_before} stamps)',
                )
            card.stamps = remaining
            card.save()
            LoyaltyTransaction.objects.create(
                loyalty_card=card,
                transaction_type='card_reset',
                stamps_before=stamps_before,
                stamps_after=remaining,
                notes=f'Normalised from {stamps_before} stamps: {given} historical reward(s) recorded',
            )

        verb = 'Would normalise' if dry_run else 'Normalised'
        self.stdout.write(self.style.SUCCESS(f'{verb} {total_cards} card(s), {total_rewards} historical 100% reward(s).'))
