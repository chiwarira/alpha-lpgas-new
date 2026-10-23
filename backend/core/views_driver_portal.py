"""
Driver Portal Views
Dedicated views for drivers to manage their deliveries
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.staticfiles import finders
from django.http import JsonResponse, FileResponse, Http404
from django.templatetags.static import static
from django.utils import timezone
from django.db.models import Q, Sum
from functools import wraps
from datetime import date
from .models import Driver, Order, Payment
from .models_fleet import DriverStockCount, DriverStockCountItem
from .models_stock import CylinderSize


def driver_manifest(request):
    """PWA manifest so drivers can add the portal to their home screen.
    Served as a view so static() resolves hashed filenames in production."""
    return JsonResponse({
        'name': 'Alpha LPGas Driver',
        'short_name': 'LPGas Driver',
        'description': 'Delivery management for Alpha LPGas drivers',
        'start_url': '/driver/',
        'scope': '/driver/',
        'display': 'standalone',
        'orientation': 'portrait',
        'background_color': '#f8f9fa',
        'theme_color': '#0d6efd',
        'icons': [
            {'src': static('driver/icons/icon-192.png'), 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any'},
            {'src': static('driver/icons/icon-512.png'), 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any'},
        ],
    })


def driver_required(view_func):
    """Decorator to ensure user is a driver"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('driver_portal:login')
        
        try:
            driver = request.user.driver_profile
            if not driver.is_active:
                messages.error(request, 'Your driver account is inactive. Please contact admin.')
                logout(request)
                return redirect('driver_portal:login')
        except Driver.DoesNotExist:
            messages.error(request, 'You do not have driver access. Please contact admin.')
            logout(request)
            return redirect('driver_portal:login')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def stock_check_required(view_func):
    """Redirect to the opening stock check until the driver has submitted
    today's opening count. Applied after driver_required."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        driver = request.user.driver_profile
        has_opening = driver.stock_counts.filter(date=date.today(), count_type='opening').exists()
        if not has_opening:
            return redirect('driver_portal:stock_check')
        return view_func(request, *args, **kwargs)
    return wrapper


def driver_sw(request):
    """Serve the service worker from /driver/sw.js so its registration scope
    covers the whole portal (/static/ paths get hashed in production anyway)."""
    sw_path = finders.find('driver/sw.js')
    if not sw_path:
        raise Http404
    return FileResponse(open(sw_path, 'rb'), content_type='application/javascript')


def driver_login(request):
    """Driver login page"""
    if request.user.is_authenticated:
        # Check if user is a driver
        try:
            driver = request.user.driver_profile
            if driver.is_active:
                return redirect('driver_portal:dashboard')
        except Driver.DoesNotExist:
            pass
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if user is a driver
            try:
                driver = user.driver_profile
                if not driver.is_active:
                    messages.error(request, 'Your driver account is inactive. Please contact admin.')
                    return render(request, 'core/driver_portal/login.html')
                
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                return redirect('driver_portal:dashboard')
            except Driver.DoesNotExist:
                messages.error(request, 'You do not have driver access. Please contact admin.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'core/driver_portal/login.html')


@driver_required
def driver_logout(request):
    """Driver logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('driver_portal:login')


@driver_required
@stock_check_required
def driver_dashboard(request):
    """Driver dashboard showing assigned deliveries"""
    driver = request.user.driver_profile
    today = timezone.now().date()
    
    # Get active deliveries
    active_deliveries = driver.assigned_orders.filter(
        status__in=['pending', 'confirmed', 'preparing', 'out_for_delivery', 'failed']
    ).order_by('estimated_delivery')
    
    # Get today's completed deliveries
    today_completed = driver.assigned_orders.filter(
        status='delivered',
        delivered_at__date=today
    ).count()
    
    # Get pending deliveries (not yet out for delivery)
    pending_deliveries = driver.assigned_orders.filter(
        status__in=['pending', 'confirmed', 'preparing']
    ).count()
    
    # Get deliveries out for delivery
    out_for_delivery = driver.assigned_orders.filter(
        status='out_for_delivery'
    ).count()
    
    # Stock check state for the dashboard buttons
    has_closing = driver.stock_counts.filter(date=today, count_type='closing').exists()
    
    return render(request, 'core/driver_portal/dashboard.html', {
        'driver': driver,
        'active_deliveries': active_deliveries,
        'today_completed': today_completed,
        'pending_deliveries': pending_deliveries,
        'out_for_delivery': out_for_delivery,
        'vehicle_today': driver.get_vehicle_for_date(today),
        'has_closing': has_closing,
    })


