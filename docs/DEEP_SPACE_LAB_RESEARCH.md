# Deep Space Lab research basis — Order 011

This implementation is clean-room and MIT-compatible. It adopts architectural and mathematical ideas, not source code, from the references named by AUD.

| Reference | License posture | Adopted pattern | Not copied / rejected |
|---|---|---|---|
| SatDump | GPL-3.0 | modular source → processors → products, live/recorded parity | no code, decoder, UI, or protocol implementation copied |
| sgoudelis/ground-station | GPL-3.0 | one bounded IQ stream with isolated consumers and drop metrics | no broker or source copied |
| Virgo | GPL-3.0 | four-tap WOLA concept, robust median/MAD RFI controls, station sensitivity context | equations reimplemented from public DSP/radiometry definitions; no source copied |
| bistromath/voyager | no declared license | scientific principles: integration, Horizons Doppler, residual search | no notebook/code/expression copied |
| SpiceyPy | MIT | optional offline geometry verification tooling boundary | browser/Worker do not require SpiceyPy |
| gr-satellites / GRCon workshop | GPL/reference material | plugin boundaries and GNU Radio adapter patterns | no claim that an existing CCSDS/Turbo decoder decodes current Voyager 1 |

Primary mathematical definitions used by the project are standard public equations: Fourier transform/FFT, windowed overlap processing, WGS84 topocentric transforms, classical narrowband Doppler, antenna effective aperture/gain, G/T, SEFD, and the radiometer equation. The project does not claim absolute dBm without a traceable calibration chain.
