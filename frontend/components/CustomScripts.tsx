'use client'

import { useEffect, useState } from 'react'
import { usePathname } from 'next/navigation'

interface ScriptData {
  id: number
  name: string
  script_code: string
  position: string
  order: number
}

interface ScriptsByPosition {
  head_start: ScriptData[]
  head_end: ScriptData[]
  body_start: ScriptData[]
  body_end: ScriptData[]
  footer: ScriptData[]
}

export default function CustomScripts() {
  const pathname = usePathname()
  const [scripts, setScripts] = useState<ScriptsByPosition | null>(null)

  useEffect(() => {
    const fetchScripts = async () => {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        const apiUrl = baseUrl.endsWith('/api') ? baseUrl : `${baseUrl}/api`
        const response = await fetch(`${apiUrl}/public/custom-scripts/?path=${encodeURIComponent(pathname)}`)
        
        if (response.ok) {
          const data = await response.json()
          setScripts(data)
        } else {
          console.error('Failed to fetch custom scripts:', response.status)
        }
      } catch (error) {
        console.error('Failed to fetch custom scripts:', error)
      }
    }

    fetchScripts()
  }, [pathname])

  useEffect(() => {
    if (!scripts) return

    // Inject body_start scripts
    if (scripts.body_start.length > 0) {
      const bodyStartContainer = document.getElementById('custom-scripts-body-start')
      if (bodyStartContainer) {
        bodyStartContainer.innerHTML = scripts.body_start.map(s => s.script_code).join('\n')
      }
    }

    // Inject body_end scripts
    if (scripts.body_end.length > 0) {
      const bodyEndContainer = document.getElementById('custom-scripts-body-end')
      if (bodyEndContainer) {
        bodyEndContainer.innerHTML = scripts.body_end.map(s => s.script_code).join('\n')
      }
    }

    // Inject footer scripts
    if (scripts.footer.length > 0) {
      const footerContainer = document.getElementById('custom-scripts-footer')
      if (footerContainer) {
        footerContainer.innerHTML = scripts.footer.map(s => s.script_code).join('\n')
      }
    }

    // Execute any inline scripts
    const executeScripts = (containerId: string) => {
      const container = document.getElementById(containerId)
      if (!container) return

      const scriptElements = container.getElementsByTagName('script')
      Array.from(scriptElements).forEach((oldScript) => {
        const newScript = document.createElement('script')
        Array.from(oldScript.attributes).forEach((attr) => {
          newScript.setAttribute(attr.name, attr.value)
        })
        newScript.textContent = oldScript.textContent
        oldScript.parentNode?.replaceChild(newScript, oldScript)
      })
    }

    executeScripts('custom-scripts-body-start')
    executeScripts('custom-scripts-body-end')
    executeScripts('custom-scripts-footer')
  }, [scripts])

  return (
    <>
      <div id="custom-scripts-body-start" suppressHydrationWarning />
      <div id="custom-scripts-body-end" suppressHydrationWarning />
      <div id="custom-scripts-footer" suppressHydrationWarning />
    </>
  )
}
