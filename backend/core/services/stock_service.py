"""
Cylinder stock service.

Keeps full/empty cylinder counts in sync with invoice line items, produces
sales summaries (tanks sold per day/week/month), re-order recommendations
based on historical sales, and sends WhatsApp stock alerts.
"""
import logging
from calendar import monthrange
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum, F
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Stock effects of a sale
# ---------------------------------------------------------------------------

def _effect_deltas(stock_effect, qty):
    """Return (full_change, empty_change) for selling `qty` units with the given effect."""
    qty = int(qty)
    if stock_effect == 'exchange':
        return -qty, qty
    if stock_effect == 'deposit':
        return 0, -qty
    if stock_effect == 'deposit_refund':
        return 0, qty
    return 0, 0


def _movement_type_for(stock_effect):
    return {'exchange': 'sale', 'deposit': 'deposit', 'deposit_refund': 'return'}.get(stock_effect, 'sale')


def _item_tracks_stock(product):
    return bool(product and product.cylinder_size_id and product.stock_effect != 'none')


def apply_invoice_item_stock(item):
    """Create the stock movement for a (new) invoice line item. Idempotent via stock_deducted."""
    from ..models_stock import StockMovement
    from ..models import InvoiceItem

    product = item.product
    if item.stock_deducted or not _item_tracks_stock(product):
        return None

    full_change, empty_change = _effect_deltas(product.stock_effect, item.quantity)
    if full_change == 0 and empty_change == 0:
        return None

    movement = StockMovement.objects.create(
        movement_type=_movement_type_for(product.stock_effect),
        date=item.invoice.issue_date,
        cylinder_size=product.cylinder_size,
        quantity=full_change,
        empty_change=empty_change,
        invoice=item.invoice,
        invoice_item=item,
        reference=item.invoice.invoice_number,
        notes=f"{product.name} x {int(item.quantity)}",
        created_by=item.invoice.created_by,
    )
    InvoiceItem.objects.filter(pk=item.pk).update(stock_deducted=True)
    item.stock_deducted = True
    return movement


def reverse_invoice_item_stock(item, product=None, quantity=None, reason="Line item removed"):
    """Reverse the stock effect previously applied for an invoice line item."""
    from ..models_stock import StockMovement
    from ..models import InvoiceItem

    product = product or item.product
    quantity = item.quantity if quantity is None else quantity
    if not item.stock_deducted or not _item_tracks_stock(product):
        return None

    full_change, empty_change = _effect_deltas(product.stock_effect, quantity)
    movement = StockMovement.objects.create(
        movement_type='reversal',
        date=date.today(),
        cylinder_size=product.cylinder_size,
        quantity=-full_change,
        empty_change=-empty_change,
        invoice=item.invoice,
        invoice_item=item if item.pk else None,
        reference=item.invoice.invoice_number,
        notes=f"Reversal ({reason}): {product.name} x {int(quantity)}",
    )
    if item.pk:
        InvoiceItem.objects.filter(pk=item.pk).update(stock_deducted=False)
    item.stock_deducted = False
    return movement


def sync_invoice_item_stock(item, previous=None):
    """
    Called after an InvoiceItem is saved. For new items, applies stock.
    For edited items whose product or quantity changed, reverses the old effect
    and applies the new one.
    """
    try:
        if previous is None:
            apply_invoice_item_stock(item)
            return
        changed = previous.product_id != item.product_id or int(previous.quantity) != int(item.quantity)
        if not changed:
            # Nothing stock-relevant changed; still apply if never deducted (e.g. product was re-configured)
            if not item.stock_deducted:
                apply_invoice_item_stock(item)
            return
        reverse_invoice_item_stock(item, product=previous.product, quantity=previous.quantity, reason="Line item edited")
        apply_invoice_item_stock(item)
    except Exception:  # never let stock bookkeeping break invoicing
        logger.exception("Stock sync failed for invoice item %s", item.pk)


# ---------------------------------------------------------------------------
# Stock receipts / adjustments
# ---------------------------------------------------------------------------

