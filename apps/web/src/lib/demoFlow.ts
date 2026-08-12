import type { SessionSnapshot, Speaker } from '../types/contracts'

export interface DemoTurn {
  speaker: Speaker
  text: string
  label: string
}

export const DEMO_TURNS: readonly DemoTurn[] = [
  { speaker: 'agent', label: 'Opening and qualification', text: 'Thanks for speaking with me. What are you looking for, and what matters most for your move?' },
  { speaker: 'customer', label: 'Buyer requirements', text: "I'm a buyer looking in Manchester city centre for 2 bedrooms. My budget is £450,000, mortgage approved, and I need to move within six weeks." },
  { speaker: 'agent', label: 'Progression question', text: 'That gives me a clear brief. Is there anything stopping you from arranging a viewing if we find the right property?' },
  { speaker: 'customer', label: 'Objection and market claim', text: 'The asking price feels too high and overpriced. I heard Manchester house prices fell 10%.' },
  { speaker: 'agent', label: 'Commitment request', text: 'I understand the price concern. Shall I arrange a viewing for Saturday so you can assess the value in person?' },
  { speaker: 'customer', label: 'Concrete commitment', text: 'Yes, a Saturday viewing works for me. Please book the viewing.' },
] as const

export interface DemoApi {
  startDemo(phoneNumber: string, customerId?: string): Promise<SessionSnapshot>
  utterance(callId: string, speaker: string, text: string, isFinal?: boolean): Promise<unknown>
  snapshot(callId: string): Promise<SessionSnapshot>
  endCall(callId: string): Promise<SessionSnapshot>
}

export interface DemoProgress {
  step: number
  total: number
  message: string
}

interface AutomatedDemoOptions {
  api: DemoApi
  delayMs?: number
  signal?: AbortSignal
  onSnapshot?: (snapshot: SessionSnapshot) => void
  onProgress?: (progress: DemoProgress) => void
}

const abortError = () => Object.assign(new Error('Automated demo cancelled'), { name: 'AbortError' })

function assertNotAborted(signal?: AbortSignal) {
  if (signal?.aborted) throw abortError()
}

function wait(milliseconds: number, signal?: AbortSignal): Promise<void> {
  assertNotAborted(signal)
  if (milliseconds <= 0) return Promise.resolve()
  return new Promise((resolve, reject) => {
    const onAbort = () => { clearTimeout(timer); reject(abortError()) }
    const timer = setTimeout(() => { signal?.removeEventListener('abort', onAbort); resolve() }, milliseconds)
    signal?.addEventListener('abort', onAbort, { once: true })
  })
}

const errorMessage = (error: unknown) => error instanceof Error ? error.message : String(error)

export async function runAutomatedDemo({
  api,
  delayMs = 900,
  signal,
  onSnapshot,
  onProgress,
}: AutomatedDemoOptions): Promise<SessionSnapshot> {
  assertNotAborted(signal)
  const started = await api.startDemo('+447700900123', 'automated-demo-customer')
  const callId = String(started.call.id ?? '')
  if (!callId) throw new Error('Automated demo did not receive a call ID')

  let completed = false
  onSnapshot?.(started)

  try {
    for (const [index, turn] of DEMO_TURNS.entries()) {
      assertNotAborted(signal)
      onProgress?.({ step: index + 1, total: DEMO_TURNS.length, message: turn.label })
      await wait(delayMs, signal)
      try {
        await api.utterance(callId, turn.speaker, turn.text, true)
      } catch (error) {
        throw new Error(`Automated demo stopped at turn ${index + 1}: ${errorMessage(error)}`)
      }
      assertNotAborted(signal)
      const current = await api.snapshot(callId)
      onSnapshot?.(current)
    }

    onProgress?.({ step: DEMO_TURNS.length, total: DEMO_TURNS.length, message: 'Preparing call summary' })
    const finalSnapshot = await api.endCall(callId)
    completed = true
    onSnapshot?.(finalSnapshot)
    return finalSnapshot
  } finally {
    if (!completed) {
      try {
        const finalSnapshot = await api.endCall(callId)
        onSnapshot?.(finalSnapshot)
      } catch {
        // Preserve the original cancellation or turn failure for the UI.
      }
    }
  }
}
