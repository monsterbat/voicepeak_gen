"""Split Lines into Segments respecting Voicepeak's 140-character CLI limit.

Strategy: prefer breaking on Japanese sentence terminators (。！？!?), then on
secondary punctuation (、,，), then hard-wrap. Each Line yields >= 1 Segments
with the same narrator/emotion/speed/pitch.
"""

from __future__ import annotations

import re

from voicepeak_gen.models import Line, Segment


# Primary breakpoints — full-stop level (keep terminator with preceding chunk).
_PRIMARY = re.compile(r"([。！？!?]+)")
# Secondary — commas, when a piece is still over the limit.
_SECONDARY = re.compile(r"([、，,])")


def _split_keeping_delim(text: str, pattern: re.Pattern[str]) -> list[str]:
    """Split on `pattern`, attaching the delimiter to the preceding piece."""
    parts = pattern.split(text)
    out: list[str] = []
    buf = ""
    for piece in parts:
        if pattern.fullmatch(piece):
            buf += piece
            out.append(buf)
            buf = ""
        else:
            buf += piece
    if buf:
        out.append(buf)
    return [p.strip() for p in out if p.strip()]


def _chunk(text: str, max_chars: int) -> list[str]:
    """Recursive split: primary → secondary → hard wrap."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    # Try primary breaks first.
    pieces = _split_keeping_delim(text, _PRIMARY)
    if len(pieces) > 1:
        return _greedy_merge(pieces, max_chars)

    # Then secondary.
    pieces = _split_keeping_delim(text, _SECONDARY)
    if len(pieces) > 1:
        return _greedy_merge(pieces, max_chars)

    # Hard wrap fallback.
    return [text[i : i + max_chars] for i in range(0, len(text), max_chars)]


def _greedy_merge(pieces: list[str], max_chars: int) -> list[str]:
    """Pack pieces back together greedily, never exceeding max_chars."""
    out: list[str] = []
    current = ""
    for p in pieces:
        if len(p) > max_chars:
            # piece itself too long — recurse one level
            if current:
                out.append(current)
                current = ""
            out.extend(_chunk(p, max_chars))
            continue
        if not current:
            current = p
        elif len(current) + len(p) <= max_chars:
            current += p
        else:
            out.append(current)
            current = p
    if current:
        out.append(current)
    return out


def split_lines(lines: list[Line], max_chars: int = 140) -> list[Segment]:
    segments: list[Segment] = []
    idx = 0
    for line in lines:
        chunks = _chunk(line.text, max_chars)
        for chunk in chunks:
            segments.append(
                Segment(
                    index=idx,
                    narrator=line.narrator,
                    text=chunk,
                    emotion=line.emotion,
                    speed=line.speed,
                    pitch=line.pitch,
                )
            )
            idx += 1
    return segments
