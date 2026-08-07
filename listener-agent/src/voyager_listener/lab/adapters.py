from __future__ import annotations
from datetime import datetime,timezone,timedelta
from pathlib import Path
from typing import Iterable,Iterator
from voyager_listener.lab.iqbus import CanonicalIQFrame
from voyager_listener.sources.sigmf_source import inspect,read_chunks

def _iso(t:datetime)->str:return t.astimezone(timezone.utc).isoformat().replace("+00:00","Z")
def frames_from_chunks(chunks:Iterable[list[complex]],*,stream_id:str,sample_rate_hz:float,center_frequency_hz:float,truth_class:str,provenance_id:str,start_time:str,datatype:str="complex64",timestamp_quality:str="HOST")->Iterator[CanonicalIQFrame]:
    origin=datetime.fromisoformat(start_time.replace("Z","+00:00"));sample_start=0
    for sequence,chunk in enumerate(chunks):
        at=origin+timedelta(seconds=sample_start/sample_rate_hz)
        yield CanonicalIQFrame(stream_id,sequence,sample_start,len(chunk),sample_rate_hz,center_frequency_hz,datatype,_iso(at),timestamp_quality,0,truth_class,provenance_id,tuple(chunk));sample_start+=len(chunk)
def sigmf_frames(meta_path:str|Path,chunk_samples:int=65536)->Iterator[CanonicalIQFrame]:
    info=inspect(meta_path);global_meta=info.metadata.get("global",{});start=global_meta.get("core:datetime") or global_meta.get("voyager:observation_time") or "1970-01-01T00:00:00Z"
    yield from frames_from_chunks(read_chunks(info,chunk_samples),stream_id=info.data_sha256[:16],sample_rate_hz=info.sample_rate_hz,center_frequency_hz=info.center_frequency_hz,truth_class=info.truth_class,provenance_id=info.data_sha256,start_time=start,datatype=info.datatype,timestamp_quality="RECORDED")
