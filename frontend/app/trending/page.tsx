'use client'
import { ArticleCard } from '@/components/ArticleCard'
import { useTrendingArticles } from '@/hooks/useArticles'

export default function TrendingPage() {
  const { data, isLoading } = useTrendingArticles()
  if (isLoading) return <p>Loading trending stories...</p>

  return (
    <section>
      <h1 style={{ marginTop: 0 }}>Trending Feed</h1>
      <p style={{ color: '#6b6b6b', fontFamily: 'Inter, Arial, sans-serif' }}>
        Popular picks ranked by recency and engagement score.
      </p>
      <div className="article-list">{data?.map((a) => <ArticleCard key={a.id} article={a} />)}</div>
    </section>
  )
}
