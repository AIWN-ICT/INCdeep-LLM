"""Reward-generation and evaluation pipeline CLI entry.

Modes:
- stage1: generate candidate reward functions with reasoning models
- stage2: evaluate generated candidates and export best one
- both: run stage1 then stage2 (default)
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from dotenv import load_dotenv

from reward_generation_runner import generate_reward_functions
from reward_pipeline_runner import run_evaluation_from_generation, run_two_stage_pipeline


def _build_result_run_dir() -> Path:
    """Return fixed output folder under ./result/LLM_reward."""
    root = Path(__file__).resolve().parent
    run_dir = root / "result" / "LLM_reward"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir

load_dotenv()


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for pipeline execution mode and outputs."""
    parser = argparse.ArgumentParser(description="Reward generation + evaluation pipeline")
    parser.add_argument("--mode", choices=["stage1", "stage2", "both"], default="both")
    parser.add_argument("--generation-output", default=None)
    parser.add_argument("--generation-csv-output", default=None)
    parser.add_argument("--best-output", default=None)
    parser.add_argument("--summary-output", default=None)
    parser.add_argument("--output-dir", default=None, help="Directory for all generated artifacts")
    return parser.parse_args()


def main() -> None:
    """Dispatch pipeline stages based on ``--mode``."""
    args = parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else _build_result_run_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    generation_output = args.generation_output or str(output_dir / "reward_generation_results.json")
    generation_csv_output = args.generation_csv_output or str(output_dir / "reward_generation_functions.csv")
    best_output = args.best_output or str(output_dir / "best_reward_function.py")
    summary_output = args.summary_output or str(output_dir / "two_stage_summary.json")

    print(f"[CLI] output directory: {output_dir}")

    if args.mode == "stage1":
        print("=== Running mode: stage1 ===")
        stage_start = time.time()
        generate_reward_functions(
            output_path=generation_output,
            csv_output_path=generation_csv_output,
        )
        stage_elapsed = time.time() - stage_start
        print(f"[CLI] stage1 total elapsed: {stage_elapsed:.3f}s")
        return

    if args.mode == "stage2":
        print("=== Running mode: stage2 ===")
        stage_start = time.time()
        run_evaluation_from_generation(
            generation_output_path=generation_output,
            best_output_path=best_output,
            summary_output_path=summary_output,
            report_output_dir=str(output_dir),
        )
        stage_elapsed = time.time() - stage_start
        print(f"[CLI] stage2 total elapsed: {stage_elapsed:.3f}s")
        return

    stage_start = time.time()
    run_two_stage_pipeline(
        generation_output_path=generation_output,
        generation_csv_output_path=generation_csv_output,
        best_output_path=best_output,
        summary_output_path=summary_output,
        report_output_dir=str(output_dir),
    )
    stage_elapsed = time.time() - stage_start
    print(f"[CLI] both(total) elapsed: {stage_elapsed:.3f}s")


if __name__ == "__main__":
    main()
