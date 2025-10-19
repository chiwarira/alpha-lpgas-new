# Alpha LPGas - Modern Gas Delivery Platform

A comprehensive full-stack web application for LPG gas delivery with integrated accounting system, built with Django, PostgreSQL, React, and Next.js.

## 🚀 Features

### Public Website
- **Modern E-Commerce**: Browse and order gas cylinders online (5kg, 9kg, 14kg, 19kg, 48kg)
- **Delivery Scheduling**: Choose preferred delivery date and time slots
- **Delivery Zones**: Area-based delivery with dynamic pricing
- **Product Catalog**: Featured products, categories, and search functionality
- **Customer Reviews**: Rate and review products
- **Responsive Design**: Mobile-first design with Tailwind CSS

### Customer Features
- **User Accounts**: Register with email or Google OAuth
- **Order Tracking**: View order history and status
- **Saved Addresses**: Store multiple delivery addresses
- **Secure Payments**: YOCO payment gateway integration

### Accounting System (Staff Only)
- **Client Management**: Track customer information and transaction history
- **Product/Service Management**: Maintain catalog with VAT-inclusive pricing
- **Quote Generation**: Create and send quotes to clients
- **Quote to Invoice Conversion**: Convert accepted quotes into invoices
- **Invoice Management**: Generate invoices, track payment status
- **Payment Tracking**: Record and monitor payments
- **Credit Notes**: Issue credit notes for returns or adjustments
- **Client Statements**: Generate detailed account statements with aging
- **VAT Calculation**: Automatic VAT extraction from VAT-inclusive prices

### CMS (Content Management)
- **Wagtail CMS**: Manage website content, blog posts, and pages
- **Rich Text Editor**: Create engaging content with images and formatting
- **SEO Optimization**: Meta tags and descriptions for better search visibility

## 🛠️ Tech Stack

### Backend
- **Django 4.2.7**: Python web framework
- **Django REST Framework**: RESTful API
- **PostgreSQL**: Production database
- **Wagtail 5.2**: CMS functionality
- **Celery + Redis**: Async task processing
- **JWT Authentication**: Secure token-based auth
- **Google OAuth**: Social authentication

### Frontend
- **Next.js 14**: React framework with SSR
- **React 18**: UI library
- **Tailwind CSS**: Utility-first styling
- **Axios**: HTTP client
- **React Query**: Data fetching and caching
- **Zustand**: State management

### Payment & Integration
- **YOCO**: Payment gateway for South Africa
- **WhatsApp Business API**: Order notifications (optional)

### Deployment
- **DigitalOcean**: Cloud hosting
- **Nginx**: Web server
- **Gunicorn**: WSGI server
- **Let's Encrypt**: SSL certificates

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Redis (for Celery)
- Git

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd alpha-lpgas-new
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
copy .env.example .env
# Edit .env with your configuration

# Create PostgreSQL database
createdb alphalpgas

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load initial data (optional)
python manage.py loaddata initial_data.json

# Start development server
python manage.py runserver
```

Backend will be available at `http://localhost:8000`

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create .env.local file
copy .env.example .env.local
# Edit .env.local with your configuration

# Start development server
npm run dev
```

Frontend will be available at `http://localhost:3000`

### 4. Start Celery (Optional - for async tasks)

```bash
# In a new terminal, activate venv and run:
celery -A alphalpgas worker -l info
```

## 🔐 Environment Variables

### Backend (.env)

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/alphalpgas

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# YOCO Payment
YOCO_SECRET_KEY=your-yoco-secret-key
YOCO_PUBLIC_KEY=your-yoco-public-key

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=info@alphalpgas.co.za
EMAIL_HOST_PASSWORD=your-password

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_YOCO_PUBLIC_KEY=your-yoco-public-key
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id
```

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/api/docs/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

### Main API Endpoints

#### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login
- `POST /api/auth/google/` - Google OAuth login
- `POST /api/auth/token/refresh/` - Refresh JWT token

#### Shop (Public)
- `GET /api/shop/products/` - List products
- `GET /api/shop/categories/` - List categories
- `GET /api/shop/delivery-zones/` - List delivery zones
- `POST /api/shop/orders/` - Create order
- `GET /api/shop/orders/` - List user orders

#### Accounting (Staff Only)
- `GET /api/accounting/clients/` - List clients
- `GET /api/accounting/invoices/` - List invoices
- `GET /api/accounting/quotes/` - List quotes
- `GET /api/accounting/payments/` - List payments
- `GET /api/accounting/settings/` - Company settings

## 🎨 Frontend Structure

```
frontend/
├── app/                    # Next.js app directory
│   ├── (public)/          # Public pages
│   │   ├── page.tsx       # Home page
│   │   ├── shop/          # Shop pages
│   │   ├── about/         # About page
│   │   └── contact/       # Contact page
│   ├── (auth)/            # Auth pages
│   │   ├── login/
│   │   └── register/
│   └── (dashboard)/       # Admin dashboard
│       ├── dashboard/
│       ├── clients/
│       ├── invoices/
│       ├── quotes/
│       └── payments/
├── components/            # Reusable components
│   ├── ui/               # UI components
│   ├── shop/             # Shop components
│   └── dashboard/        # Dashboard components
├── lib/                  # Utilities
│   ├── api.ts           # API client
│   └── utils.ts         # Helper functions
└── public/              # Static assets
```

## 🚀 Deployment

### DigitalOcean Deployment

1. **Create Droplet**
   - Ubuntu 22.04 LTS
   - 2GB RAM minimum
   - Add SSH key

2. **Create Managed PostgreSQL Database**
   - PostgreSQL 12+
   - Note connection details

3. **Deploy Backend**
   ```bash
   # SSH into droplet
   ssh root@your-droplet-ip
   
   # Clone repository
   git clone <repository-url>
   cd alpha-lpgas-new/backend
   
   # Install dependencies
   sudo apt update
   sudo apt install python3-pip python3-venv nginx
   
   # Setup application
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Configure environment
   nano .env
   # Add production settings
   
   # Run migrations
   python manage.py migrate
   python manage.py collectstatic
   
   # Setup Gunicorn and Nginx
   # (See deployment guide for detailed steps)
   ```

4. **Deploy Frontend**
   ```bash
   # Build Next.js app
   cd frontend
   npm install
   npm run build
   
   # Deploy to Vercel or serve with Nginx
   ```

5. **SSL Certificate**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

## 🧪 Testing

```bash
# Backend tests
cd backend
python manage.py test

# Frontend tests
cd frontend
npm test
```

## 📱 Future Enhancements

- [ ] Mobile app (React Native)
- [ ] PDF generation for invoices/quotes
- [ ] Email notifications
- [ ] SMS notifications
- [ ] Advanced reporting and analytics
- [ ] Recurring orders
- [ ] Loyalty program
- [ ] Multi-language support
- [ ] Inventory management
- [ ] Driver app for deliveries

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is proprietary software owned by Alpha LPGas.

## 📞 Support

For support, email info@alphalpgas.co.za or call 074 454 5665.

## 🙏 Acknowledgments

- Inspired by leading gas delivery platforms: gas24.co.za, gas2home.co.za, epggas.co.za
- Built with modern best practices and security in mind
- Designed for scalability and future mobile app integration
