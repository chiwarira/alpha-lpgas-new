from datetime import date
from decimal import Decimal
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.db.models.signals import post_save
from django.test import TestCase
from django.urls import reverse

from core import signals as core_signals
from core.models import Client, Product, Invoice, InvoiceItem, CompanySettings, OrderItem
from core.models_loyalty import LoyaltyCard, LoyaltyTransaction
from core.utils_loyalty import (
    process_loyalty_stamp, reprocess_loyalty_stamp, remove_loyalty_stamp, _size_from_name, LOYALTY_REWARD_SKU,
)


class LoyaltyTestBase(TestCase):
    def setUp(self):
        # Order auto-generation uses second-resolution order numbers; disconnect for multi-invoice tests
        post_save.disconnect(core_signals.sync_invoice_item_to_order, sender=InvoiceItem)
        self.addCleanup(post_save.connect, core_signals.sync_invoice_item_to_order, sender=InvoiceItem)
        self.user = User.objects.create_user('staff', password='pw', is_staff=True)
        self.gas9 = Product.objects.create(name='9KG Gas Exchange', sku='GAS9', unit_price=330)
        self.gas19 = Product.objects.create(name='19KG Gas Exchange', sku='GAS19', unit_price=720)
        self.hose = Product.objects.create(name='Hose', sku='HOSE', unit_price=30)
        self.client_obj = Client.objects.create(name='Loyal Client', phone='0821234567')

    def make_invoice(self, *lines):
        inv = Invoice.objects.create(client=self.client_obj, issue_date=date.today(), due_date=date.today(), created_by=self.user)
        for product, qty in lines:
            InvoiceItem.objects.create(invoice=inv, product=product, quantity=qty, unit_price=product.unit_price, tax_rate=15)
        inv.calculate_totals()
        return inv

    def stamp(self, *lines):
        inv = self.make_invoice(*lines)
        card = process_loyalty_stamp(inv)
        inv.refresh_from_db()
        return inv, card

    def set_stamps(self, n):
        LoyaltyCard.objects.update_or_create(client=self.client_obj, is_active=True, defaults={'stamps': n, 'cylinder_size': '9kg'})

    def reward_lines(self, inv):
        return inv.items.filter(product__sku=LOYALTY_REWARD_SKU)


class SizeParsingTests(TestCase):
    def test_sizes(self):
        self.assertEqual(_size_from_name('19KG Gas Exchange'), '19kg')
        self.assertEqual(_size_from_name('9KG Gas Exchange'), '9kg')
        self.assertEqual(_size_from_name('48 kg Gas Refill'), '48kg')
        self.assertEqual(_size_from_name('14kg gas exchange'), '14kg')
        self.assertIsNone(_size_from_name('Hose'))


