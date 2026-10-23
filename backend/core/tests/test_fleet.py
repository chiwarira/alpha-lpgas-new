import tempfile
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import Client, Product, Invoice, InvoiceItem, Driver, Order, Payment
from core.models_fleet import Vehicle, VehicleServiceRecord, VehicleAssignment, DriverStockCount
from core.models_stock import CylinderSize


class FleetTestBase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('staff', password='pw')
        self.driver_user = User.objects.create_user('driver1', password='pw', first_name='John', last_name='Doe')
        self.driver = Driver.objects.create(user=self.driver_user, phone='0821234567')
        self.vehicle = Vehicle.objects.create(
            registration_number='ABC 123 GP', vehicle_type='bakkie', make_model='Toyota Hilux'
        )
        self.other_vehicle = Vehicle.objects.create(registration_number='XYZ 789 GP')
        self.client_obj = Client.objects.create(name='Test Client', phone='0821234567')
        self.product = Product.objects.create(name='19kg Cylinder', sku='19KGCYL', unit_price=850)
        self.size19 = CylinderSize.objects.create(name='19kg', weight_kg=19)
        self.size9 = CylinderSize.objects.create(name='9kg', weight_kg=9)

    def make_order(self, **kwargs):
        defaults = dict(
            client=self.client_obj, customer_name='Test Client', customer_phone='0821234567',
            delivery_address='1 Test St', subtotal=850, total=850,
            payment_method='cash', assigned_driver=self.driver,
        )
        defaults.update(kwargs)
        return Order.objects.create(**defaults)

    def make_opening_count(self):
        count = DriverStockCount.objects.create(driver=self.driver, date=date.today(), count_type='opening')
        count.items.create(cylinder_size=self.size19, full=10, empty=2)
        return count


class VehicleAssignmentTests(FleetTestBase):
    def test_driver_cannot_have_two_vehicles_same_day(self):
        VehicleAssignment.objects.create(date=date.today(), driver=self.driver, vehicle=self.vehicle)
        with self.assertRaises(IntegrityError):
            VehicleAssignment.objects.create(date=date.today(), driver=self.driver, vehicle=self.other_vehicle)

    def test_vehicle_cannot_go_to_two_drivers_same_day(self):
        other_user = User.objects.create_user('driver2', password='pw')
        other_driver = Driver.objects.create(user=other_user, phone='0829999999')
        VehicleAssignment.objects.create(date=date.today(), driver=self.driver, vehicle=self.vehicle)
        with self.assertRaises(IntegrityError):
            VehicleAssignment.objects.create(date=date.today(), driver=other_driver, vehicle=self.vehicle)

    def test_same_assignment_allowed_on_different_days(self):
        VehicleAssignment.objects.create(date=date.today(), driver=self.driver, vehicle=self.vehicle)
        VehicleAssignment.objects.create(
            date=date.today() + timedelta(days=1), driver=self.driver, vehicle=self.vehicle
        )

    def test_get_vehicle_for_date_uses_assignment(self):
        self.driver.default_vehicle = self.other_vehicle
        self.driver.save()
        VehicleAssignment.objects.create(date=date.today(), driver=self.driver, vehicle=self.vehicle)
        self.assertEqual(self.driver.get_vehicle_for_date(date.today()), self.vehicle)

    def test_get_vehicle_for_date_falls_back_to_default(self):
        self.driver.default_vehicle = self.other_vehicle
        self.driver.save()
        self.assertEqual(self.driver.get_vehicle_for_date(date.today()), self.other_vehicle)


class VehicleServiceTests(FleetTestBase):
    def test_service_record_updates_vehicle_dates(self):
        next_due = date.today() + timedelta(days=180)
        VehicleServiceRecord.objects.create(
            vehicle=self.vehicle, service_date=date.today(), description='Oil change',
            next_service_due_date=next_due,
        )
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.last_service_date, date.today())
        self.assertEqual(self.vehicle.next_service_due_date, next_due)

    def test_latest_record_wins_and_delete_reverts(self):
        old = VehicleServiceRecord.objects.create(
            vehicle=self.vehicle, service_date=date.today() - timedelta(days=30), description='Old service'
        )
        latest = VehicleServiceRecord.objects.create(
            vehicle=self.vehicle, service_date=date.today(), description='New service'
        )
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.last_service_date, date.today())

        latest.delete()
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.last_service_date, old.service_date)
        self.assertIsNone(self.vehicle.next_service_due_date)


