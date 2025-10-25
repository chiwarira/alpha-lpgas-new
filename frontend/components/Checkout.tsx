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

  const validateStep1 = () => {
    if (!formData.customer_name.trim()) {
      alert('Please enter your name');
      return false;
    }
    if (!formData.customer_phone.trim()) {
      alert('Please enter your phone number');
      return false;
    }
    return true;
  };

  const validateStep2 = () => {
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
    setLoading(true);
    
    const orderData = {
      ...formData,
      delivery_zone: selectedZone?.id || null,
      subtotal: getCartTotal().toFixed(2),
      delivery_fee: selectedZone?.delivery_fee || '0.00',
      discount_amount: discount.toFixed(2),
      total: calculateTotal().toFixed(2),
      items: cart.map(item => ({
        product: item.product.id,
        variant: item.variant?.id || null,
        quantity: item.quantity,
        unit_price: item.product.unit_price
      }))
    };

    try {
      const response = await fetch('http://localhost:8000/api/accounting/orders/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(orderData)
      });

      if (response.ok) {
        const order = await response.json();
        
        // If Yoco payment, process payment
        if (formData.payment_method === 'yoco') {
          processYocoPayment(order);
        } else {
          // Clear cart and show success
          localStorage.removeItem('cart');
          onOrderComplete(order);
        }
      } else {
        const error = await response.json();
        alert('Failed to create order: ' + JSON.stringify(error));
      }
    } catch (error) {
      alert('Error creating order: ' + error);
    } finally {
      setLoading(false);
    }
  };

  const processYocoPayment = (order: any) => {
    const yocoPublicKey = process.env.NEXT_PUBLIC_YOCO_PUBLIC_KEY;
    
    if (!yocoPublicKey) {
      alert('Yoco payment not configured');
      setLoading(false);
      return;
    }

    // @ts-ignore
    const yoco = new window.YocoSDK({
      publicKey: yocoPublicKey
    });

    yoco.showPopup({
      amountInCents: Math.round(parseFloat(order.total) * 100),
      currency: 'ZAR',
      name: 'Alpha LPGas',
      description: `Order #${order.order_number}`,
      callback: function (result: any) {
        if (result.error) {
          const errorMessage = result.error.message || 'Payment failed';
          alert('Payment failed: ' + errorMessage);
          setLoading(false);
        } else {
          // Send payment ID to backend
          fetch(`http://localhost:8000/api/accounting/orders/${order.id}/process_yoco_payment/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ payment_id: result.id })
          })
          .then(response => {
            if (response.ok) {
              return response.json();
            } else {
              throw new Error('Payment verification failed');
            }
          })
          .then(data => {
            localStorage.removeItem('cart');
            setLoading(false);
            onOrderComplete(data.order);
          })
          .catch(error => {
            alert('Error processing payment: ' + error.message);
            setLoading(false);
          });
        }
      }
    });
  };

  const nextStep = () => {
    if (step === 1 && !validateStep1()) return;
    if (step === 2 && !validateStep2()) return;
    setStep(step + 1);
  };

  const prevStep = () => {
    setStep(step - 1);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-30 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="bg-blue-600 text-white p-6 rounded-t-xl">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold">Checkout</h2>
            <button onClick={onClose} className="text-white hover:text-gray-200 text-3xl">×</button>
          </div>
          
          {/* Progress Steps */}
          <div className="flex justify-between mt-6">
            <div className={`flex-1 text-center ${step >= 1 ? 'opacity-100' : 'opacity-50'}`}>
              <div className={`w-8 h-8 rounded-full mx-auto mb-2 flex items-center justify-center ${step >= 1 ? 'bg-white text-blue-600' : 'bg-blue-400'}`}>
                1
              </div>
              <p className="text-sm">Details</p>
            </div>
            <div className={`flex-1 text-center ${step >= 2 ? 'opacity-100' : 'opacity-50'}`}>
              <div className={`w-8 h-8 rounded-full mx-auto mb-2 flex items-center justify-center ${step >= 2 ? 'bg-white text-blue-600' : 'bg-blue-400'}`}>
                2
              </div>
              <p className="text-sm">Delivery</p>
            </div>
            <div className={`flex-1 text-center ${step >= 3 ? 'opacity-100' : 'opacity-50'}`}>
              <div className={`w-8 h-8 rounded-full mx-auto mb-2 flex items-center justify-center ${step >= 3 ? 'bg-white text-blue-600' : 'bg-blue-400'}`}>
                3
              </div>
              <p className="text-sm">Payment</p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Step 1: Customer Details */}
          {step === 1 && (
            <div className="space-y-4">
              <h3 className="text-xl font-bold mb-4">Your Details</h3>
              
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
          )}

          {/* Step 2: Delivery Details */}
          {step === 2 && (
            <div className="space-y-4">
              <h3 className="text-xl font-bold mb-4">Delivery Details</h3>
              
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

              {/* Promo Code */}
              <div className="border-t pt-4">
                <label className="block text-sm font-semibold mb-2">Promo Code</label>
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
            </div>
          )}

          {/* Step 3: Payment */}
          {step === 3 && (
            <div className="space-y-4">
              <h3 className="text-xl font-bold mb-4">Payment Method</h3>
              
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

              {/* Order Summary */}
              <div className="border-t pt-4 mt-6">
                <h4 className="font-bold text-lg mb-3">Order Summary</h4>
                
                {cart.map((item) => (
                  <div key={item.product.id} className="flex justify-between py-2 text-sm">
                    <span>{item.quantity}x {item.product.name}</span>
                    <span>R{(parseFloat(item.product.unit_price) * item.quantity).toFixed(2)}</span>
                  </div>
                ))}
                
                <div className="border-t mt-3 pt-3 space-y-2">
                  <div className="flex justify-between">
                    <span>Subtotal:</span>
                    <span>R{getCartTotal().toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Delivery Fee:</span>
                    <span>R{selectedZone ? parseFloat(selectedZone.delivery_fee).toFixed(2) : '0.00'}</span>
                  </div>
                  {discount > 0 && (
                    <div className="flex justify-between text-green-600">
                      <span>Discount:</span>
                      <span>-R{discount.toFixed(2)}</span>
                    </div>
                  )}
                  <div className="flex justify-between text-xl font-bold border-t pt-2">
                    <span>Total:</span>
                    <span className="text-rose-600">R{calculateTotal().toFixed(2)}</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex justify-between mt-6 pt-6 border-t">
            {step > 1 && (
              <button
                onClick={prevStep}
                className="bg-gray-200 text-gray-700 px-6 py-3 rounded-lg font-semibold hover:bg-gray-300 transition"
              >
                ← Back
              </button>
            )}
            
            {step < 3 ? (
              <button
                onClick={nextStep}
                className="ml-auto bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
              >
                Continue →
              </button>
            ) : (
              <button
                onClick={submitOrder}
                disabled={loading}
                className="ml-auto bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {loading ? 'Processing...' : formData.payment_method === 'yoco' ? '💳 Pay Now' : '✓ Place Order'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
