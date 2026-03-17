import Link from 'next/link';

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-white py-12">
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
  );
}
