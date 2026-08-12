# Limitations

- Credential-backed Twilio, Deepgram, LLM, PostgreSQL/pgvector and Neo4j acceptance remains pending until every required credential, public HTTPS/WSS and reachable durable services are supplied.
- Synthetic mode verifies product contracts and failure behavior, not carrier audio, real speaker accuracy or latency SLOs.
- Twilio trial calls only verified destinations. Browser microphone/background behavior depends on supported browsers.
- Official external coverage is intentionally narrow; unsupported topics abstain. This avoids fabricated evidence.
- Prototype is outbound, one call, one user and UK-oriented. It has no inbound/IVR/CRM/multi-tenant production controls.
- `DATA_RETENTION_DAYS` records the bounded policy; production deployment must schedule physical deletion and audit jobs.
