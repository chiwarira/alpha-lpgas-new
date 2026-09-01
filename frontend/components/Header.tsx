'use client';

import Link from 'next/link';
import { useState } from 'react';
import { Phone, Menu, X, ShoppingCart, Clock3 } from 'lucide-react';

export default function Header({
  cartCount,
  onCartClick,
}: {
  cartCount?: number;
  onCartClick?: () => void;
}) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { href: '/', label: 'Home' },
    { href: '/#products', label: 'Products' },
    { href: '/blog', label: 'Blog' },
    { href: '/contact', label: 'Contact Us' },
  ];

  return (
    <>
      <div className="bg-[#101d35] text-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-2 text-xs sm:px-6 lg:px-8">
          <p className="flex items-center gap-2 text-slate-300">
            <Clock3 className="h-3.5 w-3.5 text-red-500" /> Open daily, 8am–7pm
          </p>
          <p className="hidden text-slate-300 sm:block">Fast, reliable LPG delivery across the South Peninsula</p>
        </div>
      </div>
      <nav className="bg-white border-b-2 border-red-600 text-slate-900 sticky top-0 z-50 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">
          <Link href="/" className="flex items-center">
            <img
              src="/alpha-lpgas-logo.svg"
              alt="Alpha LPGas"
              className="h-10 w-auto"
            />
          </Link>

          <div className="hidden md:flex items-center gap-8">
            {navLinks.map((link) =>
              link.href.includes('#') ? (
                <a
                  key={link.href}
                    href={link.href}
                  className="text-sm font-medium text-slate-600 hover:text-red-600 transition"
                >
                  {link.label}
                </a>
              ) : (
                <Link
                  key={link.href}
                  href={link.href}
                  className="text-sm font-medium text-slate-600 hover:text-red-600 transition"
                >
                  {link.label}
                </Link>
              )
            )}
          </div>

          <div className="hidden md:flex items-center gap-4">
            {onCartClick && (
              <button
                onClick={onCartClick}
                className="relative flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-red-600 transition"
              >
                <ShoppingCart className="w-5 h-5" />
                Cart
                {typeof cartCount === 'number' && cartCount > 0 ? (
                  <span className="absolute -top-2 -right-2 bg-red-600 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                    {cartCount}
                  </span>
                ) : (
                  <span className="ml-1 text-slate-400">0</span>
                )}
              </button>
            )}
            <a
              href="tel:0744545665"
              className="inline-flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white px-5 py-2.5 rounded-full text-sm font-semibold transition"
            >
              <Phone className="w-4 h-4" />
              <span className="hidden sm:inline">074 454 5665</span>
            </a>
          </div>

          <div className="md:hidden flex items-center gap-3">
            {onCartClick && (
              <button
                onClick={onCartClick}
                className="relative text-slate-600 hover:text-red-600"
              >
                <ShoppingCart className="w-6 h-6" />
                {typeof cartCount === 'number' && cartCount > 0 && (
                  <span className="absolute -top-1 -right-1 bg-red-600 text-white text-xs rounded-full h-4 w-4 flex items-center justify-center">
                    {cartCount}
                  </span>
                )}
              </button>
            )}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="text-slate-700 hover:text-red-600 focus:outline-none"
            >
              {mobileMenuOpen ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>

        {mobileMenuOpen && (
          <div className="md:hidden pb-4 border-t border-slate-100">
            <div className="flex flex-col gap-3 pt-4">
              {navLinks.map((link) =>
                link.href.includes('#') ? (
                  <a
                    key={link.href}
                    href={link.href}
                    className="text-slate-600 hover:text-red-600 font-medium py-2"
                  >
                    {link.label}
                  </a>
                ) : (
                  <Link
                    key={link.href}
                    href={link.href}
                    className="text-slate-600 hover:text-red-600 font-medium py-2"
                  >
                    {link.label}
                  </Link>
                )
              )}
              <a
                href="tel:0744545665"
                className="inline-flex items-center justify-center gap-2 bg-red-600 hover:bg-red-700 text-white px-5 py-2.5 rounded-full font-semibold"
              >
                <Phone className="w-4 h-4" />
                074 454 5665
              </a>
            </div>
          </div>
        )}
      </div>
    </nav>
  </>
  );
}
