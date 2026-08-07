# Third-party notices

Voyager Link includes or references the following third-party material.

## Runtime code

- **Three.js 0.180.0** — MIT license. Runtime ES modules are vendored into the production build for deterministic offline use.
- **Draco decoder distributed with Three.js** — used only to decode the NASA GLB when required by that asset.

## NASA visual asset

- **Voyager Probe (A)** from NASA 3D Resources / `nasa/NASA-3D-Resources`.
- Pinned source commit: `11ebb4ee043715aefbba6aeec8a61746fad67fa7`.
- Bundled GLB SHA-256: `7cf8eefb5a0fca9e4e1b0d1e51c37433124169183e5dbfd2d8034af902311821`.
- Credit: NASA.
- Usage is subject to NASA's Images and Media Usage Guidelines. No NASA/JPL logo is bundled and no affiliation or endorsement is claimed.
- Machine-readable provenance is in `assets/voyager-probe-a.provenance.json`.

## Data and science sources

NASA/JPL Horizons, DSN Now public status, NASA mission pages, PDS and NAIF/SPICE are upstream data/documentation/science sources. Their inclusion as sources does not imply operational access to NASA/JPL/DSN systems.

## CI-only tools

CI installs pinned tools without committing their package trees: Wrangler 4.114.0, Playwright 1.62.0 and `@axe-core/playwright` 4.12.1.

No OpenWebRX+ or unlicensed `bistromath/voyager` code is copied. The procedural spacecraft in `src/scene.js` is original project code and is only a fallback when the official model cannot load.
