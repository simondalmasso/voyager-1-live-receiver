# Floating origin

Status: Accepted

## Context

Astronomical kilometer magnitudes exceed stable direct scene coordinates.

## Decision

Keep Voyager at local origin and transform/compress external coordinates before rendering.

## Alternatives

Direct absolute coordinates, arbitrary tiny global scale.

## Consequences

Numerical mission state remains separate from visual coordinates.
