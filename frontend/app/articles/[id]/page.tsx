import { CommentSection } from '@/components/CommentSection'
import { SummaryPanel } from '@/components/SummaryPanel'

type Props = { params: Promise<{ id: string }> }

export default async function ArticleReaderPage({ params }: Props) {
  const { id } = await params

  return (
    <section
      style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(0, 2.2fr) minmax(280px, 1fr)',
        gap: '1.5rem',
        alignItems: 'start',
      }}
    >
      <article style={{ background: '#fff', border: '1px solid #e6e6e6', borderRadius: 14, padding: '1.5rem' }}>
        <p style={{ color: '#6b6b6b', marginTop: 0, fontFamily: 'Inter, Arial, sans-serif' }}>8 min read · Engineering</p>
        <h1 style={{ marginTop: 0 }}>Article {id}</h1>
        <p style={{ lineHeight: 1.7 }}>
          Reader view with rich text and code blocks. This layout is optimized for long-form reading and contextual AI
          support.
        </p>
        <pre style={{ background: '#f8f8f8', padding: '0.9rem', borderRadius: 8, overflowX: 'auto' }}>
          <code>{`def summarize(article_text: str) -> str:\n    return llm.generate(article_text)`}</code>
        </pre>
        <div style={{ display: 'flex', gap: '0.6rem', marginTop: '0.7rem' }}>
          <button className="btn btn-muted">👏 Like</button>
          <button className="btn btn-muted">🔖 Bookmark</button>
        </div>
      </article>

      <aside>
        <SummaryPanel articleId={Number(id)} />
        <CommentSection />
      </aside>
    </section>
  )
}
