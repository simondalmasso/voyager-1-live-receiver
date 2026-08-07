from __future__ import annotations
import argparse
import hashlib
import json
import platform
import struct
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator
from .dsp.detector import Detection
from .dsp.doppler import classical_observed_frequency
from .ephemeris.horizons import topocentric_query
from .lab.adapters import frames_from_chunks,gnuradio_frames,sigmf_frames,soapy_frames
from .lab.pipeline import DeepSpaceLabPipeline
from .lab.spectrometer import SpectrometerConfig
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
    live=sub.add_parser("live");live.add_argument("--source",choices=["gnuradio-udp","stdin","sigmf-stream","soapy"],required=True);live.add_argument("--meta");live.add_argument("--host",default="127.0.0.1");live.add_argument("--port",type=int,default=8766);live.add_argument("--sample-rate-hz",type=float,default=4096);live.add_argument("--center-frequency-hz",type=float,default=DEFAULT_CARRIER_HZ);live.add_argument("--expected-frequency-hz",type=float,default=DEFAULT_CARRIER_HZ);live.add_argument("--drift-hz-s",type=float,default=0.0);live.add_argument("--fft-size",type=int,default=4096);live.add_argument("--integration-seconds",type=float,default=8);live.add_argument("--driver");live.add_argument("--device-args",default="")
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

def _config(fft_size:int,sample_rate_hz:float,integration_seconds:float=8.0)->SpectrometerConfig:
    span=fft_size*4;windows=max(1,min(16,int(max(integration_seconds,span/sample_rate_hz)*sample_rate_hz/span)))
    return SpectrometerConfig(mode="WOLA",nfft=fft_size,taps=4,integration_method="INCOHERENT",integration_windows=windows)

def _snapshot_from_product(product:dict[str,Any],frame:Any,expected_hz:float|None,prov:Provenance,station_id:str,station_name:str,started_at:str)->dict[str,Any]:
    measured=product.get("measured",{});candidate=product.get("candidate",{});residual=measured.get("frequencyResidualHz");expected=expected_hz if expected_hz is not None else frame.center_frequency_hz;observed=expected+residual if residual is not None else None;score=candidate.get("score")
    detection=Detection(candidate.get("classification","INSUFFICIENT_EVIDENCE"),observed,expected,residual,measured.get("snrDb"),float(score or 0),float(product.get("spectrum",{}).get("integrationSeconds",0)),frame.sample_count,frame.dropped_samples_before,float(measured.get("persistence") or 0))
    spectrum=list(product.get("spectrum",{}).get("valuesDb",[]));snap=signal_snapshot(detection,spectrum,stream_id=frame.stream_id,sequence=frame.sequence,source_mode=frame.source_truth_class,station_id=station_id,station_name=station_name,started_at=started_at,sample_rate_hz=frame.sample_rate_hz,center_frequency_hz=frame.center_frequency_hz,datatype=frame.datatype,bin_width_hz=float(product.get("spectrum",{}).get("binWidthHz",frame.sample_rate_hz/max(1,len(spectrum)))),provenance=prov);snap["labPipeline"]=product.get("pipeline");snap["measured"]=measured;snap["rfiMask"]=product.get("rfiMask");snap["candidate"]=candidate;snap["evidence"]=product.get("evidence");return snap

