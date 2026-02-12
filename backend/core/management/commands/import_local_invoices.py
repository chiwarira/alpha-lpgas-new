"""
Import invoices from local database to Railway database.
Usage: DATABASE_URL=<railway_url> python manage.py import_local_invoices
"""
import os
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import connection
from core.models import Client, Invoice, InvoiceItem, Product, Payment


class Command(BaseCommand):
    help = 'Import invoices from local SQLite database to Railway PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--local-db',
            type=str,
            default='db.sqlite3',
            help='Path to local SQLite database'
        )

    def handle(self, *args, **options):
        import psycopg2
        import psycopg2.extras
        
        # Local PostgreSQL database
        local_conn = psycopg2.connect(
            dbname='alphalpgas',
            user='alphalpgas_user',
            password='fun2gai2',
            host='localhost',
            port=5432
        )
        local_cursor = local_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        self.stdout.write('Connected to local PostgreSQL database')
        
        # Get local invoices
        local_cursor.execute('SELECT * FROM core_invoice ORDER BY id')
        invoices = local_cursor.fetchall()
        self.stdout.write(f'Found {len(invoices)} invoices in local database')
        
        # Get local invoice items
        local_cursor.execute('SELECT * FROM core_invoiceitem')
        all_items = {row['invoice_id']: [] for row in local_cursor.fetchall()}
        local_cursor.execute('SELECT * FROM core_invoiceitem')
        for row in local_cursor.fetchall():
            if row['invoice_id'] not in all_items:
                all_items[row['invoice_id']] = []
            all_items[row['invoice_id']].append(dict(row))
        self.stdout.write(f'Found {sum(len(v) for v in all_items.values())} invoice items')
        
        # Get local payments
        local_cursor.execute('SELECT * FROM core_payment')
        all_payments = {}
        for row in local_cursor.fetchall():
            inv_id = row['invoice_id']
            if inv_id not in all_payments:
                all_payments[inv_id] = []
            all_payments[inv_id].append(dict(row))
        self.stdout.write(f'Found {sum(len(v) for v in all_payments.values())} payments')
        
        # Build client mapping from local to Railway by ID (IDs match between databases)
        self.stdout.write('Building client mappings...')
        railway_clients_by_id = {client.id: client for client in Client.objects.all()}
        self.stdout.write(f'Loaded {len(railway_clients_by_id)} Railway clients')
        
        # Get default product
        default_product = Product.objects.first()
        
        # Pre-fetch products by name
        products_by_name = {}
        for product in Product.objects.all():
            products_by_name[product.name.lower()] = product
        
        # Get local products for mapping
        local_cursor.execute('SELECT id, name FROM core_product')
        local_products = {row['id']: row['name'] for row in local_cursor.fetchall()}
        
        created = 0
        updated = 0
        errors = 0
        items_created = 0
        payments_created = 0
        batch_size = 50
        
        self.stdout.write('Processing invoices...')
        for idx, inv_row in enumerate(invoices):
            # Reconnect every batch to avoid timeout
            if idx > 0 and idx % batch_size == 0:
                connection.close()
                self.stdout.write(f'Processed {idx}/{len(invoices)} invoices...')
            
            inv_data = dict(inv_row)
            invoice_number = inv_data.get('invoice_number') or inv_data.get('number', '')
            
            try:
                # Find client by ID (IDs match between local and Railway)
                client_id = inv_data.get('client_id')
                client = railway_clients_by_id.get(client_id) if client_id else None
                
                if not client:
                    errors += 1
                    continue
                
                # Check if invoice exists
                existing = Invoice.objects.filter(invoice_number=invoice_number).first()
                
                defaults = {
                    'client': client,
                    'issue_date': inv_data.get('issue_date'),
                    'due_date': inv_data.get('due_date') or inv_data.get('issue_date'),
                    'subtotal': Decimal(str(inv_data.get('subtotal', 0) or 0)),
                    'tax_amount': Decimal(str(inv_data.get('tax_amount', 0) or 0)),
                    'total_amount': Decimal(str(inv_data.get('total_amount', 0) or 0)),
                    'paid_amount': Decimal(str(inv_data.get('paid_amount', 0) or 0)),
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
                
                # Import invoice items
                old_inv_id = inv_data.get('id')
                if old_inv_id in all_items:
                    for item in all_items[old_inv_id]:
                        product = default_product
                        prod_id = item.get('product_id')
                        if prod_id and prod_id in local_products:
                            prod_name = local_products[prod_id].lower()
                            if prod_name in products_by_name:
                                product = products_by_name[prod_name]
                        
                        if product:
                            InvoiceItem.objects.get_or_create(
                                invoice=invoice,
                                product=product,
                                defaults={
                                    'description': item.get('description') or '',
                                    'quantity': Decimal(str(item.get('quantity', 1) or 1)),
                                    'unit_price': Decimal(str(item.get('unit_price') or item.get('price', 0) or 0)),
                                    'tax_rate': Decimal(str(item.get('tax_rate', 15) or 15)),
                                }
                            )
                            items_created += 1
                
                # Import payments
                if old_inv_id in all_payments:
                    for pay in all_payments[old_inv_id]:
                        Payment.objects.get_or_create(
                            invoice=invoice,
                            amount=Decimal(str(pay.get('amount', 0) or 0)),
                            payment_date=pay.get('payment_date'),
                            defaults={
                                'payment_method': pay.get('payment_method') or 'cash',
                                'reference_number': pay.get('reference_number') or pay.get('reference') or '',
                                'notes': pay.get('notes') or '',
                            }
                        )
                        payments_created += 1
                
            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f'Error: {invoice_number}: {str(e)}'))
        
        local_conn.close()
        
        self.stdout.write(self.style.SUCCESS(
            f'\nImport completed!\n'
            f'Invoices: {created} created, {updated} updated, {errors} errors\n'
            f'Invoice items: {items_created} created\n'
            f'Payments: {payments_created} created'
        ))
