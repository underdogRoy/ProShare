import Link from 'next/link'

export default function HomePage() {
  return (
    <section>
      <div
        style={{
          background: '#fff',
          border: '1px solid #e6e6e6',
          borderRadius: 16,
          padding: '2rem',
          display: 'grid',
          gridTemplateColumns: '2fr 1fr',
          gap: '1rem',
        }}
      >
        <div>
          <p style={{ fontFamily: 'Inter, Arial, sans-serif', color: '#6b6b6b' }}>Knowledge-first community</p>
          <h1 style={{ marginTop: 0, fontSize: '3rem', lineHeight: 1.05 }}>
            Share professional insight, not noise.
          </h1>
          <p style={{ fontSize: '1.1rem', maxWidth: 620 }}>
            ProShare helps experts publish thoughtful articles, while AI summaries give readers quick TL;DR and key
            takeaways.
          </p>
          <div style={{ display: 'flex', gap: '0.7rem', marginTop: '1rem' }}>
            <Link href="/recent" className="btn btn-primary">
              Start Reading
            </Link>
            <Link href="/editor" className="btn btn-muted">
              Write an Article
            </Link>
          </div>
        </div>
        <aside style={{ borderLeft: '1px solid #e6e6e6', paddingLeft: '1rem' }}>
          <h3>What&apos;s in MVP</h3>
          <ul>
            <li>Article publishing and editing</li>
            <li>Trending and recent discovery feeds</li>
            <li>AI summary generation + caching</li>
            <li>Comments, likes, bookmarks, moderation</li>
          </ul>
        </aside>
      </div>
    </section>
  )
}
