# Canonical IQ bus

`CanonicalIQFrame` is the single post-acquisition contract for SoapySDR/GNU Radio/SigMF/test fixtures. Acquisition adapters normalize metadata; every downstream DSP stage consumes the same frame type. Per-consumer queues are bounded and use explicit drop-oldest policy with counters so a slow recorder or visualizer cannot create unbounded memory or block acquisition. Stream sequence gaps and source-reported dropped samples remain observable.

Replay retains the original `timestampStart`, truth class and provenance ID, and adds `replayReceivedAt`. A recorded authentic capture remains `RECORDED_AUTHENTIC_VERIFIED`; parity never aliases replay to live.
