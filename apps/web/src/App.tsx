import { useCallback, useEffect, useReducer, useRef, useState } from 'react'
import { api } from './lib/api'
import { runAutomatedDemo } from './lib/demoFlow'
import { emptySession, sessionReducer } from './lib/sessionReducer'
import { TwilioCallClient } from './lib/twilio'
import { useSessionSocket } from './hooks/useSessionSocket'
import { HealthBar } from './components/HealthBar'
import { CallPanel } from './components/CallPanel'
import { TranscriptPanel } from './components/TranscriptPanel'
import { CoachPanel } from './components/CoachPanel'
import { SummaryPanel } from './components/SummaryPanel'
import { ModeBanner } from './components/ModeBanner'
import type { SessionSnapshot } from './types/contracts'
import { ProviderReadiness, type ProviderReadinessState } from './components/ProviderReadiness'
import { requestMicrophone } from './lib/microphone'

const demoSnapshot: SessionSnapshot = {
  call: { id: 'demo', status: 'connected' },
  pre_call_brief: { customer_id: 'demo-customer', known: ['Budget: £425,000'], source_call_id: 'prior-demo', last_commitment: ['Viewing: Saturday'], suggested_opening: 'Refer to the previous Saturday viewing commitment.' },
  health: { call: 'live', media: 'live', stt: 'live', coach: 'live', data: 'live' },
  transcript: [
    { id: 'a1', call_id: 'demo', speaker: 'agent', text: 'What budget are you working to?', timestamp: new Date().toISOString(), sequence: 1, is_final: true, source_track: 'outbound_track' },
    { id: 'b1', call_id: 'demo', speaker: 'customer', text: 'Up to £450,000, mortgage approved, and we need to move in 6 weeks. Some places feel overpriced.', timestamp: new Date().toISOString(), sequence: 2, is_final: true, source_track: 'inbound_track' },
  ],
  conversation_state: {
    ...emptySession.conversation_state,
    call_id: 'demo', call_type: 'buyer', stage: 'objection_handling', temperature: 'warm',
    customer: { budget: { value: 450000 }, mortgage_approval: { value: 'approved' }, location_preferences: [{ value: 'Manchester city centre' }], bedrooms: { value: 2 }, timeline: { value: '6 weeks' } },
    signals: [{ type: 'high_intent', evidence: 'Wants to move quickly' }], objections: [{ type: 'price', evidence: 'Price feels a bit high' }], commitments: [{ type: 'viewing', detail: 'Open to a Saturday viewing' }], sensitive_items: [{ type: 'financial_position' }],
  },
  recommendations: [{ id: 'rec-demo', type: 'deep', next_move: 'Acknowledge the price concern, confirm the mortgage position, then offer a Saturday viewing.', reason: 'The buyer raised a price objection. Reassure on value and move toward a concrete next step.', confidence: 'high', lifecycle: 'refined', created_at: new Date().toISOString(), evidence_ids: ['ev-demo'] }],
  external_context: [],
  evidence: [{ id: 'ev-demo', claim: 'Prices fell 10%', source_title: 'UK House Price Index (synthetic fixture)', source_url: 'https://www.gov.uk/government/collections/uk-house-price-index-reports', source_tier: 1, retrieved_at: new Date().toISOString(), published_at: new Date().toISOString(), support_status: 'partial', confidence: .8, freshness: 'current', safe_to_surface_as_fact: true }],
  summary: null,
}

type DemoStatus = 'idle' | 'running' | 'completed' | 'cancelled' | 'failed'

function configuredDemoDelay() {
  const raw = new URLSearchParams(window.location.search).get('demoDelay')
  if (raw === null) return 900
  const delay = Number(raw)
  return Number.isFinite(delay) ? Math.min(5000, Math.max(0, delay)) : 900
}

