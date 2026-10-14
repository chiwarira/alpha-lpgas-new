"""
Stock management views: dashboard, receiving stock, stocktake, sales report,
movements and WhatsApp alert settings.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .models_accounting import Supplier
from .models_stock import CylinderSize, GasStock, StockMovement, StockPurchase, StockAlertSettings
from .services import stock_service


def _active_sizes():
    return list(CylinderSize.objects.filter(is_active=True))


def _parse_date(value, default):
    try:
        return datetime.strptime(value, '%Y-%m-%d').date() if value else default
    except ValueError:
        return default


class StockAlertSettingsForm(forms.ModelForm):
    class Meta:
        model = StockAlertSettings
        fields = [
            'alerts_enabled', 'whatsapp_numbers', 'notify_on_stock_received', 'notify_on_low_stock',
            'low_stock_alert_cooldown_hours', 'sales_history_days', 'supplier_lead_time_days',
            'safety_stock_days', 'reorder_cover_days',
        ]
        widgets = {
            'whatsapp_numbers': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '27821234567, 27831234567'}),
            'low_stock_alert_cooldown_hours': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'sales_history_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'supplier_lead_time_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'safety_stock_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'reorder_cover_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'alerts_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_on_stock_received': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_on_low_stock': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


@login_required
def stock_dashboard(request):
    recs = stock_service.reorder_recommendations()
    summary = stock_service.quick_sales_summary()
    sizes = _active_sizes()
    recent_movements = StockMovement.objects.select_related('cylinder_size', 'invoice').order_by('-created_at')[:15]
    recent_purchases = StockPurchase.objects.select_related('supplier').prefetch_related('items__cylinder_size').order_by('-date', '-created_at')[:5]
    settings_obj = StockAlertSettings.load()

    return render(request, 'core/stock/dashboard.html', {
        'recs': recs,
        'low_recs': [r for r in recs if r['is_low']],
        'summary': summary,
        'sizes': sizes,
        'total_full': sum(r['full'] for r in recs),
        'total_empty': sum(r['empties'] for r in recs),
        'recent_movements': recent_movements,
        'recent_purchases': recent_purchases,
        'settings': settings_obj,
        'alerts_configured': bool(settings_obj.recipient_numbers),
    })


@login_required
def stock_receive(request):
    """Record new stock from a supplier (full cylinders in, empties out)."""
    sizes = _active_sizes()
    suppliers = Supplier.objects.filter(is_active=True).order_by('name')
    stocks = {s.cylinder_size_id: s for s in GasStock.objects.all()}

    if request.method == 'POST':
        received_on = _parse_date(request.POST.get('date'), date.today())
        supplier = Supplier.objects.filter(pk=request.POST.get('supplier') or None).first()
        lines = []
        for cs in sizes:
            qty = request.POST.get(f'qty_{cs.id}') or 0
            empties = request.POST.get(f'empties_{cs.id}') or 0
            cost = request.POST.get(f'cost_{cs.id}') or '0'
            try:
                qty, empties, cost = int(qty), int(empties), Decimal(cost)
            except (ValueError, InvalidOperation):
                messages.error(request, f'Invalid quantity for {cs.name}.')
                break
            if qty < 0 or empties < 0:
                messages.error(request, f'Quantities for {cs.name} cannot be negative.')
                break
            if qty:
                lines.append({'cylinder_size': cs, 'quantity': qty, 'empties_returned': empties, 'unit_cost': cost})
        else:
            if not lines:
                messages.error(request, 'Enter at least one quantity received.')
            else:
                purchase = stock_service.receive_stock(
                    received_on, lines, supplier=supplier,
                    invoice_number=request.POST.get('invoice_number', ''),
                    notes=request.POST.get('notes', ''), user=request.user,
                    send_alert=request.POST.get('send_alert') == 'on',
                )
                messages.success(request, f'Stock received: {purchase.purchase_number} ({purchase.total_cylinders} cylinders).')
                return redirect('accounting_forms:stock_dashboard')

    return render(request, 'core/stock/receive.html', {
        'sizes': sizes,
        'suppliers': suppliers,
        'stocks': stocks,
        'today': date.today(),
        'alerts_configured': bool(StockAlertSettings.load().recipient_numbers),
    })


@login_required
def stock_adjust(request):
    """Stocktake: set actual counts of full and empty cylinders per size."""
    sizes = _active_sizes()
    stocks = {s.cylinder_size_id: s for s in GasStock.objects.all()}
    for cs in sizes:
        if cs.id not in stocks:
            stocks[cs.id] = GasStock.objects.create(cylinder_size=cs)

    if request.method == 'POST':
        counts = []
        reorder_updates = []
        try:
            for cs in sizes:
                full = request.POST.get(f'full_{cs.id}', '').strip()
                empty = request.POST.get(f'empty_{cs.id}', '').strip()
                reorder = request.POST.get(f'reorder_{cs.id}', '').strip()
                counts.append({
                    'cylinder_size': cs,
                    'full_quantity': int(full) if full != '' else None,
                    'empty_quantity': int(empty) if empty != '' else None,
                })
                if reorder != '':
                    reorder_updates.append((cs, int(reorder)))
        except ValueError:
            messages.error(request, 'All counts must be whole numbers.')
        else:
            movements = stock_service.set_stock_levels(counts, user=request.user, notes=request.POST.get('notes') or 'Stocktake')
            for cs, level in reorder_updates:
                GasStock.objects.filter(cylinder_size=cs).update(reorder_level=level)
            messages.success(request, f'Stock levels updated ({len(movements)} adjustment(s) recorded).')
            return redirect('accounting_forms:stock_dashboard')

    rows = [{'size': cs, 'stock': stocks[cs.id]} for cs in sizes]
    return render(request, 'core/stock/adjust.html', {'rows': rows})


@login_required
def stock_sales_report(request):
    """Tanks sold (refills) and cylinders sold (deposits) per day/week/month/custom."""
    today = date.today()
    range_type = request.GET.get('range', 'daily')
    ref = _parse_date(request.GET.get('date'), today)
    if range_type == 'monthly':
        ref = _parse_date((request.GET.get('month') or today.strftime('%Y-%m')) + '-01', today.replace(day=1))
    elif range_type == 'yearly':
        try:
            ref = date(int(request.GET.get('year', today.year)), 1, 1)
        except ValueError:
            ref = date(today.year, 1, 1)
    start, end = (_parse_date(request.GET.get('date_from'), today), _parse_date(request.GET.get('date_to'), today))
    start_date, end_date, label = stock_service.period_bounds(range_type, ref=ref, start=start, end=end)

    group = {'daily': 'day', 'weekly': 'day', 'monthly': 'day', 'yearly': 'month', 'custom': 'day'}[range_type]
    if range_type == 'custom' and (end_date - start_date).days > 62:
        group = 'week'

    sizes = _active_sizes()
    refills = stock_service.sales_by_size(start_date, end_date, 'exchange')
    tanks = stock_service.sales_by_size(start_date, end_date, 'deposit')
    refunds = stock_service.sales_by_size(start_date, end_date, 'deposit_refund')
    refill_rows = stock_service.sales_timeline(start_date, end_date, 'exchange', group)
    tank_rows = stock_service.sales_timeline(start_date, end_date, 'deposit', group)

    # Merge timelines so each period shows refills and tanks side by side
    merged = {}
    for r in refill_rows:
        merged.setdefault(r['period'], {'period': r['period'], 'refills': {}, 'refills_total': 0, 'tanks': {}, 'tanks_total': 0})
        merged[r['period']]['refills'] = r['sizes']
        merged[r['period']]['refills_total'] = r['total']
    for r in tank_rows:
        merged.setdefault(r['period'], {'period': r['period'], 'refills': {}, 'refills_total': 0, 'tanks': {}, 'tanks_total': 0})
        merged[r['period']]['tanks'] = r['sizes']
        merged[r['period']]['tanks_total'] = r['total']
    timeline = sorted(merged.values(), key=lambda b: b['period'], reverse=True)
    for row in timeline:
        row['refill_cells'] = [row['refills'].get(cs.name, 0) for cs in sizes]
        row['tank_cells'] = [row['tanks'].get(cs.name, 0) for cs in sizes]

    size_totals = [{
        'size': cs,
        'refills': refills.get(cs, 0),
        'tanks': tanks.get(cs, 0),
        'refunds': refunds.get(cs, 0),
        'gas_kg': refills.get(cs, 0) * cs.weight_kg,
    } for cs in sizes]

    # Navigation helpers
    if range_type == 'weekly':
        prev_ref, next_ref = ref - timedelta(days=7), ref + timedelta(days=7)
    elif range_type == 'monthly':
        prev_ref = (ref.replace(day=1) - timedelta(days=1)).replace(day=1)
        next_ref = (ref.replace(day=28) + timedelta(days=4)).replace(day=1)
    elif range_type == 'yearly':
        prev_ref, next_ref = date(ref.year - 1, 1, 1), date(ref.year + 1, 1, 1)
    else:
        prev_ref, next_ref = ref - timedelta(days=1), ref + timedelta(days=1)

    return render(request, 'core/stock/sales_report.html', {
        'range_type': range_type,
        'ref': ref,
        'prev_ref': prev_ref,
        'next_ref': next_ref,
        'start_date': start_date,
        'end_date': end_date,
        'label': label,
        'group': group,
        'sizes': sizes,
        'size_totals': size_totals,
        'refills_total': sum(refills.values()),
        'tanks_total': sum(tanks.values()),
        'refunds_total': sum(refunds.values()),
        'gas_kg_total': sum(t['gas_kg'] for t in size_totals),
        'timeline': timeline,
        'empty_colspan': 2 * len(sizes) + 3,
        'today': today,
    })


@login_required
def stock_movements(request):
    qs = StockMovement.objects.select_related('cylinder_size', 'invoice', 'supplier', 'created_by').order_by('-date', '-created_at')
    size_id = request.GET.get('size')
    mtype = request.GET.get('type')
    date_from = _parse_date(request.GET.get('date_from'), None)
    date_to = _parse_date(request.GET.get('date_to'), None)
    if size_id:
        qs = qs.filter(cylinder_size_id=size_id)
    if mtype:
        qs = qs.filter(movement_type=mtype)
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)
    page = Paginator(qs, 50).get_page(request.GET.get('page'))
    return render(request, 'core/stock/movements.html', {
        'page': page,
        'sizes': _active_sizes(),
        'types': StockMovement.MOVEMENT_TYPE_CHOICES,
        'filters': {'size': size_id or '', 'type': mtype or '', 'date_from': request.GET.get('date_from', ''), 'date_to': request.GET.get('date_to', '')},
    })


@login_required
def stock_purchase_detail(request, pk):
    purchase = get_object_or_404(StockPurchase.objects.select_related('supplier').prefetch_related('items__cylinder_size'), pk=pk)
    return render(request, 'core/stock/purchase_detail.html', {'purchase': purchase})


@login_required
def stock_settings(request):
    settings_obj = StockAlertSettings.load()
    if request.method == 'POST':
        form = StockAlertSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Stock alert settings saved.')
            return redirect('accounting_forms:stock_settings')
    else:
        form = StockAlertSettingsForm(instance=settings_obj)
    return render(request, 'core/stock/settings.html', {
        'form': form,
        'settings': settings_obj,
        'recipients': settings_obj.recipient_numbers,
        'recs': stock_service.reorder_recommendations(settings_obj),
    })


@login_required
@require_POST
def stock_send_test_alert(request):
    settings_obj = StockAlertSettings.load()
    if not settings_obj.recipient_numbers:
        messages.error(request, 'Add at least one WhatsApp number first.')
        return redirect('accounting_forms:stock_settings')
    recs = stock_service.reorder_recommendations(settings_obj)
    msg = "STOCK ALERT TEST - Alpha LPGas\nCurrent stock:\n" + stock_service._format_stock_lines(recs)
    results = stock_service._send_whatsapp_to_recipients(msg, settings_obj)
    _report_send_results(request, results)
    return redirect('accounting_forms:stock_settings')


@login_required
@require_POST
def stock_run_low_stock_check(request):
    low, alerted, results = stock_service.check_low_stock_and_alert(force=True)
    if not low:
        messages.info(request, 'All cylinder sizes are above their reorder levels. No alert sent.')
    else:
        names = ', '.join(r['cylinder_size'].name for r in low)
        messages.warning(request, f'Low stock: {names}.')
        _report_send_results(request, results)
    return redirect(request.POST.get('next') or 'accounting_forms:stock_dashboard')


def _report_send_results(request, results):
    if not results:
        messages.error(request, 'No WhatsApp message was sent. Check that alerts are enabled and numbers are configured.')
        return
    ok = [n for n, r in results if r.get('success')]
    failed = [(n, f"{r.get('error')} {r.get('response') or ''}".strip()) for n, r in results if not r.get('success')]
    if ok:
        messages.success(request, f'WhatsApp sent to {", ".join(ok)}.')
    for n, err in failed:
        messages.error(request, f'Failed to send to {n}: {err}')
