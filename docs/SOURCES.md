# Sources

The machine-readable catalog is `data/sources.json`. Runtime fixed upstreams are JPL Horizons and the NASA Eyes DSN public XML feed. Mission status uses a versioned NASA Science snapshot. NAIF/SPICE and PDS URLs are documented for reproducible operator workflows but no large kernel, PDS bundle, or IQ capture is redistributed. CAMRAS and SETI Institute reception reports inform the hardware and carrier-detection documentation.

Every source entry records authority, URL, purpose, access pattern, cache, fallback, and parser. References to GitHub projects are conceptual only unless their license permits reuse; no code was copied from OpenWebRX+ or the unlicensed `bistromath/voyager` repository.


Additional OS VOYAGER sources:
- NASA/JPL DSN Now public status: https://eyes.nasa.gov/apps/dsn-now/dsn.html and fixed XML feed https://eyes.nasa.gov/dsn/data/dsn.xml. The public display updates about every five seconds and can misidentify spacecraft in off-nominal conditions.
- NASA Voyager instrument status snapshot: https://science.nasa.gov/mission/voyager/where-are-voyager-1-and-voyager-2-now/ (updated April 17, 2026 in the source reviewed for this release; not live telemetry).
- NASA PDS Voyager PWS VLISM Electron Density bundle: https://pds.nasa.gov/ds-view/pds/viewBundle.jsp?identifier=urn%3Anasa%3Apds%3Avoyager-pws-vlism-density (bundle metadata covers 2012-10-22 through 2025-09-01).
- NASA PDS Voyager PWS VLISM Density data collection: https://pds.nasa.gov/ds-view/pds/viewCollection.jsp?identifier=urn%3Anasa%3Apds%3Avoyager-pws-vlism-density%3Adata (the collection page reports a different stop date, 2025-04-14; the interface preserves this discrepancy).
- NASA Voyager FAQ on imaging cameras: https://science.nasa.gov/mission/voyager/frequently-asked-questions/ (camera-control software was removed after the 1990 shutdown; reactivation feasibility is uncertain).
