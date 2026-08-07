from __future__ import annotations
import cmath, math
from dataclasses import dataclass
from statistics import fmean
from voyager_listener.dsp.fft import fft, hann

def _shift(values:list[complex])->list[complex]:
    h=len(values)//2; return values[h:]+values[:h]
def _db(power:float)->float: return 10*math.log10(max(power,1e-20))
def _prototype(nfft:int,taps:int)->list[float]:
    total=nfft*taps; out=[]
    for i in range(total):
        t=(i-(total-1)/2)/nfft
        sinc=1.0 if abs(t)<1e-15 else math.sin(math.pi*t)/(math.pi*t)
        window=.5-.5*math.cos(2*math.pi*i/(total-1))
        out.append(sinc*window)
    return out

def simple_fft_spectrum(samples:list[complex],nfft:int)->list[float]:
    if len(samples)<nfft: raise ValueError("insufficient samples")
    w=hann(nfft); z=fft([samples[i]*w[i] for i in range(nfft)])
    return [_db(abs(v/nfft)**2) for v in _shift(z)]

def wola_spectrum(samples:list[complex],nfft:int,taps:int=4)->list[float]:
    required=nfft*taps
    if taps<2 or len(samples)<required: raise ValueError("insufficient WOLA samples")
    p=_prototype(nfft,taps)
    poly=[sum(samples[k+m*nfft]*p[k+m*nfft] for m in range(taps)) for k in range(nfft)]
    z=fft(poly)
    return [_db(abs(v/nfft)**2) for v in _shift(z)]

def channelize(samples:list[complex],sample_rate_hz:float,offset_hz:float,bandwidth_hz:float)->tuple[list[complex],float]:
    if sample_rate_hz<=0 or bandwidth_hz<=0 or bandwidth_hz>sample_rate_hz: raise ValueError("invalid channelizer rates")
    mixed=[v*cmath.exp(-2j*math.pi*offset_hz*i/sample_rate_hz) for i,v in enumerate(samples)]
    factor=max(1,int(sample_rate_hz//max(bandwidth_hz*2,1)))
    if factor==1:return mixed,sample_rate_hz
    reduced=[sum(mixed[i:i+factor])/factor for i in range(0,len(mixed)-factor+1,factor)]
    return reduced,sample_rate_hz/factor

@dataclass(frozen=True,slots=True)
class SpectrometerConfig:
    mode:str="WOLA"
    nfft:int=256
    taps:int=4
    integration_method:str="INCOHERENT"
    integration_windows:int=1
    channel_bandwidth_hz:float|None=None
    def __post_init__(self):
        if self.mode not in {"SIMPLE_FFT","WOLA"}:raise ValueError("invalid spectrometer mode")
        if self.nfft<16 or self.nfft&(self.nfft-1):raise ValueError("nfft must be power of two")
        if self.taps<2:raise ValueError("taps must be >=2")
        if self.integration_method not in {"COHERENT","INCOHERENT","ROLLING","ACCUMULATED"}:raise ValueError("invalid integration method")
        if self.integration_windows<1:raise ValueError("integration_windows")

@dataclass(frozen=True,slots=True)
class SpectrumProduct:
    mode:str; values_db:tuple[float,...]; bin_width_hz:float; integration_method:str; integration_seconds:float; window_count:int; units:str="dBFS_RELATIVE"
    def as_dict(self): return {"mode":self.mode,"binWidthHz":self.bin_width_hz,"integrationMethod":self.integration_method,"integrationSeconds":self.integration_seconds,"windowCount":self.window_count,"units":self.units,"valuesDb":list(self.values_db)}

class DeepSpaceSpectrometer:
    def __init__(self,config:SpectrometerConfig):self.config=config
    def process(self,samples:list[complex],sample_rate_hz:float)->SpectrumProduct:
        c=self.config; span=c.nfft*(c.taps if c.mode=="WOLA" else 1); count=min(c.integration_windows,len(samples)//span)
        if count<1: raise ValueError("insufficient samples for spectrometer")
        spectra=[]
        for w in range(count):
            chunk=samples[w*span:(w+1)*span]
            spectra.append(wola_spectrum(chunk,c.nfft,c.taps) if c.mode=="WOLA" else simple_fft_spectrum(chunk,c.nfft))
        if c.integration_method=="COHERENT":
            aligned=[sum(samples[w*span+i] for w in range(count))/count for i in range(span)]
            values=wola_spectrum(aligned,c.nfft,c.taps) if c.mode=="WOLA" else simple_fft_spectrum(aligned,c.nfft)
        else:
            linear=[[10**(v/10) for v in row] for row in spectra]
            values=[_db(fmean(row[i] for row in linear)) for i in range(c.nfft)]
        return SpectrumProduct(c.mode,tuple(values),sample_rate_hz/c.nfft,c.integration_method,count*span/sample_rate_hz,count)
