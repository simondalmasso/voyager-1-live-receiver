from __future__ import annotations
import statistics
from dataclasses import dataclass,field
from datetime import datetime
from voyager_listener.dsp.doppler import dedrift
from voyager_listener.lab.evidence import build_manifest
from voyager_listener.lab.iqbus import CanonicalIQBus,CanonicalIQFrame
from voyager_listener.lab.spectrometer import DeepSpaceSpectrometer,SpectrometerConfig,channelize
from voyager_listener.lab.rfi import build_stationary_mask,candidate_score

@dataclass(slots=True)
class PipelineTelemetry:
    source_status:str="IDLE"; sample_rate_hz:float=0; source_drops:int=0; sequence_gaps:int=0; bus_consumer_drops:int=0; channel_bandwidth_hz:float=0; doppler_expected_hz:float=0; doppler_drift_hz_s:float=0; spectrometer_mode:str="WOLA"; bin_width_hz:float=0; integration_method:str="INCOHERENT"; integration_seconds:float=0; rfi_masked_bins:int=0; detector_state:str="NO_SOURCE"; evidence_status:str="NOT_READY"; evidence_missing:list[str]=field(default_factory=list); stage_errors:list[str]=field(default_factory=list)
    def as_dict(self):return {"schemaVersion":2,"source":{"status":self.source_status,"sampleRateHz":self.sample_rate_hz,"drops":self.source_drops,"sequenceGaps":self.sequence_gaps},"canonicalIQBus":{"status":"OPERATIONAL","consumerDrops":self.bus_consumer_drops,"bounded":True},"channelizer":{"outputBandwidthHz":self.channel_bandwidth_hz},"doppler":{"expectedHz":self.doppler_expected_hz,"driftHzS":self.doppler_drift_hz_s},"spectrometer":{"mode":self.spectrometer_mode,"binWidthHz":self.bin_width_hz},"integrator":{"method":self.integration_method,"durationSeconds":self.integration_seconds},"rfi":{"maskedBins":self.rfi_masked_bins},"detector":{"state":self.detector_state},"evidence":{"status":self.evidence_status,"missing":list(self.evidence_missing)},"errors":list(self.stage_errors)}

def _ts(value:str)->float:return datetime.fromisoformat(value.replace("Z","+00:00")).timestamp()
def _noise(values:list[float],peak:int,guard:int=3)->tuple[float,float]:
    bins=[v for i,v in enumerate(values) if abs(i-peak)>guard]
    if not bins:return 0.0,0.0
    med=statistics.median(bins);mad=statistics.median(abs(v-med) for v in bins);return med,mad
def _off_target_conflict(values:list[float]|None,peak:int)->bool|None:
    if values is None:return None
    if not values:return False
    ref_peak=max(range(len(values)),key=values.__getitem__);noise,_=_noise(values,ref_peak);return abs(ref_peak-peak)<=1 and values[ref_peak]-noise>=6.0

