import argparse,cmath,contextlib,io,json,math,tempfile,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from unittest.mock import patch
from voyager_listener.cli import DEFAULT_CARRIER_HZ,analyze_meta,live_command,synth_command
from voyager_listener.lab.adapters import frames_from_chunks
from voyager_listener.lab.iqbus import CanonicalIQFrame
from voyager_listener.lab.observation import topocentric
from voyager_listener.lab.pipeline import DeepSpaceLabPipeline
from voyager_listener.lab.rfi import candidate_score
from voyager_listener.lab.spectrometer import DeepSpaceSpectrometer,SpectrometerConfig
from voyager_listener.provenance import Provenance

def tone(count,fs,bin_pos,nfft):return [cmath.exp(2j*math.pi*(bin_pos*fs/nfft)*i/fs) for i in range(count)]
def frame(seq=0,samples=None,dropped=0):
    s=tuple(samples or tone(1024,1024,30.35,256));at=(datetime(2026,8,7,12,0,tzinfo=timezone.utc)+timedelta(seconds=seq)).isoformat().replace('+00:00','Z');return CanonicalIQFrame('s',seq,seq*len(s),len(s),1024,8420430000,'complex64',at,'SYNTHETIC',dropped,'SYNTHETIC_TEST','prov',s)
class R2Tests(unittest.TestCase):
    def test_rotating_observer_range_rate_matches_finite_difference(self):
        station={'lat':-31.4,'lon':-64.2,'elevation':500};pos=[2.4e10,1e10,4e9];vel=[16,2,1];at=datetime(2026,8,7,12,0,tzinfo=timezone.utc);dt=.5
        def sample(delta):
            t=at+timedelta(seconds=delta);p=[pos[i]+vel[i]*delta for i in range(3)];return topocentric(p,station['lat'],station['lon'],station['elevation'],t.isoformat(),vel)
        center=sample(0);fd=(sample(dt)['rangeKm']-sample(-dt)['rangeKm'])/(2*dt);geo=sum(pos[i]*vel[i] for i in range(3))/math.sqrt(sum(x*x for x in pos));self.assertAlmostEqual(center['rangeRateKmS'],fd,places=4);self.assertGreater(abs(center['rangeRateKmS']-geo),1e-3);self.assertGreater(math.sqrt(sum(x*x for x in center['observerVelocityKmS'])),.1)
    def test_candidate_score_fails_closed_without_measured_features(self):
        out=candidate_score(frequency_residual_hz=0,drift_residual_hz_s=None,persistence=None,snr_db=12,stationary_rfi=None,off_target_conflict=None);self.assertEqual(out['classification'],'INSUFFICIENT_EVIDENCE');self.assertIsNone(out['score']);self.assertIn('driftResidualHzS',out['missing'])
    def test_rolling_and_accumulated_have_real_bounded_state(self):
        a=tone(1024,1024,20,256);b=tone(1024,1024,40,256);rolling=DeepSpaceSpectrometer(SpectrometerConfig(mode='WOLA',nfft=256,taps=4,integration_method='ROLLING',integration_windows=2));r1=rolling.process(a,1024);r2=rolling.process(b,1024);r3=rolling.process(a,1024);self.assertTrue(r2.stateful);self.assertEqual(r2.window_count,2);self.assertEqual(r3.window_count,2);self.assertNotEqual(r1.values_db,r2.values_db)
        acc=DeepSpaceSpectrometer(SpectrometerConfig(mode='WOLA',nfft=256,taps=4,integration_method='ACCUMULATED',integration_windows=1,accumulation_limit_windows=2));self.assertEqual(acc.process(a,1024).window_count,1);self.assertEqual(acc.process(b,1024).window_count,2);p3=acc.process(a,1024);self.assertEqual(p3.window_count,2);self.assertTrue(p3.saturated);acc.reset();self.assertEqual(acc.process(a,1024).window_count,1)
    def test_pipeline_measures_features_and_propagates_gap(self):
        pipe=DeepSpaceLabPipeline(SpectrometerConfig(mode='WOLA',nfft=256,taps=4));off=[-120.0]*256;station={'id':'fixture'};out=None
        for seq in (0,1,2):out=pipe.process(frame(seq),expected_frequency_hz=8420430000,expected_drift_hz_s=0,off_target_values_db=off,station=station)
        for key in ('snrDb','frequencyResidualHz','driftResidualHzS','persistence','stationaryRfi','offTargetConflict'):self.assertIsNotNone(out['measured'][key])
        self.assertEqual(out['evidence']['status'],'READY_CANONICAL_MANIFEST');gap=pipe.process(frame(4,dropped=17),expected_frequency_hz=8420430000,expected_drift_hz_s=0,off_target_values_db=off,station=station);self.assertGreaterEqual(gap['pipeline']['source']['sequenceGaps'],1);self.assertIn('SOURCE_GAP_BUFFER_RESET',gap['pipeline']['errors'])
    def test_noise_only_never_becomes_candidate(self):
        pipe=DeepSpaceLabPipeline(SpectrometerConfig(mode='WOLA',nfft=256,taps=4));out=None
        for seq in range(3):out=pipe.process(frame(seq,[0j]*1024),expected_frequency_hz=8420430000,expected_drift_hz_s=0,off_target_values_db=[-120.0]*256,station={'id':'fixture'})
        self.assertNotEqual(out['candidate']['classification'],'CANDIDATE')
    def test_cli_analyze_and_live_use_canonical_pipeline(self):
        with tempfile.TemporaryDirectory() as d:
            meta=str(Path(d)/'fixture.sigmf-meta');synth_command(argparse.Namespace(output=meta,no_signal=False,seed=1701));snap,_=analyze_meta(meta,DEFAULT_CARRIER_HZ+48,.2,256,.5,None);self.assertIn('labPipeline',snap);self.assertIn('evidence',snap);self.assertEqual(snap['evidence']['manifest']['truthClass'],'SYNTHETIC_TEST')
        samples=tone(1024,1024,10,256);frames=frames_from_chunks([samples,samples,samples],stream_id='live-cli',sample_rate_hz=1024,center_frequency_hz=DEFAULT_CARRIER_HZ,truth_class='UNVERIFIED_SOURCE',provenance_id='live-cli',start_time='2026-08-07T12:00:00Z',timestamp_quality='HOST');args=argparse.Namespace(fft_size=256,sample_rate_hz=1024,integration_seconds=1,expected_frequency_hz=DEFAULT_CARRIER_HZ,drift_hz_s=0)
        with patch('voyager_listener.cli._live_frames',return_value=(frames,'2026-08-07T12:00:00Z',Provenance('UNVERIFIED_SOURCE','test','2026-08-07T12:00:00Z'))),io.StringIO() as buf,contextlib.redirect_stdout(buf):
            self.assertEqual(live_command(args),0);lines=[json.loads(x) for x in buf.getvalue().splitlines() if x.strip()];self.assertTrue(lines);self.assertTrue(all(x['labPipeline']['canonicalIQBus']['status']=='OPERATIONAL' for x in lines))
if __name__=='__main__':unittest.main()
