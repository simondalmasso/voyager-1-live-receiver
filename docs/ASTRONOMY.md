# Astronomy

The Worker queries Horizons object `-31`, center `500@399`, vector ephemeris, ICRF, frame plane, km/s, and no light-time correction for geometric state. Distance is the Euclidean norm of the relative vector. One-way light time is distance divided by the exact speed of light, 299,792.458 km/s. AU conversion uses 149,597,870.7 km. Radial range rate is the dot product of velocity and the normalized line of sight.

The browser never calls Horizons directly. Current state is cached for ten minutes and may fall back to a visibly stale embedded seed. Orientation is `EARTH_POINTING_DERIVED`, not an exact CK attitude.
