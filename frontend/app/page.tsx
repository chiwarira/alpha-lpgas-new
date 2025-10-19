export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-center font-mono text-sm">
        <h1 className="text-4xl font-bold text-center mb-8">
          Welcome to Alpha LPGas
        </h1>
        <p className="text-xl text-center mb-4">
          Door to Door LPG Gas Delivery
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-12">
          <div className="p-6 border rounded-lg">
            <h2 className="text-2xl font-semibold mb-2">🚚 Fast Delivery</h2>
            <p>Same-day delivery available in Fish Hoek and surrounding areas</p>
          </div>
          <div className="p-6 border rounded-lg">
            <h2 className="text-2xl font-semibold mb-2">💳 Secure Payment</h2>
            <p>Pay securely online with YOCO payment gateway</p>
          </div>
          <div className="p-6 border rounded-lg">
            <h2 className="text-2xl font-semibold mb-2">📱 Easy Ordering</h2>
            <p>Order online or call us at 074 454 5665</p>
          </div>
        </div>
        <div className="text-center mt-12">
          <p className="text-gray-600">
            Backend API: <a href="http://localhost:8000/api" className="text-blue-600 hover:underline" target="_blank">http://localhost:8000/api</a>
          </p>
          <p className="text-gray-600 mt-2">
            Admin Panel: <a href="http://localhost:8000/admin" className="text-blue-600 hover:underline" target="_blank">http://localhost:8000/admin</a>
          </p>
        </div>
      </div>
    </main>
  )
}
