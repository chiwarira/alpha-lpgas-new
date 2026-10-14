"""
Daily low-stock check. Sends a WhatsApp summary (with re-order suggestions based on
recent sales) to the numbers configured under Stock -> Alerts & Re-order Settings.

Usage:
    python manage.py check_stock_levels            # respects per-size cooldown
    python manage.py check_stock_levels --force    # ignore cooldown
    python manage.py check_stock_levels --dry-run  # print message, don't send
"""
from django.core.management.base import BaseCommand

from core.models_stock import StockAlertSettings
from core.services import stock_service


class Command(BaseCommand):
    help = 'Check cylinder stock levels and send low-stock WhatsApp alerts with re-order suggestions'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Send even if an alert was sent recently')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be sent without sending')

    def handle(self, *args, **options):
        settings = StockAlertSettings.load()
        recs = stock_service.reorder_recommendations(settings)
        low = [r for r in recs if r['is_low']]

        self.stdout.write(stock_service._format_stock_lines(recs))
        if not low:
            self.stdout.write(self.style.SUCCESS('All cylinder sizes are above reorder levels.'))
            return

        if options['dry_run']:
            self.stdout.write('\n--- Message that would be sent ---')
            self.stdout.write(stock_service.build_low_stock_message(low, settings))
            self.stdout.write(f"\nRecipients: {', '.join(settings.recipient_numbers) or '(none configured)'}")
            return

        low, alerted, results = stock_service.check_low_stock_and_alert(force=options['force'])
        if not alerted:
            self.stdout.write(self.style.WARNING(
                f"{len(low)} size(s) low but alert skipped (cooldown or alerts disabled)."))
            return
        for number, res in results:
            if res.get('success'):
                self.stdout.write(self.style.SUCCESS(f'Sent to {number}'))
            else:
                self.stderr.write(self.style.ERROR(f"Failed to send to {number}: {res.get('error')}"))
