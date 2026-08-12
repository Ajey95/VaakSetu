import { describe, expect, it } from 'vitest'
import { emptyConversation, emptySession, sessionReducer } from './sessionReducer'

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
  it('updates structured conversation state and lookup health from live events', () => {
    const conversation = { ...emptyConversation, call_id: 'call-1', stage: 'objection_handling', temperature: 'warm',
      objections: [{ type: 'price' }] }
    let state = sessionReducer(emptySession, { type: 'conversation.state.updated', event_id: 'evt-state', payload: conversation })
    state = sessionReducer(state, { type: 'context.lookup.started', event_id: 'evt-start', payload: { topic: 'market' } })
    expect(state.conversation_state.stage).toBe('objection_handling')
    expect(state.conversation_state.objections).toHaveLength(1)
    expect(state.health.data).toBe('connecting')
    state = sessionReducer(state, { type: 'context.lookup.completed', event_id: 'evt-done', payload: { status: 'verified' } })
    expect(state.health.data).toBe('live')
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
  it('uses the authoritative stale lifecycle from state instead of leaving a prior card current', () => {
    const rec = { id: 'rec-1', type: 'fast', next_move: 'Ask about budget', reason: 'Discovery', confidence: 'medium',
      lifecycle: 'visible', created_at: '2026-08-12T12:00:00Z', evidence_ids: [] }
    let state = sessionReducer(emptySession, { type: 'coach.fast.ready', event_id: 'evt-rec', payload: rec })
    state = sessionReducer(state, { type: 'conversation.state.updated', event_id: 'evt-state', payload: {
      ...emptyConversation, current_recommendation: { ...rec, lifecycle: 'stale' }, stage: 'objection_handling' } })
    expect(state.recommendations.at(-1)?.lifecycle).toBe('stale')
  })
})
