'use client'

import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import { getChatSessions as apiGetChatSessions, deleteChat as apiDeleteChat } from '@/components/api/chatApi'
import { ChatSession } from '@/types'


type Ctx = {
  chatSessions: ChatSession[]
  setChatSessions: (rows: ChatSession[]) => void
  refreshChats: () => Promise<void>
  deleteSession: (id: string) => Promise<void>
  updateChatMeta: (meta: { id: string; title?: string | null; updated_at?: string }) => void
}

const ChatSessionsCtx = createContext<Ctx | undefined>(undefined)

export function ChatSessionsProvider({
  initial,
  children,
}: { initial: ChatSession[]; children: React.ReactNode }) {
  const [chatSessions, setChatSessions] = useState<ChatSession[]>(initial)

  const refreshChats = useCallback(async () => {
    const rows = await apiGetChatSessions()
    setChatSessions(rows)
  }, [])

  const deleteSession = useCallback(async (id: string) => {
    setChatSessions(prev => prev.filter(s => s.id !== id))
    try {
      await apiDeleteChat(id)
    } catch (e) {
      await refreshChats()
      throw e
    }
  }, [refreshChats])

  const updateChatMeta = useCallback((meta: { id: string; title?: string | null; updated_at?: string }) => {
    setChatSessions(prev => {
      const idx = prev.findIndex(c => c.id === meta.id)
      if (idx === -1) return prev
      const next = [...prev]
      next[idx] = {
        ...next[idx],
        title: meta.title ?? next[idx].title,
        updatedAt: meta.updated_at ?? next[idx].updatedAt,
      }
      next.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
      return next
    })
  }, [])

  const value = useMemo(() => ({
    chatSessions, setChatSessions, refreshChats, deleteSession, updateChatMeta,
  }), [chatSessions, refreshChats, deleteSession, updateChatMeta])

  return <ChatSessionsCtx.Provider value={value}>{children}</ChatSessionsCtx.Provider>
}

export function useChatSessions() {
  const ctx = useContext(ChatSessionsCtx)
  if (!ctx) throw new Error('useChatSessions must be used within <ChatSessionsProvider>')
  return ctx
}
