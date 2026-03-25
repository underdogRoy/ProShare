import Link from 'next/link'

import { Article } from '@/types/api'

export function ArticleCard({ article }: { article: Article }) {
  return (
    <article className="border rounded p-3">
      <h3>
        <Link href={`/articles/${article.id}`}>{article.title}</Link>
      </h3>
      <p>{article.tags.join(', ')}</p>
      <p>{article.content.slice(0, 160)}...</p>
    </article>
  )
}
