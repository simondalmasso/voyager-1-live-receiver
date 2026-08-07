from __future__ import annotations
from datetime import datetime,timezone,timedelta
from pathlib import Path
from typing import Iterable,Iterator
from voyager_listener.lab.iqbus import CanonicalIQFrame
from voyager_listener.sources.sigmf_source import inspect,read_chunks

def _iso(t:datetime)->str:return t.astimezone(timezone.utc).isoformat().replace("+00:00","Z")
def _now()->str:return _iso(datetime.now(timezone.utc))
def frames_from_chunks(chunks:Iterable[list[complex]],*,stream_id:str,sample_rate_hz:float,center_frequency_hz:float,truth_class:str,provenance_id:str,start_time:str,datatype:str="complex64",timestamp_quality:str="HOST")->Iterator[CanonicalIQFrame]:
    origin=datetime.fromisoformat(start_time.replace("Z","+00:00"));sample_start=0
    for sequence,chunk in enumerate(chunks):
        at=origin+timedelta(seconds=sample_start/sample_rate_hz)
        yield CanonicalIQFrame(stream_id,sequence,sample_start,len(chunk),sample_rate_hz,center_frequency_hz,datatype,_iso(at),timestamp_quality,0,truth_class,provenance_id,tuple(chunk));sample_start+=len(chunk)
def sigmf_frames(meta_path:str|Path,chunk_samples:int=65536,*,truth_class:str|None=None,provenance_id:str|None=None)->Iterator[CanonicalIQFrame]:
    info=inspect(meta_path);global_meta=info.metadata.get("global",{});captures=info.metadata.get("captures",[]);start=(captures[0].get("core:datetime") if captures else None) or global_meta.get("core:datetime") or global_meta.get("voyager:observation_time") or "1970-01-01T00:00:00Z";truth=truth_class or info.truth_class;prov=provenance_id or info.data_sha256
    yield from frames_from_chunks(read_chunks(info,chunk_samples),stream_id=info.data_sha256[:16],sample_rate_hz=info.sample_rate_hz,center_frequency_hz=info.center_frequency_hz,truth_class=truth,provenance_id=prov,start_time=start,datatype=info.datatype,timestamp_quality="RECORDED")
def soapy_frames(driver:str,sample_rate_hz:float,center_frequency_hz:float,*,stream_id:str="soapy-live",provenance_id:str="local-soapysdr",chunk_samples:int=16384,truth_class:str="UNVERIFIED_SOURCE",**settings:object)->Iterator[CanonicalIQFrame]:
    from voyager_listener.sources.soapy_source import cf32_chunks
    chunks=cf32_chunks(driver,sample_rate_hz,center_frequency_hz,chunk_samples,**settings)
    yield from frames_from_chunks(chunks,stream_id=stream_id,sample_rate_hz=sample_rate_hz,center_frequency_hz=center_frequency_hz,truth_class=truth_class,provenance_id=provenance_id,start_time=_now(),datatype="cf32_le",timestamp_quality="HARDWARE")
def gnuradio_frames(host:str="127.0.0.1",port:int=8766,*,sample_rate_hz:float,center_frequency_hz:float,stream_id:str="gnuradio-live",provenance_id:str="local-gnuradio-udp",truth_class:str="UNVERIFIED_SOURCE")->Iterator[CanonicalIQFrame]:
    from voyager_listener.sources.gnuradio_bridge import udp_cf32
    chunks=udp_cf32(host,port)
    yield from frames_from_chunks(chunks,stream_id=stream_id,sample_rate_hz=sample_rate_hz,center_frequency_hz=center_frequency_hz,truth_class=truth_class,provenance_id=provenance_id,start_time=_now(),datatype="cf32_le",timestamp_quality="HOST")
