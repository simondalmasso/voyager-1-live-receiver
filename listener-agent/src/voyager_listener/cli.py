from __future__ import annotations
import argparse
import hashlib
import json
import math
import platform
import struct
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator
from .dsp.detector import analyze
from .dsp.doppler import classical_observed_frequency
from .ephemeris.horizons import topocentric_query
from .protocol.server import SnapshotServer
from .protocol.snapshot import signal_snapshot
from .provenance import Provenance, utc_now
from .sources.gnuradio_bridge import udp_cf32
from .sources.sigmf_source import inspect, read_chunks, verify_manifest
from .sources.synthetic_source import generate, write_cf32

DEFAULT_CARRIER_HZ = 8_420_430_000.0

def parser() -> argparse.ArgumentParser:
    p=argparse.ArgumentParser(prog="voyager-listener",description="Receive-only Voyager narrowband carrier laboratory")
    sub=p.add_subparsers(dest="command",required=True)
    sub.add_parser("doctor")
    synth=sub.add_parser("synth");synth.add_argument("--output",default="fixture.sigmf-meta");synth.add_argument("--no-signal",action="store_true");synth.add_argument("--seed",type=int,default=1701)
    pred=sub.add_parser("predict");pred.add_argument("--lat",type=float,required=True);pred.add_argument("--lon",type=float,required=True);pred.add_argument("--elevation-m",type=float,default=0);pred.add_argument("--carrier-hz",type=float,default=DEFAULT_CARRIER_HZ);pred.add_argument("--minutes",type=int,default=4)
    ana=sub.add_parser("analyze");ana.add_argument("meta");ana.add_argument("--manifest");ana.add_argument("--expected-frequency-hz",type=float);ana.add_argument("--drift-hz-s",type=float,default=0.0);ana.add_argument("--fft-size",type=int,default=4096);ana.add_argument("--overlap",type=float,default=.5)
    live=sub.add_parser("live");live.add_argument("--source",choices=["gnuradio-udp","stdin","sigmf-stream","soapy"],required=True);live.add_argument("--meta");live.add_argument("--host",default="127.0.0.1");live.add_argument("--port",type=int,default=8766);live.add_argument("--sample-rate-hz",type=float,default=4096);live.add_argument("--center-frequency-hz",type=float,default=DEFAULT_CARRIER_HZ);live.add_argument("--expected-frequency-hz",type=float,default=DEFAULT_CARRIER_HZ);live.add_argument("--fft-size",type=int,default=4096);live.add_argument("--integration-seconds",type=float,default=8);live.add_argument("--driver");live.add_argument("--device-args",default="")
    rec=sub.add_parser("record");rec.add_argument("--source",choices=["gnuradio-udp","stdin"],required=True);rec.add_argument("--output",required=True);rec.add_argument("--seconds",type=float,default=30);rec.add_argument("--host",default="127.0.0.1");rec.add_argument("--port",type=int,default=8766);rec.add_argument("--sample-rate-hz",type=float,required=True);rec.add_argument("--center-frequency-hz",type=float,required=True)
    serve=sub.add_parser("serve");serve.add_argument("meta",nargs="?");serve.add_argument("--manifest");serve.add_argument("--synthetic",action="store_true");serve.add_argument("--port",type=int,default=8765);serve.add_argument("--host",default="127.0.0.1")
    vm=sub.add_parser("verify-manifest");vm.add_argument("manifest")
    replay=sub.add_parser("replay");replay.add_argument("ndjson");replay.add_argument("--speed",type=float,default=1.0)
    return p

