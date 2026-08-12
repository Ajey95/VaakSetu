export type ProviderReadinessState = {
  configured: boolean
  blocking: boolean
  mode: string
}

const labels: Record<string, string> = {
  twilio: 'TWILIO', stt: 'STT', llm: 'LLM', database: 'DATABASE',
  graph: 'GRAPH', external_data: 'EXTERNAL DATA',
}

export function ProviderReadiness({ providers }: { providers: Record<string, ProviderReadinessState> }) {
  return <div className="provider-readiness" aria-label="Provider readiness">
    {Object.entries(labels).map(([key, label]) => {
      const provider = providers[key]
      const status = provider?.configured ? 'Ready' : provider?.blocking ? 'Required' : 'Optional'
      return <div className={`provider provider--${status.toLowerCase()}`} key={key}>
        <strong>{label}</strong><span>{status}</span>
      </div>
    })}
  </div>
}