def analyze_meta(meta: str, expected: float | None, drift: float, fft_size: int, overlap: float=.5, manifest: str | None=None) -> tuple[dict[str, Any], list[complex]]:
    del overlap
    info=inspect(meta);source_mode,prov=_provenance_for(info,manifest);expected_hz=expected if expected is not None else info.center_frequency_hz;global_meta=info.metadata.get("global",{});captures=info.metadata.get("captures",[]);start=(captures[0].get("core:datetime") if captures else None) or global_meta.get("core:datetime") or global_meta.get("voyager:observation_time") or "1970-01-01T00:00:00Z";chunks=read_chunks(info,max(fft_size,fft_size*2));frames=frames_from_chunks(chunks,stream_id=f"sigmf-{info.data_sha256[:12]}",sample_rate_hz=info.sample_rate_hz,center_frequency_hz=info.center_frequency_hz,truth_class=source_mode,provenance_id=info.data_sha256,start_time=start,datatype=info.datatype,timestamp_quality="RECORDED");pipeline=DeepSpaceLabPipeline(_config(fft_size,info.sample_rate_hz));last=None;last_frame=None;all_samples=[]
    for frame in frames:
        all_samples.extend(frame.samples);product=pipeline.process(frame,expected_frequency_hz=expected_hz,expected_drift_hz_s=drift);last_frame=frame
        if product.get("ready"):last=product
    if last is None or last_frame is None:raise ValueError("not enough samples for canonical IQ pipeline")
    return _snapshot_from_product(last,last_frame,expected_hz,prov,"operator","Operator supplied source",start),all_samples

def predict_command(args: argparse.Namespace) -> dict[str, Any]:
    now=datetime.now(timezone.utc).replace(microsecond=0);stop=now+timedelta(minutes=max(2,args.minutes));fmt=lambda d:d.strftime("%Y-%m-%d %H:%M:%S")
    url=topocentric_query(start_time=fmt(now),stop_time=fmt(stop),latitude_deg=args.lat,longitude_deg=args.lon,elevation_m=args.elevation_m)
    req=urllib.request.Request(url,headers={"User-Agent":"voyager-listener/1.1-r2"});text=urllib.request.urlopen(req,timeout=15).read(2_000_000).decode("utf-8","replace");rows=_horizons_observer_rows(text)
    if not rows:raise RuntimeError("Horizons returned no parseable range-rate rows")
    points=[]
    for row in rows:
        observed=classical_observed_frequency(args.carrier_hz,row["rangeRateKmS"]*1000);points.append({**row,"predictedCarrierHz":observed,"dopplerHz":observed-args.carrier_hz})
    drift=(points[-1]["predictedCarrierHz"]-points[0]["predictedCarrierHz"])/max(1,(datetime.fromisoformat(points[-1]["observedAt"].replace("Z","+00:00"))-datetime.fromisoformat(points[0]["observedAt"].replace("Z","+00:00"))).total_seconds()) if len(points)>1 else 0.0
    return {"schemaVersion":2,"truthClass":"DERIVED_GEOMETRY","predictionFreshness":"HORIZONS_OBSERVER_FRESH","rfPredictionReady":True,"receiveOnly":True,"observer":{"lat":args.lat,"lon":args.lon,"elevationM":args.elevation_m},"restCarrierHz":args.carrier_hz,"points":points,"estimatedDriftHzPerSecond":drift,"sourceUrl":url,"generatedAt":utc_now()}

def _horizons_observer_rows(text: str) -> list[dict[str, Any]]:
    start=text.find("$$SOE");end=text.find("$$EOE")
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

def _live_frames(args:argparse.Namespace):
    started=utc_now()
    if args.source=="gnuradio-udp":return gnuradio_frames(args.host,args.port,sample_rate_hz=args.sample_rate_hz,center_frequency_hz=args.center_frequency_hz),started,Provenance("UNVERIFIED_SOURCE","gnuradio-udp-input",started,fallback_reason="Local receive-only input is not cryptographically registered")
    if args.source=="soapy":
        if not args.driver:raise SystemExit("--driver is required for soapy")
        settings=dict(x.split("=",1) for x in args.device_args.split(",") if "=" in x);return soapy_frames(args.driver,args.sample_rate_hz,args.center_frequency_hz,**settings),started,Provenance("UNVERIFIED_SOURCE","soapysdr-input",started,fallback_reason="Local receive-only input is not cryptographically registered")
    if args.source=="sigmf-stream":
        if not args.meta:raise SystemExit("--meta is required for sigmf-stream")
        return sigmf_frames(args.meta,max(1024,args.fft_size)),started,Provenance("UNVERIFIED_SOURCE","sigmf-stream-input",started,fallback_reason="Replay provenance follows SigMF metadata; no authentic manifest supplied in live mode")
    return frames_from_chunks(_stdin_cf32(),stream_id="stdin-live",sample_rate_hz=args.sample_rate_hz,center_frequency_hz=args.center_frequency_hz,truth_class="UNVERIFIED_SOURCE",provenance_id="local-stdin",start_time=started,datatype="cf32_le",timestamp_quality="HOST"),started,Provenance("UNVERIFIED_SOURCE","stdin-input",started,fallback_reason="Local receive-only input is not cryptographically registered")

