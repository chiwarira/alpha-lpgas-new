"""
Fleet management views: vehicles, service history and daily driver assignments.
"""
from datetime import date, datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import Driver
from .models_fleet import Vehicle, VehicleServiceRecord, VehicleAssignment, DriverStockCount
from .models_stock import CylinderSize
from .forms import VehicleForm, VehicleServiceRecordForm


def _parse_date(value, default):
    try:
        return datetime.strptime(value, '%Y-%m-%d').date() if value else default
    except ValueError:
        return default


@login_required
def vehicle_list(request):
    """List all fleet vehicles with search and filtering"""
    vehicles = Vehicle.objects.all()

    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('type', '')

    if search_query:
        vehicles = vehicles.filter(
            Q(registration_number__icontains=search_query) |
            Q(vin_number__icontains=search_query) |
            Q(engine_number__icontains=search_query) |
            Q(make_model__icontains=search_query)
        )

    if status_filter:
        vehicles = vehicles.filter(status=status_filter)
    if type_filter:
        vehicles = vehicles.filter(vehicle_type=type_filter)

    vehicles = vehicles.order_by('registration_number')

    total_vehicles = Vehicle.objects.count()
    active_count = Vehicle.objects.filter(status='active', is_active=True).count()
    in_maintenance_count = Vehicle.objects.filter(status='in_maintenance').count()

    # Vehicles due or overdue for service
    service_due = Vehicle.objects.filter(
        next_service_due_date__lte=date.today(), is_active=True
    ).order_by('next_service_due_date')

    return render(request, 'core/vehicle_list.html', {
        'vehicles': vehicles,
        'total_vehicles': total_vehicles,
        'active_count': active_count,
        'in_maintenance_count': in_maintenance_count,
        'service_due': service_due,
        'search_query': search_query,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'type_choices': Vehicle.VEHICLE_TYPE_CHOICES,
        'status_choices': Vehicle.STATUS_CHOICES,
    })


@login_required
def vehicle_create(request):
    """Register a new vehicle"""
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save()
            messages.success(request, f'Vehicle {vehicle.registration_number} registered successfully!')
            return redirect('accounting_forms:vehicle_detail', pk=vehicle.pk)
    else:
        form = VehicleForm()

    return render(request, 'core/vehicle_form.html', {
        'form': form,
        'title': 'Register Vehicle',
        'is_edit': False,
    })


@login_required
def vehicle_edit(request, pk):
    """Edit an existing vehicle"""
    vehicle = get_object_or_404(Vehicle, pk=pk)

    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            vehicle = form.save()
            messages.success(request, f'Vehicle {vehicle.registration_number} updated successfully!')
            return redirect('accounting_forms:vehicle_detail', pk=vehicle.pk)
    else:
        form = VehicleForm(instance=vehicle)

    return render(request, 'core/vehicle_form.html', {
        'form': form,
        'vehicle': vehicle,
        'title': f'Edit {vehicle.registration_number}',
        'is_edit': True,
    })


@login_required
def vehicle_detail(request, pk):
    """Vehicle details, service history and assignment history"""
    vehicle = get_object_or_404(Vehicle, pk=pk)

    service_records = vehicle.service_records.select_related('created_by').all()
    assignments = vehicle.driver_assignments.select_related('driver__user', 'vehicle').order_by('-date')[:30]
    default_drivers = vehicle.default_for_drivers.select_related('user').filter(is_active=True)
    service_form = VehicleServiceRecordForm(initial={'service_date': date.today()})

    return render(request, 'core/vehicle_detail.html', {
        'vehicle': vehicle,
        'service_records': service_records,
        'assignments': assignments,
        'default_drivers': default_drivers,
        'service_form': service_form,
    })


