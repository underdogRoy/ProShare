'use client'
import { useMutation } from '@tanstack/react-query'

import { apiFetch } from '@/lib/api'
import { SummaryPayload } from '@/types/api'

export function useGenerateSummary(articleId: number) {
  return useMutation({
    mutationFn: (regenerate: boolean) =>
      apiFetch<SummaryPayload>(`/articles/${articleId}/summary`, {
        method: 'POST',
        body: JSON.stringify({ method: 'abstractive', regenerate }),
      }),
  })
}
