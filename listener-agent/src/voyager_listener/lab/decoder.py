from __future__ import annotations
from typing import Protocol,Any

class DemodulatorPlugin(Protocol):
    def demodulate(self,carrier_product:dict[str,Any])->dict[str,Any]:...
class FramerFECPlugin(Protocol):
    def frame(self,demodulated:dict[str,Any])->dict[str,Any]:...
class TelemetryDecoderPlugin(Protocol):
    def decode(self,framed:dict[str,Any])->dict[str,Any]:...

def decoder_boundary()->dict:
    return {"input":"CarrierDetectorProduct","stages":["optional DemodulatorPlugin","optional Framer/FECPlugin","optional TelemetryDecoderPlugin"],"implementedDecoder":False,"voyagerTelemetryClaim":False,"reason":"Order 011 deliberately defines a boundary without claiming a demonstrated current Voyager telemetry format."}
