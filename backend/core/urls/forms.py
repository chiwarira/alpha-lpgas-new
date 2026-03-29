from django.urls import path
from ..views_forms import (
    # Dashboard
    accounting_dashboard, daily_sales_report,
    
    # Clients
    client_list, client_create, client_create_ajax, client_last_invoice_ajax, client_edit, client_detail, client_delete, client_bulk_delete, client_statement, client_statement_preview,
    
    # Products
    product_list, product_create, product_edit,
    
    # Quotes
    quote_list, quote_create, quote_edit, quote_detail, quote_delete,
    
    # Invoices
    invoice_list, invoice_create, invoice_edit, invoice_detail, invoice_delete, invoice_mark_whatsapp_sent, invoice_bulk_action,
    
    # Payments
    payment_create, payment_list, payment_delete, invoice_balance_api, quick_payment, add_payment, client_unpaid_invoices,
    
    # Credit Notes
    credit_note_create, credit_note_detail, credit_note_list,
    
    # Orders
    order_list, order_detail, order_assign_driver,
    
    # Drivers
    driver_list, driver_create, driver_edit, driver_detail, driver_delete,
    
    # Contact Submissions
    contact_submission_list, contact_submission_detail,
    
    # Delivery Zones
    delivery_zone_list, delivery_zone_create, delivery_zone_edit, delivery_zone_delete,
    
    # Suppliers
    supplier_list, supplier_create, supplier_edit, supplier_detail,
    
    # Journal Entries
    journal_entry_list, journal_entry_detail,
)

from ..views_eft_reconciliation import (
    eft_reconciliation_upload, eft_reconciliation_review,
)

from ..views_analytics import (
    client_analytics, client_analytics_api,
)

from ..pdf_generator import download_invoice_pdf, download_quote_pdf
from ..views_loyalty import (
    loyalty_card_list, loyalty_card_detail,
    send_loyalty_card_whatsapp_view, download_loyalty_card
)
from ..views_client_leadtime import client_lead_time_analysis

app_name = 'accounting_forms'

