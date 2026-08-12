# E2E and Fault Testing

## Automated demo acceptance

The browser suite clicks the public **Demo** control against the synthetic FastAPI backend and asserts that the scenario reaches a structured call summary containing the expected budget and Saturday viewing commitment. A browser-level `getUserMedia` trap also proves this path never requests microphone access.

For a fast local run:

```powershell
npm --workspace apps/web run e2e -- --project=desktop --grep "one click"
```

Run the commands in README. Playwright checks the accepted 1536x1024 desktop surface and Pixel 7 responsive surface with no horizontal overflow. `scripts/fault_injection.py` behaviorally exercises all 13 PRD fault cases; each must leave call status connected. Backend integration tests cover speaker mapping, partial/final transcript flow, fast-before-lookup ordering, RAG/evidence refinement, reconnect snapshots, duplicate completion idempotency and two-call memory. The final real rehearsal follows all 35 SSOT acceptance steps and records actual carrier/STT/LLM latencies.
