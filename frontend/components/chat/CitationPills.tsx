'use client'
import { CalendarDays, Mail, Link2 } from 'lucide-react'
import { CitationPill } from '@/types'
export function CitationPills({
  citations,
  onOpen,                
}: {
  citations: CitationPill[]
  onOpen?: (c: CitationPill) => void
}) {
  if (!citations?.length) return null

  const fmt = (iso?: string | null) => {
    if (!iso) return ''
    try { return new Date(iso).toLocaleString() } catch { return '' }
  }

  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {citations.map((c) => (
        <button
          key={c.id || c.messageId}
          onClick={() => onOpen?.(c)}
          className="group max-w-full inline-flex items-center gap-2 rounded-full border border-slate-200/70 bg-white/70 px-3 py-1.5 text-xs shadow-sm hover:shadow transition hover:bg-white focus:outline-none focus:ring-2 focus:ring-slate-300"
          title={c.subject || 'Open citation'}
        >
          <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow">
            <Mail className="h-3.5 w-3.5" />
          </span>
          <span className="truncate max-w-[14rem] font-medium text-slate-700">
            {c.subject || '(no subject)'}
          </span>
          {c.from && (
            <span className="hidden sm:inline text-slate-500 truncate max-w-[10rem]">
              • {c.from}
            </span>
          )}
          {c.date && (
            <span className="hidden md:inline-flex items-center gap-1 text-slate-500">
              <CalendarDays className="h-3 w-3" />
              {fmt(c.date)}
            </span>
          )}
          <span className="ml-1 hidden sm:inline text-[10px] text-slate-400 group-hover:text-slate-500">
            <Link2 className="inline h-3 w-3 -mt-0.5" /> view
          </span>
        </button>
      ))}
    </div>
  )
}