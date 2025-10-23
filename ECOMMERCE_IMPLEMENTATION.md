# E-Commerce Enhancement Implementation Guide

## ✅ Completed: Backend Models

All e-commerce models have been added to `backend/core/models.py`:

### Models Created:
1. **DeliveryZone** - Manage delivery areas and fees
2. **PromoCode** - Discount codes with validation
3. **ProductVariant** - Product variations (size, type)
4. **Order** - Customer orders with full tracking
5. **OrderItem** - Order line items
6. **OrderStatusHistory** - Track order status changes

---

## 🔄 Next Steps to Complete Implementation

### Step 1: Update Admin Panel

Add to `backend/core/admin.py`:

```python
from .models import (
    HeroBanner, CompanySettings, Client, Category, Product, ProductVariant,
    Quote, QuoteItem, Invoice, InvoiceItem, Payment, CreditNote, CreditNoteItem,
    DeliveryZone, PromoCode, Order, OrderItem, OrderStatusHistory
)

@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'delivery_fee', 'minimum_order', 'estimated_delivery_time', 'is_active', 'order']
    list_editable = ['delivery_fee', 'is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['name', 'postal_codes']

@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'times_used', 'max_uses', 'valid_from', 'valid_until', 'is_active']
    list_filter = ['is_active', 'discount_type']
    search_fields = ['code', 'description']
    readonly_fields = ['times_used']

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'sku', 'price_adjustment', 'stock_quantity', 'is_active']
    list_filter = ['is_active', 'product']
    search_fields = ['name', 'sku']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total_price']

class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['created_at', 'created_by']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer_name', 'status', 'payment_status', 'total', 'created_at']
    list_filter = ['status', 'payment_status', 'payment_method', 'delivery_zone']
    search_fields = ['order_number', 'customer_name', 'customer_email', 'customer_phone']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
    fieldsets = (
        ('Order Info', {
            'fields': ('order_number', 'status', 'created_at', 'updated_at')
        }),
        ('Customer', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('Delivery', {
            'fields': ('delivery_address', 'delivery_zone', 'delivery_notes', 'estimated_delivery', 'delivered_at')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'delivery_fee', 'discount_amount', 'promo_code', 'total')
        }),
        ('Payment', {
            'fields': ('payment_method', 'payment_status', 'yoco_payment_id')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )
```

### Step 2: Create Serializers

Add to `backend/core/serializers.py`:

```python
class DeliveryZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryZone
        fields = '__all__'

class PromoCodeSerializer(serializers.ModelSerializer):
    is_valid_now = serializers.SerializerMethodField()
    
    class Meta:
        model = PromoCode
        fields = '__all__'
    
    def get_is_valid_now(self, obj):
        return obj.is_valid()

class ProductVariantSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductVariant
        fields = '__all__'
    
    def get_price(self, obj):
        return str(obj.get_price())

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    variant_name = serializers.CharField(source='variant.name', read_only=True, allow_null=True)
    
    class Meta:
        model = OrderItem
        fields = '__all__'

class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    delivery_zone_name = serializers.CharField(source='delivery_zone.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['order_number', 'created_at', 'updated_at']
```

### Step 3: Create Views

Add to `backend/core/views.py`:

```python
class DeliveryZoneViewSet(viewsets.ModelViewSet):
    queryset = DeliveryZone.objects.filter(is_active=True)
    serializer_class = DeliveryZoneSerializer
    permission_classes = [permissions.AllowAny]

class PromoCodeViewSet(viewsets.ModelViewSet):
    queryset = PromoCode.objects.all()
    serializer_class = PromoCodeSerializer
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['post'])
    def validate_code(self, request):
        code = request.data.get('code')
        order_total = Decimal(request.data.get('order_total', 0))
        
        try:
            promo = PromoCode.objects.get(code=code.upper())
            if not promo.is_valid():
                return Response({'error': 'Promo code is not valid'}, status=400)
            if order_total < promo.minimum_order:
                return Response({'error': f'Minimum order amount is R{promo.minimum_order}'}, status=400)
            
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
    queryset = ProductVariant.objects.filter(is_active=True)
    serializer_class = ProductVariantSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'is_active']

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.AllowAny]  # Change to IsAuthenticated for production
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'payment_status']
    search_fields = ['order_number', 'customer_name', 'customer_email']
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')
        
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response({'error': 'Invalid status'}, status=400)
        
        order.status = new_status
        order.save()
        
        OrderStatusHistory.objects.create(
            order=order,
            status=new_status,
            notes=notes,
            created_by=request.user if request.user.is_authenticated else None
        )
        
        return Response(OrderSerializer(order).data)
    
    @action(detail=True, methods=['post'])
    def process_yoco_payment(self, request, pk=None):
        order = self.get_object()
        payment_id = request.data.get('payment_id')
        
        # TODO: Verify payment with Yoco API
        
        order.yoco_payment_id = payment_id
        order.payment_status = 'paid'
        order.status = 'confirmed'
        order.save()
        
        return Response({'success': True, 'order': OrderSerializer(order).data})
```

