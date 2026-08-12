import type { SessionSnapshot } from '../types/contracts'

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, { ...init, headers: { 'Content-Type': 'application/json', ...init?.headers } })
  if (!response.ok) { const detail = await response.json().catch(() => ({})); throw new Error(detail.detail ?? `Request failed (${response.status})`) }
  return response.status === 204 ? undefined as T : response.json()
}

export const api = {
  providers: () => request<Record<string, { configured: boolean; blocking: boolean; mode: string }>>('/health/providers'),
  startDemo: (phone_number: string, customer_id?: string) => request<SessionSnapshot>('/demo/calls', { method: 'POST', body: JSON.stringify({ phone_number, customer_id }) }),
  utterance: (callId: string, speaker: string, text: string, is_final = true) => request(`/demo/calls/${callId}/utterances`, { method: 'POST', body: JSON.stringify({ speaker, text, is_final }) }),
  endDemo: (callId: string) => request<SessionSnapshot>(`/demo/calls/${callId}/end`, { method: 'POST' }),
  snapshot: (callId: string) => request<SessionSnapshot>(`/calls/${callId}`),
  token: (identity: string) => request<{ mode: string; token: string | null }>('/twilio/token', { method: 'POST', body: JSON.stringify({ identity }) }),
  feedback: (id: string, useful: boolean) => request(`/recommendations/${id}/feedback`, { method: 'POST', body: JSON.stringify({ useful }) }),
}

export const wsUrl = (callId: string) => `${API.replace(/^http/, 'ws')}/ws/ui/${callId}`

