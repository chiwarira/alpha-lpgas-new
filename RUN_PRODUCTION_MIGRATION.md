# Run Migration on Railway Production

## Option 1: Using Railway CLI

1. **Install Railway CLI** (if not already installed):
```bash
npm install -g @railway/cli
```

2. **Login to Railway**:
```bash
railway login
```

3. **Link to your project**:
```bash
railway link
```

4. **Run the migration**:
```bash
railway run python manage.py migrate
```

## Option 2: Using Railway Dashboard

1. Go to your Railway project dashboard
2. Click on your Django service
3. Go to the **"Settings"** tab
4. Scroll to **"Deploy"** section
5. Add a **one-off command**:
   ```
   python manage.py migrate
   ```
6. Click **"Run"**

## Option 3: Add to Deployment Process

Update your Railway deployment to always run migrations:

1. In Railway dashboard, go to **Settings** → **Deploy**
2. Set **"Build Command"**:
   ```
   pip install -r requirements.txt
   ```
3. Set **"Start Command"**:
   ```
   python manage.py migrate && gunicorn alphalpgas.wsgi:application
   ```

This will automatically run migrations on every deployment.

## Verify Migration

After running, check the migration was applied:
```bash
railway run python manage.py showmigrations core
```

Look for:
```
[X] 0036_alter_creditnoteitem_quantity_and_more
```

The `[X]` means it's been applied.
