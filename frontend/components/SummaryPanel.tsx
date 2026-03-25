'use client'
import { useState } from 'react'

import { useGenerateSummary } from '@/hooks/useSummary'

type Props = { articleId: number }

export function SummaryPanel({ articleId }: Props) {
  const [feedback, setFeedback] = useState('')
  const summaryMutation = useGenerateSummary(articleId)

  return (
    <section aria-label="AI summary panel" className="border rounded p-4 mt-4">
      <h2 className="font-semibold">AI Summary</h2>
      <p className="text-xs text-gray-600">
        AI-generated summary; please read full article for complete understanding.
      </p>
      <div className="mt-2">
        {summaryMutation.isPending ? 'Generating summary...' : summaryMutation.data?.summary}
      </div>
      <div className="flex gap-2 mt-3">
        <button onClick={() => summaryMutation.mutate(false)}>Generate Summary</button>
        <button onClick={() => summaryMutation.mutate(true)}>Regenerate (24h limit)</button>
      </div>
      <div className="mt-3">
        <button aria-label="helpful">Helpful</button>
        <button aria-label="not-helpful">Not helpful</button>
      </div>
      <textarea
        aria-label="summary feedback"
        value={feedback}
        onChange={(e) => setFeedback(e.target.value)}
        placeholder="Optional feedback"
      />
    </section>
  )
}
