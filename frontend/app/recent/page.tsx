'use client'
import { ArticleCard } from '@/components/ArticleCard'
import { useRecentArticles } from '@/hooks/useArticles'

export default function RecentPage() {
  const { data, isLoading } = useRecentArticles()
  if (isLoading) return <p>Loading recent stories...</p>

  return (
    <section>
      <h1 style={{ marginTop: 0 }}>Recent Feed</h1>
      <p style={{ color: '#6b6b6b', fontFamily: 'Inter, Arial, sans-serif' }}>
        Freshly published insights from the ProShare community.
      </p>
      <div className="article-list">{data?.map((a) => <ArticleCard key={a.id} article={a} />)}</div>
    </section>
  )
}
