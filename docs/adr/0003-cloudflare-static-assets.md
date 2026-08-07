# Cloudflare Static Assets

Status: Accepted

## Context

The product needs one zero-cost deployable unit and honest local preview.

## Decision

Serve the SPA and API as one Worker with ASSETS and `/api/*` worker-first.

## Alternatives

Workers Sites, Pages plus separate API.

## Consequences

No paid storage or additional service is required.
