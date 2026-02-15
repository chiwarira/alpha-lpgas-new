"""
Management command to sync customer IDs from DigitalOcean database to Railway database.
Matches clients by name + phone, then updates customer_id in the current database.

Usage:
  railway run python manage.py sync_customer_ids_from_do --dry-run   # Preview changes
  railway run python manage.py sync_customer_ids_from_do              # Apply changes
"""
import os
import psycopg
from django.core.management.base import BaseCommand
from core.models import Client


class Command(BaseCommand):
    help = 'Sync customer IDs from DigitalOcean database to the current (Railway) database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without applying them',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        do_url = os.environ.get('DO_DATABASE_URL')

        if not do_url:
            self.stderr.write(self.style.ERROR('DO_DATABASE_URL environment variable not set.'))
            return

        # Step 1: Fetch all clients from DO database
        self.stdout.write('Connecting to DigitalOcean database...')
        try:
            do_conn = psycopg.connect(do_url)
            do_cur = do_conn.cursor()
            do_cur.execute('SELECT customer_id, name, phone FROM core_client ORDER BY id')
            do_clients = do_cur.fetchall()
            do_conn.close()
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Failed to connect to DO database: {e}'))
            return

        self.stdout.write(f'Fetched {len(do_clients)} clients from DO database.')

        # Build lookup: (name, phone) -> customer_id from DO
        do_lookup = {}
        for customer_id, name, phone in do_clients:
            key = (name.strip().lower(), phone.strip() if phone else '')
            do_lookup[key] = customer_id

        # Also build a name-only lookup for fallback
        do_name_lookup = {}
        for customer_id, name, phone in do_clients:
            name_key = name.strip().lower()
            if name_key not in do_name_lookup:
                do_name_lookup[name_key] = customer_id

        # Step 2: Compare with Railway clients
        railway_clients = Client.objects.all()
        self.stdout.write(f'Found {railway_clients.count()} clients in Railway database.')

        updated = 0
        skipped = 0
        not_found = 0
        already_correct = 0

        for client in railway_clients:
            key = (client.name.strip().lower(), client.phone.strip() if client.phone else '')
            do_customer_id = do_lookup.get(key)

            # Fallback: match by name only
            if not do_customer_id:
                name_key = client.name.strip().lower()
                do_customer_id = do_name_lookup.get(name_key)

            if not do_customer_id:
                not_found += 1
                if not_found <= 10:
                    self.stdout.write(f'  NOT FOUND: "{client.name}" ({client.phone})')
                continue

            if client.customer_id == do_customer_id:
                already_correct += 1
                continue

            if dry_run:
                self.stdout.write(
                    f'  WOULD UPDATE: "{client.name}" | '
                    f'{client.customer_id} -> {do_customer_id}'
                )
            else:
                Client.objects.filter(pk=client.pk).update(customer_id=do_customer_id)

            updated += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'=== Summary ==='))
        self.stdout.write(f'  Already correct: {already_correct}')
        self.stdout.write(f'  {"Would update" if dry_run else "Updated"}: {updated}')
        self.stdout.write(f'  Not found in DO: {not_found}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDry run — no changes were made. Remove --dry-run to apply.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\nDone! Updated {updated} customer IDs.'))
