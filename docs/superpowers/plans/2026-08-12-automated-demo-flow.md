# Automated End-to-End Demo Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a one-click, visibly synthetic demo that drives a complete buyer conversation through the existing backend and finishes on the real structured summary UI.

**Architecture:** A focused `demoFlow.ts` runner owns immutable turns, sequential API orchestration, timing, progress, cancellation, snapshot refresh, and canonical completion. `App` integrates runner state through the existing reducer, while `CallPanel` remains presentational. The backend API is reused unchanged.

**Tech Stack:** React 19, TypeScript 5.9, Vite 8, Vitest 4, Testing Library, Playwright, FastAPI synthetic REST contracts.

## Global Constraints

- Demo is explicitly synthetic and must never place a phone call or request microphone access.
- All visible transcript/state/coaching/summary data must pass through existing backend APIs.
- Scripted utterances run sequentially; default production delay is 1,000 ms and tests inject zero delay.
- Double-start is prevented; Call and Demo are disabled while demo is active.
- Cancellation stops remaining turns and calls canonical end at most once.
- Errors are user-readable and never expose credentials, provider payloads, or stack traces.
- Desktop and Pixel 7 layouts must not horizontally overflow.
- The production site remains in real-provider mode while Demo remains explicitly synthetic.

---

### Task 1: Deterministic demo runner

**Files:**
- Create: `apps/web/src/lib/demoFlow.ts`
- Create: `apps/web/src/lib/demoFlow.test.ts`
- Modify: `apps/web/src/lib/api.ts`

**Interfaces:**
- Consumes: `SessionSnapshot`, `Speaker`, and API functions `startDemo`, `utterance`, `snapshot`, `endCall`.
- Produces: `DEMO_TURNS`, `DemoApi`, `DemoProgress`, `runAutomatedDemo(options): Promise<SessionSnapshot>`.

- [ ] **Step 1: Write failing runner tests**

Test an injected fake API and zero-delay runner. Assert one call creation, six utterances in exact speaker/text order, progress/snapshot delivery, one canonical completion, returned summary, cancellation stopping later turns, and turn failure stopping the sequence.

- [ ] **Step 2: Run runner tests and verify RED**

Run: `npm --workspace apps/web test -- --run src/lib/demoFlow.test.ts`

Expected: FAIL because `demoFlow.ts` does not exist.

- [ ] **Step 3: Implement minimal runner**

Create the six immutable turns from the approved spec. Implement abort-aware delay, one sequential loop, best-effort snapshots, progress callback, and one `endCall` in success/cancel/failure cleanup. Add explicit `Promise<SessionSnapshot>` typing to `api.utterance`.

- [ ] **Step 4: Run runner tests and verify GREEN**

Run: `npm --workspace apps/web test -- --run src/lib/demoFlow.test.ts`

Expected: all runner tests pass.

- [ ] **Step 5: Commit runner**

```powershell
git add apps/web/src/lib/demoFlow.ts apps/web/src/lib/demoFlow.test.ts apps/web/src/lib/api.ts
git commit -m "feat: add deterministic automated demo runner"
```

### Task 2: Demo controls and React state integration

**Files:**
- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/App.test.tsx`
- Modify: `apps/web/src/components/CallPanel.tsx`
- Modify: `apps/web/src/styles.css`

**Interfaces:**
- Consumes: `runAutomatedDemo`, `DemoProgress`, existing `api`, `sessionReducer`.
- Produces: `Demo` button, `Running demo…` state, synthetic-demo status/error copy, cancellation through Hang up, and reducer-driven progressive UI updates.

- [ ] **Step 1: Write failing UI tests**

Add component tests asserting `Demo` is visible, starting the demo never calls `navigator.mediaDevices.getUserMedia`, running disables Call and Demo, progress is accessible, and completion dispatches the returned summary. Inject or mock only the API boundary and timer delay.

- [ ] **Step 2: Run component tests and verify RED**

Run: `npm --workspace apps/web test -- --run src/App.test.tsx`

Expected: FAIL because no Demo control exists.

- [ ] **Step 3: Implement minimal integration**

In `App`, add `demoStatus`, progress text, an `AbortController`, cleanup on unmount, `startAutomatedDemo`, and cancellation in `hangup`. Dispatch each runner snapshot through `session.snapshot`. In `CallPanel`, add semantic Demo/running controls and explicit synthetic progress. Update the dialer to a three-control grid that remains responsive.

- [ ] **Step 4: Run component and unit suites**

Run: `npm --workspace apps/web test -- --run`

Expected: all frontend unit/component tests pass.

- [ ] **Step 5: Commit UI integration**

```powershell
git add apps/web/src/App.tsx apps/web/src/App.test.tsx apps/web/src/components/CallPanel.tsx apps/web/src/styles.css
git commit -m "feat: add one-click automated demo controls"
```

### Task 3: Browser acceptance, complete verification, and deployment

**Files:**
- Modify: `apps/web/e2e/synthetic-call.spec.ts`
- Modify if required: `README.md`

**Interfaces:**
- Consumes: deployed/local frontend and existing local backend on port 8000.
- Produces: browser acceptance proving one click reaches transcript/coaching/summary without microphone access or overflow.

- [ ] **Step 1: Write failing Playwright demo test**

Mock only the backend HTTP routes or run against the local backend with test timing. Click `Demo`, assert progressive transcript/coaching, wait for `CALL SUMMARY`, assert category headings, and verify no horizontal overflow on desktop/mobile.

- [ ] **Step 2: Run Playwright test and verify RED**

Run: `npm --workspace apps/web run e2e`

Expected: new demo scenario fails until UI integration is complete or test API timing is configured.

- [ ] **Step 3: Complete browser wiring/documentation**

Add test-only zero-delay configuration through an environment variable or query parameter that affects demo delay only. Add a short README feature note explaining that Demo is synthetic and does not make a call.

- [ ] **Step 4: Run complete verification**

```powershell
npm --workspace apps/web test -- --run
npm --workspace apps/web run typecheck
npm run build
npm --workspace apps/web run e2e
uv run --project apps/api pytest apps/api/tests -q
```

Expected: frontend unit/component, typecheck, production build, Playwright, and 110 backend tests pass. Run backend tests from `apps/api` if root `.env` affects default readiness expectations.

- [ ] **Step 5: Commit and push final acceptance**

```powershell
git add apps/web/e2e/synthetic-call.spec.ts README.md
git commit -m "test: cover automated demo end to end"
git push origin HEAD:main
```

- [ ] **Step 6: Verify Vercel production**

Wait for the Git-triggered deployment to report Ready. Open `https://vaaksetu-psi.vercel.app`, assert real-provider mode, click Demo, confirm no microphone prompt, observe progressive transcript/coaching, and confirm the summary. Check browser console for errors and preserve the production tab for user handoff.
