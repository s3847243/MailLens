export type User = {
  id: string;
  name: string;
  email: string;
  picture_url?: string;
};

export interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
}

export type SyncStatus = {
  state: 'idle' | 'initializing' | 'syncing' | 'done' | 'error'
  total?: number
  processed?: number
  errors?: number
  started_at?: string
  finished_at?: string
  message?: string
}
export type CitationPill = {
  id: string            // internal EmailMessage.id (or any stable id)
  messageId: string     // Gmail message id
  threadId?: string | null
  subject?: string | null
  from?: string | null
  date?: string | null  // ISO
  snippet?: string | null
  score?: number | null
  source?: 'Gmail'
}