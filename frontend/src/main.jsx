import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import ReactQuill from 'react-quill'
import 'react-quill/dist/quill.snow.css'
import './styles.css'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const EMPTY_EDITOR = { id: null, title: '', content: '', tags: '', status: 'published' }
const EMPTY_CREDENTIALS = { email: '', username: '', password: '' }

async function api(path, method = 'GET', token = '', body) {
  const res = await fetch(`${API}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  })
  const text = await res.text()
  let data = {}
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = { detail: text }
    }
  }
  if (!res.ok) {
    throw new Error(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail || data))
  }
  return data
}

function formatDate(value) {
  if (!value) return 'Just now'
  return new Date(value).toLocaleString([], { year: 'numeric', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
}

function excerpt(text, length = 180) {
  if (!text) return ''
  const plain = text.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim()
  return plain.length > length ? `${plain.slice(0, length).trim()}...` : plain
}

function readingTime(text) {
  const plain = text.replace(/<[^>]*>/g, ' ')
  const words = plain.trim().split(/\s+/).filter(Boolean).length
  return `${Math.max(1, Math.ceil(words / 180))} min read`
}

function normalizeEditor(article) {
  return { id: article.id ?? null, title: article.title ?? '', content: article.content ?? '', tags: article.tags ?? '', status: article.status ?? 'draft' }
}

function StatusBadge({ status }) {
  return <span className={`statusBadge status-${status}`}>{status === 'published' ? 'Published' : 'Draft'}</span>
}

function EmptyState({ title, text, actionLabel, onAction }) {
  return (
    <section className="pageSurface emptyState">
      <p className="eyebrow">Nothing Here Yet</p>
      <h3>{title}</h3>
      <p>{text}</p>
      {actionLabel && <button type="button" className="primaryButton" onClick={onAction}>{actionLabel}</button>}
    </section>
  )
}

function ArticleCard({ article, onOpen, onEdit, showEdit }) {
  return (
    <article className="pageSurface articleCard" onClick={() => onOpen(article.id)}>
      <div className="articleCardTop">
        <StatusBadge status={article.status} />
        <span className="metaText">{readingTime(article.content)}</span>
      </div>
      <h3>{article.title}</h3>
      <p className="articleExcerpt">{excerpt(article.content)}</p>
      <div className="tagRow">
        {(article.tags || 'untagged').split(',').map((tag) => tag.trim()).filter(Boolean).map((tag) => (
          <span key={tag} className="tagChip">{tag}</span>
        ))}
      </div>
      <div className="articleCardFooter">
        <span className="metaText">{formatDate(article.updated_at || article.created_at)}</span>
        <div className="cardActions">
          {showEdit && (
            <button
              type="button"
              className="ghostButton compactButton"
              onClick={(event) => {
                event.stopPropagation()
                onEdit(article)
              }}
            >
              Edit
            </button>
          )}
          <button type="button" className="secondaryButton compactButton">Open</button>
        </div>
      </div>
    </article>
  )
}

function App() {
  const [token, setToken] = useState(() => window.localStorage.getItem('proshare_token') || '')
  const [page, setPage] = useState(() => (window.localStorage.getItem('proshare_token') ? 'explore' : 'auth'))
  const [authMode, setAuthMode] = useState('login')
  const [credentials, setCredentials] = useState(EMPTY_CREDENTIALS)
  const [currentUser, setCurrentUser] = useState(null)
  const [notice, setNotice] = useState(null)
  const [isBootstrapping, setIsBootstrapping] = useState(Boolean(window.localStorage.getItem('proshare_token')))
  const [isBusy, setIsBusy] = useState(false)
  const [exploreArticles, setExploreArticles] = useState([])
  const [exploreQuery, setExploreQuery] = useState('')
  const [mineArticles, setMineArticles] = useState([])
  const [mineFilter, setMineFilter] = useState('all')
  const [selectedArticle, setSelectedArticle] = useState(null)
  const [articleReturnTo, setArticleReturnTo] = useState('explore')
  const [articleStats, setArticleStats] = useState(null)
  const [comments, setComments] = useState([])
  const [commentDraft, setCommentDraft] = useState('')
  const [summary, setSummary] = useState(null)
  const [feedbackMessage, setFeedbackMessage] = useState('')
  const [editor, setEditor] = useState(EMPTY_EDITOR)
  const [editorMode, setEditorMode] = useState('create')

  const loggedIn = Boolean(token)
  const publishedCount = mineArticles.filter((article) => article.status === 'published').length
  const draftCount = mineArticles.filter((article) => article.status !== 'published').length
  const filteredMineArticles = mineArticles.filter((article) => mineFilter === 'all' || article.status === mineFilter)

  useEffect(() => {
    if (token) window.localStorage.setItem('proshare_token', token)
    else window.localStorage.removeItem('proshare_token')
  }, [token])

  useEffect(() => {
    if (!token) {
      setIsBootstrapping(false)
      setCurrentUser(null)
      return
    }
    let active = true
    setIsBootstrapping(true)
    async function bootstrap() {
      try {
        const [profile, recent, mine] = await Promise.all([api('/users/me', 'GET', token), api('/feeds/recent', 'GET', token), api('/articles/mine', 'GET', token)])
        if (!active) return
        setCurrentUser(profile)
        setExploreArticles(recent)
        setMineArticles(mine)
        setPage((current) => (current === 'auth' ? 'explore' : current))
      } catch (error) {
        if (!active) return
        setToken('')
        setPage('auth')
        setNotice({ type: 'error', text: error.message })
      } finally {
        if (active) setIsBootstrapping(false)
      }
    }
    bootstrap()
    return () => {
      active = false
    }
  }, [token])

  async function loadExplore(query = exploreQuery) {
    const cleaned = query.trim()
    const path = cleaned ? `/search?q=${encodeURIComponent(cleaned)}` : '/feeds/recent'
    const data = await api(path, 'GET', token)
    setExploreArticles(data)
    return data
  }

  async function loadMine() {
    const data = await api('/articles/mine', 'GET', token)
    setMineArticles(data)
    return data
  }

  async function openArticle(articleId, returnTo = 'explore') {
    const [article, articleComments, stats] = await Promise.all([
      api(`/articles/${articleId}`, 'GET', token),
      api(`/articles/${articleId}/comments`, 'GET', token),
      api(`/articles/${articleId}/stats`, 'GET', token),
    ])
    setSelectedArticle(article)
    setComments(articleComments)
    setArticleStats(stats)
    setCommentDraft('')
    setSummary(null)
    setFeedbackMessage('')
    setArticleReturnTo(returnTo)
    setPage('article')
  }

  function startNewArticle() {
    setEditor({ ...EMPTY_EDITOR })
    setEditorMode('create')
    setPage('editor')
  }

  function startEditingArticle(article) {
    setEditor(normalizeEditor(article))
    setEditorMode('edit')
    setPage('editor')
  }

  function logout() {
    setToken('')
    setCurrentUser(null)
    setCredentials(EMPTY_CREDENTIALS)
    setEditor({ ...EMPTY_EDITOR })
    setEditorMode('create')
    setExploreArticles([])
    setMineArticles([])
    setSelectedArticle(null)
    setSummary(null)
    setComments([])
    setArticleStats(null)
    setFeedbackMessage('')
    setPage('auth')
    setNotice({ type: 'success', text: 'You have been signed out.' })
  }

  async function submitAuth(event) {
    event.preventDefault()
    setNotice(null)
    if (!credentials.email || !credentials.password) {
      setNotice({ type: 'error', text: 'Email and password are required.' })
      return
    }
    if (authMode === 'register' && !credentials.username) {
      setNotice({ type: 'error', text: 'Username is required to create an account.' })
      return
    }
    setIsBusy(true)
    try {
      const body = authMode === 'login'
        ? { email: credentials.email, password: credentials.password }
        : { email: credentials.email, username: credentials.username, password: credentials.password }
      const result = await api(authMode === 'login' ? '/auth/login' : '/auth/register', 'POST', '', body)
      setToken(result.access_token)
      setCredentials(EMPTY_CREDENTIALS)
      setPage('explore')
      setNotice({ type: 'success', text: authMode === 'login' ? 'Welcome back.' : 'Account created. You are now signed in.' })
    } catch (error) {
      setNotice({ type: 'error', text: error.message })
    } finally {
      setIsBusy(false)
    }
  }

  async function submitArticle(event) {
    event.preventDefault()
    setNotice(null)
    if (!editor.title.trim() || !editor.content.trim()) {
      setNotice({ type: 'error', text: 'Title and content are required.' })
      return
    }
    setIsBusy(true)
    try {
      const payload = { title: editor.title.trim(), content: editor.content.trim(), tags: editor.tags.trim(), status: editor.status }
      const article = editorMode === 'create'
        ? await api('/articles', 'POST', token, payload)
        : await api(`/articles/${editor.id}`, 'PUT', token, payload)
      setExploreQuery('')
      await Promise.all([loadExplore(''), loadMine()])
      setNotice({
        type: 'success',
        text: editorMode === 'create'
          ? article.status === 'published' ? 'Article published to the community feed.' : 'Draft saved to My Articles.'
          : 'Article updated successfully.',
      })
      setEditorMode('edit')
      setEditor(normalizeEditor(article))
      await openArticle(article.id, 'mine')
    } catch (error) {
      setNotice({ type: 'error', text: error.message })
    } finally {
      setIsBusy(false)
    }
  }

  async function refreshExplore(event) {
    if (event) event.preventDefault()
    setNotice(null)
    setIsBusy(true)
    try {
      await loadExplore(exploreQuery)
    } catch (error) {
      setNotice({ type: 'error', text: error.message })
    } finally {
      setIsBusy(false)
    }
  }

  async function refreshMine() {
    setNotice(null)
    setIsBusy(true)
    try {
      await loadMine()
    } catch (error) {
      setNotice({ type: 'error', text: error.message })
    } finally {
      setIsBusy(false)
    }
  }

  async function handleOpenArticle(articleId, returnTo = 'explore') {
    setNotice(null)
    setIsBusy(true)
    try {
      await openArticle(articleId, returnTo)
    } catch (error) {
      setNotice({ type: 'error', text: error.message })
    } finally {
      setIsBusy(false)
    }
  }

  async function handleEngagement(action) {
    if (!selectedArticle) return
    setNotice(null)
    setIsBusy(true)
    try {
      await api(`/articles/${selectedArticle.id}/${action}`, 'POST', token)
      setArticleStats(await api(`/articles/${selectedArticle.id}/stats`, 'GET', token))
      setNotice({ type: 'success', text: action === 'like' ? 'Article liked.' : 'Article bookmarked.' })
    } catch (error) {
      setNotice({ type: 'error', text: error.message })
    } finally {
      setIsBusy(false)
    }
  }

  async function handleSummary(regenerate = false) {
    if (!selectedArticle) return
    setNotice(null)
    setIsBusy(true)
    try {
      setSummary(await api(regenerate ? `/articles/${selectedArticle.id}/summary?regenerate=true` : `/articles/${selectedArticle.id}/summary`, 'POST', token))
      setFeedbackMessage('')
    } catch (error) {
      setNotice({ type: 'error', text: error.message })
    } finally {
      setIsBusy(false)
    }
  }

  async function handleSummaryFeedback(helpful) {
    if (!selectedArticle) return
    setNotice(null)
    setIsBusy(true)
    try {
      await api(`/articles/${selectedArticle.id}/summary/feedback`, 'POST', token, { helpful, feedback: helpful ? 'helpful' : 'not helpful' })
      setFeedbackMessage(helpful ? 'Thanks, we saved your positive feedback.' : 'Got it, we saved your feedback.')
    } catch (error) {
      setNotice({ type: 'error', text: error.message })
    } finally {
      setIsBusy(false)
    }
  }

  async function handleComment(event) {
    event.preventDefault()
    if (!selectedArticle) return
    if (!commentDraft.trim()) {
      setNotice({ type: 'error', text: 'Write a comment before posting.' })
      return
    }
    setNotice(null)
    setIsBusy(true)
    try {
      await api(`/articles/${selectedArticle.id}/comments`, 'POST', token, { content: commentDraft.trim() })
      const [articleComments, stats] = await Promise.all([api(`/articles/${selectedArticle.id}/comments`, 'GET', token), api(`/articles/${selectedArticle.id}/stats`, 'GET', token)])
      setComments(articleComments)
      setArticleStats(stats)
      setCommentDraft('')
      setNotice({ type: 'success', text: 'Comment posted.' })
    } catch (error) {
      setNotice({ type: 'error', text: error.message })
    } finally {
      setIsBusy(false)
    }
  }

  if (!loggedIn) {
    return (
      <div className="authShell">
        <div className="backgroundMesh" />
        <section className="pageSurface authHero">
          <p className="eyebrow">Professional Knowledge, Better Presented</p>
          <h1>ProShare</h1>
          <p className="authLead">Explore a cleaner publishing flow: read community articles, write in a focused editor, and use AI summaries when you want the fast version.</p>
          <div className="featurePills"><span>Separate login and registration</span><span>Community article feed</span><span>Editable drafts and published posts</span></div>
        </section>
        <section className="pageSurface authPanel">
          <div className="panelHeader">
            <p className="eyebrow">Access Your Workspace</p>
            <div className="modeSwitch">
              <button type="button" className={`modeButton ${authMode === 'login' ? 'active' : ''}`} onClick={() => setAuthMode('login')}>Login</button>
              <button type="button" className={`modeButton ${authMode === 'register' ? 'active' : ''}`} onClick={() => setAuthMode('register')}>Register</button>
            </div>
          </div>
          <form className="authForm" onSubmit={submitAuth}>
            <label><span>Email</span><input value={credentials.email} onChange={(event) => setCredentials({ ...credentials, email: event.target.value })} placeholder="you@example.com" /></label>
            {authMode === 'register' && (
              <label><span>Username</span><input value={credentials.username} onChange={(event) => setCredentials({ ...credentials, username: event.target.value })} placeholder="Choose a public handle" /></label>
            )}
            <label><span>Password</span><input type="password" value={credentials.password} onChange={(event) => setCredentials({ ...credentials, password: event.target.value })} placeholder="At least 8 characters" /></label>
            <button type="submit" className="primaryButton wideButton" disabled={isBusy}>{isBusy ? 'Please wait...' : authMode === 'login' ? 'Sign In' : 'Create Account'}</button>
          </form>
          {notice && <div className={`notice notice-${notice.type}`}>{notice.text}</div>}
        </section>
      </div>
    )
  }

  return (
    <div className="appShell">
      <div className="backgroundMesh" />
      <header className="pageSurface topBar">
        <div>
          <p className="eyebrow">Editorial Workspace</p>
          <div className="brandRow"><h1>ProShare</h1>{currentUser && <span className="userPill">@{currentUser.username}</span>}</div>
        </div>
        <nav className="navBar">
          <button type="button" className={`navButton ${page === 'explore' ? 'active' : ''}`} onClick={() => setPage('explore')}>Explore</button>
          <button type="button" className={`navButton ${page === 'editor' ? 'active' : ''}`} onClick={startNewArticle}>Write</button>
          <button type="button" className={`navButton ${page === 'mine' ? 'active' : ''}`} onClick={() => { setPage('mine'); refreshMine() }}>My Articles</button>
        </nav>
        <div className="headerActions">
          <div className="userSummary"><strong>{currentUser?.username || 'Writer'}</strong><span>{currentUser?.email || ''}</span></div>
          <button type="button" className="ghostButton" onClick={logout}>Log Out</button>
        </div>
      </header>
      <main className="dashboard">
        {notice && <div className={`notice notice-${notice.type}`}>{notice.text}</div>}
        {isBootstrapping && <div className="pageSurface loadingPanel">Loading your workspace...</div>}

        {!isBootstrapping && page === 'explore' && (
          <>
            <section className="pageSurface pageHeader">
              <div>
                <p className="eyebrow">Read Across The Community</p>
                <h2>Published articles from every user</h2>
                <p>Browse the latest writing, search by topic, and open any article for comments, engagement, and AI summaries.</p>
              </div>
              <form className="toolbar" onSubmit={refreshExplore}>
                <input value={exploreQuery} onChange={(event) => setExploreQuery(event.target.value)} placeholder="Search by title, content, or tags" />
                <button type="submit" className="primaryButton" disabled={isBusy}>Search</button>
                <button type="button" className="ghostButton" onClick={() => { setExploreQuery(''); refreshExplore() }}>Show Latest</button>
              </form>
            </section>
            {exploreArticles.length ? (
              <section className="articleGrid">
                {exploreArticles.map((article) => <ArticleCard key={article.id} article={article} onOpen={(id) => handleOpenArticle(id, 'explore')} />)}
              </section>
            ) : (
              <EmptyState title="No articles matched this view" text="Try clearing the search box or publish the first article in the community." actionLabel="Start Writing" onAction={startNewArticle} />
            )}
          </>
        )}

        {!isBootstrapping && page === 'mine' && (
          <>
            <section className="pageSurface pageHeader">
              <div>
                <p className="eyebrow">Your Writing Desk</p>
                <h2>Manage articles you have written</h2>
                <p>Review drafts, polish published posts, and jump into editing whenever you need to refine something.</p>
              </div>
              <div className="statGrid">
                <div className="statCard"><strong>{mineArticles.length}</strong><span>Total Articles</span></div>
                <div className="statCard"><strong>{publishedCount}</strong><span>Published</span></div>
                <div className="statCard"><strong>{draftCount}</strong><span>Drafts</span></div>
              </div>
            </section>
            <section className="pageSurface filterBar">
              <div className="modeSwitch">
                {['all', 'published', 'draft'].map((filter) => (
                  <button key={filter} type="button" className={`modeButton ${mineFilter === filter ? 'active' : ''}`} onClick={() => setMineFilter(filter)}>
                    {filter === 'all' ? 'All' : filter === 'published' ? 'Published' : 'Drafts'}
                  </button>
                ))}
              </div>
              <button type="button" className="ghostButton" onClick={refreshMine}>Refresh</button>
            </section>
            {filteredMineArticles.length ? (
              <section className="articleGrid">
                {filteredMineArticles.map((article) => (
                  <ArticleCard key={article.id} article={article} onOpen={(id) => handleOpenArticle(id, 'mine')} onEdit={startEditingArticle} showEdit />
                ))}
              </section>
            ) : (
              <EmptyState title="No articles in this filter" text="Create a new piece or switch filters to see your other drafts and published posts." actionLabel="Write A New Article" onAction={startNewArticle} />
            )}
          </>
        )}

        {!isBootstrapping && page === 'editor' && (
          <section className="editorLayout">
            <form className="pageSurface editorPanel" onSubmit={submitArticle}>
              <div className="panelHeader">
                <div>
                  <p className="eyebrow">{editorMode === 'create' ? 'Focused Writing' : 'Editing Session'}</p>
                  <h2>{editorMode === 'create' ? 'Write a new article' : 'Edit your article'}</h2>
                </div>
                {editorMode === 'edit' && <button type="button" className="ghostButton" onClick={() => { setEditor({ ...EMPTY_EDITOR }); setEditorMode('create') }}>Start Fresh</button>}
              </div>
              <label><span>Title</span><input value={editor.title} onChange={(event) => setEditor({ ...editor, title: event.target.value })} placeholder="Give your article a clear headline" /></label>
              <div className="splitFields">
                <label><span>Tags</span><input value={editor.tags} onChange={(event) => setEditor({ ...editor, tags: event.target.value })} placeholder="leadership, backend, career" /></label>
                <label><span>Status</span><select value={editor.status} onChange={(event) => setEditor({ ...editor, status: event.target.value })}><option value="published">Published</option><option value="draft">Draft</option></select></label>
              </div>
              <div className="richEditorWrapper">
                <span className="richEditorLabel">Content</span>
                <ReactQuill
                  theme="snow"
                  value={editor.content}
                  onChange={(value) => setEditor({ ...editor, content: value })}
                  placeholder="Write the article body here..."
                  modules={{
                    toolbar: [
                      [{ font: [] }, { size: ['small', false, 'large', 'huge'] }],
                      ['bold', 'italic', 'underline', 'strike'],
                      [{ color: [] }, { background: [] }],
                      [{ list: 'ordered' }, { list: 'bullet' }],
                      ['clean'],
                    ],
                  }}
                />
              </div>
              <div className="editorActions">
                <button type="submit" className="primaryButton" disabled={isBusy}>
                  {isBusy ? 'Saving...' : editorMode === 'create' ? editor.status === 'published' ? 'Publish Article' : 'Save Draft' : 'Save Changes'}
                </button>
                <button type="button" className="ghostButton" onClick={() => setPage('mine')}>Back To My Articles</button>
              </div>
            </form>
            <aside className="pageSurface writingGuide">
              <p className="eyebrow">Editor Notes</p>
              <h3>Use this space for writing, not browsing</h3>
              <p>This page is intentionally separate from the reader view so creating content feels focused instead of crowded.</p>
              <div className="statGrid slimStats">
                <div className="statCard"><strong>{editor.title.trim() ? editor.title.trim().split(/\s+/).length : 0}</strong><span>Title Words</span></div>
                <div className="statCard"><strong>{editor.content.trim() ? editor.content.trim().split(/\s+/).length : 0}</strong><span>Body Words</span></div>
                <div className="statCard"><strong>{readingTime(editor.content)}</strong><span>Estimated Read</span></div>
              </div>
              <p className="guideHint">Tip: save as draft if the structure is still changing, then publish once the article is ready for the public feed.</p>
            </aside>
          </section>
        )}

        {!isBootstrapping && page === 'article' && selectedArticle && (
          <section className="articleLayout">
            <div className="articleMain">
              <article className="pageSurface articleDetail">
                <div className="articleDetailHeader">
                  <button type="button" className="ghostButton" onClick={() => setPage(articleReturnTo === 'mine' ? 'mine' : 'explore')}>Back To {articleReturnTo === 'mine' ? 'My Articles' : 'Explore'}</button>
                  {selectedArticle.author_id === currentUser?.id && <button type="button" className="secondaryButton" onClick={() => startEditingArticle(selectedArticle)}>Edit Article</button>}
                </div>
                <div className="metaCluster">
                  <StatusBadge status={selectedArticle.status} />
                  <span className="metaText">{formatDate(selectedArticle.updated_at || selectedArticle.created_at)}</span>
                  <span className="metaText">{readingTime(selectedArticle.content)}</span>
                </div>
                <h2>{selectedArticle.title}</h2>
                <div className="tagRow">
                  {(selectedArticle.tags || 'untagged').split(',').map((tag) => tag.trim()).filter(Boolean).map((tag) => (
                    <span key={tag} className="tagChip">{tag}</span>
                  ))}
                </div>
                <div className="articleBody ql-snow"><div className="ql-editor" dangerouslySetInnerHTML={{ __html: selectedArticle.content }} /></div>
              </article>
              <section className="pageSurface sidePanel">
                <p className="eyebrow">Engagement</p>
                <div className="statGrid slimStats">
                  <div className="statCard"><strong>{articleStats?.like_count ?? 0}</strong><span>Likes</span></div>
                  <div className="statCard"><strong>{articleStats?.comment_count ?? 0}</strong><span>Comments</span></div>
                  <div className="statCard"><strong>{articleStats?.bookmarked ? 'Yes' : 'No'}</strong><span>Bookmarked</span></div>
                </div>
                <div className="stackedActions">
                  <button type="button" className="primaryButton" onClick={() => handleEngagement('like')}>Like Article</button>
                  <button type="button" className="ghostButton" onClick={() => handleEngagement('bookmark')}>Bookmark Article</button>
                </div>
              </section>
              <section className="pageSurface commentsPanel">
                <div className="panelHeader"><div><p className="eyebrow">Discussion</p><h3>Comments</h3></div></div>
                <form className="commentComposer" onSubmit={handleComment}>
                  <input value={commentDraft} onChange={(event) => setCommentDraft(event.target.value)} placeholder="Add a thoughtful response" />
                  <button type="submit" className="primaryButton" disabled={isBusy}>Post Comment</button>
                </form>
                {comments.length ? (
                  <div className="commentList">
                    {comments.map((item) => (
                      <article key={item.id} className="commentItem">
                        <strong>User #{item.user_id}</strong>
                        <span className="metaText">{formatDate(item.created_at)}</span>
                        <p>{item.content}</p>
                      </article>
                    ))}
                  </div>
                ) : <p className="subtleMessage">No comments yet. Start the discussion.</p>}
              </section>
            </div>
            <aside className="articleSidebar">
              <section className="pageSurface sidePanel">
                <p className="eyebrow">AI Summary</p>
                <h3>Summarize this article</h3>
                <p>Generate a quick TL;DR and takeaways without leaving the reading page.</p>
                <div className="stackedActions">
                  <button type="button" className="primaryButton" onClick={() => handleSummary(false)}>Generate Summary</button>
                  <button type="button" className="ghostButton" onClick={() => handleSummary(true)}>Regenerate</button>
                </div>
                {summary && (
                  <div className="summaryPanel">
                    <h4>TL;DR</h4>
                    <p>{summary.tldr}</p>
                    <ul>{summary.takeaways.map((item) => <li key={item}>{item}</li>)}</ul>
                    <div className="feedbackRow">
                      <button type="button" className="secondaryButton compactButton" onClick={() => handleSummaryFeedback(true)}>Helpful</button>
                      <button type="button" className="ghostButton compactButton" onClick={() => handleSummaryFeedback(false)}>Not Helpful</button>
                    </div>
                    {feedbackMessage && <p className="subtleMessage">{feedbackMessage}</p>}
                  </div>
                )}
              </section>
            </aside>
          </section>
        )}
      </main>
    </div>
  )
}

createRoot(document.getElementById('root')).render(<App />)
