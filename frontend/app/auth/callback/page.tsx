'use client'
import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { api } from '@/components/api/axiosInstance'
import { startInitialSync } from '@/components/api/syncApi'

export default function OAuthCallback() {
  const [status, setStatus] = useState('finalizing…')
  const router = useRouter()
  const sp = useSearchParams()

  useEffect(() => {
    const ok = sp.get('ok');
    (async () => {
      try {
        const meRes = await api.get('/me')
        
        if (!meRes.data) throw new Error('Not authenticated')
        

        const initialSync = await startInitialSync();
        if ( initialSync.status == 200){
            setStatus('Connected! Redirecting… Syncing started')
        }
        
        router.replace('/c') //  chat page
      } catch (e) {
        console.error(e)
        setStatus('Failed to complete login.')
      }
    })()
  }, [router, sp])

  return <p className='justify-center'>{status}</p>
}
