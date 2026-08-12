# SSOT Requirement Matrix

Status is evidence-based. `Automated` means credential-independent code paths are exercised; it does not claim carrier or provider behavior. `Live pending` is intentionally excluded from the current completion scope.

| SSOT area | Status | Evidence |
|---|---|---|
| Browser dial/hangup, call state, summary | Automated | React tests, Playwright, API integration tests |
| Real Twilio phone connection and two-human interruption | Live pending | Requires public HTTPS/WSS, TwiML App, verified destination and rehearsal |
| Speaker-separated streaming and reconnect contracts | Automated | Both Twilio tracks, partial/final handling, replay buffer, dedup and reconnect tests |
| Structured facts, signals, objections, commitments, stage, temperature, sentiment | Automated | Reducer and media-to-coach integration tests |
| Fast recommendation independent of research | Automated | Ordering, cooldown and external-failure integration tests |
| Deep coach, official/synthetic research and evidence provenance | Automated | Evidence/refinement, cache/provenance and failure tests |
| Event-triggered knowledge RAG | Automated | Knowledge indexing/vector retrieval and live knowledge refinement tests |
| Recommendation visible/refined/stale/accepted/rejected lifecycle | Automated | Backend feedback and frontend authoritative-state tests |
| PostgreSQL, pgvector and Neo4j implementations | Implemented/contract-tested | Adapter selection, schema/migration and fault-isolation tests; reachable-service acceptance is live/infrastructure pending |
| First-call memory and follow-up pre-call brief | Automated | Canonical create/reconnect two-call integration test |
| Telephony/intelligence fault isolation | Automated | 13/13 behavioral scenarios leave call connected |
| Structured logs, trace correlation, metrics and trajectories | Automated | Observability integration tests and `/metrics` contract |
| Offline/online evaluations and feedback | Automated | 28/28 offline dataset; queued async online eval tests |
| Provider readiness visibility | Automated | Health endpoint and frontend readiness component tests |
| Security/privacy baseline | Automated/documented | Signature validation, phone hashing, safe-log tests, no audio retention, bounded retention setting |
| Required assessment documents and runbooks | Complete | README, domain/prompt, system design, architecture, demo, limitations, E2E, provenance/memory, observability and synthetic disclosure |

The repository must not be described as having passed the exact 35-step final acceptance test until the `Live pending` row is rehearsed successfully. All other SSOT Definition-of-Done areas have an implementation and automated or documented evidence path.
