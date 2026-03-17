'use client';

import Link from 'next/link';
import { useState } from 'react';

export default function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <nav className="bg-white text-gray-800 shadow-lg border-b-2 border-rose-500 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <Link href="/" className="cursor-pointer">
              <img src="/alpha-lpgas-logo.svg" alt="Alpha LPGas Logo" className="h-12" />
            </Link>
          </div>
          
          {/* Desktop Navigation */}
          <div className="hidden md:flex space-x-8">
            <Link href="/" className="text-gray-700 hover:text-rose-600 font-semibold transition">
              Home
            </Link>
            <a href="/#products" className="text-gray-700 hover:text-rose-600 font-semibold transition">
              Products
            </a>
            <Link href="/blog" className="text-gray-700 hover:text-rose-600 font-semibold transition">
              Blog
            </Link>
            <Link href="/contact" className="text-gray-700 hover:text-rose-600 font-semibold transition">
              Contact Us
            </Link>
          </div>
          
          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="text-gray-700 hover:text-rose-600 focus:outline-none"
            >
              <svg className="h-6 w-6" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
                {mobileMenuOpen ? (
                  <path d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
          
          {/* Contact Button */}
          <div className="hidden md:flex items-center space-x-4">
            <a href="tel:0744545665" className="bg-rose-600 text-white hover:bg-rose-700 px-4 py-2 rounded-lg font-semibold transition whitespace-nowrap">
              📞 074 454 5665
            </a>
          </div>
        </div>
        
        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden pb-4">
            <div className="flex flex-col space-y-3">
              <Link href="/" className="text-gray-700 hover:text-rose-600 font-semibold transition py-2">
                Home
              </Link>
              <a href="/#products" className="text-gray-700 hover:text-rose-600 font-semibold transition py-2">
                Products
              </a>
              <Link href="/blog" className="text-gray-700 hover:text-rose-600 font-semibold transition py-2">
                Blog
              </Link>
              <Link href="/contact" className="text-gray-700 hover:text-rose-600 font-semibold transition py-2">
                Contact Us
              </Link>
              <a href="tel:0744545665" className="bg-rose-600 text-white hover:bg-rose-700 px-4 py-2 rounded-lg font-semibold transition text-center">
                📞 074 454 5665
              </a>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}