@transaction.atomic
def receive_stock(date_received, lines, supplier=None, invoice_number='', notes='', user=None, send_alert=True):
    """
    Record a stock delivery.

    lines: iterable of dicts {cylinder_size, quantity, empties_returned, unit_cost}
    Returns the StockPurchase.
    """
    from ..models_stock import StockPurchase, StockPurchaseItem

    purchase = StockPurchase.objects.create(
        date=date_received, supplier=supplier, invoice_number=invoice_number or '',
        notes=notes or '', created_by=user,
    )
    for line in lines:
        if not line.get('quantity'):
            continue
        StockPurchaseItem.objects.create(
            purchase=purchase,
            cylinder_size=line['cylinder_size'],
            quantity=int(line['quantity']),
            empties_returned=int(line.get('empties_returned') or 0),
            unit_cost=line.get('unit_cost') or Decimal('0.00'),
        )
    purchase.calculate_totals()
    if send_alert:
        transaction.on_commit(lambda: send_stock_received_alert(purchase))
    return purchase


@transaction.atomic
def set_stock_levels(counts, user=None, notes='Stocktake'):
    """
    Set absolute stock counts (stocktake). counts: iterable of dicts
    {cylinder_size, full_quantity, empty_quantity} (either may be None to leave unchanged).
    Creates adjustment movements for the differences.
    """
    from ..models_stock import GasStock, StockMovement

    movements = []
    for row in counts:
        stock, _ = GasStock.objects.get_or_create(cylinder_size=row['cylinder_size'])
        full_target = row.get('full_quantity')
        empty_target = row.get('empty_quantity')
        full_change = 0 if full_target is None else int(full_target) - stock.quantity
        empty_change = 0 if empty_target is None else int(empty_target) - stock.empty_quantity
        if full_change == 0 and empty_change == 0:
            continue
        movements.append(StockMovement.objects.create(
            movement_type='adjustment', date=date.today(), cylinder_size=row['cylinder_size'],
            quantity=full_change, empty_change=empty_change, notes=notes, created_by=user,
        ))
    return movements


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def period_bounds(range_type, ref=None, start=None, end=None):
    """Return (start_date, end_date, label) for a report range."""
    today = date.today()
    ref = ref or today
    if range_type == 'weekly':
        s = ref - timedelta(days=ref.weekday())
        e = s + timedelta(days=6)
        return s, e, f"Week of {s.strftime('%d %b')} - {e.strftime('%d %b %Y')}"
    if range_type == 'monthly':
        s = ref.replace(day=1)
        e = ref.replace(day=monthrange(ref.year, ref.month)[1])
        return s, e, s.strftime('%B %Y')
    if range_type == 'yearly':
        return date(ref.year, 1, 1), date(ref.year, 12, 31), str(ref.year)
    if range_type == 'custom':
        s, e = start or today, end or today
        if s > e:
            s, e = e, s
        return s, e, f"{s.strftime('%d %b %Y')} - {e.strftime('%d %b %Y')}"
    return ref, ref, ref.strftime('%A, %d %B %Y')


def _sales_items(start, end, stock_effect):
    from ..models import InvoiceItem
    return InvoiceItem.objects.filter(
        invoice__issue_date__gte=start,
        invoice__issue_date__lte=end,
        product__stock_effect=stock_effect,
        product__cylinder_size__isnull=False,
    )


def sales_by_size(start, end, stock_effect='exchange'):
    """{CylinderSize: qty} sold in the period for the given effect."""
    from ..models_stock import CylinderSize
    rows = _sales_items(start, end, stock_effect).values('product__cylinder_size').annotate(qty=Sum('quantity'))
    by_id = {r['product__cylinder_size']: int(r['qty'] or 0) for r in rows}
    return {cs: by_id.get(cs.id, 0) for cs in CylinderSize.objects.filter(is_active=True)}


