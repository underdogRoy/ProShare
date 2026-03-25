import { CommentSection } from '@/components/CommentSection'
import { SummaryPanel } from '@/components/SummaryPanel'

type Props = { params: Promise<{ id: string }> }

export default async function ArticleReaderPage({ params }: Props) {
  const { id } = await params

  return (
    <section>
      <h1>Article {id}</h1>
      <div>Reader view with rich text and code blocks.</div>
      <div>
        <button>Like</button>
        <button>Bookmark</button>
      </div>
      <SummaryPanel articleId={Number(id)} />
      <CommentSection />
    </section>
  )
}
