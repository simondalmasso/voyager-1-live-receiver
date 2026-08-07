from __future__ import annotations
import hashlib
import json
import mmap
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

@dataclass(frozen=True)
class SigMFInfo:
    meta_path: Path
    data_path: Path
    datatype: str
    sample_rate_hz: float
    center_frequency_hz: float
    sample_count: int
    truth_class: str
    data_sha256: str
    metadata: dict[str, Any]

def sha256_file(path: Path, block: int = 1024 * 1024) -> str:
    h=hashlib.sha256()
    with path.open("rb") as handle:
        while chunk:=handle.read(block): h.update(chunk)
    return h.hexdigest()

def inspect(meta_path: str | Path) -> SigMFInfo:
    meta=Path(meta_path).resolve();raw=meta.read_bytes();doc=json.loads(raw.decode("utf-8"));global_meta=doc.get("global",{})
    datatype=global_meta.get("core:datatype")
    if datatype not in {"cf32_le","ci16_le"}: raise ValueError(f"unsupported SigMF datatype: {datatype}")
    rate=float(global_meta["core:sample_rate"]);captures=doc.get("captures") or []
    if not captures or "core:frequency" not in captures[0]: raise ValueError("SigMF capture frequency is required")
    data=meta.with_name(meta.name.replace(".sigmf-meta",".sigmf-data"))
    if data.parent!=meta.parent or not data.is_file(): raise ValueError("SigMF data file is missing")
    bytes_per=8 if datatype=="cf32_le" else 4;size=data.stat().st_size
    if size%bytes_per: raise ValueError("SigMF data size is not aligned to datatype")
    digest=sha256_file(data);declared=global_meta.get("voyager:data_sha256")
    if declared and declared.lower()!=digest: raise ValueError("SigMF data sha256 mismatch")
    truth=global_meta.get("voyager:truth_class","UNVERIFIED_SOURCE")
    if truth not in {"SYNTHETIC_TEST","RECORDED_AUTHENTIC_VERIFIED","UNVERIFIED_SOURCE"}: truth="UNVERIFIED_SOURCE"
    if truth=="RECORDED_AUTHENTIC_VERIFIED":
        required=["voyager:source_url","voyager:observatory","voyager:observation_time","voyager:license","voyager:transform_chain","voyager:data_sha256"]
        missing=[k for k in required if not global_meta.get(k)]
        if missing: raise ValueError(f"authentic SigMF missing provenance: {','.join(missing)}")
    return SigMFInfo(meta,data,datatype,rate,float(captures[0]["core:frequency"]),size//bytes_per,truth,digest,doc)

def verify_manifest(path: str | Path) -> dict[str, Any]:
    manifest_path=Path(path).resolve();doc=json.loads(manifest_path.read_text(encoding="utf-8"));meta_path=(manifest_path.parent/doc["sigmfMeta"]).resolve();data_path=(manifest_path.parent/doc["sigmfData"]).resolve()
    if meta_path.parent!=manifest_path.parent or data_path.parent!=manifest_path.parent: raise ValueError("manifest paths must remain in directory")
    if sha256_file(meta_path)!=doc.get("metadataSha256"): raise ValueError("metadata sha256 mismatch")
    if sha256_file(data_path)!=doc.get("dataSha256"): raise ValueError("data sha256 mismatch")
    required=["sourceUrl","observatory","observationTime","license","transformChain"]
    if any(not doc.get(k) for k in required): raise ValueError("manifest provenance incomplete")
    info=inspect(meta_path)
    return {"valid":True,"truthClass":"RECORDED_AUTHENTIC_VERIFIED","metadataSha256":doc["metadataSha256"],"dataSha256":doc["dataSha256"],"sourceUrl":doc["sourceUrl"],"observatory":doc["observatory"],"observationTime":doc["observationTime"],"license":doc["license"],"transformChain":doc["transformChain"],"sampleCount":info.sample_count}

def read_chunks(info: SigMFInfo,chunk_samples: int=65536,offset_samples: int=0,length_samples: int|None=None)->Iterator[list[complex]]:
    if chunk_samples<=0 or offset_samples<0: raise ValueError("invalid chunk or offset")
    bytes_per=8 if info.datatype=="cf32_le" else 4;end=min(info.sample_count,offset_samples+length_samples) if length_samples else info.sample_count
    with info.data_path.open("rb") as handle,mmap.mmap(handle.fileno(),0,access=mmap.ACCESS_READ) as mm:
        for start in range(offset_samples,end,chunk_samples):
            count=min(chunk_samples,end-start);raw=mm[start*bytes_per:(start+count)*bytes_per];fmt="<"+("ff" if info.datatype=="cf32_le" else "hh")*count;values=struct.unpack(fmt,raw);scale=1.0 if info.datatype=="cf32_le" else 1/32768.0
            yield [complex(values[i]*scale,values[i+1]*scale) for i in range(0,len(values),2)]
