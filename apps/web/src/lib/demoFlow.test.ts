import { describe, expect, it, vi } from 'vitest'
import type { SessionSnapshot } from '../types/contracts'
import { DEMO_TURNS, runAutomatedDemo, type DemoApi } from './demoFlow'

const snapshot = (status: string, summary: SessionSnapshot['summary'] = null): SessionSnapshot => ({
  call: { id: 'call-demo', status }, health: {}, transcript: [],
  conversation_state: { call_id: 'call-demo', call_type: 'buyer', stage: 'opening', temperature: 'unknown',
    sentiment: 'unknown', customer: {}, signals: [], objections: [], commitments: [], open_questions: [],
    sensitive_items: [], external_claims: [], external_context: [], current_recommendation: null,
    previous_recommendations: [] },
  recommendations: [], external_context: [], evidence: [], summary,
})

const fakeApi = (): DemoApi => ({
  startDemo: vi.fn().mockResolvedValue(snapshot('connected')),
  utterance: vi.fn().mockResolvedValue(snapshot('connected')),
  snapshot: vi.fn().mockResolvedValue(snapshot('connected')),
  endCall: vi.fn().mockResolvedValue(snapshot('ended', {
    customer_facts: ['Budget: £450,000'], sales_signals: ['High intent'], objections: ['Price'],
    commitments: ['Saturday viewing'], external_verified_context: [], unverified_claims: [],
    ai_inferences: [], next_steps: ['Book viewing'], follow_up_memory: ['Saturday viewing'],
  })),
})

describe('runAutomatedDemo', () => {
  it('drives every scripted turn in order and returns the final summary', async () => {
    const api = fakeApi()
    const snapshots: SessionSnapshot[] = []

    const result = await runAutomatedDemo({ api, delayMs: 0, onSnapshot: (value) => snapshots.push(value) })

    expect(api.startDemo).toHaveBeenCalledWith('+447700900123', 'automated-demo-customer')
    expect(api.utterance).toHaveBeenCalledTimes(6)
    expect(vi.mocked(api.utterance).mock.calls.map(([, speaker, text]) => ({ speaker, text })))
      .toEqual(DEMO_TURNS.map(({ speaker, text }) => ({ speaker, text })))
    expect(api.endCall).toHaveBeenCalledOnce()
    expect(result.summary?.commitments).toEqual(['Saturday viewing'])
    expect(snapshots.at(-1)?.call.status).toBe('ended')
  })

  it('stops remaining turns when cancelled and completes the created session once', async () => {
    const api = fakeApi()
    const controller = new AbortController()
    vi.mocked(api.utterance).mockImplementation(async () => {
      controller.abort()
      return snapshot('connected')
    })

    await expect(runAutomatedDemo({ api, delayMs: 0, signal: controller.signal })).rejects.toMatchObject({ name: 'AbortError' })

    expect(api.utterance).toHaveBeenCalledOnce()
    expect(api.endCall).toHaveBeenCalledOnce()
  })

  it('stops after a failed turn and attempts canonical completion', async () => {
    const api = fakeApi()
    vi.mocked(api.utterance).mockRejectedValueOnce(new Error('backend unavailable'))

    await expect(runAutomatedDemo({ api, delayMs: 0 })).rejects.toThrow('Automated demo stopped at turn 1')

    expect(api.utterance).toHaveBeenCalledOnce()
    expect(api.endCall).toHaveBeenCalledOnce()
  })
})
