from __future__ import annotations
from collections import deque
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Iterable, Iterator

TRUTH_CLASSES={"TELESCOPE_LIVE_VERIFIED","RECORDED_AUTHENTIC_VERIFIED","SYNTHETIC_TEST","UNVERIFIED_SOURCE"}
TIMESTAMP_QUALITIES={"HARDWARE","HOST","RECORDED","SYNTHETIC"}

def _utc(value: str) -> str:
    parsed=datetime.fromisoformat(value.replace("Z","+00:00"))
    if parsed.tzinfo is None: raise ValueError("timestamp must include timezone")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00","Z")

@dataclass(frozen=True, slots=True)
class CanonicalIQFrame:
    stream_id: str
    sequence: int
    sample_start: int
    sample_count: int
    sample_rate_hz: float
    center_frequency_hz: float
    datatype: str
    timestamp_start: str
    timestamp_quality: str
    dropped_samples_before: int
    source_truth_class: str
    source_provenance_id: str
    samples: tuple[complex,...]
    replay_received_at: str|None=None
    def __post_init__(self):
        if not self.stream_id or not self.source_provenance_id: raise ValueError("stream/provenance id required")
        if self.sequence<0 or self.sample_start<0 or self.sample_count<0 or self.dropped_samples_before<0: raise ValueError("negative IQ counters")
        if self.sample_count != len(self.samples): raise ValueError("sample_count mismatch")
        if self.sample_rate_hz<=0 or not self.center_frequency_hz: raise ValueError("invalid sample/frequency metadata")
        if self.datatype not in {"cf32_le","ci16_le","complex64"}: raise ValueError("unsupported canonical IQ datatype")
        if self.timestamp_quality not in TIMESTAMP_QUALITIES: raise ValueError("invalid timestamp quality")
        if self.source_truth_class not in TRUTH_CLASSES: raise ValueError("invalid source truth class")
        _utc(self.timestamp_start)
        if self.replay_received_at: _utc(self.replay_received_at)

@dataclass(slots=True)
class ConsumerMetrics:
    accepted_frames:int=0
    dropped_frames:int=0
    sequence_gaps:int=0
    last_sequence:int|None=None

class IQConsumer:
    def __init__(self,name:str,capacity:int=8):
        if capacity<1: raise ValueError("capacity must be >=1")
        self.name=name; self.capacity=capacity; self._queue:deque[CanonicalIQFrame]=deque(); self.metrics=ConsumerMetrics(); self.closed=False
    def put(self,frame:CanonicalIQFrame)->None:
        if self.closed: return
        last=self.metrics.last_sequence
        if last is not None and frame.sequence>last+1: self.metrics.sequence_gaps += frame.sequence-last-1
        self.metrics.last_sequence=frame.sequence
        if len(self._queue)>=self.capacity:
            self._queue.popleft(); self.metrics.dropped_frames+=1
        self._queue.append(frame); self.metrics.accepted_frames+=1
    def get(self)->CanonicalIQFrame|None:
        return self._queue.popleft() if self._queue else None
    def drain(self)->list[CanonicalIQFrame]:
        out=list(self._queue); self._queue.clear(); return out
    def close(self)->None: self.closed=True; self._queue.clear()
    def snapshot(self)->dict:
        return {"name":self.name,"capacity":self.capacity,"queued":len(self._queue),"acceptedFrames":self.metrics.accepted_frames,"droppedFrames":self.metrics.dropped_frames,"sequenceGaps":self.metrics.sequence_gaps,"closed":self.closed}

class CanonicalIQBus:
    def __init__(self): self._consumers:dict[str,IQConsumer]={}; self._last_by_stream:dict[str,int]={}; self.published_frames=0; self.sequence_gaps=0; self.closed=False
    def subscribe(self,name:str,capacity:int=8)->IQConsumer:
        if self.closed: raise RuntimeError("bus closed")
        if name in self._consumers: raise ValueError("duplicate consumer")
        c=IQConsumer(name,capacity); self._consumers[name]=c; return c
    def publish(self,frame:CanonicalIQFrame)->None:
        if self.closed: raise RuntimeError("bus closed")
        last=self._last_by_stream.get(frame.stream_id)
        if last is not None:
            if frame.sequence<=last: raise ValueError("non-monotonic sequence")
            if frame.sequence>last+1: self.sequence_gaps += frame.sequence-last-1
        self._last_by_stream[frame.stream_id]=frame.sequence; self.published_frames+=1
        for consumer in self._consumers.values(): consumer.put(frame)
    def close(self)->None:
        if self.closed:return
        self.closed=True
        for c in self._consumers.values(): c.close()
    def snapshot(self)->dict:
        return {"publishedFrames":self.published_frames,"sequenceGaps":self.sequence_gaps,"closed":self.closed,"consumers":{n:c.snapshot() for n,c in self._consumers.items()}}

def replay_frames(frames:Iterable[CanonicalIQFrame],received_at:callable|None=None)->Iterator[CanonicalIQFrame]:
    now=received_at or (lambda: datetime.now(timezone.utc).isoformat().replace("+00:00","Z"))
    for frame in frames:
        yield replace(frame,replay_received_at=now())
