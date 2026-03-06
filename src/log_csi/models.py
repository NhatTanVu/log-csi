from __future__ import annotations
from pydantic import Field, BaseModel
from typing import Any, Optional


class SourceRef(BaseModel):
    path: str
    line_start: int
    line_end: int


class LogEvent(BaseModel):
    ts_event: float
    service: str
    severity: str = "INFO"
    message: str
    attrs: dict[str, Any] = Field(default_factory=dict)
    source_ref: Optional[SourceRef] = None
