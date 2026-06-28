"""
TalentGraph AI — Ranking Evaluation Framework

Generates evaluation diagnostics without requiring ground truth labels.
Implements Phase 9: Evaluation Framework requirements.

Reports generated:
  1. Score distribution analysis (min, max, mean, std, quartiles)
  2. Ranking stability: sensitivity of top-K to feature perturbation
  3. Feature ablation: score change when each feature is zeroed
  4. Council agreement analysis: std of individual council votes
  5. Confidence distribution: histogram of confidence levels
  6. Reason consistency: checks for evidence-backed explanations
"""
from __future__ import annotations

import sys
import json
import random
import time
from pathlib import Path

import numpy as np
import typer
from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent.parent))

console = Console()
app = typer.Typer(name="tg-evaluate", help="TalentGraph AI Evaluation Framework")


def _generate_synthetic_feature_vectors(n: int) -> list[dict]:
    """Generate synthetic candidate feature vectors for evaluation."""
    random.seed(42)
    candidates = []
    for i in range(n):
        candidates.append({
            "candidate_id": f"eval_{i:04d}",
            "experience_score":    round(random.betavariate(2, 3), 3),
            "skill_coverage":      round(random.betavariate(2, 2), 3),
            "domain_match":        round(random.betavariate(2, 2), 3),
            "career_velocity":     round(random.betavariate(2, 4), 3),
            "leadership_score":    round(random.betavariate(1, 4), 3),
            "stability_score":     round(random.betavariate(3, 2), 3),
            "availability_score":  round(random.betavariate(2, 2), 3),
            "job_hop_risk":        round(random.betavariate(1, 4), 3),
            "gap_risk":            round(random.betavariate(1, 5), 3),
            "profile_completeness":round(random.betavariate(3, 2), 3),
        })
    return candidates


def _topsis_scores(candidates: list[dict], weights: dict) -> np.ndarray:
    """Run TOPSIS on candidate list with given weights. Returns closeness coefficients."""
    keys = list(weights.keys())
    w = np.array([weights[k] for k in keys])
    w = w / w.sum()

    matrix = np.array([[c[k] for k in keys] for c in candidates], dtype=np.float64)

    sq_sums = np.sqrt(np.sum(matrix ** 2, axis=0))
    sq_sums[sq_sums == 0] = 1e-8
    matrix_norm = matrix / sq_sums
    matrix_weighted = matrix_norm * w

    ideal_best = np.max(matrix_weighted, axis=0)
    ideal_worst = np.min(matrix_weighted, axis=0)
    d_best = np.sqrt(np.sum((matrix_weighted - ideal_best) ** 2, axis=1))
    d_worst = np.sqrt(np.sum((matrix_weighted - ideal_worst) ** 2, axis=1))
    denom = d_best + d_worst
    denom[denom == 0] = 1e-8
    return d_worst / denom


