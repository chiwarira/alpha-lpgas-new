from rest_framework import viewsets, filters, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from datetime import datetime, date, timedelta
from decimal import Decimal
from .models import (
    HeroBanner, CompanySettings, Client, Category, Product, ProductVariant,
    Quote, QuoteItem, Invoice, InvoiceItem, Payment, CreditNote, CreditNoteItem,
    DeliveryZone, PromoCode, Order, OrderItem, OrderStatusHistory, ContactSubmission, Testimonial
)
from .serializers import (
    HeroBannerSerializer, CompanySettingsSerializer, UserSerializer, ClientSerializer, CategorySerializer, ProductSerializer,
    QuoteSerializer, QuoteItemSerializer, InvoiceSerializer,
    InvoiceItemSerializer, PaymentSerializer, CreditNoteSerializer, CreditNoteItemSerializer,
    DeliveryZoneSerializer, PromoCodeSerializer, ProductVariantSerializer, OrderSerializer, OrderItemSerializer, OrderStatusHistorySerializer,
    ContactSubmissionSerializer, TestimonialSerializer
)


class HeroBannerViewSet(viewsets.ModelViewSet):
    """ViewSet for managing hero banners"""
    queryset = HeroBanner.objects.filter(is_active=True)
    serializer_class = HeroBannerSerializer
    permission_classes = [permissions.AllowAny]  # Public access for website
    
    def get_queryset(self):
        queryset = HeroBanner.objects.all()
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset.order_by('order', '-created_at')


class CompanySettingsView(APIView):
    """API view for company settings (singleton)"""
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get(self, request):
        """Get company settings"""
        settings = CompanySettings.load()
        serializer = CompanySettingsSerializer(settings)
        return Response(serializer.data)
    
    def put(self, request):
        """Update company settings"""
        settings = CompanySettings.load()
        serializer = CompanySettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing users"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'email', 'date_joined']


