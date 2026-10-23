from django.db import migrations


TYPE_MAP = {
    'bakkie': 'bakkie',
    'van': 'van',
    'truck': 'truck',
    'motorcycle': 'motorcycle',
    'bike': 'motorcycle',
}


def forwards(apps, schema_editor):
    """Create a Vehicle from each driver's embedded vehicle fields and set it
    as the driver's default vehicle."""
    Driver = apps.get_model('core', 'Driver')
    Vehicle = apps.get_model('core', 'Vehicle')

    existing_regs = set(Vehicle.objects.values_list('registration_number', flat=True))
    for driver in Driver.objects.all():
        reg = (driver.vehicle_registration or '').strip()
        if not reg:
            continue

        vehicle = Vehicle.objects.filter(registration_number__iexact=reg).first()
        if vehicle is None and reg not in existing_regs:
            vtype = (driver.vehicle_type or '').strip().lower()
            vehicle = Vehicle.objects.create(
                registration_number=reg,
                vehicle_type=TYPE_MAP.get(vtype, 'other'),
                make_model=driver.vehicle_make_model or '',
            )
            existing_regs.add(reg)

        if vehicle:
            Driver.objects.filter(pk=driver.pk).update(default_vehicle=vehicle)


def backwards(apps, schema_editor):
    """Copy default vehicle details back onto the driver fields."""
    Driver = apps.get_model('core', 'Driver')
    for driver in Driver.objects.select_related('default_vehicle').all():
        vehicle = driver.default_vehicle
        if not vehicle:
            continue
        Driver.objects.filter(pk=driver.pk).update(
            vehicle_type=vehicle.get_vehicle_type_display(),
            vehicle_registration=vehicle.registration_number,
            vehicle_make_model=vehicle.make_model,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0046_fleet_vehicles_assignments'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
