"""Internal data structures shared across parsers, splitter, synthesizer."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


EmotionDict = dict[str, Annotated[int, Field(ge=0, le=100)]]


class Line(BaseModel):
    """One spoken line, before splitting. Comes from a parser."""

    model_config = ConfigDict(extra="forbid")

    narrator: str
    text: str = Field(min_length=1)
    emotion: EmotionDict = Field(default_factory=dict)
    speed: Annotated[int, Field(ge=50, le=200)] = 100
    pitch: Annotated[int, Field(ge=-300, le=300)] = 0


class Segment(BaseModel):
    """A line after splitting (<= max_chars per piece). 1:1 with one wav file."""

    model_config = ConfigDict(extra="forbid")

    index: int
    narrator: str
    text: str
    emotion: EmotionDict = Field(default_factory=dict)
    speed: int = 100
    pitch: int = 0
    wav_path: Path | None = None
