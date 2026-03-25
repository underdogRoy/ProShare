export default function SearchPage() {
  return (
    <section>
      <h1>Search</h1>
      <input aria-label="search" placeholder="Search articles" />
      <p>Debounced results with pagination are backed by /articles/search.</p>
    </section>
  )
}
