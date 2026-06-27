"""
TalentGraph AI — Preprocessing Pipeline CLI

Run the full offline preprocessing pipeline from the command line.

Usage:
    python -m scripts.preprocess --input data/raw/candidates.csv
    python -m scripts.preprocess --input data/raw/candidates.csv --resume
    python -m scripts.preprocess --input data/raw/candidates.csv --reset
    python -m scripts.preprocess --status
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.config import settings
from shared.logging_setup import configure_logging, get_logger

logger = get_logger(__name__)
console = Console()
app = typer.Typer(
    name="tg-preprocess",
    help="TalentGraph AI — Offline Preprocessing Pipeline",
    add_completion=False,
)


@app.command()
def run(
    input: Path = typer.Option(
        ...,
        "--input", "-i",
        help="Path to the raw candidates CSV file",
        exists=True,
        readable=True,
    ),
    resume: bool = typer.Option(
        True,
        "--resume/--no-resume",
        help="Resume from last checkpoint if available",
    ),
    reset: bool = typer.Option(
        False,
        "--reset",
        help="Reset all checkpoints and start fresh",
    ),
    batch_size: int = typer.Option(
        settings.preprocessing_batch_size,
        "--batch-size",
        help="Number of candidates to process per batch",
    ),
    skip_embeddings: bool = typer.Option(
        False,
        "--skip-embeddings",
        help="Skip embedding generation (use if already generated)",
    ),
) -> None:
    """
    Run the complete TalentGraph AI preprocessing pipeline.

    This command processes the raw candidate data through:
    1. Loading and validation
    2. Cleaning and deduplication
    3. Profile parsing
    4. Feature extraction (15 features)
    5. Embedding generation
    6. FAISS index building
    7. BM25 index building
    8. Feature store population
    9. Quality report generation
    """
    configure_logging()

    console.print(Panel.fit(
        "[bold blue]TalentGraph AI[/bold blue] — Preprocessing Pipeline\n"
        f"Input: [yellow]{input}[/yellow]\n"
        f"Resume: [green]{resume}[/green] | Reset: [red]{reset}[/red]",
        title="🚀 Starting Preprocessing",
        border_style="blue",
    ))

    start_time = time.perf_counter()

    try:
        from services.preprocessing.pipeline import PreprocessingPipeline

        pipeline = PreprocessingPipeline(settings)

        if reset:
            console.print("⚠️  [yellow]Resetting all checkpoints...[/yellow]")
            pipeline.reset_checkpoints()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            result = pipeline.run(
                input_path=str(input),
                resume=resume,
                batch_size=batch_size,
                skip_embeddings=skip_embeddings,
                progress=progress,
            )

        total_time = time.perf_counter() - start_time

        # Results table
        table = Table(title="📊 Pipeline Results", border_style="green")
        table.add_column("Stage", style="cyan")
        table.add_column("Input", justify="right")
        table.add_column("Output", justify="right")
        table.add_column("Duration", justify="right")
        table.add_column("Status", justify="center")

        for stage_result in result.stage_results:
            table.add_row(
                stage_result.stage_name,
                str(stage_result.input_count),
                str(stage_result.output_count),
                f"{stage_result.duration_seconds:.1f}s",
                "✅" if stage_result.success else "❌",
            )

        console.print(table)
        console.print(Panel.fit(
            f"✅ Pipeline complete!\n"
            f"Processed: [bold green]{result.total_processed:,}[/bold green] candidates\n"
            f"Total time: [bold]{total_time:.1f}s[/bold]\n"
            f"FAISS index: [yellow]{settings.faiss_index_path}[/yellow]\n"
            f"Feature store: [yellow]{settings.duckdb_path}[/yellow]",
            title="✨ Success",
            border_style="green",
        ))

    except KeyboardInterrupt:
        console.print("\n⚠️  [yellow]Pipeline interrupted. Run with --resume to continue.[/yellow]")
        sys.exit(1)
    except Exception as exc:
        console.print(f"\n❌ [red]Pipeline failed: {exc}[/red]")
        logger.exception("Preprocessing pipeline failed")
        sys.exit(1)


@app.command()
def status() -> None:
    """Check the status of the preprocessing pipeline."""
    configure_logging()

    from services.preprocessing.checkpoint import CheckpointManager
    manager = CheckpointManager(settings.preprocessing_checkpoint_path)
    status_data = manager.get_all_status()

    table = Table(title="📊 Pipeline Stage Status", border_style="blue")
    table.add_column("Stage", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Processed", justify="right")
    table.add_column("Last Updated", justify="right")

    for stage, info in status_data.items():
        status_icon = "✅" if info.get("complete") else "⏳"
        table.add_row(
            stage,
            status_icon,
            str(info.get("processed_count", 0)),
            info.get("updated_at", "Never"),
        )

    console.print(table)


if __name__ == "__main__":
    app()
