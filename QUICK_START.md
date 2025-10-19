# Alpha LPGas - Quick Start Guide

Get up and running in 15 minutes!

## Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Git

## Quick Setup

### 1. Clone and Navigate

```bash
git clone <repository-url>
cd alpha-lpgas-new
```

### 2. Backend Setup (5 minutes)

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# OR Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
copy .env.example .env  # Windows
# OR
cp .env.example .env    # macOS/Linux

# Edit .env - Add your database credentials
# Minimum required:
# SECRET_KEY=your-secret-key
# DATABASE_URL=postgresql://postgres:password@localhost:5432/alphalpgas

# Create database
createdb alphalpgas

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start server
python manage.py runserver
```

Backend running at: http://localhost:8000

### 3. Frontend Setup (5 minutes)

Open new terminal:

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Create .env.local
copy .env.example .env.local  # Windows
# OR
cp .env.example .env.local    # macOS/Linux

# Edit .env.local - Minimum required:
# NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Start development server
npm run dev
```

Frontend running at: http://localhost:3000

### 4. Initial Setup (5 minutes)

1. **Access Admin**: http://localhost:8000/admin/
   - Login with superuser credentials

2. **Configure Company Settings**:
   - Go to Core > Company Settings
   - Update company information
   - Save

3. **Create Product Categories**:
   - Go to Shop > Categories
   - Add: "Gas Cylinders", "Accessories"

4. **Add Products**:
   - Go to Shop > Shop Products
   - Add sample products:
     - 9kg Gas Exchange - R340
     - 14kg Gas Exchange - R540
     - 19kg Gas Exchange - R730

5. **Create Delivery Zone**:
   - Go to Shop > Delivery Zones
   - Add: "Fish Hoek" - R0 delivery fee

6. **Test Frontend**:
   - Visit http://localhost:3000
   - Browse products
   - Test ordering flow

## Quick Commands

### Backend

```bash
# Run server
python manage.py runserver

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Run tests
python manage.py test
```

### Frontend

```bash
# Development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

## Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api
- **Django Admin**: http://localhost:8000/admin
- **Wagtail CMS**: http://localhost:8000/cms
- **API Docs**: http://localhost:8000/api/docs

## Default Test Data

After setup, you can create test data:

### Products
- 5kg Gas Exchange - R200
- 9kg Gas Exchange - R340
- 14kg Gas Exchange - R540
- 19kg Gas Exchange - R730
- 48kg Gas Exchange - R1830
- Bull Nose Regulator - R150
- Gas Hose (per metre) - R30

### Delivery Zones
- Fish Hoek - Free delivery
- Southern Suburbs - R50
- Cape Town CBD - R80

## Common Issues

### Port Already in Use

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:8000 | xargs kill -9
```

### Database Connection Error

- Ensure PostgreSQL is running
- Check DATABASE_URL in .env
- Verify database exists

### Module Not Found

```bash
# Ensure venv is activated
pip install -r requirements.txt
```

### CORS Error

- Check CORS_ALLOWED_ORIGINS in backend .env
- Ensure http://localhost:3000 is included
- Restart backend server

## Next Steps

1. **Configure OAuth**: See SETUP_GUIDE.md for Google OAuth setup
2. **Setup YOCO**: Add YOCO keys for payment testing
3. **Customize Design**: Update colors and branding
4. **Add Content**: Create pages in Wagtail CMS
5. **Deploy**: Follow DEPLOYMENT_GUIDE.md for production

## Need Help?

- **Full Setup Guide**: See SETUP_GUIDE.md
- **Deployment Guide**: See DEPLOYMENT_GUIDE.md
- **Project Summary**: See PROJECT_SUMMARY.md
- **Email**: info@alphalpgas.co.za
- **Phone**: 074 454 5665

## Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature
   ```

2. **Make Changes**
   - Edit code
   - Test locally

3. **Commit Changes**
   ```bash
   git add .
   git commit -m "Add your feature"
   ```

4. **Push and Create PR**
   ```bash
   git push origin feature/your-feature
   ```

## Testing Checklist

- [ ] Backend server starts without errors
- [ ] Frontend builds and runs
- [ ] Can access admin panel
- [ ] Can create products
- [ ] Can browse shop
- [ ] Can create test order
- [ ] API endpoints respond correctly

## Production Checklist

Before deploying to production:

- [ ] Change DEBUG=False
- [ ] Set strong SECRET_KEY
- [ ] Configure production database
- [ ] Setup HTTPS/SSL
- [ ] Configure CORS for production domain
- [ ] Add production OAuth credentials
- [ ] Add production YOCO keys
- [ ] Setup email SMTP
- [ ] Configure backups
- [ ] Test all features

---

**Ready to go!** 🚀

For detailed information, see the full documentation in SETUP_GUIDE.md and DEPLOYMENT_GUIDE.md.
