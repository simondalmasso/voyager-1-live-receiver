# Order 013 — clean-room visual research

This document records the observable interaction and visualization patterns used for Order 013. It is a design/provenance record, not a claim of affiliation with NASA/JPL. Voyager Link remains an independent receive-only project.

## Primary interaction references

### NASA Eyes on the Solar System

Sources:

- https://eyes.nasa.gov/apps/solar-system/#/sc_voyager_1
- https://science.nasa.gov/eyes/
- https://science.nasa.gov/wp-content/uploads/2024/08/nasa-eyes-for-museums-relevant-links.pdf

Observable patterns adopted clean-room:

- A selected spacecraft remains the visual anchor while the camera can move from a close spacecraft view to Solar System context.
- Object selection, camera target and time/epoch are separate concepts.
- Distance is an explicit `FROM → TO` interaction with the two endpoints visually connected.
- Large changes of scale are handled as visualization transforms; numeric geometry is not inferred from screen distance.
- Labels are anchored to bodies and selectively culled rather than presented as a permanent dashboard.
- Controls live at the edges and scientific detail is progressively disclosed.
- Camera transitions frame the selected subject and context; user input can interrupt a transition.

The NASA Eyes educator/museum toolkit explicitly documents deep links to spacecraft/time states and Distance Tool routes. It also describes Eyes as responsive and physics-driven. Voyager Link reimplements only those observable interaction concepts with its own code, layout and identity.

Discarded:

- NASA branding, insignia, logos and pixel-for-pixel UI reproduction.
- Embedding NASA Eyes as the product surface.
- Any internal/proprietary Eyes asset not published as a downloadable NASA resource.
- Treating the scene scale itself as scientific distance truth.

### NASA Eyes trajectory context

NASA Eyes' trajectory views establish a useful mental model for long-duration missions: retain the mission object while pulling back far enough to understand the complete path. Order 013 maps that pattern to `MISSION_TRAJECTORY`, using Voyager Link's existing trajectory product and floating-origin rendering.

## Official Voyager model candidates

### Voyager Probe (A)

- Source page: https://science.nasa.gov/3d-resources/voyager-probe-a/
- Agency: NASA
- Existing pinned repository asset: `assets/voyager-probe-a.glb`
- Role in Order 013: candidate and `HERO_LOW` fallback.

### Voyager Probe (B)

- Source page: https://science.nasa.gov/3d-resources/voyager-probe-b/
- NASA 3D Resources repository: https://github.com/nasa/NASA-3D-Resources/tree/master/3D%20Models/Voyager%20Probe%20%28B%29
- Agency/credit: NASA / Michael D. Carbajal
- Published GLB size: about 1.64 MB.
- Role in Order 013: `HERO_HIGH` candidate. The exact production selection is recorded by `artifacts/order013/model-comparison.json`, not assumed from file size.

### Voyager VTAD model

- Source page: https://science.nasa.gov/resource/voyager-3d-model/
- Agency/credit: NASA Visualization Technology Applications and Development (VTAD)
- Published glTF size: about 2.98 MB.
- Role in Order 013: controlled comparison candidate. It is not loaded in production merely because it is larger.

Selection policy: compare source bytes, glTF structural metrics and hero-relevant detail indicators under a common test policy. The selected production asset must preserve recognisable HGA, bus, RTGs, booms/instruments and material differentiation while remaining inside the mobile startup budget. Original source hashes and production hashes are kept separately.

## Solar System references

Official visual/provenance references:

- Earth: https://science.nasa.gov/resource/earth-3d-model/
- Jupiter: https://science.nasa.gov/resource/jupiter-3d-model/
- Saturn: https://science.nasa.gov/resource/saturn-3d-model/
- Neptune: https://science.nasa.gov/resource/neptune-3d-model/
- Solar System scale: https://science.nasa.gov/resource/solar-system-scales-artists-concept/
- Oort Cloud/logarithmic context: https://science.nasa.gov/resource/oort-cloud-and-scale-of-the-solar-system-infographic/
- JPL approximate orbital elements: https://ssd.jpl.nasa.gov/planets/approx_pos.html
- JPL Horizons API: https://ssd.jpl.nasa.gov/api/horizons.api

Implementation decision:

- Current body positions are a same-epoch heliocentric `ECLIPJ2000` product generated from JPL Horizons and committed as reduced data.
- Overview bodies use efficient sphere/ring geometry and purpose-built materials; heavy planetary 3D models are not part of first load.
- Orbit curves are explicitly labeled `ORBIT_APPROXIMATION`; current markers remain at the Horizons vectors.
- `TRUE_ORBIT_RELATIVE`, `PLANETARY_OVERVIEW` and `VOYAGER_DISTANCE_LOG` are visual scale modes. They never alter the numeric km/AU/light-time calculations.
- Saturn's ring is a dedicated inclined ring surface rather than a generic torus.

## Secondary competitor

Sources:

- https://theskylive.com/3dsolarsystem?obj=voyager1
- https://theskylive.com/voyager1-tracker

Adopted concept: a user should be able to understand a spacecraft as both a local object and a member of a Solar System-scale scene.

Discarded: dense astronomy-site chrome and any screen-space distance semantics. Voyager Link keeps the immersive canvas primary and sends details to drawers/sheets.

## Visual system decisions

### Spacecraft local view

`SPACECRAFT_LOCAL` uses an official NASA glTF asset, ACES tone mapping, sRGB textures, bounded anisotropy, directional key/fill and a restricted rim aid. Hero distance derives from model bounds, FOV, aspect and safe-area. Procedural geometry is emergency-only and truth-labeled.

### Solar System context

`SOLAR_SYSTEM_CONTEXT` uses the common ephemeris epoch and a floating visual origin. Body display radii are intentionally exaggerated and surfaced as `DISPLAY_RADIUS_EXAGGERATED`. Long-distance overview uses an explicit logarithmic transform surfaced as `LOG_DISTANCE`.

### Distance Tool

`DISTANCE_TOOL` defaults to Voyager 1 → Earth. Numeric distance, AU, light time and range rate are computed from the physical ephemeris vectors/velocities. The rendered line is a visualization of those endpoints after the selected scale transform; it is not a ruler.

### Mission trajectory

`MISSION_TRAJECTORY` reuses the existing Voyager trajectory product rather than inventing a decorative line.

## Media/usage boundary

NASA public 3D resources are used with source/credit/provenance records and without implying endorsement. NASA identifiers/logos are not used as Voyager Link branding. The project keeps an independent disclaimer and preserves the repository's existing third-party notices.