### Step 4: Add URLs

Add to `backend/core/urls/accounting.py`:

```python
router.register(r'delivery-zones', DeliveryZoneViewSet, basename='delivery-zone')
router.register(r'promo-codes', PromoCodeViewSet, basename='promo-code')
router.register(r'product-variants', ProductVariantViewSet, basename='product-variant')
router.register(r'orders', OrderViewSet, basename='order')
```

### Step 5: Run Migrations

```bash
cd backend
.\venv\Scripts\python.exe manage.py makemigrations core
.\venv\Scripts\python.exe manage.py migrate core
```

---

## Frontend Implementation

### Step 6: Update Product Interface

Add to `frontend/app/page.tsx`:

```typescript
interface ProductVariant {
  id: number;
  name: string;
  sku: string;
  price_adjustment: string;
  price: string;
  stock_quantity: number;
  is_active: boolean;
}

interface Product {
  // ... existing fields
  variants?: ProductVariant[];
}

interface DeliveryZone {
  id: number;
  name: string;
  postal_codes: string;
  delivery_fee: string;
  minimum_order: string;
  estimated_delivery_time: string;
}

interface PromoCode {
  code: string;
  discount_type: string;
  discount_value: string;
  minimum_order: string;
}

interface OrderData {
  customer_name: string;
  customer_email: string;
  customer_phone: string;
  delivery_address: string;
  delivery_zone: number | null;
  delivery_notes: string;
  subtotal: string;
  delivery_fee: string;
  discount_amount: string;
  promo_code: number | null;
  total: string;
  payment_method: string;
  items: Array<{
    product: number;
    variant: number | null;
    quantity: number;
    unit_price: string;
  }>;
}
```

### Step 7: Add Local Storage for Cart

```typescript
// Load cart from localStorage on mount
useEffect(() => {
  const savedCart = localStorage.getItem('cart');
  if (savedCart) {
    setCart(JSON.parse(savedCart));
  }
}, []);

// Save cart to localStorage whenever it changes
useEffect(() => {
  localStorage.setItem('cart', JSON.stringify(cart));
}, [cart]);
```

### Step 8: Create Checkout Component

Create `frontend/components/Checkout.tsx`:

```typescript
'use client';

import { useState, useEffect } from 'react';

export default function Checkout({ cart, onClose, onOrderComplete }) {
  const [step, setStep] = useState(1); // 1: Details, 2: Delivery, 3: Payment
  const [deliveryZones, setDeliveryZones] = useState([]);
  const [selectedZone, setSelectedZone] = useState(null);
  const [promoCode, setPromoCode] = useState('');
  const [discount, setDiscount] = useState(0);
  
  const [formData, setFormData] = useState({
    customer_name: '',
    customer_email: '',
    customer_phone: '',
    delivery_address: '',
    delivery_notes: '',
    payment_method: 'cash'
  });

  // Fetch delivery zones
  useEffect(() => {
    fetch('http://localhost:8000/api/accounting/delivery-zones/')
      .then(res => res.json())
      .then(data => setDeliveryZones(data.results || data));
  }, []);

  const validatePromoCode = async () => {
    const subtotal = getCartTotal();
    const response = await fetch('http://localhost:8000/api/accounting/promo-codes/validate_code/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: promoCode, order_total: subtotal })
    });
    
    if (response.ok) {
      const data = await response.json();
      setDiscount(parseFloat(data.discount_amount));
    } else {
      alert('Invalid promo code');
    }
  };

  const submitOrder = async () => {
    const orderData = {
      ...formData,
      delivery_zone: selectedZone?.id || null,
      subtotal: getCartTotal().toFixed(2),
      delivery_fee: selectedZone?.delivery_fee || '0.00',
      discount_amount: discount.toFixed(2),
      total: (getCartTotal() + parseFloat(selectedZone?.delivery_fee || 0) - discount).toFixed(2),
      items: cart.map(item => ({
        product: item.product.id,
        variant: item.variant?.id || null,
        quantity: item.quantity,
        unit_price: item.product.unit_price
      }))
    };

    const response = await fetch('http://localhost:8000/api/accounting/orders/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(orderData)
    });

    if (response.ok) {
      const order = await response.json();
      onOrderComplete(order);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6">
        {/* Checkout form implementation */}
      </div>
    </div>
  );
}
```

