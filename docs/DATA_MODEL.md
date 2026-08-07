# Data model

All network payloads use `schemaVersion: 1`, UTC ISO-8601 timestamps, explicit units, and provenance. Core models are Voyager state, trajectory manifest, DSN snapshot, mission status, signal snapshot, and source health. Unknown fields are tolerated; required core fields are strict at network boundaries.

Voyager position is `ICRF_GEOCENTRIC` in km and velocity in km/s. Signal frequencies are Hz, sample rates Hz, drift Hz/s, and powers relative dB unless calibration metadata exists. Schema V2 must be introduced through additive compatibility or a versioned endpoint; V1 remains accepted during migration.
