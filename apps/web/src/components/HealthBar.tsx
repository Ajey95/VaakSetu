const labels = [['call','CALL'], ['media','MEDIA'], ['stt','STT'], ['coach','COACH'], ['data','DATA']]
export function HealthBar({ health, connected = false }: { health: Record<string, unknown>; connected?: boolean }) {
  return <div className="healthbar" aria-label="Provider health">{labels.map(([key,label]) => { const value = String(health[key] ?? (connected ? 'live' : 'connecting')); return <div className={`health health--${value}`} key={key}><strong>{label}</strong><span className="health__dot"/><span>{value[0].toUpperCase()+value.slice(1)}</span></div> })}</div>
}

