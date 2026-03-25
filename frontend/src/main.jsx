import React, { useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function api(path, method = 'GET', token = '', body) {
  const res = await fetch(`${API}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  })

  const data = await res.json()
  if (!res.ok) {
    throw new Error(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail))
  }
  return data
}

function App() {
  const [token, setToken] = useState('')
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [articles, setArticles] = useState([])
  const [selected, setSelected] = useState(null)
  const [summary, setSummary] = useState(null)
  const [comment, setComment] = useState('')
  const [comments, setComments] = useState([])
  const [draft, setDraft] = useState({ title: '', content: '', tags: '', status: 'published' })
  const [message, setMessage] = useState('')
  const [helpful, setHelpful] = useState(null)

  const loggedIn = useMemo(() => Boolean(token), [token])

  const run = async (action) => {
    try {
      setMessage('')
      await action()
    } catch (error) {
      setMessage(error.message)
    }
  }

  const loadRecent = () => run(async () => setArticles(await api('/feeds/recent', 'GET', token)))

  const loadArticle = (id) =>
    run(async () => {
      setSelected(await api(`/articles/${id}`, 'GET', token))
      setComments(await api(`/articles/${id}/comments`, 'GET', token))
      setSummary(null)
      setHelpful(null)
    })

  return (
    <div className="page">
      <header className="hero">
        <h1>ProShare</h1>
        <p>Share professional knowledge with faster AI-powered reading.</p>
      </header>

      {!loggedIn ? (
        <section className="card">
          <h2>Login / Register</h2>
          <div className="row">
            <input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
            <input placeholder="Username (register)" value={username} onChange={(e) => setUsername(e.target.value)} />
            <input placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          <div className="row">
            <button onClick={() => run(async () => setToken((await api('/auth/login', 'POST', '', { email, password })).access_token))}>Login</button>
            <button onClick={() => run(async () => setToken((await api('/auth/register', 'POST', '', { email, username, password })).access_token))}>Register</button>
          </div>
        </section>
      ) : (
        <>
          <section className="card">
            <h2>Write Article</h2>
            <input placeholder="Title" value={draft.title} onChange={(e) => setDraft({ ...draft, title: e.target.value })} />
            <textarea placeholder="Article content" rows={8} value={draft.content} onChange={(e) => setDraft({ ...draft, content: e.target.value })} />
            <input placeholder="Tags: ai,backend,career" value={draft.tags} onChange={(e) => setDraft({ ...draft, tags: e.target.value })} />
            <button
              onClick={() =>
                run(async () => {
                  await api('/articles', 'POST', token, draft)
                  setDraft({ title: '', content: '', tags: '', status: 'published' })
                  await loadRecent()
                })
              }
            >
              Publish
            </button>
          </section>

          <section className="card">
            <div className="row between">
              <h2>Recent Feed</h2>
              <button onClick={loadRecent}>Refresh</button>
            </div>
            <div className="list">
              {articles.map((article) => (
                <article key={article.id} className="articleItem" onClick={() => loadArticle(article.id)}>
                  <h3>{article.title}</h3>
                  <p>{article.tags}</p>
                </article>
              ))}
            </div>
          </section>

          {selected && (
            <section className="card">
              <h2>{selected.title}</h2>
              <p>{selected.content}</p>
              <div className="row">
                <button onClick={() => run(async () => api(`/articles/${selected.id}/like`, 'POST', token))}>Like</button>
                <button onClick={() => run(async () => api(`/articles/${selected.id}/bookmark`, 'POST', token))}>Bookmark</button>
                <button onClick={() => run(async () => setSummary(await api(`/articles/${selected.id}/summary`, 'POST', token)))}>Generate Summary</button>
                <button onClick={() => run(async () => setSummary(await api(`/articles/${selected.id}/summary?regenerate=true`, 'POST', token)))}>Regenerate</button>
              </div>

              {summary && (
                <>
                  <div className="summaryBox">
                    <h3>TL;DR</h3>
                    <p>{summary.tldr}</p>
                    <ul>
                      {summary.takeaways.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="row">
                    <button
                      onClick={() =>
                        run(async () => {
                          await api(`/articles/${selected.id}/summary/feedback`, 'POST', token, { helpful: true, feedback: 'helpful' })
                          setHelpful('Thanks for your feedback!')
                        })
                      }
                    >
                      Helpful
                    </button>
                    <button
                      onClick={() =>
                        run(async () => {
                          await api(`/articles/${selected.id}/summary/feedback`, 'POST', token, { helpful: false, feedback: 'not helpful' })
                          setHelpful('Feedback saved.')
                        })
                      }
                    >
                      Not Helpful
                    </button>
                  </div>
                  {helpful && <small>{helpful}</small>}
                </>
              )}

              <div className="commentBox">
                <h3>Comments</h3>
                <div className="row">
                  <input value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Write a comment" />
                  <button
                    onClick={() =>
                      run(async () => {
                        await api(`/articles/${selected.id}/comments`, 'POST', token, { content: comment })
                        setComments(await api(`/articles/${selected.id}/comments`, 'GET', token))
                        setComment('')
                      })
                    }
                  >
                    Post
                  </button>
                </div>
                <ul>
                  {comments.map((item) => (
                    <li key={item.id}>{item.content}</li>
                  ))}
                </ul>
              </div>
            </section>
          )}
        </>
      )}

      {message && <p className="error">{message}</p>}
    </div>
  )
}

createRoot(document.getElementById('root')).render(<App />)
