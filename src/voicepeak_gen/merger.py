"""Concatenate wav segments via ffmpeg, optionally with silence gaps.

Approach: generate a silence wav matching the first segment's sample rate, then
build a concat-demuxer file listing [seg, silence, seg, silence, ...]. Final mux
re-encodes to the requested format (wav passthrough / mp3 via libmp3lame).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from voicepeak_gen.config import Config


def _probe_audio(path: Path, ffmpeg_path: Path) -> tuple[int, int]:
    """Return (sample_rate, channels) for a wav file via ffprobe."""
    ffprobe = ffmpeg_path.parent / "ffprobe"
    proc = subprocess.run(
        [
            str(ffprobe),
            "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=sample_rate,channels",
            "-of", "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    info = json.loads(proc.stdout)["streams"][0]
    return int(info["sample_rate"]), int(info["channels"])


def _make_silence(path: Path, ms: int, sample_rate: int, channels: int, ffmpeg_path: Path) -> None:
    duration = ms / 1000.0
    layout = "mono" if channels == 1 else "stereo"
    subprocess.run(
        [
            str(ffmpeg_path),
            "-y",
            "-f", "lavfi",
            "-i", f"anullsrc=channel_layout={layout}:sample_rate={sample_rate}",
            "-t", f"{duration}",
            "-c:a", "pcm_s16le",
            str(path),
        ],
        capture_output=True,
        check=True,
    )


def merge(
    wav_paths: list[Path],
    out_path: Path,
    config: Config,
    gap_ms: int | None = None,
) -> Path:
    """Merge wav_paths → out_path, inserting `gap_ms` silence between segments."""
    if not wav_paths:
        raise ValueError("merge: empty wav list")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    gap_ms = gap_ms if gap_ms is not None else config.defaults.gap_ms
    work_dir = out_path.parent / ".merge_work"
    work_dir.mkdir(exist_ok=True)

    sequence: list[Path]
    if gap_ms > 0 and len(wav_paths) > 1:
        sample_rate, channels = _probe_audio(wav_paths[0], config.ffmpeg_path)
        silence = work_dir / "silence.wav"
        _make_silence(silence, gap_ms, sample_rate, channels, config.ffmpeg_path)
        sequence = []
        for i, p in enumerate(wav_paths):
            sequence.append(p)
            if i < len(wav_paths) - 1:
                sequence.append(silence)
    else:
        sequence = list(wav_paths)

    list_file = work_dir / "concat.txt"
    list_file.write_text(
        "\n".join(f"file '{p.resolve()}'" for p in sequence) + "\n",
        encoding="utf-8",
    )

    output_codec = (
        ["-c:a", "libmp3lame", "-q:a", "2"]
        if out_path.suffix.lower() == ".mp3"
        else ["-c:a", "pcm_s16le"]
    )

    subprocess.run(
        [
            str(config.ffmpeg_path),
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            *output_codec,
            str(out_path),
        ],
        capture_output=True,
        check=True,
    )

    # cleanup work files
    for f in work_dir.iterdir():
        f.unlink(missing_ok=True)
    work_dir.rmdir()

    return out_path
