# AUD-002 research basis

## Adopted reception patterns

- CAMRAS/Dwingeloo: X-band reception requires an appropriate 8.4 GHz feed, physical pointing predictions and Doppler correction. The project adopts prediction-driven narrowband search, receive-only wording and explicit separation between reception and communication.
- Allen Telescope Array: Voyager 1's coherent downlink is near 8420.43 MHz and narrower than 1 Hz. The detector therefore uses configurable sub-Hz resolution, time-variable dechirp and long integration rather than a fixed 1024-bin FFT.
- `bistromath/voyager`: only public scientific principles were considered: SigMF capture metadata, integration and search around predicted drift. The repository has no declared license, so no code, notebook, flowgraph or asset was copied.
- SatNOGS: station identity, observation identity, timestamps and publication metadata informed the registered-station and signed-product model.
- OpenWebRX+ and Browser Ground Station: waterfall/source-state UX informed the interface. Their AGPL/GPL code and assets were not copied; implementation is clean-room native JavaScript/Python under MIT.

## Adopted formats and astronomy

- SigMF: strict required metadata, dataset SHA-512, explicit license/source, bounded streaming reads and transformation chain.
- JPL Horizons: target `-31`, geocentric center `500@399`, ICRF/J2000, geometric `NONE`, km and km/s for state; `OBSERVER` with explicit geodetic coordinates for sky view.
- NAIF/SPICE: official `vgr1.x2100.bsp`, `de440s.bsp` and `naif0012.tls` are fetched reproducibly, hashed and used at build time. The large kernels are not committed.
- NASA PDS: Voyager 1 PWS Spectrum Analyzer DOI `10.17189/rg5g-ta53` is catalogued as in-situ plasma-wave science and never as Earth-received X-band carrier data.

## Cloudflare runtime decision

`ReceiverHub` is one SQLite-backed Durable Object addressed by the stable name `voyager-1`. It stores only the latest reduced snapshot, sequence/nonce replay state and short rate windows. WebSocket Hibernation is used; raw IQ is rejected. Hard limits are 256 KiB per product, 30 products/minute in the object, 60 ingress requests/minute at the Worker edge, 120-second retention and one logical object. This design targets Workers Free and does not request paid resources or automatic upgrades.

## Rejected patterns

- Browser/client declarations of authenticity or verification.
- Filename-based authenticity heuristics.
- Continuous synthetic receiver data on page load.
- DSN activity interpreted as proof of local reception.
- Fixed-angle presets described as real Earth geometry.
- Raw IQ upload to Cloudflare.
- Redistributing ATA/CAMRAS captures without a stable checksum and compatible license.
- Copying AGPL/GPL/unlicensed implementation material into the MIT tree.
