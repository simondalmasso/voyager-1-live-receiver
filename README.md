# Voyager Link

Voyager Link is an independent, receive-only Voyager 1 mission experience and verified signal laboratory. It is not affiliated with NASA, JPL, or the Deep Space Network. It contains no RF uplink, command, transmitter, telescope-control, or DSN-control path.

## Product

- Fullscreen desktop/mobile 3D scene with NASA's official lightweight Voyager GLB as the primary model and a procedural fallback.
- Current JPL Horizons geocentric geometry: distance, one-way/round-trip light time, range rate, RA/Dec and optional request-only observer az/el.
- Reproducible NAIF/SPICE trajectory from launch onward, with adaptive encounter sampling and a machine-recorded Horizons cross-check.
- Public DSN Now status, explicitly separated from telescope reception and spacecraft telemetry.
- Official NASA mission/instrument status snapshots, explicitly time-stamped and never represented as live telemetry.
- Receive-only Python listener for SigMF, SoapySDR, GNU Radio UDP and stdin streams, including Doppler prediction and narrowband detection.
- Cloudflare SQLite Durable Object ReceiverHub for replay-safe, Ed25519-signed reduced products and hibernating WebSocket fan-out.
- Signal Hunt synthetic training, Virtual Light Pulse, Truth Layer, YouTube album control and offline PWA shell.

## Truth classes

| Class | Meaning |
|---|---|
| `MISSION_STATUS_OFFICIAL_SNAPSHOT` | Official NASA mission/instrument snapshot at a stated verification time. |
| `DSN_LIVE_PUBLIC_STATUS` | Public DSN Now activity only; never DSN command/control. |
| `PWS_ARCHIVED_SCIENCE` | Archived Plasma Wave Subsystem science. |
| `DERIVED_GEOMETRY` | Reproducible values calculated from sourced geometry. |
| `TELESCOPE_LIVE_VERIFIED` | Fresh registered-station product after signature, timestamp, station, band and replay gates. |
| `RECORDED_AUTHENTIC_VERIFIED` | Recording with machine-verifiable provenance and hashes. |
| `SYNTHETIC_TEST` | Generated test/challenge data; cannot promote itself to live. |
| `UNVERIFIED_SOURCE` | Physical/supplied source that has not passed the live/authenticity contract. |
| `STALE`, `LOST`, `UNAVAILABLE` | Explicit degraded states. |

## Architecture

```text
NASA/JPL Horizons ─┐
NASA DSN public ───┼─> Cloudflare Worker ─> browser Truth Layer / 3D mission scene
NASA mission/PDS ──┘          │
NAIF/SPICE artifact ──────────┤
                              └─> SQLite ReceiverHub Durable Object
                                   ├─ station sequence + nonce replay state
                                   ├─ latest verified reduced product (30 s TTL)
                                   └─ hibernating WebSocket clients

SDR / telescope / SigMF -> local listener -> signed reduced product -> /api/v1/receiver/ingest
                                                      browser <- /snapshot + /live
```

Raw IQ is not uploaded by the canonical live path. The Worker verifies the registered station, Ed25519 signature, timestamp/future skew, allowed X-band range, source mode and detector state before the Durable Object can accept a product. Sequence and nonce checks are persisted transactionally in SQLite.

## Local web

```bash
npm ci
npm run dev
# http://127.0.0.1:4173
```

## Listener

```bash
PYTHONPATH=listener-agent/src python -m voyager_listener.cli doctor
PYTHONPATH=listener-agent/src python -m voyager_listener.cli synth --output /tmp/voyager.sigmf-meta
PYTHONPATH=listener-agent/src python -m voyager_listener.cli analyze /tmp/voyager.sigmf-meta --expected-frequency-hz 8420430048 --drift-hz-s 0.2
PYTHONPATH=listener-agent/src python -m voyager_listener.cli serve --synthetic
```

Synthetic products remain `SYNTHETIC_TEST` everywhere. A physical local stream remains `UNVERIFIED_SOURCE` until it satisfies the registered-station live contract.

## Verification

```bash
npm test
npm run lint
npm run format:check
npm run build
npm run bundle:report
npm run verify:data
npm run inventory
PYTHONPATH=listener-agent/src python -m unittest discover -s listener-agent/tests -v
npx wrangler@4.114.0 deploy --dry-run --outdir .wrangler-dry-run
```

CI additionally runs Playwright desktop/mobile, axe, listener evidence, security checks and deployment dry-run artifacts.

## Cloudflare

`wrangler.jsonc` uses Static Assets with `/api/*` Worker-first routing and a SQLite Durable Object binding named `RECEIVER_HUB`. Order 010 authorizes deployment through GitHub Secrets with `USD_BUDGET=0`; secret values must never be printed or committed.

## Privacy and safety

No account, ads, analytics, fingerprinting, microphone, camera, automatic geolocation, payment data or RF transmission. Observer coordinates are request-scoped and are not persisted. The public app does not expose any DSN, spacecraft-command, RF-transmit or telescope-control capability.

## Known limits

A real green `TELESCOPE_LIVE_VERIFIED` state requires an independently operated, registered receive-only station and fresh signed reduced products. DSN Now is opportunistic public status. NASA upstreams can degrade; degraded states remain labeled. Authentic raw IQ is not redistributed by default.

Licensed MIT. See `THIRD_PARTY_NOTICES.md`, `data/sources.json`, `docs/PRODUCT_TRUTH.md`, `docs/SECURITY.md`, and `artifacts/science-evidence/`.


## OS VOYAGER: public status, science archive and simulated operations

The OS VOYAGER panel separates the NASA/JPL DSN Now public status feed, JPL Horizons derived geometry, the registered receive-only station pipeline, NASA's dated mission snapshot, and archived PDS PWS science. DSN Now is not spacecraft telemetry; archived PWS measurements are not live downlink data.

Open OS VOYAGER from the navigation bar to inspect provenance and timestamps, run a local-only diagnostic rehearsal, or analyze a downloaded PDS measurement CSV in the browser. The CSV is not uploaded and fill values are not masked automatically. The simulated operations panel does not generate command frames or transmit RF. Real uplink remains disabled until an official NASA/JPL/operator interface and written authorization exist. See docs/OS_VOYAGER.md.
