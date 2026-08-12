import { describe, expect, it } from 'vitest'
import { emptySession, sessionReducer } from './sessionReducer'

const utterance = { id: 'partial-customer', call_id: 'call-1', speaker: 'customer' as const,
  text: 'My budget', timestamp: '2026-08-12T12:00:00Z', sequence: 1, is_final: false, source_track: 'inbound_track' }

describe('session reducer', () => {
  it('replaces state from a reconnect snapshot', () => {
    const snapshot = { ...emptySession, call: { id: 'call-1', status: 'connected' }, transcript: [{ ...utterance, id: 'utt-1', is_final: true }] }
    expect(sessionReducer(emptySession, { type: 'session.snapshot', payload: snapshot }).call.id).toBe('call-1')
  })
  it('tracks provider call lifecycle before the first backend snapshot arrives', () => {
    const state = sessionReducer(emptySession, { type: 'call.status', payload: { status: 'ringing' } })
    expect(state.call.status).toBe('ringing')
  })
  it('replaces partial speech in place then replaces it with final speech', () => {
    let state = sessionReducer(emptySession, { type: 'stt.partial', payload: utterance })
    state = sessionReducer(state, { type: 'stt.partial', payload: { ...utterance, text: 'My budget is £450,000' } })
    state = sessionReducer(state, { type: 'stt.final', payload: { ...utterance, id: 'utt-1', text: 'My budget is £450,000', is_final: true } })
    expect(state.transcript).toHaveLength(1)
    expect(state.transcript[0]).toMatchObject({ id: 'utt-1', is_final: true })
  })
  it('deduplicates repeated events and preserves refined recommendation lifecycle', () => {
    const rec = { id: 'rec-1', type: 'deep', next_move: 'Offer Saturday', reason: 'Ready', confidence: 'high',
      lifecycle: 'refined', created_at: '2026-08-12T12:00:00Z', evidence_ids: ['ev-1'] }
    let state = sessionReducer(emptySession, { type: 'coach.deep.ready', event_id: 'evt-1', payload: rec })
    state = sessionReducer(state, { type: 'coach.deep.ready', event_id: 'evt-1', payload: rec })
    expect(state.recommendations).toHaveLength(1)
    expect(state.conversation_state.current_recommendation?.lifecycle).toBe('refined')
  })
})
