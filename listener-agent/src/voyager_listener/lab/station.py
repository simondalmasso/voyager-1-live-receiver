from __future__ import annotations
import math
from dataclasses import dataclass
K_B=1.380649e-23
C=299792458.0

@dataclass(frozen=True,slots=True)
class StationInputs:
    antenna_diameter_m:float|None=None
    effective_area_m2:float|None=None
    aperture_efficiency:float|None=None
    system_temperature_k:float|None=None
    receiver_noise_figure_db:float|None=None
    bandwidth_hz:float|None=None
    integration_seconds:float|None=None
    polarization:str|None=None
    frequency_hz:float|None=None
    losses_db:float=0.0
    calibrated:bool=False

def evaluate_station(v:StationInputs)->dict:
    missing=[]
    if not v.frequency_hz:missing.append("frequencyHz")
    area=v.effective_area_m2
    if area is None and v.antenna_diameter_m and v.aperture_efficiency: area=math.pi*(v.antenna_diameter_m/2)**2*v.aperture_efficiency
    if area is None:missing.append("effectiveAreaM2 or diameter+efficiency")
    temp=v.system_temperature_k; temp_source="MEASURED" if temp else None
    if temp is None and v.receiver_noise_figure_db is not None: temp=290*(10**(v.receiver_noise_figure_db/10)-1);temp_source="NOISE_FIGURE_EQUIVALENT"
    if temp is None:missing.append("systemTemperatureK or receiverNoiseFigureDb")
    if not v.bandwidth_hz:missing.append("bandwidthHz")
    if not v.integration_seconds:missing.append("integrationSeconds")
    if missing:return {"classification":"STATION_MODEL_INCOMPLETE","feasibility":"FEASIBILITY_ESTIMATE_UNAVAILABLE","missing":missing}
    assert area and temp and v.frequency_hz and v.bandwidth_hz and v.integration_seconds
    wavelength=C/v.frequency_hz; gain_linear=4*math.pi*area/wavelength**2; gain_dbi=10*math.log10(gain_linear)-v.losses_db
    gt=gain_dbi-10*math.log10(temp); sefd=2*K_B*temp/area*1e26; npol=2 if (v.polarization or "").lower() in {"dual","2","dual-pol"} else 1
    sigma=sefd/math.sqrt(npol*v.bandwidth_hz*v.integration_seconds); hpbw=70*wavelength/v.antenna_diameter_m if v.antenna_diameter_m else None
    classification="STATION_MODEL_CALIBRATED" if v.calibrated and temp_source=="MEASURED" else "STATION_MODEL_ESTIMATED"
    return {"classification":classification,"feasibility":"FEASIBILITY_ESTIMATE","assumptions":["radiometer-equation thermal-noise estimate","no claim of Voyager detectability","SEFD uses 2*k*Tsys/Aeff"],"effectiveAreaM2":area,"antennaGainDbi":gain_dbi,"hpbwDeg":hpbw,"gOverTDbPerK":gt,"sefdJy":sefd,"radiometerSigmaJy":sigma,"integrationNoiseReduction":math.sqrt(npol*v.bandwidth_hz*v.integration_seconds),"systemTemperatureK":temp,"temperatureSource":temp_source,"polarizations":npol}