def sales_timeline(start, end, stock_effect='exchange', group='day'):
    """
    Rows of {period, sizes: {size_name: qty}, total} grouped by day/week/month,
    for building the sales table in the report.
    """
    trunc = {'day': TruncDate, 'week': TruncWeek, 'month': TruncMonth}[group]
    rows = (_sales_items(start, end, stock_effect)
            .annotate(period=trunc('invoice__issue_date'))
            .values('period', 'product__cylinder_size__name')
            .annotate(qty=Sum('quantity'))
            .order_by('period'))
    timeline = {}
    for r in rows:
        p = r['period']
        p = p.date() if isinstance(p, datetime) else p
        bucket = timeline.setdefault(p, {'period': p, 'sizes': {}, 'total': 0})
        q = int(r['qty'] or 0)
        bucket['sizes'][r['product__cylinder_size__name']] = bucket['sizes'].get(r['product__cylinder_size__name'], 0) + q
        bucket['total'] += q
    return sorted(timeline.values(), key=lambda b: b['period'], reverse=True)


def quick_sales_summary():
    """Today / this week / this month / last 30 days for refills and tank (deposit) sales."""
    today = date.today()
    periods = {
        'today': (today, today),
        'week': period_bounds('weekly')[:2],
        'month': period_bounds('monthly')[:2],
        'last_30': (today - timedelta(days=29), today),
    }
    out = {}
    for key, (s, e) in periods.items():
        refills = sales_by_size(s, e, 'exchange')
        tanks = sales_by_size(s, e, 'deposit')
        out[key] = {
            'start': s, 'end': e,
            'refills': refills, 'refills_total': sum(refills.values()),
            'tanks': tanks, 'tanks_total': sum(tanks.values()),
        }
    return out


# ---------------------------------------------------------------------------
# Re-order recommendations
# ---------------------------------------------------------------------------

def reorder_recommendations(settings=None):
    """
    For every active cylinder size: current stock, average daily sales over the
    configured history window, days of cover left and a suggested order quantity.
    """
    from ..models_stock import CylinderSize, GasStock, StockAlertSettings

    settings = settings or StockAlertSettings.load()
    today = date.today()
    history_days = max(settings.sales_history_days, 1)
    start = today - timedelta(days=history_days - 1)
    sold = sales_by_size(start, today, 'exchange')
    sold_tanks = sales_by_size(start, today, 'deposit')
    stocks = {s.cylinder_size_id: s for s in GasStock.objects.select_related('cylinder_size')}

    cover_target_days = settings.supplier_lead_time_days + settings.safety_stock_days + settings.reorder_cover_days
    recs = []
    for cs in CylinderSize.objects.filter(is_active=True):
        stock = stocks.get(cs.id)
        full = stock.quantity if stock else 0
        empties = stock.empty_quantity if stock else 0
        reorder_level = stock.reorder_level if stock else 0
        avg_daily = Decimal(sold.get(cs, 0)) / Decimal(history_days)
        days_cover = (Decimal(full) / avg_daily) if avg_daily > 0 else None
        # Stock needed to cover lead time + safety + desired cover, minus what we have
        target = avg_daily * Decimal(cover_target_days)
        suggested = int(max(Decimal(0), (target - Decimal(full)).to_integral_value(rounding='ROUND_CEILING')))
        reorder_point = avg_daily * Decimal(settings.supplier_lead_time_days + settings.safety_stock_days)
        is_low = full <= reorder_level or (avg_daily > 0 and Decimal(full) <= reorder_point)
        recs.append({
            'cylinder_size': cs,
            'stock': stock,
            'full': full,
            'empties': empties,
            'reorder_level': reorder_level,
            'sold_in_window': sold.get(cs, 0),
            'tanks_sold_in_window': sold_tanks.get(cs, 0),
            'avg_daily': avg_daily,
            'avg_weekly': avg_daily * 7,
            'days_cover': days_cover,
            'reorder_point': reorder_point,
            'suggested_order_qty': suggested,
            'is_low': is_low,
            'runs_out_on': (today + timedelta(days=int(days_cover))) if days_cover is not None else None,
        })
    return recs


# ---------------------------------------------------------------------------
# WhatsApp alerts
# ---------------------------------------------------------------------------

