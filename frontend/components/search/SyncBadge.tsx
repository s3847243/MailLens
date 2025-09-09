'use client'
import { useMemo } from 'react'
import { useSyncStatus } from '@/hooks/useSyncStatus'
import { startIncrementalSync } from '../api/syncApi'


export function SyncBadge() {
  const { status, refresh } = useSyncStatus(2000)

  const label = useMemo(() => {
    switch (status.state) {
      case 'initializing': return 'Preparing…'
      case 'syncing': {
        const t = status.total ?? 0
        const p = status.processed ?? 0
        return t > 0 ? `Syncing ${p}/${t}` : 'Syncing…'
      }
      case 'done': return 'Up to date'
      case 'error': return 'Sync error'
      default: return 'Idle'
    }
  }, [status])

  const color = status.state === 'error'
    ? 'text-red-600'
    : status.state === 'syncing' || status.state === 'initializing'
      ? 'text-amber-600'
      : 'text-emerald-600'

  return (
    <div className="flex items-center gap-2">
      <span className={`text-xs ${color}`}>{label}</span>
      <button
        className="rounded border px-2 py-1 text-xs hover:bg-gray-50"
        onClick={async () => {
          try {
            await startIncrementalSync()
            await refresh()
          } catch (e) {
            console.error('Failed to trigger incremental sync', e)
          }
        }}
        title="Sync now"
      >
        Sync now
      </button>
    </div>
  )
}
