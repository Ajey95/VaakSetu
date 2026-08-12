# AI Sales Coach Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete provider-ready, realtime AI Sales Coach specified by the SSOT, with an honest deterministic synthetic mode until external credentials are supplied.

**Architecture:** A React/TypeScript/Vite single-page client uses Twilio Voice for the human call and a reconnecting application WebSocket for intelligence updates. A Python 3.12/FastAPI service separates telephony from an event-driven observer plane, routes two media tracks through provider abstractions, runs fast and deep LangGraph intelligence, and persists operational/vector/temporal memory without putting those dependencies in the call path.

**Tech Stack:** React 19, TypeScript, Vite 8, Twilio Voice JS SDK 2.18, Vitest 4, Playwright 1.62, Python 3.12, FastAPI, Pydantic 2, SQLAlchemy 2, PostgreSQL 16 + pgvector, Neo4j 5 Community, LangGraph, OpenTelemetry, pytest.

## Global Constraints

- The SSOT at `C:/Users/srija/Downloads/AI_Sales_Coach_SSOT_PRD.md` has priority over all other project material.
- The communication plane must remain active through STT, LLM, external-tool, database, graph, frontend, observability, and evaluation failures.
- Twilio `inbound_track` maps to customer; `outbound_track` maps to browser agent.
- Fast coaching must not wait for external research, RAG, graph, database, or evaluation.
- Partial transcripts are replaceable UI state; finalized utterances are immutable durable input unless explicitly corrected.
- Customer statements, extracted facts, external verified context, and AI inference remain distinct in data and UI.
- Synthetic providers are visibly labeled and never count as real-provider acceptance evidence.
- One outbound call at a time; no inbound calls, IVR, multi-user implementation, autonomous voice, Kafka, Kubernetes, or microservice expansion.
- Raw audio, full transcripts, full prompts, contact details, and sensitive values are excluded from normal logs.

---

### Task 1: Repository, shared contracts, and executable baselines

**Files:**
- Create: `.gitignore`, `.env.example`, `docker-compose.yml`, `package.json`
- Create: `apps/api/pyproject.toml`, `apps/api/app/__init__.py`, `apps/api/app/config.py`, `apps/api/app/models/contracts.py`
- Create: `apps/web/package.json`, `apps/web/tsconfig.json`, `apps/web/vite.config.ts`, `apps/web/index.html`, `apps/web/src/types/contracts.ts`
- Test: `apps/api/tests/unit/test_config.py`, `apps/api/tests/unit/test_contracts.py`, `apps/web/src/types/contracts.test.ts`

**Interfaces:**
- Produces Python `Settings`, `CallStatus`, `Speaker`, `HealthState`, `Utterance`, `ConversationState`, `Recommendation`, `Evidence`, `CallSummary`, `SessionSnapshot`, and `AppEvent` models.
- Produces matching TypeScript discriminated unions and interfaces consumed by every frontend feature.

- [ ] Write failing Python tests proving missing real-mode credentials are reported without preventing synthetic startup, phone numbers are normalized/validated, and event envelopes require correlation IDs.
- [ ] Run `uv run --project apps/api pytest apps/api/tests/unit/test_config.py apps/api/tests/unit/test_contracts.py -q`; expect collection/import failure because the application modules do not exist.
- [ ] Add the workspace manifests, environment schema, Pydantic contracts, and matching TypeScript contracts. Configure `APP_MODE=synthetic|real`, strict CORS origins, provider settings, safe defaults, and no frontend secrets.
- [ ] Run the Python tests and `npm install`; expect all Task 1 Python tests to pass and lockfiles to be generated.
- [ ] Write the TypeScript contract test around a literal `coach.fast.ready` event and snapshot reduction input; run `npm --workspace apps/web test -- --run`; expect failure until the exported narrowing helpers exist.
- [ ] Add narrowing helpers and rerun both suites plus `git diff --check`; expect zero failures.
- [ ] Commit with `git commit -m "chore: scaffold typed sales coach workspace"`.

### Task 2: Session state, transcript semantics, and deterministic conversation intelligence

**Files:**
- Create: `apps/api/app/sessions/store.py`, `apps/api/app/conversation/reducer.py`, `apps/api/app/conversation/triggers.py`, `apps/api/app/conversation/deduplication.py`
- Create: `apps/api/app/agents/conversation_agent.py`, `apps/api/app/agents/fast_coach.py`, `apps/api/app/agents/summary_agent.py`
- Test: `apps/api/tests/unit/test_session_store.py`, `test_reducer.py`, `test_triggers.py`, `test_deduplication.py`, `test_fast_coach.py`, `test_summary.py`

