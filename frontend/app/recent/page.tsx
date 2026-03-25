'use client'
import { ArticleCard } from '@/components/ArticleCard'
import { useRecentArticles } from '@/hooks/useArticles'

export default function RecentPage() {
  const { data, isLoading } = useRecentArticles()
  if (isLoading) return <p>Loading...</p>
  return (
    <section>
      <h1>Recent Feed</h1>
      <div>{data?.map((a) => <ArticleCard key={a.id} article={a} />)}</div>
    </section>
  )
}
