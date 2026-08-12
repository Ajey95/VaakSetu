import type { PreCallBrief } from '../types/contracts'
import { AlertIcon, HangupIcon, PhoneIcon } from './Icons'

export function CallPanel({ phone, setPhone, status, error, onCall, onHangup, customer, signals,
  objections, commitments, sensitive, preCallBrief, onDemo, demoStatus = 'idle', demoProgress = '' }: any & { preCallBrief?: PreCallBrief | null }) {
  const fact = (key: string) => customer?.[key]?.value
  const demoRunning = demoStatus === 'running'
  const callActive = ['dialing', 'ringing', 'connected'].includes(status)
  return <aside className="panel panel--profile"><h2>CALL &amp; PROFILE</h2><div className="dialer">
    <label className="sr-only" htmlFor="phone">Phone number</label><input id="phone" value={phone} onChange={e => setPhone(e.target.value)} placeholder="+44 7700 900123"/>
    <button className="button button--call" onClick={onCall} disabled={callActive || demoRunning}><PhoneIcon/>Call</button>
    <button className="button button--demo" onClick={onDemo} disabled={callActive || demoRunning} aria-label={demoRunning ? 'Demo running' : 'Start automated demo'}>{demoRunning ? 'Running…' : 'Demo'}</button>
    <button className="button button--hangup" onClick={onHangup} disabled={status !== 'connected' && !demoRunning}><HangupIcon/>{demoRunning ? 'Cancel demo' : 'Hang up'}</button></div>
    {demoProgress && <p role="status" aria-live="polite" className={`demo-progress demo-progress--${demoStatus}`}>{demoProgress}</p>}
    {error && <p role="alert" className="form-error">{error}</p>}
    <div className="duration"><span className="health__dot"/>STATUS <strong>{String(status).toUpperCase()}</strong></div>
    {preCallBrief?.source_call_id && <Section title="PREVIOUS CALL"><p className="brief-copy">{preCallBrief.suggested_opening}</p>
      <List items={[...(preCallBrief.known ?? []), ...(preCallBrief.last_commitment ?? [])].map(detail => ({ type: detail, detail }))} fallback="No prior context"/></Section>}
    <Section title="CUSTOMER FACTS"><Fact label="Budget" value={fact('budget') ? `£${Number(fact('budget')).toLocaleString('en-GB')}` : '—'}/>
      <Fact label="Mortgage" value={fact('mortgage_approval') === 'approved' ? 'Approved' : '—'} live/>
      <Fact label="Location" value={customer?.location_preferences?.[0]?.value ?? '—'}/><Fact label="Bedrooms" value={fact('bedrooms') ?? '—'}/>
      <Fact label="Timeline" value={fact('timeline') ?? '—'} live/></Section>
    <Section title="SIGNALS"><List items={signals} fallback="Listening for intent"/></Section>
    <Section title="OBJECTIONS"><List items={objections} fallback="No active objection" warning/></Section>
    <Section title="COMMITMENTS"><List items={commitments} fallback="No commitment yet"/></Section>
    {sensitive?.length > 0 && <div className="sensitive"><div><AlertIcon/><strong>SENSITIVE</strong></div><p>Use only for relevant qualification. Never use protected or personal circumstances for prioritization.</p></div>}
  </aside>
}
const Section = ({ title, children }: any) => <section className="profile-section"><h3>{title}</h3>{children}</section>
const Fact = ({ label, value, live }: any) => <div className="fact"><span>{label}</span><strong className={live ? 'live-text' : ''}>{value}</strong></div>
const List = ({ items = [], fallback, warning }: any) => <ul className="signal-list">{items.length ? items.map((item: any, i: number) => <li key={`${item.type}-${i}`}><span className={warning ? 'dot dot--warning' : 'dot'}/>{item.evidence ?? item.detail ?? String(item.type).replaceAll('_', ' ')}</li>) : <li className="muted">{fallback}</li>}</ul>