**Interfaces:**
- Produces `InMemorySessionStore.create/get/update/delete/snapshot`.
- Produces `apply_final_utterance(state, utterance) -> ConversationUpdate`, `detect_triggers(update) -> list[ConversationTrigger]`, `deduplicate_final(existing, candidate) -> bool`, `FastCoach.recommend(...) -> Recommendation`, and `SummaryAgent.summarize(...) -> CallSummary`.

- [ ] Write table-driven failing tests for buyer/vendor stage changes, price/fee objections, budget/mortgage/location/bedroom/timeline extraction, commitments, sensitive items, external claims, and recommendation invalidation.
- [ ] Run those files; expect import failures for the missing reducer and trigger modules.
- [ ] Implement deterministic reducers and triggers using compiled patterns plus explicit provenance. Ensure partial utterances cannot mutate durable state.
- [ ] Run the reducer and trigger tests; expect pass.
- [ ] Write failing behavior tests for same-track replay overlap, cross-track text preservation, recommendation specificity, cooldown, stale transitions, structured summary attribution, and session snapshot replacement.
- [ ] Implement deduplication, session locking, rule-backed fast coaching, and category-preserving summary generation; rerun all Task 2 and Task 1 tests.
- [ ] Commit with `git commit -m "feat: add realtime conversation state engine"`.

### Task 3: Telephony, media sequencing, and streaming STT adapters

**Files:**
- Create: `apps/api/app/telephony/twilio_service.py`, `apps/api/app/streaming/media.py`, `apps/api/app/streaming/buffer.py`
- Create: `apps/api/app/stt/base.py`, `apps/api/app/stt/deepgram.py`, `apps/api/app/stt/synthetic.py`, `apps/api/app/stt/manager.py`
- Test: `apps/api/tests/unit/test_twilio_service.py`, `test_media.py`, `test_audio_buffer.py`, `test_stt_manager.py`
- Test fixture: `apps/api/tests/fixtures/twilio_media.jsonl`

**Interfaces:**
- Produces Twilio access-token and outbound TwiML generation, `map_twilio_track(track) -> Speaker`, `MediaSequencer.accept(packet) -> PacketDecision`, `AudioReplayBuffer`, and async `STTProvider` lifecycle methods.
- `STTManager` owns one logical connection and replay buffer per speaker and emits partial/final events without controlling the call.

- [ ] Write failing contract tests asserting TwiML dials only the validated destination, starts a unidirectional `both_tracks` stream over `wss`, registers status callbacks, and never exposes secrets.
- [ ] Implement Twilio service methods and run tests; expect pass with SDK calls isolated behind the service boundary.
- [ ] Write failing tests for track mapping, missing/out-of-order/duplicate sequence decisions, 2-3 second buffer eviction, reconnect state, replay, and final deduplication.
- [ ] Implement media sequencing, bounded buffers, base/synthetic/Deepgram adapters, keepalive, bounded reconnect, and manager degradation events.
- [ ] Run Task 3 tests and the full backend unit suite; expect zero failures.
- [ ] Commit with `git commit -m "feat: add isolated telephony and streaming transcription"`.

### Task 4: Agent graph, contextual retrieval, evidence, and recommendation refinement

**Files:**
- Create: `apps/api/app/agents/graph.py`, `knowledge_agent.py`, `research_agent.py`, `evidence_agent.py`, `deep_coach.py`
- Create: `apps/api/app/llm/base.py`, `apps/api/app/llm/structured.py`, `apps/api/app/llm/synthetic.py`
- Create: `apps/api/app/tools/base.py`, `official_uk.py`, `synthetic.py`, `router.py`, `cache.py`
- Create: `apps/api/app/rag/service.py`, `knowledge/buyer/playbook.md`, `knowledge/vendor/playbook.md`, `knowledge/objections/playbook.md`, `knowledge/progression/playbook.md`, `knowledge/compliance/safety.md`
- Test: `apps/api/tests/unit/test_router.py`, `test_cache.py`, `test_evidence.py`, `test_graph.py`, `test_llm_provider.py`

**Interfaces:**
- Produces deterministic `route_event`, typed `ExternalTool.search`, freshness-aware `ContextCache`, `EvidenceAgent.evaluate`, and compiled LangGraph fast/deep orchestration.
- Produces a provider-neutral structured LLM call with bounded retry and deterministic synthetic output.

