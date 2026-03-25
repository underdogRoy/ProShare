type Props = { params: Promise<{ tag: string }> }

export default async function TagPage({ params }: Props) {
  const { tag } = await params
  return (
    <section>
      <h1>Tag: {tag}</h1>
      <p>Browse articles by topic.</p>
    </section>
  )
}
