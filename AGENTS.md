# Alpha LPGas - agent notes

## Layout
- `backend/` Django 4.2 (apps: `core`, `cms`). Staff accounting UI is server-rendered under `/accounting/` (`core/urls/forms.py`, templates in `backend/templates/core/`). Nav lives in `templates/core/base.html`.
- `frontend/` Next.js 14 public site.

## Running locally
- Backend: `cd backend && venv/Scripts/python manage.py runserver 8000` (Windows venv at `backend/venv`). Uses local Postgres from `backend/.env` (`DATABASE_URL`).
- Apply migrations: `venv/Scripts/python manage.py migrate`.

## Tests
- The local Postgres role cannot create databases, so run tests with the SQLite test settings:
  `cd backend && venv/Scripts/python manage.py test core.tests --settings=alphalpgas.settings_test`
  (`alphalpgas/settings_test.py` builds an in-memory DB directly from models, skipping migrations.)
- `Order.order_number` is a second-resolution timestamp; tests that create several invoices quickly should disconnect `core.signals.sync_invoice_item_to_order` (see `core/tests/test_stock.py`).

## Stock module (cylinders)
- Models: `core/models_stock.py` (`CylinderSize`, `GasStock` with `quantity`=full and `empty_quantity`, `StockMovement` with `quantity`=full change and `empty_change`, `StockPurchase[Item]`, `StockAlertSettings` singleton).
- `Product.cylinder_size` + `Product.stock_effect` (`exchange` / `deposit` / `deposit_refund` / `none`) decide how an invoice line moves stock. Set on the product edit form.
- Logic lives in `core/services/stock_service.py`; `InvoiceItem.save()` and a `pre_delete` signal call it, so create/edit/delete of invoice lines (UI, API, WhatsApp AI) all stay in sync. Reports read `InvoiceItem` directly, so history before the module existed is included.
- Daily low-stock WhatsApp check: `python manage.py check_stock_levels [--force] [--dry-run]`. Recipients/thresholds at `/accounting/stock/settings/`.
