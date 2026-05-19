<<<<<<< HEAD
"""Stage2 and two-stage reward pipeline orchestration."""

from __future__ import annotations

import json
import os
from typing import Dict

import reward_eval_runner
from reward_generation_runner import generate_reward_functions


def _load_generation_results(path: str) -> Dict[str, Dict[str, object]]:
    """Load stage1 generation JSON and validate top-level structure.

    Args:
        path: Path to generation result JSON file.

    Returns:
        Parsed generation-results dictionary.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Generation result file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise RuntimeError("Invalid generation results format: root must be a JSON object.")
    return data


def _build_eval_reward_functions(generation_results: Dict[str, Dict[str, object]]) -> Dict[str, str]:
    """Extract valid generated reward-function code for evaluation.

    Args:
        generation_results: Stage1 output mapping by model.

    Returns:
        Mapping ``{model_name: reward_function_text}`` for successful items.
    """
    reward_functions: Dict[str, str] = {}
    for model_name, item in generation_results.items():
        if item.get("ok") and isinstance(item.get("reward_function_text"), str):
            reward_functions[model_name] = item["reward_function_text"].strip()
    return reward_functions


def run_evaluation_from_generation(
    generation_output_path: str = "reward_generation_results.json",
    best_output_path: str = "best_reward_function.py",
    summary_output_path: str = "two_stage_summary.json",
) -> Dict[str, object]:
    """Run stage2 evaluation from saved stage1 outputs.

    Args:
        generation_output_path: Stage1 JSON result path.
        best_output_path: File path for selected best reward function.
        summary_output_path: File path for compact stage2 summary JSON.

    Returns:
        Summary dictionary including best model and score.
    """
    generation_results = _load_generation_results(generation_output_path)
    reward_functions = _build_eval_reward_functions(generation_results)

    if len(reward_functions) < 2:
        raise RuntimeError("Not enough generated reward functions for cross-model evaluation (need at least 2).")

    print("\n=== Evaluation source info ===")
    print("source_type: generated")
    print(f"count: {len(reward_functions)}")
    print(f"path: {generation_output_path}")

    eval_result = reward_eval_runner.run_evaluation(reward_functions=reward_functions)
    reward_eval_runner.save_reports(eval_result, output_dir=".")

    if not eval_result["avg_score_by_reward_function"]:
        raise RuntimeError("Evaluation completed but no ranking data was produced.")

    best_model = max(
        eval_result["avg_score_by_reward_function"],
        key=eval_result["avg_score_by_reward_function"].get,
    )
    best_score = eval_result["avg_score_by_reward_function"][best_model]
    best_code = reward_functions.get(best_model, "")

    with open(best_output_path, "w", encoding="utf-8") as f:
        f.write("# Auto-selected best reward function\n")
        f.write(f"# Source model: {best_model}\n")
        f.write(f"# Average score: {best_score:.4f}\n\n")
        f.write(best_code.strip() + "\n")

    summary = {
        "best_model": best_model,
        "best_score": best_score,
        "best_output_path": best_output_path,
        "generation_output_path": generation_output_path,
    }
    with open(summary_output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n=== Stage2 completed ===")
    print(f"Best model: {best_model}")
    print(f"Best score: {best_score:.4f}")
    print(f"Best reward function saved to: {best_output_path}")
    return summary


def run_two_stage_pipeline(
    prompt: str | None = None,
    generation_output_path: str = "reward_generation_results.json",
    best_output_path: str = "best_reward_function.py",
    summary_output_path: str = "two_stage_summary.json",
) -> Dict[str, object]:
    """Run stage1 generation followed by stage2 evaluation.

    Args:
        prompt: Optional custom generation prompt for stage1.
        generation_output_path: Stage1 JSON output path.
        best_output_path: File path for selected best reward function.
        summary_output_path: File path for final pipeline summary.

    Returns:
        Same summary dictionary returned by stage2 runner.
    """
    print("=== Running mode: both (stage1 -> stage2) ===")
    generate_reward_functions(prompt=prompt, output_path=generation_output_path)
    return run_evaluation_from_generation(
        generation_output_path=generation_output_path,
        best_output_path=best_output_path,
        summary_output_path=summary_output_path,
    )
=======
"""Stage2 and two-stage reward pipeline orchestration."""

from __future__ import annotations

import json
import os
from typing import Dict

import reward_eval_runner
from reward_generation_runner import generate_reward_functions


def _load_generation_results(path: str) -> Dict[str, Dict[str, object]]:
    """Load stage1 generation JSON and validate top-level structure.

    Args:
        path: Path to generation result JSON file.

    Returns:
        Parsed generation-results dictionary.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Generation result file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise RuntimeError("Invalid generation results format: root must be a JSON object.")
    return data


