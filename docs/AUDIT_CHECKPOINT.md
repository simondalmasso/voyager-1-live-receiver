# ORDER 010 — terminal audit checkpoint

Authority: GitHub issue #10, latest AUD continuation comment `5214873711` with `ACTION_NOW=CONTINUE_ORDER_010_END_TO_END`.

Canonical branch: `feat/aud-001-complete-product`. `main` remains outside the deployment path and must not be merged by ORDER 010.

## Implemented scope

- Fullscreen desktop/mobile Voyager Link experience with orbit/zoom/recenter, guided views, reduced-motion handling and accessible 2D fallback.
- Official NASA Voyager Probe (A) GLB as primary model, pinned by source commit and SHA-256; procedural model is fallback only.
- JPL Horizons current geocentric geometry with explicit frames/units/provenance, plus request-only WGS84/GMST topocentric az/el.
- NAIF/SPICE trajectory from launch onward using official Voyager kernels with adaptive encounter density and persisted Horizons cross-check evidence.
- Public DSN status, NASA mission snapshot and PDS science surfaces with separate truth classes; no source is aliased to telescope reception.
- Operational receive-only Python listener: SigMF, SoapySDR, GNU Radio UDP/stdin, deterministic synthetic fixtures, Doppler prediction/de-doppler, overlapped FFT, robust noise floor, persistence and detector states.
- Authentic-recording manifest/hash verification. Filenames never grant authenticity.
- Cloud relay contract: registered station, Ed25519 signature, timestamp/future-skew, X-band constraints, station binding, source-mode validation and reduced-product-only payloads.
- SQLite Durable Object ReceiverHub with transactional sequence + nonce replay state, 30-second live TTL, explicit `LOST`, and hibernating WebSocket distribution.
- Signal Hunt synthetic challenge, simulated light pulse with no RF transmission, Truth Layer, optional YouTube IFrame music control and offline PWA shell.
- Security headers, CSP, no account/analytics/ads/payment/geolocation persistence, source/license inventory and test/CI gates.

## Scientific evidence

`artifacts/science-evidence/spice-horizons-crosscheck.json` records 473 full-mission adaptive samples and a 2026-08-07 Earth-relative SPICE/Horizons comparison with `pass=true`. Kernel hashes and coverage windows are recorded in the same artifact.

## Cost and safety invariants

- `USD_BUDGET=0`
- `PAYMENT_DATA=NO`
- `RF_TX=NO`
- `MAIN_MERGE=NO`
- Canonical Cloudflare resources are Workers Static Assets + Worker + SQLite Durable Object, all compatible with Workers Free. No paid add-on is required by configuration.
- No secret value is committed or printed.

## Terminal procedure

The permanent CI workflows remain `ci.yml`, `listener-ci.yml`, `data-verify.yml`, and `security.yml`. `order010-deploy.yml` is the sole audited remote-deploy mechanism and is path-gated by `ops/order010-deploy-request.json`; it repeats core, listener, security and Wrangler dry-run checks before deploying the exact triggering SHA. Production smoke must validate health/build SHA, static assets, NASA model digest, SPICE cross-check, ReceiverHub snapshot/WebSocket, rejection of an unregistered ingest, and security headers before it may publish `STATUS=DEPLOYED_READY_FOR_AUD` to issue #10 and PR #8.

This file intentionally contains no claimed production URL, Cloudflare version ID, GitHub deployment ID or successful deploy status before those facts exist remotely.
