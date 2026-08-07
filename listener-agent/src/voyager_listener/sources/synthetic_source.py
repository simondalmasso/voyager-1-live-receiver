from __future__ import annotations
import cmath
import math
import random
import struct
from pathlib import Path
from typing import Iterator

def generate(sample_rate_hz: float = 4096.0, duration_seconds: float = 8.0, tone_offset_hz: float = 48.0, drift_hz_s: float = 0.2, amplitude: float = 0.22, noise_std: float = 0.55, seed: int = 1701, include_tone: bool = True) -> list[complex]:
    rng = random.Random(seed)
    count = int(sample_rate_hz * duration_seconds)
    result = []
    for i in range(count):
        t = i / sample_rate_hz
        phase = 2 * math.pi * (tone_offset_hz * t + 0.5 * drift_hz_s * t * t)
        tone = amplitude * cmath.exp(1j * phase) if include_tone else 0j
        noise = complex(rng.gauss(0, noise_std), rng.gauss(0, noise_std))
        result.append(tone + noise)
    return result

def write_cf32(path: Path, samples: list[complex]) -> str:
    import hashlib
    digest = hashlib.sha256()
    with path.open("wb") as handle:
        for sample in samples:
            chunk = struct.pack("<ff", sample.real, sample.imag)
            handle.write(chunk)
            digest.update(chunk)
    return digest.hexdigest()

def chunks(samples: list[complex], size: int) -> Iterator[list[complex]]:
    for start in range(0, len(samples), size):
        yield samples[start:start + size]