@login_required
@require_POST
def vehicle_service_add(request, pk):
    """Log a service record for a vehicle"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    form = VehicleServiceRecordForm(request.POST)
    if form.is_valid():
        record = form.save(commit=False)
        record.vehicle = vehicle
        record.created_by = request.user
        record.save()
        messages.success(request, f'Service on {record.service_date} logged for {vehicle.registration_number}')
    else:
        messages.error(request, 'Could not save the service record. Please check the form.')
    return redirect('accounting_forms:vehicle_detail', pk=pk)


@login_required
@require_POST
def vehicle_service_delete(request, pk, record_pk):
    """Delete a service record"""
    record = get_object_or_404(VehicleServiceRecord, pk=record_pk, vehicle_id=pk)
    record.delete()
    messages.success(request, 'Service record deleted.')
    return redirect('accounting_forms:vehicle_detail', pk=pk)


@login_required
def vehicle_delete(request, pk):
    """Delete a vehicle"""
    vehicle = get_object_or_404(Vehicle, pk=pk)

    if request.method == 'POST':
        reg = vehicle.registration_number
        vehicle.delete()
        messages.success(request, f'Vehicle {reg} deleted successfully!')
        return redirect('accounting_forms:vehicle_list')

    return render(request, 'core/vehicle_confirm_delete.html', {
        'vehicle': vehicle,
    })


@login_required
def vehicle_assignments(request):
    """Daily roster: assign each driver a vehicle for a given date"""
    roster_date = _parse_date(request.GET.get('date'), date.today())

    if request.method == 'POST':
        driver_id = request.POST.get('driver_id')
        vehicle_id = request.POST.get('vehicle_id')
        notes = request.POST.get('notes', '')

        try:
            driver = Driver.objects.get(pk=driver_id, is_active=True)
            vehicle = Vehicle.objects.get(pk=vehicle_id, is_active=True)
            VehicleAssignment.objects.create(
                date=roster_date,
                driver=driver,
                vehicle=vehicle,
                notes=notes,
                created_by=request.user,
            )
            messages.success(
                request,
                f'{driver.user.get_full_name() or driver.user.username} assigned {vehicle.registration_number} for {roster_date}'
            )
        except (Driver.DoesNotExist, Vehicle.DoesNotExist, ValueError, TypeError):
            messages.error(request, 'Invalid driver or vehicle selected')
        except IntegrityError:
            messages.error(request, 'That driver or vehicle is already assigned for this date')

        return redirect(f"{reverse('accounting_forms:vehicle_assignments')}?date={roster_date}")

    assignments = (
        VehicleAssignment.objects
        .filter(date=roster_date)
        .select_related('driver__user', 'vehicle')
        .order_by('driver__user__first_name')
    )

    assigned_driver_ids = assignments.values_list('driver_id', flat=True)
    assigned_vehicle_ids = assignments.values_list('vehicle_id', flat=True)

    available_drivers = (
        Driver.objects.filter(is_active=True)
        .exclude(pk__in=assigned_driver_ids)
        .select_related('user')
        .order_by('user__first_name', 'user__last_name')
    )
    available_vehicles = (
        Vehicle.objects.filter(is_active=True, status='active')
        .exclude(pk__in=assigned_vehicle_ids)
        .order_by('registration_number')
    )

    return render(request, 'core/vehicle_assignments.html', {
        'roster_date': roster_date,
        'assignments': assignments,
        'available_drivers': available_drivers,
        'available_vehicles': available_vehicles,
        'today': date.today(),
    })


@login_required
@require_POST
def vehicle_assignment_delete(request, pk):
    """Remove a daily assignment"""
    assignment = get_object_or_404(VehicleAssignment, pk=pk)
    roster_date = assignment.date
    assignment.delete()
    messages.success(request, 'Assignment removed.')
    return redirect(f"{reverse('accounting_forms:vehicle_assignments')}?date={roster_date}")


@login_required
def driver_stock_report(request):
    """Daily driver cylinder counts: opening / restock / closing per driver."""
    report_date = _parse_date(request.GET.get('date'), date.today())
    sizes = list(CylinderSize.objects.filter(is_active=True).order_by('weight_kg'))

    counts = (
        DriverStockCount.objects
        .filter(date=report_date)
        .select_related('driver__user')
        .prefetch_related('items__cylinder_size')
        .order_by('driver__user__first_name', 'count_type')
    )

    # Build one row per driver with cells aligned to the sizes list
    drivers_map = {}
    for count in counts:
        entry = drivers_map.setdefault(count.driver_id, {
            'driver': count.driver, 'opening': {}, 'restock': {}, 'closing': {},
        })
        for item in count.items.all():
            cell = entry['restock'].setdefault(item.cylinder_size_id, [0, 0]) if count.count_type == 'restock' \
                else entry[count.count_type].setdefault(item.cylinder_size_id, [0, 0])
            cell[0] += item.full
            cell[1] += item.empty

    report_rows = []
    for entry in drivers_map.values():
        cells = [
            {
                'size': size,
                'opening': entry['opening'].get(size.pk),
                'restock': entry['restock'].get(size.pk),
                'closing': entry['closing'].get(size.pk),
            }
            for size in sizes
        ]
        report_rows.append({'driver': entry['driver'], 'cells': cells})

    missing_opening = (
        Driver.objects.filter(is_active=True)
        .exclude(stock_counts__date=report_date, stock_counts__count_type='opening')
        .select_related('user')
        .order_by('user__first_name')
    )

    return render(request, 'core/driver_stock_report.html', {
        'report_date': report_date,
        'sizes': sizes,
        'report_rows': report_rows,
        'missing_opening': missing_opening,
    })
