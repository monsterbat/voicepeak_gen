"""voicepeak-gen: typer-based command line entry point."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from voicepeak_gen.config import DEFAULT_CONFIG_PATH, load_config
from voicepeak_gen.merger import merge
from voicepeak_gen.parsers import parse
from voicepeak_gen.splitter import split_lines
from voicepeak_gen.synthesizer import list_emotions, list_narrators, synthesize_all


app = typer.Typer(
    help="Pipeline that turns a script (CSV/JSON) into one merged audio file via Voicepeak's CLI.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


def _load_config_opt(config_path: Path | None):
    return load_config(config_path) if config_path else load_config()


@app.command()
def synth(
    input_file: Path = typer.Argument(..., exists=True, readable=True, help="CSV / TSV / TXT / JSON script."),
    output: Path = typer.Option(..., "-o", "--output", help="Final audio file (.wav or .mp3)."),
    gap_ms: int | None = typer.Option(None, "--gap-ms", help="Silence between segments in ms. Defaults to config."),
    keep_temp: bool = typer.Option(False, "--keep-temp", help="Keep the per-segment wav files for inspection."),
    config_path: Path | None = typer.Option(None, "--config", help=f"Override config file (default: {DEFAULT_CONFIG_PATH})."),
):
    """Render a script into one merged audio file."""
    config = _load_config_opt(config_path)

    console.print(f"[bold]Parsing[/bold] {input_file}")
    lines = parse(input_file, config)
    segments = split_lines(lines, max_chars=config.defaults.max_chars)
    console.print(f"  → {len(lines)} lines → {len(segments)} segments")

    temp_root = Path(tempfile.mkdtemp(prefix="voicepeak_gen_"))
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Synthesizing", total=len(segments))
            def _tick(seg):
                progress.update(task, advance=1, description=f"[{seg.narrator}] {seg.text[:24]}…")
            wavs = synthesize_all(segments, temp_root, config, on_progress=_tick)

        console.print(f"[bold]Merging[/bold] {len(wavs)} segments → {output}")
        merge(wavs, output, config, gap_ms=gap_ms)
        console.print(f"[green]✓ done:[/green] {output}")

        if keep_temp:
            console.print(f"  segments kept at: {temp_root}")
    finally:
        if not keep_temp:
            shutil.rmtree(temp_root, ignore_errors=True)


@app.command()
def narrators(
    config_path: Path | None = typer.Option(None, "--config"),
):
    """List narrators installed in Voicepeak."""
    config = _load_config_opt(config_path)
    names = list_narrators(config)
    table = Table(title="Installed narrators")
    table.add_column("Narrator")
    table.add_column("Aliases")
    alias_lookup: dict[str, list[str]] = {}
    for alias, target in config.narrator_aliases.items():
        alias_lookup.setdefault(target, []).append(alias)
    for name in names:
        table.add_row(name, ", ".join(alias_lookup.get(name, [])))
    console.print(table)


@app.command()
def emotions(
    narrator: str = typer.Argument(..., help="Narrator name (or alias from config)."),
    config_path: Path | None = typer.Option(None, "--config"),
):
    """List the emotion knobs available for one narrator."""
    config = _load_config_opt(config_path)
    resolved = config.resolve_narrator(narrator)
    for e in list_emotions(config, resolved):
        console.print(e)


@app.command()
def studio(
    recipes_dir: Path = typer.Option(Path("recipes"), "--recipes-dir", help="存試聽定案的情緒配方 JSON 的資料夾。"),
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8000, "--port"),
    config_path: Path | None = typer.Option(None, "--config"),
):
    """啟動本地語音工作室：即時拉 slider 調情緒/語速/音高、聽、存配方。"""
    from voicepeak_gen.studio import run_studio

    config = _load_config_opt(config_path)
    url = f"http://{host}:{port}/"
    console.print(f"[bold]語音工作室[/bold] → [green]{url}[/green]  （Ctrl-C 結束）")
    console.print(f"  配方存到：{recipes_dir.resolve()}")
    run_studio(config, recipes_dir, host=host, port=port)


@app.command()
def check(
    input_file: Path = typer.Argument(..., exists=True, readable=True),
    config_path: Path | None = typer.Option(None, "--config"),
):
    """Validate a script file without synthesizing."""
    config = _load_config_opt(config_path)
    lines = parse(input_file, config)
    segments = split_lines(lines, max_chars=config.defaults.max_chars)
    installed = set(list_narrators(config))
    unknown = sorted({line.narrator for line in lines} - installed)

    table = Table(title=f"{input_file.name} — {len(lines)} lines, {len(segments)} segments")
    table.add_column("#", justify="right")
    table.add_column("Narrator")
    table.add_column("Length")
    table.add_column("Text")
    for seg in segments:
        table.add_row(str(seg.index), seg.narrator, str(len(seg.text)), seg.text[:40])
    console.print(table)
    if unknown:
        console.print(f"[red]⚠ unknown narrators (not installed):[/red] {', '.join(unknown)}")
        raise typer.Exit(code=1)
    console.print("[green]✓ all narrators valid[/green]")


if __name__ == "__main__":
    app()
