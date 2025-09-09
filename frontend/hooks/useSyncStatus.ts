'use client'
import { useCallback, useEffect, useRef, useState } from 'react'
import { getSyncStatus } from '@/components/api/syncApi'
import { SyncStatus } from '@/types'

export function useSyncStatus(pollMs = 2000) {
  const [status, setStatus] = useState<SyncStatus>({ state: 'idle' })
  const timer = useRef<number | null>(null)

  const poll = useCallback(async () => {
    try {
      const s = await getSyncStatus()
      setStatus(s)
    } catch (e) {
    }
  }, [])

  const start = useCallback(() => {
    if (timer.current) return
    void poll()
    timer.current = window.setInterval(poll, pollMs)
  }, [poll, pollMs])

  const stop = useCallback(() => {
    if (timer.current) {
      window.clearInterval(timer.current)
      timer.current = null
    }
  }, [])

  useEffect(() => {
    start()
    return () => stop()
  }, [start, stop])

  return { status, refresh: poll, start, stop }
}
