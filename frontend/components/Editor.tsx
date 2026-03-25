'use client'
import { useState } from 'react'

export function Editor() {
  const [content, setContent] = useState('')

  return (
    <section>
      <h1>Article Editor</h1>
      <div className="flex gap-2">
        <button>B</button>
        <button>I</button>
        <button>List</button>
        <button>Code block</button>
      </div>
      <textarea
        aria-label="article-content"
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="Write your article"
      />
      <div>
        <button>Save Draft</button>
        <button>Publish</button>
      </div>
    </section>
  )
}
