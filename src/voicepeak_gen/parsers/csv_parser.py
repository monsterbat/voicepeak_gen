"""CSV/TSV/text parser.

Format: `narrator<delim>text`, one line per row.
- Delimiter is auto-detected per row: tab if present, else first comma.
- Lines starting with '#' or blank are skipped.
- Narrator is resolved through Config.narrator_aliases.
"""

from __future__ import annotations

from pathlib import Path

from voicepeak_gen.config import Config
from voicepeak_gen.models import Line


def parse_csv(path: Path, config: Config) -> list[Line]:
    raw = path.read_text(encoding="utf-8")
    lines: list[Line] = []

    for lineno, row in enumerate(raw.splitlines(), start=1):
        stripped = row.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if "\t" in row:
            narrator, _, text = row.partition("\t")
        elif "," in row:
            narrator, _, text = row.partition(",")
        else:
            raise ValueError(
                f"{path}:{lineno}: row has no tab/comma delimiter — "
                f"expected `narrator,text`"
            )

        narrator = config.resolve_narrator(narrator)
        text = text.strip()
        if not text:
            raise ValueError(f"{path}:{lineno}: empty text after delimiter")

        lines.append(
            Line(
                narrator=narrator,
                text=text,
                speed=config.defaults.speed,
                pitch=config.defaults.pitch,
            )
        )

    if not lines:
        raise ValueError(f"{path}: no usable rows found")
    return lines
