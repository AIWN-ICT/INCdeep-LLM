"""Stage1 reward-function generation runner."""

from __future__ import annotations

import json
import re
import time
from typing import Dict

from langchain_openai import ChatOpenAI

from reward_config import MODEL_LANGUAGE_OVERRIDES, ModelSpec, build_spec_list, get_env
from reward_prompt_templates import REWARD_FUNCTION_DESIGN_PROMPTS_BY_LANGUAGE


def _build_client(spec: ModelSpec) -> ChatOpenAI:
    """Create generation-model client from model spec.

    Args:
        spec: Model spec with name and env var keys.

    Returns:
        Configured ``ChatOpenAI`` instance.
    """
    return ChatOpenAI(
        model=spec.name,
        temperature=0.0,
        openai_api_key=get_env(spec.api_key_env),
        openai_api_base=get_env(spec.base_url_env),
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
) -> Dict[str, Dict[str, object]]:
    """Run stage1 generation for all configured models.

    Args:
        prompt: Optional custom prompt; if omitted, language-specific
            defaults are chosen per model.
        output_path: JSON file path used to persist generation results.

    Returns:
        Mapping of model name to generation status, runtime, and outputs.
    """
    results: Dict[str, Dict[str, object]] = {}

    for spec in build_spec_list():
        print(f"\n=== Stage1: generating with model: {spec.name} ===")
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
            print(f"Success: {spec.name}, elapsed={elapsed:.2f}s")
        except Exception as exc:
            elapsed = time.time() - start
            results[spec.name] = {
                "ok": False,
                "elapsed_seconds": round(elapsed, 3),
                "error": str(exc),
            }
            print(f"Failed: {spec.name}, elapsed={elapsed:.2f}s, error={exc}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nSaved stage1 results to: {output_path}")
    return results
