from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any
@dataclass(frozen=True)
class Provenance:
    truth_class: str
    source_id: str
    fetched_at: str
    source_url: str | None = None
    fallback_reason: str | None = None
    def to_wire(self) -> dict[str, Any]:
        data = asdict(self)
        return {"truthClass": data.pop("truth_class"), "sourceId": data.pop("source_id"), "fetchedAt": data.pop("fetched_at"), **{_camel(k): v for k, v in data.items() if v is not None}}
def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
def _camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part.title() for part in tail)
