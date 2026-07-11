"""Wrap Voicepeak CLI: one Segment → one wav file."""

from __future__ import annotations

import subprocess
import threading
import time
from pathlib import Path

from voicepeak_gen.config import Config
from voicepeak_gen.models import Segment

# Voicepeak（尤其 1.2.x on macOS 26）偶爾會在啟動/合成時 segfault，且**不能同時跑兩個實例**。
# 用一把全域鎖把每次呼叫序列化（studio 的併發 HTTP 執行緒也吃這把鎖），
# 再對「非 0 結束 / 沒生出 wav」重試幾次，扛住它間歇性抽風。
_VP_LOCK = threading.Lock()
_MAX_TRIES = 3
_RETRY_SLEEP = 0.8


def _format_emotion(emotion: dict[str, int]) -> str | None:
    if not emotion:
        return None
    return ",".join(f"{k}={v}" for k, v in emotion.items())


def list_narrators(config: Config) -> list[str]:
    proc = subprocess.run(
        [str(config.voicepeak_path), "--list-narrator"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"voicepeak --list-narrator failed: {proc.stderr}")
    return [line for line in proc.stdout.splitlines() if line.strip()]


def list_emotions(config: Config, narrator: str) -> list[str]:
    proc = subprocess.run(
        [str(config.voicepeak_path), "--list-emotion", narrator],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"voicepeak --list-emotion failed: {proc.stderr}")
    return [line for line in proc.stdout.splitlines() if line.strip()]


def synthesize(segment: Segment, out_path: Path, config: Config) -> Path:
    """Render one segment to a wav file. Returns the output path."""
    cmd = [
        str(config.voicepeak_path),
        "-s", segment.text,
        "-o", str(out_path),
        "-n", segment.narrator,
        "--speed", str(segment.speed),
        "--pitch", str(segment.pitch),
    ]
    emo = _format_emotion(segment.emotion)
    if emo:
        cmd.extend(["-e", emo])

    last_err = ""
    for attempt in range(1, _MAX_TRIES + 1):
        with _VP_LOCK:  # 序列化：同一時間只准一個 voicepeak 在跑
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode == 0 and out_path.exists() and out_path.stat().st_size > 0:
            segment.wav_path = out_path
            return out_path
        # segfault → returncode 為負（-11）或非 0；wav 沒生出來。記錄後重試。
        last_err = (proc.stderr.strip() or proc.stdout.strip()
                    or f"exit {proc.returncode}（可能 Voicepeak 自身 crash）")
        out_path.unlink(missing_ok=True)
        if attempt < _MAX_TRIES:
            time.sleep(_RETRY_SLEEP)

    raise RuntimeError(
        f"voicepeak 連續 {_MAX_TRIES} 次失敗 for segment #{segment.index} "
        f"({segment.narrator}): {last_err}"
    )


def synthesize_all(
    segments: list[Segment],
    temp_dir: Path,
    config: Config,
    on_progress=None,
) -> list[Path]:
    """Render every segment into temp_dir as segment_NNNN.wav."""
    temp_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for seg in segments:
        out = temp_dir / f"segment_{seg.index:04d}.wav"
        synthesize(seg, out, config)
        paths.append(out)
        if on_progress is not None:
            on_progress(seg)
    return paths
