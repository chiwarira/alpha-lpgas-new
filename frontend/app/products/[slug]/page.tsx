'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { ChevronDown, ChevronUp, Truck } from 'lucide-react';
import Checkout from '../../../components/CheckoutSinglePage';

interface Product {
  id: number;
  name: string;
  description: string;
  sku: string;
  unit_price: string;
  tax_rate: string;
  unit: string;
  is_active: boolean;
  main_image?: string;
  image_2?: string;
  image_3?: string;
  image_4?: string;
  weight?: string;
  category_name?: string;
}

interface FAQ {
  question: string;
  answer: string;
}

interface CartItem {
  product: Product;
  quantity: number;
  includeCylinder?: boolean;
  cylinderProduct?: Product;
}

export default function ProductDetail() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [selectedImage, setSelectedImage] = useState(0);
  const [expandedFAQ, setExpandedFAQ] = useState<number | null>(null);
  const [cart, setCart] = useState<CartItem[]>([]);
  const [showCart, setShowCart] = useState(false);
  const [showCheckout, setShowCheckout] = useState(false);
  const [orderSuccess, setOrderSuccess] = useState<any>(null);
  const viewItemTrackedRef = useState({ current: false })[0];

  useEffect(() => {
    const fetchProduct = async () => {
      try {
        // Fetch all products and find by slug (product name-based)
        const response = await fetch(`${apiUrl}/api/accounting/products/?is_active=true&show_on_website=true`);
        if (response.ok) {
          const data = await response.json();
          const allProducts = data.results || data;
          // Find product by slug (convert product name to slug format)
          const foundProduct = allProducts.find((p: Product) => 
            p.name.toLowerCase().replace(/\s+/g, '-') === slug
          );
          setProduct(foundProduct || null);
          
          // GA4: Track view_item event (only once per product)
          if (foundProduct && typeof window !== 'undefined' && !viewItemTrackedRef.current) {
            viewItemTrackedRef.current = true;
            (window as any).dataLayer = (window as any).dataLayer || [];
            const viewItemEvent = {
              event: 'view_item',
              ecommerce: {
                currency: 'ZAR',
                value: parseFloat(foundProduct.unit_price),
                items: [{
                  item_id: foundProduct.sku,
                  item_name: foundProduct.name,
                  price: parseFloat(foundProduct.unit_price),
                  quantity: 1
                }]
              }
            };
            (window as any).dataLayer.push(viewItemEvent);
          }
        }
      } catch (error) {
        console.error('Error fetching product:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchProduct();
  }, [slug, apiUrl]);

  useEffect(() => {
    const savedCart = localStorage.getItem('cart');
    if (savedCart) {
      setCart(JSON.parse(savedCart));
    }
  }, []);

  useEffect(() => {
    if (cart.length > 0) {
      localStorage.setItem('cart', JSON.stringify(cart));
      window.dispatchEvent(new Event('cartUpdated'));
    }
  }, [cart]);

  const handleAddToCart = () => {
    if (!product) return;
    
    // GA4: Track add_to_cart event
    if (typeof window !== 'undefined') {
      (window as any).dataLayer = (window as any).dataLayer || [];
      const addToCartEvent = {
        event: 'add_to_cart',
        ecommerce: {
          currency: 'ZAR',
          value: parseFloat(product.unit_price) * quantity,
          items: [{
            item_id: product.sku,
            item_name: product.name,
            price: parseFloat(product.unit_price),
            quantity: quantity
          }]
        }
      };
      (window as any).dataLayer.push(addToCartEvent);
    }
    
    setCart(prevCart => {
      const existingItem = prevCart.find(item => item.product.id === product.id);
      if (existingItem) {
        return prevCart.map(item =>
          item.product.id === product.id
            ? { ...item, quantity: item.quantity + quantity }
            : item
        );
      }
      return [...prevCart, { product, quantity }];
    });
    setShowCart(true);
  };

  const removeFromCart = (productId: number) => {
    setCart(prevCart => prevCart.filter(item => item.product.id !== productId));
  };

  const updateQuantity = (productId: number, newQuantity: number) => {
    if (newQuantity < 1) return;
    setCart(prevCart =>
      prevCart.map(item =>
        item.product.id === productId
          ? { ...item, quantity: newQuantity }
          : item
      )
    );
  };

  const getCartTotal = () => {
    return cart.reduce((total, item) => {
      let itemTotal = parseFloat(item.product.unit_price) * item.quantity;
      if (item.includeCylinder && item.cylinderProduct) {
        itemTotal += parseFloat(item.cylinderProduct.unit_price) * item.quantity;
      }
      return total + itemTotal;
    }, 0);
  };

  const getCartCount = () => {
    return cart.reduce((count, item) => count + item.quantity, 0);
  };

  const orderViaWhatsApp = () => {
    if (!product) return;
    
    const phone = '27744545665';
    const message = `Hi! I'd like to order:\n\n${quantity}x ${product.name} - R${(parseFloat(product.unit_price) * quantity).toFixed(2)}`;
    
    // GA4: Track WhatsApp order event
    if (typeof window !== 'undefined') {
      (window as any).dataLayer = (window as any).dataLayer || [];
      const whatsappOrderEvent = {
        event: 'whatsapp_order',
        ecommerce: {
          currency: 'ZAR',
          value: parseFloat(product.unit_price) * quantity,
          items: [{
            item_id: product.sku,
            item_name: product.name,
            price: parseFloat(product.unit_price),
            quantity: quantity
          }]
        }
      };
      (window as any).dataLayer.push(whatsappOrderEvent);
    }
    
    const whatsappUrl = `https://wa.me/${phone}?text=${encodeURIComponent(message)}`;
    window.open(whatsappUrl, '_blank');
  };

  const images = product ? [
    product.main_image,
    product.image_2,
    product.image_3,
    product.image_4
  ].filter(Boolean) : [];

  const faqs: FAQ[] = [
    {
      question: "Is this cylinder exchangeable?",
      answer: "Yes, we offer cylinder exchange services. Simply provide your empty cylinder when we deliver your full one for a hassle-free experience."
    },
    {
      question: "Do I need any special equipment?",
      answer: "You'll need a compatible regulator and connection hose. Our team can advise you on setup if needed, and we can provide the necessary equipment."
    },
    {
      question: "What areas do you deliver to?",
      answer: "We provide fast, efficient gas delivery across Fish Hoek and surrounding areas in Cape Town, including the Southern Peninsula."
    },
    {
      question: "How quickly can I get my delivery?",
      answer: "We offer same-day delivery for orders placed before our cut-off time. Choose your preferred delivery time slot during checkout."
    }
  ];

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">⏳</div>
          <p className="text-xl text-gray-600">Loading product...</p>
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">📦</div>
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Product Not Found</h1>
          <Link href="/" className="text-blue-600 hover:text-blue-700 font-semibold">
            ← Back to Home
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="bg-white text-gray-800 shadow-lg border-b-2 border-rose-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <a href="/" className="cursor-pointer">
                <img src="/alpha-lpgas-logo.svg" alt="Alpha LPGas Logo" className="h-12" />
              </a>
            </div>
            <div className="hidden md:flex space-x-8">
              <a href="/" className="text-gray-700 hover:text-rose-600 font-semibold transition">Home</a>
              <a href="/#products" className="text-gray-700 hover:text-rose-600 font-semibold transition">Products</a>
              <Link href="/contact" className="text-gray-700 hover:text-rose-600 font-semibold transition">Contact Us</Link>
            </div>
            <div className="flex items-center space-x-2 sm:space-x-4">
              <button 
                onClick={() => setShowCart(true)}
                className="relative bg-blue-600 text-white hover:bg-blue-700 px-3 py-2 sm:px-4 rounded-lg font-semibold transition"
              >
                <span className="hidden sm:inline">🛒 Cart</span>
                <span className="sm:hidden text-xl">🛒</span>
                {getCartCount() > 0 && (
                  <span className="absolute -top-2 -right-2 bg-rose-600 text-white text-xs rounded-full h-5 w-5 sm:h-6 sm:w-6 flex items-center justify-center font-bold">
                    {getCartCount()}
                  </span>
                )}
              </button>
              <a href="tel:0744545665" className="bg-rose-600 text-white hover:bg-rose-700 px-3 py-2 sm:px-4 rounded-lg font-semibold transition whitespace-nowrap">
                <span className="hidden sm:inline">📞 074 454 5665</span>
                <span className="sm:hidden text-xl">📞</span>
              </a>
            </div>
          </div>
        </div>
      </nav>

      {/* Breadcrumb */}
      <div className="bg-gray-50 border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <div className="flex items-center space-x-2 text-sm">
            <Link href="/" className="text-blue-600 hover:text-blue-700">Home</Link>
            <span className="text-gray-400">/</span>
            <Link href="/#products" className="text-blue-600 hover:text-blue-700">Products</Link>
            <span className="text-gray-400">/</span>
            <span className="text-gray-600">{product.name}</span>
          </div>
        </div>
      </div>

      {/* Product Detail Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid md:grid-cols-2 gap-12">
          {/* Product Images */}
          <div>
            <div className="bg-gray-100 rounded-lg overflow-hidden mb-4">
              <img 
                src={images[selectedImage] || '/placeholder-product.png'} 
                alt={product.name}
                className="w-full h-96 object-contain"
              />
            </div>
            {images.length > 1 && (
              <div className="grid grid-cols-4 gap-2">
                {images.map((img, idx) => (
                  <button
                    key={idx}
                    onClick={() => setSelectedImage(idx)}
                    className={`border-2 rounded-lg overflow-hidden ${selectedImage === idx ? 'border-blue-600' : 'border-gray-200'}`}
                  >
                    <img src={img} alt={`${product.name} ${idx + 1}`} className="w-full h-20 object-contain" />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Product Info */}
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-4">{product.name}</h1>
            
            <div className="flex items-baseline mb-6">
              <span className="text-4xl font-bold text-blue-600">R{parseFloat(product.unit_price).toFixed(2)}</span>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <div className="flex items-center text-blue-800">
                <Truck className="w-5 h-5 mr-2" />
                <span className="font-semibold">Delivery fee - determined at checkout</span>
              </div>
            </div>

            <div className="prose prose-lg mb-8">
              <p className="text-gray-700">{product.description}</p>
            </div>

            {/* Quantity Selector */}
            <div className="mb-6">
              <label className="block text-sm font-semibold text-gray-700 mb-2">Quantity</label>
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => setQuantity(Math.max(1, quantity - 1))}
                  className="w-10 h-10 rounded-lg border-2 border-gray-300 hover:border-blue-600 flex items-center justify-center font-bold text-xl"
                >
                  -
                </button>
                <span className="text-2xl font-bold w-12 text-center">{quantity}</span>
                <button
                  onClick={() => setQuantity(quantity + 1)}
                  className="w-10 h-10 rounded-lg border-2 border-gray-300 hover:border-blue-600 flex items-center justify-center font-bold text-xl"
                >
                  +
                </button>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="space-y-3">
              <button
                onClick={orderViaWhatsApp}
                className="flex items-center justify-center w-full bg-green-600 hover:bg-green-700 text-white py-3 rounded-lg font-semibold transition shadow-md"
              >
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.890-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>
                </svg>
                Order via WhatsApp
              </button>
              <button
                onClick={handleAddToCart}
                className="block w-full bg-blue-600 hover:bg-blue-700 text-white text-center py-3 rounded-lg font-semibold transition shadow-md"
              >
                🛒 Add to Cart
              </button>
            </div>
          </div>
        </div>

        {/* Features Section */}
        <div className="mt-16 grid md:grid-cols-4 gap-8">
          <div className="text-center">
            <div className="text-5xl mb-3">🚚</div>
            <h3 className="font-bold text-lg mb-2">Same-Day Delivery</h3>
            <p className="text-gray-600 text-sm">Get your gas the same day you order</p>
          </div>
          <div className="text-center">
            <div className="text-5xl mb-3">💳</div>
            <h3 className="font-bold text-lg mb-2">Secure Payment</h3>
            <p className="text-gray-600 text-sm">Safe and secure online payment</p>
          </div>
          <div className="text-center">
            <div className="text-5xl mb-3">💰</div>
            <h3 className="font-bold text-lg mb-2">Best Prices</h3>
            <p className="text-gray-600 text-sm">Competitive pricing guaranteed</p>
          </div>
          <div className="text-center">
            <div className="text-5xl mb-3">😊</div>
            <h3 className="font-bold text-lg mb-2">Friendly Service</h3>
            <p className="text-gray-600 text-sm">Professional and courteous staff</p>
          </div>
        </div>

        {/* Why Choose This Product */}
        <div className="mt-16 bg-gradient-to-r from-blue-600 to-blue-700 rounded-2xl p-12 text-white">
          <h2 className="text-3xl font-bold mb-6">Why Choose {product.name}?</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-xl font-semibold mb-3">Perfect For:</h3>
              <ul className="space-y-2">
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>Gas stoves and ovens</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>Gas heaters</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>Braais and outdoor cooking</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>Everyday household energy needs</span>
                </li>
              </ul>
            </div>
            <div>
              <h3 className="text-xl font-semibold mb-3">Benefits:</h3>
              <ul className="space-y-2">
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>Cost-effective energy solution</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>Reliable and portable</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>Better energy efficiency than electric</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>Environmentally friendly</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* FAQ Section */}
        <div className="mt-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">Frequently Asked Questions</h2>
          <div className="max-w-3xl mx-auto space-y-4">
            {faqs.map((faq, idx) => (
              <div key={idx} className="border border-gray-200 rounded-lg overflow-hidden">
                <button
                  onClick={() => setExpandedFAQ(expandedFAQ === idx ? null : idx)}
                  className="w-full px-6 py-4 flex justify-between items-center bg-white hover:bg-gray-50 transition"
                >
                  <span className="font-semibold text-left text-gray-900">{faq.question}</span>
                  {expandedFAQ === idx ? (
                    <ChevronUp className="w-5 h-5 text-gray-500" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-gray-500" />
                  )}
                </button>
                {expandedFAQ === idx && (
                  <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
                    <p className="text-gray-700">{faq.answer}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* CTA Section */}
        <div className="mt-16 bg-rose-600 rounded-2xl p-12 text-center text-white">
          <h2 className="text-3xl font-bold mb-4">Ready to Order?</h2>
          <p className="text-xl mb-8">Experience fast, dependable delivery from Alpha LPGas today!</p>
          <button
            onClick={handleAddToCart}
            className="bg-white text-rose-600 hover:bg-gray-100 px-12 py-4 rounded-lg font-bold text-lg transition shadow-lg"
          >
            Add to Cart Now
          </button>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-3 gap-8 mb-8">
            {/* Address */}
            <div>
              <h3 className="text-xl font-bold mb-4 text-blue-400">Address</h3>
              <p className="text-gray-300 leading-relaxed">
                Sunnyacres Shopping Centre,<br />
                Sunnydale, Fish Hoek,<br />
                Cape Town
              </p>
            </div>

            {/* Contact */}
            <div>
              <h3 className="text-xl font-bold mb-4 text-blue-400">Contact</h3>
              <div className="space-y-2">
                <a href="tel:0744545665" className="block text-gray-300 hover:text-blue-400 transition">
                  📞 074 454 5665
                </a>
                <a href="mailto:info@alphalpgas.co.za" className="block text-gray-300 hover:text-blue-400 transition">
                  ✉️ info@alphalpgas.co.za
                </a>
              </div>
            </div>

            {/* Trading Hours */}
            <div>
              <h3 className="text-xl font-bold mb-4 text-blue-400">Trading Hours</h3>
              <div className="space-y-1 text-gray-300">
                <p><span className="font-semibold">Mon – Sun:</span> 8am – 7pm</p>
              </div>
            </div>
          </div>

          {/* Bottom Bar */}
          <div className="border-t border-gray-700 pt-6 text-center">
            <p className="italic text-blue-400 text-lg mb-2">Always striving for customer satisfaction!</p>
            <p className="text-gray-400">&copy; {new Date().getFullYear()} Alpha LPGas. All rights reserved.</p>
          </div>
        </div>
      </footer>

      {/* Cart Sidebar */}
      {showCart && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-end" onClick={() => setShowCart(false)}>
          <div className="bg-white w-full max-w-md h-full overflow-y-auto shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900">Shopping Cart</h2>
                <button onClick={() => setShowCart(false)} className="text-gray-500 hover:text-gray-700 text-3xl">
                  ×
                </button>
              </div>

              {cart.length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">🛒</div>
                  <p className="text-gray-600 text-lg">Your cart is empty</p>
                  <button 
                    onClick={() => setShowCart(false)}
                    className="mt-6 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition"
                  >
                    Continue Shopping
                  </button>
                </div>
              ) : (
                <>
                  <div className="space-y-4 mb-6">
                    {cart.map((item) => (
                      <div key={item.product.id} className="bg-gray-50 p-4 rounded-lg">
                        <div className="flex gap-4">
                          <div className="flex-1">
                            <h3 className="font-semibold text-gray-900">{item.product.name}</h3>
                            <p className="text-rose-600 font-bold">R{parseFloat(item.product.unit_price).toFixed(2)}</p>
                            {item.includeCylinder && item.cylinderProduct && (
                              <p className="text-sm text-blue-600 mt-1">
                                + {item.cylinderProduct.name} (R{parseFloat(item.cylinderProduct.unit_price).toFixed(2)})
                              </p>
                            )}
                            <div className="flex items-center gap-2 mt-2">
                            <button
                              onClick={() => updateQuantity(item.product.id, item.quantity - 1)}
                              className="bg-gray-200 hover:bg-gray-300 w-8 h-8 rounded flex items-center justify-center font-bold"
                            >
                              -
                            </button>
                            <span className="w-12 text-center font-semibold">{item.quantity}</span>
                            <button
                              onClick={() => updateQuantity(item.product.id, item.quantity + 1)}
                              className="bg-gray-200 hover:bg-gray-300 w-8 h-8 rounded flex items-center justify-center font-bold"
                            >
                              +
                            </button>
                            </div>
                          </div>
                          <button
                            onClick={() => removeFromCart(item.product.id)}
                            className="text-red-500 hover:text-red-700 font-bold"
                          >
                            ×
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="border-t pt-4 mb-6">
                    <div className="flex justify-between items-center text-xl font-bold">
                      <span>Total:</span>
                      <span className="text-rose-600">R{getCartTotal().toFixed(2)}</span>
                    </div>
                  </div>

                  <button
                    onClick={() => {
                      // GA4: Track begin_checkout event
                      if (typeof window !== 'undefined') {
                        (window as any).dataLayer = (window as any).dataLayer || [];
                        const items = cart.map(item => ({
                          item_id: item.product.sku,
                          item_name: item.product.name,
                          price: parseFloat(item.product.unit_price),
                          quantity: item.quantity
                        }));
                        
                        const beginCheckoutEvent = {
                          event: 'begin_checkout',
                          ecommerce: {
                            currency: 'ZAR',
                            value: getCartTotal(),
                            items: items
                          }
                        };
                        (window as any).dataLayer.push(beginCheckoutEvent);
                      }
                      
                      setShowCart(false);
                      setShowCheckout(true);
                    }}
                    className="w-full bg-rose-600 text-white py-4 rounded-lg font-bold text-lg hover:bg-rose-700 transition"
                  >
                    Proceed to Checkout
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Checkout Modal */}
      {showCheckout && (
        <Checkout
          cart={cart}
          onClose={() => setShowCheckout(false)}
          onOrderComplete={(order) => {
            setShowCheckout(false);
            setCart([]);
            localStorage.removeItem('cart');
            setOrderSuccess(order);
          }}
          getCartTotal={getCartTotal}
        />
      )}

      {/* Order Success Modal */}
      {orderSuccess && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4" onClick={() => setOrderSuccess(null)}>
          <div className="bg-white rounded-xl max-w-md w-full p-8 text-center" onClick={(e) => e.stopPropagation()}>
            <div className="text-6xl mb-4">🎉</div>
            <h2 className="text-3xl font-bold text-green-600 mb-4">Order Placed Successfully!</h2>
            <p className="text-gray-600 mb-6">
              Your order has been received and is being processed.
            </p>
            
            <div className="bg-gray-50 rounded-lg p-4 mb-6">
              <p className="text-sm text-gray-600 mb-2">Order Number</p>
              <p className="text-2xl font-bold text-blue-600">{orderSuccess.order_number}</p>
            </div>

            <div className="space-y-2 text-left mb-6">
              <div className="flex justify-between">
                <span className="text-gray-600">Status:</span>
                <span className="font-semibold capitalize">{orderSuccess.status}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Payment:</span>
                <span className="font-semibold capitalize">{orderSuccess.payment_method}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Total:</span>
                <span className="font-bold text-rose-600">R{parseFloat(orderSuccess.total).toFixed(2)}</span>
              </div>
            </div>

            <p className="text-sm text-gray-600 mb-6">
              We'll contact you shortly to confirm your delivery details.
            </p>

            <div className="space-y-3">
              <a
                href={`/track/${orderSuccess.order_number}`}
                className="block w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg font-semibold transition"
              >
                Track Your Order
              </a>
              <button
                onClick={() => {
                  setOrderSuccess(null);
                  router.push('/');
                }}
                className="w-full bg-gray-200 hover:bg-gray-300 text-gray-700 py-3 rounded-lg font-semibold transition"
              >
                Continue Shopping
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
