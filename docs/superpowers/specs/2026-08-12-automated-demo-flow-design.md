# Automated End-to-End Demo Flow Design

**Date:** 2026-08-12  
**Status:** Approved design, ready for implementation planning

## 1. Objective

Add a `Demo` control to the AI Sales Coach workspace that runs a complete, deterministic product walkthrough without placing a real phone call or requesting microphone access. The walkthrough must use the existing synthetic backend APIs so transcript processing, conversation state, coaching, evidence, memory, and summary remain real application behavior rather than a client-only animation.

The demo exists for reviewers who need to understand the full product in one click even when Twilio, browser microphone permission, a verified destination, or a live conversation partner is unavailable.

## 2. User experience

The call panel will contain three controls:

- `Call`: existing real/synthetic call behavior;
- `Demo`: start the automated demonstration;
- `Hang up`: existing call termination behavior.

Clicking `Demo` will:

1. clear prior transient errors;
2. visibly identify the run as an automated synthetic demonstration;
3. create a synthetic call for a stable demo customer;
4. connect the UI to the returned session snapshot;
5. submit a scripted sequence of agent and customer utterances at readable intervals;
6. let the backend update transcript, state, triggers, Fast Coach, retrieval, evidence, and Deep Coach;
7. refresh the authoritative snapshot after each turn so the walkthrough remains understandable even if WebSocket delivery is delayed;
8. end the call through the canonical endpoint;
9. display the structured post-call summary.

The `Demo` button will be disabled while a demo is running or while a real call is active. `Call` will be disabled during an automated demo. The running control will display a progress-oriented label such as `Running demo…`. The user can use `Hang up` to cancel a running demo; cancellation must stop remaining scripted turns before ending the synthetic session.

The demo must never invoke `getUserMedia`, instantiate the Twilio client, or dial a phone number.

## 3. Scripted scenario

The walkthrough will use a concise UK buyer scenario that exercises the assessment's visible capabilities:

| Turn | Speaker | Script purpose |
|---:|---|---|
| 1 | Agent | Open with qualification: desired property and location |
| 2 | Customer | State Manchester location, two bedrooms, £450,000 budget, approved mortgage, and six-week timeline |
| 3 | Agent | Acknowledge the buying position and ask what is blocking progression |
| 4 | Customer | Raise a price objection and claim local prices fell 10% |
| 5 | Agent | Acknowledge the concern and ask for a concrete viewing commitment |
| 6 | Customer | Commit to a Saturday viewing |

This sequence must demonstrate:

- separate agent/customer transcript lanes;
- customer facts and sensitive financial context;
- intent signals;
- objection detection;
- stage, temperature, and sentiment changes;
- an immediate conversation-grounded recommendation;
- contextual external lookup for the market claim;
- evidence/provenance and optional refined coaching;
- a viewing commitment;
- a category-separated final summary and follow-up memory.

The wording must remain fixture-safe. Any external result is produced by the backend's configured synthetic/official adapter and must preserve the existing provenance and abstention rules.

## 4. Architecture and boundaries

### 4.1 Frontend demo runner

A focused demo module will own:

- the immutable scenario definition;
- per-turn delay;
- sequential utterance submission;
- cancellation via `AbortSignal` or equivalent explicit cancellation state;
- authoritative snapshot refresh;
- canonical call completion.

The module will receive an API-like dependency so it can be tested without a browser or timer-heavy component test. It will expose progress callbacks rather than mutating React state directly.

### 4.2 React integration

`App` will own whether a demo is idle, running, completed, cancelled, or failed. It will dispatch snapshots returned by the runner through the existing `sessionReducer`. This preserves one authoritative state path for manual calls, WebSocket updates, and automated demo updates.

`CallPanel` will receive `onDemo` and demo status props. It remains a presentation component and does not know the scenario or API sequencing.

### 4.3 Backend reuse

No new backend route is required. The runner will use:

