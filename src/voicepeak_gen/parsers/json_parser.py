"""JSON parser.

Expected shape: a top-level list of objects:
    [
      {"narrator": "Miyamai Moca", "text": "...", "emotion": {"happy": 50}, "speed": 100, "pitch": 0},
      ...
    ]
Only `narrator` and `text` are required. Aliases are resolved against config.
"""

from __future__ import annotations

import json
from pathlib import Path

from voicepeak_gen.config import Config
from voicepeak_gen.models import Line


def parse_json(path: Path, config: Config) -> list[Line]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path}: top-level JSON must be a list of objects")

    lines: list[Line] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"{path}: item #{i} is not an object")

        narrator = item.get("narrator")
        text = item.get("text")
        if not narrator or not text:
            raise ValueError(f"{path}: item #{i} missing narrator or text")

        merged = {
            "narrator": config.resolve_narrator(narrator),
            "text": str(text).strip(),
            "emotion": item.get("emotion", {}),
            "speed": item.get("speed", config.defaults.speed),
            "pitch": item.get("pitch", config.defaults.pitch),
        }
        lines.append(Line.model_validate(merged))

    if not lines:
        raise ValueError(f"{path}: empty list")
    return lines