---

## Yoco Payment Integration

### Step 9: Add Yoco SDK

Add to `frontend/app/layout.tsx`:

```tsx
<Script src="https://js.yoco.com/sdk/v1/yoco-sdk-web.js" />
```

### Step 10: Implement Yoco Payment

```typescript
const processYocoPayment = async (orderId: string, amount: number) => {
  const yoco = new window.YocoSDK({
    publicKey: 'YOUR_YOCO_PUBLIC_KEY'
  });

  yoco.showPopup({
    amountInCents: Math.round(amount * 100),
    currency: 'ZAR',
    name: 'Alpha LPGas',
    description: `Order #${orderId}`,
    callback: async function (result) {
      if (result.error) {
        alert('Payment failed: ' + result.error.message);
      } else {
        // Send payment ID to backend
        const response = await fetch(`http://localhost:8000/api/accounting/orders/${orderId}/process_yoco_payment/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ payment_id: result.id })
        });
        
        if (response.ok) {
          alert('Payment successful!');
        }
      }
    }
  });
};
```

---

## Order Tracking Component

### Step 11: Create Order Tracking Page

Create `frontend/app/track/[orderNumber]/page.tsx`:

```typescript
'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';

export default function TrackOrder() {
  const params = useParams();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`http://localhost:8000/api/accounting/orders/?search=${params.orderNumber}`)
      .then(res => res.json())
      .then(data => {
        if (data.results && data.results.length > 0) {
          setOrder(data.results[0]);
        }
        setLoading(false);
      });
  }, [params.orderNumber]);

  const statusSteps = [
    { key: 'pending', label: 'Order Placed', icon: '📝' },
    { key: 'confirmed', label: 'Confirmed', icon: '✅' },
    { key: 'preparing', label: 'Preparing', icon: '📦' },
    { key: 'out_for_delivery', label: 'Out for Delivery', icon: '🚚' },
    { key: 'delivered', label: 'Delivered', icon: '🎉' }
  ];

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4">
        <h1 className="text-3xl font-bold mb-8">Track Your Order</h1>
        
        {loading ? (
          <p>Loading...</p>
        ) : order ? (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <div className="mb-8">
              <h2 className="text-2xl font-bold">Order #{order.order_number}</h2>
              <p className="text-gray-600">Placed on {new Date(order.created_at).toLocaleDateString()}</p>
            </div>

            {/* Status Timeline */}
            <div className="relative">
              {statusSteps.map((step, index) => {
                const isComplete = statusSteps.findIndex(s => s.key === order.status) >= index;
                const isCurrent = step.key === order.status;
                
                return (
                  <div key={step.key} className="flex items-center mb-8">
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center text-2xl ${
                      isComplete ? 'bg-green-500' : 'bg-gray-200'
                    }`}>
                      {step.icon}
                    </div>
                    <div className="ml-4">
                      <p className={`font-semibold ${isCurrent ? 'text-green-600' : ''}`}>
                        {step.label}
                      </p>
                      {isCurrent && <p className="text-sm text-gray-600">Current Status</p>}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Order Details */}
            <div className="border-t pt-6 mt-6">
              <h3 className="font-bold text-lg mb-4">Order Items</h3>
              {order.items.map(item => (
                <div key={item.id} className="flex justify-between py-2">
                  <span>{item.quantity}x {item.product_name}</span>
                  <span>R{parseFloat(item.total_price).toFixed(2)}</span>
                </div>
              ))}
              <div className="border-t mt-4 pt-4">
                <div className="flex justify-between font-bold text-lg">
                  <span>Total</span>
                  <span>R{parseFloat(order.total).toFixed(2)}</span>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <p>Order not found</p>
        )}
      </div>
    </div>
  );
}
```

---

## Summary of Enhancements

### ✅ Implemented:
1. **Backend Models** - All e-commerce models created
2. **Database Schema** - Ready for migration

### 📋 To Complete:
1. **Admin Panel** - Add model registrations
2. **Serializers** - Create API serializers
3. **Views** - Add ViewSets and endpoints
4. **URLs** - Register new routes
5. **Migrations** - Run database migrations
6. **Frontend** - Implement checkout flow
7. **Local Storage** - Persist cart
8. **Yoco Integration** - Payment processing
9. **Order Tracking** - Track page
10. **Product Variants** - Variant selection

### Next Action:
Run the provided code snippets in order to complete the implementation.
