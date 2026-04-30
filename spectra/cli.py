from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()  # loads .env from cwd or any parent directory

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .analyzer import analyze
from .parsers import detect_and_normalize
from .reporters import render_json, render_markdown

app = typer.Typer(
    name="spectra",
    help="[bold cyan]SPECTRA[/bold cyan] — AI-Powered Security Intelligence Platform",
    rich_markup_mode="rich",
    no_args_is_help=True,
)
console = Console()
err_console = Console(stderr=True)


# ─── analyze command ──────────────────────────────────────────────────────────

@app.command(name="analyze")
def analyze_cmd(
    input_file: Optional[Path] = typer.Argument(
        None,
        help="Scanner output file (omit to read from stdin)",
        show_default=False,
    ),
    scanner: str = typer.Option(
        "auto",
        "--scanner",
        "-s",
        help="Scanner format: auto, trivy, semgrep, generic",
    ),
    fmt: str = typer.Option(
        "markdown",
        "--format",
        "-f",
        help="Output format: markdown, json, both",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Write output to file (auto-suffixed for 'both')",
    ),
    model: str = typer.Option(
        "claude-opus-4-7",
        "--model",
        "-m",
        help="Claude model to use",
    ),
    show_thinking: bool = typer.Option(
        False,
        "--think",
        "-t",
        help="Stream Claude's reasoning (verbose)",
    ),
    show_usage: bool = typer.Option(
        False,
        "--usage",
        "-u",
        help="Print token usage after analysis",
    ),
):
    """
    Analyze security scanner output and generate an intelligence report.

    Examples:

    \b
      spectra analyze trivy.json
      spectra analyze scan.txt --scanner generic --format json
      cat semgrep.json | spectra analyze --format both --output ./reports/run
      spectra analyze nessus.txt --think --usage
    """
    # ── read input ────────────────────────────────────────────────────────────
    if input_file:
        if not input_file.exists():
            err_console.print(f"[red]Error:[/red] File not found: {input_file}")
            raise typer.Exit(1)
        raw = input_file.read_text(encoding="utf-8", errors="replace")
    elif not sys.stdin.isatty():
        raw = sys.stdin.read()
    else:
        err_console.print(
            "[red]Error:[/red] Provide a scanner output file or pipe data to stdin.\n"
            "       Example: [dim]spectra analyze trivy.json[/dim]"
        )
        raise typer.Exit(1)

    if not raw.strip():
        err_console.print("[red]Error:[/red] Input is empty.")
        raise typer.Exit(1)

    # ── normalize ─────────────────────────────────────────────────────────────
    try:
        normalized = detect_and_normalize(raw, hint=scanner)
    except Exception as e:
        err_console.print(f"[red]Parse error:[/red] {e}")
        raise typer.Exit(1)

    # ── analyze ───────────────────────────────────────────────────────────────
    report = None
    usage_stats: dict = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=err_console,
        transient=True,
    ) as progress:
        progress.add_task("SPECTRA is analyzing...", total=None)
        try:
            report, usage_stats = analyze(
                normalized,
                model=model,
                show_thinking=show_thinking,
            )
        except Exception as e:
            err_console.print(f"[red]Analysis failed:[/red] {e}")
            raise typer.Exit(1)

    # ── render ────────────────────────────────────────────────────────────────
    fmt = fmt.lower()

    if fmt in ("markdown", "both"):
        md_text = render_markdown(report)
        if output:
            suffix = ".md"
            out_path = output.with_suffix(suffix) if fmt == "both" else output
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(md_text, encoding="utf-8")
            err_console.print(f"[green]✓[/green] Markdown report → [cyan]{out_path}[/cyan]")
        else:
            console.print(Markdown(md_text))

    if fmt in ("json", "both"):
        json_text = render_json(report)
        if output:
            suffix = ".json"
            out_path = output.with_suffix(suffix) if fmt == "both" else output
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json_text, encoding="utf-8")
            err_console.print(f"[green]✓[/green] JSON report    → [cyan]{out_path}[/cyan]")
        else:
            console.print_json(json_text)

    if fmt not in ("markdown", "json", "both"):
        err_console.print(f"[red]Unknown format:[/red] {fmt!r}. Use: markdown, json, both")
        raise typer.Exit(1)

    # ── usage stats ───────────────────────────────────────────────────────────
    if show_usage and usage_stats:
        _print_usage(usage_stats)


# ─── version command ──────────────────────────────────────────────────────────

@app.command(name="version")
def version_cmd():
    """Show SPECTRA version information."""
    from . import __version__
    console.print(
        Panel(
            f"[bold cyan]SPECTRA[/bold cyan]  v{__version__}\n"
            "AI-Powered Security Intelligence Platform",
            border_style="cyan",
        )
    )


# ─── helpers ──────────────────────────────────────────────────────────────────

def _print_usage(stats: dict) -> None:
    table = Table(title="Token Usage", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="dim")
    table.add_column("Tokens", justify="right")

    table.add_row("Input tokens", f"{stats.get('input_tokens', 0):,}")
    table.add_row("Output tokens", f"{stats.get('output_tokens', 0):,}")
    cache_read = stats.get("cache_read_tokens", 0)
    cache_write = stats.get("cache_creation_tokens", 0)
    if cache_read:
        table.add_row("[green]Cache read[/green]", f"[green]{cache_read:,}[/green]")
    if cache_write:
        table.add_row("[yellow]Cache write[/yellow]", f"[yellow]{cache_write:,}[/yellow]")

    err_console.print(table)


def main() -> None:
    app()
