# Product truth

`TELESCOPE_LIVE` requires a real receiver source, recent heartbeat, station identity, capture metadata, and a provenance record. `RECORDED_AUTHENTIC` requires a manifest with source URL, observatory, capture time, frequency, sample rate, checksum, and redistribution terms. `SYNTHETIC_TEST` is deterministic generated IQ. `OFFICIAL` is a normalized official source; `DERIVED` is a documented calculation; `INTERPOLATED` is a rendering or time interpolation; `STALE` is an expired fallback.

The X-band carrier is not decoded telemetry. DSN status is not a local reception. PWS science data and sonification are not the communications carrier. A single spectral peak can be `CANDIDATE`; `DETECTED` additionally requires threshold, integration persistence, source validity, and confidence.

Correct: “Synthetic carrier detected in deterministic fixture.” Incorrect: “Receiving Voyager live” while replaying generated IQ. Correct: “Derived one-way light time from Horizons distance.” Incorrect: “Live telemetry delay.”