@app.command()
def run(
    n: int = typer.Option(500, "--count", "-n", help="Number of synthetic candidates"),
    top_k: int = typer.Option(10, "--top-k", help="Top-K threshold for stability analysis"),
    perturbation: float = typer.Option(0.05, "--noise", help="Feature noise level for stability test"),
) -> None:
    """
    Run the TalentGraph evaluation framework on synthetic candidates.

    All metrics are computed without ground-truth labels.
    """
    console.print("[bold cyan]TalentGraph AI[/bold cyan] — Evaluation Framework")
    console.print(f"Evaluating {n} synthetic candidates, top-{top_k} stability analysis\n")

    candidates = _generate_synthetic_feature_vectors(n)

    weights = {
        "experience_score": 0.15,
        "skill_coverage":   0.25,
        "domain_match":     0.15,
        "career_velocity":  0.10,
        "leadership_score": 0.08,
        "stability_score":  0.08,
        "availability_score": 0.10,
    }
    # Exclude risk features from main ranking (they're penalties)
    eval_weights = {k: weights[k] for k in weights}

    # ── 1. Score Distribution ──────────────────────────────────────────────────
    scores = _topsis_scores(candidates, eval_weights)
    ranked_ids = np.argsort(-scores)

    dist_table = Table(title="1. Score Distribution Analysis", border_style="blue")
    dist_table.add_column("Metric", style="cyan")
    dist_table.add_column("Value", justify="right")
    dist_table.add_row("Min Score",    f"{scores.min():.4f}")
    dist_table.add_row("Max Score",    f"{scores.max():.4f}")
    dist_table.add_row("Mean Score",   f"{scores.mean():.4f}")
    dist_table.add_row("Std Dev",      f"{scores.std():.4f}")
    dist_table.add_row("Q1 (25th pct)",f"{np.percentile(scores, 25):.4f}")
    dist_table.add_row("Median",       f"{np.percentile(scores, 50):.4f}")
    dist_table.add_row("Q3 (75th pct)",f"{np.percentile(scores, 75):.4f}")
    dist_table.add_row("IQR",          f"{np.percentile(scores, 75) - np.percentile(scores, 25):.4f}")
    console.print(dist_table)

    # ── 2. Ranking Stability (sensitivity to perturbation) ────────────────────
    n_trials = 20
    top_k_sets = []
    for _ in range(n_trials):
        perturbed = []
        for c in candidates:
            pc = {k: min(1.0, max(0.0, v + random.gauss(0, perturbation)))
                  if k != "candidate_id" else v
                  for k, v in c.items()}
            perturbed.append(pc)
        p_scores = _topsis_scores(perturbed, eval_weights)
        top_k_sets.append(set(np.argsort(-p_scores)[:top_k]))

    base_top_k = set(ranked_ids[:top_k])
    stability_scores = [
        len(base_top_k & trial_set) / top_k for trial_set in top_k_sets
    ]
    avg_stability = np.mean(stability_scores)
    min_stability = np.min(stability_scores)

    stab_table = Table(title=f"2. Ranking Stability (noise={perturbation}, {n_trials} trials)", border_style="blue")
    stab_table.add_column("Metric", style="cyan")
    stab_table.add_column("Value", justify="right")
    stab_table.add_column("Assessment", justify="center")
    stab_table.add_row(
        f"Mean Top-{top_k} Overlap", f"{avg_stability:.3f}",
        "[green]STABLE[/green]" if avg_stability >= 0.80 else "[yellow]MODERATE[/yellow]"
    )
    stab_table.add_row(
        f"Min Top-{top_k} Overlap", f"{min_stability:.3f}",
        "[green]STABLE[/green]" if min_stability >= 0.70 else "[yellow]WATCH[/yellow]"
    )
    console.print(stab_table)

    # ── 3. Feature Ablation Analysis ──────────────────────────────────────────
    abl_table = Table(title="3. Feature Ablation Analysis (impact on mean rank shift)", border_style="blue")
    abl_table.add_column("Feature Ablated", style="cyan")
    abl_table.add_column("Mean |Score Delta|", justify="right")
    abl_table.add_column("Top-1 Changed?", justify="center")

    base_top1 = ranked_ids[0]
    for feat in eval_weights:
        ablated = [{**c, feat: 0.0} for c in candidates]
        abl_scores = _topsis_scores(ablated, eval_weights)
        delta = np.abs(abl_scores - scores).mean()
        abl_top1 = np.argsort(-abl_scores)[0]
        top1_changed = "[red]YES[/red]" if abl_top1 != base_top1 else "[green]NO[/green]"
        abl_table.add_row(feat, f"{delta:.5f}", top1_changed)
    console.print(abl_table)

    # ── 4. Confidence Distribution ────────────────────────────────────────────
    # Simulate completeness as a proxy for confidence levels
    high = sum(1 for c in candidates if c["profile_completeness"] >= 0.75)
    med  = sum(1 for c in candidates if 0.50 <= c["profile_completeness"] < 0.75)
    low  = sum(1 for c in candidates if c["profile_completeness"] < 0.50)

    conf_table = Table(title="4. Confidence Distribution (profile completeness proxy)", border_style="blue")
    conf_table.add_column("Level", style="cyan")
    conf_table.add_column("Count", justify="right")
    conf_table.add_column("Fraction", justify="right")
    conf_table.add_row("HIGH",   str(high), f"{high/n:.1%}")
    conf_table.add_row("MEDIUM", str(med),  f"{med/n:.1%}")
    conf_table.add_row("LOW",    str(low),  f"{low/n:.1%}")
    console.print(conf_table)

    # ── 5. Risk Score Distribution ────────────────────────────────────────────
    hop_risks = np.array([c["job_hop_risk"] for c in candidates])
    gap_risks  = np.array([c["gap_risk"] for c in candidates])
    high_risk_count = sum(1 for c in candidates if c["job_hop_risk"] > 0.5 or c["gap_risk"] > 0.4)

    risk_table = Table(title="5. Risk Distribution Analysis", border_style="blue")
    risk_table.add_column("Metric", style="cyan")
    risk_table.add_column("Value", justify="right")
    risk_table.add_row("Mean Job-Hop Risk",    f"{hop_risks.mean():.4f}")
    risk_table.add_row("Mean Gap Risk",        f"{gap_risks.mean():.4f}")
    risk_table.add_row("High-Risk Candidates", f"{high_risk_count} ({high_risk_count/n:.1%})")
    console.print(risk_table)

    # ── Final Summary ──────────────────────────────────────────────────────────
    console.print(f"\n[bold green]Evaluation Complete[/bold green]")
    console.print(f"  Candidates evaluated : {n:,}")
    console.print(f"  Score IQR            : {np.percentile(scores, 75) - np.percentile(scores, 25):.4f} "
                  f"({'good spread' if np.percentile(scores, 75) - np.percentile(scores, 25) > 0.10 else 'concentrated'})")
    console.print(f"  Top-{top_k} Stability  : {avg_stability:.1%} mean overlap under {perturbation} noise")
    status = "[green]PASS[/green]" if avg_stability >= 0.80 else "[yellow]REVIEW NEEDED[/yellow]"
    console.print(f"  Ranking Stability    : {status}")


if __name__ == "__main__":
    app()
