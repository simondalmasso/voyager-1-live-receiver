from __future__ import annotations
import unittest
from voyager_listener.lab.pipeline import DeepSpaceLabPipeline
from voyager_listener.lab.iqbus import CanonicalIQFrame


def frame(sequence:int)->CanonicalIQFrame:
    samples=tuple(complex((i%5)/10,0) for i in range(16))
    return CanonicalIQFrame(
        stream_id="r3-stream",sequence=sequence,sample_start=(sequence-1)*len(samples),sample_count=len(samples),
        sample_rate_hz=3200,center_frequency_hz=8420430000,datatype="complex64",
        timestamp_start=f"2026-08-07T17:4{sequence}:00Z",timestamp_quality="SYNTHETIC",dropped_samples_before=0,
        source_truth_class="SYNTHETIC_TEST",source_provenance_id="r3-backpressure-fixture",samples=samples,
    )


class Order011R3Tests(unittest.TestCase):
    def test_normal_sustained_flow_has_no_artificial_consumer_drops(self):
        pipeline=DeepSpaceLabPipeline()
        out=None
        for sequence in range(1,7):
            out=pipeline.process(frame(sequence))
        self.assertIsNotNone(out)
        self.assertEqual(out["pipeline"]["canonicalIQBus"]["consumerDrops"],0)
        snap=pipeline.bus.snapshot()
        self.assertEqual(set(snap["consumers"]),{"dsp"})
        self.assertEqual(snap["consumers"]["dsp"]["droppedFrames"],0)


if __name__ == "__main__":
    unittest.main()
