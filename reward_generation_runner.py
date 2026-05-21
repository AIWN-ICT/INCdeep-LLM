"""Stage1 reward-function generation runner."""

from __future__ import annotations

import csv
import json
import re
import time
from typing import Dict

from langchain_openai import ChatOpenAI
from tqdm import tqdm

from reward_config import (
    MODEL_LANGUAGE_OVERRIDES,
    ModelSpec,
    UNIFIED_API_KEY,
    UNIFIED_BASE_URL,
    build_spec_list,
)
from reward_prompt_templates import REWARD_FUNCTION_DESIGN_PROMPTS_BY_LANGUAGE


def _build_client(spec: ModelSpec) -> ChatOpenAI:
    """Create generation-model client from model spec.

    Args:
        spec: Model spec with model name.

    Returns:
        Configured ``ChatOpenAI`` instance.
    """
    return ChatOpenAI(
        model=spec.name,
        temperature=0.0,
        openai_api_key=UNIFIED_API_KEY,
        openai_api_base=UNIFIED_BASE_URL,
    )


def _extract_reward_code(text: str) -> str:
    """Extract reward-function code from raw model output.

    Priority:
    1) fenced code block
    2) substring starting from first ``def``
    3) full content fallback

    Args:
        text: Raw model response.

    Returns:
        Cleaned reward-function code text.
    """
    content = text.strip()

    code_fence = re.search(r"```(?:python)?\s*([\s\S]*?)```", content, flags=re.IGNORECASE)
    if code_fence:
        return code_fence.group(1).strip()

    func_start = re.search(r"\bdef\s+\w+\s*\(", content)
    if func_start:
        return content[func_start.start() :].strip()

    return content


def _resolve_generation_prompt(model_name: str) -> str:
    """Select generation prompt by model language preference.

    Args:
        model_name: Generation model name.

    Returns:
        Prompt template text in the resolved language.
    """
    language = MODEL_LANGUAGE_OVERRIDES.get(model_name, "en")
    if language not in REWARD_FUNCTION_DESIGN_PROMPTS_BY_LANGUAGE:
        language = "en"
    return REWARD_FUNCTION_DESIGN_PROMPTS_BY_LANGUAGE[language]


def generate_reward_functions(
    prompt: str | None = None,
    output_path: str = "reward_generation_results.json",
    csv_output_path: str = "reward_generation_functions.csv",
) -> Dict[str, object]:
    """Run stage1 generation for all configured models.

    Args:
        prompt: Optional custom prompt; if omitted, language-specific
            defaults are chosen per model.
        output_path: JSON file path used to persist generation results.
        csv_output_path: CSV file path used to persist extracted reward
            functions for quick inspection.

    Returns:
        Dictionary containing per-model generation details and stage-level
        timing summary. Structure:
        {
            "models": {model_name: {...}},
            "summary": {
                "total_elapsed_seconds": float,
                "success_count": int,
                "failure_count": int,
                "model_count": int,
            }
        }
    """
    pipeline_start = time.time()
    results: Dict[str, Dict[str, object]] = {}
    specs = build_spec_list()

    with tqdm(specs, desc="Reward function generation", ncols=80) as pbar:
        for spec in pbar:
            pbar.set_postfix_str(f"current: {spec.name}")
            start = time.time()
            try:
                llm = _build_client(spec)
                prompt_text = prompt if prompt is not None else _resolve_generation_prompt(spec.name)
                response = llm.invoke(prompt_text)
                elapsed = time.time() - start

                raw = response.content if isinstance(response.content, str) else str(response.content)
                reward_code = _extract_reward_code(raw)

                results[spec.name] = {
                    "ok": True,
                    "elapsed_seconds": round(elapsed, 3),
                    "reward_function_text": reward_code,
                    "raw_response": raw,
                }
            except Exception as exc:
                elapsed = time.time() - start
                results[spec.name] = {
                    "ok": False,
                    "elapsed_seconds": round(elapsed, 3),
                    "error": str(exc),
                }
                print(f"⚠️ Failed: {spec.name}, elapsed={elapsed:.2f}s, error={exc}")

    total_elapsed = round(time.time() - pipeline_start, 3)
    success_count = sum(1 for item in results.values() if item.get("ok"))
    model_count = len(results)
    failure_count = model_count - success_count

    payload: Dict[str, object] = {
        "models": results,
        "summary": {
            "total_elapsed_seconds": total_elapsed,
            "success_count": success_count,
            "failure_count": failure_count,
            "model_count": model_count,
        },
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    with open(csv_output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["model_name", "ok", "elapsed_seconds", "reward_function_text", "error"],
        )
        writer.writeheader()
        for model_name, item in results.items():
            writer.writerow(
                {
                    "model_name": model_name,
                    "ok": item.get("ok", False),
                    "elapsed_seconds": item.get("elapsed_seconds", ""),
                    "reward_function_text": item.get("reward_function_text", ""),
                    "error": item.get("error", ""),
                }
            )

        writer.writerow({})
        writer.writerow({"model_name": "__summary__", "ok": ""})
        writer.writerow({"model_name": "total_elapsed_seconds", "ok": total_elapsed})
        writer.writerow({"model_name": "success_count", "ok": success_count})
        writer.writerow({"model_name": "failure_count", "ok": failure_count})
        writer.writerow({"model_name": "model_count", "ok": model_count})

    print(f"\n=== Stage1 completed ===")
    print(f"Stage1 total elapsed: {total_elapsed:.3f}s")
    print(f"Saved stage1 results to: {output_path}")
    print(f"Saved extracted reward functions CSV to: {csv_output_path}")
    return payload
