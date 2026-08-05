from __future__ import annotations

def open_device(driver: str, **settings: object) -> object:
    try:
        import SoapySDR  # type: ignore
    except ImportError as exc:
        raise RuntimeError("SoapySDR is optional. Install the hardware extra and the system driver for your SDR.") from exc
    return SoapySDR.Device({"driver": driver, **{k: str(v) for k, v in settings.items()}})
