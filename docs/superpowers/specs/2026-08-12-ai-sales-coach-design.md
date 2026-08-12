# AI Sales Coach Design

**Status:** Approved on 2026-08-12 by instruction to implement the supplied PRD and chat history exactly.

## Authority and scope

`AI_Sales_Coach_SSOT_PRD.md` is the implementation authority. The assessment and chat history provide rationale and examples, but cannot weaken or contradict the SSOT. The prototype is one outbound call at a time, one frontend page, and one backend service. It excludes inbound calling, IVR, multi-tenancy, autonomous voice output, Kafka, Kubernetes, and other stated non-goals.

The repository delivers the full six-phase SSOT: realtime calling and transcription; structured intelligence UX; contextual evidence; relational, vector, and temporal memory; resilience, observability, and evaluation; and the complete assessment documentation.

## Architecture

The communication plane is a browser-based Twilio Voice call from a React client to a real phone. Twilio independently forks both call tracks into a FastAPI media WebSocket. Customer audio maps from `inbound_track`; browser-agent audio maps from `outbound_track`. No intelligence-plane dependency is permitted to terminate the phone call.

The observer plane maintains independent Deepgram-compatible streaming STT connections per speaker, a 2-3 second replay buffer, media sequence checks, and final-transcript deduplication. Final utterances update a typed in-memory session and emit typed conversation events. Partial utterances update the UI without becoming durable facts.

The intelligence plane uses deterministic routing around a LangGraph workflow. The Conversation Agent structures each meaningful final utterance. The Fast Coach operates only on current structured state, recent exchanges, and cached domain rules. Knowledge, Research, Evidence, Memory, and evaluation run asynchronously. Validated knowledge or evidence may cause the Deep Coach to refine the active recommendation. The Summary Agent runs after call completion.

PostgreSQL with pgvector is the operational, episodic, and domain-knowledge store. Neo4j is accessed behind an asynchronous `TemporalGraphStore` interface and is never required in the realtime hot path. In-memory fallbacks keep the live session functioning when either data service is unavailable.

## Provider strategy

Telephony, STT, LLM, external-data, relational/vector, and graph dependencies have explicit interfaces. Production adapters target Twilio Programmable Voice, Deepgram streaming STT, an environment-selected structured-output LLM, official UK public sources where accessible, PostgreSQL/pgvector, and Neo4j Community.

Until credentials are supplied, synthetic adapters provide deterministic development and automated-test behavior through the same interfaces. Synthetic mode is visibly labeled in the UI, health responses, logs, README, and synthetic-data disclosure. It is not evidence of a real phone call, live provider latency, or provider reliability.

## Product surface

The desktop interface has a compact health header and three primary columns:

1. Call and customer profile: phone input, dial/hang-up controls, pre-call brief, facts, signals, objections, commitments, and sensitive alerts.
2. Live conversation: stable agent/customer lanes, subdued replace-in-place partials, finalized utterances, semantic highlights, and lookup/evidence markers.
3. AI coach: stage, temperature, current next-best action, reason, confidence, lifecycle state, evidence chips/cards, freshness, source links, and useful/not-useful feedback.

The current recommendation and call status have highest visual priority. Customer statements, extracted facts, externally verified context, and AI inference use distinct labels and treatments. The mobile layout preserves the same workflow in a vertical order without hiding required status or controls.

## Core data and contracts

Pydantic and TypeScript models mirror the SSOT schemas for call state, utterances, conversation state, events, recommendations, sources, evidence, summaries, health, pre-call briefs, trajectories, and UI snapshots. Every event carries `event_id`, `timestamp`, `trace_id`, `call_id`, and `session_id`.

The REST surface provides health/provider health, Twilio token/voice/status, call snapshot/summary, customer brief/history, recommendation feedback, evidence, a development simulation endpoint, metrics, and fault-injection controls. The media WebSocket accepts Twilio events. The UI WebSocket sends a full snapshot on connection and typed incremental events afterward.

## Failure behavior

- STT disconnect marks transcription as reconnecting, buffers audio, reconnects with bounded backoff, replays only the small buffer, and deduplicates overlap.
- LLM failure keeps transcription live, retains the last valid recommendation with a stale marker when needed, and retries without blocking later events.
- External lookup failure preserves fast coaching and surfaces `Unable to verify`; it never fabricates context.
- Database and graph failures queue or skip noncritical persistence while in-memory state continues.
- UI disconnect does not destroy backend state; reconnect begins from a full canonical snapshot.
- Logs contain identifiers and metadata by default, not raw audio, full transcripts, prompts, contact details, or sensitive values.

## Verification

Implementation follows red-green-refactor cycles for domain reducers, event routing, recommendation lifecycle, evidence ranking, caching, replay deduplication, provider degradation, API contracts, and frontend state recovery. Integration tests cover Twilio webhook generation, media-to-STT routing, transcript-to-coach flow, evidence refinement, persistence, and post-call summary. Fault tests cover all thirteen SSOT cases and assert the call remains active.

The browser workflow is verified in synthetic mode at desktop and mobile sizes. Credential-backed completion additionally requires a real Twilio call, two live speakers, Deepgram transcription, real LLM coaching, external evidence, reconnect demonstrations, persistence, follow-up brief, traces, trajectories, and the 35-step acceptance rehearsal. Until that rehearsal is run, provider-backed items remain explicitly unverified.

## Documentation

The repository includes setup and service rationale, domain research and prompt design, system design and architecture diagrams, demo script, limitations, synthetic-data policy, E2E instructions, evaluation instructions, fault-injection instructions, provenance design, follow-up memory design, and observability guidance.
