# SPICE trajectory pipeline V2

`scripts/generate-spice.py --bootstrap` downloads official kernels, records byte length plus SHA-256/SHA-512, generates a reduced J2000 heliocentric trajectory, captures three official Horizons geocentric references and checks SPICE/Horizons differences against explicit tolerances. HGA boresight alignment must have dot product at least `0.999999`.

Normal CI runs the script without `--bootstrap`. It redownloads or reuses the pinned kernels, rejects hash drift, regenerates deterministic outputs and compares them byte-for-byte with committed reduced products. BSP files stay in `.cache/spice` and Actions artifacts, not Git.
