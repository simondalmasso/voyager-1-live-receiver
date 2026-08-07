# Order 011 contracts

V1 receiver snapshot and signed-reduced-product ingest remain backward compatible. Order 011 adds local scientific contracts (`CanonicalIQFrame`, `SpectrumProduct`, `PipelineTelemetry`) and read-only `/api/v2/lab/*`, `/api/v2/station/physics`, `/api/v2/observation-window` endpoints. No V1 field is silently redefined. Raw IQ remains local and no uplink/control contract exists.

Multi-station support is explicitly L0 independent observations, L1 time/frequency-aligned comparison, and conservative L2 statistical fusion. L3 coherent/phase-sensitive combination is rejected unless clock, phase, delay and calibration requirements are independently demonstrated.
