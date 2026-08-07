# Native WebGL and ES modules

Status: Accepted

## Context

The repository began empty; zero runtime dependencies minimize supply-chain risk, install failure, and bundle size while still delivering a real navigable 3D scene.

## Decision

Use a dependency-free native WebGL renderer instead of React Three Fiber for the initial audited core.

## Alternatives

React Three Fiber, Three.js, static 2D only.

## Consequences

More local rendering code is owned by the project; official-model loading can be added behind the same scene interface.
