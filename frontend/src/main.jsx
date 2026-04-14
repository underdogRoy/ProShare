import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const EMPTY_EDITOR = { id: null, title: '', content: '', tags: '', status: 'published' }
const EMPTY_CREDENTIALS = { email: '', username: '', password: '' }
const EMPTY_RESET = { token: '', newPassword: '', confirmPassword: '' }
const EMPTY_PROFILE = { bio: '', expertise_tags: '', links: '' }

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
  return text.length > length ? `${text.slice(0, length).trim()}...` : text
}

function readingTime(text) {
  const words = text.trim().split(/\s+/).filter(Boolean).length
  return `${Math.max(1, Math.ceil(words / 180))} min read`
}

function normalizeEditor(article) {
  return { id: article.id ?? null, title: article.title ?? '', content: article.content ?? '', tags: article.tags ?? '', status: article.status ?? 'draft' }
}

function parseTags(value) {
  return value.split(',').map((item) => item.trim()).filter(Boolean)
}

function getResetTokenFromUrl() {
  return new URLSearchParams(window.location.search).get('reset_token') || ''
}

function syncResetTokenInUrl(token) {
  const url = new URL(window.location.href)
  if (token) url.searchParams.set('reset_token', token)
  else url.searchParams.delete('reset_token')
  window.history.replaceState({}, '', url)
}

