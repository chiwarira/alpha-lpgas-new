from django.db.models.signals import pre_delete
from django.dispatch import receiver


@receiver(pre_delete, sender='core.Invoice')
def reverse_loyalty_on_invoice_delete(sender, instance, **kwargs):
    """When an invoice is deleted, reverse any loyalty stamps it created."""
    from .models_loyalty import LoyaltyTransaction

    transactions = LoyaltyTransaction.objects.filter(
        invoice=instance,
        transaction_type='stamp'
    ).select_related('loyalty_card')

    for txn in transactions:
        card = txn.loyalty_card
        # Decrement stamps (don't go below 0)
        card.stamps = max(0, card.stamps - 1)
        card.save()
        txn.delete()
