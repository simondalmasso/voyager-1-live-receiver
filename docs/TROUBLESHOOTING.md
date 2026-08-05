# Troubleshooting

- Black screen/WebGL: use the SVG/text fallback, update graphics drivers, disable problematic extensions.
- Missing spacecraft: recenter with R; procedural model requires no network asset.
- Low FPS: select a smaller viewport, reduce OS/browser scaling, pause visual motion.
- Horizons timeout or HTML: Worker returns stale state with reason.
- DSN feed down: DSN is unavailable; the rest remains usable.
- Listener disconnected/SSE blocked: verify loopback URL, origin allowlist, port, token, and firewall.
- Invalid SigMF: verify paired filenames, datatype, sample rate, capture frequency, and byte alignment.
- Wrong frequency/sample rate: correct metadata and rerun; 8420.43 MHz is only an orienting reference.
- No tone: widen residual search, validate Doppler sign, integration time, clock, polarization, and system sensitivity.
- False candidate: increase threshold/persistence, inspect interferers outside the expected window, and run no-signal controls.
- CSP/CORS: keep listener on the documented allowlist; do not open `*`.
- Build/preview: use Node 24 LTS and `npm ci && npm run build && npm run preview`.
- Soapy/GNU Radio: install optional system packages; core tests do not require hardware.
