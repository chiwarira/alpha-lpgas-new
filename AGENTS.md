# Alpha LPGas - agent notes

## Layout
- `backend/` Django 4.2 (apps: `core`, `cms`). Staff accounting UI is server-rendered under `/accounting/` (`core/urls/forms.py`, templates in `backend/templates/core/`). Nav lives in `templates/core/base.html`.
- `frontend/` Next.js 14 public site.

## Running locally
- Backend: `cd backend && venv/Scripts/python manage.py runserver 8000` (Windows venv at `backend/venv`). Uses local Postgres from `backend/.env` (`DATABASE_URL`).
- Apply migrations: `venv/Scripts/python manage.py migrate`.

## Deployment
- Backend + frontend both deploy on Vercel (project `alpha-lpgas-backend` / repo linked via root `.vercel/`).
- `main` → production (`api.alphalpgas.co.za`); `dev` → preview deploy aliased to `api-staging.alphalpgas.co.za` (`vercel ls` / `vercel inspect` to check).
- GitHub Actions run migrations on push: `migrate-staging.yml` (dev → `DATABASE_URL_STAGING`) and `migrate.yml` (main → `DATABASE_URL`). No code-deploy workflow — Vercel's Git integration handles that.
- `settings.py` extends `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS`/CORS for `*.vercel.app` + `*.alphalpgas.co.za` when `VERCEL_ENV` is set.

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

## Fleet module (vehicles)
- Models: `core/models_fleet.py` (`Vehicle`, `VehicleServiceRecord`, `VehicleAssignment` = daily driver↔vehicle roster, unique per driver/day and per vehicle/day).
- `Driver.default_vehicle` is the fallback; `Driver.get_vehicle_for_date(date)` = roster assignment else default. Old `Driver.vehicle_*` fields were migrated to `Vehicle` rows (migration `0047`) and removed (`0048`).
- `Invoice.assigned_driver` is required on the invoice form (nullable in DB for API/WhatsApp-created invoices). `Invoice.assigned_vehicle` auto-fills from the roster for the invoice date unless explicitly chosen; `Order.assigned_vehicle` copies through `core.signals` (`create_order_from_invoice` / `sync_order_from_invoice`).
- UI: `/accounting/vehicles/` CRUD, `/accounting/vehicles/assignments/` daily roster, service log on vehicle detail (updates `last_service_date`/`next_service_due_date` via `update_service_dates`). Nav entries gated by `UserMenuPermission.can_see_vehicles`.

## Driver portal
- Server-rendered mobile UI at `/driver/` (`core/urls/driver_portal.py`, `views_driver_portal.py`, `templates/core/driver_portal/`). Login at `/driver/login/` requires a `Driver` profile (`driver_required` decorator).
- Drivers see orders in `pending`/`confirmed`/`preparing`/`out_for_delivery`/`failed` and can advance them: `out_for_delivery` → `delivered` or `failed` (requires `delivery_failure_reason`); `failed` can be re-attempted (`driver_update_status`). `get_active_deliveries()` includes `pending`/`failed` so assigned orders appear without a manual confirm step.
- Daily stock check: `DriverStockCount` + `DriverStockCountItem` (`models_fleet.py`) hold opening/restock/closing counts per `CylinderSize`. `stock_check_required` redirects every portal page to `/driver/stock-check/` until today's opening count is submitted (one opening + one closing per day via partial unique constraint; restocks unlimited). Staff report at `/accounting/stock/driver-stock/`.
- Proof of delivery: `Order.pod_photo` (file upload) and `Order.pod_signature` (canvas → base64 → `ContentFile`) captured on "Mark as Delivered". COD: `driver_collect_cash` sets `payment_status='paid'` and creates a `Payment` (auto-numbers and updates the invoice's paid_amount).
- PWA: manifest served as a view at `/driver/manifest.json` and service worker at `/driver/sw.js` (view `driver_sw` reads `static/driver/sw.js` via `finders`) so registration scope covers `/driver/`. Icons generated from `static/alpha-lpgas-logo.png` into `static/driver/icons/` — remember `collectstatic` after changing static files (whitenoise manifest storage).
