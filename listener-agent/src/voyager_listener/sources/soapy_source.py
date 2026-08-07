from __future__ import annotations
from typing import Iterator

def open_device(driver: str, **settings: object) -> object:
    try:
        import SoapySDR  # type: ignore
    except ImportError as exc:
        raise RuntimeError("SoapySDR is optional. Install the hardware extra and the system driver for your SDR.") from exc
    return SoapySDR.Device({"driver":driver,**{k:str(v) for k,v in settings.items()}})

def cf32_chunks(driver: str,sample_rate_hz: float,center_frequency_hz: float,chunk_samples: int=16384,**settings: object)->Iterator[list[complex]]:
    try:
        import SoapySDR  # type: ignore
        from SoapySDR import SOAPY_SDR_CF32, SOAPY_SDR_RX  # type: ignore
    except ImportError as exc:
        raise RuntimeError("SoapySDR is optional. Install the hardware extra and system driver.") from exc
    if sample_rate_hz<=0 or center_frequency_hz<=0 or chunk_samples<=0:raise ValueError("invalid SDR configuration")
    dev=SoapySDR.Device({"driver":driver,**{k:str(v) for k,v in settings.items()}});dev.setSampleRate(SOAPY_SDR_RX,0,sample_rate_hz);dev.setFrequency(SOAPY_SDR_RX,0,center_frequency_hz);stream=dev.setupStream(SOAPY_SDR_RX,SOAPY_SDR_CF32,[0]);dev.activateStream(stream)
    try:
        import array
        while True:
            buf=array.array('f',[0.0])*(chunk_samples*2);result=dev.readStream(stream,[buf],chunk_samples,timeoutUs=2_000_000);count=int(getattr(result,'ret',-1))
            if count<0:continue
            yield [complex(buf[i],buf[i+1]) for i in range(0,count*2,2)]
    finally:
        try:dev.deactivateStream(stream)
        finally:dev.closeStream(stream)
