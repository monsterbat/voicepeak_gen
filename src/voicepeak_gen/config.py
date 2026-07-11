"""Config loading: ~/.config/voicepeak_gen/config.yaml + package defaults."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated

import yaml
from pydantic import BaseModel, ConfigDict, Field


DEFAULT_CONFIG_PATH = Path(
    os.environ.get(
        "VOICEPEAK_GEN_CONFIG",
        Path.home() / ".config" / "voicepeak_gen" / "config.yaml",
    )
)

# Bundled defaults — tuned for SC's macOS install with the three current voices.
BUILTIN_DEFAULTS: dict = {
    "voicepeak_path": "/Applications/voicepeak.app/Contents/MacOS/voicepeak",
    "ffmpeg_path": "/opt/homebrew/bin/ffmpeg",
    "narrator_aliases": {
        # Convenience names users can put in CSV instead of full narrator names.
        "moca": "Miyamai Moca",
        "rikka": "Koharu Rikka",
        "frimomen": "Frimomen",
        # Chinese shortcuts
        "茉歌": "Miyamai Moca",
        "六花": "Koharu Rikka",
    },
    "defaults": {
        "speed": 100,
        "pitch": 0,
        "gap_ms": 300,
        "output_format": "wav",
        "max_chars": 140,
    },
}


class Defaults(BaseModel):
    model_config = ConfigDict(extra="forbid")

    speed: Annotated[int, Field(ge=50, le=200)] = 100
    pitch: Annotated[int, Field(ge=-300, le=300)] = 0
    gap_ms: Annotated[int, Field(ge=0, le=5000)] = 300
    output_format: str = "wav"
    max_chars: Annotated[int, Field(ge=10, le=140)] = 140


class Config(BaseModel):
    model_config = ConfigDict(extra="forbid")

    voicepeak_path: Path
    ffmpeg_path: Path
    narrator_aliases: dict[str, str] = Field(default_factory=dict)
    defaults: Defaults = Field(default_factory=Defaults)

    def resolve_narrator(self, name: str) -> str:
        """Look up alias; fall back to the literal name."""
        return self.narrator_aliases.get(name.strip(), name.strip())


def load_config(path: Path | None = None) -> Config:
    """Load config from yaml; missing file → use bundled defaults."""
    raw = dict(BUILTIN_DEFAULTS)
    target = path or DEFAULT_CONFIG_PATH

    if target.exists():
        with target.open(encoding="utf-8") as f:
            overrides = yaml.safe_load(f) or {}
        # shallow merge: top-level keys; for narrator_aliases / defaults do dict-merge
        for key, value in overrides.items():
            if key in ("narrator_aliases", "defaults") and isinstance(value, dict):
                raw[key] = {**raw[key], **value}
            else:
                raw[key] = value

    return Config.model_validate(raw)