- [ ] Write failing routing tests for market, environment, mortgage/rates, EPC, property, policy, and no-lookup events; include unnecessary-lookup rejection.
- [ ] Implement the router and cache TTL policies; run tests.
- [ ] Write failing evidence tests for source-tier preference, supported/partial/conflicting/unverified outcomes, freshness, unsafe surfacing, and provenance preservation.
- [ ] Implement official-source-compatible and synthetic tool contracts, evidence evaluation, RAG service, and domain documents; run tests.
- [ ] Write failing graph tests proving fast output precedes research, research failure yields unverified evidence, validated evidence refines rather than erases the fast recommendation, and malformed LLM output degrades safely.
- [ ] Implement the LLM providers and deterministic LangGraph; run all backend tests.
- [ ] Commit with `git commit -m "feat: orchestrate evidence-backed fast and deep coaching"`.

### Task 5: PostgreSQL/pgvector persistence, temporal graph, memory, and evaluation records

**Files:**
- Create: `apps/api/app/db/base.py`, `models.py`, `repository.py`, `migrations/001_initial.sql`
- Create: `apps/api/app/memory/relational.py`, `vector.py`, `temporal_graph.py`, `service.py`
- Create: `apps/api/app/agents/memory_agent.py`, `apps/api/app/evals/service.py`, `apps/api/app/observability/trajectory.py`
- Test: `apps/api/tests/unit/test_memory_service.py`, `test_temporal_graph.py`, `test_trajectory.py`
- Test: `apps/api/tests/integration/test_persistence_flow.py`

**Interfaces:**
- Produces repositories for the minimum SSOT tables, vector knowledge/episodic retrieval, `TemporalGraphStore`, async durable-memory queue, pre-call brief assembly, recommendation feedback, eval records, and trajectories.

- [ ] Write failing unit tests proving graph writes are asynchronous, changing facts preserve valid-time history, absent graph/database dependencies do not alter live state, and a known customer receives an attributable pre-call brief.
- [ ] Implement memory interfaces, in-memory fallbacks, PostgreSQL/pgvector and Neo4j adapters, then run unit tests.
- [ ] Write a failing integration test that ends a synthetic call, persists its summary/facts/commitments, and retrieves a follow-up brief without placing graph access in the fast path.
- [ ] Implement repositories, migration, memory agent, eval/feedback persistence, and trajectory records; run unit and integration tests using Docker services when available and in-memory adapters otherwise.
- [ ] Commit with `git commit -m "feat: persist episodic vector and temporal call memory"`.

### Task 6: FastAPI REST/WebSocket surface and end-to-end backend flow

**Files:**
- Create: `apps/api/app/api/routes.py`, `apps/api/app/websocket/media.py`, `apps/api/app/websocket/ui.py`, `apps/api/app/services/call_service.py`, `apps/api/app/main.py`
- Test: `apps/api/tests/integration/test_api.py`, `test_media_to_coach.py`, `test_fault_isolation.py`

**Interfaces:**
- Produces every REST and WebSocket capability in SSOT section 31 plus synthetic demo, metrics, and safe fault controls.
- `CallService` is the sole coordinator for call lifecycle, session updates, UI publication, async intelligence, persistence, and summaries.

- [ ] Write failing API tests for health/provider labels, token behavior by mode, TwiML/status transitions, snapshot/summary, pre-call brief/history, evidence, feedback, and request validation.
- [ ] Implement dependency-injected routes and application lifespan; run API tests.
- [ ] Write failing WebSocket integration tests that feed both Twilio tracks and assert stable speaker labels, replaceable partials, finalized state extraction, fast recommendation, async evidence/deep refinement, and reconnect snapshot recovery.
- [ ] Implement media/UI sockets, subscriber cleanup, bounded task isolation, and synthetic scenario driver; run integration tests.
- [ ] Write and run thirteen fault cases from SSOT section 44.3; each must assert call state remains connected until an explicit hang-up.
- [ ] Commit with `git commit -m "feat: expose resilient realtime call intelligence API"`.

### Task 7: Production-grade single-page agent workspace

**Files:**
- Create: `apps/web/src/main.tsx`, `App.tsx`, `styles.css`, `test/setup.ts`
- Create: `apps/web/src/lib/api.ts`, `twilio.ts`, `sessionReducer.ts`, `format.ts`
- Create: `apps/web/src/hooks/useCall.ts`, `useSessionSocket.ts`
- Create: `apps/web/src/components/HealthBar.tsx`, `CallPanel.tsx`, `ProfilePanel.tsx`, `TranscriptPanel.tsx`, `CoachPanel.tsx`, `EvidenceCard.tsx`, `SummaryPanel.tsx`, `ModeBanner.tsx`
- Test: matching `*.test.tsx` files and `apps/web/e2e/synthetic-call.spec.ts`