class ClientViewSet(viewsets.ModelViewSet):
    """ViewSet for managing clients"""
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'country', 'state']
    search_fields = ['name', 'email', 'phone', 'tax_id', 'customer_id']
    ordering_fields = ['name', 'created_at', 'updated_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def invoices(self, request, pk=None):
        """Get all invoices for a client"""
        client = self.get_object()
        invoices = client.invoices.all()
        serializer = InvoiceSerializer(invoices, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def quotes(self, request, pk=None):
        """Get all quotes for a client"""
        client = self.get_object()
        quotes = client.quotes.all()
        serializer = QuoteSerializer(quotes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def statement(self, request, pk=None):
        """Get statement for a client with date range"""
        client = self.get_object()
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Get all invoices for the client within date range
        invoices = client.invoices.all().order_by('issue_date')
        if start_date:
            invoices = invoices.filter(issue_date__gte=start_date)
        if end_date:
            invoices = invoices.filter(issue_date__lte=end_date)
        
        # Calculate balance brought forward (invoices before start_date)
        balance_bf = Decimal('0.00')
        if start_date:
            previous_invoices = client.invoices.filter(issue_date__lt=start_date)
            balance_bf = sum(inv.balance for inv in previous_invoices)
        
        # Build statement data
        transactions = []
        running_balance = balance_bf
        
        for invoice in invoices:
            # Add invoice as debit
            running_balance += invoice.total_amount
            transactions.append({
                'date': invoice.issue_date,
                'invoice_number': invoice.invoice_number,
                'description': f'Invoice #{invoice.invoice_number}',
                'debit': float(invoice.total_amount),
                'credit': 0,
                'balance': float(running_balance),
                'status': invoice.status
            })
            
            # Add payments as credits
            for payment in invoice.payments.all():
                if (not start_date or payment.payment_date >= datetime.strptime(start_date, '%Y-%m-%d').date()) and \
                   (not end_date or payment.payment_date <= datetime.strptime(end_date, '%Y-%m-%d').date()):
                    running_balance -= payment.amount
                    transactions.append({
                        'date': payment.payment_date,
                        'invoice_number': invoice.invoice_number,
                        'description': f'Payment - {payment.payment_method}',
                        'debit': 0,
                        'credit': float(payment.amount),
                        'balance': float(running_balance),
                        'status': 'paid'
                    })
        
        # Calculate aging
        today = date.today()
        aging = {
            'current': Decimal('0.00'),
            '30_days': Decimal('0.00'),
            '60_days': Decimal('0.00'),
            '90_days': Decimal('0.00'),
            'over_90_days': Decimal('0.00'),
        }
        
        for invoice in client.invoices.filter(status__in=['sent', 'partially_paid', 'overdue']):
            days_overdue = (today - invoice.due_date).days
            if days_overdue < 0:
                aging['current'] += invoice.balance
            elif days_overdue <= 30:
                aging['30_days'] += invoice.balance
            elif days_overdue <= 60:
                aging['60_days'] += invoice.balance
            elif days_overdue <= 90:
                aging['90_days'] += invoice.balance
            else:
                aging['over_90_days'] += invoice.balance
        
        return Response({
            'client': ClientSerializer(client).data,
            'start_date': start_date,
            'end_date': end_date,
            'balance_brought_forward': float(balance_bf),
            'transactions': transactions,
            'total_debits': float(sum(t['debit'] for t in transactions)),
            'total_credits': float(sum(t['credit'] for t in transactions)),
            'total_balance': float(running_balance),
            'aging': {
                'current': float(aging['current']),
                '30_days': float(aging['30_days']),
                '60_days': float(aging['60_days']),
                '90_days': float(aging['90_days']),
                'over_90_days': float(aging['over_90_days']),
                'total': float(sum(aging.values()))
            }
        })


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing product categories"""
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]  # Public access for e-commerce
    
    def get_queryset(self):
        queryset = Category.objects.all()
        # Filter by active status if requested
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet for managing products"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]  # Public access for e-commerce
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'show_on_website', 'is_featured']
    search_fields = ['name', 'description', 'sku']
    ordering_fields = ['name', 'unit_price', 'created_at', 'order']
    
    def get_queryset(self):
        queryset = Product.objects.all()
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        # Filter by website visibility
        show_on_website = self.request.query_params.get('show_on_website', None)
        if show_on_website is not None:
            queryset = queryset.filter(show_on_website=show_on_website.lower() == 'true')
        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category__slug=category)
        # Filter featured products
        is_featured = self.request.query_params.get('is_featured', None)
        if is_featured is not None:
            queryset = queryset.filter(is_featured=is_featured.lower() == 'true')
        return queryset.select_related('category')


class QuoteViewSet(viewsets.ModelViewSet):
    """ViewSet for managing quotes"""
    queryset = Quote.objects.all()
    serializer_class = QuoteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'client']
    search_fields = ['quote_number', 'client__name']
    ordering_fields = ['quote_number', 'issue_date', 'expiry_date', 'total_amount', 'created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def calculate_totals(self, request, pk=None):
        """Recalculate quote totals"""
        quote = self.get_object()
        quote.calculate_totals()
        serializer = self.get_serializer(quote)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def convert_to_invoice(self, request, pk=None):
        """Convert quote to invoice"""
        quote = self.get_object()
        
        # Create invoice from quote
        invoice = Invoice.objects.create(
            invoice_number=request.data.get('invoice_number'),
            client=quote.client,
            quote=quote,
            issue_date=request.data.get('issue_date'),
            due_date=request.data.get('due_date'),
            status='draft',
            subtotal=quote.subtotal,
            tax_amount=quote.tax_amount,
            total_amount=quote.total_amount,
            notes=quote.notes,
            terms=quote.terms,
            created_by=request.user
        )
        
        # Copy quote items to invoice items
        for quote_item in quote.items.all():
            InvoiceItem.objects.create(
                invoice=invoice,
                product=quote_item.product,
                description=quote_item.description,
                quantity=quote_item.quantity,
                unit_price=quote_item.unit_price,
                tax_rate=quote_item.tax_rate
            )
        
        # Update quote status
        quote.status = 'accepted'
        quote.save()
        
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class QuoteItemViewSet(viewsets.ModelViewSet):
    """ViewSet for managing quote items"""
    queryset = QuoteItem.objects.all()
    serializer_class = QuoteItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['quote', 'product']


class InvoiceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing invoices"""
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'client']
    search_fields = ['invoice_number', 'client__name']
    ordering_fields = ['invoice_number', 'issue_date', 'due_date', 'total_amount', 'created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def calculate_totals(self, request, pk=None):
        """Recalculate invoice totals"""
        invoice = self.get_object()
        invoice.calculate_totals()
        serializer = self.get_serializer(invoice)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def payments(self, request, pk=None):
        """Get all payments for an invoice"""
        invoice = self.get_object()
        payments = invoice.payments.all()
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)


class InvoiceItemViewSet(viewsets.ModelViewSet):
    """ViewSet for managing invoice items"""
    queryset = InvoiceItem.objects.all()
    serializer_class = InvoiceItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['invoice', 'product']


class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing payments"""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['invoice', 'payment_method']
    search_fields = ['payment_number', 'reference_number', 'invoice__invoice_number']
    ordering_fields = ['payment_number', 'payment_date', 'amount', 'created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class CreditNoteViewSet(viewsets.ModelViewSet):
    """ViewSet for managing credit notes"""
    queryset = CreditNote.objects.all()
    serializer_class = CreditNoteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'client', 'invoice']
    search_fields = ['credit_note_number', 'client__name', 'invoice__invoice_number']
    ordering_fields = ['credit_note_number', 'issue_date', 'total_amount', 'created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def calculate_totals(self, request, pk=None):
        """Recalculate credit note totals"""
        credit_note = self.get_object()
        credit_note.calculate_totals()
        serializer = self.get_serializer(credit_note)
        return Response(serializer.data)


class CreditNoteItemViewSet(viewsets.ModelViewSet):
    """ViewSet for managing credit note items"""
    queryset = CreditNoteItem.objects.all()
    serializer_class = CreditNoteItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['credit_note', 'product']


# E-commerce ViewSets

class DeliveryZoneViewSet(viewsets.ModelViewSet):
    """ViewSet for managing delivery zones"""
    queryset = DeliveryZone.objects.filter(is_active=True)
    serializer_class = DeliveryZoneSerializer
    permission_classes = [permissions.AllowAny]  # Public access for website


class PromoCodeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing promo codes"""
    queryset = PromoCode.objects.all()
    serializer_class = PromoCodeSerializer
    permission_classes = [permissions.AllowAny]  # Public access for validation
    
    @action(detail=False, methods=['post'])
    def validate_code(self, request):
        """Validate a promo code"""
        code = request.data.get('code', '').upper()
        order_total = Decimal(request.data.get('order_total', 0))
        
        try:
            promo = PromoCode.objects.get(code=code)
            
            # Check if valid
            if not promo.is_valid():
                return Response({'error': 'Promo code is not valid or has expired'}, status=400)
            
            # Check minimum order
            if order_total < promo.minimum_order:
                return Response({
                    'error': f'Minimum order amount is R{promo.minimum_order}'
                }, status=400)
            
            # Calculate discount
            if promo.discount_type == 'percentage':
                discount = order_total * (promo.discount_value / 100)
            else:
                discount = promo.discount_value
            
            return Response({
                'valid': True,
                'discount_amount': str(discount),
                'promo_code': PromoCodeSerializer(promo).data
            })
        except PromoCode.DoesNotExist:
            return Response({'error': 'Invalid promo code'}, status=404)


class ProductVariantViewSet(viewsets.ModelViewSet):
    """ViewSet for managing product variants"""
    queryset = ProductVariant.objects.filter(is_active=True)
    serializer_class = ProductVariantSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'is_active']


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for managing orders"""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.AllowAny]  # Change to IsAuthenticated for production
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'payment_status', 'payment_method']
    search_fields = ['order_number', 'customer_name', 'customer_email', 'customer_phone']
    
    def create(self, request, *args, **kwargs):
        """Create order with items"""
        try:
            # Get items data without modifying request.data
            items_data = request.data.get('items', [])
            
            # Create order data without items
            order_data = {k: v for k, v in request.data.items() if k != 'items'}
            
            print(f"Creating order with data: {order_data}")
            print(f"Items data: {items_data}")
            
            # Create order
            serializer = self.get_serializer(data=order_data)
            serializer.is_valid(raise_exception=True)
            order = serializer.save()
            
            print(f"Order created: {order.order_number}")
            
            # Create order items
            from decimal import Decimal
            for item_data in items_data:
                print(f"Creating item with unit_price: {item_data['unit_price']} (type: {type(item_data['unit_price'])})")
                OrderItem.objects.create(
                    order=order,
                    product_id=item_data['product'],
                    variant_id=item_data.get('variant'),
                    quantity=item_data['quantity'],
                    unit_price=Decimal(str(item_data['unit_price']))
                )
            
            print(f"Created {len(items_data)} order items")
            
            # Create initial status history
            OrderStatusHistory.objects.create(
                order=order,
                status='pending',
                notes='Order created'
            )
            
            # Increment promo code usage if applicable
            if order.promo_code:
                order.promo_code.times_used += 1
                order.promo_code.save()
            
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            print(f"ERROR creating order: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update order status"""
        order = self.get_object()
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')
        
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response({'error': 'Invalid status'}, status=400)
        
        order.status = new_status
        
        # Update delivered_at if status is delivered
        if new_status == 'delivered':
            from django.utils import timezone
            order.delivered_at = timezone.now()
        
        order.save()
        
        # Create status history entry
        OrderStatusHistory.objects.create(
            order=order,
            status=new_status,
            notes=notes,
            created_by=request.user if request.user.is_authenticated else None
        )
        
        return Response(OrderSerializer(order).data)
    
    @action(detail=True, methods=['post'])
    def process_yoco_payment(self, request, pk=None):
        """Process Yoco payment"""
        from django.conf import settings
        import requests
        import logging
        
        logger = logging.getLogger(__name__)
        order = self.get_object()
        payment_id = request.data.get('payment_id')
        
        # Verify payment with Yoco API using secret key
        if settings.YOCO_SECRET_KEY and not settings.DEBUG:
            # Only verify in production
            try:
                # Verify the payment with Yoco
                headers = {
                    'Authorization': f'Bearer {settings.YOCO_SECRET_KEY}',
                    'Content-Type': 'application/json'
                }
                
                # Get payment details from Yoco
                yoco_response = requests.get(
                    f'https://api.yoco.com/v1/charges/{payment_id}',
                    headers=headers,
                    timeout=10
                )
                
                if yoco_response.status_code == 200:
                    payment_data = yoco_response.json()
                    
                    # Verify payment amount matches order total
                    expected_amount = int(float(order.total) * 100)  # Convert to cents
                    actual_amount = payment_data.get('amount')
                    
                    if actual_amount != expected_amount:
                        logger.error(f'Payment amount mismatch: expected {expected_amount}, got {actual_amount}')
                        return Response({
                            'error': 'Payment amount mismatch'
                        }, status=400)
                    
                    # Verify payment status
                    if payment_data.get('status') != 'successful':
                        logger.error(f'Payment not successful: {payment_data.get("status")}')
                        return Response({
                            'error': 'Payment not successful'
                        }, status=400)
                else:
                    logger.error(f'Yoco API returned status {yoco_response.status_code}: {yoco_response.text}')
                    # In test mode, continue anyway
                    if settings.DEBUG:
                        logger.warning('Skipping verification in DEBUG mode')
                    else:
                        return Response({
                            'error': 'Failed to verify payment with Yoco'
                        }, status=400)
                    
            except Exception as e:
                logger.error(f'Payment verification error: {str(e)}')
                # In test mode, continue anyway
                if settings.DEBUG:
                    logger.warning(f'Skipping verification due to error in DEBUG mode: {str(e)}')
                else:
                    return Response({
                        'error': f'Payment verification failed: {str(e)}'
                    }, status=400)
        else:
            # Skip verification in DEBUG mode or if secret key not set
            logger.info(f'Skipping Yoco verification (DEBUG={settings.DEBUG}, SECRET_KEY_SET={bool(settings.YOCO_SECRET_KEY)})')
        
        # Update order
        order.yoco_payment_id = payment_id
        order.payment_status = 'paid'
        order.status = 'confirmed'
        order.save()
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            status='confirmed',
            notes=f'Payment received via Yoco (ID: {payment_id})'
        )
        
        return Response({'success': True, 'order': OrderSerializer(order).data})


