from __future__ import annotations
import argparse
import json
import platform
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .dsp.detector import analyze
from .protocol.server import SnapshotServer
from .protocol.snapshot import signal_snapshot
from .provenance import Provenance, utc_now
from .sources.sigmf_source import inspect, read_chunks
from .sources.synthetic_source import generate, write_cf32

def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="voyager-listener", description="Receive-only Voyager carrier detector")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    synth = sub.add_parser("synth"); synth.add_argument("--output", default="fixture.sigmf-meta"); synth.add_argument("--no-signal", action="store_true"); synth.add_argument("--seed", type=int, default=1701)
    ana = sub.add_parser("analyze"); ana.add_argument("meta"); ana.add_argument("--expected-frequency-hz", type=float); ana.add_argument("--drift-hz-s", type=float, default=0.0); ana.add_argument("--fft-size", type=int, default=1024)
    serve = sub.add_parser("serve"); serve.add_argument("meta", nargs="?"); serve.add_argument("--synthetic", action="store_true"); serve.add_argument("--port", type=int, default=8765); serve.add_argument("--host", default="127.0.0.1")
    replay = sub.add_parser("replay"); replay.add_argument("ndjson"); replay.add_argument("--speed", type=float, default=1.0)
    return p

def synth_command(args: argparse.Namespace) -> dict[str, Any]:
    meta_path = Path(args.output).resolve(); data_path = meta_path.with_name(meta_path.name.replace(".sigmf-meta", ".sigmf-data")); rate=4096.0; center=8_420_430_000.0; offset=48.0; drift=.2
    samples=generate(rate,8.0,offset,drift,seed=args.seed,include_tone=not args.no_signal); digest=write_cf32(data_path,samples)
    doc={"global":{"core:datatype":"cf32_le","core:sample_rate":rate,"core:description":"Deterministic synthetic test fixture; not Voyager reception","voyager:truth_class":"SIMULATED","voyager:sha256":digest},"captures":[{"core:sample_start":0,"core:frequency":center,"core:datetime":utc_now()}],"annotations":[{"core:sample_start":0,"core:sample_count":len(samples),"voyager:tone_offset_hz":offset,"voyager:drift_hz_s":drift}]}
    meta_path.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8"); return {"meta":str(meta_path),"data":str(data_path),"sha256":digest,"sampleCount":len(samples),"truthClass":"SIMULATED"}

def analyze_meta(meta: str, expected: float | None, drift: float, fft_size: int) -> tuple[dict[str, Any], list[complex]]:
    info=inspect(meta); samples=[s for chunk in read_chunks(info) for s in chunk]; expected_hz=expected if expected is not None else info.center_frequency_hz; detection,spectrum=analyze(samples,info.sample_rate_hz,info.center_frequency_hz,expected_hz,drift_hz_s=drift,fft_size=fft_size)
    prov=Provenance("RECORDED_AUTHENTIC" if "authentic" in Path(meta).name.lower() else "SIMULATED", "sigmf-file", utc_now(), source_url=Path(meta).resolve().as_uri())
    snap=signal_snapshot(detection,spectrum,stream_id="sigmf-analysis",sequence=1,source_mode="RECORDED_AUTHENTIC" if prov.truth_class=="RECORDED_AUTHENTIC" else "SYNTHETIC_TEST",station_id="operator",station_name="Operator supplied source",started_at=utc_now(),sample_rate_hz=info.sample_rate_hz,center_frequency_hz=info.center_frequency_hz,datatype=info.datatype,bin_width_hz=info.sample_rate_hz/fft_size,provenance=prov); return snap,samples

def main(argv: list[str] | None = None) -> int:
    args=parser().parse_args(argv)
    if args.command=="doctor":
        print(json.dumps({"python":platform.python_version(),"minimum":"3.12","receiveOnly":True,"optional":{"numpy":_module("numpy"),"astropy":_module("astropy"),"SoapySDR":_module("SoapySDR")},"status":"ok"},indent=2)); return 0
    if args.command=="synth": print(json.dumps(synth_command(args),indent=2)); return 0
    if args.command=="analyze": snap,_=analyze_meta(args.meta,args.expected_frequency_hz,args.drift_hz_s,args.fft_size); print(json.dumps(snap,indent=2)); return 0
    if args.command=="serve":
        if args.synthetic:
            samples=generate(); detection,spectrum=analyze(samples,4096,8_420_430_000,8_420_430_000,drift_hz_s=.2); sequence={"v":0}
            def provider() -> dict[str, Any]:
                sequence["v"]+=1; return signal_snapshot(detection,spectrum,stream_id="synthetic-live-demo",sequence=sequence["v"],source_mode="SYNTHETIC_TEST",station_id="local-fixture",station_name="Local deterministic fixture",started_at=utc_now(),sample_rate_hz=4096,center_frequency_hz=8_420_430_000,datatype="cf32_le",bin_width_hz=4,provenance=Provenance("SIMULATED","listener-synthetic",utc_now()))
        elif args.meta:
            snap,_=analyze_meta(args.meta,None,0.0,1024); provider=lambda:snap
        else: raise SystemExit("serve requires --synthetic or a SigMF metadata path")
        server=SnapshotServer(provider,args.host,args.port); print(f"serving receive-only products on http://{args.host}:{args.port}",file=sys.stderr); server.serve_forever(); return 0
    if args.command=="replay":
        for line in Path(args.ndjson).read_text(encoding="utf-8").splitlines():
            if line.strip(): print(line,flush=True)
        return 0
    return 2

def _module(name: str) -> bool:
    try: __import__(name); return True
    except ImportError: return False
if __name__=="__main__": raise SystemExit(main())
