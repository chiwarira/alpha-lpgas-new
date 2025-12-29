import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import Script from 'next/script'
import './globals.css'
import FaviconLoader from './FaviconLoader'
import CustomScripts from '@/components/CustomScripts'
import ScriptInjector from '@/components/ScriptInjector'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Alpha LPGas - Door to Door Gas Delivery',
  description: 'Professional LPG gas delivery service in Cape Town. Order online for fast, reliable delivery.',
}

async function getCustomScripts() {
  try {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const apiUrl = baseUrl.endsWith('/api') ? baseUrl : `${baseUrl}/api`
    const response = await fetch(`${apiUrl}/public/custom-scripts/?path=/`, {
      cache: 'no-store'
    })
    
    if (response.ok) {
      return await response.json()
    } else {
      console.error('Failed to fetch custom scripts:', response.status, response.statusText)
    }
  } catch (error) {
    console.error('Failed to fetch custom scripts:', error)
  }
  
  return {
    head_start: [],
    head_end: [],
    body_start: [],
    body_end: [],
    footer: []
  }
}

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const scripts = await getCustomScripts()

  return (
    <html lang="en">
      <head>
        <ScriptInjector 
          headStartScripts={scripts.head_start}
          headEndScripts={scripts.head_end}
        />
        <Script 
          src="https://js.yoco.com/sdk/v1/yoco-sdk-web.js" 
          strategy="beforeInteractive"
        />
      </head>
      <body className={inter.className}>
        <FaviconLoader />
        <CustomScripts />
        {children}
      </body>
    </html>
  )
}
