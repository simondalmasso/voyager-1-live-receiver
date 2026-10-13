# Product truth

Canonical source states are explicit and non-interchangeable:

- `TELESCOPE_LIVE_VERIFIED`: fresh registered-station receive-only product after signature, timestamp, station, band and replay gates.
- `RECORDED_AUTHENTIC_VERIFIED`: recording whose source, capture metadata, redistribution terms and full-data hashes satisfy the authentic-recording contract.
- `SYNTHETIC_TEST`: deterministic generated IQ used for tests/training; it can never promote itself to authentic/live.
- `UNVERIFIED_SOURCE`: physical or supplied source that has not passed the live/authenticity contract.
- `NO_SOURCE`: no receiver product is present.
- `STALE`: source/prediction exists but its freshness gate has expired; RF predictions fail closed when freshness is required.
- `LOST`: a previously verified live receiver heartbeat expired.
- `UNAVAILABLE`: upstream/public source unavailable when no stronger state applies.

Other provenance classes describe non-receiver facts, including `MISSION_STATUS_OFFICIAL_SNAPSHOT`, `DSN_LIVE_PUBLIC_STATUS`, `PWS_ARCHIVED_SCIENCE` and `DERIVED_GEOMETRY`. They must never be presented as telescope reception or spacecraft telemetry.

The X-band carrier is not decoded telemetry. DSN status is not a local reception. PWS science data and sonification are not the communications carrier. A spectral feature is never promoted merely because a peak exists: detection confidence depends on measured frequency/drift residuals, persistence, SNR and RFI/reference evidence, and may remain `INSUFFICIENT_EVIDENCE`.

Evidence is fail-closed. `READY_CANONICAL_MANIFEST` is a listener declaration, not a browser inference: it requires a manifest to exist and `missing` to be empty. A partial manifest may remain inside the listener product for diagnostics, but Worker/API/browser surfaces keep it `NOT_READY` and do not expose it as downloadable scientific evidence.

Correct: “Synthetic carrier detected in deterministic fixture.” Incorrect: “Receiving Voyager live” while replaying generated IQ. Correct: “Derived one-way light time from sourced geometry.” Incorrect: “Live telemetry delay.”


## OS VOYAGER operational boundary

The OS VOYAGER console polls the public DSN Now status and current JPL Horizons geometry separately from the local physical receiver hub. DSN Now is public ground-network status; Horizons is derived geometry; neither is spacecraft telemetry. A signed station product verifies the registered receive-only source and freshness gates, not NASA's identity attribution by itself.

The browser's deterministic signal fixture uses the detector state CANDIDATE and provenance SYNTHETIC_TEST. Signal mode defaults to the receiver hub, so absence is shown as NO_SOURCE rather than generating a synthetic carrier. Archived PWS CSV summaries are processed locally in the browser and explicitly do not mask fill values or claim real-time observations.