def _build_eval_reward_functions(generation_results: Dict[str, Dict[str, object]]) -> Dict[str, str]:
    """Extract valid generated reward-function code for evaluation.

    Args:
        generation_results: Stage1 output mapping by model.

    Returns:
        Mapping ``{model_name: reward_function_text}`` for successful items.
    """
    reward_functions: Dict[str, str] = {}
    for model_name, item in generation_results.items():
        if item.get("ok") and isinstance(item.get("reward_function_text"), str):
            reward_functions[model_name] = item["reward_function_text"].strip()
    return reward_functions


def run_evaluation_from_generation(
    generation_output_path: str = "reward_generation_results.json",
    best_output_path: str = "best_reward_function.py",
    summary_output_path: str = "two_stage_summary.json",
) -> Dict[str, object]:
    """Run stage2 evaluation from saved stage1 outputs.

    Args:
        generation_output_path: Stage1 JSON result path.
        best_output_path: File path for selected best reward function.
        summary_output_path: File path for compact stage2 summary JSON.

    Returns:
        Summary dictionary including best model and score.
    """
    generation_results = _load_generation_results(generation_output_path)
    reward_functions = _build_eval_reward_functions(generation_results)

    if len(reward_functions) < 2:
        raise RuntimeError("Not enough generated reward functions for cross-model evaluation (need at least 2).")

    print("\n=== Evaluation source info ===")
    print("source_type: generated")
    print(f"count: {len(reward_functions)}")
    print(f"path: {generation_output_path}")

    eval_result = reward_eval_runner.run_evaluation(reward_functions=reward_functions)
    reward_eval_runner.save_reports(eval_result, output_dir=".")

    if not eval_result["avg_score_by_reward_function"]:
        raise RuntimeError("Evaluation completed but no ranking data was produced.")

    best_model = max(
        eval_result["avg_score_by_reward_function"],
        key=eval_result["avg_score_by_reward_function"].get,
    )
    best_score = eval_result["avg_score_by_reward_function"][best_model]
    best_code = reward_functions.get(best_model, "")

    with open(best_output_path, "w", encoding="utf-8") as f:
        f.write("# Auto-selected best reward function\n")
        f.write(f"# Source model: {best_model}\n")
        f.write(f"# Average score: {best_score:.4f}\n\n")
        f.write(best_code.strip() + "\n")

    summary = {
        "best_model": best_model,
        "best_score": best_score,
        "best_output_path": best_output_path,
        "generation_output_path": generation_output_path,
    }
    with open(summary_output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n=== Stage2 completed ===")
    print(f"Best model: {best_model}")
    print(f"Best score: {best_score:.4f}")
    print(f"Best reward function saved to: {best_output_path}")
    return summary


def run_two_stage_pipeline(
    prompt: str | None = None,
    generation_output_path: str = "reward_generation_results.json",
    best_output_path: str = "best_reward_function.py",
    summary_output_path: str = "two_stage_summary.json",
) -> Dict[str, object]:
    """Run stage1 generation followed by stage2 evaluation.

    Args:
        prompt: Optional custom generation prompt for stage1.
        generation_output_path: Stage1 JSON output path.
        best_output_path: File path for selected best reward function.
        summary_output_path: File path for final pipeline summary.

    Returns:
        Same summary dictionary returned by stage2 runner.
    """
    print("=== Running mode: both (stage1 -> stage2) ===")
    generate_reward_functions(prompt=prompt, output_path=generation_output_path)
    return run_evaluation_from_generation(
        generation_output_path=generation_output_path,
        best_output_path=best_output_path,
        summary_output_path=summary_output_path,
    )
>>>>>>> 7d2f6d8c28f3c5b7e47d00807eec56d14f052984
