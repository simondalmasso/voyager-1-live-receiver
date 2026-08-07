from __future__ import annotations
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from voyager_listener.cli import _horizons_observer_rows
from voyager_listener.dsp.detector import analyze
from voyager_listener.dsp.doppler import classical_observed_frequency, dedrift
from voyager_listener.protocol.snapshot import signal_snapshot
from voyager_listener.provenance import Provenance, utc_now
from voyager_listener.sources.synthetic_source import generate, write_cf32
from voyager_listener.sources.sigmf_source import inspect, read_chunks, verify_manifest
class ListenerTests(unittest.TestCase):
    def test_detects_integrated_dedrifted_tone(self) -> None:
        samples=generate(duration_seconds=8,tone_offset_hz=48,drift_hz_s=.2,amplitude=.24,noise_std=.55)
        d,_=analyze(samples,4096,8_420_430_000,8_420_430_048,drift_hz_s=.2,fft_size=1024,search_half_width_hz=120,threshold_db=7)
        self.assertEqual(d.state,"VERIFIED_CARRIER");self.assertGreater(d.confidence,.7);self.assertGreater(d.persistence_fraction,.5);self.assertAlmostEqual(d.observed_frequency_hz or 0,8_420_430_048,delta=4.1)
    def test_no_signal_is_not_verified(self) -> None:
        samples=generate(duration_seconds=8,include_tone=False,noise_std=.55,seed=99);d,_=analyze(samples,4096,8_420_430_000,8_420_430_000,fft_size=1024,search_half_width_hz=120,threshold_db=10);self.assertNotEqual(d.state,"VERIFIED_CARRIER")
    def test_sigmf_chunked_cf32_and_hash(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            meta=Path(td)/"x.sigmf-meta";data=Path(td)/"x.sigmf-data";samples=generate(duration_seconds=1);digest=write_cf32(data,samples)
            meta.write_text(json.dumps({"global":{"core:datatype":"cf32_le","core:sample_rate":4096,"voyager:truth_class":"SYNTHETIC_TEST","voyager:data_sha256":digest},"captures":[{"core:sample_start":0,"core:frequency":8420430000}]}),encoding="utf-8")
            info=inspect(meta);got=sum(len(c) for c in read_chunks(info,257));self.assertEqual(got,len(samples));self.assertEqual(info.truth_class,"SYNTHETIC_TEST");self.assertEqual(info.data_sha256,digest)
    def test_recorded_name_never_grants_authenticity(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            meta=Path(td)/"recorded-authentic.sigmf-meta";data=Path(td)/"recorded-authentic.sigmf-data";digest=write_cf32(data,generate(duration_seconds=1));meta.write_text(json.dumps({"global":{"core:datatype":"cf32_le","core:sample_rate":4096,"voyager:data_sha256":digest},"captures":[{"core:sample_start":0,"core:frequency":8420430000}]}),encoding="utf-8");self.assertEqual(inspect(meta).truth_class,"UNVERIFIED_SOURCE")
    def test_verified_manifest_checks_both_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);meta=base/"v.sigmf-meta";data=base/"v.sigmf-data";digest=write_cf32(data,generate(duration_seconds=1));g={"core:datatype":"cf32_le","core:sample_rate":4096,"voyager:truth_class":"RECORDED_AUTHENTIC_VERIFIED","voyager:data_sha256":digest,"voyager:source_url":"https://example.invalid/source","voyager:observatory":"TEST","voyager:observation_time":"2020-01-01T00:00:00Z","voyager:license":"test fixture","voyager:transform_chain":"none"};meta.write_text(json.dumps({"global":g,"captures":[{"core:sample_start":0,"core:frequency":8420430000}]}),encoding="utf-8");mh=hashlib.sha256(meta.read_bytes()).hexdigest();manifest=base/"manifest.json";manifest.write_text(json.dumps({"sigmfMeta":meta.name,"sigmfData":data.name,"metadataSha256":mh,"dataSha256":digest,"sourceUrl":"https://example.invalid/source","observatory":"TEST","observationTime":"2020-01-01T00:00:00Z","license":"test fixture","transformChain":"none"}),encoding="utf-8");self.assertTrue(verify_manifest(manifest)["valid"])
    def test_snapshot_rejects_fake_live(self) -> None:
        d,_=analyze(generate(duration_seconds=4),4096,8420430000,8420430000,fft_size=1024)
        with self.assertRaises(ValueError):signal_snapshot(d,[-1.0],stream_id="x",sequence=1,source_mode="TELESCOPE_LIVE_VERIFIED",station_id="x",station_name="x",started_at=utc_now(),sample_rate_hz=4096,center_frequency_hz=8420430000,datatype="cf32_le",bin_width_hz=4,provenance=Provenance("UNVERIFIED_SOURCE","x",utc_now()))
    def test_horizons_quantity20_parser(self) -> None:
        text="header\n$$SOE\n2026-Aug-07 08:00:00.000, *, 168.5, 16.20\n2026-Aug-07 08:01:00.000, *, 168.5, 16.19\n$$EOE\n";rows=_horizons_observer_rows(text);self.assertEqual(len(rows),2);self.assertAlmostEqual(rows[0]["rangeRateKmS"],16.2)
    def test_doppler_sign(self) -> None:self.assertLess(classical_observed_frequency(1000,1000),1000)
if __name__=="__main__":unittest.main()
