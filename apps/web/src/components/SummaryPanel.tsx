import type { CallSummary } from '../types/contracts'

export function SummaryPanel({ summary }: { summary: CallSummary }) {
  const verified = summary.external_verified_context.map(item =>
    `${String(item.claim ?? 'Verified context')} — ${String(item.source ?? 'attributed source')} (${String(item.status ?? 'verified')})`)
  const sections: [string, string[]][] = [
    ['CUSTOMER FACTS', summary.customer_facts],
    ['SALES SIGNALS', summary.sales_signals],
    ['OBJECTIONS', summary.objections],
    ['COMMITMENTS', summary.commitments],
    ['VERIFIED EXTERNAL CONTEXT', verified],
    ['CUSTOMER CLAIMS NOT VERIFIED', summary.unverified_claims],
    ['AI INFERENCE', summary.ai_inferences],
    ['NEXT STEPS', summary.next_steps],
    ['FOLLOW-UP MEMORY', summary.follow_up_memory],
  ]
  return <section className="summary"><h2>CALL SUMMARY</h2><div className="summary-grid">
    {sections.map(([title, items]) => <section key={title}><h3>{title}</h3>
      {items.length ? <ul>{items.map(item => <li key={item}>{item}</li>)}</ul> : <p>None captured.</p>}
    </section>)}
  </div></section>
}
