from __future__ import annotations
from dataclasses import dataclass, asdict
import math
import statistics
from .fft import hann, shifted_power_db
from .doppler import dedrift
@dataclass(frozen=True)
class Detection:
    state: str
    observed_frequency_hz: float | None
    expected_frequency_hz: float
    residual_hz: float | None
    snr_db: float | None
    confidence: float
    integration_seconds: float
    sample_count: int
    dropped_samples: int = 0
    def to_dict(self) -> dict[str, object]:
        return asdict(self)

def analyze(samples: list[complex], sample_rate_hz: float, center_frequency_hz: float, expected_frequency_hz: float, drift_hz_s: float = 0.0, fft_size: int = 1024, search_half_width_hz: float = 250.0, threshold_db: float = 8.0) -> tuple[Detection, list[float]]:
    if sample_rate_hz <= 0 or fft_size <= 0 or fft_size & (fft_size - 1):
        raise ValueError("invalid sample rate or FFT size")
    if len(samples) < fft_size:
        raise ValueError("not enough samples")
    offset = expected_frequency_hz - center_frequency_hz
    corrected = dedrift(samples, sample_rate_hz, offset_hz=offset, drift_hz_s=drift_hz_s)
    window = hann(fft_size)
    integrated = [0.0] * fft_size
    segments = 0
    for start in range(0, len(corrected) - fft_size + 1, fft_size):
        block = [corrected[start + i] * window[i] for i in range(fft_size)]
        power = shifted_power_db(block)
        for i, value in enumerate(power):
            integrated[i] += 10 ** (value / 10)
        segments += 1
    spectrum = [10 * math.log10(max(1e-20, value / segments)) for value in integrated]
    bin_hz = sample_rate_hz / fft_size
    center_bin = fft_size // 2
    half_bins = max(2, min(center_bin - 1, int(search_half_width_hz / bin_hz)))
    lo, hi = center_bin - half_bins, center_bin + half_bins + 1
    peak_bin = max(range(lo, hi), key=spectrum.__getitem__)
    guard = max(2, int(2.5))
    noise_bins = [spectrum[i] for i in range(lo, hi) if abs(i - peak_bin) > guard]
    noise = statistics.median(noise_bins)
    mad = statistics.median(abs(v - noise) for v in noise_bins) or 0.1
    snr = spectrum[peak_bin] - noise
    z = max(0.0, (snr - threshold_db) / max(1.0, 1.4826 * mad))
    confidence = 1 - math.exp(-z)
    observed = expected_frequency_hz + (peak_bin - center_bin) * bin_hz
    state = "DETECTED" if snr >= threshold_db and segments >= 3 and confidence >= 0.7 else "CANDIDATE" if snr >= threshold_db * 0.65 else "SEARCHING"
    return Detection(state, observed if state != "SEARCHING" else None, expected_frequency_hz, observed - expected_frequency_hz if state != "SEARCHING" else None, snr, confidence, len(samples) / sample_rate_hz, len(samples)), spectrum
