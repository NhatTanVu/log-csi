from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import yaml

@dataclass
class Profile:
    name: str
    type: str
    raw: dict

def load_profile(path: str) -> Profile:
    p = Path(path)
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    return Profile(name=path, type=data["type"], raw=data)