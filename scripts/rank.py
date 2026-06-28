"""
TalentGraph AI — Ranking Pipeline CLI

Run the full ranking pipeline for a job description.

Usage:
    python -m scripts.rank --jd "path/to/jd.txt" --title "Senior ML Engineer"
    python -m scripts.rank --jd-text "We are looking for..." --title "Data Scientist"
    python -m scripts.rank --job-id job_001  (if already analyzed)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.config import settings
from shared.logging_setup import configure_logging, get_logger

logger = get_logger(__name__)
console = Console()
app = typer.Typer(
    name="tg-rank",
    help="TalentGraph AI — Ranking Pipeline",
    add_completion=False,
)


@app.command()
def run(
    jd: Path | None = typer.Option(
        None,
        "--jd",
        help="Path to job description text file",
    ),
    jd_text: str | None = typer.Option(
        None,
        "--jd-text",
        help="Job description text (inline)",
    ),
    title: str = typer.Option(
        "Software Engineer",
        "--title",
        "-t",
        help="Job title",
    ),
    job_id: str | None = typer.Option(
        None,
        "--job-id",
        help="Use an already-analyzed job ID",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path for submission.csv",
    ),
    top_k: int = typer.Option(
        100,
        "--top-k",
        help="Number of top candidates to return",
    ),
) -> None:
    """
    Run the TalentGraph AI 4-stage ranking pipeline.

    Pipeline stages:
    1. Job Intelligence: Analyze JD → Ideal Persona + Job Genome
    2. Hybrid Retrieval: FAISS + BM25 → Top 2,000 candidates
    3. Feature Ranking: DuckDB features → Top 200 candidates
    4. Hiring Council: 5 parallel evaluators → Top 100 candidates
    5. Explainability: Generate transparent explanations
    6. Submission: Generate submission.csv

    Total runtime target: < 5 minutes for 100K candidates (CPU only).
    """
    configure_logging()

    if not jd and not jd_text and not job_id:
        console.print("❌ [red]Provide --jd, --jd-text, or --job-id[/red]")
        raise typer.Exit(1)

    console.print(
        Panel.fit(
            f"[bold blue]TalentGraph AI[/bold blue] — Ranking Pipeline\n"
            f"Job: [yellow]{title}[/yellow]\n"
            f"Top K: [green]{top_k}[/green]",
            title="🏆 Starting Ranking",
            border_style="blue",
        )
    )

    start_time = time.perf_counter()

    try:
        from services.analytics.submission_generator import SubmissionGenerator
        from services.preprocessing.feature_store import FeatureStore
        from services.ranking.ranking_pipeline import RankingPipeline
        from shared.types.job import JobRaw

        # Load JD text
        description = ""
        if jd:
            description = jd.read_text(encoding="utf-8")
        elif jd_text:
            description = jd_text

        final_job_id = job_id or f"job_{int(time.time())}"

        store = FeatureStore(settings.duckdb_path)
        pipeline = RankingPipeline(config=settings, feature_store=store)

        if description:
            job_raw = JobRaw(
                job_id=final_job_id,
                title=title,
                description=description,
            )
            console.print(f"📝 Analyzing job description ({len(description)} chars)...")
        else:
            # Use existing job profile
            job_profile = store.get_job_profile(final_job_id)
            if not job_profile:
                console.print(f"❌ [red]Job '{final_job_id}' not found[/red]")
                raise typer.Exit(1)
            job_raw = JobRaw(
                job_id=final_job_id,
                title=job_profile.title,
                description=" ".join(job_profile.key_responsibilities),
            )

        console.print("🚀 Running ranking pipeline...")
        ranked_list = pipeline.rank(job_raw)

        total_time = time.perf_counter() - start_time

        # Stage results table
        table = Table(title="📊 Ranking Pipeline Results", border_style="blue")
        table.add_column("Stage", style="cyan")
        table.add_column("Input → Output", justify="center")
        table.add_column("Duration", justify="right")

        for sr in ranked_list.stage_results:
            table.add_row(
                sr.stage_name,
                f"{sr.input_count:,} → {sr.output_count:,}",
                f"{sr.duration_seconds:.1f}s",
            )

        console.print(table)

        # Top candidates preview
        console.print("\n🏆 [bold]Top 10 Candidates:[/bold]")
        top_table = Table(border_style="green")
        top_table.add_column("Rank", justify="center", style="bold")
        top_table.add_column("Candidate ID", style="cyan")
        top_table.add_column("Score", justify="right")
        top_table.add_column("Confidence", justify="center")
        top_table.add_column("Recommendation", justify="center")

        for c in ranked_list.candidates[:10]:
            score_color = (
                "green" if c.overall_score >= 0.7 else "yellow" if c.overall_score >= 0.5 else "red"
            )
            top_table.add_row(
                str(c.rank),
                c.candidate_id,
                f"[{score_color}]{c.overall_score:.4f}[/{score_color}]",
                c.confidence_level.value,
                c.hiring_recommendation.value,
            )

        console.print(top_table)

        # Generate submission
        output_path = str(output) if output else settings.submission_output_path
        generator = SubmissionGenerator()
        generator.generate(ranked_list.candidates, output_path)
        valid, errors = generator.validate(output_path)

        console.print(
            Panel.fit(
                f"✅ Ranking complete!\n"
                f"Total candidates: [bold]{ranked_list.total_processed:,}[/bold]\n"
                f"Shortlisted: [bold green]{len(ranked_list.candidates)}[/bold green]\n"
                f"Total time: [bold]{total_time:.1f}s[/bold] "
                f"({'< 5 min ✓' if total_time < 300 else '⚠ > 5 min'})\n"
                f"Submission: [yellow]{output_path}[/yellow] "
                f"({'✓ valid' if valid else '✗ invalid'})",
                title="✨ Pipeline Complete",
                border_style="green",
            )
        )

        if not valid and errors:
            console.print("⚠️  Validation errors:")
            for err in errors:
                console.print(f"  - {err}")

    except Exception as exc:
        console.print(f"\n❌ [red]Ranking failed: {exc}[/red]")
        logger.exception("Ranking pipeline failed")
        sys.exit(1)


if __name__ == "__main__":
    app()
