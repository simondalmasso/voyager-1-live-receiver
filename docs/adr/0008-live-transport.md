# SSE and HTTP live transport

Status: Accepted

## Context

The browser needs live updates without raw IQ or stateful paid infrastructure.

## Decision

Implement SSE plus HTTP snapshot for zero-dependency reduced products.

## Alternatives

WebSocket-first, Worker proxy, raw IQ.

## Consequences

A WebSocket adapter can be added later without changing SignalSnapshotV1.
