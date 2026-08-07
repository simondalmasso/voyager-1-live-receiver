# Listener protocol

`GET /health` returns receive-only health. `GET /snapshot` returns `SignalSnapshotV1`. `GET /events` streams SSE frames with sequence, source mode, station, capture metadata, detector analysis, bounded spectrum, provenance, and generated time. The frontend does not receive raw IQ. SSE is the implemented zero-dependency live transport; a future WebSocket adapter must preserve the same schema, heartbeat, backpressure, limits, and authentication semantics.
