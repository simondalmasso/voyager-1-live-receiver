# Radio architecture

IQ chunks pass through optional offset/drift correction, Hann windowing, FFT, incoherent integration, robust median noise estimation, bounded residual search, thresholding, and confidence. The browser receives only reduced spectra and detector metrics. The pure-Python radix-2 core provides deterministic CI; NumPy/SciPy are optional accelerators for large captures.

A real path requires a suitable radiotelescope, stable frequency reference, X-band receiver/downconverter, SDR, accurate timing, and observatory coordinates. A domestic antenna/SDR is not represented as sufficient.
