import type { ReactNode } from 'react'
import Link from 'next/link'

import { Providers } from '@/app/providers'
import './globals.css'

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="site-header">
          <div className="header-inner">
            <Link href="/" className="brand">
              ProShare
            </Link>
            <nav className="header-nav">
              <Link href="/recent">Recent</Link>
              <Link href="/trending">Trending</Link>
              <Link href="/search">Search</Link>
              <Link href="/editor" className="nav-pill">
                Write
              </Link>
            </nav>
          </div>
        </header>
        <main className="main-shell">
          <Providers>{children}</Providers>
        </main>
      </body>
    </html>
  )
}
