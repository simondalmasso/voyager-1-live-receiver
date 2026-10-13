import cmath,math,tempfile,unittest,zipfile
from pathlib import Path
from voyager_listener.lab.iqbus import *
from voyager_listener.lab.spectrometer import *
from voyager_listener.lab.rfi import *
from voyager_listener.lab.station import *
from voyager_listener.lab.observation import *
from voyager_listener.lab.evidence import *
from voyager_listener.lab.multistation import *
from voyager_listener.lab.decoder import *
from voyager_listener.lab.pipeline import *
from voyager_listener.lab.adapters import frames_from_chunks

def tone(count,fs,bin_pos,nfft):return [cmath.exp(2j*math.pi*(bin_pos*fs/nfft)*i/fs) for i in range(count)]
def frame(seq=0,samples=None,truth="SYNTHETIC_TEST"):
    s=tuple(samples or tone(1024,1024,30.35,256));return CanonicalIQFrame("s",seq,seq*len(s),len(s),1024,8420430000,"complex64","2026-08-07T12:00:00Z","SYNTHETIC",0,truth,"prov",s)
class LabTests(unittest.TestCase):
    def test_bus_bounded_and_gaps(self):
        b=CanonicalIQBus();c=b.subscribe("slow",2);b.publish(frame(0));b.publish(frame(2));b.publish(frame(3));self.assertEqual(c.snapshot()["droppedFrames"],1);self.assertEqual(b.snapshot()["sequenceGaps"],1);b.close();self.assertTrue(b.closed)
    def test_replay_preserves_truth_and_timestamp(self):
        f=frame();r=next(replay_frames([f],lambda:"2026-08-07T12:01:00Z"));self.assertEqual(r.timestamp_start,f.timestamp_start);self.assertEqual(r.source_truth_class,"SYNTHETIC_TEST");self.assertIsNotNone(r.replay_received_at)
    def test_live_replay_adapters_share_identical_dsp_after_normalization(self):
        samples=tone(1024,1024,30.35,256);cfg=SpectrometerConfig(mode="WOLA",nfft=256,taps=4)
        live=next(frames_from_chunks([samples],stream_id="live",sample_rate_hz=1024,center_frequency_hz=8420430000,truth_class="UNVERIFIED_SOURCE",provenance_id="soapy-fixture",start_time="2026-08-07T12:00:00Z",timestamp_quality="HARDWARE"))
        recorded=next(frames_from_chunks([samples],stream_id="replay",sample_rate_hz=1024,center_frequency_hz=8420430000,truth_class="RECORDED_AUTHENTIC_VERIFIED",provenance_id="sigmf-fixture",start_time="2026-08-07T12:00:00Z",timestamp_quality="RECORDED"))
        a=DeepSpaceLabPipeline(cfg).process(live);b=DeepSpaceLabPipeline(cfg).process(recorded)
        self.assertEqual(a["spectrum"]["valuesDb"],b["spectrum"]["valuesDb"]);self.assertEqual(a["truthClass"],"UNVERIFIED_SOURCE");self.assertEqual(b["truthClass"],"RECORDED_AUTHENTIC_VERIFIED")
    def test_wola_suppresses_far_sidelobes(self):
        x=tone(1024,1024,30.35,256);a=simple_fft_spectrum(x,256);w=wola_spectrum(x,256,4)
        def margin(p):
            peak=max(range(len(p)),key=p.__getitem__);return p[peak]-max(v for i,v in enumerate(p) if abs(i-peak)>2)
        self.assertGreater(margin(w),margin(a)+20)
    def test_bin_width_and_integration_semantics(self):
        p=DeepSpaceSpectrometer(SpectrometerConfig(mode="WOLA",nfft=256,taps=4,integration_method="INCOHERENT",integration_windows=2)).process(tone(2048,1024,31,256),1024);self.assertAlmostEqual(p.bin_width_hz,4);self.assertEqual(p.window_count,2);self.assertEqual(p.units,"dBFS_RELATIVE")
    def test_rfi_stationary_rejected_and_drift_retained(self):
        h=[[-60.0]*16 for _ in range(5)]
        for row in h:row[4]=-10
        mask=build_stationary_mask(h,threshold_mad=5);self.assertIn(4,mask.masked_bins)
        good=candidate_score(frequency_residual_hz=1,drift_residual_hz_s=.02,persistence=.95,snr_db=12,stationary_rfi=False,off_target_conflict=False);bad=candidate_score(frequency_residual_hz=1,drift_residual_hz_s=.02,persistence=.95,snr_db=12,stationary_rfi=True,off_target_conflict=False);self.assertEqual(good["classification"],"CANDIDATE");self.assertLess(bad["score"],good["score"])
    def test_station_physics(self):
        out=evaluate_station(StationInputs(antenna_diameter_m=20,aperture_efficiency=.6,system_temperature_k=50,bandwidth_hz=1,integration_seconds=100,polarization="dual",frequency_hz=8.42e9,calibrated=True));self.assertEqual(out["classification"],"STATION_MODEL_CALIBRATED");self.assertGreater(out["antennaGainDbi"],50);self.assertGreater(out["sefdJy"],0);self.assertEqual(evaluate_station(StationInputs())["classification"],"STATION_MODEL_INCOMPLETE")
    def test_observation_window(self):
        states=[]
        for m in range(3):states.append({"observedAt":f"2026-08-07T12:{m:02d}:00Z","positionKm":[2.4e10,1e10,4e9],"velocityKmS":[16,2,1],"provenance":{"truthClass":"DERIVED_GEOMETRY"}})
        out=observation_window(states,{"lat":-31.4,"lon":-64.2,"elevation":500},8.42e9,-90);self.assertEqual(out["status"],"USABLE_WINDOW");self.assertTrue(out["receiveOnly"]);self.assertEqual(len(out["predictions"]),3)
    def test_evidence_determinism_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"a.zip";q=Path(d)/"b.zip";files={"station.json":{"x":1},"detection.json":{"truth":"SYNTHETIC_TEST"}};a=create_bundle(p,files,"obs","SYNTHETIC_TEST");b=create_bundle(q,files,"obs","SYNTHETIC_TEST");self.assertEqual(a["sha256"],b["sha256"]);self.assertTrue(verify_bundle(p)["valid"])
            with zipfile.ZipFile(p,"a") as z:z.writestr("unexpected.txt",b"x")
            self.assertTrue(verify_bundle(p)["tampered"])
    def test_multi_station_and_decoder_boundary(self):
        self.assertFalse(compare_observations([{"stationId":"a","score":.8},{"stationId":"b","score":.7}],2)["coherentCombination"]);self.assertFalse(decoder_boundary()["voyagerTelemetryClaim"]);self.assertRaises(ValueError,compare_observations,[],3)
    def test_pipeline_truth_preserved(self):
        out=DeepSpaceLabPipeline(SpectrometerConfig(mode="WOLA",nfft=256,taps=4)).process(frame());self.assertEqual(out["truthClass"],"SYNTHETIC_TEST");self.assertEqual(out["pipeline"]["spectrometer"]["mode"],"WOLA")
if __name__=='__main__':unittest.main()
