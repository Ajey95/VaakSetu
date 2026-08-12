export type CallStatus = 'idle' | 'dialing' | 'ringing' | 'connected' | 'ended' | 'error'
export type Speaker = 'agent' | 'customer'
export type HealthState = 'live' | 'connecting' | 'reconnecting' | 'degraded' | 'unavailable'

export interface Utterance {
  id: string; call_id: string; speaker: Speaker; text: string; timestamp: string
  sequence: number; is_final: boolean; confidence?: number | null; source_track: string
}

export interface Recommendation {
  id: string; type: 'fast' | 'deep'; next_move: string; reason: string
  confidence: 'low' | 'medium' | 'high'; lifecycle: 'created' | 'visible' | 'refined' | 'stale' | 'replaced'
  created_at: string; evidence_ids: string[]
}

export interface Evidence {
  id: string; claim: string; source_id?: string | null; source_title?: string | null
  source_url?: string | null; source_tier?: number | null; retrieved_at: string
  published_at?: string | null; support_status: string; confidence: number
  freshness: string; safe_to_surface_as_fact: boolean
}

export interface ConversationState {
  call_id: string; customer_id?: string | null; call_type: 'buyer' | 'vendor' | 'unknown'
  stage: string; temperature: string; sentiment: string; customer: Record<string, unknown>
  signals: Record<string, unknown>[]; objections: Record<string, unknown>[]
  commitments: Record<string, unknown>[]; open_questions: string[]
  sensitive_items: Record<string, unknown>[]; external_claims: Record<string, unknown>[]
  external_context: Record<string, unknown>[]; current_recommendation?: Recommendation | null
  previous_recommendations: Recommendation[]
}

export interface CallSummary {
  customer_facts: string[]; sales_signals: string[]; objections: string[]; commitments: string[]
  external_verified_context: Record<string, unknown>[]; unverified_claims: string[]
  ai_inferences: string[]; next_steps: string[]; follow_up_memory: string[]
}

export interface SessionSnapshot {
  call: Record<string, unknown>; health: Record<string, unknown>; transcript: Utterance[]
  conversation_state: ConversationState; recommendations: Recommendation[]
  external_context: Record<string, unknown>[]; evidence: Evidence[]; summary: CallSummary | null
}

export interface AppEvent {
  type: string; event_id: string; timestamp: string; trace_id: string
  call_id: string; session_id: string; payload: Record<string, unknown>
}

const object = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null

export function isAppEvent(value: unknown): value is AppEvent {
  if (!object(value)) return false
  return ['type', 'event_id', 'timestamp', 'trace_id', 'call_id', 'session_id']
    .every((key) => typeof value[key] === 'string' && value[key].length > 0) && object(value.payload)
}

export function isSessionSnapshot(value: unknown): value is SessionSnapshot {
  if (!object(value)) return false
  return object(value.call) && object(value.health) && Array.isArray(value.transcript)
    && object(value.conversation_state) && Array.isArray(value.recommendations)
    && Array.isArray(value.external_context) && Array.isArray(value.evidence)
    && (value.summary === null || object(value.summary))
}
