# Evidence bundles

The listener is the only canonical evidence producer. It creates deterministic evidence bundles/manifests with canonical JSON, stable file metadata, SHA-256 per-file hashes and tamper verification. Raw evidence is never rewritten by RFI transforms; masks, DSP configuration and derived products remain separate manifest entries. Secret-like material is rejected before packaging.

The browser does not synthesize a parallel evidence format and Cloudflare does not receive raw IQ on the canonical path. `/api/v2/lab/evidence` exposes a downloadable listener manifest only when all three conditions hold simultaneously: listener `status=READY_CANONICAL_MANIFEST`, a manifest exists, and `missing` is empty. If the listener declares `NOT_READY`, reports missing inputs, or has no manifest, the Worker and pipeline remain `NOT_READY` even when a partial diagnostic manifest exists internally.

A partial manifest may be retained in the signed/reduced listener snapshot for diagnosis, but it is not returned as complete downloadable scientific evidence. Hash manifests provide integrity; they are not identity signatures. Station/envelope identity is handled separately by the registered Ed25519 receiver contract.
