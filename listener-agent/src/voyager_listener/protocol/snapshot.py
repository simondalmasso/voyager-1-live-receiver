from __future__ import annotations
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any
from voyager_listener.dsp.detector import Detection
from voyager_listener.provenance import Provenance

def signal_snapshot(detection: Detection, spectrum: list[float], *, stream_id: str, sequence: int, source_mode: str, station_id: str, station_name: str, started_at: str, sample_rate_hz: float, center_frequency_hz: float, datatype: str, bin_width_hz: float, provenance: Provenance) -> dict[str, Any]:
    if source_mode not in {"TELESCOPE_LIVE", "RECORDED_AUTHENTIC", "SYNTHETIC_TEST"}:
        raise ValueError("invalid source mode")
    analysis = {
        "expectedFrequencyHz": detection.expected_frequency_hz,
        "observedFrequencyHz": detection.observed_frequency_hz,
        "residualHz": detection.residual_hz,
        "snrDb": detection.snr_db,
        "confidence": detection.confidence,
        "state": detection.state,
        "integrationSeconds": detection.integration_seconds,
        "droppedSamples": detection.dropped_samples,
    }
    return {
        "schemaVersion": 1,
        "streamId": stream_id,
        "sequence": sequence,
        "sourceMode": source_mode,
        "station": {"id": station_id, "name": station_name},
        "capture": {"startedAt": started_at, "sampleRateHz": sample_rate_hz, "centerFrequencyHz": center_frequency_hz, "datatype": datatype},
        "analysis": analysis,
        "spectrum": {"startHz": center_frequency_hz - sample_rate_hz / 2, "binWidthHz": bin_width_hz, "valuesDb": [round(v, 4) for v in spectrum]},
        "provenance": provenance.to_wire(),
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