def live_command(args: argparse.Namespace)->int:
    frames,started,prov=_live_frames(args);pipeline=DeepSpaceLabPipeline(_config(args.fft_size,args.sample_rate_hz,args.integration_seconds))
    for frame in frames:
        product=pipeline.process(frame,expected_frequency_hz=args.expected_frequency_hz,expected_drift_hz_s=args.drift_hz_s)
        if not product.get("ready"):continue
        snap=_snapshot_from_product(product,frame,args.expected_frequency_hz,prov,"local-operator","Local receive-only input",started);print(json.dumps(snap,separators=(",",":")),flush=True)
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
    if args.command=="doctor":print(json.dumps({"python":platform.python_version(),"minimum":"3.12","receiveOnly":True,"rfUplink":False,"canonicalIqPipeline":"OPERATIONAL_R2","optional":{"numpy":_module("numpy"),"astropy":_module("astropy"),"SoapySDR":_module("SoapySDR")},"status":"ok"},indent=2));return 0
    if args.command=="synth":print(json.dumps(synth_command(args),indent=2));return 0
    if args.command=="predict":print(json.dumps(predict_command(args),indent=2));return 0
    if args.command=="analyze":snap,_=analyze_meta(args.meta,args.expected_frequency_hz,args.drift_hz_s,args.fft_size,args.overlap,args.manifest);print(json.dumps(snap,indent=2));return 0
    if args.command=="live":return live_command(args)
    if args.command=="record":print(json.dumps(record_command(args),indent=2));return 0
    if args.command=="verify-manifest":print(json.dumps(verify_manifest(args.manifest),indent=2));return 0
    if args.command=="serve":
        if args.synthetic:
            started=utc_now();samples=generate();frames=frames_from_chunks([samples],stream_id="synthetic-demo",sample_rate_hz=4096,center_frequency_hz=DEFAULT_CARRIER_HZ,truth_class="SYNTHETIC_TEST",provenance_id="listener-synthetic",start_time=started,datatype="cf32_le",timestamp_quality="SYNTHETIC");pipeline=DeepSpaceLabPipeline(_config(1024,4096));frame=next(frames);product=pipeline.process(frame,expected_frequency_hz=DEFAULT_CARRIER_HZ,expected_drift_hz_s=.2);snap=_snapshot_from_product(product,frame,DEFAULT_CARRIER_HZ,Provenance("SYNTHETIC_TEST","listener-synthetic",started),"local-fixture","Local deterministic fixture",started);sequence={"v":0}
            def provider()->dict[str,Any]:sequence["v"]+=1;return {**snap,"sequence":sequence["v"],"generatedAt":utc_now()}
        elif args.meta:
            snap,_=analyze_meta(args.meta,None,0.0,4096,.5,args.manifest);sequence={"v":0}
            def provider()->dict[str,Any]:sequence["v"]+=1;return {**snap,"sequence":sequence["v"],"generatedAt":utc_now()}
        else:raise SystemExit("serve requires --synthetic or a SigMF metadata path")
        server=SnapshotServer(provider,args.host,args.port);print(f"serving receive-only products on http://{args.host}:{args.port}",file=sys.stderr);server.serve_forever();return 0
    if args.command=="replay":
        lines=[x for x in Path(args.ndjson).read_text(encoding="utf-8").splitlines() if x.strip()];delay=max(0,1/max(.001,args.speed))
        for line in lines:print(line,flush=True);time.sleep(delay)
        return 0
    return 2

def _module(name: str)->bool:
    try:__import__(name);return True
    except ImportError:return False
if __name__=="__main__":raise SystemExit(main())
