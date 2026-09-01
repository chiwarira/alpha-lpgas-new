'use client';

import Link from 'next/link';
import { Phone, Mail, MapPin, Clock } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-slate-900 text-slate-300 py-14">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid md:grid-cols-4 gap-8 mb-10">
          <div className="md:col-span-1">
            <Link href="/" className="inline-block text-white font-bold text-2xl mb-4">
              Alpha LPGas
            </Link>
            <p className="text-slate-400 text-sm leading-relaxed">
              Premium LPG delivery to your door. Reliable, safe and on time.
            </p>
          </div>

          <div>
            <h4 className="text-white font-semibold mb-4">Contact</h4>
            <ul className="space-y-3 text-sm">
              <li className="flex items-start gap-3">
                <Phone className="w-4 h-4 mt-0.5 text-red-600 shrink-0" />
                <a href="tel:0744545665" className="hover:text-white transition">074 454 5665</a>
              </li>
              <li className="flex items-start gap-3">
                <Mail className="w-4 h-4 mt-0.5 text-red-600 shrink-0" />
                <a href="mailto:info@alphalpgas.co.za" className="hover:text-white transition">info@alphalpgas.co.za</a>
              </li>
              <li className="flex items-start gap-3">
                <MapPin className="w-4 h-4 mt-0.5 text-red-600 shrink-0" />
                <span>Sunnyacres Shopping Centre, Sunnydale, Fish Hoek, Cape Town</span>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="text-white font-semibold mb-4">Trading Hours</h4>
            <ul className="space-y-3 text-sm">
              <li className="flex items-start gap-3">
                <Clock className="w-4 h-4 mt-0.5 text-red-600 shrink-0" />
                <span>Mon – Sun: 8am – 7pm</span>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="text-white font-semibold mb-4">Explore</h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="/" className="hover:text-white transition">Home</Link></li>
              <li><a href="/#products" className="hover:text-white transition">Products</a></li>
              <li><Link href="/blog" className="hover:text-white transition">Blog</Link></li>
              <li><Link href="/contact" className="hover:text-white transition">Contact</Link></li>
            </ul>
          </div>
        </div>

        <div className="border-t border-slate-800 pt-6 text-center text-sm text-slate-500">
          <p>&copy; {new Date().getFullYear()} Alpha LPGas. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}
