# ORDER013 Deployment Unblock Implementation Plan

> **For agentic workers:** Use the host's available task-by-task implementation workflow. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unblock the guarded OS VOYAGER deployment by fixing the Draco/WebAssembly CSP boundary and aligning E2E coverage with the current interface.

**Architecture:** Keep the existing receive-only Worker and OS VOYAGER behavior. Apply the same narrow CSP policy in the HTML meta element and Worker response header, permitting only same-origin resources plus the local blob worker required by Draco and WebAssembly compilation. Update browser tests to use the current navigation while retaining assertions for the R3 station-physics and canonical evidence flows. Permit the Worker CSP change in deployment guards only when normalizing the CSP line proves that no other Worker code changed.

**Tech Stack:** JavaScript ESM, Three.js GLTFLoader/DRACOLoader, Cloudflare Workers, Node test runner, Playwright, GitHub Actions.

## Global Constraints

- Keep `main` at `8cc2d69352847cc3032aaa2cf6cc0bd638475f6a`; do not merge PR #15.
- Preserve `listener-agent/`, `shared/contracts.js`, and all Worker logic except the existing DSN parser path and the explicitly checked CSP-only change in `worker/index.js`.
- Keep real RF transmission and spacecraft uplink disabled; no mission commands, no RF TX, and no spend.
- Require exact-commit CI, visual, security, data, listener, dry-run, and production black-box gates before publishing.
- Keep all public data and receiver truth labels distinct; do not label synthetic tests or DSN activity as locally received Voyager telemetry.

---

### Task 1: Enable the local Draco decoder under the strict CSP

**Files:**
- Modify: `index.html`
- Modify: `worker/index.js`
- Modify: `tests/content.test.mjs`

**Interfaces:**
- Consumes: the existing CSP meta policy and exported Worker `SECURITY` response headers.
- Produces: identical HTML and Worker CSP policies with `worker-src 'self' blob:` and `'wasm-unsafe-eval'`.

- [ ] **Step 1: Add the policy regression assertion**

Add a Node test that extracts both CSP policies, asserts they are identical, requires the local blob-worker directive, and requires the WebAssembly-specific script permission.

- [ ] **Step 2: Verify the current failure**

The existing Playwright trace already shows the browser blocking DRACOLoader's blob worker and leaving the model audit at `LOADING`. Run `npm test` after adding the assertion to confirm the old policy fails it.

- [ ] **Step 3: Implement the minimum policy change**

Add only `'wasm-unsafe-eval'` to `script-src` and `worker-src 'self' blob:` to both policies. Do not add new network origins or generic `'unsafe-eval'`.

- [ ] **Step 4: Verify the focused pass**

Run: `npm test`

Expected: the CSP equality assertion passes and all existing unit tests pass.

- [ ] **Step 5: Run browser verification**

Run: `npm run test:e2e`

Expected: the GLB audit leaves `LOADING`, reports `NASA_OFFICIAL_GLB`, and the production model remains the selected asset.

### Task 2: Align E2E checks with the current navigation without dropping R3 coverage

**Files:**
- Create: `tests/e2e/helpers.mjs`
- Modify: `tests/e2e/app.spec.mjs`
- Modify: `tests/e2e/order011.spec.mjs`
- Modify: `tests/e2e/order011-r3.spec.mjs`
- Modify: `tests/e2e/order013.spec.mjs`

**Interfaces:**
- Consumes: `window.__order013.getAudit()`, current `data-o13-mode` buttons, and the existing `#lab-drawer` station/evidence controls.
- Produces: a shared readiness helper that waits for the common-epoch frame and a resolved model truth, plus E2E tests that use the current navigation.

- [ ] **Step 1: Replace obsolete selectors with public UI behavior**

Use the visible `SIGNAL LAB` button to open the existing lab drawer. Use `OS VOYAGER` for the simulation/uplink-disabled assertions. Retain the station physics form, R3 canonical evidence refusal/download assertions, six viewport screenshots, reduced-motion checks, and accessibility checks.

- [ ] **Step 2: Verify the previous failure evidence**

The prior Playwright artifacts show old tests timing out on the intentionally hidden `#hud-menu` and `#hud-lab`, while the current visible navigation exposes `SIGNAL LAB` and `OS VOYAGER`.

- [ ] **Step 3: Implement shared readiness and current selectors**

Wait with Playwright's third-argument options signature so the 25-second readiness timeout is effective. Assert the actual audit and UI state rather than an empty legacy bridge.

- [ ] **Step 4: Verify browser coverage**

Run: `npm run test:e2e`

Expected: Chromium, mobile Chromium, and mobile WebKit complete with no failures; the canonical screenshot matrix runs only in Chromium.

### Task 3: Preserve deployment guardrails and trigger the next guarded attempt

**Files:**
- Modify: `.github/workflows/order013-ci.yml`
- Modify: `.github/workflows/order013-final.yml`
- Modify: `ops/order013-final-request.json`
- Create: `docs/plans/2026-10-13-order013-deploy-unblock.md`

**Interfaces:**
- Consumes: baseline commit `aaf686e33de7df600c066caca0b0d20cbf80c9d4`, fixed `main` SHA, and the exact-commit Actions gate.
- Produces: a guarded attempt 7 and a CSP-only exception that rejects any other `worker/index.js` changes.

- [ ] **Step 1: Restrict the Worker exception**

Allow `worker/index.js` only when replacing its CSP line with a placeholder makes the candidate file byte-for-byte identical to baseline; require the two new CSP directives.

- [ ] **Step 2: Preserve all other gates**

Keep the listener/contracts immutability checks, exact main SHA, no-merge request, zero budget, and RF-transmit prohibition unchanged.

- [ ] **Step 3: Trigger guarded deployment attempt 7**

Update only the request attempt and timestamp. Do not deploy directly, skip CI, merge to `main`, or change Cloudflare secrets.

- [ ] **Step 4: Verify the final deployment**

Require the workflow's exact-SHA checks, `wrangler --dry-run`, production health, OS VOYAGER asset, receive-only assertions, and production browser checks. If any gate fails, leave the prior production version active.