@driver_required
@stock_check_required
def driver_deliveries(request):
    """List all deliveries assigned to driver"""
    driver = request.user.driver_profile
    
    # Filter options
    status_filter = request.GET.get('status', 'active')
    
    if status_filter == 'active':
        deliveries = driver.assigned_orders.filter(
            status__in=['pending', 'confirmed', 'preparing', 'out_for_delivery', 'failed']
        )
    elif status_filter == 'completed':
        deliveries = driver.assigned_orders.filter(status='delivered')
    elif status_filter == 'cancelled':
        deliveries = driver.assigned_orders.filter(status='cancelled')
    else:
        deliveries = driver.assigned_orders.all()
    
    deliveries = deliveries.order_by('-created_at')
    
    return render(request, 'core/driver_portal/deliveries.html', {
        'driver': driver,
        'deliveries': deliveries,
        'status_filter': status_filter,
    })


@driver_required
@stock_check_required
def driver_delivery_detail(request, order_id):
    """View delivery details"""
    driver = request.user.driver_profile
    
    # Ensure the order is assigned to this driver
    delivery = get_object_or_404(
        Order.objects.select_related('delivery_zone').prefetch_related('items__product'),
        pk=order_id,
        assigned_driver=driver
    )
    
    return render(request, 'core/driver_portal/delivery_detail.html', {
        'driver': driver,
        'delivery': delivery,
    })


@driver_required
@stock_check_required
def driver_update_status(request, order_id):
    """Update delivery status (handles proof of delivery and failed attempts)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST request required'}, status=400)
    
    driver = request.user.driver_profile
    
    # Ensure the order is assigned to this driver
    delivery = get_object_or_404(Order, pk=order_id, assigned_driver=driver)
    
    new_status = request.POST.get('status')
    
    # Validate status transitions
    valid_statuses = ['out_for_delivery', 'delivered', 'failed']
    
    if new_status not in valid_statuses:
        messages.error(request, 'Invalid status.')
        return redirect('driver_portal:delivery_detail', order_id=order_id)
    
    history_notes = f'Status updated by driver {driver.user.get_full_name()}'
    
    if new_status == 'failed':
        reason = request.POST.get('failure_reason', '').strip()
        if not reason:
            messages.error(request, 'Please provide a reason for the failed delivery.')
            return redirect('driver_portal:delivery_detail', order_id=order_id)
        delivery.delivery_failure_reason = reason
        history_notes = f'Delivery failed: {reason}'
        # Driver becomes available again for other deliveries
        if not driver.get_active_deliveries().exclude(pk=delivery.pk).exists():
            driver.status = 'available'
            driver.save()
    elif new_status == 'delivered':
        delivery.delivered_at = timezone.now()
        delivery.delivery_failure_reason = ''
        
        # Proof of delivery: photo upload + signature captured on canvas
        if request.FILES.get('pod_photo'):
            delivery.pod_photo = request.FILES['pod_photo']
        signature_data = request.POST.get('signature_data', '')
        if signature_data.startswith('data:image/png;base64,'):
            import base64
            from django.core.files.base import ContentFile
            try:
                sig_bytes = base64.b64decode(signature_data.split(',', 1)[1])
                delivery.pod_signature.save(
                    f'sig-{delivery.order_number}.png', ContentFile(sig_bytes), save=False
                )
            except (ValueError, TypeError):
                pass
        
        driver.status = 'available'
        driver.save()
        driver.update_delivery_count()
    elif new_status == 'out_for_delivery':
        driver.status = 'on_delivery'
        driver.save()
    
    delivery.status = new_status
    delivery.save()
    
    # Create status history entry
    from .models import OrderStatusHistory
    OrderStatusHistory.objects.create(
        order=delivery,
        status=new_status,
        notes=history_notes,
        created_by=request.user
    )
    
    messages.success(request, f'Delivery status updated to {delivery.get_status_display()}')
    
    # Return JSON for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'new_status': new_status,
            'status_display': delivery.get_status_display()
        })
    
    return redirect('driver_portal:delivery_detail', order_id=order_id)


@driver_required
@stock_check_required
def driver_collect_cash(request, order_id):
    """Record that the driver collected the cash-on-delivery amount"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST request required'}, status=400)
    
    driver = request.user.driver_profile
    delivery = get_object_or_404(Order, pk=order_id, assigned_driver=driver)
    
    if delivery.payment_method != 'cash':
        messages.error(request, 'This order is not a cash-on-delivery order.')
        return redirect('driver_portal:delivery_detail', order_id=order_id)
    
    if delivery.payment_status == 'paid':
        messages.info(request, 'This order has already been paid.')
        return redirect('driver_portal:delivery_detail', order_id=order_id)
    
    delivery.payment_status = 'paid'
    delivery.save()
    
    # Record a Payment so the linked invoice reflects the collection
    invoice = delivery.invoices.first()
    driver_name = driver.user.get_full_name() or driver.user.username
    Payment.objects.create(
        client=delivery.client,
        invoice=invoice,
        payment_date=date.today(),
        amount=delivery.total,
        payment_method='cash',
        notes=f'Cash collected by driver {driver_name} on delivery {delivery.order_number}',
        created_by=request.user,
    )
    
    from .models import OrderStatusHistory
    OrderStatusHistory.objects.create(
        order=delivery,
        status=delivery.status,
        notes=f'Cash payment of R{delivery.total} collected by driver {driver_name}',
        created_by=request.user
    )
    
    messages.success(request, f'Cash of R{delivery.total} recorded as collected.')
    return redirect('driver_portal:delivery_detail', order_id=order_id)


