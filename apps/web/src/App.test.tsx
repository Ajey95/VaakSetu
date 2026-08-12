import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import App from './App'
import { ModeBanner } from './components/ModeBanner'
import { ProviderReadiness } from './components/ProviderReadiness'
import { SummaryPanel } from './components/SummaryPanel'
import { CallPanel } from './components/CallPanel'

describe('sales coach workspace', () => {
  it('shows explicit synthetic mode and all required health domains', () => {
    render(<App />)
    expect(screen.getByText(/synthetic demonstration/i)).toBeInTheDocument()
    const health = screen.getByLabelText('Provider health')
    for (const label of ['CALL', 'MEDIA', 'STT', 'COACH', 'DATA']) expect(within(health).getByText(label)).toBeInTheDocument()
  })
  it('labels credential-backed operation as real provider mode', () => {
    render(<ModeBanner mode="real" />)
    expect(screen.getByText(/real provider mode/i)).toBeInTheDocument()
    expect(screen.queryByText(/synthetic demonstration/i)).not.toBeInTheDocument()
  })
  it('makes every provider readiness state visible without exposing credentials', () => {
    render(<ProviderReadiness providers={{
      twilio: { configured: true, blocking: false, mode: 'real' },
      stt: { configured: true, blocking: false, mode: 'deepgram' },
      llm: { configured: false, blocking: true, mode: 'unconfigured' },
      database: { configured: false, blocking: false, mode: 'memory' },
      graph: { configured: false, blocking: false, mode: 'memory' },
      external_data: { configured: true, blocking: false, mode: 'official_uk' },
    }} />)
    for (const label of ['TWILIO', 'STT', 'LLM', 'DATABASE', 'GRAPH', 'EXTERNAL DATA']) {
      expect(screen.getByText(label)).toBeInTheDocument()
    }
    expect(screen.getByText('Required')).toBeInTheDocument()
    expect(screen.getAllByText('Ready').length).toBeGreaterThan(0)
  })
  it('validates phone number before calling', async () => {
    render(<App />)
    fireEvent.change(screen.getByLabelText(/phone number/i), { target: { value: 'Ajay' } })
    fireEvent.click(screen.getByRole('button', { name: /^call$/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/valid phone/i)
  })
  it('exposes a one-click automated demo control with visible progress', () => {
    const onDemo = vi.fn()
    render(<CallPanel phone="" setPhone={vi.fn()} status="idle" error="" onCall={vi.fn()} onHangup={vi.fn()}
      onDemo={onDemo} demoStatus="running" demoProgress="Step 2 of 6: Buyer requirements"
      customer={{}} signals={[]} objections={[]} commitments={[]} sensitive={[]} />)

    const demo = screen.getByRole('button', { name: /demo running/i })
    expect(demo).toBeDisabled()
    expect(screen.getByRole('status')).toHaveTextContent('Step 2 of 6: Buyer requirements')
    expect(onDemo).not.toHaveBeenCalled()
  })
  it('renders coaching, transcript, profile and evidence semantics from a session', () => {
    render(<App initialDemo />)
    expect(screen.getByRole('heading', { name: /call & profile/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /live conversation/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /ai coach/i })).toBeInTheDocument()
    expect(screen.getByText('£450,000')).toBeInTheDocument()
    expect(screen.getAllByText(/buyer/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/UK House Price Index/i)).toBeInTheDocument()
    expect(screen.getByText(/Partially supported/i)).toBeInTheDocument()
    expect(screen.getByText(/SENTIMENT/i)).toBeInTheDocument()
    expect(screen.getByText(/PREVIOUS CALL/i)).toBeInTheDocument()
  })
  it('keeps verified external context distinct in the post-call summary', () => {
    render(<SummaryPanel summary={{ customer_facts:['Budget: £450,000'], sales_signals:[], objections:[],
      commitments:[], external_verified_context:[{claim:'Annual prices rose 2%',source:'UK HPI',status:'supported'}],
      unverified_claims:['Customer said prices fell 10%'], ai_inferences:['Buyer appears cautious'],
      next_steps:[], follow_up_memory:[] }} />)
    expect(screen.getByRole('heading',{name:'VERIFIED EXTERNAL CONTEXT'})).toBeInTheDocument()
    expect(screen.getByText(/Annual prices rose 2%.*UK HPI/)).toBeInTheDocument()
    expect(screen.getByRole('heading',{name:'CUSTOMER CLAIMS NOT VERIFIED'})).toBeInTheDocument()
    expect(screen.getByRole('heading',{name:'AI INFERENCE'})).toBeInTheDocument()
  })
})
