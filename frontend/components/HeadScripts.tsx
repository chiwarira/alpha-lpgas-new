import Script from 'next/script'

interface ScriptData {
  id: number
  name: string
  script_code: string
  position: string
  order: number
}

interface HeadScriptsProps {
  scripts: ScriptData[]
  position: 'head_start' | 'head_end'
}

export default function HeadScripts({ scripts, position }: HeadScriptsProps) {
  if (!scripts || scripts.length === 0) return null

  const strategy = position === 'head_start' ? 'beforeInteractive' : 'afterInteractive'

  return (
    <>
      {scripts.map((script) => {
        // Check if it's an inline script or external script
        const isInlineScript = script.script_code.includes('<script') && !script.script_code.includes('src=')
        
        if (isInlineScript) {
          // Extract script content between <script> tags
          const scriptContent = script.script_code
            .replace(/<script[^>]*>/gi, '')
            .replace(/<\/script>/gi, '')
            .trim()

          return (
            <Script
              key={script.id}
              id={`custom-script-${script.id}`}
              strategy={strategy}
              dangerouslySetInnerHTML={{ __html: scriptContent }}
            />
          )
        } else {
          // For external scripts or noscript tags, render as-is
          return (
            <div
              key={script.id}
              dangerouslySetInnerHTML={{ __html: script.script_code }}
            />
          )
        }
      })}
    </>
  )
}
