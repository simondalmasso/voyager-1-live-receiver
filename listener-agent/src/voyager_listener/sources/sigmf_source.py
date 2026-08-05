from __future__ import annotations
import json
import mmap
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator
@dataclass(frozen=True)
class SigMFInfo:
    meta_path: Path
    data_path: Path
    datatype: str
    sample_rate_hz: float
    center_frequency_hz: float
    sample_count: int

def inspect(meta_path: str | Path) -> SigMFInfo:
    meta = Path(meta_path).resolve()
    doc = json.loads(meta.read_text(encoding="utf-8"))
    global_meta = doc.get("global", {})
    datatype = global_meta.get("core:datatype")
    if datatype not in {"cf32_le", "ci16_le"}:
        raise ValueError(f"unsupported SigMF datatype: {datatype}")
    rate = float(global_meta["core:sample_rate"])
    captures = doc.get("captures") or []
    if not captures or "core:frequency" not in captures[0]:
        raise ValueError("SigMF capture frequency is required")
    data = meta.with_name(meta.name.replace(".sigmf-meta", ".sigmf-data"))
    if data.parent != meta.parent or not data.is_file():
        raise ValueError("SigMF data file is missing")
    bytes_per = 8 if datatype == "cf32_le" else 4
    size = data.stat().st_size
    if size % bytes_per:
        raise ValueError("SigMF data size is not aligned to datatype")
    return SigMFInfo(meta, data, datatype, rate, float(captures[0]["core:frequency"]), size // bytes_per)

def read_chunks(info: SigMFInfo, chunk_samples: int = 65536, offset_samples: int = 0, length_samples: int | None = None) -> Iterator[list[complex]]:
    if chunk_samples <= 0 or offset_samples < 0:
        raise ValueError("invalid chunk or offset")
    bytes_per = 8 if info.datatype == "cf32_le" else 4
    end = min(info.sample_count, offset_samples + length_samples) if length_samples else info.sample_count
    with info.data_path.open("rb") as handle, mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        for start in range(offset_samples, end, chunk_samples):
            count = min(chunk_samples, end - start)
            raw = mm[start * bytes_per:(start + count) * bytes_per]
            fmt = "<" + ("ff" if info.datatype == "cf32_le" else "hh") * count
            values = struct.unpack(fmt, raw)
            scale = 1.0 if info.datatype == "cf32_le" else 1 / 32768.0
            yield [complex(values[i] * scale, values[i + 1] * scale) for i in range(0, len(values), 2)]
