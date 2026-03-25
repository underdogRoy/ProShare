import { render, screen } from '@testing-library/react'

import { SummaryPanel } from '@/components/SummaryPanel'

jest.mock('@/hooks/useSummary', () => ({
  useGenerateSummary: () => ({
    mutate: jest.fn(),
    isPending: false,
    data: { summary: 'TLDR: test' },
  }),
}))

describe('SummaryPanel', () => {
  it('renders summary disclaimer', () => {
    render(<SummaryPanel articleId={1} />)
    expect(screen.getByText(/AI-generated summary/i)).toBeInTheDocument()
  })
})
