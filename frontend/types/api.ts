export type Article = {
  id: number
  user_id: number
  title: string
  content: string
  status: 'draft' | 'published' | 'hidden'
  tags: string[]
  created_at: string
  updated_at: string
  published_at: string | null
}

export type SummaryPayload = {
  summary: string
  cached?: boolean
  fallback?: boolean
}
