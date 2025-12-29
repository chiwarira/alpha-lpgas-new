'use client'

import { useEffect, useState } from 'react'

interface CustomScript {
  id: number
  name: string
  placement: string
  placement_display: string
  script_code: string
  order: number
}

interface ScriptsResponse {
  head: CustomScript[]
  body_start: CustomScript[]
  body_end: CustomScript[]
}

export default function CustomScripts() {
  const [scripts, setScripts] = useState<ScriptsResponse | null>(null)

  useEffect(() => {
    const fetchScripts = async () => {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'
        // Ensure we have the /api prefix
        const apiUrl = baseUrl.includes('/api') ? baseUrl : `${baseUrl}/api`
        const response = await fetch(`${apiUrl}/accounting/custom-scripts/`)
        if (response.ok) {
          const data = await response.json()
          setScripts(data)
        }
      } catch (error) {
        console.error('Failed to fetch custom scripts:', error)
      }
    }

    fetchScripts()
  }, [])

  useEffect(() => {
    if (!scripts) return

    // Inject head scripts
    scripts.head.forEach((script) => {
      injectScript(script.script_code, 'head')
    })

    // Inject body_start scripts (at beginning of body)
    scripts.body_start.forEach((script) => {
      injectScript(script.script_code, 'body_start')
    })

    // Inject body_end scripts (at end of body)
    scripts.body_end.forEach((script) => {
      injectScript(script.script_code, 'body_end')
    })
  }, [scripts])

  const injectScript = (scriptCode: string, placement: string) => {
    // Create a container div to parse the HTML
    const container = document.createElement('div')
    container.innerHTML = scriptCode

    // Get all elements from the container
    const elements = Array.from(container.childNodes)

    elements.forEach((element) => {
      if (element.nodeType === Node.ELEMENT_NODE) {
        const el = element as Element
        
        if (el.tagName === 'SCRIPT') {
          // For script tags, we need to create a new script element
          const newScript = document.createElement('script')
          
          // Copy attributes
          Array.from(el.attributes).forEach((attr) => {
            newScript.setAttribute(attr.name, attr.value)
          })
          
          // Copy inline content
          if (el.textContent) {
            newScript.textContent = el.textContent
          }

          // Append to appropriate location
          if (placement === 'head') {
            document.head.appendChild(newScript)
          } else if (placement === 'body_start') {
            document.body.insertBefore(newScript, document.body.firstChild)
          } else {
            document.body.appendChild(newScript)
          }
        } else {
          // For non-script elements (like noscript), clone and append
          const cloned = el.cloneNode(true)
          
          if (placement === 'head') {
            document.head.appendChild(cloned)
          } else if (placement === 'body_start') {
            document.body.insertBefore(cloned, document.body.firstChild)
          } else {
            document.body.appendChild(cloned)
          }
        }
      }
    })
  }

  // This component doesn't render anything visible
  return null
}
