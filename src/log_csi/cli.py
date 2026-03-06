from __future__ import annotations
import os
from pathlib import Path
from zoneinfo import ZoneInfo
import typer
from log_csi.config import load_profile
from log_csi.parser.regex_multiline import parse_file_regex_multiline
from dateutil import parser as dtparser
from log_csi.storyline.summarize import summarize_storyline
from dotenv import load_dotenv

load_dotenv()

app = typer.Typer(no_args_is_help=True)


@app.command()
def validate_profile(
        profile: str = typer.Option(..., "--profile",
                                    help="Log parsing profile"),
        sample: str = typer.Option(..., "--sample", help="Sample log file"),
        tz: str = typer.Option("America/Vancouver", "--tz", help="Timezone")):
    profile = load_profile(profile)
    if profile.type != "regex_multiline":
        raise typer.BadParameter(
            "MVP v1 supports only type=regex_multiline for now")

    events = parse_file_regex_multiline(
        Path(sample),
        event_start_regex=profile.raw["event_start_regex"],
        tz=profile.raw.get("timestamp", {}).get("timezone", tz)
    )
    print(f"[bold]Parsed events:[/bold] {len(events)}")
    if events:
        print("[bold]First event:[/bold]")
        print(events[0].model_dump())


@app.command()
def query(
        root: str = typer.Option(..., "--root",
                                 help="Root folder containing logs"),
        profile: str = typer.Option(..., "--profile",
                                    help="Log parsing profile"),
        start: str = typer.Option(..., "--start", help="Start time"),
        end: str = typer.Option(..., "--end", help="End time"),
        tz: str = typer.Option("America/Vancouver", "--tz", help="Timezone"),
        glob: str = typer.Option("*.log", "--glob", help="glob"),
        limit: int = typer.Option(400, "--limit", help="limit")):

    profile = load_profile(profile)
    if profile.type != "regex_multiline":
        raise typer.BadParameter(
            "MVP v1 supports only type=regex_multiline for now")

    tzinfo = ZoneInfo(tz)
    dt_start = dtparser.parse(start)
    dt_end = dtparser.parse(end)
    if dt_start.tzinfo is None:
        dt_start = dt_start.replace(tzinfo=tzinfo)
    if dt_end.tzinfo is None:
        dt_end = dt_end.replace(tzinfo=tzinfo)
    ts_start = dt_start.timestamp()
    ts_end = dt_end.timestamp()

    root_path = Path(root)
    files = list(root_path.rglob(glob))
    if not files:
        print(
            f"[red]No files found.[/red]")
        raise typer.Exit(code=2)

    all_events = []
    for file in files:
        try:
            events = parse_file_regex_multiline(
                file,
                event_start_regex=profile.raw["event_start_regex"],
                tz=profile.raw.get("timestamp", {}).get("timezone", tz),
                service_from_path=("path_parent", profile.raw.get(
                    "service", {}).get("depth", 1)),
            )
            all_events.extend(events)
        except Exception as e:
            print(f"[yellow]Skip[/yellow] {file}: {e}")

    window = [e for e in all_events if ts_start <= e.ts_event <= ts_end]
    window.sort(key=lambda e: e.ts_event)

    if not window:
        print(f"[yellow]No events found in the window.[/yellow]")
        raise typer.Exit(code=0)

    # Limit for MVP (avoid massive output)
    window = window[:limit]

    model = os.getenv("STORYLINE_MODEL", "gpt-4o-mini")
    storyline = summarize_storyline(window, model=model, tz_name=tz)
    print(storyline)