class LoyaltyRewardTests(LoyaltyTestBase):
    def test_tenth_purchase_gets_50_percent_and_resets(self):
        for _ in range(9):
            inv, card = self.stamp((self.gas9, 1))
            self.assertFalse(self.reward_lines(inv).exists())
        self.assertEqual(card.stamps, 9)

        inv, card = self.stamp((self.gas9, 1))
        self.assertEqual(card.stamps, 0)
        self.assertEqual(card.rewards_applied, 1)
        line = self.reward_lines(inv).get()
        self.assertEqual(line.unit_price, Decimal('-165.00'))
        self.assertEqual(inv.total_amount, Decimal('165.00'))
        reward = LoyaltyTransaction.objects.get(transaction_type='reward_claimed')
        self.assertEqual((reward.reward_percent, reward.reward_amount, reward.invoice), (50, Decimal('165.00'), inv))
        self.assertEqual((card.half_rewards_count, card.full_rewards_count), (1, 0))

        # Counting restarts
        _, card = self.stamp((self.gas9, 1))
        self.assertEqual(card.stamps, 1)

    def test_multi_bottle_invoice_discounts_cheapest_and_carries_over(self):
        self.set_stamps(8)
        # bottle 9 stamps, bottle 10 is rewarded, bottle 11 starts the new card
        inv, card = self.stamp((self.gas19, 1), (self.gas9, 2), (self.hose, 1))
        self.assertEqual(card.stamps, 1)
        line = self.reward_lines(inv).get()
        self.assertEqual((line.quantity, line.unit_price), (Decimal('1'), Decimal('-165.00')))
        self.assertIn('9KG Gas Exchange', line.description)
        self.assertEqual(inv.total_amount, Decimal('720') + Decimal('660') + Decimal('30') - Decimal('165'))

    def test_large_order_can_earn_multiple_rewards(self):
        self.set_stamps(9)
        inv, card = self.stamp((self.gas9, 11))
        # bottle 1 rewarded, bottles 2-10 stamp (9), bottle 11 rewarded
        self.assertEqual(card.rewards_applied, 2)
        self.assertEqual(card.stamps, 0)
        self.assertEqual(self.reward_lines(inv).get().quantity, Decimal('2'))

    def test_100_percent_setting(self):
        settings = CompanySettings.load()
        settings.loyalty_reward_percent = 100
        settings.save()
        self.set_stamps(9)
        inv, card = self.stamp((self.gas19, 1))
        self.assertEqual(inv.total_amount, Decimal('0.00'))
        self.assertEqual(card.full_rewards_count, 1)

    def test_free_r0_line_does_not_earn_stamp(self):
        inv = Invoice.objects.create(client=self.client_obj, issue_date=date.today(), due_date=date.today())
        InvoiceItem.objects.create(invoice=inv, product=self.gas9, quantity=1, unit_price=0, tax_rate=15)
        self.assertIsNone(process_loyalty_stamp(inv))

    def test_processing_twice_is_idempotent(self):
        self.set_stamps(9)
        inv, _ = self.stamp((self.gas9, 1))
        process_loyalty_stamp(inv)
        self.assertEqual(self.reward_lines(inv).count(), 1)
        self.assertEqual(LoyaltyTransaction.objects.filter(transaction_type='reward_claimed').count(), 1)

    def test_delete_reward_invoice_restores_stamps(self):
        self.set_stamps(9)
        inv, _ = self.stamp((self.gas9, 1))
        inv.delete()
        card = LoyaltyCard.objects.get(client=self.client_obj)
        self.assertEqual(card.stamps, 9)
        self.assertFalse(LoyaltyTransaction.objects.filter(transaction_type='reward_claimed').exists())

    def test_remove_then_edit_keeps_original_percent(self):
        self.set_stamps(9)
        inv, _ = self.stamp((self.gas9, 1))
        settings = CompanySettings.load()
        settings.loyalty_reward_percent = 100
        settings.save()
        # Edit: add a second bottle; reward stays 50% and only one reward line exists
        InvoiceItem.objects.create(invoice=inv, product=self.gas9, quantity=1, unit_price=330, tax_rate=15)
        card = reprocess_loyalty_stamp(inv)
        inv.refresh_from_db()
        self.assertEqual(card.stamps, 1)
        self.assertEqual(self.reward_lines(inv).get().unit_price, Decimal('-165.00'))
        self.assertEqual(inv.total_amount, Decimal('495.00'))

    def test_remove_cancels_reward_and_restores_total(self):
        self.set_stamps(9)
        inv, _ = self.stamp((self.gas9, 1))
        remove_loyalty_stamp(inv, log_reversal=False)
        inv.refresh_from_db()
        self.assertFalse(self.reward_lines(inv).exists())
        self.assertEqual(inv.total_amount, Decimal('330.00'))
        self.assertEqual(LoyaltyCard.objects.get(client=self.client_obj).stamps, 9)


class LoyaltyOrderSyncTests(LoyaltyTestBase):
    def setUp(self):
        super().setUp()
        post_save.connect(core_signals.sync_invoice_item_to_order, sender=InvoiceItem)

    def test_reward_line_syncs_to_order_and_is_removed_with_it(self):
        self.set_stamps(9)
        inv, _ = self.stamp((self.gas9, 1))
        self.assertEqual(OrderItem.objects.filter(order=inv.order, unit_price=Decimal('-165.00')).count(), 1)
        remove_loyalty_stamp(inv, log_reversal=False)
        self.assertFalse(OrderItem.objects.filter(order=inv.order, unit_price__lt=0).exists())


class InvoiceViewLoyaltyTests(LoyaltyTestBase):
    """Through the staff invoice create/edit forms (single invoice, so the order signal can stay on)."""

    def setUp(self):
        super().setUp()
        post_save.connect(core_signals.sync_invoice_item_to_order, sender=InvoiceItem)
        from core.models import Driver
        self.driver = Driver.objects.create(user=User.objects.create_user('driver1', password='pw'), phone='0820000000')
        self.client.force_login(self.user)

    def form_data(self, qty, item_id=None, invoice=None):
        return {
            'client': self.client_obj.pk, 'issue_date': date.today().isoformat(), 'payment_terms': 'immediate',
            'assigned_driver': self.driver.pk, 'assigned_vehicle': '', 'discount_amount': '0',
            'notes': '', 'delivery_note': '', 'whatsapp_invoice_message': '',
            'items-TOTAL_FORMS': '1', 'items-INITIAL_FORMS': '1' if item_id else '0',
            'items-MIN_NUM_FORMS': '0', 'items-MAX_NUM_FORMS': '1000',
            'items-0-id': item_id or '', 'items-0-invoice': invoice.pk if invoice else '',
            'items-0-product': self.gas9.pk, 'items-0-quantity': str(qty),
        }

    def test_create_and_edit_reward_invoice(self):
        self.set_stamps(9)
        resp = self.client.post(reverse('accounting_forms:invoice_create'), self.form_data(1))
        self.assertEqual(resp.status_code, 302)
        inv = Invoice.objects.get()
        self.assertEqual(inv.total_amount, Decimal('165.00'))
        self.assertEqual(inv.order.items.count(), 2)

        # Edit form must not show the reward line as an editable item
        resp = self.client.get(reverse('accounting_forms:invoice_edit', args=[inv.invoice_number]))
        self.assertEqual(resp.context['formset'].total_form_count(), 1)

        gas_line = inv.items.get(product=self.gas9)
        resp = self.client.post(reverse('accounting_forms:invoice_edit', args=[inv.invoice_number]), self.form_data(2, gas_line.pk, inv))
        self.assertEqual(resp.status_code, 302)
        inv.refresh_from_db()
        self.assertEqual(self.reward_lines(inv).count(), 1)
        self.assertEqual(inv.total_amount, Decimal('495.00'))
        self.assertEqual(LoyaltyCard.objects.get(client=self.client_obj).stamps, 1)
        self.assertEqual(LoyaltyTransaction.objects.filter(transaction_type='reward_claimed').count(), 1)

        resp = self.client.post(reverse('accounting_forms:invoice_delete', args=[inv.invoice_number]))
        self.assertEqual(LoyaltyCard.objects.get(client=self.client_obj).stamps, 9)
        self.assertFalse(LoyaltyTransaction.objects.filter(transaction_type='reward_claimed').exists())


