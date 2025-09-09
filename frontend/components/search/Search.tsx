'use client'

import { useState, FormEvent, KeyboardEvent } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Search, Send, Loader2, RefreshCw, AlertCircle } from "lucide-react"
import { searchEmail } from "../api/searchApi"
import { useMemo } from 'react'
import { useSyncStatus } from "@/hooks/useSyncStatus"
import { startIncrementalSync } from "../api/syncApi"

interface SearchResult {
  id: string
  subject: string
  sender: string
  snippet: string
  timestamp: string
}

export function SearchEmails() {
  const [query, setQuery] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  // const [isSyncing, setIsSyncing] = useState(false)
  const [results, setResults] = useState<SearchResult[]>([])
  const [hasSearched, setHasSearched] = useState(false)
  // const [lastSyncTime, setLastSyncTime] = useState<string>("2 minutes ago")
  const { status, refresh } = useSyncStatus(2000) 
  const isSyncing = status.state === 'initializing' || status.state === 'syncing'
  const label = useMemo(() => {
    if (status.state === 'initializing') return 'Preparing…'
    if (status.state === 'syncing') {
      
      const t = status.total ?? 0
      const p = status.processed ?? 0
      return t > 0 ? `Syncing ${p}/${t}` : 'Syncing…'
    }
    if (status.state === 'error') return status.message || 'Sync error'
    return 'Email Sync'
  }, [status])
  // const lastSyncTime = useMemo(() => {
  //   const ts = status.finished_at || status.started_at
  //   console.log(ts)
  //   return ts ? new Date(ts).toLocaleString() : '—'
  // }, [status.finished_at, status.started_at])
  const lastSyncTime = useMemo(() => {
    const iso = status.finished_at || status.started_at
    if (!iso) return '—'
    try { return new Date(iso).toLocaleString() } catch { return iso }
  }, [status.finished_at, status.started_at])
  const syncNow = async () => {
    try {
      await startIncrementalSync()  // enqueues Celery job
      await refresh()               // optional immediate refresh
    } catch (e) {
      console.error('Failed to trigger sync:', e)
    }
  }

  const searchEmails = async (searchQuery: string) => {
    if (!searchQuery.trim()) return

    setIsLoading(true)
    setHasSearched(true)

    try {
      const response = await searchEmail(searchQuery);
      
       setIsLoading(false)
      const data = response.results;
      console.log(data);
      setResults(data || [])
      
       
    } catch (error) {
      console.error('Search failed:', error)
      setResults([])
    } 
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    searchEmails(query)
  }

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      searchEmails(query)
    }
  }

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-50 to-blue-50/30">
      {/* Sync Section */}
      <div className="p-6 border-b border-slate-200/50 bg-white/80 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-600 shadow-lg">
              <RefreshCw className={`h-5 w-5 text-white ${isSyncing ? 'animate-spin' : ''}`} />
            </div>
            <div>
              <h2 className="text-lg font-semibold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
                {isSyncing ? 'Syncing emails...' : 'Email Sync'}
              </h2>
              <p className="text-sm text-slate-500">
                Last synced: {lastSyncTime}
              </p>
            </div>
          </div>
          
          <Button
          onClick={syncNow}
          disabled={isSyncing}
          size="sm"
          className="bg-gradient-to-r from-emerald-500 to-cyan-600 hover:from-emerald-600 hover:to-cyan-700 border-0 shadow-md hover:shadow-lg transition-all duration-200 disabled:opacity-50"
        >
          {isSyncing ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
              {label}
            </>
          ) : (
            <>
              <RefreshCw className="h-4 w-4 mr-2" />
              Sync now
            </>
          )}
        </Button>
        </div>
        {status.state === 'error' && (
          <p className="text-xs text-red-600">Error: {status.message || 'Unknown error'}</p>
        )}
        {/* Warning Message */}
        <div className="flex items-start gap-3 p-3 rounded-lg bg-amber-50/80 border border-amber-200/50">
          <AlertCircle className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
          <p className="text-sm text-amber-800 leading-relaxed">
            Emails sync automatically every 15 minutes. For immediate updates, use the manual sync button above.
          </p>
        </div>
      </div>

      <div className="p-6 border-b border-slate-200/50 bg-white/80 backdrop-blur-sm">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg">
            <Search className="h-5 w-5 text-white" />
          </div>
          <h2 className="text-xl font-semibold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
            Search Emails
          </h2>
        </div>
        
        <form onSubmit={handleSubmit} className="relative">
          <div className="relative group">
            <Input
              type="text"
              placeholder="Search through your emails..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              className="pr-12 border-slate-200 focus:border-blue-400 focus:ring-blue-400/20 transition-all duration-200 bg-white/90 backdrop-blur-sm shadow-sm hover:shadow-md focus:shadow-lg"
            />
            <Button
              type="submit"
              size="sm"
              disabled={isLoading || !query.trim()}
              className="absolute right-1 top-1 h-8 w-8 p-0 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 border-0 shadow-md hover:shadow-lg transition-all duration-200 disabled:opacity-50"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin text-white" />
              ) : (
                <Send className="h-4 w-4 text-white" />
              )}
            </Button>
          </div>
        </form>
      </div>

      {/* Results Area */}
      <div className="flex-1 overflow-auto">
        {isLoading && (
          <div className="flex flex-col items-center justify-center p-8 text-center">
            <div className="p-4 rounded-full bg-gradient-to-br from-blue-100 to-purple-100 mb-4">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            </div>
            <p className="text-slate-600 font-medium">Searching emails...</p>
            <p className="text-sm text-slate-400 mt-1">This may take a moment</p>
          </div>
        )}

        {!isLoading && hasSearched && results.length === 0 && (
          <div className="flex flex-col items-center justify-center p-8 text-center">
            <div className="p-4 rounded-full bg-slate-100 mb-4">
              <Search className="h-8 w-8 text-slate-400" />
            </div>
            <p className="text-slate-600 font-medium">No emails found</p>
            <p className="text-sm text-slate-400 mt-1">Try adjusting your search terms</p>
          </div>
        )}

        {!isLoading && results.length > 0 && (
          <div className="p-4 space-y-3">
            {results.map((email, index) => (
              <div
                key={email.id}
                className="group p-4 rounded-xl bg-white/60 backdrop-blur-sm border border-slate-200/50 hover:border-blue-300/50 hover:bg-white/80 transition-all cursor-pointer shadow-sm hover:shadow-md animate-in slide-in-from-bottom-2 fade-in duration-500"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-semibold text-slate-800 group-hover:text-blue-700 transition-colors line-clamp-1">
                    {email.subject}
                  </h3>
                  <span className="text-xs text-slate-500 ml-2 shrink-0">
                    {email.timestamp}
                  </span>
                </div>
                <p className="text-sm text-blue-600 font-medium mb-2">
                  {email.sender}
                </p>
                <p className="text-sm text-slate-600 line-clamp-2 leading-relaxed">
                  {email.snippet.length > 100 ? email.snippet.substring(0, 100) + '...' : email.snippet}
                </p>
              </div>
            ))}
          </div>
        )}

        {!hasSearched && (
          <div className="flex flex-col items-center justify-center p-8 text-center">
            <div className="p-6 rounded-2xl bg-gradient-to-br from-blue-50 to-purple-50 mb-6">
              <Search className="h-12 w-12 text-blue-500 mx-auto" />
            </div>
            <h3 className="text-lg font-semibold text-slate-800 mb-2">
              Search Your Emails
            </h3>
            <p className="text-slate-500 text-sm max-w-xs leading-relaxed">
              Enter keywords to find specific emails, senders, or topics in your inbox
            </p>
          </div>
        )}
      </div>
    </div>
  )
}