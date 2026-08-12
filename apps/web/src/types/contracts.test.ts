import { describe, expect, it } from 'vitest'
import { isAppEvent, isSessionSnapshot } from './contracts'

describe('wire contracts', () => {
  it('narrows a complete coach event', () => {
    expect(isAppEvent({
      type: 'coach.fast.ready', event_id: 'evt-1', timestamp: '2026-08-12T12:00:00Z',
      trace_id: 'trace-1', call_id: 'call-1', session_id: 'session-1', payload: {},
    })).toBe(true)
  })

  it('rejects an event without correlation', () => {
    expect(isAppEvent({ type: 'coach.fast.ready', payload: {} })).toBe(false)
  })

  it('recognizes canonical reconnect snapshots', () => {
    expect(isSessionSnapshot({
      call: {}, health: {}, transcript: [], conversation_state: {}, recommendations: [],
      external_context: [], evidence: [], summary: null,
    })).toBe(true)
  })
})
