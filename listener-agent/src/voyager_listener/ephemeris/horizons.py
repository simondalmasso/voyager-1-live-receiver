from __future__ import annotations
from urllib.parse import urlencode

def topocentric_query(*, start_time: str, stop_time: str, latitude_deg: float, longitude_deg: float, elevation_m: float) -> str:
    site = f"{longitude_deg},{latitude_deg},{elevation_m / 1000.0}"
    params = {"format":"text","COMMAND":"'-31'","OBJ_DATA":"NO","MAKE_EPHEM":"YES","EPHEM_TYPE":"OBSERVER","CENTER":"'coord@399'","SITE_COORD":f"'{site}'","START_TIME":f"'{start_time}'","STOP_TIME":f"'{stop_time}'","STEP_SIZE":"'1 m'","QUANTITIES":"'20'","CSV_FORMAT":"YES"}
    return "https://ssd.jpl.nasa.gov/api/horizons.api?" + urlencode(params)
