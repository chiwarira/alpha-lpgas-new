from django.urls import path
from ..views_forms import (
    # Dashboard
    accounting_dashboard,
    
    # Clients
    client_list, client_create, client_edit, client_detail, client_delete, client_bulk_delete, client_statement, client_statement_preview,
    
    # Products
    product_list, product_create, product_edit,
    
    # Quotes
    quote_list, quote_create, quote_edit, quote_detail,
    
    # Invoices
    invoice_list, invoice_create, invoice_edit, invoice_detail,
    
    # Payments
    payment_create,
    
    # Credit Notes
    credit_note_create, credit_note_detail,
)

from ..pdf_generator import download_invoice_pdf, download_quote_pdf

app_name = 'accounting_forms'

urlpatterns = [
    # Dashboard
    path('', accounting_dashboard, name='dashboard'),
    
    # Clients
    path('clients/', client_list, name='client_list'),
    path('clients/create/', client_create, name='client_create'),
    path('clients/bulk-delete/', client_bulk_delete, name='client_bulk_delete'),
    path('clients/<int:pk>/', client_detail, name='client_detail'),
    path('clients/<int:pk>/edit/', client_edit, name='client_edit'),
    path('clients/<int:pk>/delete/', client_delete, name='client_delete'),
    path('clients/<int:pk>/statement/', client_statement, name='client_statement'),
    path('clients/<int:pk>/statement/<str:start_date>/<str:end_date>/', client_statement_preview, name='client_statement_preview'),
    
    # Products
    path('products/', product_list, name='product_list'),
    path('products/create/', product_create, name='product_create'),
    path('products/<int:pk>/edit/', product_edit, name='product_edit'),
    
    # Quotes
    path('quotes/', quote_list, name='quote_list'),
    path('quotes/create/', quote_create, name='quote_create'),
    path('quotes/<int:pk>/', quote_detail, name='quote_detail'),
    path('quotes/<int:pk>/edit/', quote_edit, name='quote_edit'),
    path('quotes/<int:pk>/pdf/', download_quote_pdf, name='quote_pdf'),
    
    # Invoices
    path('invoices/', invoice_list, name='invoice_list'),
    path('invoices/create/', invoice_create, name='invoice_create'),
    path('invoices/<int:pk>/', invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/edit/', invoice_edit, name='invoice_edit'),
    path('invoices/<int:pk>/pdf/', download_invoice_pdf, name='invoice_pdf'),
    
    # Payments
    path('payments/create/', payment_create, name='payment_create'),
    path('invoices/<int:invoice_pk>/payments/create/', payment_create, name='payment_create_for_invoice'),
    
    # Credit Notes
    path('credit-notes/create/', credit_note_create, name='credit_note_create'),
    path('invoices/<int:invoice_pk>/credit-notes/create/', credit_note_create, name='credit_note_create_for_invoice'),
    path('credit-notes/<int:pk>/', credit_note_detail, name='credit_note_detail'),
]
