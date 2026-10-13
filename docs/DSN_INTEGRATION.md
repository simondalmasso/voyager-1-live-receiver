# DSN integration

Voyager Link reads the fixed NASA Eyes DSN Now XML feed at https://eyes.nasa.gov/dsn/data/dsn.xml. The public page says the status feed updates about every five seconds. The Worker uses a short timeout, rejects DTD/entity declarations, limits payload size, sanitizes strings, tolerates optional/missing elements, and does not accept arbitrary upstream URLs.

The XML schema has dish elements with nested target, downSignal, and upSignal elements. A target is commonly represented by a name attribute such as target name="Voyager 1"; directional signal elements carry active, band, dataRate, power, and spacecraft attributes. The parser reads those nested attributes instead of assuming target is plain element text.

The API distinguishes:
- DSN_LIVE_PUBLIC_STATUS: the public snapshot explicitly lists Voyager 1 as a target or signal spacecraft.
- UNAVAILABLE with feedAvailable=true: the feed was parsed, but this snapshot had no explicit Voyager 1 target match. This is not proof that NASA has no contact.
- UNAVAILABLE without feedAvailable=true: the public feed could not be fetched or parsed.

When explicit signal metadata is present, upSignal and downSignal activity are shown separately. A target listing alone is not described as an active downlink. NASA warns that DSN Now can misidentify a spacecraft in off-nominal situations, so this is public ground-network status, not definitive spacecraft telemetry or independent local RF reception. It exposes no control, scheduling, credentials, or uplink.
