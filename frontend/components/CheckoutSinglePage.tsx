'use client';

import { useState, useEffect } from 'react';

interface Product {
  id: number;
  name: string;
  unit_price: string;
}

interface CartItem {
  product: Product;
  quantity: number;
  variant?: any;
  includeCylinder?: boolean;
  cylinderProduct?: Product;
}

interface DeliveryZone {
  id: number;
  name: string;
  postal_codes: string;
  delivery_fee: string;
  minimum_order: string;
  estimated_delivery_time: string;
}

interface CheckoutProps {
  cart: CartItem[];
  onClose: () => void;
  onOrderComplete: (order: any) => void;
  getCartTotal: () => number;
}

export default function Checkout({ cart, onClose, onOrderComplete, getCartTotal }: CheckoutProps) {
  const [deliveryZones, setDeliveryZones] = useState<DeliveryZone[]>([]);
  const [selectedZone, setSelectedZone] = useState<DeliveryZone | null>(null);
  const [promoCode, setPromoCode] = useState('');
  const [discount, setDiscount] = useState(0);
  const [promoError, setPromoError] = useState('');
  const [promoSuccess, setPromoSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [postalCode, setPostalCode] = useState('');
  const [showingYoco, setShowingYoco] = useState(false);
  
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
      .then(data => setDeliveryZones(data.results || data))
      .catch(err => console.error('Error fetching zones:', err));
  }, []);

  // Auto-detect zone from postal code
  useEffect(() => {
    if (postalCode.length >= 4) {
      const zone = deliveryZones.find(z => 
        z.postal_codes.split(',').some(pc => pc.trim() === postalCode.trim())
      );
      if (zone) {
        setSelectedZone(zone);
      }
    }
  }, [postalCode, deliveryZones]);

  const validatePromoCode = async () => {
    setPromoError('');
    setPromoSuccess('');
    
    if (!promoCode.trim()) {
      setPromoError('Please enter a promo code');
      return;
    }

    const subtotal = getCartTotal();
    try {
      const response = await fetch('http://localhost:8000/api/accounting/promo-codes/validate_code/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: promoCode.toUpperCase(), order_total: subtotal })
      });
      
      if (response.ok) {
        const data = await response.json();
        setDiscount(parseFloat(data.discount_amount));
        setPromoSuccess(`Promo code applied! You saved R${parseFloat(data.discount_amount).toFixed(2)}`);
      } else {
        const error = await response.json();
        setPromoError(error.error || 'Invalid promo code');
        setDiscount(0);
      }
    } catch (error) {
      setPromoError('Failed to validate promo code');
      setDiscount(0);
    }
  };

  const removePromoCode = () => {
    setPromoCode('');
    setDiscount(0);
    setPromoError('');
    setPromoSuccess('');
  };

  const calculateTotal = () => {
    const subtotal = getCartTotal();
    const deliveryFee = selectedZone ? parseFloat(selectedZone.delivery_fee) : 0;
    return subtotal + deliveryFee - discount;
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const validateForm = () => {
    if (!formData.customer_name.trim()) {
      alert('Please enter your name');
      return false;
    }
    if (!formData.customer_phone.trim()) {
      alert('Please enter your phone number');
      return false;
    }
    if (!formData.delivery_address.trim()) {
      alert('Please enter your delivery address');
      return false;
    }
    if (!selectedZone) {
      alert('Please select a delivery zone or enter a valid postal code');
      return false;
    }
    const subtotal = getCartTotal();
    if (subtotal < parseFloat(selectedZone.minimum_order)) {
      alert(`Minimum order for ${selectedZone.name} is R${selectedZone.minimum_order}`);
      return false;
    }
    return true;
  };

  const submitOrder = async () => {
    if (!validateForm()) return;
    
    setLoading(true);
    
    // For Yoco payments, don't create order yet - wait for payment success
    if (formData.payment_method === 'yoco') {
      // Prepare order data but don't submit yet
      const subtotal = Number(getCartTotal());
      const deliveryFee = selectedZone ? Number(selectedZone.delivery_fee) : 0;
      const discountAmount = Number(discount);
      const total = subtotal + deliveryFee - discountAmount;
      
      const orderData = {
        customer_name: formData.customer_name,
        customer_email: formData.customer_email,
        customer_phone: formData.customer_phone,
        delivery_address: formData.delivery_address,
        delivery_notes: formData.delivery_notes,
        payment_method: 'yoco',
        delivery_zone: selectedZone?.id || null,
        subtotal: subtotal.toFixed(2),
        delivery_fee: deliveryFee.toFixed(2),
        discount_amount: discountAmount.toFixed(2),
        total: total.toFixed(2),
        items: cart.flatMap(item => {
          const items = [{
            product: item.product.id,
            variant: item.variant?.id || null,
            quantity: item.quantity,
            unit_price: item.product.unit_price
          }];
          
          // Add cylinder as separate line item if included
          if (item.includeCylinder && item.cylinderProduct) {
            items.push({
              product: item.cylinderProduct.id,
              variant: null,
              quantity: item.quantity,
              unit_price: item.cylinderProduct.unit_price
            });
          }
          
          return items;
        })
      };
      
      console.log('Prepared order data:', orderData);
      
      // Process Yoco payment first, then create order
      processYocoPayment(orderData);
      return;
    }
    
    // For other payment methods, create order immediately
    const subtotal = Number(getCartTotal());
    const deliveryFee = selectedZone ? Number(selectedZone.delivery_fee) : 0;
    const discountAmount = Number(discount);
    const total = subtotal + deliveryFee - discountAmount;
    
    const orderData = {
      customer_name: formData.customer_name,
      customer_email: formData.customer_email,
      customer_phone: formData.customer_phone,
      delivery_address: formData.delivery_address,
      delivery_notes: formData.delivery_notes,
      payment_method: formData.payment_method,
      delivery_zone: selectedZone?.id || null,
      subtotal: subtotal.toFixed(2),
      delivery_fee: deliveryFee.toFixed(2),
      discount_amount: discountAmount.toFixed(2),
      total: total.toFixed(2),
      items: cart.flatMap(item => {
        const items = [{
          product: item.product.id,
          variant: item.variant?.id || null,
          quantity: item.quantity,
          unit_price: item.product.unit_price
        }];
        
        // Add cylinder as separate line item if included
        if (item.includeCylinder && item.cylinderProduct) {
          items.push({
            product: item.cylinderProduct.id,
            variant: null,
            quantity: item.quantity,
            unit_price: item.cylinderProduct.unit_price
          });
        }
        
        return items;
      })
    };

    try {
      const response = await fetch('http://localhost:8000/api/accounting/orders/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(orderData)
      });

      if (response.ok) {
        const order = await response.json();
        localStorage.removeItem('cart');
        onOrderComplete(order);
        setLoading(false);
      } else {
        const error = await response.json();
        alert('Failed to create order: ' + JSON.stringify(error));
        setLoading(false);
      }
    } catch (error) {
      alert('Error creating order: ' + error);
      setLoading(false);
    }
  };

  const processYocoPayment = (orderData: any) => {
    const yocoPublicKey = process.env.NEXT_PUBLIC_YOCO_PUBLIC_KEY;
    
    if (!yocoPublicKey) {
      alert('Yoco payment not configured. Please add NEXT_PUBLIC_YOCO_PUBLIC_KEY to .env.local');
      setLoading(false);
      return;
    }

    // Check if Yoco SDK is loaded
    // @ts-ignore
    if (typeof window.YocoSDK === 'undefined') {
      alert('Yoco SDK not loaded. Please refresh the page and try again.');
      setLoading(false);
      return;
    }

    // Hide checkout modal while Yoco is showing
    setShowingYoco(true);

    try {
      // @ts-ignore
      const yoco = new window.YocoSDK({
        publicKey: yocoPublicKey
      });

      const amountInCents = Math.round(parseFloat(orderData.total) * 100);
      
      console.log('Initiating Yoco payment:', {
        amount: amountInCents,
        publicKey: yocoPublicKey.substring(0, 10) + '...'
      });

      yoco.showPopup({
        amountInCents: amountInCents,
        currency: 'ZAR',
        name: 'Alpha LPGas',
        description: 'Gas Delivery Order',
        callback: function (result: any) {
          console.log('Yoco callback received:', result);
          setShowingYoco(false);
          
          if (result.error) {
            const errorMessage = result.error.message || 'Payment failed';
            console.error('Yoco payment error:', result.error);
            alert('Payment failed: ' + errorMessage);
            setLoading(false);
          } else {
            console.log('Payment successful, creating order...');
            // Payment successful - now create the order with payment ID
            const orderWithPayment = {
              ...orderData,
              payment_method: 'yoco',
              yoco_payment_id: result.id
            };
            
            console.log('Order data being sent:', orderWithPayment);
            
            fetch('http://localhost:8000/api/accounting/orders/', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(orderWithPayment)
            })
            .then(response => {
              console.log('Order creation response status:', response.status);
              if (response.ok) {
                return response.json();
              } else {
                // Try to parse as JSON, if fails, get text
                return response.text().then(text => {
                  console.error('Order creation error response:', text);
                  try {
                    const err = JSON.parse(text);
                    throw new Error(JSON.stringify(err));
                  } catch {
                    throw new Error(`Server error (${response.status}): ${text.substring(0, 200)}`);
                  }
                });
              }
            })
            .then(order => {
              console.log('Order created, processing payment...');
              // Update order with payment status
              return fetch(`http://localhost:8000/api/accounting/orders/${order.id}/process_yoco_payment/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ payment_id: result.id })
              })
              .then(res => {
                if (res.ok) {
                  return res.json();
                } else {
                  return res.json().then(err => {
                    throw new Error(JSON.stringify(err));
                  });
                }
              })
              .then(data => data.order);
            })
            .then(order => {
              console.log('Payment processed successfully');
              localStorage.removeItem('cart');
              setLoading(false);
              onOrderComplete(order);
            })
            .catch(error => {
              console.error('Order creation error:', error);
              alert('Error creating order: ' + error.message);
              setLoading(false);
            });
          }
        }
      });
    } catch (error: any) {
      console.error('Yoco initialization error:', error);
      alert('Failed to initialize payment: ' + error.message);
      setShowingYoco(false);
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-20 flex items-center justify-center p-4" onClick={onClose}>
      <div className={`bg-white rounded-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto ${showingYoco ? 'opacity-0 pointer-events-none' : ''}`} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="bg-blue-600 text-white p-6 rounded-t-xl">
          <div className="flex justify-between items-center">
            <h2 className="text-3xl font-bold">Checkout</h2>
            <button onClick={onClose} className="text-white hover:text-gray-200 text-3xl">×</button>
          </div>
        </div>

        {/* Content - Two Column Layout */}
        <div className="p-6 grid md:grid-cols-2 gap-8">
          {/* Left Column - Form */}
          <div className="space-y-6">
            {/* Customer Details */}
            <div>
              <h3 className="text-xl font-bold mb-4 pb-2 border-b">👤 Your Details</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold mb-2">Full Name *</label>
                  <input
                    type="text"
                    name="customer_name"
                    value={formData.customer_name}
                    onChange={handleInputChange}
                    className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="John Doe"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-2">Phone Number *</label>
                  <input
                    type="tel"
                    name="customer_phone"
                    value={formData.customer_phone}
                    onChange={handleInputChange}
                    className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="074 454 5665"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-2">Email (Optional)</label>
                  <input
                    type="email"
                    name="customer_email"
                    value={formData.customer_email}
                    onChange={handleInputChange}
                    className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="john@example.com"
                  />
                </div>
              </div>
            </div>

            {/* Delivery Details */}
            <div>
              <h3 className="text-xl font-bold mb-4 pb-2 border-b">🚚 Delivery Details</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold mb-2">Delivery Address *</label>
                  <textarea
                    name="delivery_address"
                    value={formData.delivery_address}
                    onChange={handleInputChange}
                    className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows={3}
                    placeholder="123 Main Street, Fish Hoek, Cape Town"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-2">Postal Code</label>
                  <input
                    type="text"
                    value={postalCode}
                    onChange={(e) => setPostalCode(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="7975"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-2">Delivery Zone *</label>
                  <select
                    value={selectedZone?.id || ''}
                    onChange={(e) => {
                      const zone = deliveryZones.find(z => z.id === parseInt(e.target.value));
                      setSelectedZone(zone || null);
                    }}
                    className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  >
                    <option value="">Select delivery zone</option>
                    {deliveryZones.map(zone => (
                      <option key={zone.id} value={zone.id}>
                        {zone.name} - R{parseFloat(zone.delivery_fee).toFixed(2)} (Min: R{parseFloat(zone.minimum_order).toFixed(2)})
                      </option>
                    ))}
                  </select>
                  {selectedZone && (
                    <p className="text-sm text-gray-600 mt-2">
                      ⏱️ Estimated delivery: {selectedZone.estimated_delivery_time}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-2">Delivery Notes (Optional)</label>
                  <textarea
                    name="delivery_notes"
                    value={formData.delivery_notes}
                    onChange={handleInputChange}
                    className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows={2}
                    placeholder="Gate code, special instructions, etc."
                  />
                </div>
              </div>
            </div>

            {/* Payment Method */}
            <div>
              <h3 className="text-xl font-bold mb-4 pb-2 border-b">💳 Payment Method</h3>
              <div className="space-y-3">
                <label className="flex items-center p-4 border-2 border-gray-300 rounded-lg cursor-pointer hover:border-blue-500 transition">
                  <input
                    type="radio"
                    name="payment_method"
                    value="cash"
                    checked={formData.payment_method === 'cash'}
                    onChange={handleInputChange}
                    className="mr-3"
                  />
                  <div>
                    <p className="font-semibold">💵 Cash on Delivery</p>
                    <p className="text-sm text-gray-600">Pay with cash when your order arrives</p>
                  </div>
                </label>

                <label className="flex items-center p-4 border-2 border-gray-300 rounded-lg cursor-pointer hover:border-blue-500 transition">
                  <input
                    type="radio"
                    name="payment_method"
                    value="eft"
                    checked={formData.payment_method === 'eft'}
                    onChange={handleInputChange}
                    className="mr-3"
                  />
                  <div>
                    <p className="font-semibold">🏦 EFT / Bank Transfer</p>
                    <p className="text-sm text-gray-600">Pay via electronic funds transfer</p>
                  </div>
                </label>

                <label className="flex items-center p-4 border-2 border-gray-300 rounded-lg cursor-pointer hover:border-blue-500 transition">
                  <input
                    type="radio"
                    name="payment_method"
                    value="yoco"
                    checked={formData.payment_method === 'yoco'}
                    onChange={handleInputChange}
                    className="mr-3"
                  />
                  <div>
                    <p className="font-semibold">💳 Card Payment (Yoco)</p>
                    <p className="text-sm text-gray-600">Secure online card payment</p>
                  </div>
                </label>
              </div>
            </div>
          </div>

          {/* Right Column - Order Summary */}
          <div>
            <div className="sticky top-6">
              <h3 className="text-xl font-bold mb-4 pb-2 border-b">📦 Order Summary</h3>
              
              {/* Cart Items */}
              <div className="space-y-3 mb-4 max-h-60 overflow-y-auto">
                {cart.map((item) => (
                  <div key={item.product.id} className="flex justify-between py-2 text-sm border-b">
                    <span className="font-medium">{item.quantity}x {item.product.name}</span>
                    <span className="font-semibold">R{(parseFloat(item.product.unit_price) * item.quantity).toFixed(2)}</span>
                  </div>
                ))}
              </div>

              {/* Promo Code */}
              <div className="mb-4 p-4 bg-gray-50 rounded-lg">
                <label className="block text-sm font-semibold mb-2">🎟️ Promo Code</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={promoCode}
                    onChange={(e) => setPromoCode(e.target.value.toUpperCase())}
                    className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="WELCOME10"
                    disabled={discount > 0}
                  />
                  {discount > 0 ? (
                    <button
                      onClick={removePromoCode}
                      className="bg-rose-600 text-white px-4 py-2 rounded-lg hover:bg-rose-700 transition"
                    >
                      Remove
                    </button>
                  ) : (
                    <button
                      onClick={validatePromoCode}
                      className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition"
                    >
                      Apply
                    </button>
                  )}
                </div>
                {promoError && <p className="text-rose-600 text-sm mt-2">{promoError}</p>}
                {promoSuccess && <p className="text-green-600 text-sm mt-2">{promoSuccess}</p>}
              </div>

              {/* Totals */}
              <div className="space-y-2 mb-6 p-4 bg-gray-50 rounded-lg">
                <div className="flex justify-between">
                  <span>Subtotal:</span>
                  <span className="font-semibold">R{getCartTotal().toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Delivery Fee:</span>
                  <span className="font-semibold">R{selectedZone ? parseFloat(selectedZone.delivery_fee).toFixed(2) : '0.00'}</span>
                </div>
                {discount > 0 && (
                  <div className="flex justify-between text-green-600">
                    <span>Discount:</span>
                    <span className="font-semibold">-R{discount.toFixed(2)}</span>
                  </div>
                )}
                <div className="flex justify-between text-2xl font-bold border-t pt-2 mt-2">
                  <span>Total:</span>
                  <span className="text-rose-600">R{calculateTotal().toFixed(2)}</span>
                </div>
              </div>

              {/* Submit Button */}
              <button
                onClick={submitOrder}
                disabled={loading}
                className="w-full bg-blue-600 text-white py-4 rounded-lg font-bold text-lg hover:bg-blue-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed shadow-lg"
              >
                {loading ? 'Processing...' : formData.payment_method === 'yoco' ? '💳 Pay Now' : '✓ Place Order'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
