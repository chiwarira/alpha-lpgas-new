from datetime import date, timedelta
from decimal import Decimal
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import Client, Product, Invoice, InvoiceItem
from core.models_stock import CylinderSize, GasStock, StockMovement, StockAlertSettings
from core.services import stock_service


class StockTestBase(TestCase):
    def setUp(self):
        # Order auto-generation uses second-resolution order numbers; it is irrelevant here
        from django.db.models.signals import post_save
        from core import signals as core_signals
        post_save.disconnect(core_signals.sync_invoice_item_to_order, sender=InvoiceItem)
        self.addCleanup(post_save.connect, core_signals.sync_invoice_item_to_order, sender=InvoiceItem)
        self.user = User.objects.create_user('staff', password='pw')
        self.size19 = CylinderSize.objects.create(name='19kg', weight_kg=19)
        self.size14 = CylinderSize.objects.create(name='14kg', weight_kg=14)
        self.stock19 = GasStock.objects.create(cylinder_size=self.size19, quantity=20, empty_quantity=5, reorder_level=5)
        self.stock14 = GasStock.objects.create(cylinder_size=self.size14, quantity=10, empty_quantity=2, reorder_level=5)
        self.refill19 = Product.objects.create(name='19kg Cylinder', sku='19KGCYL', unit_price=850, cylinder_size=self.size19, stock_effect='exchange')
        self.deposit19 = Product.objects.create(name='Cylinder Deposit 19kg', sku='DEP019', unit_price=900, cylinder_size=self.size19, stock_effect='deposit')
        self.refund19 = Product.objects.create(name='19kg Return', sku='RET019', unit_price=-900, cylinder_size=self.size19, stock_effect='deposit_refund')
        self.hose = Product.objects.create(name='Hose', sku='AC003', unit_price=30)
        self.client_obj = Client.objects.create(name='Test Client', phone='0821234567')

    def make_invoice(self, issue_date=None):
        return Invoice.objects.create(client=self.client_obj, issue_date=issue_date or date.today(),
                                      due_date=issue_date or date.today(), created_by=self.user)

    def refresh(self):
        self.stock19.refresh_from_db()
        self.stock14.refresh_from_db()


class InvoiceStockSyncTests(StockTestBase):
    def test_refill_reduces_full_and_adds_empty(self):
        inv = self.make_invoice()
        item = InvoiceItem.objects.create(invoice=inv, product=self.refill19, quantity=3, unit_price=850, tax_rate=15)
        self.refresh()
        self.assertEqual(self.stock19.quantity, 17)
        self.assertEqual(self.stock19.empty_quantity, 8)
        item.refresh_from_db()
        self.assertTrue(item.stock_deducted)
        m = StockMovement.objects.get(invoice_item=item)
        self.assertEqual((m.movement_type, m.quantity, m.empty_change), ('sale', -3, 3))

    def test_deposit_counts_tank_sold_and_removes_empty(self):
        inv = self.make_invoice()
        InvoiceItem.objects.create(invoice=inv, product=self.refill19, quantity=1, unit_price=850, tax_rate=15)
        InvoiceItem.objects.create(invoice=inv, product=self.deposit19, quantity=1, unit_price=900, tax_rate=15)
        self.refresh()
        # Customer bought gas + tank: one full out, no net empty in
        self.assertEqual(self.stock19.quantity, 19)
        self.assertEqual(self.stock19.empty_quantity, 5)

    def test_deposit_refund_adds_empty(self):
        inv = self.make_invoice()
        InvoiceItem.objects.create(invoice=inv, product=self.refund19, quantity=1, unit_price=-900, tax_rate=15)
        self.refresh()
        self.assertEqual(self.stock19.empty_quantity, 6)

    def test_non_stock_product_has_no_effect(self):
        inv = self.make_invoice()
        InvoiceItem.objects.create(invoice=inv, product=self.hose, quantity=2, unit_price=30, tax_rate=15)
        self.refresh()
        self.assertEqual((self.stock19.quantity, self.stock14.quantity), (20, 10))
        self.assertFalse(StockMovement.objects.exists())

    def test_saving_item_twice_does_not_double_deduct(self):
        inv = self.make_invoice()
        item = InvoiceItem.objects.create(invoice=inv, product=self.refill19, quantity=2, unit_price=850, tax_rate=15)
        item.description = 'changed'
        item.save()
        self.refresh()
        self.assertEqual(self.stock19.quantity, 18)
        self.assertEqual(StockMovement.objects.count(), 1)

    def test_quantity_change_adjusts_stock(self):
        inv = self.make_invoice()
        item = InvoiceItem.objects.create(invoice=inv, product=self.refill19, quantity=2, unit_price=850, tax_rate=15)
        item.quantity = 5
        item.save()
        self.refresh()
        self.assertEqual(self.stock19.quantity, 15)
        self.assertEqual(self.stock19.empty_quantity, 10)

    def test_product_change_moves_stock_between_sizes(self):
        refill14 = Product.objects.create(name='14kg Cylinder', sku='14KGCYL', unit_price=690, cylinder_size=self.size14, stock_effect='exchange')
        inv = self.make_invoice()
        item = InvoiceItem.objects.create(invoice=inv, product=self.refill19, quantity=1, unit_price=850, tax_rate=15)
        item.product = refill14
        item.save()
        self.refresh()
        self.assertEqual((self.stock19.quantity, self.stock19.empty_quantity), (20, 5))
        self.assertEqual((self.stock14.quantity, self.stock14.empty_quantity), (9, 3))

    def test_deleting_item_reverses_stock(self):
        inv = self.make_invoice()
        item = InvoiceItem.objects.create(invoice=inv, product=self.refill19, quantity=4, unit_price=850, tax_rate=15)
        item.delete()
        self.refresh()
        self.assertEqual((self.stock19.quantity, self.stock19.empty_quantity), (20, 5))
        self.assertTrue(StockMovement.objects.filter(movement_type='reversal').exists())

    def test_deleting_invoice_reverses_all_items(self):
        inv = self.make_invoice()
        InvoiceItem.objects.create(invoice=inv, product=self.refill19, quantity=4, unit_price=850, tax_rate=15)
        InvoiceItem.objects.create(invoice=inv, product=self.deposit19, quantity=1, unit_price=900, tax_rate=15)
        inv.delete()
        self.refresh()
        self.assertEqual((self.stock19.quantity, self.stock19.empty_quantity), (20, 5))


