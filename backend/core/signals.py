from django.db.models.signals import pre_delete, post_save
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


def create_order_from_invoice(invoice):
    """Create a delivery Order mirroring an invoice's current line items."""
    from .models import Order, OrderItem, OrderStatusHistory

    client = invoice.client
    address_parts = [client.address, client.city, client.state, client.postal_code, client.country]
    delivery_address = ', '.join(p for p in address_parts if p)

    # Compute totals from line items — invoice totals may not be recalculated yet
    items_total = sum(item.total for item in invoice.items.all())

    order = Order.objects.create(
        client=client,
        customer_name=client.name,
        customer_email=client.email or '',
        customer_phone=client.phone,
        delivery_address=delivery_address,
        delivery_zone=invoice.delivery_zone,
        delivery_notes=invoice.delivery_note,
        subtotal=items_total,
        discount_amount=invoice.discount_amount,
        total=items_total - invoice.discount_amount,
        payment_method='eft',
        payment_status='paid' if invoice.status == 'paid' else 'pending',
        notes=f'Auto-created from {invoice.invoice_number}',
    )
    OrderStatusHistory.objects.create(
        order=order,
        status='pending',
        notes=f'Order created from invoice {invoice.invoice_number}',
    )
    for item in invoice.items.all():
        OrderItem.objects.create(
            order=order,
            invoice_item=item,
            product=item.product,
            quantity=int(item.quantity),
            unit_price=item.unit_price,
        )
    return order


@receiver(post_save, sender='core.InvoiceItem')
def sync_invoice_item_to_order(sender, instance, created, **kwargs):
    """When an invoice gets its first line item, generate a delivery order.
    Line items added afterwards are synced onto the existing order."""
    invoice = instance.invoice

    if invoice.order_id is None:
        order = create_order_from_invoice(invoice)
        type(invoice).objects.filter(pk=invoice.pk).update(order=order)
        invoice.order = order
    elif created and not instance.order_items.exists():
        from .models import OrderItem
        OrderItem.objects.create(
            order_id=invoice.order_id,
            invoice_item=instance,
            product=instance.product,
            quantity=int(instance.quantity),
            unit_price=instance.unit_price,
        )


@receiver(post_save, sender='core.Invoice')
def sync_order_from_invoice(sender, instance, **kwargs):
    """Keep the generated order's payment status and totals aligned with the invoice."""
    if not instance.order_id:
        return
    from .models import Order
    payment_status = 'paid' if instance.status == 'paid' else 'pending'
    Order.objects.filter(pk=instance.order_id).exclude(
        payment_status=payment_status,
        subtotal=instance.subtotal,
        discount_amount=instance.discount_amount,
        total=instance.total_amount,
    ).update(
        payment_status=payment_status,
        subtotal=instance.subtotal,
        discount_amount=instance.discount_amount,
        total=instance.total_amount,
    )