class InvoiceOrderDriverTests(FleetTestBase):
    def test_order_created_from_invoice_copies_driver_and_vehicle(self):
        invoice = Invoice.objects.create(
            client=self.client_obj, issue_date=date.today(), due_date=date.today(),
            assigned_driver=self.driver, assigned_vehicle=self.vehicle, created_by=self.user,
        )
        InvoiceItem.objects.create(invoice=invoice, product=self.product, quantity=1, unit_price=850)

        invoice.refresh_from_db()
        self.assertIsNotNone(invoice.order)
        self.assertEqual(invoice.order.assigned_driver, self.driver)
        self.assertEqual(invoice.order.assigned_vehicle, self.vehicle)

    def test_order_driver_updates_when_invoice_driver_changes(self):
        invoice = Invoice.objects.create(
            client=self.client_obj, issue_date=date.today(), due_date=date.today(),
            assigned_driver=self.driver, assigned_vehicle=self.vehicle, created_by=self.user,
        )
        InvoiceItem.objects.create(invoice=invoice, product=self.product, quantity=1, unit_price=850)

        other_user = User.objects.create_user('driver2', password='pw')
        other_driver = Driver.objects.create(user=other_user, phone='0829999999')
        invoice.assigned_driver = other_driver
        invoice.assigned_vehicle = self.other_vehicle
        invoice.save()

        invoice.order.refresh_from_db()
        self.assertEqual(invoice.order.assigned_driver, other_driver)
        self.assertEqual(invoice.order.assigned_vehicle, self.other_vehicle)


class InvoiceCreateViewTests(FleetTestBase):
    def _post_invoice(self, extra=None):
        data = {
            'client': self.client_obj.pk,
            'issue_date': date.today().isoformat(),
            'payment_terms': 'immediate',
            'assigned_driver': self.driver.pk,
            'assigned_vehicle': '',
            'discount_amount': '0',
            'notes': '', 'delivery_note': '', 'whatsapp_invoice_message': '',
            'items-TOTAL_FORMS': '1', 'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '0', 'items-MAX_NUM_FORMS': '1000',
            'items-0-product': self.product.pk, 'items-0-quantity': '1',
        }
        if extra:
            data.update(extra)
        return self.client.post(reverse('accounting_forms:invoice_create'), data)

    def test_invoice_create_requires_driver(self):
        self.client.force_login(self.user)
        response = self._post_invoice({'assigned_driver': ''})
        self.assertEqual(response.status_code, 200)  # form re-rendered with errors
        self.assertFalse(Invoice.objects.exists())

    def test_invoice_create_assigns_vehicle_from_roster(self):
        VehicleAssignment.objects.create(date=date.today(), driver=self.driver, vehicle=self.vehicle)
        self.client.force_login(self.user)
        response = self._post_invoice()
        self.assertEqual(response.status_code, 302)

        invoice = Invoice.objects.latest('created_at')
        self.assertEqual(invoice.assigned_driver, self.driver)
        self.assertEqual(invoice.assigned_vehicle, self.vehicle)
        # ...and it trickles down to the generated order
        self.assertEqual(invoice.order.assigned_driver, self.driver)
        self.assertEqual(invoice.order.assigned_vehicle, self.vehicle)

    def test_invoice_create_vehicle_override_beats_roster(self):
        VehicleAssignment.objects.create(date=date.today(), driver=self.driver, vehicle=self.vehicle)
        self.client.force_login(self.user)
        response = self._post_invoice({'assigned_vehicle': self.other_vehicle.pk})
        self.assertEqual(response.status_code, 302)

        invoice = Invoice.objects.latest('created_at')
        self.assertEqual(invoice.assigned_vehicle, self.other_vehicle)


