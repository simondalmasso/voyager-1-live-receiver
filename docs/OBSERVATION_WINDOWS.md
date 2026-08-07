# Observation windows

The browser/Worker advisory path computes WGS84/GMST topocentric azimuth/elevation from the current JPL Horizons geocentric state and linearly propagates the short planning interval with the current velocity. It reports start/peak/end, expected classical Doppler curve, carrier region, UTC timestamps and provenance, and labels the approximation.

Offline reproducibility is provided by `voyager-science generate-observation-window`; SPICE/Horizons cross-check evidence remains the independent geometry gate. Voyager is treated as a deep-space target: no TLE/LEO model and no rotator control are used.