class ContactSubmissionViewSet(viewsets.ModelViewSet):
    """ViewSet for contact form submissions"""
    queryset = ContactSubmission.objects.all()
    serializer_class = ContactSubmissionSerializer
    permission_classes = [permissions.AllowAny]  # Allow anyone to submit
    http_method_names = ['get', 'post', 'head', 'options']  # Only allow GET and POST
    
    def get_permissions(self):
        """Only staff can view submissions, anyone can create"""
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [permissions.AllowAny()]
    
    def create(self, request, *args, **kwargs):
        """Create a new contact submission and send email notification"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Send email notification (optional)
        self.send_notification_email(serializer.instance)
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            {'success': True, 'message': 'Thank you for contacting us! We will get back to you soon.'},
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    def send_notification_email(self, submission):
        """Send email notification to admin when new contact form is submitted"""
        from django.core.mail import send_mail
        from django.conf import settings
        
        print("=" * 50)
        print("ATTEMPTING TO SEND EMAIL NOTIFICATION")
        print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
        print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        print("=" * 50)
        
        try:
            subject = f'New Contact Form Submission: {submission.subject or "No Subject"}'
            message = f"""
New contact form submission received:

Name: {submission.name}
Email: {submission.email}
Phone: {submission.phone or 'Not provided'}
Subject: {submission.subject or 'No subject'}

Message:
{submission.message}

---
Submitted at: {submission.created_at.strftime('%Y-%m-%d %H:%M:%S')}
IP Address: {submission.ip_address or 'Unknown'}
            """
            
            print(f"Sending email to: {settings.DEFAULT_FROM_EMAIL}")
            print(f"Subject: {subject}")
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.DEFAULT_FROM_EMAIL],  # Send to company email
                fail_silently=False,  # Show errors for debugging
            )
            
            print("✓ Email sent successfully!")
            
        except Exception as e:
            # Log error but don't fail the request
            print(f"✗ Failed to send contact form notification email: {e}")
            import traceback
            traceback.print_exc()


class TestimonialViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for testimonials - Read only for public"""
    queryset = Testimonial.objects.filter(is_active=True)
    serializer_class = TestimonialSerializer
    permission_classes = [permissions.AllowAny]  # Public access
    
    def get_queryset(self):
        """Return active testimonials ordered by display order"""
        return Testimonial.objects.filter(is_active=True).order_by('order', '-created_at')
