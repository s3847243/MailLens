// components/chat/EmailModal.tsx
'use client'
import { useEffect, useState } from 'react'
import { X, Mail, User2, Users, CalendarDays } from 'lucide-react'
import { getEmailByDbId, type EmailDetail } from '@/components/api/emails'

type Props = {
  open: boolean
  onClose: () => void
  pill: {
    id: string
    subject?: string | null
    from?: string | null
    date?: string | null
    snippet?: string | null
  } | null
}

export default function EmailModal({ open, onClose, pill }: Props) {
  const [email, setEmail] = useState<EmailDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open || !pill?.id) return
    let cancelled = false
    ;(async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await getEmailByDbId(pill.id)
        console.log(data)
        if (!cancelled) setEmail(data)
      } catch (e: any) {
        if (!cancelled) setError(e?.message || 'Failed to load email')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => { cancelled = true }
  }, [open, pill?.id])

  if (!open) return null


  const HtmlBody = () =>
    email?.body_html ? (
      <iframe
        className="w-full h-[55vh] border rounded-lg"
        sandbox="allow-same-origin"
        srcDoc={email.body_html}
      />
    ) : (
      <pre className="whitespace-pre-wrap text-sm text-slate-700">{email?.body_text || pill?.snippet || ''}</pre>
    )

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-[900px] max-w-[95vw] rounded-2xl bg-white shadow-2xl border border-slate-200">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-slate-800">
              <Mail className="h-5 w-5 text-indigo-600" />
              <h3 className="font-semibold truncate">
                {email?.subject ?? pill?.subject ?? '(no subject)'}
              </h3>
            </div>
            <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-slate-500">
              {email?.from_addr && (
                <span className="inline-flex items-center gap-1">
                  <User2 className="h-3.5 w-3.5" /> {email.from_addr}
                </span>
              )}
              {email?.to_addr && (
                <span className="inline-flex items-center gap-1">
                  <Users className="h-3.5 w-3.5" /> To: {email.to_addr}
                </span>
              )}
              {(email?.cc || email?.bcc) && (
                <span className="inline-flex items-center gap-1">
                  <Users className="h-3.5 w-3.5" /> CC/BCC
                </span>
              )}
              {(email?.date ?? pill?.date) && (
                <span className="inline-flex items-center gap-1">
                  <CalendarDays className="h-3.5 w-3.5" />
                  {new Date(email?.date ?? (pill?.date as string)).toLocaleString()}
                </span>
              )}
            </div>
          </div>

          <button
            onClick={onClose}
            className="rounded-full p-2 hover:bg-slate-100 text-slate-500 hover:text-slate-700 transition"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-5">
          {loading && <p className="text-sm text-slate-600">Loading…</p>}
          {error && <p className="text-sm text-red-600">Error: {error}</p>}
          {!loading && !error && <HtmlBody />}
        </div>
      </div>
    </div>
  )
}
  