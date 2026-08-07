from __future__ import annotations
import statistics
from dataclasses import dataclass

@dataclass(frozen=True,slots=True)
class RFIMask:
    masked_bins:tuple[int,...]
    reasons:dict[int,str]
    method:str="MEDIAN_MAD_STATIONARY"
    def as_dict(self):return {"method":self.method,"maskedBins":list(self.masked_bins),"reasons":{str(k):v for k,v in self.reasons.items()}}

def median_mad(values:list[float])->tuple[float,float]:
    if not values:return 0.0,0.0
    med=statistics.median(values); mad=statistics.median(abs(v-med) for v in values)
    return med,max(mad,1e-9)

def build_stationary_mask(history:list[list[float]],threshold_mad:float=8.0,max_span_db:float=1.5)->RFIMask:
    if not history:return RFIMask((),{})
    bins=len(history[0]); reasons={}; global_values=[v for row in history for v in row]; floor,mad=median_mad(global_values)
    for i in range(bins):
        col=[row[i] for row in history if len(row)==bins]
        if len(col)<2:continue
        span=max(col)-min(col); med=statistics.median(col); neighbors=[]
        for j in (i-2,i-1,i+1,i+2):
            if 0<=j<bins: neighbors.extend(row[j] for row in history)
        neighbor=statistics.median(neighbors) if neighbors else floor
        if med>neighbor+threshold_mad*mad and span<=max_span_db: reasons[i]="persistent-stationary-excess"
    return RFIMask(tuple(sorted(reasons)),reasons)

def masked_copy(values:list[float],mask:RFIMask,replacement:float|None=None)->list[float]:
    out=list(values); repl=statistics.median(values) if replacement is None and values else (replacement or 0.0)
    for i in mask.masked_bins:
        if 0<=i<len(out):out[i]=repl
    return out

def candidate_score(*,frequency_residual_hz:float|None,drift_residual_hz_s:float|None,persistence:float|None,snr_db:float|None,stationary_rfi:bool|None,off_target_conflict:bool|None,frequency_window_hz:float=50.0,drift_window_hz_s:float=1.0)->dict:
    values={"frequencyResidualHz":frequency_residual_hz,"driftResidualHzS":drift_residual_hz_s,"persistence":persistence,"snrDb":snr_db,"stationaryRfi":stationary_rfi,"offTargetConflict":off_target_conflict};missing=[name for name,value in values.items() if value is None]
    if missing:return {"score":None,"frequencyConsistency":None,"driftConsistency":None,"persistence":persistence,"snrComponent":None,"stationaryRfi":stationary_rfi,"offTargetConflict":off_target_conflict,"classification":"INSUFFICIENT_EVIDENCE","missing":missing,"measured":values}
    freq=max(0.0,1-abs(float(frequency_residual_hz))/max(frequency_window_hz,1e-9)); drift=max(0.0,1-abs(float(drift_residual_hz_s))/max(drift_window_hz_s,1e-9)); snr=max(0.0,min(1.0,(float(snr_db)+3)/18)); persist=max(0.0,min(1.0,float(persistence))); score=.3*freq+.25*drift+.25*persist+.2*snr
    if stationary_rfi:score*=.2
    if off_target_conflict:score*=.35
    return {"score":round(score,6),"frequencyConsistency":freq,"driftConsistency":drift,"persistence":persist,"snrComponent":snr,"stationaryRfi":stationary_rfi,"offTargetConflict":off_target_conflict,"classification":"CANDIDATE" if score>=.65 and not stationary_rfi and not off_target_conflict else "REJECTED_OR_WEAK","missing":[],"measured":values}
