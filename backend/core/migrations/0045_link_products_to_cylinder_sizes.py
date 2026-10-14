"""
Link existing gas products to cylinder sizes and set their stock effect, and make
sure a 'Cylinder Deposit Xkg' product exists for every active cylinder size.

Matching rules (case-insensitive, by product name):
  - "...deposit..."  -> stock_effect='deposit'
  - "...return..."/"...refund..." -> stock_effect='deposit_refund'
  - otherwise anything containing "<N>kg" that is a cylinder/exchange/refill -> 'exchange'
Products already configured (stock_effect != 'none') are left untouched.
"""
import re
from decimal import Decimal

from django.db import migrations


SIZE_RE = re.compile(r'(\d+)\s*kg', re.IGNORECASE)
DEFAULT_SIZES = [(5, '5kg'), (9, '9kg'), (14, '14kg'), (19, '19kg'), (48, '48kg')]


def forwards(apps, schema_editor):
    Product = apps.get_model('core', 'Product')
    CylinderSize = apps.get_model('core', 'CylinderSize')
    GasStock = apps.get_model('core', 'GasStock')

    # Ensure the standard sizes exist
    for weight, name in DEFAULT_SIZES:
        cs, _ = CylinderSize.objects.get_or_create(weight_kg=Decimal(weight), defaults={'name': name, 'order': weight})
        GasStock.objects.get_or_create(cylinder_size=cs)

    sizes = {int(cs.weight_kg): cs for cs in CylinderSize.objects.all()}

    for product in Product.objects.all():
        if product.stock_effect != 'none' and product.cylinder_size_id:
            continue
        name = (product.name or '').lower()
        m = SIZE_RE.search(name) or SIZE_RE.search(product.weight or '')
        if not m:
            # e.g. "48 Return" (no kg suffix)
            m2 = re.search(r'\b(\d+)\b', name)
            m = m2 if (m2 and 'return' in name) else None
        if not m:
            continue
        weight = int(m.group(1))
        cs = sizes.get(weight)
        if not cs:
            continue

        if 'deposit' in name:
            effect = 'deposit'
        elif 'return' in name or 'refund' in name:
            effect = 'deposit_refund'
        elif any(k in name for k in ('cylinder', 'exchange', 'refill', 'gas')):
            effect = 'exchange'
        else:
            continue

        product.cylinder_size = cs
        product.stock_effect = effect
        product.save(update_fields=['cylinder_size', 'stock_effect'])

    # Create deposit products where missing (name format used in production)
    for weight, cs in sizes.items():
        if not cs.is_active:
            continue
        exists = Product.objects.filter(stock_effect='deposit', cylinder_size=cs).exists()
        if exists:
            continue
        name = f"Cylinder Deposit {cs.name}"
        if Product.objects.filter(name__iexact=name).exists():
            p = Product.objects.filter(name__iexact=name).first()
            p.cylinder_size, p.stock_effect = cs, 'deposit'
            p.save(update_fields=['cylinder_size', 'stock_effect'])
            continue
        sku = f"DEP{weight:03d}"
        if Product.objects.filter(sku=sku).exists():
            sku = f"DEP{weight:03d}-{cs.id}"
        Product.objects.create(
            name=name, sku=sku, description=f"Refundable deposit for a {cs.name} cylinder",
            unit_price=Decimal('0.00'), tax_rate=Decimal('15.00'), unit='cylinder',
            weight=cs.name, cylinder_size=cs, stock_effect='deposit',
            show_on_website=False, available_for_invoicing=True, is_active=True,
        )


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0044_stock_module_empties_alerts'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
