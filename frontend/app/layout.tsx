import type { ReactNode } from 'react'

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header>
          <nav>
            <a href="/recent">Recent</a> | <a href="/trending">Trending</a> |
            <a href="/editor">Write</a>
          </nav>
        </header>
        <main>{children}</main>
      </body>
    </html>
  )
}
