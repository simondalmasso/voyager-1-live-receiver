from __future__ import annotations
from statistics import fmean

def compare_observations(observations:list[dict],level:int=1)->dict:
    if level not in {0,1,2}:raise ValueError("LEVEL_3 coherent fusion is intentionally unsupported")
    stations=[o.get("stationId","unknown") for o in observations]
    base={"level":level,"stations":stations,"claim":"INDEPENDENT_OBSERVATIONS" if level==0 else "TIME_FREQUENCY_EVIDENCE_COMPARISON" if level==1 else "INCOHERENT_STATISTICAL_FUSION","coherentCombination":False}
    if not observations:return {**base,"count":0}
    scores=[float(o.get("score",0)) for o in observations]
    if level==2:base["fusedScore"]=fmean(scores);base["method"]="arithmetic mean of independent normalized evidence scores; no dB gain claim"
    else:base["scores"]=scores
    return {**base,"count":len(observations)}
