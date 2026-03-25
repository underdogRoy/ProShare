'use client'
import { useState } from 'react'

import { useGenerateSummary } from '@/hooks/useSummary'

type Props = { articleId: number }

export function SummaryPanel({ articleId }: Props) {
  const [feedback, setFeedback] = useState('')
  const summaryMutation = useGenerateSummary(articleId)

  return (
    <section
      aria-label="AI summary panel"
      style={{ background: '#fff', border: '1px solid #e6e6e6', borderRadius: 14, padding: '1rem', marginBottom: '1rem' }}
    >
      <h2 style={{ marginTop: 0 }}>AI Summary</h2>
      <p style={{ fontSize: 12, color: '#6b6b6b', fontFamily: 'Inter, Arial, sans-serif' }}>
        AI-generated summary; please read full article for complete understanding.
      </p>
      <div style={{ marginTop: '0.6rem', lineHeight: 1.5 }}>
        {summaryMutation.isPending ? 'Generating summary...' : summaryMutation.data?.summary}
      </div>
      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.9rem' }}>
        <button className="btn btn-primary" onClick={() => summaryMutation.mutate(false)}>
          Generate Summary
        </button>
        <button className="btn btn-muted" onClick={() => summaryMutation.mutate(true)}>
          Regenerate
        </button>
      </div>
      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.9rem' }}>
        <button className="btn btn-muted" aria-label="helpful">
          Helpful
        </button>
        <button className="btn btn-muted" aria-label="not-helpful">
          Not helpful
        </button>
      </div>
      <textarea
        aria-label="summary feedback"
        value={feedback}
        onChange={(e) => setFeedback(e.target.value)}
        placeholder="Optional feedback"
        style={{ width: '100%', marginTop: '0.8rem', minHeight: 92, borderRadius: 8, border: '1px solid #e6e6e6', padding: '0.6rem' }}
      />
    </section>
  )
}
