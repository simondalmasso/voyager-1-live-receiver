# DSN integration

The Worker fetches the fixed NASA Eyes DSN XML URL with a short timeout, rejects DTD/entity declarations, limits payload size, sanitizes strings, tolerates unknown elements, and reports activity only when the feed explicitly identifies Voyager 1. A missing match is `UNAVAILABLE`, not an inferred idle or active session. This integration is public status only and provides no control, scheduling, credentials, or uplink.
