from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class Station:
    id: str
    name: str
    latitude_deg: float
    longitude_deg: float
    elevation_m: float
    def validate(self) -> "Station":
        if not -90 <= self.latitude_deg <= 90 or not -180 <= self.longitude_deg <= 180 or not -500 <= self.elevation_m <= 10000:
            raise ValueError("station coordinates outside supported WGS84 range")
        return self
