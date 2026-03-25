import Link from 'next/link'

import { Article } from '@/types/api'

export function ArticleCard({ article }: { article: Article }) {
  return (
    <article
      style={{
        background: '#fff',
        border: '1px solid #e6e6e6',
        borderRadius: '12px',
        padding: '1rem',
      }}
    >
      <p style={{ color: '#6b6b6b', marginTop: 0, fontFamily: 'Inter, Arial, sans-serif' }}>
        {article.tags.slice(0, 3).join(' · ') || 'General'}
      </p>
      <h3 style={{ marginTop: 0, marginBottom: '0.4rem' }}>
        <Link href={`/articles/${article.id}`}>{article.title}</Link>
      </h3>
      <p style={{ color: '#444', marginBottom: '0.8rem' }}>{article.content.slice(0, 160)}...</p>
      <small style={{ color: '#6b6b6b', fontFamily: 'Inter, Arial, sans-serif' }}>
        Updated {new Date(article.updated_at).toLocaleDateString()}
      </small>
    </article>
  )
}
