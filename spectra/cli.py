from __future__ import annotations

import json
import shutil
import subprocess
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

from .analyzer import DEFAULT_MODEL, analyze
from .models import AnalysisReport
from .parsers import detect_and_normalize
from .parsers.snyk import is_snyk
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
        help="Scanner format: auto, trivy, semgrep, snyk, generic",
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
        DEFAULT_MODEL,
        "--model",
        "-m",
        envvar="SPECTRA_MODEL",
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

    if not _render_report(report, fmt, output):
        raise typer.Exit(1)

    if show_usage and usage_stats:
        _print_usage(usage_stats)


@app.command(name="scan")
def scan_cmd(
    scanner: str = typer.Argument(..., help="Scanner to run (currently: snyk)"),
    product: str = typer.Option(
        ...,
        "--product",
        help="Snyk product: open-source, code, container, or iac",
    ),
    target: str = typer.Option(
        ".",
        "--target",
        help="Project path for open-source/code/iac, or image name for container",
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
        help="Write report to file (auto-suffixed for 'both')",
    ),
    scan_output: Optional[Path] = typer.Option(
        None,
        "--scan-output",
        help="Optionally save the raw Snyk JSON scan output",
    ),
    snyk_args: Optional[list[str]] = typer.Option(
        None,
        "--snyk-arg",
        help="Additional Snyk CLI argument (repeatable), e.g. --snyk-arg=--all-projects",
    ),
    model: str = typer.Option(
        DEFAULT_MODEL,
        "--model",
        "-m",
        envvar="SPECTRA_MODEL",
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
    """Run a Snyk CLI scan and analyze its JSON results with Spectra."""
    if scanner.lower() != "snyk":
        err_console.print(f"[red]Unsupported scanner:[/red] {scanner!r}. Use: snyk")
        raise typer.Exit(2)

    product_commands = {
        "open-source": ["test"],
        "code": ["code", "test"],
        "container": ["container", "test"],
        "iac": ["iac", "test"],
    }
    product = product.lower()
    if product not in product_commands:
        err_console.print(
            f"[red]Unknown Snyk product:[/red] {product!r}. "
            "Use: open-source, code, container, iac"
        )
        raise typer.Exit(2)

    snyk_executable = shutil.which("snyk")
    if not snyk_executable:
        err_console.print(
            "[red]Snyk CLI not found.[/red] Install it and ensure [cyan]snyk[/cyan] "
            "is on PATH. Set [cyan]SNYK_TOKEN[/cyan] for non-interactive authentication."
        )
        raise typer.Exit(1)

    command = [snyk_executable, *product_commands[product], "--json"]
    scan_cwd = None
    if product == "open-source":
        target_path = Path(target).expanduser()
        if target_path.is_dir():
            scan_cwd = target_path
        elif target_path.is_file():
            scan_cwd = target_path.parent
            command.append(f"--file={target_path.name}")
        else:
            err_console.print(f"[red]Open Source target not found:[/red] {target_path}")
            raise typer.Exit(1)
    else:
        command.append(target)
    command.extend(snyk_args or [])

    err_console.print(f"Running Snyk {product} scan...")
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            cwd=scan_cwd,
        )
    except OSError as exc:
        err_console.print(f"[red]Could not run Snyk CLI:[/red] {exc}")
        raise typer.Exit(1) from exc

    raw = result.stdout
    try:
        scan_data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        detail = result.stderr.strip() or raw.strip() or "Snyk CLI returned no output."
        err_console.print(f"[red]Snyk scan failed (exit {result.returncode}):[/red] {detail}")
        raise typer.Exit(result.returncode or 1)

    if result.returncode not in (0, 1) or not is_snyk(scan_data):
        detail = (
            result.stderr.strip()
            or raw.strip()
            or "Snyk did not return a recognized JSON result."
        )
        err_console.print(f"[red]Snyk scan failed (exit {result.returncode}):[/red] {detail}")
        raise typer.Exit(result.returncode or 1)

    if scan_output:
        scan_output.parent.mkdir(parents=True, exist_ok=True)
        scan_output.write_text(raw, encoding="utf-8")
        err_console.print(f"[green]✓[/green] Snyk scan output → [cyan]{scan_output}[/cyan]")

    normalized = detect_and_normalize(raw, hint="snyk")
    try:
        report, usage_stats = analyze(
            normalized,
            model=model,
            show_thinking=show_thinking,
        )
    except Exception as exc:
        err_console.print(f"[red]Analysis failed:[/red] {exc}")
        raise typer.Exit(1) from exc

    if not _render_report(report, fmt, output):
        raise typer.Exit(2)

    if show_usage and usage_stats:
        _print_usage(usage_stats)


def _render_report(
    report: AnalysisReport,
    fmt: str,
    output: Optional[Path],
) -> bool:
    fmt = fmt.lower()
    if fmt not in ("markdown", "json", "both"):
        err_console.print(f"[red]Unknown format:[/red] {fmt!r}. Use: markdown, json, both")
        return False

    if fmt in ("markdown", "both"):
        md_text = render_markdown(report)
        if output:
            out_path = output.with_suffix(".md")
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(md_text, encoding="utf-8")
            err_console.print(f"[green]✓[/green] Markdown report → [cyan]{out_path}[/cyan]")
        else:
            console.print(Markdown(md_text))

    if fmt in ("json", "both"):
        json_text = render_json(report)
        if output:
            out_path = output.with_suffix(".json")
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json_text, encoding="utf-8")
            err_console.print(f"[green]✓[/green] JSON report    → [cyan]{out_path}[/cyan]")
        else:
            console.print_json(json_text)
    return True


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
