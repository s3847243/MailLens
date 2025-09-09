// hooks/useAskStream.ts
'use client'

import { useRef } from 'react'

type Handlers = {
  onOpen?: () => void
  onState?: (v: 'searching' | 'answering' | string) => void
  onDelta?: (delta: string) => void
  onChat?: (meta: { id: string; title?: string | null; updated_at?: string }) => void
  onFinal?: (payload: { citations?: any[] }) => void
  onError?: (err?: unknown) => void
  onClose?: () => void
}

export function useAskStream() {
  const esRef = useRef<EventSource | null>(null)

  const start = (chatId: string, question: string, handlers: Handlers) => {
    if (esRef.current) {
      esRef.current.close()
      esRef.current = null
    }

    const url = `/api/chats/${encodeURIComponent(chatId)}/ask?q=${encodeURIComponent(question)}`
    const es = new EventSource(url, { withCredentials: true } as any)
    esRef.current = es

    es.addEventListener('open', () => handlers.onOpen?.())

    es.addEventListener('state', (e: MessageEvent) => {
      try {
        const { value } = JSON.parse(e.data)
        console.log("state being received")
        handlers.onState?.(value)
      } catch {
        handlers.onState?.('unknown')
      }
    })

    es.addEventListener('message', (e: MessageEvent) => {
      try {
        const { delta } = JSON.parse(e.data)
        console.log("message event being received")
        if (typeof delta === 'string') handlers.onDelta?.(delta)
      } catch {
      }
    })

    es.addEventListener('chat', (e: MessageEvent) => {
      try {
        const meta = JSON.parse(e.data)
        console.log("message event being received")
        handlers.onChat?.(meta)
      } catch {}
    })

    es.addEventListener('final', (e: MessageEvent) => {
      try {
        const payload = JSON.parse(e.data)
        handlers.onFinal?.(payload)
      } catch {
        handlers.onFinal?.({})
      }
      es.close()
      esRef.current = null
      handlers.onClose?.()
    })

    es.addEventListener('error', () => {
      es.close()
      esRef.current = null
      handlers.onError?.(new Error('SSE connection error'))
      handlers.onClose?.()
    })
  }

  const stop = () => {
    if (esRef.current) {
      esRef.current.close()
      esRef.current = null
    }
  }

  return { start, stop }
}