def synth_command(args: argparse.Namespace) -> dict[str, Any]:
    meta_path=Path(args.output).resolve();data_path=meta_path.with_name(meta_path.name.replace(".sigmf-meta",".sigmf-data"));rate=4096.0;center=DEFAULT_CARRIER_HZ;offset=48.0;drift=.2
    samples=generate(rate,8.0,offset,drift,seed=args.seed,include_tone=not args.no_signal);digest=write_cf32(data_path,samples)
    doc={"global":{"core:datatype":"cf32_le","core:sample_rate":rate,"core:description":"Deterministic synthetic test fixture; not Voyager reception","voyager:truth_class":"SYNTHETIC_TEST","voyager:data_sha256":digest},"captures":[{"core:sample_start":0,"core:frequency":center,"core:datetime":utc_now()}],"annotations":[{"core:sample_start":0,"core:sample_count":len(samples),"voyager:tone_offset_hz":offset,"voyager:drift_hz_s":drift}]}
    meta_path.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8");return {"meta":str(meta_path),"data":str(data_path),"sha256":digest,"sampleCount":len(samples),"truthClass":"SYNTHETIC_TEST"}

def _provenance_for(info: Any, manifest: str | None) -> tuple[str, Provenance]:
    if manifest:
        verified=verify_manifest(manifest);return "RECORDED_AUTHENTIC_VERIFIED",Provenance("RECORDED_AUTHENTIC_VERIFIED","verified-sigmf-manifest",utc_now(),source_url=verified["sourceUrl"])
    if info.truth_class=="SYNTHETIC_TEST":return "SYNTHETIC_TEST",Provenance("SYNTHETIC_TEST","sigmf-synthetic",utc_now(),source_url=info.meta_path.as_uri())
    return "UNVERIFIED_SOURCE",Provenance("UNVERIFIED_SOURCE","operator-supplied-sigmf",utc_now(),source_url=info.meta_path.as_uri(),fallback_reason="No machine-verifiable authentic manifest supplied")

def analyze_meta(meta: str, expected: float | None, drift: float, fft_size: int, overlap: float=.5, manifest: str | None=None) -> tuple[dict[str, Any], list[complex]]:
    info=inspect(meta);samples=[s for chunk in read_chunks(info) for s in chunk];expected_hz=expected if expected is not None else info.center_frequency_hz;detection,spectrum=analyze(samples,info.sample_rate_hz,info.center_frequency_hz,expected_hz,drift_hz_s=drift,fft_size=fft_size,overlap=overlap)
    source_mode,prov=_provenance_for(info,manifest);snap=signal_snapshot(detection,spectrum,stream_id="sigmf-analysis",sequence=1,source_mode=source_mode,station_id="operator",station_name="Operator supplied source",started_at=utc_now(),sample_rate_hz=info.sample_rate_hz,center_frequency_hz=info.center_frequency_hz,datatype=info.datatype,bin_width_hz=info.sample_rate_hz/fft_size,provenance=prov);return snap,samples

def predict_command(args: argparse.Namespace) -> dict[str, Any]:
    now=datetime.now(timezone.utc).replace(microsecond=0);stop=now+timedelta(minutes=max(2,args.minutes));fmt=lambda d:d.strftime("%Y-%m-%d %H:%M:%S")
    url=topocentric_query(start_time=fmt(now),stop_time=fmt(stop),latitude_deg=args.lat,longitude_deg=args.lon,elevation_m=args.elevation_m)
    req=urllib.request.Request(url,headers={"User-Agent":"voyager-listener/1.1"});text=urllib.request.urlopen(req,timeout=15).read(2_000_000).decode("utf-8","replace");rows=_horizons_observer_rows(text)
    if not rows:raise RuntimeError("Horizons returned no parseable range-rate rows")
    points=[]
    for row in rows:
        observed=classical_observed_frequency(args.carrier_hz,row["rangeRateKmS"]*1000);points.append({**row,"predictedCarrierHz":observed,"dopplerHz":observed-args.carrier_hz})
    drift=(points[-1]["predictedCarrierHz"]-points[0]["predictedCarrierHz"])/max(1,(datetime.fromisoformat(points[-1]["observedAt"].replace("Z","+00:00"))-datetime.fromisoformat(points[0]["observedAt"].replace("Z","+00:00"))).total_seconds()) if len(points)>1 else 0.0
    return {"schemaVersion":1,"truthClass":"DERIVED_GEOMETRY","receiveOnly":True,"observer":{"lat":args.lat,"lon":args.lon,"elevationM":args.elevation_m},"restCarrierHz":args.carrier_hz,"points":points,"estimatedDriftHzPerSecond":drift,"sourceUrl":url,"generatedAt":utc_now()}

