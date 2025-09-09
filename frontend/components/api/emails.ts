import { api } from '@/components/api/axiosInstance'

export type EmailDetail = {
  id: string
  gmail_account_id: string
  message_id: string
  thread_id?: string | null
  subject?: string | null
  from_addr?: string | null
  to_addr?: string | null
  cc?: string | null
  bcc?: string | null
  date?: string | null
  snippet?: string | null
  body_text?: string | null
  body_html?: string | null
  headers_json?: Record<string, string> | null
}

export async function getEmailByDbId(id: string): Promise<EmailDetail> {
  const { data } = await api.get(`/emails/${id}`)
  return data
}

export async function getEmailByMessageId(messageId: string): Promise<EmailDetail> {
  const { data } = await api.get(`/emails/by-gmail/${messageId}`)
  return data
}