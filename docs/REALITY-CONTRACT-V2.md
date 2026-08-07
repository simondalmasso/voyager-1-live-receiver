# Reality contract V2

Receiver truth states are closed and versioned: `TELESCOPE_LIVE_VERIFIED`, `RECORDED_AUTHENTIC_VERIFIED`, `SYNTHETIC_TEST`, `UNVERIFIED_SOURCE`, `NO_SOURCE`, `STALE`, and `LOST`.

A live product becomes verified only after strict schema validation, registered station lookup, Ed25519 verification over canonical JSON, band/version policy, monotonic sequence, nonce uniqueness, clock-skew checks and freshness. A fixture key is rejected whenever `APP_ENV=production`. Unknown critical fields are rejected. Any validation failure degrades downward and never returns a verified state.

The browser revalidates schema version, truth state and freshness. It cannot elevate data. Signal mode starts at `NO VERIFIED LIVE SOURCE`; synthetic generation requires an explicit button press.

A recorded capture becomes authentic only after SigMF required fields, SHA-512 byte verification, explicit compatible license, stable URL/DOI, station/recorder/hardware identity and transformation-chain validation. Names containing `authentic` have no authority.
