'use client'

import { useEffect } from 'react'
import Script from 'next/script'

interface ScriptData {
  id: number
  name: string
  script_code: string
  position: string
  order: number
}

interface ScriptInjectorProps {
  headStartScripts?: ScriptData[]
  headEndScripts?: ScriptData[]
}

export default function ScriptInjector({ headStartScripts = [], headEndScripts = [] }: ScriptInjectorProps) {
  const renderScript = (script: ScriptData, index: number) => {
    // Remove HTML comments and extract script content
    let scriptContent = script.script_code
      .replace(/<!--/g, '')
      .replace(/-->/g, '')
      .trim()

    // Check if it contains a <script> tag
    if (scriptContent.includes('<script')) {
      // Extract the content between script tags
      const match = scriptContent.match(/<script[^>]*>([\s\S]*?)<\/script>/i)
      if (match && match[1]) {
        const innerContent = match[1].trim()
        const strategy = script.position === 'head_start' ? 'beforeInteractive' : 'afterInteractive'
        
        return (
          <Script
            key={`${script.position}-${script.id}-${index}`}
            id={`custom-script-${script.id}`}
            strategy={strategy}
          >
            {innerContent}
          </Script>
        )
      }
    }

    // For noscript or other tags, render directly
    if (scriptContent.includes('<noscript')) {
      return (
        <div
          key={`${script.position}-${script.id}-${index}`}
          dangerouslySetInnerHTML={{ __html: scriptContent }}
        />
      )
    }

    return null
  }

  return (
    <>
      {headStartScripts.map((script, index) => renderScript(script, index))}
      {headEndScripts.map((script, index) => renderScript(script, index))}
    </>
  )
}
