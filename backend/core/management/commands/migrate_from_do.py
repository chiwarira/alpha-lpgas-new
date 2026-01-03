"""
Management command to migrate clients and invoices from DigitalOcean database.
Usage: python manage.py migrate_from_do --connection-string "postgresql://..."
"""
import psycopg2
from decimal import Decimal
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core.models import Client, Invoice, InvoiceItem, Product, Payment


class Command(BaseCommand):
    help = 'Migrate clients and invoices from DigitalOcean PostgreSQL database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--connection-string',
            type=str,
            required=True,
            help='PostgreSQL connection string for the source database'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview migration without making changes'
        )
        parser.add_argument(
            '--clients-only',
            action='store_true',
            help='Only migrate clients'
        )
        parser.add_argument(
            '--invoices-only',
            action='store_true',
            help='Only migrate invoices (requires clients to exist)'
        )

    def handle(self, *args, **options):
        connection_string = options['connection_string']
        dry_run = options['dry_run']
        clients_only = options['clients_only']
        invoices_only = options['invoices_only']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        try:
            self.stdout.write(f'Connecting to source database...')
            conn = psycopg2.connect(connection_string)
            cursor = conn.cursor()
            self.stdout.write(self.style.SUCCESS('Connected successfully!'))

            # Get table info first
            self.stdout.write('\nDiscovering database schema...')
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            self.stdout.write(f'Found tables: {", ".join(tables)}')

            # Migrate based on options
            if not invoices_only:
                self.migrate_clients(cursor, dry_run)
            
            if not clients_only:
                self.migrate_invoices(cursor, dry_run)

            cursor.close()
            conn.close()

            self.stdout.write(self.style.SUCCESS('\nMigration completed!'))

        except psycopg2.Error as e:
            raise CommandError(f'Database error: {e}')
        except Exception as e:
            raise CommandError(f'Error: {e}')

    def migrate_clients(self, cursor, dry_run):
        self.stdout.write('\n' + '='*50)
        self.stdout.write('MIGRATING CLIENTS')
        self.stdout.write('='*50)

        # Try to find client table - common names
        client_tables = ['core_client', 'clients', 'client', 'customers', 'core_customer']
        client_table = None
        
        for table in client_tables:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = %s
                )
            """, (table,))
            if cursor.fetchone()[0]:
                client_table = table
                break

        if not client_table:
            self.stdout.write(self.style.WARNING('No client table found. Checking all tables...'))
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            self.stdout.write(f'Available tables: {[r[0] for r in cursor.fetchall()]}')
            return

        # Get column names
        cursor.execute(f"""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = '{client_table}' ORDER BY ordinal_position
        """)
        columns = [row[0] for row in cursor.fetchall()]
        self.stdout.write(f'Client table "{client_table}" columns: {columns}')

        # Fetch clients
        cursor.execute(f'SELECT * FROM {client_table}')
        rows = cursor.fetchall()
        self.stdout.write(f'Found {len(rows)} clients in source database')

        if dry_run:
            for row in rows[:5]:  # Show first 5 in dry run
                client_data = dict(zip(columns, row))
                self.stdout.write(f"Would migrate: {client_data.get('name', 'Unknown')}")
            if len(rows) > 5:
                self.stdout.write(f'  ... and {len(rows) - 5} more')
            return
        
        # Pre-fetch all existing clients to avoid repeated DB queries
        self.stdout.write("Pre-fetching existing clients...")
        existing_clients_by_phone = {}
        existing_clients_by_email = {}
        
        for client in Client.objects.all():
            if client.phone:
                existing_clients_by_phone[client.phone] = client
            if client.email:
                existing_clients_by_email[client.email] = client
        
        self.stdout.write(f"Loaded {len(existing_clients_by_phone)} clients by phone, {len(existing_clients_by_email)} by email")
        
        created = 0
        updated = 0
        errors = 0
        
        for row in rows:
            client_data = dict(zip(columns, row))
                
            try:
                defaults = {
                    'name': client_data.get('name', ''),
                    'email': client_data.get('email', ''),
                    'phone': client_data.get('phone', ''),
                    'address': client_data.get('address', ''),
                    'city': client_data.get('city', ''),
                    'postal_code': client_data.get('postal_code', ''),
                    'tax_id': client_data.get('vat_number', ''),
                    'is_active': client_data.get('is_active', True),
                }
                
                # Use customer_id if exists, otherwise generate
                customer_id = client_data.get('customer_id', '')
                if customer_id:
                    defaults['customer_id'] = customer_id

                # Try to match by phone or email using pre-fetched data
                phone = defaults['phone']
                email = defaults['email']
                
                existing = None
                if phone and phone in existing_clients_by_phone:
                    existing = existing_clients_by_phone[phone]
                elif email and email in existing_clients_by_email:
                    existing = existing_clients_by_email[email]

                if existing:
                    for key, value in defaults.items():
                        if value:  # Only update non-empty values
                            setattr(existing, key, value)
                    existing.save()
                    updated += 1
                else:
                    new_client = Client.objects.create(**defaults)
                    # Add to cache for future lookups
                    if new_client.phone:
                        existing_clients_by_phone[new_client.phone] = new_client
                    if new_client.email:
                        existing_clients_by_email[new_client.email] = new_client
                    created += 1

            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f"Error migrating client {client_data.get('name', 'Unknown')}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(f'Clients: {created} created, {updated} updated, {errors} errors'))

    def migrate_invoices(self, cursor, dry_run):
        self.stdout.write('\n' + '='*50)
        self.stdout.write('MIGRATING INVOICES')
        self.stdout.write('='*50)

        # Find invoice table
        invoice_tables = ['core_invoice', 'invoices', 'invoice']
        invoice_table = None
        
        for table in invoice_tables:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = %s
                )
            """, (table,))
            if cursor.fetchone()[0]:
                invoice_table = table
                break

        if not invoice_table:
            self.stdout.write(self.style.WARNING('No invoice table found'))
            return

        # Get column names
        cursor.execute(f"""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = '{invoice_table}' ORDER BY ordinal_position
        """)
        columns = [row[0] for row in cursor.fetchall()]
        self.stdout.write(f'Invoice table "{invoice_table}" columns: {columns}')

        # Fetch invoices
        cursor.execute(f'SELECT * FROM {invoice_table}')
        rows = cursor.fetchall()
        self.stdout.write(f'Found {len(rows)} invoices in source database')

        if dry_run:
            for row in rows[:5]:
                inv_data = dict(zip(columns, row))
                self.stdout.write(f'  - {inv_data.get("invoice_number") or inv_data.get("number", "Unknown")}')
            if len(rows) > 5:
                self.stdout.write(f'  ... and {len(rows) - 5} more')
            return

        # Also get invoice items
        item_table = None
        for table in ['core_invoiceitem', 'invoice_items', 'invoiceitem']:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = %s
                )
            """, (table,))
            if cursor.fetchone()[0]:
                item_table = table
                break

        item_columns = []
        if item_table:
            cursor.execute(f"""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = '{item_table}' ORDER BY ordinal_position
            """)
            item_columns = [row[0] for row in cursor.fetchall()]
            self.stdout.write(f'Invoice item table "{item_table}" columns: {item_columns}')

        # Get payments table
        payment_table = None
        for table in ['core_payment', 'payments', 'payment']:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = %s
                )
            """, (table,))
            if cursor.fetchone()[0]:
                payment_table = table
                break

        payment_columns = []
        if payment_table:
            cursor.execute(f"""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = '{payment_table}' ORDER BY ordinal_position
            """)
            payment_columns = [row[0] for row in cursor.fetchall()]
            self.stdout.write(f'Payment table "{payment_table}" columns: {payment_columns}')

        # Migrate invoices
        created = 0
        updated = 0
        errors = 0
        items_created = 0
        payments_created = 0

        # Get default product for items without product match
        default_product = Product.objects.first()

        # Pre-fetch all old clients for mapping
        self.stdout.write('Building client mapping...')
        cursor.execute('SELECT id, phone, email, name FROM core_client')
        old_clients = {row[0]: {'phone': row[1], 'email': row[2], 'name': row[3]} for row in cursor.fetchall()}
        self.stdout.write(f'Loaded {len(old_clients)} client mappings')

        # Pre-fetch product mappings
        self.stdout.write('Building product mapping...')
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'core_product'")
        prod_columns = [r[0] for r in cursor.fetchall()]
        self.stdout.write(f'Product columns: {prod_columns}')
        
        # Use name as fallback if no sku column
        if 'sku' in prod_columns:
            cursor.execute('SELECT id, sku, name FROM core_product')
            old_products = {row[0]: {'sku': row[1], 'name': row[2]} for row in cursor.fetchall()}
        else:
            cursor.execute('SELECT id, name FROM core_product')
            old_products = {row[0]: {'sku': None, 'name': row[1]} for row in cursor.fetchall()}
        self.stdout.write(f'Loaded {len(old_products)} product mappings')

        # Pre-fetch all invoice items
        items_by_invoice = {}
        if item_table:
            self.stdout.write('Pre-fetching invoice items...')
            cursor.execute(f'SELECT * FROM {item_table}')
            all_items = cursor.fetchall()
            for item_row in all_items:
                item_data = dict(zip(item_columns, item_row))
                inv_id = item_data.get('invoice_id')
                if inv_id not in items_by_invoice:
                    items_by_invoice[inv_id] = []
                items_by_invoice[inv_id].append(item_data)
            self.stdout.write(f'Loaded {len(all_items)} invoice items')

        # Pre-fetch all payments
        payments_by_invoice = {}
        if payment_table:
            self.stdout.write('Pre-fetching payments...')
            cursor.execute(f'SELECT * FROM {payment_table}')
            all_payments = cursor.fetchall()
            for pay_row in all_payments:
                pay_data = dict(zip(payment_columns, pay_row))
                inv_id = pay_data.get('invoice_id')
                if inv_id not in payments_by_invoice:
                    payments_by_invoice[inv_id] = []
                payments_by_invoice[inv_id].append(pay_data)
            self.stdout.write(f'Loaded {len(all_payments)} payments')

        self.stdout.write('Processing invoices...')
        batch_size = 50  # Process in smaller batches
        for idx, row in enumerate(rows):
            # Reconnect Django DB every 50 invoices to avoid timeout
            if idx > 0 and idx % batch_size == 0:
                from django.db import connection
                connection.close()
                self.stdout.write(f'Processed {idx}/{len(rows)} invoices...')
            
            inv_data = dict(zip(columns, row))
            old_invoice_id = inv_data.get('id')
            invoice_number = inv_data.get('invoice_number') or inv_data.get('number', '')
            
            try:
                # Find client using pre-fetched data
                client = None
                client_id = inv_data.get('client_id') or inv_data.get('customer_id')
                if client_id and client_id in old_clients:
                    old_client_data = old_clients[client_id]
                    phone = old_client_data.get('phone', '')
                    if phone:
                        client = Client.objects.filter(phone=phone).first()

                if not client:
                    continue  # Skip invoices without matching client

                # Check if invoice already exists
                existing = Invoice.objects.filter(invoice_number=invoice_number).first()
                
                # Get total from db field or calculate
                total_amount = inv_data.get('total_amount_db') or inv_data.get('total_amount') or inv_data.get('total', 0) or 0
                paid_amount = inv_data.get('total_paid_db') or inv_data.get('paid_amount', 0) or 0
                
                # Get dates - use issue_date as fallback for due_date
                issue_date = inv_data.get('issue_date') or inv_data.get('date') or inv_data.get('created_at')
                due_date = inv_data.get('due_date') or issue_date  # Fallback to issue_date if null
                
                defaults = {
                    'client': client,
                    'issue_date': issue_date,
                    'due_date': due_date,
                    'subtotal': Decimal(str(inv_data.get('subtotal', 0) or 0)),
                    'tax_amount': Decimal(str(inv_data.get('tax_amount', 0) or inv_data.get('vat_amount', 0) or 0)),
                    'total_amount': Decimal(str(total_amount)),
                    'paid_amount': Decimal(str(paid_amount)),
                    'status': inv_data.get('status', 'draft'),
                    'notes': inv_data.get('notes') or '',
                }

                if existing:
                    for key, value in defaults.items():
                        setattr(existing, key, value)
                    existing.save()
                    invoice = existing
                    updated += 1
                else:
                    invoice = Invoice.objects.create(invoice_number=invoice_number, **defaults)
                    created += 1

                # Migrate invoice items using pre-fetched data
                if old_invoice_id and old_invoice_id in items_by_invoice:
                    for item_data in items_by_invoice[old_invoice_id]:
                        # Find product using pre-fetched data
                        product = default_product
                        product_id = item_data.get('product_id')
                        if product_id and product_id in old_products:
                            old_prod_data = old_products[product_id]
                            prod_name = old_prod_data.get('name', '')
                            if prod_name:
                                # Match by name since old system has no SKU
                                product = Product.objects.filter(name__icontains=prod_name.split()[0]).first() or default_product

                        if product:
                            # Use price field from old system
                            unit_price = item_data.get('price') or item_data.get('unit_price', 0) or 0
                            InvoiceItem.objects.get_or_create(
                                invoice=invoice,
                                product=product,
                                defaults={
                                    'description': item_data.get('description') or '',
                                    'quantity': Decimal(str(item_data.get('quantity', 1) or 1)),
                                    'unit_price': Decimal(str(unit_price)),
                                    'tax_rate': Decimal(str(item_data.get('vat_rate') or item_data.get('tax_rate', 15) or 15)),
                                }
                            )
                            items_created += 1

                # Migrate payments using pre-fetched data
                if old_invoice_id and old_invoice_id in payments_by_invoice:
                    for pay_data in payments_by_invoice[old_invoice_id]:
                        payment_number = pay_data.get('payment_number') or f'PAY-{invoice.invoice_number}-{payments_created}'
                        
                        Payment.objects.get_or_create(
                            payment_number=payment_number,
                            defaults={
                                'invoice': invoice,
                                'payment_date': pay_data.get('payment_date') or pay_data.get('date') or invoice.issue_date,
                                'amount': Decimal(str(pay_data.get('amount', 0) or 0)),
                                'payment_method': pay_data.get('payment_method', 'cash'),
                                'reference_number': pay_data.get('reference') or pay_data.get('reference_number') or '',
                                'notes': pay_data.get('notes') or '',
                            }
                        )
                        payments_created += 1

            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f'Error migrating invoice {invoice_number}: {e}'))

        self.stdout.write(self.style.SUCCESS(
            f'Invoices: {created} created, {updated} updated, {errors} errors\n'
            f'Invoice items: {items_created} created\n'
            f'Payments: {payments_created} created'
        ))
