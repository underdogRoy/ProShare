'use client'
import { ArticleCard } from '@/components/ArticleCard'
import { useTrendingArticles } from '@/hooks/useArticles'

export default function TrendingPage() {
  const { data, isLoading } = useTrendingArticles()
  if (isLoading) return <p>Loading...</p>
  return (
    <section>
      <h1>Trending Feed</h1>
      <div>{data?.map((a) => <ArticleCard key={a.id} article={a} />)}</div>
    </section>
  )
}
