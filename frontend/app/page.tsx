'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Checkout from '../components/CheckoutSinglePage';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import WhatsAppButton from '@/components/WhatsAppButton';
import { Flame, Check, Package, Truck, Shield, Award, Phone, MapPin, Home as HomeIcon, ShoppingCart, PartyPopper, Loader2 } from 'lucide-react';

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

interface HeroBanner {
  id: number;
  title: string;
  subtitle: string;
  background_image?: string;
  overlay_color: string;
  overlay_opacity: number;
  overlay_rgba: string;
  cta_text: string;
  cta_link: string;
  secondary_cta_text?: string;
  secondary_cta_link?: string;
  is_active: boolean;
}

interface CartItem {
  product: Product;
  quantity: number;
  includeCylinder?: boolean;
  cylinderProduct?: Product;
}

interface Testimonial {
  id: number;
  customer_name: string;
  location: string;
  company_name?: string;
  review: string;
  rating: number;
  avatar_color: string;
  initials: string;
}

export default function Home() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const [selectedProduct, setSelectedProduct] = useState<string | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [products, setProducts] = useState<Product[]>([]);
  const [cylinderProducts, setCylinderProducts] = useState<Product[]>([]);
  const [banner, setBanner] = useState<HeroBanner | null>(null);
  const [testimonials, setTestimonials] = useState<Testimonial[]>([]);
  const [displayedTestimonials, setDisplayedTestimonials] = useState<Testimonial[]>([]);
  const [loading, setLoading] = useState(true);
  const [cart, setCart] = useState<CartItem[]>([]);
  const [showCart, setShowCart] = useState(false);
  const [showCheckout, setShowCheckout] = useState(false);
  const [orderSuccess, setOrderSuccess] = useState<any>(null);
  const [cylinderSelections, setCylinderSelections] = useState<{[key: number]: boolean}>({});

  // Load cart from localStorage on mount
  useEffect(() => {
    const savedCart = localStorage.getItem('cart');
    if (savedCart) {
      try {
        setCart(JSON.parse(savedCart));
      } catch (error) {
        console.error('Error loading cart:', error);
      }
    }
  }, []);

  // Save cart to localStorage whenever it changes
  useEffect(() => {
    if (cart.length > 0) {
      localStorage.setItem('cart', JSON.stringify(cart));
    } else {
      localStorage.removeItem('cart');
    }
  }, [cart]);

  // Fetch products and banner from backend API
  useEffect(() => {
    const fetchData = async () => {
      try {
        console.log('API URL:', apiUrl);
        // Fetch products
        const productsUrl = `${apiUrl}/api/accounting/products/?is_active=true&show_on_website=true`;
        console.log('Fetching products from:', productsUrl);
        const productsResponse = await fetch(productsUrl);
        console.log('Products response status:', productsResponse.status);
        if (productsResponse.ok) {
          const productsData = await productsResponse.json();
          console.log('Fetched products:', productsData);
          const allProducts = productsData.results || productsData;
          
          // Separate gas products and cylinder products
          const gasProducts = allProducts.filter((p: Product) => 
            !p.name.toLowerCase().includes('cylinder') && !p.category_name?.toLowerCase().includes('cylinder')
          );
          const cylinders = allProducts.filter((p: Product) => 
            p.name.toLowerCase().includes('cylinder') || p.category_name?.toLowerCase().includes('cylinder')
          );
          
          setProducts(gasProducts);
          setCylinderProducts(cylinders);
        } else {
          console.error('Failed to fetch products:', productsResponse.status, productsResponse.statusText);
        }

        // Fetch hero banner
        const bannerResponse = await fetch(`${apiUrl}/api/accounting/hero-banners/?is_active=true`);
        if (bannerResponse.ok) {
          const bannerData = await bannerResponse.json();
          console.log('Fetched banner:', bannerData);
          // Get the first active banner
          const banners = bannerData.results || bannerData;
          if (banners.length > 0) {
            setBanner(banners[0]);
          }
        }

        // Fetch testimonials
        const testimonialsResponse = await fetch(`${apiUrl}/api/accounting/testimonials/`);
        if (testimonialsResponse.ok) {
          const testimonialsData = await testimonialsResponse.json();
          console.log('Fetched testimonials:', testimonialsData);
          const allTestimonials = testimonialsData.results || testimonialsData;
          setTestimonials(allTestimonials);
          
          // Randomly select 3 testimonials to display (or all if less than 3)
          const shuffled = [...allTestimonials].sort(() => 0.5 - Math.random());
          setDisplayedTestimonials(shuffled.slice(0, 3));
        }
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Product icon fallback is handled inline

  // Helper function to find matching cylinder for a gas product
  const findMatchingCylinder = (gasProduct: Product): Product | undefined => {
    const name = gasProduct.name.toLowerCase();
    let size = '';
    
    if (name.includes('9kg') || name.includes('9 kg')) size = '9kg';
    else if (name.includes('14kg') || name.includes('14 kg')) size = '14kg';
    else if (name.includes('19kg') || name.includes('19 kg')) size = '19kg';
    else if (name.includes('48kg') || name.includes('48 kg')) size = '48kg';
    
    if (!size) return undefined;
    
    return cylinderProducts.find(cyl => 
      cyl.name.toLowerCase().includes(size)
    );
  };

  // Cart functions
  const addToCart = (product: Product) => {
    const includeCylinder = cylinderSelections[product.id] || false;
    const cylinderProduct = includeCylinder ? findMatchingCylinder(product) : undefined;
    
    // GA4: Track add_to_cart event
    if (typeof window !== 'undefined') {
      (window as any).dataLayer = (window as any).dataLayer || [];
      const items = [{
        item_id: product.sku,
        item_name: product.name,
        price: parseFloat(product.unit_price),
        quantity: 1
      }];
      
      let totalValue = parseFloat(product.unit_price);
      
      if (includeCylinder && cylinderProduct) {
        items.push({
          item_id: cylinderProduct.sku,
          item_name: cylinderProduct.name,
          price: parseFloat(cylinderProduct.unit_price),
          quantity: 1
        });
        totalValue += parseFloat(cylinderProduct.unit_price);
      }
      
      const addToCartEvent = {
        event: 'add_to_cart',
        ecommerce: {
          currency: 'ZAR',
          value: totalValue,
          items: items
        }
      };
      (window as any).dataLayer.push(addToCartEvent);
    }
    
    setCart(prevCart => {
      const existingItem = prevCart.find(item => item.product.id === product.id);
      if (existingItem) {
        return prevCart.map(item =>
          item.product.id === product.id
            ? { ...item, quantity: item.quantity + 1, includeCylinder, cylinderProduct }
            : item
        );
      }
      return [...prevCart, { product, quantity: 1, includeCylinder, cylinderProduct }];
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

  const orderViaWhatsApp = (product?: Product) => {
    const phone = process.env.NEXT_PUBLIC_WHATSAPP_NUMBER || '27744545665'; // WhatsApp number
    let message = '';
    
    if (product) {
      // Single product order
      const includeCylinder = cylinderSelections[product.id] || false;
      const cylinderProduct = includeCylinder ? findMatchingCylinder(product) : undefined;
      
      message = `Hi! I'd like to order:\n\n${product.name} - R${parseFloat(product.unit_price).toFixed(2)}`;
      
      if (includeCylinder && cylinderProduct) {
        message += `\n+ ${cylinderProduct.name} - R${parseFloat(cylinderProduct.unit_price).toFixed(2)}`;
        message += `\n\nTotal: R${(parseFloat(product.unit_price) + parseFloat(cylinderProduct.unit_price)).toFixed(2)}`;
      }
      
      // GA4: Track WhatsApp order event
      if (typeof window !== 'undefined') {
        (window as any).dataLayer = (window as any).dataLayer || [];
        const items = [{
          item_id: product.sku,
          item_name: product.name,
          price: parseFloat(product.unit_price),
          quantity: 1
        }];
        
        let totalValue = parseFloat(product.unit_price);
        
        if (includeCylinder && cylinderProduct) {
          items.push({
            item_id: cylinderProduct.sku,
            item_name: cylinderProduct.name,
            price: parseFloat(cylinderProduct.unit_price),
            quantity: 1
          });
          totalValue += parseFloat(cylinderProduct.unit_price);
        }
        
        const whatsappOrderEvent = {
          event: 'whatsapp_order',
          ecommerce: {
            currency: 'ZAR',
            value: totalValue,
            items: items
          }
        };
        (window as any).dataLayer.push(whatsappOrderEvent);
      }
    } else {
      // Cart order
      message = `Hi! I'd like to order:\n\n`;
      cart.forEach(item => {
        message += `${item.quantity}x ${item.product.name} - R${(parseFloat(item.product.unit_price) * item.quantity).toFixed(2)}\n`;
        if (item.includeCylinder && item.cylinderProduct) {
          message += `  + ${item.quantity}x ${item.cylinderProduct.name} - R${(parseFloat(item.cylinderProduct.unit_price) * item.quantity).toFixed(2)}\n`;
        }
      });
      message += `\nTotal: R${getCartTotal().toFixed(2)}`;
      
      // GA4: Track WhatsApp order event for cart
      if (typeof window !== 'undefined') {
        (window as any).dataLayer = (window as any).dataLayer || [];
        const items = cart.map(item => {
          const cartItems = [{
            item_id: item.product.sku,
            item_name: item.product.name,
            price: parseFloat(item.product.unit_price),
            quantity: item.quantity
          }];
          
          if (item.includeCylinder && item.cylinderProduct) {
            cartItems.push({
              item_id: item.cylinderProduct.sku,
              item_name: item.cylinderProduct.name,
              price: parseFloat(item.cylinderProduct.unit_price),
              quantity: item.quantity
            });
          }
          
          return cartItems;
        }).flat();
        
        const whatsappOrderEvent = {
          event: 'whatsapp_order',
          ecommerce: {
            currency: 'ZAR',
            value: getCartTotal(),
            items: items
          }
        };
        (window as any).dataLayer.push(whatsappOrderEvent);
      }
    }
    
    const whatsappUrl = `https://wa.me/${phone}?text=${encodeURIComponent(message)}`;
    window.open(whatsappUrl, '_blank');
  };

  return (
    <div className="min-h-screen bg-white">
      <Header cartCount={getCartCount()} onCartClick={() => setShowCart(true)} />

      {/* Hero Section */}
      <section
        id="home"
        className="relative bg-slate-900 text-white py-24 lg:py-32 bg-cover bg-center"
        style={{
          backgroundImage: `linear-gradient(${banner?.overlay_rgba || 'rgba(37, 99, 235, 0.3)'}, ${banner?.overlay_rgba || 'rgba(37, 99, 235, 0.3)'}), url(${banner?.background_image ? (banner.background_image.startsWith('http') ? banner.background_image : `${apiUrl}/media/${banner.background_image}`) : '/images/hero-bg.jpg'})`
        }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div>
              <div className="inline-flex items-center gap-2 bg-red-600/20 text-red-300 px-4 py-2 rounded-full text-sm font-medium mb-6">
                <Flame className="w-4 h-4" />
                Premium LPG Delivery
              </div>
              <h1 className="text-4xl md:text-6xl font-bold mb-6 leading-tight">
                {banner?.title || 'Door to Door LPG Gas Delivery'}
              </h1>
              <p className="text-lg md:text-xl mb-8 text-slate-200 max-w-xl">
                {banner?.subtitle || 'Fast, reliable gas delivery to your doorstep in Fish Hoek and surrounding areas. Order online and get same-day delivery!'}
              </p>
              <div className="flex flex-col sm:flex-row flex-wrap gap-4">
                <a href="#products" className="inline-flex items-center justify-center bg-red-600 hover:bg-red-700 text-white px-8 py-4 rounded-full font-bold text-lg transition shadow-lg">
                  Order Now
                </a>
                <Link href="/contact" className="inline-flex items-center justify-center bg-white text-slate-900 hover:bg-slate-100 px-8 py-4 rounded-full font-bold text-lg transition shadow-lg">
                  Contact Us
                </Link>
                <WhatsAppButton label="Order on WhatsApp" />
              </div>
            </div>
            <div className="hidden lg:block">
              <div className="bg-white/10 backdrop-blur-sm border border-white/10 rounded-3xl p-8">
                <div className="flex items-center gap-3 mb-6">
                  <div className="p-3 bg-red-600 rounded-xl">
                    <Flame className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold">Why Choose Us?</h3>
                </div>
                <ul className="space-y-4">
                  {['Same-day delivery available', 'Secure online payment', 'Competitive prices', 'Friendly local service'].map((item) => (
                    <li key={item} className="flex items-center">
                      <div className="p-1 bg-green-500 rounded-full mr-3">
                        <Check className="w-3 h-3 text-white" />
                      </div>
                      <span className="text-slate-100">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Coverage / Service / Ordering */}
      <section className="bg-white border-b border-slate-200 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-3 gap-8">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-slate-100 rounded-xl text-red-600">
                <MapPin className="w-8 h-8" />
              </div>
              <div>
                <p className="text-sm text-slate-500 uppercase tracking-wide font-semibold">Coverage</p>
                <p className="text-lg font-bold text-slate-900">Fish Hoek & Surrounds</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="p-3 bg-slate-100 rounded-xl text-red-600">
                <HomeIcon className="w-8 h-8" />
              </div>
              <div>
                <p className="text-sm text-slate-500 uppercase tracking-wide font-semibold">Service</p>
                <p className="text-lg font-bold text-slate-900">Homes & Business</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="p-3 bg-slate-100 rounded-xl text-red-600">
                <Phone className="w-8 h-8" />
              </div>
              <div>
                <p className="text-sm text-slate-500 uppercase tracking-wide font-semibold">Ordering</p>
                <p className="text-lg font-bold text-slate-900">Web + Phone</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Products Section */}
      <section id="products" className="py-20 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-slate-900 mb-4">Our Products</h2>
            <p className="text-xl text-slate-600">Choose the perfect size for your needs</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {loading ? (
              <div className="col-span-3 text-center py-12">
                <Loader2 className="w-12 h-12 text-red-600 mx-auto mb-4 animate-spin" />
                <p className="text-slate-600">Loading products...</p>
              </div>
            ) : products.length === 0 ? (
              <div className="col-span-3 text-center py-12">
                <Package className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                <p className="text-slate-600">No products available at the moment.</p>
              </div>
            ) : (
              products.map((product) => {
                const productSlug = product.name.toLowerCase().replace(/\s+/g, '-');
                return (
                <div key={product.id} className="bg-white rounded-2xl shadow-sm border border-slate-200 hover:shadow-xl transition-all duration-300 overflow-hidden">
                  <Link href={`/products/${productSlug}`}>
                    <div className="bg-slate-900 p-8 text-center cursor-pointer">
                      {product.main_image ? (
                        <img 
                          src={product.main_image.startsWith('http') ? product.main_image : `${apiUrl}/media/${product.main_image}`} 
                          alt={product.name}
                          className="w-full h-48 object-contain mb-4"
                        />
                      ) : (
                        <Package className="w-20 h-20 text-white mx-auto mb-4" />
                      )}
                      <h3 className="text-2xl font-bold text-white">{product.name}</h3>
                    </div>
                  </Link>
                  <div className="p-6">
                    {/* Cylinder Checkbox */}
                    {findMatchingCylinder(product) && (
                      <div className="mb-4 bg-slate-50 p-3 rounded-lg border border-slate-200">
                        <label className="flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={cylinderSelections[product.id] || false}
                            onChange={(e) => setCylinderSelections(prev => ({
                              ...prev,
                              [product.id]: e.target.checked
                            }))}
                            className="w-5 h-5 text-red-600 rounded focus:ring-2 focus:ring-orange-500 mr-3"
                          />
                          <span className="text-sm font-medium text-slate-700">
                            Add {findMatchingCylinder(product)?.name} (+R{parseFloat(findMatchingCylinder(product)?.unit_price || '0').toFixed(2)})
                          </span>
                        </label>
                      </div>
                    )}
                    
                    <div className="text-3xl font-bold text-red-600 mb-6">
                      <span className="text-lg font-normal text-slate-500">from </span>R{parseFloat(product.unit_price).toFixed(2)}
                    </div>
                    <div className="space-y-3">
                      <button
                        onClick={() => orderViaWhatsApp(product)}
                        className="flex items-center justify-center w-full bg-green-600 hover:bg-green-700 text-white py-3 rounded-lg font-semibold transition shadow-md"
                      >
                        <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.890-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>
                        </svg>
                        Order via WhatsApp
                      </button>
                      <button
                        onClick={() => addToCart(product)}
                        className="flex items-center justify-center w-full bg-red-600 hover:bg-red-700 text-white text-center py-3 rounded-lg font-semibold transition shadow-md"
                      >
                        <ShoppingCart className="w-4 h-4 mr-2" /> Add to Cart
                      </button>
                    </div>
                  </div>
                </div>
                );
              })
            )}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="text-center bg-white rounded-2xl p-8 shadow-sm border border-slate-100">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 text-red-600 rounded-2xl mb-4">
                <Truck className="w-8 h-8" />
              </div>
              <h3 className="text-xl font-bold mb-2 text-slate-900">Fast Delivery</h3>
              <p className="text-slate-600">Same-day delivery available</p>
            </div>
            <div className="text-center bg-white rounded-2xl p-8 shadow-sm border border-slate-100">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 text-red-600 rounded-2xl mb-4">
                <Shield className="w-8 h-8" />
              </div>
              <h3 className="text-xl font-bold mb-2 text-slate-900">Secure Payment</h3>
              <p className="text-slate-600">Pay online with YOCO</p>
            </div>
            <div className="text-center bg-white rounded-2xl p-8 shadow-sm border border-slate-100">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 text-red-600 rounded-2xl mb-4">
                <Award className="w-8 h-8" />
              </div>
              <h3 className="text-xl font-bold mb-2 text-slate-900">Quality Service</h3>
              <p className="text-slate-600">Trusted by hundreds</p>
            </div>
            <div className="text-center bg-white rounded-2xl p-8 shadow-sm border border-slate-100">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 text-red-600 rounded-2xl mb-4">
                <Phone className="w-8 h-8" />
              </div>
              <h3 className="text-xl font-bold mb-2 text-slate-900">Easy Ordering</h3>
              <p className="text-slate-600">Order online or by phone</p>
            </div>
          </div>
        </div>
      </section>

      {/* Client Testimonials Section - Content managed from Django backend */}
      <section id="testimonials" className="py-20 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-slate-900 mb-4">What Our Clients Say</h2>
            <p className="text-xl text-slate-600">Trusted by families and businesses across Fish Hoek</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {displayedTestimonials.length > 0 ? (
              displayedTestimonials.map((testimonial) => {
                const avatarColors: {[key: string]: string} = {
                  blue: 'bg-blue-100 text-red-600',
                  rose: 'bg-rose-100 text-red-600',
                  green: 'bg-green-100 text-green-600',
                  purple: 'bg-purple-100 text-purple-600',
                  yellow: 'bg-yellow-100 text-yellow-600',
                  red: 'bg-red-100 text-red-600',
                };
                const colorClass = avatarColors[testimonial.avatar_color] || 'bg-blue-100 text-red-600';

                return (
                  <div key={testimonial.id} className="bg-white rounded-2xl shadow-sm border border-slate-100 p-8 hover:shadow-md transition">
                    <div className="flex items-center mb-4">
                      <div className="flex text-yellow-400">
                        {[...Array(testimonial.rating)].map((_, i) => (
                          <svg key={i} className="w-5 h-5 fill-current" viewBox="0 0 20 20">
                            <path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z" />
                          </svg>
                        ))}
                      </div>
                    </div>
                    <p className="text-slate-600 mb-4 italic">
                      "{testimonial.review}"
                    </p>
                    <div className="flex items-center">
                      <div className={`w-12 h-12 ${colorClass} rounded-full flex items-center justify-center font-bold text-lg`}>
                        {testimonial.initials}
                      </div>
                      <div className="ml-4">
                        <p className="font-semibold text-slate-900">{testimonial.customer_name}</p>
                        <p className="text-sm text-slate-500">{testimonial.location}</p>
                        {testimonial.company_name && (
                          <p className="text-xs text-slate-400">{testimonial.company_name}</p>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="col-span-3 text-center text-slate-500 py-12">
                <p>No testimonials available yet. Check back soon!</p>
              </div>
            )}
          </div>

          <div className="text-center mt-12">
            <Link href="/contact" className="inline-block bg-red-600 text-white hover:bg-red-700 px-8 py-4 rounded-full font-bold text-lg transition shadow-lg">
              Share Your Experience
            </Link>
          </div>
        </div>
      </section>

      <Footer />

      {/* Floating WhatsApp CTA */}
      <div className="fixed bottom-6 right-6 z-50">
        <WhatsAppButton label="Order on WhatsApp" className="shadow-2xl" />
      </div>

      {/* Cart Sidebar */}
      {showCart && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-end" onClick={() => setShowCart(false)}>
          <div className="bg-white w-full max-w-md h-full overflow-y-auto shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-slate-900">Shopping Cart</h2>
                <button onClick={() => setShowCart(false)} className="text-slate-500 hover:text-slate-700 text-3xl">
                  ×
                </button>
              </div>

              {cart.length === 0 ? (
                <div className="text-center py-12">
                  <ShoppingCart className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                  <p className="text-slate-600 text-lg">Your cart is empty</p>
                  <button 
                    onClick={() => setShowCart(false)}
                    className="mt-6 bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 transition"
                  >
                    Continue Shopping
                  </button>
                </div>
              ) : (
                <>
                  <div className="space-y-4 mb-6">
                    {cart.map((item) => (
                      <div key={item.product.id} className="bg-slate-50 p-4 rounded-lg">
                        <div className="flex gap-4">
                          <div className="flex-1">
                            <h3 className="font-semibold text-slate-900">{item.product.name}</h3>
                            <p className="text-red-600 font-bold">R{parseFloat(item.product.unit_price).toFixed(2)}</p>
                            {item.includeCylinder && item.cylinderProduct && (
                              <p className="text-sm text-red-600 mt-1">
                                + {item.cylinderProduct.name} (R{parseFloat(item.cylinderProduct.unit_price).toFixed(2)})
                              </p>
                            )}
                            <div className="flex items-center gap-2 mt-2">
                            <button
                              onClick={() => updateQuantity(item.product.id, item.quantity - 1)}
                              className="bg-slate-200 hover:bg-slate-300 w-8 h-8 rounded flex items-center justify-center font-bold"
                            >
                              -
                            </button>
                            <span className="w-12 text-center font-semibold">{item.quantity}</span>
                            <button
                              onClick={() => updateQuantity(item.product.id, item.quantity + 1)}
                              className="bg-slate-200 hover:bg-slate-300 w-8 h-8 rounded flex items-center justify-center font-bold"
                            >
                              +
                            </button>
                            </div>
                          </div>
                          <div className="flex flex-col justify-between items-end">
                            <button
                              onClick={() => removeFromCart(item.product.id)}
                              className="text-red-600 hover:text-red-700 font-semibold"
                            >
                              Remove
                            </button>
                            <p className="font-bold text-slate-900">
                              R{(parseFloat(item.product.unit_price) * item.quantity + (item.includeCylinder && item.cylinderProduct ? parseFloat(item.cylinderProduct.unit_price) * item.quantity : 0)).toFixed(2)}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="border-t pt-4 mb-6">
                    <div className="flex justify-between items-center text-xl font-bold mb-6">
                      <span>Total:</span>
                      <span className="text-red-600">R{getCartTotal().toFixed(2)}</span>
                    </div>
                    
                    <div className="space-y-3">
                      <button
                        onClick={() => {
                          // GA4: Track begin_checkout event
                          if (typeof window !== 'undefined') {
                            (window as any).dataLayer = (window as any).dataLayer || [];
                            const items = cart.map(item => {
                              const cartItems = [{
                                item_id: item.product.sku,
                                item_name: item.product.name,
                                price: parseFloat(item.product.unit_price),
                                quantity: item.quantity
                              }];
                              
                              if (item.includeCylinder && item.cylinderProduct) {
                                cartItems.push({
                                  item_id: item.cylinderProduct.sku,
                                  item_name: item.cylinderProduct.name,
                                  price: parseFloat(item.cylinderProduct.unit_price),
                                  quantity: item.quantity
                                });
                              }
                              
                              return cartItems;
                            }).flat();
                            
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
                        className="flex items-center justify-center w-full bg-red-600 hover:bg-red-700 text-white py-4 rounded-lg font-bold text-lg transition shadow-lg"
                      >
                        <ShoppingCart className="w-5 h-5 mr-2" /> Proceed to Checkout
                      </button>
                      
                      <button
                        onClick={() => orderViaWhatsApp()}
                        className="w-full bg-green-600 hover:bg-green-700 text-white py-4 rounded-lg font-bold text-lg transition shadow-lg flex items-center justify-center"
                      >
                        <svg className="w-6 h-6 mr-2" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.890-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>
                        </svg>
                        Quick Order via WhatsApp
                      </button>
                    </div>
                  </div>
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
            setOrderSuccess(order);
          }}
          getCartTotal={getCartTotal}
        />
      )}

      {/* Order Success Modal */}
      {orderSuccess && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4" onClick={() => setOrderSuccess(null)}>
          <div className="bg-white rounded-2xl max-w-md w-full p-8 text-center" onClick={(e) => e.stopPropagation()}>
            <PartyPopper className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <h2 className="text-3xl font-bold text-green-600 mb-4">Order Placed Successfully!</h2>
            <p className="text-slate-600 mb-6">
              Your order has been received and is being processed.
            </p>
            
            <div className="bg-slate-50 rounded-lg p-4 mb-6">
              <p className="text-sm text-slate-600 mb-2">Order Number</p>
              <p className="text-2xl font-bold text-red-600">{orderSuccess.order_number}</p>
            </div>

            <div className="space-y-2 text-left mb-6">
              <div className="flex justify-between">
                <span className="text-slate-600">Status:</span>
                <span className="font-semibold capitalize">{orderSuccess.status}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Payment:</span>
                <span className="font-semibold capitalize">{orderSuccess.payment_method}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Total:</span>
                <span className="font-bold text-red-600">R{parseFloat(orderSuccess.total).toFixed(2)}</span>
              </div>
            </div>

            <p className="text-sm text-slate-600 mb-6">
              We'll contact you shortly to confirm your delivery details.
            </p>

            <div className="space-y-3">
              <a
                href={`/track/${orderSuccess.order_number}`}
                className="block w-full bg-red-600 hover:bg-red-700 text-white py-3 rounded-lg font-semibold transition"
              >
                Track Your Order
              </a>
              <button
                onClick={() => setOrderSuccess(null)}
                className="w-full bg-slate-200 hover:bg-slate-300 text-slate-700 py-3 rounded-lg font-semibold transition"
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
