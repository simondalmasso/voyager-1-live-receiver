# Sources

The machine-readable catalog is `data/sources.json`. Runtime fixed upstreams are JPL Horizons and the NASA Eyes DSN public XML feed. Mission status uses a versioned NASA Science snapshot. NAIF/SPICE and PDS URLs are documented for reproducible operator workflows but no large kernel, PDS bundle, or IQ capture is redistributed. CAMRAS and SETI Institute reception reports inform the hardware and carrier-detection documentation.

Every source entry records authority, URL, purpose, access pattern, cache, fallback, and parser. References to GitHub projects are conceptual only unless their license permits reuse; no code was copied from OpenWebRX+ or the unlicensed `bistromath/voyager` repository.
