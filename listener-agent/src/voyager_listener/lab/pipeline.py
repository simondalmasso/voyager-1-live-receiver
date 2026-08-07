from __future__ import annotations
from dataclasses import dataclass,field
from voyager_listener.lab.iqbus import CanonicalIQBus,CanonicalIQFrame
from voyager_listener.lab.spectrometer import DeepSpaceSpectrometer,SpectrometerConfig
from voyager_listener.lab.rfi import build_stationary_mask,candidate_score

@dataclass(slots=True)
class PipelineTelemetry:
    source_status:str="IDLE"; sample_rate_hz:float=0; source_drops:int=0; channel_bandwidth_hz:float=0; doppler_expected_hz:float=0; doppler_drift_hz_s:float=0; spectrometer_mode:str="WOLA"; bin_width_hz:float=0; integration_method:str="INCOHERENT"; integration_seconds:float=0; rfi_masked_bins:int=0; detector_state:str="NO_SOURCE"; evidence_status:str="NOT_READY"; stage_errors:list[str]=field(default_factory=list)
    def as_dict(self):return {"schemaVersion":1,"source":{"status":self.source_status,"sampleRateHz":self.sample_rate_hz,"drops":self.source_drops},"channelizer":{"outputBandwidthHz":self.channel_bandwidth_hz},"doppler":{"expectedHz":self.doppler_expected_hz,"driftHzS":self.doppler_drift_hz_s},"spectrometer":{"mode":self.spectrometer_mode,"binWidthHz":self.bin_width_hz},"integrator":{"method":self.integration_method,"durationSeconds":self.integration_seconds},"rfi":{"maskedBins":self.rfi_masked_bins},"detector":{"state":self.detector_state},"evidence":{"status":self.evidence_status},"errors":list(self.stage_errors)}

class DeepSpaceLabPipeline:
    def __init__(self,config:SpectrometerConfig|None=None):
        self.bus=CanonicalIQBus();self.spectrometer=DeepSpaceSpectrometer(config or SpectrometerConfig());self.history=[];self.telemetry=PipelineTelemetry(spectrometer_mode=self.spectrometer.config.mode,integration_method=self.spectrometer.config.integration_method)
    def process(self,frame:CanonicalIQFrame,*,frequency_residual_hz:float=0,drift_residual_hz_s:float=0,persistence:float=1,snr_db:float=12,off_target_conflict:bool=False)->dict:
        self.bus.publish(frame);self.telemetry.source_status=frame.source_truth_class;self.telemetry.sample_rate_hz=frame.sample_rate_hz;self.telemetry.source_drops=frame.dropped_samples_before
        product=self.spectrometer.process(list(frame.samples),frame.sample_rate_hz);self.history.append(list(product.values_db));self.history=self.history[-8:];mask=build_stationary_mask(self.history);score=candidate_score(frequency_residual_hz=frequency_residual_hz,drift_residual_hz_s=drift_residual_hz_s,persistence=persistence,snr_db=snr_db,stationary_rfi=False,off_target_conflict=off_target_conflict)
        self.telemetry.bin_width_hz=product.bin_width_hz;self.telemetry.integration_seconds=product.integration_seconds;self.telemetry.rfi_masked_bins=len(mask.masked_bins);self.telemetry.detector_state=score["classification"];self.telemetry.evidence_status="READY_REDUCED_PRODUCT"
        return {"spectrum":product.as_dict(),"rfiMask":mask.as_dict(),"candidate":score,"pipeline":self.telemetry.as_dict(),"truthClass":frame.source_truth_class,"provenanceId":frame.source_provenance_id}
