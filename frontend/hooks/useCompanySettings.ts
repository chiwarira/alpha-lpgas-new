import { useState, useEffect } from 'react'

interface CompanySettings {
  id: number
  company_name: string
  registration_number: string
  vat_number: string
  phone: string
  email: string
  address: string
  logo: string | null
  logo_url: string | null
  favicon: string | null
  favicon_url: string | null
  bank_name: string
  account_name: string
  account_number: string
  account_type: string
  branch_code: string
  payment_reference_note: string
}

export function useCompanySettings() {
  const [settings, setSettings] = useState<CompanySettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        const response = await fetch(`${apiUrl}/api/accounting/settings/`)
        
        if (!response.ok) {
          throw new Error('Failed to fetch company settings')
        }
        
        const data = await response.json()
        setSettings(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
        console.error('Error fetching company settings:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchSettings()
  }, [])

  return { settings, loading, error }
}
