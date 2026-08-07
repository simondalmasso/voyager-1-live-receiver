from __future__ import annotations
import json,urllib.request
from datetime import datetime,timedelta,timezone
from pathlib import Path
from voyager_listener.cli import _horizons_observer_rows
from voyager_listener.ephemeris.horizons import topocentric_query
from voyager_listener.dsp.doppler import classical_observed_frequency
AU_KM=149597870.7
CARRIER=8420430000.0
RR_TOL_KM_S=0.00075
SEARCH_WINDOW_HZ=50.0
CASES=[
    {"id":"cordoba","lat":-31.4,"lon":-64.2,"elevationM":500,"at":"2026-08-07T12:00:00Z"},
    {"id":"goldstone","lat":35.2472,"lon":-116.7933,"elevationM":1000,"at":"2026-01-15T03:00:00Z"},
    {"id":"canberra","lat":-35.3985,"lon":148.9819,"elevationM":700,"at":"2025-11-20T18:00:00Z"},
]
def dt(value:str)->datetime:return datetime.fromisoformat(value.replace('Z','+00:00')).astimezone(timezone.utc)
def fmt(value:datetime)->str:return value.strftime('%Y-%m-%d %H:%M:%S')
def run_case(case:dict)->dict:
    start=dt(case['at']);stop=start+timedelta(minutes=6);url=topocentric_query(start_time=fmt(start),stop_time=fmt(stop),latitude_deg=case['lat'],longitude_deg=case['lon'],elevation_m=case['elevationM']);req=urllib.request.Request(url,headers={'User-Agent':'voyager-order011-r2-science-gate/1.0'});text=urllib.request.urlopen(req,timeout=20).read(2_000_000).decode('utf-8','replace');rows=_horizons_observer_rows(text)
    if len(rows)<5:raise RuntimeError(f"{case['id']}: insufficient Horizons rows")
    mid=len(rows)//2;first,last,center=rows[0],rows[-1],rows[mid];elapsed=(dt(last['observedAt'])-dt(first['observedAt'])).total_seconds();fd=((last['rangeAu']-first['rangeAu'])*AU_KM)/elapsed;error=abs(fd-center['rangeRateKmS']);continuity=max(abs(rows[i+1]['rangeRateKmS']-rows[i]['rangeRateKmS']) for i in range(len(rows)-1));doppler_error_hz=CARRIER*error/299792.458
    for cur in rows:
        doppler=classical_observed_frequency(CARRIER,cur['rangeRateKmS']*1000)-CARRIER
        if cur['rangeRateKmS']>0 and not doppler<0:raise RuntimeError(f"{case['id']}: Doppler sign mismatch")
        if cur['rangeRateKmS']<0 and not doppler>0:raise RuntimeError(f"{case['id']}: Doppler sign mismatch")
    if error>=RR_TOL_KM_S:raise RuntimeError(f"{case['id']}: long-baseline finite-difference range-rate error {error} km/s")
    if continuity>=0.05:raise RuntimeError(f"{case['id']}: discontinuous range-rate curve")
    return {**case,"rowCount":len(rows),"finiteDifferenceBaselineSeconds":elapsed,"centerRangeRateKmS":center['rangeRateKmS'],"finiteDifferenceRangeRateKmS":fd,"maxRangeRateErrorKmS":error,"maxEquivalentDopplerErrorHz":doppler_error_hz,"maxOneMinuteRangeRateChangeKmS":continuity,"sourceUrl":url,"pass":True}
def main()->None:
    results=[run_case(case) for case in CASES];max_rr=max(x['maxRangeRateErrorKmS'] for x in results);max_hz=max(x['maxEquivalentDopplerErrorHz'] for x in results);tol_hz=CARRIER*RR_TOL_KM_S/299792.458;doc={"schemaVersion":1,"authority":"JPL Horizons OBSERVER quantity 20","caseCount":len(results),"carrierHz":CARRIER,"rangeRateToleranceKmS":RR_TOL_KM_S,"equivalentDopplerToleranceHz":tol_hz,"declaredSearchWindowHz":SEARCH_WINDOW_HZ,"maxRangeRateErrorKmS":max_rr,"maxEquivalentDopplerErrorHz":max_hz,"toleranceSmallerThanSearchWindow":tol_hz<SEARCH_WINDOW_HZ,"method":"symmetric six-minute finite difference of Horizons range compared with center-epoch Horizons range-rate; longer baseline suppresses published range quantization","cases":results,"pass":all(x['pass'] for x in results) and tol_hz<SEARCH_WINDOW_HZ and max_hz<tol_hz}
    out=Path('artifacts/order011-r2/horizons-observer-crosscheck.json');out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n',encoding='utf-8');print(json.dumps(doc,sort_keys=True));raise SystemExit(0 if doc['pass'] else 2)
if __name__=='__main__':main()
