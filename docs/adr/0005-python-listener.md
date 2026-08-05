# Python listener

Status: Accepted

## Context

CI and demo must run without hardware or paid services.

## Decision

Use a Python 3.12 stdlib core with optional scientific/hardware accelerators.

## Alternatives

Mandatory GNU Radio, browser DSP, Node listener.

## Consequences

Pure Python is slower on large captures; observatories should install NumPy/SciPy.
