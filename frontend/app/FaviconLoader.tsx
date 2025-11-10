'use client'

import { useEffect } from 'react'

export default function FaviconLoader() {
  useEffect(() => {
    // Fetch company settings to get favicon URL
    const loadFavicon = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        const response = await fetch(`${apiUrl}/api/accounting/settings/`)
        
        if (response.ok) {
          const settings = await response.json()
          
          // Update favicon if available
          if (settings.favicon_url) {
            // Remove existing favicon links
            const existingLinks = document.querySelectorAll("link[rel*='icon']")
            existingLinks.forEach(link => link.remove())
            
            // Add new favicon
            const link = document.createElement('link')
            link.rel = 'icon'
            link.type = 'image/png'
            link.href = settings.favicon_url
            document.head.appendChild(link)
            
            // Add shortcut icon
            const shortcut = document.createElement('link')
            shortcut.rel = 'shortcut icon'
            shortcut.type = 'image/png'
            shortcut.href = settings.favicon_url
            document.head.appendChild(shortcut)
          }
          
          // Update page title with company name if available
          if (settings.company_name) {
            document.title = `${settings.company_name} - Door to Door Gas Delivery`
          }
        }
      } catch (error) {
        console.log('Could not load company settings for favicon')
      }
    }
    
    loadFavicon()
  }, [])
  
  return null
}
