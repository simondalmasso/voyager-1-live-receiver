from __future__ import annotations
from collections.abc import Iterable
import cmath
import math
C_M_S = 299_792_458.0

def classical_observed_frequency(reference_hz: float, radial_velocity_m_s: float) -> float:
    return reference_hz * (1.0 - radial_velocity_m_s / C_M_S)

def relativistic_observed_frequency(reference_hz: float, radial_velocity_m_s: float) -> float:
    beta = radial_velocity_m_s / C_M_S
    if abs(beta) >= 1:
        raise ValueError("radial velocity must be subluminal")
    return reference_hz * math.sqrt((1 - beta) / (1 + beta))

def dedrift(samples: Iterable[complex], sample_rate_hz: float, offset_hz: float = 0.0, drift_hz_s: float = 0.0, start_index: int = 0) -> list[complex]:
    result = []
    for local, sample in enumerate(samples):
        i = start_index + local
        t = i / sample_rate_hz
        phase = 2 * math.pi * (offset_hz * t + 0.5 * drift_hz_s * t * t)
        result.append(sample * cmath.exp(-1j * phase))
    return result
