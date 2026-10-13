# OS VOYAGER

## Purpose

OS VOYAGER is the read-only operational console integrated into Voyager Link. It combines public network status, derived geometry, a registered receive-only station status, dated mission facts, and a local scientific-data analysis path. It is not a NASA/JPL operations console and cannot control Voyager 1.

## Data panels

- NASA/JPL DSN Now: public ground-network status from the fixed NASA Eyes XML feed. The UI polls every five seconds while the panel is visible. Directional upSignal/downSignal activity is shown separately. A missing Voyager 1 target match is not interpreted as proof of no contact. NASA documents that DSN Now may misidentify a spacecraft during off-nominal scenarios.
- JPL Horizons: distance, one-way light time, and radial rate from sourced geometry. The Worker cache and source epoch are displayed. A stale fallback remains stale; no geometry value is presented as engineering telemetry.
- Receiver pipeline: displays NO_SOURCE, LOST, or the registered station product state. A valid station signature proves source registration and envelope integrity, not NASA confirmation of the spacecraft identity.
- Mission snapshot: official published instrument facts with the source update date. It is not live telemetry. NASA says Voyager 1's cameras were turned off in 1990, their control software was removed, and the original ground computers no longer exist; reactivation feasibility is uncertain.
- PWS science: links to the NASA PDS VLISM electron-density bundle and data collection. The bundle metadata reports observations through 2025-09-01, while the data-collection page reports 2025-04-14 as its stop date. The UI retains this source discrepancy. Neither is a real-time X-band carrier feed.
- Local CSV analysis: a downloaded PDS measurement CSV is processed in-browser only. The analyzer reports row/column counts, parseable time range, and descriptive numeric statistics. It does not upload or persist the file, and it does not mask fill values; the corresponding PDS label and product-specific missing-value rules must be reviewed before scientific interpretation.

## Simulated operations

The rehearsal runs a local checklist for missing receiver data, DSN/local mismatch, PWS archive review, or imaging-recovery feasibility. It does not issue commands, serialize command frames, access DSN control, or transmit RF. A simulation result is not a spacecraft diagnosis.

## Future integration gate

The uplink gateway is intentionally disabled. A future integration requires all of the following before any control implementation is considered:
1. Written authorization from the responsible NASA/JPL mission operator.
2. An official documented mission interface and explicit access credentials supplied by the operator.
3. A non-flight test environment and reviewed interface-control documents.
4. Security assessment, least privilege, dual approval, immutable audit logging, rate limits, and a tested rollback/abort plan.
5. Separate change approval after the above evidence exists.

A project owner approving this repository is not a substitute for mission-operator authorization. No RF transmit path or command frame builder is included in this release.
