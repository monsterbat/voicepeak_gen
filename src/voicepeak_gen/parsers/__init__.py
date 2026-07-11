"""Input parsers — CSV and JSON → List[Line]."""

from __future__ import annotations

from pathlib import Path

from voicepeak_gen.config import Config
from voicepeak_gen.models import Line
from voicepeak_gen.parsers.csv_parser import parse_csv
from voicepeak_gen.parsers.json_parser import parse_json


def parse(path: Path, config: Config) -> list[Line]:
    """Dispatch by extension."""
    ext = path.suffix.lower()
    if ext in (".csv", ".txt", ".tsv"):
        return parse_csv(path, config)
    if ext == ".json":
        return parse_json(path, config)
    raise ValueError(f"Unsupported file extension: {ext} (expected .csv/.txt/.tsv/.json)")


__all__ = ["parse", "parse_csv", "parse_json"]
