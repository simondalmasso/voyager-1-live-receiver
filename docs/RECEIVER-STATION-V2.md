# Connecting a physical receive-only station

1. Generate an Ed25519 private key on the station with OpenSSL. Keep it off GitHub, Cloudflare and browser storage.
2. Submit only the public raw key, station identity, allowed X-band range, minimum listener version and status for review into `data/stations.v1.json` and `worker/stations.js`.
3. Configure `voyager-listener predict` with the observatory coordinates. Coordinates are used for the Horizons request and local cache only.
4. Acquire with `voyager-listener live --source soapy|gnuradio-udp|sigmf-stream|stdin`. Use enough integration time to achieve the selected sub-Hz resolution and record an off-target/reference observation.
5. Inspect the evidence bundle: station, capture/stream manifest, hashes, prediction CSV/manifest, compact waterfall matrix, detection, off-target comparison, software and signature.
6. POST the signed reduced envelope to `/api/v1/receiver/ingress`. Never post raw IQ.
7. Confirm the public snapshot reports the exact station, signature key, sequence, software SHA, prediction hash, spectrum hash and age. It must become `STALE` and then `LOST` after heartbeat expiry.

A real station cannot be accepted using the repository fixture key. Production explicitly rejects it.
