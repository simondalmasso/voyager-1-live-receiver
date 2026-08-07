# Real signal setup

Configure a compatible X-band telescope chain, record complex IQ as SigMF, and preserve station, UTC capture time, center frequency, sample rate, polarization, clock/reference details, and SHA-256. Obtain a topocentric Doppler prediction for the exact observatory and interval, then analyze a residual window rather than assuming 8420.43 MHz is universal.

Run `voyager-listener analyze` first, inspect residual drift and false candidates, then `serve` on loopback. Remote bind requires an explicit environment flag, TLS termination outside the listener, an origin allowlist, and preferably a bearer token held only in browser memory.