- `POST /demo/calls`;
- `POST /demo/calls/{call_id}/utterances`;
- `GET /calls/{call_id}` where an authoritative refresh is useful;
- `POST /calls/{call_id}/end`.

This decision keeps the demo honest: every transcript/state/coaching/summary transition passes through the same application service as existing synthetic integration tests.

## 5. Timing and determinism

Production demo timing will default to approximately 900–1,200 ms between turns so changes can be followed visually without making the walkthrough lengthy. Timing will be injectable or configurable in tests; automated tests will use zero delay.

Utterances are submitted sequentially. A later turn cannot begin before the prior API request resolves. This guarantees ordering and prevents concurrent reducer updates from making the walkthrough nondeterministic.

If asynchronous deep refinement is still running after the final scripted utterance, the runner will perform one bounded snapshot refresh window before ending the call. The demo will not wait indefinitely for external research.

## 6. Error and cancellation behavior

- Call creation failure: show `Unable to start automated demo`; return to idle controls.
- Turn failure: stop submitting later turns, surface the failing step, and attempt canonical call completion if a call exists.
- Snapshot refresh failure: keep the last valid snapshot and continue when the utterance submission itself succeeded.
- Summary/end failure: show a recoverable error and leave the last call state visible.
- User cancellation: stop scheduled/remaining turns and end the current synthetic call once.
- Component unmount/navigation: cancel the runner and prevent state updates after unmount.
- Double click: ignored through disabled/running state and runner guard.

All errors must be user-readable and must not expose credentials, raw provider payloads, or stack traces.

## 7. Accessibility and responsive behavior

- The control must have the accessible name `Demo` when idle.
- Running state must expose an understandable label, not animation alone.
- Disabled states must be semantic HTML `disabled` states.
- Existing keyboard access and focus behavior must remain intact.
- The three-control dialer must fit the existing desktop and Pixel 7 layouts with no horizontal overflow.
- Synthetic status must be explicit throughout the demo; the walkthrough must not be mistaken for a real phone call.

## 8. Testing strategy

Implementation will follow red-green-refactor.

### 8.1 Unit tests

The demo runner tests will prove:

- it creates one synthetic call;
- it submits every scripted utterance in order with correct speaker attribution;
- it refreshes progress/snapshots;
- it ends the call once and returns the final summary snapshot;
- cancellation prevents remaining utterances;
- a failed utterance stops the sequence and reports a useful error.

### 8.2 Component tests

The call panel/app tests will prove:

- a `Demo` button is visible;
- running state disables Call and Demo;
- the demo path does not request microphone permission;
- progress and failure text are accessible;
- completion renders the summary.

### 8.3 Browser tests

Playwright will run the automated demo at test timing and assert:

- one click begins the scenario;
- transcript and coaching become visible;
- the run finishes on the summary;
- the layout has no desktop or mobile overflow.

The existing microphone, component, typecheck, production build, and responsive browser suites must remain green.

## 9. Acceptance criteria

The feature is accepted when all of the following are true:

1. `Demo` is visible beside the existing call controls.
2. One click runs the scenario without further input.
3. No phone call or microphone permission is used.
4. Agent and customer turns appear progressively and in order.
5. Facts, signals, objection, stage, temperature/sentiment, and coaching visibly update.
6. The market claim triggers evidence-aware behavior without blocking earlier coaching.
7. The walkthrough finishes with a structured summary.
8. Re-entry and double-start are prevented while running.
9. Cancellation and API failure leave the UI recoverable.
10. Unit, component, typecheck, build, and Playwright verification pass.
11. The production Vercel deployment is in real-provider mode while the Demo action remains explicitly synthetic.

## 10. Out of scope

- placing a prerecorded audio call;
- browser speech synthesis or audio playback;
- automatically granting microphone permission;
- faking carrier or Deepgram behavior;
- multiple selectable scenarios;
- pausing/resuming or scrubbing the script;
- changing existing live-call telephony or backend provider contracts.
