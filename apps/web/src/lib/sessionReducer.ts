import type { SessionSnapshot, Utterance, Recommendation, Evidence } from '../types/contracts'

export type ClientSession = SessionSnapshot & { processedEvents: Set<string> }

export const emptyConversation = { call_id: '', call_type: 'unknown' as const, stage: 'opening', temperature: 'unknown',
  sentiment: 'unknown', customer: {}, signals: [], objections: [], commitments: [], open_questions: [],
  sensitive_items: [], external_claims: [], external_context: [], current_recommendation: null, previous_recommendations: [] }
export const emptySession: ClientSession = { call: { status: 'idle' }, health: {}, transcript: [],
  conversation_state: emptyConversation, recommendations: [], external_context: [], evidence: [], summary: null, processedEvents: new Set() }

export type SessionAction = { type: string; event_id?: string; payload: unknown }

export function sessionReducer(state: ClientSession, action: SessionAction): ClientSession {
  if (action.event_id && state.processedEvents.has(action.event_id)) return state
  const events = new Set(state.processedEvents)
  if (action.event_id) events.add(action.event_id)
  if (action.type === 'session.snapshot') return { ...(action.payload as unknown as SessionSnapshot), processedEvents: events }
  if (action.type === 'stt.partial') {
    const incoming = action.payload as unknown as Utterance
    const transcript = state.transcript.filter((item) => item.is_final || item.speaker !== incoming.speaker)
    return { ...state, transcript: [...transcript, incoming], processedEvents: events }
  }
  if (action.type === 'stt.final') {
    const incoming = action.payload as unknown as Utterance
    const transcript = state.transcript.filter((item) => item.is_final || item.speaker !== incoming.speaker)
    if (!transcript.some((item) => item.id === incoming.id)) transcript.push(incoming)
    return { ...state, transcript, processedEvents: events }
  }
  if (action.type === 'coach.fast.ready' || action.type === 'coach.deep.ready') {
    const recommendation = action.payload as unknown as Recommendation
    return { ...state, recommendations: state.recommendations.some((item) => item.id === recommendation.id)
      ? state.recommendations : [...state.recommendations, recommendation],
      conversation_state: { ...state.conversation_state, current_recommendation: recommendation }, processedEvents: events }
  }
  if (action.type === 'evidence.verified') return { ...state, evidence: [...state.evidence, action.payload as unknown as Evidence], processedEvents: events }
  if (action.type === 'summary.ready') return { ...state, summary: action.payload as unknown as SessionSnapshot['summary'], processedEvents: events }
  return { ...state, processedEvents: events }
}
