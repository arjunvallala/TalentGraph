"""
TalentGraph AI — Submission Validation CLI

Validates a submission.csv file against schema, types, range, and format constraints.
"""
from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.analytics.submission_generator import SubmissionGenerator

console = Console()
app = typer.Typer(name="tg-validate", help="TalentGraph AI Submission Validator")


@app.command()
def validate(
    file: Path = typer.Option(
        Path("submission.csv"),
        "--file", "-f",
        help="Path to submission.csv file",
        exists=True,
        readable=True,
    ),
) -> None:
    """Validate a submission.csv file for conformity and correctness."""
    console.print(f"🧐 Validating submission file: [yellow]{file}[/yellow]...")

    generator = SubmissionGenerator()
    valid, errors = generator.validate(str(file))

    if valid:
        console.print(Panel.fit(
            "✅ [bold green]Validation Passed![/bold green]\n"
            f"The file {file} is fully formatted and ready for submission.",
            title="Success",
            border_style="green"
        ))
    else:
        console.print(Panel.fit(
            "❌ [bold red]Validation Failed![/bold red]\n"
            f"Found {len(errors)} format errors. See details below.",
            title="Error",
            border_style="red"
        ))
        for err in errors:
            console.print(f"  - [red]{err}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    app()
