from __future__ import annotations
import cmath
import math
from collections.abc import Sequence

def hann(size: int) -> list[float]:
    if size < 2:
        return [1.0] * size
    return [0.5 - 0.5 * math.cos(2 * math.pi * i / (size - 1)) for i in range(size)]

def fft(values: Sequence[complex]) -> list[complex]:
    n = len(values)
    if n == 0 or n & (n - 1):
        raise ValueError("FFT length must be a non-zero power of two")
    out = list(values)
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit
        if i < j:
            out[i], out[j] = out[j], out[i]
    length = 2
    while length <= n:
        angle = -2j * math.pi / length
        wlen = cmath.exp(angle)
        half = length // 2
        for i in range(0, n, length):
            w = 1 + 0j
            for k in range(half):
                u, v = out[i + k], out[i + k + half] * w
                out[i + k], out[i + k + half] = u + v, u - v
                w *= wlen
        length <<= 1
    return out

def shifted_power_db(values: Sequence[complex], floor: float = 1e-20) -> list[float]:
    transformed = fft(values)
    half = len(transformed) // 2
    shifted = transformed[half:] + transformed[:half]
    return [10 * math.log10(max(floor, abs(value) ** 2 / len(values) ** 2)) for value in shifted]