class ReceiveAndAdjustTests(StockTestBase):
    def test_receive_stock_adds_full_and_removes_returned_empties(self):
        with mock.patch.object(stock_service, 'send_stock_received_alert') as alert:
            purchase = stock_service.receive_stock(
                date.today(),
                [{'cylinder_size': self.size19, 'quantity': 30, 'empties_returned': 5, 'unit_cost': Decimal('400')},
                 {'cylinder_size': self.size14, 'quantity': 0}],
                user=self.user, send_alert=False,
            )
        self.refresh()
        self.assertEqual((self.stock19.quantity, self.stock19.empty_quantity), (50, 0))
        self.assertEqual(self.stock14.quantity, 10)
        self.assertEqual(purchase.total_cylinders, 30)
        self.assertEqual(purchase.total_cost, Decimal('12000'))
        alert.assert_not_called()

    def test_set_stock_levels_creates_adjustments(self):
        movements = stock_service.set_stock_levels([
            {'cylinder_size': self.size19, 'full_quantity': 25, 'empty_quantity': None},
            {'cylinder_size': self.size14, 'full_quantity': None, 'empty_quantity': 7},
        ], user=self.user)
        self.refresh()
        self.assertEqual(len(movements), 2)
        self.assertEqual((self.stock19.quantity, self.stock19.empty_quantity), (25, 5))
        self.assertEqual((self.stock14.quantity, self.stock14.empty_quantity), (10, 7))