urlpatterns = [
    # Dashboard
    path('', accounting_dashboard, name='dashboard'),
    path('daily-sales/', daily_sales_report, name='daily_sales_report'),
    
    # Clients
    path('clients/', client_list, name='client_list'),
    path('clients/create/', client_create, name='client_create'),
    path('clients/create-ajax/', client_create_ajax, name='client_create_ajax'),
    path('clients/<int:client_id>/last-invoice/', client_last_invoice_ajax, name='client_last_invoice_ajax'),
    path('clients/bulk-delete/', client_bulk_delete, name='client_bulk_delete'),
    path('clients/<int:pk>/', client_detail, name='client_detail'),
    path('clients/<int:pk>/edit/', client_edit, name='client_edit'),
    path('clients/<int:pk>/delete/', client_delete, name='client_delete'),
    path('clients/<int:pk>/statement/', client_statement, name='client_statement'),
    path('clients/<int:pk>/statement/<str:start_date>/<str:end_date>/', client_statement_preview, name='client_statement_preview'),
    path('clients/<int:client_id>/lead-time/', client_lead_time_analysis, name='client_lead_time'),
    path('clients/<int:pk>/analytics/', client_analytics, name='client_analytics'),
    path('api/clients/<int:pk>/analytics/', client_analytics_api, name='client_analytics_api'),
    
    # Products
    path('products/', product_list, name='product_list'),
    path('products/create/', product_create, name='product_create'),
    path('products/<int:pk>/edit/', product_edit, name='product_edit'),
    
    # Quotes
    path('quotes/', quote_list, name='quote_list'),
    path('quotes/create/', quote_create, name='quote_create'),
    path('quotes/<int:pk>/', quote_detail, name='quote_detail'),
    path('quotes/<int:pk>/edit/', quote_edit, name='quote_edit'),
    path('quotes/<int:pk>/delete/', quote_delete, name='quote_delete'),
    path('quotes/<int:pk>/pdf/', download_quote_pdf, name='quote_pdf'),
    
    # Invoices
    path('invoices/', invoice_list, name='invoice_list'),
    path('invoices/bulk-action/', invoice_bulk_action, name='invoice_bulk_action'),
    path('invoices/create/', invoice_create, name='invoice_create'),
    path('invoices/<str:invoice_number>/', invoice_detail, name='invoice_detail'),
    path('invoices/<str:invoice_number>/edit/', invoice_edit, name='invoice_edit'),
    path('invoices/<str:invoice_number>/delete/', invoice_delete, name='invoice_delete'),
    path('invoices/<str:invoice_number>/pdf/', download_invoice_pdf, name='invoice_pdf'),
    path('invoices/<str:invoice_number>/mark-whatsapp-sent/', invoice_mark_whatsapp_sent, name='invoice_mark_whatsapp_sent'),
    
    # Loyalty Cards
    path('loyalty-cards/', loyalty_card_list, name='loyalty_card_list'),
    path('loyalty-cards/<int:pk>/', loyalty_card_detail, name='loyalty_card_detail'),
    path('loyalty-cards/<int:pk>/send/', send_loyalty_card_whatsapp_view, name='send_loyalty_card'),
    path('loyalty-cards/<int:pk>/download/', download_loyalty_card, name='download_loyalty_card'),
    
    # Payments
    path('payments/', payment_list, name='payment_list'),
    path('payments/create/single/', payment_create, name='payment_create_single'),  # Single invoice payment
    path('payments/create/multi/', add_payment, name='payment_create_multi'),  # Multi-invoice payment
    path('payments/create/', add_payment, name='payment_create'),  # Default to multi-invoice
    path('payments/<int:pk>/delete/', payment_delete, name='payment_delete'),
    path('invoices/<int:invoice_pk>/payments/create/', payment_create, name='payment_create_for_invoice'),
    path('api/invoices/<int:pk>/balance/', invoice_balance_api, name='invoice_balance_api'),
    path('invoices/<int:pk>/quick-payment/', quick_payment, name='quick_payment'),
    path('api/clients/<int:client_id>/unpaid-invoices/', client_unpaid_invoices, name='client_unpaid_invoices'),
    
    # Credit Notes
    path('credit-notes/create/', credit_note_create, name='credit_note_create'),
    path('invoices/<int:invoice_pk>/credit-notes/create/', credit_note_create, name='credit_note_create_for_invoice'),
    path('credit-notes/<int:pk>/', credit_note_detail, name='credit_note_detail'),
    
    # Orders
    path('orders/', order_list, name='order_list'),
    path('orders/<int:pk>/', order_detail, name='order_detail'),
    path('orders/<int:pk>/assign-driver/', order_assign_driver, name='order_assign_driver'),
    
    # Drivers
    path('drivers/', driver_list, name='driver_list'),
    path('drivers/create/', driver_create, name='driver_create'),
    path('drivers/<int:pk>/', driver_detail, name='driver_detail'),
    path('drivers/<int:pk>/edit/', driver_edit, name='driver_edit'),
    path('drivers/<int:pk>/delete/', driver_delete, name='driver_delete'),
    
    # Contact Submissions
    path('contact-submissions/', contact_submission_list, name='contact_submission_list'),
    path('contact-submissions/<int:pk>/', contact_submission_detail, name='contact_submission_detail'),
    
    # Delivery Zones
    path('delivery-zones/', delivery_zone_list, name='delivery_zone_list'),
    path('delivery-zones/create/', delivery_zone_create, name='delivery_zone_create'),
    path('delivery-zones/<int:pk>/edit/', delivery_zone_edit, name='delivery_zone_edit'),
    path('delivery-zones/<int:pk>/delete/', delivery_zone_delete, name='delivery_zone_delete'),
    
    # Credit Notes List
    path('credit-notes/', credit_note_list, name='credit_note_list'),
    
    # Suppliers
    path('suppliers/', supplier_list, name='supplier_list'),
    path('suppliers/create/', supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/', supplier_detail, name='supplier_detail'),
    path('suppliers/<int:pk>/edit/', supplier_edit, name='supplier_edit'),
    
    # Journal Entries
    path('journal-entries/', journal_entry_list, name='journal_entry_list'),
    path('journal-entries/<int:pk>/', journal_entry_detail, name='journal_entry_detail'),
    
    # EFT Reconciliation
    path('eft-reconciliation/', eft_reconciliation_upload, name='eft_reconciliation_upload'),
    path('eft-reconciliation/review/', eft_reconciliation_review, name='eft_reconciliation_review'),
]
