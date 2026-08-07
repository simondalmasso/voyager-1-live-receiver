from __future__ import annotations
import argparse,json
from pathlib import Path
from voyager_listener.lab.evidence import create_bundle,verify_bundle
from voyager_listener.lab.observation import observation_window
from voyager_listener.lab.station import StationInputs,evaluate_station

def dump(v): print(json.dumps(v,sort_keys=True,separators=(",",":")))
def main():
    p=argparse.ArgumentParser(prog="voyager-science");s=p.add_subparsers(dest="cmd",required=True)
    g=s.add_parser("verify-geometry");g.add_argument("--crosscheck",default="artifacts/science-evidence/spice-horizons-crosscheck.json")
    c=s.add_parser("crosscheck-spice-horizons");c.add_argument("--crosscheck",default="artifacts/science-evidence/spice-horizons-crosscheck.json")
    w=s.add_parser("generate-observation-window");w.add_argument("states");w.add_argument("--lat",type=float,required=True);w.add_argument("--lon",type=float,required=True);w.add_argument("--elevation",type=float,default=0);w.add_argument("--carrier-hz",type=float,default=8420430000);w.add_argument("--min-elevation",type=float,default=10)
    st=s.add_parser("station-physics");st.add_argument("--diameter",type=float);st.add_argument("--efficiency",type=float);st.add_argument("--effective-area",type=float);st.add_argument("--system-temperature",type=float);st.add_argument("--noise-figure-db",type=float);st.add_argument("--bandwidth",type=float);st.add_argument("--integration",type=float);st.add_argument("--frequency",type=float,default=8420430000);st.add_argument("--polarization",default="single");st.add_argument("--calibrated",action="store_true")
    e=s.add_parser("evidence-fixture");e.add_argument("--output",required=True);e.add_argument("--verify",action="store_true")
    a=p.parse_args()
    if a.cmd in {"verify-geometry","crosscheck-spice-horizons"}:
        doc=json.loads(Path(a.crosscheck).read_text());cross=doc.get("horizonsCrosscheck",{});ok=bool(cross.get("pass")) and int(doc.get("sampleCount",0))>=1;dump({"schemaVersion":1,"command":a.cmd,"pass":ok,"sampleCount":doc.get("sampleCount"),"horizonsCrosscheck":cross});raise SystemExit(0 if ok else 2)
    if a.cmd=="generate-observation-window":
        states=json.loads(Path(a.states).read_text());states=states.get("states",states);dump(observation_window(states,{"lat":a.lat,"lon":a.lon,"elevation":a.elevation},a.carrier_hz,a.min_elevation));return
    if a.cmd=="station-physics":
        dump(evaluate_station(StationInputs(antenna_diameter_m=a.diameter,effective_area_m2=a.effective_area,aperture_efficiency=a.efficiency,system_temperature_k=a.system_temperature,receiver_noise_figure_db=a.noise_figure_db,bandwidth_hz=a.bandwidth,integration_seconds=a.integration,polarization=a.polarization,frequency_hz=a.frequency,calibrated=a.calibrated)));return
    files={"station.json":{"classification":"STATION_MODEL_INCOMPLETE"},"source.json":{"truthClass":"SYNTHETIC_TEST"},"software.json":{"component":"voyager-science","order":11},"prediction-manifest.json":{"truthClass":"DERIVED_GEOMETRY"},"dsp-config.json":{"mode":"WOLA","taps":4},"spectrum-summary.json":{"units":"dBFS_RELATIVE"},"rfi-mask.json":{"maskedBins":[]},"detection.json":{"state":"SEARCHING","truthClass":"SYNTHETIC_TEST"}}
    result=create_bundle(a.output,files,"order011-deterministic-fixture","SYNTHETIC_TEST",{"version":"1.1.0"});dump(verify_bundle(a.output) if a.verify else result)
if __name__=="__main__":main()