export default function App({ initialDemo = false }: { initialDemo?: boolean }) {
  const initialState = { ...(initialDemo ? demoSnapshot : emptySession), processedEvents: new Set<string>() }
  const [state, dispatch] = useReducer(sessionReducer, initialState)
  const [phone, setPhone] = useState('')
  const [error, setError] = useState('')
  const [appMode, setAppMode] = useState<'synthetic' | 'real'>('synthetic')
  const [providers, setProviders] = useState<Record<string, ProviderReadinessState>>({})
  const [demoStatus, setDemoStatus] = useState<DemoStatus>('idle')
  const [demoProgress, setDemoProgress] = useState('')
  const twilio = useRef(new TwilioCallClient())
  const demoAbort = useRef<AbortController | null>(null)
  const callId = String(state.call.id ?? '') || undefined
  const stableDispatch = useCallback((event: any) => dispatch(event), [])

  useEffect(() => {
    api.health().then(result => setAppMode(result.mode)).catch(() => undefined)
    api.providers().then(setProviders).catch(() => undefined)
  }, [])

  useEffect(() => () => demoAbort.current?.abort(), [])
  useSessionSocket(callId === 'demo' ? undefined : callId, stableDispatch)

  const status = String(state.call.status ?? 'idle')
  const recommendation = state.conversation_state.current_recommendation ?? state.recommendations.at(-1)

  const start = async () => {
    setError('')
    try {
      if (!/^\+?[\d\s()-]{7,}$/.test(phone)) throw new Error('Enter a valid phone number')
      const token = await api.token('agent-browser')
      if (token.mode === 'real' && token.token) {
        setAppMode('real')
        await requestMicrophone()
        await twilio.current.connect(token.token, phone, async (nextStatus, callSid) => {
          dispatch({ type: 'call.status', payload: { status: nextStatus } })
          if (nextStatus.startsWith('error:')) setError(`Call failed (${nextStatus.slice(6)}). Check the verified number and Twilio configuration.`)
          if (callSid) {
            for (let attempt = 0; attempt < 5; attempt++) {
              try { dispatch({ type: 'session.snapshot', payload: await api.snapshot(callSid) }); break }
              catch { await new Promise(resolve => setTimeout(resolve, 200)) }
            }
          }
        })
        return
      }
      const snapshot = await api.startDemo(phone, 'demo-customer')
      dispatch({ type: 'session.snapshot', payload: snapshot })
    } catch (cause) {
      dispatch({ type: 'call.status', payload: { status: 'error' } })
      setError(cause instanceof Error ? cause.message : 'Unable to start call')
    }
  }

  const startDemo = async () => {
    if (demoAbort.current) return
    const controller = new AbortController()
    demoAbort.current = controller
    setError('')
    setDemoStatus('running')
    setDemoProgress('Starting automated buyer scenario…')
    try {
      await runAutomatedDemo({
        api,
        signal: controller.signal,
        delayMs: configuredDemoDelay(),
        onSnapshot: snapshot => dispatch({ type: 'session.snapshot', payload: snapshot }),
        onProgress: ({ step, total, message }) => setDemoProgress(`Step ${step} of ${total}: ${message}`),
      })
      setDemoStatus('completed')
      setDemoProgress('Demo complete — post-call summary ready')
    } catch (cause) {
      if (cause instanceof Error && cause.name === 'AbortError') {
        setDemoStatus('cancelled')
        setDemoProgress('Demo cancelled')
      } else {
        setDemoStatus('failed')
        setDemoProgress('Demo stopped before completion')
        setError(cause instanceof Error ? cause.message : 'Unable to run automated demo')
      }
    } finally {
      demoAbort.current = null
    }
  }

  const hangup = async () => {
    if (demoAbort.current) {
      demoAbort.current.abort()
      return
    }
    if (callId && callId !== 'demo') {
      try { dispatch({ type: 'session.snapshot', payload: await api.endCall(callId) }) }
      catch (cause) { setError(String(cause)) }
    }
    twilio.current.hangUp()
  }

  const feedback = async (useful: boolean) => { if (recommendation) await api.feedback(recommendation.id, useful) }

  return <>
    <ModeBanner mode={appMode}/>
    <ProviderReadiness providers={providers}/>
    <header className="app-header"><h1>AI SALES COACH</h1><HealthBar health={state.health} connected={status === 'connected'}/></header>
    {state.summary && demoProgress && <p role="status" aria-live="polite" className={`demo-progress demo-progress--summary demo-progress--${demoStatus}`}>{demoProgress}</p>}
    {state.summary
      ? <SummaryPanel summary={state.summary}/>
      : <div className="workspace">
        <CallPanel phone={phone} setPhone={setPhone} status={status} error={error} onCall={start} onHangup={hangup}
          onDemo={startDemo} demoStatus={demoStatus} demoProgress={demoProgress}
          customer={state.conversation_state.customer} signals={state.conversation_state.signals} objections={state.conversation_state.objections}
          commitments={state.conversation_state.commitments} sensitive={state.conversation_state.sensitive_items} preCallBrief={state.pre_call_brief}/>
        <TranscriptPanel transcript={state.transcript} checking={state.conversation_state.external_claims.length > 0 && !state.evidence.length}/>
        <CoachPanel recommendation={recommendation} stage={state.conversation_state.stage} temperature={state.conversation_state.temperature}
          sentiment={state.conversation_state.sentiment} evidence={state.evidence.at(-1)} onFeedback={feedback}/>
      </div>}
  </>
}