**Interfaces:**
- Produces an accessible one-page UI with real Twilio device lifecycle, reconnecting session state, synthetic driver controls only in synthetic mode, and all required semantic categories.

- [ ] Write failing reducer/hook tests for full snapshot replacement, event deduplication, reconnect backoff, stale recommendation, partial replacement, and final transcript stability.
- [ ] Implement API/Twilio clients, reducer, hooks, and run Vitest.
- [ ] Write failing component tests for dial/hang-up validation, call states, health/degraded states, speaker lanes, highlights, facts/signals/objections/sensitive items, coaching priority, source/freshness, feedback, pre-call brief, and attributed summary.
- [ ] Implement focused components and exact responsive visual hierarchy; use semantic HTML, explicit typography, visible focus, reduced motion, and no unapproved dense chrome.
- [ ] Run Vitest, TypeScript checking, and production build; expect zero errors.
- [ ] Write Playwright synthetic-call flow for dial, connect, two speakers, objection, fast coach, lookup, evidence, refined coach, hang-up, summary, reconnect, and mobile overflow.
- [ ] Run the E2E test at desktop and mobile widths; correct visible/interaction drift and rerun.
- [ ] Commit with `git commit -m "feat: build live sales coaching workspace"`.

### Task 8: Observability, offline evaluation, fault tools, and submission corpus

**Files:**
- Create: `apps/api/app/observability/logging.py`, `tracing.py`, `metrics.py`
- Create: `evals/datasets/scenarios.jsonl`, `scripts/run_evals.py`, `scripts/fault_injection.py`, `scripts/seed_demo.py`, `scripts/ingest_knowledge.py`
- Create: `README.md`, `docs/DOMAIN_RESEARCH_AND_PROMPT_DESIGN.md`, `SYSTEM_DESIGN.md`, `ARCHITECTURE.md`, `DEMO_SCRIPT.md`, `LIMITATIONS.md`, `SYNTHETIC_DATA.md`, `E2E_TESTING.md`, `OBSERVABILITY.md`
- Test: `apps/api/tests/unit/test_safe_logging.py`, `test_evals.py`, `apps/api/tests/integration/test_observability.py`

**Interfaces:**
- Produces correlated JSON logs, OpenTelemetry spans/metrics, at least 25 literal eval scenarios, executable eval/fault/demo scripts, and every assessment document.

- [ ] Write failing tests that contact details/transcript text are redacted from operational logs, all events retain trace/call/session IDs, and evaluation runs do not delay live recommendations.
- [ ] Implement logging/tracing/metrics and run tests.
- [ ] Add at least 25 hand-labeled buyer, vendor, external-context, and recovery scenarios; write failing eval tests for literal expected labels/actions and then implement scoring/reporting.
- [ ] Add executable seed, ingestion, eval, and fault scripts; run them in synthetic mode and retain generated results outside version control except the compact committed baseline report.
- [ ] Write all required assessment documents with Mermaid/text architecture diagrams, prompt templates, real/synthetic disclosure, setup, demo, limitations, provenance, memory, observability, privacy, and production evolution.
- [ ] Run document link/command checks and `git diff --check`; commit with `git commit -m "docs: complete evaluation and submission package"`.

### Task 9: Fresh whole-system verification and credential handoff

**Files:**
- Modify only files implicated by verification failures.
- Create: `docs/VERIFICATION_REPORT.md`

**Interfaces:**
- Produces reproducible evidence separating synthetic verification from credential-backed acceptance.

- [ ] Run `uv run --project apps/api pytest apps/api/tests -q` and record exact pass/fail counts.
- [ ] Run `npm --workspace apps/web test -- --run`, `npm --workspace apps/web run typecheck`, and `npm --workspace apps/web run build`.
- [ ] Start Docker dependencies and both applications from README commands; verify health endpoints and synthetic workflow.
- [ ] Run Playwright desktop and mobile E2E, capture screenshots, inspect them against the approved three-column design, and document at least five fidelity checks plus copy and overflow audits.
- [ ] Run offline eval and every fault injection; confirm intelligence failures do not end the synthetic call.
- [ ] Audit the 55 SSOT sections and 35-step final acceptance list; mark each item verified-synthetic, verified-real, or awaiting credentials with evidence.
- [ ] After credentials are supplied, run the real Twilio/Deepgram/LLM/PostgreSQL/Neo4j rehearsal and update only evidence-backed statuses.
- [ ] Commit with `git commit -m "test: document end-to-end verification evidence"`.
