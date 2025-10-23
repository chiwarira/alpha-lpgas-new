import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import Script from 'next/script'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Alpha LPGas - Door to Door Gas Delivery',
  description: 'Professional LPG gas delivery service in Cape Town. Order online for fast, reliable delivery.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <Script 
          src="https://js.yoco.com/sdk/v1/yoco-sdk-web.js" 
          strategy="beforeInteractive"
        />
      </head>
      <body className={inter.className}>{children}</body>
    </html>
  )
}
