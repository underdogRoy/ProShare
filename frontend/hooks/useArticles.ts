'use client'
import { useQuery } from '@tanstack/react-query'

import { apiFetch } from '@/lib/api'
import { Article } from '@/types/api'

export function useRecentArticles() {
  return useQuery({
    queryKey: ['articles', 'recent'],
    queryFn: () => apiFetch<Article[]>('/articles/recent'),
  })
}

export function useTrendingArticles() {
  return useQuery({
    queryKey: ['articles', 'trending'],
    queryFn: () => apiFetch<Article[]>('/articles/trending'),
  })
}
