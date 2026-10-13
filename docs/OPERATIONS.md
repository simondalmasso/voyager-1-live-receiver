# Operations

Start the web runtime with `npm run dev`; health is `/api/v1/health`. Start a synthetic listener with `PYTHONPATH=listener-agent/src python -m voyager_listener.cli serve --synthetic`. Use `/health`, `/snapshot`, and `/events` for listener diagnostics. Update source snapshots only through reviewed commits. If an upstream fails, preserve the scene and display `STALE` or `UNAVAILABLE`. Local rollback is `git checkout <known-sha>` followed by a clean build. No remote operation is part of this checkpoint.


## OS VOYAGER

Open OS VOYAGER from the bottom navigation. The public DSN status and local receiver snapshot are separate cards; if the public feed has no explicit Voyager 1 target, the UI says so without inferring no contact. JPL Horizons values are derived geometry, not telemetry. The mission card is a dated NASA-published snapshot.

For PWS analysis, open the official PDS data collection, download a measurement-product CSV, and choose it in the local analyzer. Do not use the collection inventory CSV as a measurement table. The analyzer runs in the browser, never uploads the file, reports descriptive statistics, and leaves PDS fill values unmasked. Preserve the product label and its units before drawing scientific conclusions.

The diagnostic rehearsal is simulation only. It does not create command frames or transmit RF. Real uplink remains disabled until an official NASA/JPL/operator interface and written authorization are provided.