class DriverStockCountTests(FleetTestBase):
    def test_one_opening_and_one_closing_per_day(self):
        self.make_opening_count()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                DriverStockCount.objects.create(driver=self.driver, date=date.today(), count_type='opening')
        # Closing is a different type - allowed
        DriverStockCount.objects.create(driver=self.driver, date=date.today(), count_type='closing')

    def test_multiple_restocks_allowed(self):
        DriverStockCount.objects.create(driver=self.driver, date=date.today(), count_type='restock')
        DriverStockCount.objects.create(driver=self.driver, date=date.today(), count_type='restock')


class StockCheckViewTests(FleetTestBase):
    def test_dashboard_redirects_to_stock_check_without_opening(self):
        self.client.force_login(self.driver_user)
        response = self.client.get(reverse('driver_portal:dashboard'))
        self.assertRedirects(response, reverse('driver_portal:stock_check'))

    def test_opening_count_submit_unlocks_dashboard(self):
        self.client.force_login(self.driver_user)
        response = self.client.post(reverse('driver_portal:stock_check'), {
            'type': 'opening',
            f'full_{self.size19.pk}': '10', f'empty_{self.size19.pk}': '2',
            f'full_{self.size9.pk}': '5', f'empty_{self.size9.pk}': '1',
        })
        self.assertRedirects(response, reverse('driver_portal:dashboard'))

        count = DriverStockCount.objects.get(driver=self.driver, count_type='opening')
        self.assertEqual(count.items.get(cylinder_size=self.size19).full, 10)
        self.assertEqual(count.items.get(cylinder_size=self.size19).empty, 2)

        # Dashboard now accessible
        self.assertEqual(self.client.get(reverse('driver_portal:dashboard')).status_code, 200)
        # Opening page redirects to dashboard once submitted
        self.assertRedirects(
            self.client.get(reverse('driver_portal:stock_check')),
            reverse('driver_portal:dashboard'),
        )


class DeliveryStatusFlowTests(FleetTestBase):
    def setUp(self):
        super().setUp()
        self.make_opening_count()
        self.client.force_login(self.driver_user)

    def _update(self, order, **data):
        return self.client.post(reverse('driver_portal:update_status', args=[order.pk]), data)

    def test_failed_requires_reason(self):
        order = self.make_order(status='out_for_delivery')
        self._update(order, status='failed')
        order.refresh_from_db()
        self.assertEqual(order.status, 'out_for_delivery')  # unchanged without reason

        self._update(order, status='failed', failure_reason='Customer not home')
        order.refresh_from_db()
        self.assertEqual(order.status, 'failed')
        self.assertEqual(order.delivery_failure_reason, 'Customer not home')

    def test_failed_order_can_be_reattempted(self):
        order = self.make_order(status='failed', delivery_failure_reason='Gate locked')
        self._update(order, status='out_for_delivery')
        order.refresh_from_db()
        self.assertEqual(order.status, 'out_for_delivery')

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix='pod-test-'))
    def test_delivered_with_signature(self):
        order = self.make_order(status='out_for_delivery')
        # 1x1 transparent PNG
        sig = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='
        self._update(order, status='delivered', signature_data=sig)
        order.refresh_from_db()
        self.assertEqual(order.status, 'delivered')
        self.assertIsNotNone(order.delivered_at)
        self.assertTrue(order.pod_signature.name.endswith('.png'))

    def test_collect_cash_marks_paid_and_records_payment(self):
        invoice = Invoice.objects.create(
            client=self.client_obj, issue_date=date.today(), due_date=date.today(),
            assigned_driver=self.driver, created_by=self.user,
        )
        InvoiceItem.objects.create(invoice=invoice, product=self.product, quantity=1, unit_price=850)
        order = invoice.order
        order.assigned_driver = self.driver
        order.payment_method = 'cash'
        order.save()

        response = self.client.post(reverse('driver_portal:collect_cash', args=[order.pk]))
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.payment_status, 'paid')

        payment = Payment.objects.get(invoice=invoice)
        self.assertEqual(payment.amount, order.total)
        self.assertEqual(payment.payment_method, 'cash')
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'paid')
