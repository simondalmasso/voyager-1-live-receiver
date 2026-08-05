# Voyager 1 Live Receiver

An independent, receive-only webapp that combines a navigable WebGL mission scene, JPL Horizons geometry, opportunistic DSN status, and a local SigMF/synthetic narrowband receiver. It is not affiliated with NASA, JPL, or the Deep Space Network and cannot send commands to Voyager 1.

## Truth modes

| Label | Meaning |
|---|---|
| `TELESCOPE_LIVE` | Fresh reduced products from a real operator-controlled receiver with heartbeat and provenance. |
| `RECORDED_AUTHENTIC` | A prior real capture whose manifest, source, license, and checksum are verified. |
| `SYNTHETIC_TEST` / `SIMULATED` | Deterministic generated IQ or visual motion used for tests and demonstration. |
| `DERIVED` / `INTERPOLATED` | Values computed from sourced inputs or deliberately compressed rendering coordinates. |
| `STALE` / `UNAVAILABLE` | Honest fallback when an upstream or source is unavailable. |

`LIVE` never means access to JPL/DSN operations. The implemented communication path is passive reception of a narrow X-band carrier through an external telescope/listener node.

## Architecture

```text
NASA/JPL Horizons + DSN public feed -> Cloudflare Worker -> browser data layer
operator SigMF/SDR -> local Python listener -> HTTP snapshot/SSE -> browser Signal mode
browser -> custom dependency-free WebGL scene + accessible HTML controls
```

The native ES-module/WebGL architecture is recorded in ADR 0001. It removes runtime package supply-chain and bundle weight while keeping the public seams required by AUD-001. The procedural spacecraft is a clearly labeled fallback; an official NASA model is not redistributed until asset terms and a reproducible checksum are verified.

## Requirements

- Node.js 24 LTS and npm 11
- Python 3.12+
- Optional: a supported SDR stack, radiotelescope access, NumPy/SciPy, Astropy/Astroquery, SoapySDR, or GNU Radio

## Quickstart web

```bash
npm ci
npm run dev
# http://127.0.0.1:4173
```

## Quickstart synthetic listener

```bash
PYTHONPATH=listener-agent/src python -m voyager_listener.cli doctor
PYTHONPATH=listener-agent/src python -m voyager_listener.cli synth --output /tmp/voyager.sigmf-meta
PYTHONPATH=listener-agent/src python -m voyager_listener.cli analyze /tmp/voyager.sigmf-meta --expected-frequency-hz 8420430048 --drift-hz-s 0.2
PYTHONPATH=listener-agent/src python -m voyager_listener.cli serve --synthetic
```

Open Signal mode and choose `TELESCOPE LIVE`; the local endpoint is still truth-labeled synthetic because its source metadata says so.

## SigMF

```bash
PYTHONPATH=listener-agent/src python -m voyager_listener.cli analyze capture.sigmf-meta --expected-frequency-hz 8420430000
PYTHONPATH=listener-agent/src python -m voyager_listener.cli serve capture.sigmf-meta
```

The core supports chunked `cf32_le` and `ci16_le`. An authentic capture is never inferred from a filename in production; operators must provide the provenance manifest described in `docs/SIGMF.md`.

## Checks

```bash
npm test
npm run lint
npm run format:check
npm run build
npm run bundle:report
npm run verify:data
PYTHONPATH=listener-agent/src python -m unittest discover -s listener-agent/tests -v
```

CI additionally runs Playwright desktop/mobile, axe, Wrangler dry-run, source/license inventory, and security checks. No workflow deploys.

## Cloudflare pre-deploy

`wrangler.jsonc` uses Static Assets with `/api/*` worker-first and SPA fallback. The exact future command is:

```bash
npx wrangler@4.114.0 deploy
```

**Do not execute it without a separate AUD/owner authorization.** No remote Worker, route, binding, DNS, storage, secret, payment method, or production URL has been created by AUD-001.

## Repository map

- `src/`: browser UI, scene, signal visualization, data layer
- `worker/`: versioned API, Horizons/DSN adapters, security headers and fallbacks
- `shared/`: contracts, units and truth validation
- `listener-agent/`: receive-only Python DSP and SigMF/SSE implementation
- `data/`: source manifests and small deterministic metadata
- `docs/`: architecture, operations, science, security and audit records
- `tests/`: Node contract/Worker/content tests and Playwright E2E

## Privacy

No account, analytics, ads, fingerprinting, microphone, camera, or automatic geolocation request. Precise observer coordinates are request-scoped and not persisted by the app.

## Known limits

No redistributable authentic IQ capture or official NASA 3D model is bundled. DSN Now is an opportunistic public-status source, not a telescope-control interface. The pure-Python FFT core is intended for deterministic fixtures and small captures; optional NumPy/SciPy acceleration is recommended for observatory-scale data. See `docs/AUDIT_CHECKPOINT.md`.

Licensed MIT. See `THIRD_PARTY_NOTICES.md` and `data/sources.json`.