def _send_whatsapp_to_recipients(message, settings=None):
    """Send `message` to all configured recipients. Returns list of (number, result)."""
    from ..models_stock import StockAlertSettings
    from .whatsapp_service import WhatsAppService

    settings = settings or StockAlertSettings.load()
    numbers = settings.recipient_numbers
    if not settings.alerts_enabled or not numbers:
        return []
    try:
        service = WhatsAppService()
    except Exception:
        logger.exception("WhatsApp service unavailable; stock alert not sent")
        return []
    if not service.config.phone_number_id or not service.config.access_token:
        err = 'WhatsApp Business API is not configured (Admin > WhatsApp Configuration: phone number ID / access token).'
        logger.warning("Stock alert not sent: %s", err)
        return [(n, {'success': False, 'error': err}) for n in numbers]
    results = []
    for number in numbers:
        try:
            res = service.send_text_message(number, message)
        except Exception as exc:  # network errors etc.
            res = {'success': False, 'error': str(exc)}
        if not res.get('success'):
            logger.warning("Stock alert to %s failed: %s", number, res.get('error'))
        results.append((number, res))
    return results


def _format_stock_lines(recs):
    lines = []
    for r in recs:
        flag = ' (LOW)' if r['is_low'] else ''
        cover = f", ~{int(r['days_cover'])}d cover" if r['days_cover'] is not None else ''
        lines.append(f"- {r['cylinder_size'].name}: {r['full']} full / {r['empties']} empty{cover}{flag}")
    return "\n".join(lines)


def build_stock_received_message(purchase):
    recs = reorder_recommendations()
    item_lines = "\n".join(
        f"- {i.cylinder_size.name}: +{i.quantity} full" + (f", {i.empties_returned} empties returned" if i.empties_returned else '')
        for i in purchase.items.select_related('cylinder_size')
    )
    supplier = purchase.supplier.name if purchase.supplier else 'supplier'
    return (
        f"NEW STOCK RECEIVED ({purchase.purchase_number})\n"
        f"From: {supplier} on {purchase.date.strftime('%d %b %Y')}\n"
        f"{item_lines}\n\n"
        f"Stock on hand now:\n{_format_stock_lines(recs)}"
    )


def send_stock_received_alert(purchase):
    from ..models_stock import StockAlertSettings
    settings = StockAlertSettings.load()
    if not settings.notify_on_stock_received:
        return []
    return _send_whatsapp_to_recipients(build_stock_received_message(purchase), settings)


def build_low_stock_message(low_recs, settings):
    lines = []
    for r in low_recs:
        cover = f"~{int(r['days_cover'])} days cover" if r['days_cover'] is not None else 'no recent sales'
        lines.append(
            f"- {r['cylinder_size'].name}: {r['full']} full (reorder level {r['reorder_level']}), "
            f"avg {r['avg_daily']:.1f}/day over {settings.sales_history_days}d, {cover}. "
            f"Suggest ordering {r['suggested_order_qty']}. Empties on hand: {r['empties']}."
        )
    return "LOW STOCK ALERT - re-order needed\n" + "\n".join(lines) + \
        f"\n\n(Suggested qty covers {settings.supplier_lead_time_days}d lead time + {settings.safety_stock_days}d safety + {settings.reorder_cover_days}d sales)"


def check_low_stock_and_alert(force=False):
    """
    Check all sizes; send a WhatsApp for those at/below reorder level or
    below the sales-based reorder point. Respects the per-size cooldown unless `force`.
    Returns (low_recs, alerted_recs, send_results).
    """
    from ..models_stock import GasStock, StockAlertSettings

    settings = StockAlertSettings.load()
    recs = reorder_recommendations(settings)
    low = [r for r in recs if r['is_low']]
    if not low or not settings.notify_on_low_stock:
        return low, [], []

    now = timezone.now()
    cooldown = timedelta(hours=settings.low_stock_alert_cooldown_hours)
    to_alert = []
    for r in low:
        stock = r['stock']
        if force or not stock or not stock.last_low_stock_alert_at or now - stock.last_low_stock_alert_at >= cooldown:
            to_alert.append(r)
    if not to_alert:
        return low, [], []

    results = _send_whatsapp_to_recipients(build_low_stock_message(to_alert, settings), settings)
    if results and any(res.get('success') for _, res in results):
        GasStock.objects.filter(cylinder_size__in=[r['cylinder_size'] for r in to_alert]).update(last_low_stock_alert_at=now)
    return low, to_alert, results
