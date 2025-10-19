from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from datetime import datetime, date, timedelta
from decimal import Decimal
from .models import (
    CompanySettings, Client, Product, Quote, QuoteItem, Invoice, InvoiceItem,
    Payment, CreditNote, CreditNoteItem
)
from .serializers import (
    CompanySettingsSerializer, UserSerializer, ClientSerializer, ProductSerializer,
    QuoteSerializer, QuoteItemSerializer, InvoiceSerializer,
    InvoiceItemSerializer, PaymentSerializer, CreditNoteSerializer,
    CreditNoteItemSerializer
)


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


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet for managing products"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description', 'sku']
    ordering_fields = ['name', 'unit_price', 'created_at']


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
