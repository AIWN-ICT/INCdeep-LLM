<<<<<<< HEAD
"""Reward-generation and evaluation pipeline CLI entry.

Modes:
- stage1: generate candidate reward functions with reasoning models
- stage2: evaluate generated candidates and export best one
- both: run stage1 then stage2 (default)
"""

from __future__ import annotations

import argparse

from dotenv import load_dotenv

from reward_generation_runner import generate_reward_functions
from reward_pipeline_runner import run_evaluation_from_generation, run_two_stage_pipeline

load_dotenv()


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for pipeline execution mode and outputs."""
    parser = argparse.ArgumentParser(description="Reward generation + evaluation pipeline")
    parser.add_argument("--mode", choices=["stage1", "stage2", "both"], default="both")
    parser.add_argument("--generation-output", default="reward_generation_results.json")
    parser.add_argument("--best-output", default="best_reward_function.py")
    parser.add_argument("--summary-output", default="two_stage_summary.json")
    return parser.parse_args()


def main() -> None:
    """Dispatch pipeline stages based on ``--mode``."""
    args = parse_args()

    if args.mode == "stage1":
        print("=== Running mode: stage1 ===")
        generate_reward_functions(output_path=args.generation_output)
        return

    if args.mode == "stage2":
        print("=== Running mode: stage2 ===")
        run_evaluation_from_generation(
            generation_output_path=args.generation_output,
            best_output_path=args.best_output,
            summary_output_path=args.summary_output,
        )
        return

    run_two_stage_pipeline(
        generation_output_path=args.generation_output,
        best_output_path=args.best_output,
        summary_output_path=args.summary_output,
    )


if __name__ == "__main__":
    main()
=======
"""Reward-generation and evaluation pipeline CLI entry.

Modes:
- stage1: generate candidate reward functions with reasoning models
- stage2: evaluate generated candidates and export best one
- both: run stage1 then stage2 (default)
"""

from __future__ import annotations

import argparse

from dotenv import load_dotenv

from reward_generation_runner import generate_reward_functions
from reward_pipeline_runner import run_evaluation_from_generation, run_two_stage_pipeline

load_dotenv()


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for pipeline execution mode and outputs."""
    parser = argparse.ArgumentParser(description="Reward generation + evaluation pipeline")
    parser.add_argument("--mode", choices=["stage1", "stage2", "both"], default="both")
    parser.add_argument("--generation-output", default="reward_generation_results.json")
    parser.add_argument("--best-output", default="best_reward_function.py")
    parser.add_argument("--summary-output", default="two_stage_summary.json")
    return parser.parse_args()


def main() -> None:
    """Dispatch pipeline stages based on ``--mode``."""
    args = parse_args()

    if args.mode == "stage1":
        print("=== Running mode: stage1 ===")
        generate_reward_functions(output_path=args.generation_output)
        return

    if args.mode == "stage2":
        print("=== Running mode: stage2 ===")
        run_evaluation_from_generation(
            generation_output_path=args.generation_output,
            best_output_path=args.best_output,
            summary_output_path=args.summary_output,
        )
        return

    run_two_stage_pipeline(
        generation_output_path=args.generation_output,
        best_output_path=args.best_output,
        summary_output_path=args.summary_output,
    )


if __name__ == "__main__":
    main()
>>>>>>> 7d2f6d8c28f3c5b7e47d00807eec56d14f052984
