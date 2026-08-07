# Testing

Node built-in tests cover constants, units, vector calculations, truth contracts, Horizons parsing/topocentric Doppler, hostile DSN XML, input validation, security headers, receiver signatures, evidence readiness and the receive-only invariant. R3 explicitly tests that a signed snapshot with a partial manifest plus `status=NOT_READY`/`missing=[station]` remains `NOT_READY` in both Evidence API logic and PIPELINE, while only `READY_CANONICAL_MANIFEST` + manifest + empty `missing` can become downloadable `READY` evidence.

Python unittest covers deterministic tone recovery, no-signal rejection, Doppler sign, chunked SigMF, measured detector evidence, stateful integration and Canonical IQ bus behavior. R3 adds sustained-flow coverage proving the operational DSP consumer reports zero drops unless a real consumer is slow; the unused evidence queue is not counted as backpressure.

Playwright covers desktop/mobile/WebKit, fullscreen progressive disclosure, camera/recenter preservation, reduced motion, accessibility, truthful signal labels and evidence-download gating. R3 verifies the browser performs no download for `NOT_READY` partial evidence and downloads only the canonical listener manifest when the Worker reports `READY`.

CI also builds, reports bundle size, verifies data JSON, inventories licenses, scans secrets, runs CodeQL/security gates and retains a Wrangler dry-run artifact. Terminal deploy workflows then verify the exact SHA against production APIs and the accepted fullscreen viewport matrix before recording a successful GitHub Deployment.
