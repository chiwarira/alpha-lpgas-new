"""
Driver Portal Views
Dedicated views for drivers to manage their deliveries
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from functools import wraps
from .models import Driver, Order


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
def driver_dashboard(request):
    """Driver dashboard showing assigned deliveries"""
    driver = request.user.driver_profile
    
    # Get active deliveries
    active_deliveries = driver.assigned_orders.filter(
        status__in=['confirmed', 'preparing', 'out_for_delivery']
    ).order_by('estimated_delivery')
    
    # Get today's completed deliveries
    today = timezone.now().date()
    today_completed = driver.assigned_orders.filter(
        status='delivered',
        delivered_at__date=today
    ).count()
    
    # Get pending deliveries (confirmed but not yet out for delivery)
    pending_deliveries = driver.assigned_orders.filter(
        status__in=['confirmed', 'preparing']
    ).count()
    
    # Get deliveries out for delivery
    out_for_delivery = driver.assigned_orders.filter(
        status='out_for_delivery'
    ).count()
    
    return render(request, 'core/driver_portal/dashboard.html', {
        'driver': driver,
        'active_deliveries': active_deliveries,
        'today_completed': today_completed,
        'pending_deliveries': pending_deliveries,
        'out_for_delivery': out_for_delivery,
    })


@driver_required
def driver_deliveries(request):
    """List all deliveries assigned to driver"""
    driver = request.user.driver_profile
    
    # Filter options
    status_filter = request.GET.get('status', 'active')
    
    if status_filter == 'active':
        deliveries = driver.assigned_orders.filter(
            status__in=['confirmed', 'preparing', 'out_for_delivery']
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
def driver_update_status(request, order_id):
    """Update delivery status"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST request required'}, status=400)
    
    driver = request.user.driver_profile
    
    # Ensure the order is assigned to this driver
    delivery = get_object_or_404(Order, pk=order_id, assigned_driver=driver)
    
    new_status = request.POST.get('status')
    
    # Validate status transitions
    valid_statuses = ['out_for_delivery', 'delivered']
    
    if new_status not in valid_statuses:
        messages.error(request, 'Invalid status.')
        return redirect('driver_portal:delivery_detail', order_id=order_id)
    
    # Update order status
    old_status = delivery.status
    delivery.status = new_status
    
    # If delivered, set delivered_at timestamp
    if new_status == 'delivered':
        delivery.delivered_at = timezone.now()
        # Update driver status to available
        driver.status = 'available'
        driver.save()
        # Update delivery count
        driver.update_delivery_count()
    elif new_status == 'out_for_delivery':
        # Update driver status
        driver.status = 'on_delivery'
        driver.save()
    
    delivery.save()
    
    # Create status history entry
    from .models import OrderStatusHistory
    OrderStatusHistory.objects.create(
        order=delivery,
        status=new_status,
        notes=f'Status updated by driver {driver.user.get_full_name()}',
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
