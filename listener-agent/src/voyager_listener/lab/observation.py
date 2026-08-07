from __future__ import annotations
import math
from datetime import datetime,timezone
C_KM_S=299792.458; EARTH_A_KM=6378.137; E2=6.69437999014e-3

def _dt(s:str)->datetime:return datetime.fromisoformat(s.replace("Z","+00:00")).astimezone(timezone.utc)
def _mag(v):return math.sqrt(sum(x*x for x in v))
def _dot(a,b):return sum(x*y for x,y in zip(a,b))
def gmst_deg(at:str)->float:
    jd=_dt(at).timestamp()/86400+2440587.5;t=(jd-2451545.0)/36525
    return (280.46061837+360.98564736629*(jd-2451545.0)+.000387933*t*t-t*t*t/38710000)%360

def topocentric(position_km:list[float],lat_deg:float,lon_deg:float,elevation_m:float,at:str)->dict:
    if not(-90<=lat_deg<=90 and -180<=lon_deg<=180):raise ValueError("invalid station coordinates")
    phi=math.radians(lat_deg);lam=math.radians(lon_deg);h=elevation_m/1000;s=math.sin(phi);c=math.cos(phi);n=EARTH_A_KM/math.sqrt(1-E2*s*s)
    ecef=[(n+h)*c*math.cos(lam),(n+h)*c*math.sin(lam),(n*(1-E2)+h)*s];th=math.radians(gmst_deg(at))
    obs=[math.cos(th)*ecef[0]-math.sin(th)*ecef[1],math.sin(th)*ecef[0]+math.cos(th)*ecef[1],ecef[2]];v=[position_km[i]-obs[i] for i in range(3)];r=_mag(v)
    ra=math.atan2(v[1],v[0])%(2*math.pi);dec=math.asin(v[2]/r);lst=math.radians((gmst_deg(at)+lon_deg)%360);ha=lst-ra
    alt=math.asin(math.sin(phi)*math.sin(dec)+math.cos(phi)*math.cos(dec)*math.cos(ha));az=math.atan2(-math.sin(ha)*math.cos(dec),math.sin(dec)*math.cos(phi)-math.cos(dec)*math.sin(phi)*math.cos(ha))%(2*math.pi)
    return {"azimuthDeg":math.degrees(az),"elevationDeg":math.degrees(alt),"raDeg":math.degrees(ra),"decDeg":math.degrees(dec),"rangeKm":r}

def make_prediction(state:dict,station:dict,carrier_hz:float)->dict:
    pos=[float(x) for x in state["positionKm"]];vel=[float(x) for x in state["velocityKmS"]];at=state["observedAt"];geo=topocentric(pos,float(station["lat"]),float(station["lon"]),float(station.get("elevation",0)),at);rr=_dot(pos,vel)/max(_mag(pos),1);doppler=-carrier_hz*rr/C_KM_S
    return {"timestampUtc":at,**geo,"rangeRateKmS":rr,"expectedDopplerHz":doppler,"expectedCarrierHz":carrier_hz+doppler,"provenance":state.get("provenance",{})}

def observation_window(states:list[dict],station:dict,carrier_hz:float,min_elevation_deg:float=10)->dict:
    predictions=[make_prediction(s,station,carrier_hz) for s in states];usable=[p for p in predictions if p["elevationDeg"]>=min_elevation_deg]
    if not usable:return {"status":"NO_USABLE_WINDOW","minElevationDeg":min_elevation_deg,"predictions":predictions}
    peak=max(usable,key=lambda p:p["elevationDeg"]);start=usable[0];end=usable[-1]
    return {"status":"USABLE_WINDOW","minElevationDeg":min_elevation_deg,"start":start,"peak":peak,"end":end,"expectedCarrierRegionHz":[min(p["expectedCarrierHz"] for p in usable),max(p["expectedCarrierHz"] for p in usable)],"predictionFreshness":"DERIVED_FROM_INPUT_STATE_SERIES","advisoryOnly":True,"receiveOnly":True,"predictions":predictions}