function resolutionActionLabel(action) {
  if (action === 'deleted') return 'deleted'
  if (action === 'hidden') return 'hidden'
  if (action === 'unhidden') return 'unhidden'
  if (action === 'resolved') return 'manually resolved'
  return action || 'resolved'
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
  const [page, setPage] = useState(() => {
    if (window.localStorage.getItem('proshare_token')) return 'explore'
    return getResetTokenFromUrl() ? 'reset-password' : 'auth'
  })
  const [authMode, setAuthMode] = useState('login')
  const [credentials, setCredentials] = useState(EMPTY_CREDENTIALS)
  const [forgotEmail, setForgotEmail] = useState('')
  const [resetForm, setResetForm] = useState(() => ({ ...EMPTY_RESET, token: getResetTokenFromUrl() }))
  const [resetPreviewLink, setResetPreviewLink] = useState('')
  const [currentUser, setCurrentUser] = useState(null)
  const [profileDraft, setProfileDraft] = useState(EMPTY_PROFILE)
  const [profileTagDraft, setProfileTagDraft] = useState('')
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
  const [reportReason, setReportReason] = useState('')
  const [moderationReports, setModerationReports] = useState([])
  const [moderationFilter, setModerationFilter] = useState('open')
  const [summary, setSummary] = useState(null)
  const [feedbackMessage, setFeedbackMessage] = useState('')
  const [editor, setEditor] = useState(EMPTY_EDITOR)
  const [editorMode, setEditorMode] = useState('create')

  const loggedIn = Boolean(token)
  const isAdmin = Boolean(currentUser?.is_admin)
  const publishedCount = mineArticles.filter((article) => article.status === 'published').length
  const draftCount = mineArticles.filter((article) => article.status !== 'published').length
  const filteredMineArticles = mineArticles.filter((article) => mineFilter === 'all' || article.status === mineFilter)

  useEffect(() => {
    if (token) window.localStorage.setItem('proshare_token', token)
    else window.localStorage.removeItem('proshare_token')
  }, [token])

  useEffect(() => {
    const urlToken = getResetTokenFromUrl()
    setResetForm((current) => ({ ...current, token: urlToken || current.token }))
    if (!token && urlToken) setPage('reset-password')
  }, [token])

  useEffect(() => {
    if (!notice) return undefined
    const timeoutId = window.setTimeout(() => setNotice(null), 4000)
    return () => window.clearTimeout(timeoutId)
  }, [notice])

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
        setProfileDraft({
          bio: profile.bio || '',
          expertise_tags: profile.expertise_tags || '',
          links: profile.links || '',
        })
        setProfileTagDraft('')
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

  async function loadModerationReports(filter = moderationFilter) {
    const data = await api(`/admin/reports?status=${encodeURIComponent(filter)}`, 'GET', token)
    setModerationReports(data)
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
    setReportReason('')
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
    setProfileDraft(EMPTY_PROFILE)
    setProfileTagDraft('')
    setEditor({ ...EMPTY_EDITOR })
    setEditorMode('create')
    setExploreArticles([])
    setMineArticles([])
    setSelectedArticle(null)
    setSummary(null)
    setComments([])
    setReportReason('')
    setModerationReports([])
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

  async function submitForgotPassword(event) {
    event.preventDefault()
    setNotice(null)
    if (!forgotEmail.trim()) {
      setNotice({ type: 'error', text: 'Enter the email you used for this account.' })
      return
    }

    setIsBusy(true)
    try {
      const result = await api('/auth/forgot-password', 'POST', '', { email: forgotEmail.trim() })
      setResetPreviewLink(result.reset_url || '')
      setNotice({ type: 'success', text: result.message })
    } catch (error) {
      setNotice({ type: 'error', text: error.message })
    } finally {
      setIsBusy(false)
    }
  }

  async function submitResetPassword(event) {
    event.preventDefault()
    setNotice(null)
    if (!resetForm.token.trim()) {
      setNotice({ type: 'error', text: 'Open a valid reset link or paste a reset token.' })
      return
    }
    if (resetForm.newPassword.length < 8) {
      setNotice({ type: 'error', text: 'Your new password must be at least 8 characters.' })
      return
    }
    if (resetForm.newPassword !== resetForm.confirmPassword) {
      setNotice({ type: 'error', text: 'The two password fields must match.' })
      return
    }

    setIsBusy(true)
    try {
      await api('/auth/reset-password', 'POST', '', { token: resetForm.token.trim(), new_password: resetForm.newPassword })
      setResetForm({ ...EMPTY_RESET })
      syncResetTokenInUrl('')
      setPage('auth')
      setAuthMode('login')
      setNotice({ type: 'success', text: 'Password updated. You can now sign in with your new password.' })
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

  async function submitProfile(event) {
    event.preventDefault()
    setNotice(null)
    if (profileDraft.bio.trim().length > 500) {
      setNotice({ type: 'error', text: 'Bio must be 500 characters or fewer.' })
      return
    }
    setIsBusy(true)
    try {
      await api('/users/me', 'PUT', token, {
        bio: profileDraft.bio.trim(),
        expertise_tags: profileDraft.expertise_tags.trim(),
        links: profileDraft.links.trim(),
      })
      const profile = await api('/users/me', 'GET', token)
      setCurrentUser(profile)
      setProfileDraft({
        bio: profile.bio || '',
        expertise_tags: profile.expertise_tags || '',
        links: profile.links || '',
      })
      setProfileTagDraft('')
      setNotice({ type: 'success', text: 'Profile updated successfully.' })
    } catch (error) {
      setNotice({ type: 'error', text: error.message })
    } finally {
      setIsBusy(false)
    }
  }

  function addProfileTag() {
    const nextTag = profileTagDraft.trim()
    if (!nextTag) return
    const existing = parseTags(profileDraft.expertise_tags)
    if (existing.some((tag) => tag.toLowerCase() === nextTag.toLowerCase())) {
      setProfileTagDraft('')
      return
    }
    setProfileDraft({ ...profileDraft, expertise_tags: [...existing, nextTag].join(', ') })
    setProfileTagDraft('')
  }

  function removeProfileTag(tagToRemove) {
    const filtered = parseTags(profileDraft.expertise_tags).filter((tag) => tag !== tagToRemove)
    setProfileDraft({ ...profileDraft, expertise_tags: filtered.join(', ') })
  }

  async function handleReportArticle(event) {
    event.preventDefault()
    if (!selectedArticle) return
    if (!reportReason.trim()) {
      setNotice({ type: 'error', text: 'Share a short reason before submitting a report.' })
      return
    }

    setNotice(null)
    setIsBusy(true)
    try {
      await api('/reports', 'POST', token, {
        target_type: 'article',
        target_id: selectedArticle.id,
        reason: reportReason.trim(),
      })
      setReportReason('')
      setNotice({ type: 'success', text: 'Report submitted for moderator review.' })
    } catch (error) {
      setNotice({ type: 'error', text: error.message })
    } finally {
      setIsBusy(false)
    }
  }

  async function handleModerationAction(articleId, action) {
    setNotice(null)
    setIsBusy(true)
    try {
      await api(`/admin/articles/${articleId}/${action}`, 'POST', token)
      await Promise.all([loadModerationReports(moderationFilter), loadExplore(''), loadMine()])
      if (selectedArticle?.id === articleId) {
        setPage('admin')
        setSelectedArticle(null)
      }
      setNotice({
        type: 'success',
        text:
          action === 'hide'
            ? 'Article hidden from the community feed.'
            : action === 'unhide'
              ? 'Article restored to the community feed.'
              : 'Article deleted from the platform.',
      })
    } catch (error) {
      setNotice({ type: 'error', text: error.message })
    } finally {
      setIsBusy(false)
    }
  }

  async function handleResolveReport(reportId, action = 'resolved') {
    setNotice(null)
    setIsBusy(true)
    try {
      await api('/admin/reports/resolve', 'POST', token, { report_id: reportId, action })
      await loadModerationReports(moderationFilter)
      setNotice({ type: 'success', text: 'Report marked as resolved.' })
    } catch (error) {
      setNotice({ type: 'error', text: error.message })
    } finally {
      setIsBusy(false)
    }
  }

  async function handleReopenReport(reportId) {
    setNotice(null)
    setIsBusy(true)
    try {
      await api(`/admin/reports/${reportId}/reopen`, 'POST', token)
      await loadModerationReports(moderationFilter)
      setNotice({ type: 'success', text: 'Report moved back to open.' })
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
          <p className="authLead">
            {page === 'forgot-password'
              ? 'Request a secure password reset link and get back into your writing space without losing momentum.'
              : page === 'reset-password'
                ? 'Choose a new password and return to the workspace with a clean, secure sign-in.'
                : 'Explore a cleaner publishing flow: read community articles, write in a focused editor, and use AI summaries when you want the fast version.'}
          </p>
          <div className="featurePills">
            {page === 'forgot-password' || page === 'reset-password'
              ? <><span>Private reset tokens</span><span>One-step password renewal</span><span>Same polished workspace feel</span></>
              : <><span>Separate login and registration</span><span>Community article feed</span><span>Editable drafts and published posts</span></>}
          </div>
        </section>
        <section className="pageSurface authPanel">
          {page === 'auth' && (
            <>
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
              {authMode === 'login' && (
                <button
                  type="button"
                  className="textButton"
                  onClick={() => {
                    setForgotEmail(credentials.email)
                    setResetPreviewLink('')
                    setPage('forgot-password')
                  }}
                >
                  Forgot password?
                </button>
              )}
            </>
          )}

          {page === 'forgot-password' && (
            <>
              <div className="panelHeader">
                <div>
                  <p className="eyebrow">Password Recovery</p>
                  <h3>Request a reset link</h3>
                </div>
                <button type="button" className="ghostButton compactButton" onClick={() => { setPage('auth'); setResetPreviewLink('') }}>Back To Login</button>
              </div>
              <form className="authForm" onSubmit={submitForgotPassword}>
                <label><span>Email</span><input value={forgotEmail} onChange={(event) => setForgotEmail(event.target.value)} placeholder="you@example.com" /></label>
                <button type="submit" className="primaryButton wideButton" disabled={isBusy}>{isBusy ? 'Preparing link...' : 'Send Reset Link'}</button>
              </form>
              <p className="subtleMessage">
                {resetPreviewLink
                  ? 'SMTP is not configured yet, so this build shows the secure reset link here for development.'
                  : 'If the email exists in ProShare, a secure reset link will be delivered to that inbox.'}
              </p>
              {resetPreviewLink && (
                <div className="resetPreview">
                  <p className="eyebrow">Development Preview</p>
                  <p className="subtleMessage">Open the generated link to continue to the reset screen.</p>
                  <button
                    type="button"
                    className="secondaryButton wideButton"
                    onClick={() => {
                      const tokenFromLink = new URL(resetPreviewLink).searchParams.get('reset_token') || ''
                      setResetForm({ ...EMPTY_RESET, token: tokenFromLink })
                      syncResetTokenInUrl(tokenFromLink)
                      setPage('reset-password')
                    }}
                  >
                    Open Reset Link
                  </button>
                </div>
              )}
            </>
          )}

          {page === 'reset-password' && (
            <>
              <div className="panelHeader">
                <div>
                  <p className="eyebrow">Secure Reset</p>
                  <h3>Set a new password</h3>
                </div>
                <button
                  type="button"
                  className="ghostButton compactButton"
                  onClick={() => {
                    setPage('auth')
                    setResetForm({ ...EMPTY_RESET })
                    syncResetTokenInUrl('')
                  }}
                >
                  Back To Login
                </button>
              </div>
              <form className="authForm" onSubmit={submitResetPassword}>
                {!resetForm.token && (
                  <div className="notice notice-error">
                    This reset link is missing or invalid. Request a new password reset email to continue.
                  </div>
                )}
                <label><span>New Password</span><input type="password" value={resetForm.newPassword} onChange={(event) => setResetForm({ ...resetForm, newPassword: event.target.value })} placeholder="At least 8 characters" /></label>
                <label><span>Confirm New Password</span><input type="password" value={resetForm.confirmPassword} onChange={(event) => setResetForm({ ...resetForm, confirmPassword: event.target.value })} placeholder="Re-enter your new password" /></label>
                <button type="submit" className="primaryButton wideButton" disabled={isBusy || !resetForm.token}>{isBusy ? 'Updating password...' : 'Save New Password'}</button>
              </form>
            </>
          )}
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
          <button type="button" className={`navButton ${page === 'profile' ? 'active' : ''}`} onClick={() => setPage('profile')}>Profile</button>
          {isAdmin && <button type="button" className={`navButton ${page === 'admin' ? 'active' : ''}`} onClick={() => { setPage('admin'); loadModerationReports(moderationFilter) }}>Admin</button>}
        </nav>
        <div className="headerActions">
          <div className="userSummary"><strong>{currentUser?.username || 'Writer'}</strong><span>{currentUser?.email || ''}</span></div>
          <button type="button" className="ghostButton" onClick={logout}>Log Out</button>
        </div>
      </header>
      {notice && <div className={`toastNotice notice notice-${notice.type}`}>{notice.text}</div>}
      <main className="dashboard">
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

        {!isBootstrapping && page === 'profile' && currentUser && (
          <>
            <section className="pageSurface pageHeader">
              <div>
                <p className="eyebrow">Profile Studio</p>
                <h2>@{currentUser.username}</h2>
                <p>Shape how other professionals read your background, expertise, and writing focus. Your recent articles stay visible here as a quick portfolio view.</p>
              </div>
              <div className="profileHeaderAside">
                <div className="statGrid">
                  <div className="statCard"><strong>{mineArticles.length}</strong><span>Total Pieces</span></div>
                  <div className="statCard"><strong>{publishedCount}</strong><span>Published</span></div>
                  <div className="statCard"><strong>{draftCount}</strong><span>Drafts</span></div>
                </div>
                <div className="toolbar profileHeaderToolbar">
                  <button type="button" className="ghostButton compactButton" onClick={() => setPage('profile-edit')}>Edit Profile</button>
                  <button type="button" className="ghostButton compactButton" onClick={() => { setPage('mine'); refreshMine() }}>Manage Articles</button>
                </div>
              </div>
            </section>
            <section className="pageSurface profileOverview">
                <div className="panelHeader">
                  <div>
                    <p className="eyebrow">About You</p>
                    <h3>Professional snapshot</h3>
                  </div>
                  <span className="userPill">{currentUser.email}</span>
                </div>
                <div className="profileFactGrid">
                  <div className="statCard">
                    <strong>{currentUser.username}</strong>
                    <span>Username</span>
                  </div>
                  <div className="statCard">
                    <strong>{parseTags(currentUser.expertise_tags || '').length || 0}</strong>
                    <span>Expertise Tags</span>
                  </div>
                  <div className="statCard">
                    <strong>{publishedCount}</strong>
                    <span>Published Articles</span>
                  </div>
                  <div className="statCard">
                    <strong>{currentUser.links ? 'Yes' : 'No'}</strong>
                    <span>Link Added</span>
                  </div>
                </div>
                <div className="profileCopy">
                  <h4>Bio</h4>
                  <p>{currentUser.bio || 'Add a short bio so readers understand your perspective and background.'}</p>
                </div>
                <div className="profileCopy">
                  <h4>Expertise</h4>
                  <div className="tagRow">
                    {parseTags(currentUser.expertise_tags || '').length
                      ? parseTags(currentUser.expertise_tags || '').map((tag) => (
                      <span key={tag} className="tagChip">{tag}</span>
                        ))
                      : <span className="metaText">No expertise tags yet.</span>}
                  </div>
                </div>
                <div className="profileCopy">
                  <h4>Links</h4>
                  <p>{currentUser.links || 'Add a portfolio, LinkedIn, GitHub, or personal site link.'}</p>
                </div>
            </section>
            <section className="pageSurface pageHeader portfolioHeader">
              <div>
                <p className="eyebrow">Writing Portfolio</p>
                <h2>Browse your published voice and active drafts</h2>
                <p>This portfolio view gathers your recent writing in one place, so readers can quickly understand what you create and jump straight into each piece.</p>
              </div>
              <div className="toolbar">
                <button type="button" className="ghostButton" onClick={() => { setPage('mine'); refreshMine() }}>Manage In My Articles</button>
              </div>
            </section>
            {mineArticles.length ? (
              <section className="articleGrid portfolioGrid">
                {mineArticles.map((article) => (
                  <ArticleCard key={article.id} article={article} onOpen={(id) => handleOpenArticle(id, 'profile')} onEdit={startEditingArticle} showEdit />
                ))}
              </section>
            ) : (
              <EmptyState title="Your profile is ready for its first article" text="Publish or save a draft and it will appear here as part of your creator portfolio." actionLabel="Write Your First Article" onAction={startNewArticle} />
            )}
          </>
        )}

        {!isBootstrapping && page === 'profile-edit' && currentUser && (
          <section className="profileLayout">
            <form className="pageSurface profileEditor" onSubmit={submitProfile}>
              <div className="panelHeader">
                <div>
                  <p className="eyebrow">Edit Profile</p>
                  <h2>Update your creator card</h2>
                </div>
                <button type="button" className="ghostButton compactButton" onClick={() => setPage('profile')}>Back To Profile</button>
              </div>
              <label>
                <span>Bio</span>
                <textarea rows={7} value={profileDraft.bio} onChange={(event) => setProfileDraft({ ...profileDraft, bio: event.target.value })} placeholder="Share your background, interests, and what you write about." />
                <span className="metaText">{profileDraft.bio.trim().length}/500 characters</span>
              </label>
              <div className="profileTagEditor">
                <label>
                  <span>Add Expertise Tag</span>
                  <input
                    value={profileTagDraft}
                    onChange={(event) => setProfileTagDraft(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter') {
                        event.preventDefault()
                        addProfileTag()
                      }
                    }}
                    placeholder="backend systems"
                  />
                </label>
                <button type="button" className="ghostButton compactButton" onClick={addProfileTag}>Add Tag</button>
              </div>
              <div className="tagRow editableTagRow">
                {parseTags(profileDraft.expertise_tags || '').length
                  ? parseTags(profileDraft.expertise_tags || '').map((tag) => (
                    <button key={tag} type="button" className="tagChip removableTag" onClick={() => removeProfileTag(tag)}>
                      {tag} ×
                    </button>
                    ))
                  : <span className="metaText">No expertise tags added yet.</span>}
              </div>
              <label>
                <span>Links</span>
                <input value={profileDraft.links} onChange={(event) => setProfileDraft({ ...profileDraft, links: event.target.value })} placeholder="LinkedIn, GitHub, portfolio, personal website" />
              </label>
              <div className="editorActions">
                <button type="submit" className="primaryButton" disabled={isBusy}>{isBusy ? 'Saving...' : 'Save Profile'}</button>
              </div>
            </form>
            <aside className="pageSurface writingGuide">
              <p className="eyebrow">Editing Tips</p>
              <h3>Make your profile easy to scan</h3>
              <p>Keep the bio concise, use expertise tags for specialties, and add one clean link field for your most relevant external presence.</p>
              <div className="statGrid slimStats">
                <div className="statCard"><strong>{profileDraft.bio.trim() ? profileDraft.bio.trim().split(/\s+/).length : 0}</strong><span>Bio Words</span></div>
                <div className="statCard"><strong>{parseTags(profileDraft.expertise_tags || '').length}</strong><span>Expertise Tags</span></div>
                <div className="statCard"><strong>{profileDraft.links.trim() ? 'Yes' : 'No'}</strong><span>Link Added</span></div>
              </div>
            </aside>
          </section>
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
              <label><span>Content</span><textarea rows={18} value={editor.content} onChange={(event) => setEditor({ ...editor, content: event.target.value })} placeholder="Write the article body here..." /></label>
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

        {!isBootstrapping && page === 'admin' && isAdmin && (
          <>
            <section className="pageSurface pageHeader">
              <div>
                <p className="eyebrow">Moderation Desk</p>
                <h2>{moderationFilter === 'open' ? 'Review open reports' : 'Review resolved reports'}</h2>
                <p>Inspect flagged content, track moderation status, and keep a clean history of actions taken on community reports.</p>
              </div>
              <div className="moderationHeaderActions">
                <div className="modeSwitch moderationTabs">
                  <button type="button" className={`modeButton ${moderationFilter === 'open' ? 'active' : ''}`} onClick={() => { setModerationFilter('open'); loadModerationReports('open') }}>Open</button>
                  <button type="button" className={`modeButton ${moderationFilter === 'resolved' ? 'active' : ''}`} onClick={() => { setModerationFilter('resolved'); loadModerationReports('resolved') }}>Resolved</button>
                </div>
                <button type="button" className="ghostButton compactButton refreshButton" onClick={() => loadModerationReports(moderationFilter)} disabled={isBusy}>Refresh Reports</button>
              </div>
            </section>
            {moderationReports.length ? (
              <section className="moderationList">
                {moderationReports.map((report) => (
                  <article key={report.id} className="pageSurface moderationCard">
                    <div className="panelHeader">
                      <div>
                        <p className="eyebrow">Report #{report.id}</p>
                        <h3>{report.article?.title || `${report.target_type} #${report.target_id}`}</h3>
                      </div>
                      <div className="reportStatusBlock">
                        <span className={`statusBadge ${report.status === 'resolved' ? 'status-resolved' : 'status-open'}`}>
                          {report.status === 'resolved' ? 'Resolved' : 'Open'}
                        </span>
                        <span className="metaText">{formatDate(report.created_at)}</span>
                      </div>
                    </div>
                    <p>{report.reason}</p>
                    <div className="metaCluster">
                      <span className="metaText">Reported by user #{report.reporter_id}</span>
                      <span className="metaText">Target article #{report.target_id}</span>
                      {report.article && <span className="metaText">{report.article.hidden ? 'Currently hidden' : 'Currently visible'}</span>}
                      {report.article?.status === 'deleted' && <span className="metaText">Deleted</span>}
                      {report.status === 'resolved' && report.resolution_action && <span className="metaText">Resolved via {resolutionActionLabel(report.resolution_action)}</span>}
                      {report.status === 'resolved' && report.resolved_at && <span className="metaText">Resolved {formatDate(report.resolved_at)}</span>}
                    </div>
                    {report.target_type === 'article' && report.status === 'open' && (
                      <div className="moderationActions">
                        {!report.article?.hidden && report.article?.status !== 'deleted' && (
                          <button type="button" className="primaryButton compactButton" onClick={() => handleModerationAction(report.target_id, 'hide')} disabled={isBusy}>Hide</button>
                        )}
                        {report.article?.hidden && report.article?.status !== 'deleted' && (
                          <button type="button" className="secondaryButton compactButton" onClick={() => handleModerationAction(report.target_id, 'unhide')} disabled={isBusy}>Unhide</button>
                        )}
                        {report.article?.status !== 'deleted' && (
                          <button type="button" className="ghostButton compactButton" onClick={() => handleModerationAction(report.target_id, 'remove')} disabled={isBusy}>Delete Article</button>
                        )}
                        <button
                          type="button"
                          className="secondaryButton compactButton"
                          onClick={() => handleResolveReport(report.id, report.article?.status === 'deleted' ? 'deleted' : report.article?.hidden ? 'hidden' : 'unhidden')}
                          disabled={isBusy}
                        >
                          Mark Resolved
                        </button>
                      </div>
                    )}
                    {report.status === 'resolved' && (
                      <div className="moderationActions">
                        <button type="button" className="ghostButton compactButton" onClick={() => handleReopenReport(report.id)} disabled={isBusy}>Reopen Report</button>
                      </div>
                    )}
                  </article>
                ))}
              </section>
            ) : (
              <EmptyState
                title={moderationFilter === 'open' ? 'No open reports to review' : 'No resolved reports yet'}
                text={moderationFilter === 'open' ? 'Once readers flag content, reports will appear here for moderation.' : 'Resolved moderation actions will be collected here as history.'}
              />
            )}
          </>
        )}

        {!isBootstrapping && page === 'article' && selectedArticle && (
          <section className="articleLayout">
            <article className="pageSurface articleDetail">
              <div className="articleDetailHeader">
                <button type="button" className="ghostButton" onClick={() => setPage(articleReturnTo === 'mine' ? 'mine' : articleReturnTo === 'profile' ? 'profile' : 'explore')}>Back To {articleReturnTo === 'mine' ? 'My Articles' : articleReturnTo === 'profile' ? 'Profile' : 'Explore'}</button>
                {selectedArticle.author_id === currentUser?.id && <button type="button" className="secondaryButton" onClick={() => startEditingArticle(selectedArticle)}>Edit Article</button>}
              </div>
              <div className="metaCluster">
                <StatusBadge status={selectedArticle.status} />
                <span className="metaText">{formatDate(selectedArticle.updated_at || selectedArticle.created_at)}</span>
                <span className="metaText">{readingTime(selectedArticle.content)}</span>
                <span className="metaText">Author #{selectedArticle.author_id}</span>
              </div>
              <h2>{selectedArticle.title}</h2>
              <div className="tagRow">
                {(selectedArticle.tags || 'untagged').split(',').map((tag) => tag.trim()).filter(Boolean).map((tag) => (
                  <span key={tag} className="tagChip">{tag}</span>
                ))}
              </div>
              <div className="articleBody">
                {selectedArticle.content.split(/\n+/).filter((paragraph) => paragraph.trim()).map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
              </div>
            </article>
            <aside className="articleSidebar">
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
              <section className="pageSurface sidePanel">
                <p className="eyebrow">Safety</p>
                <h3>Report this article</h3>
                <p>Flag content that needs moderator attention and include a short reason.</p>
                <form className="authForm" onSubmit={handleReportArticle}>
                  <label>
                    <span>Reason</span>
                    <textarea rows={4} value={reportReason} onChange={(event) => setReportReason(event.target.value)} placeholder="Explain what should be reviewed" />
                  </label>
                  <button type="submit" className="ghostButton" disabled={isBusy}>Submit Report</button>
                </form>
              </section>
            </aside>
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
          </section>
        )}
      </main>
    </div>
  )
}

createRoot(document.getElementById('root')).render(<App />)
