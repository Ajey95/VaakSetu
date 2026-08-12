# AI Sales Coach

Provider-ready implementation of the Quantum Gandiva AI realtime real-estate sales-coaching assessment. The browser places an outbound Twilio call, Twilio Media Streams forks both tracks, Deepgram transcribes each speaker independently, and deterministic/LangGraph intelligence produces live and evidence-refined coaching. PostgreSQL/pgvector and Neo4j preserve follow-up memory outside the call hot path.

## Run locally

Requirements: Node 20+, `uv`, Docker, and provider credentials for real mode.

```powershell
Copy-Item .env.example .env
npm install
uv sync --project apps/api
docker compose up -d
# For an existing database volume, apply the idempotent schema once:
Get-Content apps/api/app/db/migrations/001_initial.sql -Raw | docker compose exec -T postgres psql -U salescoach -d salescoach
uv run --project apps/api uvicorn app.main:app --app-dir apps/api --reload --port 8000
npm --workspace apps/web run dev
```

Open `http://localhost:5173`. Default `APP_MODE=synthetic` is visibly labeled and is for deterministic development only. For live mode, populate the Twilio, Deepgram, LLM, PostgreSQL and Neo4j variables in `.env`, expose port 8000 through HTTPS/WSS, set `PUBLIC_BASE_URL`, configure the TwiML App Voice URL as `/twilio/voice`, verify the destination number on a Twilio trial, and set `APP_MODE=real` plus `EXTERNAL_DATA_MODE=real`. The included official UK source adapter does not require `GENERAL_SEARCH_API_KEY`; that variable is reserved for an optional general-search adapter.

## Service choices

- Twilio Voice JS + Programmable Voice + unidirectional Media Streams: mandated telephony and native separate tracks.
- Deepgram Nova-class streaming: low-latency interim/final output, mu-law support, keepalive and reconnect.
- Environment-selected structured-output LLM: no model name in business logic.
- FastAPI/Python 3.12 and React/TypeScript/Vite: pragmatic async backend and one-page browser workspace.
- PostgreSQL/pgvector: operational plus semantic memory in one store. Neo4j: asynchronous temporal relationships only.
- OpenTelemetry, Prometheus metrics and safe JSON logs; LangSmith optional.

## Verification

```powershell
uv run --project apps/api pytest apps/api/tests -q
npm --workspace apps/web test -- --run
npm --workspace apps/web run typecheck
npm --workspace apps/web run build
npm --workspace apps/web run e2e
uv run --project apps/api python scripts/run_evals.py
uv run --project apps/api python scripts/fault_injection.py
```

See [domain research](docs/DOMAIN_RESEARCH_AND_PROMPT_DESIGN.md), [system design](docs/SYSTEM_DESIGN.md), [demo script](docs/DEMO_SCRIPT.md), [limitations](docs/LIMITATIONS.md), and [synthetic disclosure](docs/SYNTHETIC_DATA.md).

## Known limits

Real calls and provider latency cannot be certified without credentials and a public HTTPS/WSS endpoint. Trial calls reach only verified numbers. The real external adapter currently implements an official UK market-source boundary and abstains for unsupported topics; add official provider adapters before claiming those topics verified. Audio is not stored. This is one-call, outbound-only prototype scope.