class ReportingAndReorderTests(StockTestBase):
    def test_sales_summary_counts_refills_and_tanks(self):
        today = date.today()
        inv_today = self.make_invoice(today)
        InvoiceItem.objects.create(invoice=inv_today, product=self.refill19, quantity=2, unit_price=850, tax_rate=15)
        InvoiceItem.objects.create(invoice=inv_today, product=self.deposit19, quantity=1, unit_price=900, tax_rate=15)
        inv_old = self.make_invoice(today - timedelta(days=60))
        InvoiceItem.objects.create(invoice=inv_old, product=self.refill19, quantity=7, unit_price=850, tax_rate=15)

        self.assertEqual(stock_service.sales_by_size(today, today, 'exchange')[self.size19], 2)
        self.assertEqual(stock_service.sales_by_size(today, today, 'deposit')[self.size19], 1)
        summary = stock_service.quick_sales_summary()
        self.assertEqual(summary['today']['refills_total'], 2)
        self.assertEqual(summary['today']['tanks_total'], 1)
        self.assertEqual(summary['last_30']['refills_total'], 2)

    def test_reorder_recommendation_uses_history(self):
        settings = StockAlertSettings.load()
        settings.sales_history_days = 10
        settings.supplier_lead_time_days = 2
        settings.safety_stock_days = 3
        settings.reorder_cover_days = 5
        settings.save()
        # 20 sold over the window => 2/day; stock after sale = 0 initially 20 -> 0
        inv = self.make_invoice(date.today() - timedelta(days=3))
        InvoiceItem.objects.create(invoice=inv, product=self.refill19, quantity=20, unit_price=850, tax_rate=15)
        # Top back up to 8 full so maths is easy
        stock_service.set_stock_levels([{'cylinder_size': self.size19, 'full_quantity': 8, 'empty_quantity': None}])

        rec = next(r for r in stock_service.reorder_recommendations(settings) if r['cylinder_size'] == self.size19)
        self.assertEqual(rec['avg_daily'], Decimal('2'))
        self.assertEqual(rec['days_cover'], Decimal('4'))
        # reorder point = 2 * (2+3) = 10 > 8 => low
        self.assertTrue(rec['is_low'])
        # target = 2 * (2+3+5) = 20, minus 8 on hand = 12
        self.assertEqual(rec['suggested_order_qty'], 12)

    def test_low_stock_alert_respects_cooldown(self):
        settings = StockAlertSettings.load()
        settings.whatsapp_numbers = '27820000000'
        settings.save()
        self.stock19.quantity = 1
        self.stock19.save()
        with mock.patch.object(stock_service, '_send_whatsapp_to_recipients', return_value=[('27820000000', {'success': True})]) as send:
            low, alerted, _ = stock_service.check_low_stock_and_alert()
            self.assertEqual([r['cylinder_size'] for r in alerted], [self.size19])
            send.assert_called_once()
            self.assertIn('19kg', send.call_args[0][0])
            # Second run inside cooldown: nothing sent
            _, alerted2, _ = stock_service.check_low_stock_and_alert()
            self.assertEqual(alerted2, [])
            self.assertEqual(send.call_count, 1)
            # Force bypasses cooldown
            _, alerted3, _ = stock_service.check_low_stock_and_alert(force=True)
            self.assertEqual(len(alerted3), 1)

    def test_no_alert_without_recipients(self):
        self.stock19.quantity = 0
        self.stock19.save()
        with mock.patch('core.services.whatsapp_service.WhatsAppService.send_text_message') as send:
            stock_service.check_low_stock_and_alert(force=True)
            send.assert_not_called()


class StockViewTests(StockTestBase):
    def setUp(self):
        super().setUp()
        self.client.login(username='staff', password='pw')

    def test_pages_render(self):
        for name in ['stock_dashboard', 'stock_receive', 'stock_adjust', 'stock_sales_report', 'stock_movements', 'stock_settings']:
            resp = self.client.get(reverse(f'accounting_forms:{name}'))
            self.assertEqual(resp.status_code, 200, name)
        for rng in ['daily', 'weekly', 'monthly', 'yearly', 'custom']:
            resp = self.client.get(reverse('accounting_forms:stock_sales_report'), {'range': rng})
            self.assertEqual(resp.status_code, 200, rng)

    def test_receive_stock_post(self):
        with mock.patch.object(stock_service, 'send_stock_received_alert'):
            resp = self.client.post(reverse('accounting_forms:stock_receive'), {
                'date': date.today().isoformat(),
                f'qty_{self.size19.id}': '12', f'empties_{self.size19.id}': '4', f'cost_{self.size19.id}': '410',
                f'qty_{self.size14.id}': '', f'empties_{self.size14.id}': '', f'cost_{self.size14.id}': '',
            })
        self.assertEqual(resp.status_code, 302)
        self.refresh()
        self.assertEqual((self.stock19.quantity, self.stock19.empty_quantity), (32, 1))

    def test_stocktake_post(self):
        resp = self.client.post(reverse('accounting_forms:stock_adjust'), {
            f'full_{self.size19.id}': '18', f'empty_{self.size19.id}': '', f'reorder_{self.size19.id}': '6',
            f'full_{self.size14.id}': '', f'empty_{self.size14.id}': '9', f'reorder_{self.size14.id}': '5',
            'notes': 'Count',
        })
        self.assertEqual(resp.status_code, 302)
        self.refresh()
        self.assertEqual((self.stock19.quantity, self.stock19.reorder_level), (18, 6))
        self.assertEqual(self.stock14.empty_quantity, 9)

    def test_settings_post(self):
        resp = self.client.post(reverse('accounting_forms:stock_settings'), {
            'alerts_enabled': 'on', 'whatsapp_numbers': '+27 82 123 4567\n27831234567',
            'notify_on_stock_received': 'on', 'notify_on_low_stock': 'on',
            'low_stock_alert_cooldown_hours': 24, 'sales_history_days': 28,
            'supplier_lead_time_days': 2, 'safety_stock_days': 3, 'reorder_cover_days': 14,
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(StockAlertSettings.load().recipient_numbers, ['27821234567', '27831234567'])