class BackfillTests(LoyaltyTestBase):
    def test_backfill_records_r0_gas_lines_once(self):
        inv = Invoice.objects.create(client=self.client_obj, issue_date=date.today(), due_date=date.today())
        InvoiceItem.objects.create(invoice=inv, product=self.gas9, quantity=1, unit_price=0, tax_rate=15)
        call_command('backfill_loyalty_rewards', '--dry-run', stdout=StringIO())
        self.assertFalse(LoyaltyTransaction.objects.exists())
        call_command('backfill_loyalty_rewards', stdout=StringIO())
        call_command('backfill_loyalty_rewards', stdout=StringIO())
        reward = LoyaltyTransaction.objects.get(transaction_type='reward_claimed')
        self.assertEqual((reward.reward_percent, reward.reward_amount), (100, Decimal('330.00')))


class NormalizeCardsTests(LoyaltyTestBase):
    def test_split_stamps(self):
        from core.management.commands.normalize_loyalty_cards import split_stamps
        self.assertEqual(split_stamps(10), (1, 1))
        self.assertEqual(split_stamps(18), (1, 9))
        self.assertEqual(split_stamps(19), (2, 1))
        self.assertEqual(split_stamps(40), (4, 4))

    def test_normalize_records_history_and_is_rerunnable(self):
        self.set_stamps(40)
        other = Client.objects.create(name='Due Client')
        LoyaltyCard.objects.create(client=other, stamps=9, cylinder_size='9kg')
        call_command('normalize_loyalty_cards', '--dry-run', stdout=StringIO())
        self.assertEqual(LoyaltyCard.objects.get(client=self.client_obj).stamps, 40)
        call_command('normalize_loyalty_cards', stdout=StringIO())
        call_command('normalize_loyalty_cards', stdout=StringIO())
        card = LoyaltyCard.objects.get(client=self.client_obj)
        self.assertEqual((card.stamps, card.full_rewards_count), (4, 4))
        self.assertEqual(card.reward_transactions().first().reward_amount, Decimal('330.00'))
        self.assertEqual(LoyaltyCard.objects.get(client=other).stamps, 9)
        self.assertFalse(LoyaltyTransaction.objects.filter(loyalty_card__client=other).exists())


class LoyaltyViewTests(LoyaltyTestBase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def test_pages_render_with_counts(self):
        self.set_stamps(9)
        self.stamp((self.gas9, 1))
        card = LoyaltyCard.objects.get(client=self.client_obj)
        resp = self.client.get(reverse('accounting_forms:loyalty_card_list'), {'rewards': 'half'})
        self.assertContains(resp, 'Loyal Client')
        self.assertEqual(resp.context['total_half_rewards'], 1)
        resp = self.client.get(reverse('accounting_forms:loyalty_card_list'), {'rewards': 'full'})
        self.assertNotContains(resp, 'Loyal Client')
        resp = self.client.get(reverse('accounting_forms:loyalty_card_detail', args=[card.pk]))
        self.assertContains(resp, 'Rewards Given')
        self.assertEqual(resp.context['half_rewards'], 1)
        resp = self.client.get(reverse('accounting_forms:loyalty_reward_history'), {'percent': '50'})
        self.assertContains(resp, 'R165.00')

    def test_settings_update(self):
        resp = self.client.post(reverse('accounting_forms:loyalty_settings_update'), {'loyalty_reward_percent': '100'})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(CompanySettings.load().loyalty_reward_percent, 100)
        self.client.post(reverse('accounting_forms:loyalty_settings_update'), {'loyalty_reward_percent': '75'})
        self.assertEqual(CompanySettings.load().loyalty_reward_percent, 100)
