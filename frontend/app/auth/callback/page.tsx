'use client'
import { Suspense, useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { api } from '@/components/api/axiosInstance'
import { startInitialSync } from '@/components/api/syncApi'

function OAuthCallbackContent() {
  const [status, setStatus] = useState('finalizing…')
  const router = useRouter()
  const sp = useSearchParams()

  useEffect(() => {
    (async () => {
      try {
        const meRes = await api.get('/me')
        
        if (!meRes.data) throw new Error('Not authenticated')
        
        const initialSync = await startInitialSync();
        if (initialSync.status == 200) {
          setStatus('Connected! Redirecting… Syncing started')
        }
        
        router.replace('/c') // chat page
      } catch (e) {
        console.error(e)
        setStatus('Failed to complete login.')
      }
    })()
  }, [router, sp])

  return <p className='justify-center'>{status}</p>
}

export default function OAuthCallback() {
  return (
    <Suspense fallback={<p className='justify-center'>Loading...</p>}>
      <OAuthCallbackContent />
    </Suspense>
  )
}