def _horizons_observer_rows(text: str) -> list[dict[str, Any]]:
    start=text.find("$$SOE");end=text.find("$$EOE");
    if start<0 or end<start:return []
    rows=[]
    for line in text[start+5:end].splitlines():
        fields=[x.strip() for x in line.split(",")];date=next((x for x in fields if _parse_horizons_date(x)),None)
        if not date:continue
        nums=[]
        for x in fields:
            try:nums.append(float(x))
            except ValueError:pass
        if len(nums)<2:continue
        # QUANTITIES=20 ends with range (AU) and range-rate (km/s) in CSV output.
        range_au,range_rate=nums[-2],nums[-1]
        if not (0<abs(range_au)<1000 and abs(range_rate)<100):continue
        rows.append({"observedAt":_parse_horizons_date(date),"rangeAu":range_au,"rangeRateKmS":range_rate})
    return rows

def _parse_horizons_date(value: str) -> str | None:
    value=value.replace("A.D.","").strip()
    for fmt in ("%Y-%b-%d %H:%M:%S.%f","%Y-%b-%d %H:%M:%S"):
        try:return datetime.strptime(value,fmt).replace(tzinfo=timezone.utc).isoformat().replace("+00:00","Z")
        except ValueError:pass
    return None

def _stdin_cf32(chunk_samples: int=65536)->Iterator[list[complex]]:
    read=sys.stdin.buffer.read
    while raw:=read(chunk_samples*8):
        if len(raw)%8:raw=raw[:len(raw)//8*8]
        if not raw:break
        vals=struct.unpack("<"+"ff"*(len(raw)//8),raw);yield [complex(vals[i],vals[i+1]) for i in range(0,len(vals),2)]

def _source(args: argparse.Namespace)->Iterator[list[complex]]:
    if args.source=="gnuradio-udp":return udp_cf32(args.host,args.port)
    if args.source=="stdin":return _stdin_cf32()
    if args.source=="sigmf-stream":
        if not args.meta:raise SystemExit("--meta is required for sigmf-stream")
        return read_chunks(inspect(args.meta))
    if args.source=="soapy":
        from .sources.soapy_source import cf32_chunks
        if not args.driver:raise SystemExit("--driver is required for soapy")
        settings=dict(x.split("=",1) for x in args.device_args.split(",") if "=" in x);return cf32_chunks(args.driver,args.sample_rate_hz,args.center_frequency_hz,**settings)
    raise SystemExit("unsupported source")

def live_command(args: argparse.Namespace)->int:
    needed=max(args.fft_size,int(args.sample_rate_hz*args.integration_seconds));buf:list[complex]=[];seq=0;started=utc_now()
    for chunk in _source(args):
        buf.extend(chunk)
        if len(buf)<needed:continue
        samples=buf[-needed:];detection,spectrum=analyze(samples,args.sample_rate_hz,args.center_frequency_hz,args.expected_frequency_hz,fft_size=args.fft_size,overlap=.5);seq+=1
        snap=signal_snapshot(detection,spectrum,stream_id="local-live-unverified",sequence=seq,source_mode="UNVERIFIED_SOURCE",station_id="local-operator",station_name="Local receive-only input",started_at=started,sample_rate_hz=args.sample_rate_hz,center_frequency_hz=args.center_frequency_hz,datatype="cf32_le",bin_width_hz=args.sample_rate_hz/args.fft_size,provenance=Provenance("UNVERIFIED_SOURCE",f"{args.source}-input",utc_now(),fallback_reason="Physical input is not cryptographically registered; never serialized as telescope live verified"));print(json.dumps(snap,separators=(",",":")),flush=True);buf=buf[-args.fft_size:]
    return 0

def record_command(args: argparse.Namespace)->dict[str, Any]:
    out=Path(args.output).resolve();meta=out if out.name.endswith(".sigmf-meta") else out.with_suffix(".sigmf-meta");data=meta.with_name(meta.name.replace(".sigmf-meta",".sigmf-data"));target=max(1,int(args.sample_rate_hz*args.seconds));count=0;h=hashlib.sha256();started=utc_now()
    with data.open("wb") as handle:
        for chunk in _source(args):
            take=chunk[:max(0,target-count)]
            if not take:break
            raw=b"".join(struct.pack("<ff",float(x.real),float(x.imag)) for x in take);handle.write(raw);h.update(raw);count+=len(take)
            if count>=target:break
    doc={"global":{"core:datatype":"cf32_le","core:sample_rate":args.sample_rate_hz,"core:description":"Operator receive-only capture; authenticity unverified until external manifest validation","voyager:truth_class":"UNVERIFIED_SOURCE","voyager:data_sha256":h.hexdigest()},"captures":[{"core:sample_start":0,"core:frequency":args.center_frequency_hz,"core:datetime":started}]};meta.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8");return {"meta":str(meta),"data":str(data),"sampleCount":count,"dataSha256":h.hexdigest(),"truthClass":"UNVERIFIED_SOURCE"}

def main(argv: list[str] | None=None)->int:
    args=parser().parse_args(argv)
    if args.command=="doctor":print(json.dumps({"python":platform.python_version(),"minimum":"3.12","receiveOnly":True,"rfUplink":False,"optional":{"numpy":_module("numpy"),"astropy":_module("astropy"),"SoapySDR":_module("SoapySDR")},"status":"ok"},indent=2));return 0
    if args.command=="synth":print(json.dumps(synth_command(args),indent=2));return 0
    if args.command=="predict":print(json.dumps(predict_command(args),indent=2));return 0
    if args.command=="analyze":snap,_=analyze_meta(args.meta,args.expected_frequency_hz,args.drift_hz_s,args.fft_size,args.overlap,args.manifest);print(json.dumps(snap,indent=2));return 0
    if args.command=="live":return live_command(args)
    if args.command=="record":print(json.dumps(record_command(args),indent=2));return 0
    if args.command=="verify-manifest":print(json.dumps(verify_manifest(args.manifest),indent=2));return 0
    if args.command=="serve":
        if args.synthetic:
            samples=generate();detection,spectrum=analyze(samples,4096,DEFAULT_CARRIER_HZ,DEFAULT_CARRIER_HZ,drift_hz_s=.2);sequence={"v":0}
            def provider()->dict[str,Any]:
                sequence["v"]+=1;return signal_snapshot(detection,spectrum,stream_id="synthetic-demo",sequence=sequence["v"],source_mode="SYNTHETIC_TEST",station_id="local-fixture",station_name="Local deterministic fixture",started_at=utc_now(),sample_rate_hz=4096,center_frequency_hz=DEFAULT_CARRIER_HZ,datatype="cf32_le",bin_width_hz=1,provenance=Provenance("SYNTHETIC_TEST","listener-synthetic",utc_now()))
        elif args.meta:
            snap,_=analyze_meta(args.meta,None,0.0,4096,.5,args.manifest);sequence={"v":0}
            def provider()->dict[str,Any]:sequence["v"]+=1;return {...snap,"sequence":sequence["v"],"generatedAt":utc_now()}
        else:raise SystemExit("serve requires --synthetic or a SigMF metadata path")
        server=SnapshotServer(provider,args.host,args.port);print(f"serving receive-only products on http://{args.host}:{args.port}",file=sys.stderr);server.serve_forever();return 0
    if args.command=="replay":
        lines=[x for x in Path(args.ndjson).read_text(encoding="utf-8").splitlines() if x.strip()]
        delay=max(0,1/max(.001,args.speed))
        for line in lines:print(line,flush=True);time.sleep(delay)
        return 0
    return 2

def _module(name: str)->bool:
    try:__import__(name);return True
    except ImportError:return False
if __name__=="__main__":raise SystemExit(main())