class DeepSpaceLabPipeline:
    def __init__(self,config:SpectrometerConfig|None=None):
        self.bus=CanonicalIQBus();self.dsp_consumer=self.bus.subscribe("dsp",2);self.evidence_consumer=self.bus.subscribe("evidence",2);self.spectrometer=DeepSpaceSpectrometer(config or SpectrometerConfig());self.spectrum_history:list[list[float]]=[];self.feature_history:list[dict]=[];self.sample_buffer:list[complex]=[];self.buffer_stream_id:str|None=None;self.telemetry=PipelineTelemetry(spectrometer_mode=self.spectrometer.config.mode,integration_method=self.spectrometer.config.integration_method)
    def reset(self)->None:self.spectrometer.reset();self.spectrum_history.clear();self.feature_history.clear();self.sample_buffer.clear();self.buffer_stream_id=None
    def process(self,frame:CanonicalIQFrame,*,expected_frequency_hz:float|None=None,expected_drift_hz_s:float|None=None,off_target_values_db:list[float]|None=None,station:dict|None=None)->dict:
        prior_gaps=self.bus.sequence_gaps;self.bus.publish(frame);consumed=self.dsp_consumer.get()
        if consumed is None:raise RuntimeError("canonical IQ bus produced no DSP frame")
        bus=self.bus.snapshot();self.telemetry.source_status=consumed.source_truth_class;self.telemetry.sample_rate_hz=consumed.sample_rate_hz;self.telemetry.source_drops=consumed.dropped_samples_before;self.telemetry.sequence_gaps=bus["sequenceGaps"];self.telemetry.bus_consumer_drops=sum(c["droppedFrames"] for c in bus["consumers"].values())
        if self.buffer_stream_id not in {None,consumed.stream_id} or bus["sequenceGaps"]>prior_gaps or consumed.dropped_samples_before>0:
            self.sample_buffer.clear();self.spectrometer.reset();self.feature_history.clear();self.spectrum_history.clear();self.telemetry.stage_errors.append("SOURCE_GAP_BUFFER_RESET")
        self.buffer_stream_id=consumed.stream_id;self.sample_buffer.extend(consumed.samples);c=self.spectrometer.config;span=c.nfft*(c.taps if c.mode=="WOLA" else 1);limit=span*max(1,c.integration_windows)
        if len(self.sample_buffer)>limit:self.sample_buffer=self.sample_buffer[-limit:]
        if len(self.sample_buffer)<span:
            self.telemetry.detector_state="BUFFERING";self.telemetry.evidence_status="NOT_READY";self.telemetry.evidence_missing=["spectrometerWindow"]
            return {"ready":False,"spectrum":None,"rfiMask":{"method":"MEDIAN_MAD_STATIONARY","maskedBins":[],"reasons":{}},"candidate":{"classification":"INSUFFICIENT_EVIDENCE","missing":["spectrometerWindow"],"score":None},"measured":{},"pipeline":self.telemetry.as_dict(),"evidence":{"status":"NOT_READY","missing":["spectrometerWindow"],"manifest":None,"manifestSha256":None},"truthClass":consumed.source_truth_class,"provenanceId":consumed.source_provenance_id}
        offset=(expected_frequency_hz-consumed.center_frequency_hz) if expected_frequency_hz is not None else 0.0;drift=expected_drift_hz_s or 0.0;buffer_start=max(0,consumed.sample_start+consumed.sample_count-len(self.sample_buffer));corrected=dedrift(self.sample_buffer,consumed.sample_rate_hz,offset_hz=offset,drift_hz_s=drift,start_index=buffer_start);effective_rate=consumed.sample_rate_hz
        if c.channel_bandwidth_hz:corrected,effective_rate=channelize(corrected,effective_rate,0.0,c.channel_bandwidth_hz)
        product=self.spectrometer.process(list(corrected),effective_rate);values=list(product.values_db);peak=max(range(len(values)),key=values.__getitem__);center=len(values)//2;noise,mad=_noise(values,peak);snr=values[peak]-noise;frequency_residual=(peak-center)*product.bin_width_hz if expected_frequency_hz is not None else None
        self.spectrum_history.append(values);self.spectrum_history=self.spectrum_history[-8:];mask=build_stationary_mask(self.spectrum_history);stationary=(peak in mask.masked_bins) if len(self.spectrum_history)>=2 else None
        if frequency_residual is not None:self.feature_history.append({"at":_ts(consumed.timestamp_start),"residualHz":frequency_residual,"peakBin":peak,"snrDb":snr});self.feature_history=self.feature_history[-12:]
        persistence=None;drift_residual=None
        if len(self.feature_history)>=3:
            latest=self.feature_history[-1];tol=max(product.bin_width_hz*1.5,1e-9);persistence=sum(abs(x["residualHz"]-latest["residualHz"])<=tol for x in self.feature_history)/len(self.feature_history)
        if len(self.feature_history)>=2 and expected_drift_hz_s is not None:
            first,last=self.feature_history[0],self.feature_history[-1];dt=last["at"]-first["at"]
            if dt>0:drift_residual=(last["residualHz"]-first["residualHz"])/dt
        off_target_conflict=_off_target_conflict(off_target_values_db,peak)
        score=candidate_score(frequency_residual_hz=frequency_residual,drift_residual_hz_s=drift_residual,persistence=persistence,snr_db=snr,stationary_rfi=stationary,off_target_conflict=off_target_conflict,frequency_window_hz=max(25.0,product.bin_width_hz*6),drift_window_hz_s=max(.05,product.bin_width_hz/30))
        self.telemetry.channel_bandwidth_hz=effective_rate;self.telemetry.doppler_expected_hz=expected_frequency_hz or 0;self.telemetry.doppler_drift_hz_s=expected_drift_hz_s or 0;self.telemetry.bin_width_hz=product.bin_width_hz;self.telemetry.integration_seconds=product.integration_seconds;self.telemetry.rfi_masked_bins=len(mask.masked_bins);self.telemetry.detector_state=score["classification"]
        missing=list(score.get("missing",[]));
        if station is None:missing.append("station")
        files={"source.json":{"streamId":consumed.stream_id,"sequence":consumed.sequence,"sampleStart":consumed.sample_start,"sampleCount":consumed.sample_count,"sampleRateHz":consumed.sample_rate_hz,"centerFrequencyHz":consumed.center_frequency_hz,"timestampStart":consumed.timestamp_start,"timestampQuality":consumed.timestamp_quality,"droppedSamplesBefore":consumed.dropped_samples_before,"truthClass":consumed.source_truth_class,"provenanceId":consumed.source_provenance_id},"station.json":station or {"status":"NOT_SUPPLIED"},"prediction-manifest.json":{"expectedFrequencyHz":expected_frequency_hz,"expectedDriftHzS":expected_drift_hz_s},"dsp-config.json":{"spectrometer":c.mode,"nfft":c.nfft,"taps":c.taps,"integrationMethod":c.integration_method},"spectrum-summary.json":{"peakBin":peak,"binWidthHz":product.bin_width_hz,"noiseFloorDb":noise,"noiseMadDb":mad,"snrDb":snr,"windowCount":product.window_count,"units":product.units},"rfi-mask.json":mask.as_dict(),"detection.json":score}
        observation_id=f"{consumed.stream_id}-{consumed.sequence}";built=build_manifest(files,observation_id,consumed.source_truth_class,{"component":"voyager-listener","order":11,"revision":"R2"});status="READY_CANONICAL_MANIFEST" if not missing else "NOT_READY";self.telemetry.evidence_status=status;self.telemetry.evidence_missing=sorted(set(missing));pipeline=self.telemetry.as_dict();evidence={"status":status,"missing":self.telemetry.evidence_missing,"manifest":built["manifest"],"manifestSha256":built["manifestSha256"]}
        return {"ready":True,"spectrum":product.as_dict(),"rfiMask":mask.as_dict(),"candidate":score,"measured":{"peakBin":peak,"noiseFloorDb":noise,"noiseMadDb":mad,"snrDb":snr,"frequencyResidualHz":frequency_residual,"driftResidualHzS":drift_residual,"persistence":persistence,"stationaryRfi":stationary,"offTargetConflict":off_target_conflict},"pipeline":pipeline,"evidence":evidence,"truthClass":consumed.source_truth_class,"provenanceId":consumed.source_provenance_id}
