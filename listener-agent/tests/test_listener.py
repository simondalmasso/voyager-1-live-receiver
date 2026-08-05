from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from voyager_listener.dsp.detector import analyze
from voyager_listener.dsp.doppler import classical_observed_frequency, dedrift
from voyager_listener.sources.synthetic_source import generate, write_cf32
from voyager_listener.sources.sigmf_source import inspect, read_chunks
class ListenerTests(unittest.TestCase):
    def test_detects_integrated_dedrifted_tone(self) -> None:
        samples=generate(duration_seconds=8,tone_offset_hz=48,drift_hz_s=.2,amplitude=.24,noise_std=.55)
        d,_=analyze(samples,4096,8_420_430_000,8_420_430_048,drift_hz_s=.2,fft_size=1024,search_half_width_hz=120,threshold_db=7)
        self.assertEqual(d.state,"DETECTED"); self.assertGreater(d.confidence,.7); self.assertAlmostEqual(d.observed_frequency_hz or 0,8_420_430_048,delta=4.1)
    def test_no_signal_is_not_detected(self) -> None:
        samples=generate(duration_seconds=8,include_tone=False,noise_std=.55,seed=99)
        d,_=analyze(samples,4096,8_420_430_000,8_420_430_000,fft_size=1024,search_half_width_hz=120,threshold_db=10)
        self.assertNotEqual(d.state,"DETECTED")
    def test_sigmf_chunked_cf32(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            meta=Path(td)/"x.sigmf-meta"; data=Path(td)/"x.sigmf-data"; samples=generate(duration_seconds=1); write_cf32(data,samples)
            meta.write_text(json.dumps({"global":{"core:datatype":"cf32_le","core:sample_rate":4096},"captures":[{"core:sample_start":0,"core:frequency":8420430000}]}),encoding="utf-8")
            info=inspect(meta); got=sum(len(c) for c in read_chunks(info,257)); self.assertEqual(got,len(samples))
    def test_doppler_sign(self) -> None:
        self.assertLess(classical_observed_frequency(1000,1000),1000)
if __name__=="__main__": unittest.main()