@driver_required
def driver_stock_check(request):
    """Daily cylinder stock count: opening (required before anything else),
    restock (stock added during the day) and closing (end of day) counts."""
    driver = request.user.driver_profile
    today = date.today()
    count_type = request.GET.get('type') or request.POST.get('type') or 'opening'
    if count_type not in ('opening', 'restock', 'closing'):
        count_type = 'opening'
    
    sizes = list(CylinderSize.objects.filter(is_active=True).order_by('weight_kg'))
    
    # Opening count already submitted — only one per day
    opening_done = driver.stock_counts.filter(date=today, count_type='opening').exists()
    if count_type == 'opening' and opening_done:
        return redirect('driver_portal:dashboard')
    
    if request.method == 'POST':
        if count_type == 'restock':
            count = DriverStockCount(driver=driver, date=today, count_type='restock',
                                     notes=request.POST.get('notes', ''), created_by=request.user)
            count.save()
        else:
            count, _ = DriverStockCount.objects.update_or_create(
                driver=driver, date=today, count_type=count_type,
                defaults={'notes': request.POST.get('notes', ''), 'created_by': request.user},
            )
            count.items.all().delete()
        
        for size in sizes:
            try:
                full = int(request.POST.get(f'full_{size.pk}') or 0)
                empty = int(request.POST.get(f'empty_{size.pk}') or 0)
            except ValueError:
                full = empty = 0
            DriverStockCountItem.objects.create(
                count=count, cylinder_size=size, full=max(0, full), empty=max(0, empty)
            )
        
        label = dict(DriverStockCount.COUNT_TYPE_CHOICES)[count_type]
        messages.success(request, f'{label} saved. Thank you!')
        return redirect('driver_portal:dashboard')
    
    # Pre-fill values: closing defaults to opening + restocks so far
    prefill = {}
    if count_type == 'closing':
        totals = DriverStockCountItem.objects.filter(
            count__driver=driver, count__date=today, count__count_type__in=['opening', 'restock']
        ).values('cylinder_size').annotate(full_total=Sum('full'), empty_total=Sum('empty'))
        prefill = {t['cylinder_size']: t for t in totals}
    elif count_type == 'opening':
        existing = DriverStockCount.objects.filter(
            driver=driver, date=today, count_type='opening'
        ).prefetch_related('items').first()
        if existing:
            prefill = {i.cylinder_size_id: {'full_total': i.full, 'empty_total': i.empty} for i in existing.items.all()}
    
    rows = [
        {'size': size, 'full': (prefill.get(size.pk) or {}).get('full_total'), 'empty': (prefill.get(size.pk) or {}).get('empty_total')}
        for size in sizes
    ]
    
    return render(request, 'core/driver_portal/stock_check.html', {
        'driver': driver,
        'rows': rows,
        'count_type': count_type,
        'type_label': dict(DriverStockCount.COUNT_TYPE_CHOICES)[count_type],
        'today': today,
    })


@driver_required
def driver_profile(request):
    """View and update driver profile"""
    driver = request.user.driver_profile
    
    if request.method == 'POST':
        # Update allowed fields
        driver.phone = request.POST.get('phone', driver.phone)
        driver.address = request.POST.get('address', driver.address)
        
        # Update user fields
        request.user.email = request.POST.get('email', request.user.email)
        request.user.save()
        
        driver.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('driver_portal:profile')
    
    # Get statistics
    total_deliveries = driver.total_deliveries
    completed_today = driver.assigned_orders.filter(
        status='delivered',
        delivered_at__date=timezone.now().date()
    ).count()
    
    return render(request, 'core/driver_portal/profile.html', {
        'driver': driver,
        'total_deliveries': total_deliveries,
        'completed_today': completed_today,
        'vehicle_today': driver.get_vehicle_for_date(timezone.now().date()),
    })


@driver_required
def driver_update_location(request):
    """Update driver availability status"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST request required'}, status=400)
    
    driver = request.user.driver_profile
    new_status = request.POST.get('status')
    
    # Validate status
    valid_statuses = ['available', 'on_break', 'off_duty']
    
    if new_status not in valid_statuses:
        return JsonResponse({'error': 'Invalid status'}, status=400)
    
    # Don't allow changing status if driver has active deliveries
    active_deliveries = driver.get_active_deliveries().count()
    if active_deliveries > 0 and new_status in ['off_duty']:
        return JsonResponse({
            'error': f'Cannot go off duty with {active_deliveries} active deliveries'
        }, status=400)
    
    driver.status = new_status
    driver.save()
    
    return JsonResponse({
        'success': True,
        'status': new_status,
        'status_display': driver.get_status_display()
    })
