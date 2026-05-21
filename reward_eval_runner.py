"""Core evaluation and reporting helpers for reward-function evaluation."""

import os
import time
from typing import Any, Dict

import pandas as pd
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from tqdm import tqdm

from data_processor import sanitize_filename
from reward_config import (
    DEFAULT_PROMPT_LANGUAGE,
    EVALUATION_MODELS,
    FORMAT_INSTRUCTION,
    MODEL_LANGUAGE_OVERRIDES,
    OUTPUT_KEYS,
    PROMPT_SUFFIX_BY_LANGUAGE,
    UNIFIED_API_KEY,
    UNIFIED_BASE_URL,
)
from reward_prompt_templates import PROMPTS_BY_LANGUAGE
from reward_prompt_assets import REWARD_FUNCTIONS


def _resolve_language(model_name: str) -> str:
    """Resolve prompt language for a model with safe fallback.

    Args:
        model_name: Target evaluator model name.

    Returns:
        Language code used to format prompts.
    """
    language = MODEL_LANGUAGE_OVERRIDES.get(model_name, DEFAULT_PROMPT_LANGUAGE)
    return language if language in PROMPT_SUFFIX_BY_LANGUAGE else DEFAULT_PROMPT_LANGUAGE


def _build_llm_and_prompt(model_name: str, prompt: str, language: str):
    """Build evaluator LLM client and formatted chat prompt.

    All models use one unified API key/base-url pair.

    Args:
        model_name: Evaluator model name.
        prompt: Filled evaluation prompt body.
        language: Prompt language key (e.g., ``en``/``zh``).

    Returns:
        Tuple of ``(llm, chat_prompt)`` ready for invocation.
    """
    llm = ChatOpenAI(
        model=model_name,
        temperature=0.0,
        openai_api_key=UNIFIED_API_KEY,
        openai_api_base=UNIFIED_BASE_URL,
    )

    message_suffix = PROMPT_SUFFIX_BY_LANGUAGE[language]
    chat_prompt = ChatPromptTemplate.from_messages(
        [HumanMessage(content=prompt.strip() + message_suffix + FORMAT_INSTRUCTION)]
    )
    return llm, chat_prompt


def _safe_parse_score(parser: JsonOutputParser, model_name: str, content: str):
    """Parse and validate evaluator JSON output.

    Args:
        parser: JSON parser instance.
        model_name: Evaluator model name for logging.
        content: Raw model response text.

    Returns:
        Parsed score dict when valid, otherwise ``None``.
    """
    try:
        parsed = parser.parse(content)
    except Exception as exc:
        print(f"⚠️ Failed to parse output from model {model_name}: {exc}")
        return None

    if not isinstance(parsed, dict):
        print(f"⚠️ Parsed output from model {model_name} is not a JSON object; skipping this model")
        return None

    missing_keys = [key for key in OUTPUT_KEYS if key not in parsed]
    if missing_keys:
        print(f"⚠️ Output from model {model_name} is missing fields: {missing_keys}")
        return None

    return parsed


def run_evaluation(reward_functions: Dict[str, str] | None = None) -> Dict[str, Any]:
    """Evaluate reward functions with cross-model scoring.

    Args:
        reward_functions: Optional mapping ``{name: reward_function_code}``.
            When omitted, built-in assets are used.

    Returns:
        Result dictionary including scores, averages, per-model latency,
        and total runtime.
    """
    parser = JsonOutputParser()
    scores_by_reward_function: Dict[str, Dict[str, int]] = {}
    avg_score_by_reward_function: Dict[str, float] = {}
    response_times: Dict[str, Dict[str, float]] = {}

    if reward_functions is None:
        source_type = "default"
        source_path = "reward_prompt_assets.py::REWARD_FUNCTIONS"
        target_reward_functions = REWARD_FUNCTIONS
    else:
        source_type = "generated"
        source_path = "(provided via argument)"
        target_reward_functions = reward_functions

    print("\n=== Evaluation source info ===")
    print(f"source_type: {source_type}")
    print(f"count: {len(target_reward_functions)}")
    if source_type == "default":
        print(f"path: {source_path}")

    start_time = time.time()

    with tqdm(target_reward_functions.items(), desc="Reward function evaluation", ncols=80) as pbar_outer:
        for reward_name, reward_function in pbar_outer:
            pbar_outer.set_postfix_str(f"current: {reward_name}")
            response_times[reward_name] = {}
            score_list: Dict[str, int] = {}

            evaluators = [model_name for model_name in EVALUATION_MODELS if model_name != reward_name]
            with tqdm(evaluators, desc="Model scoring", leave=False, ncols=80) as pbar_inner:
                for model_name in pbar_inner:
                    language = _resolve_language(model_name)
                    prompt_tpl = PROMPTS_BY_LANGUAGE[language]
                    prompt = prompt_tpl.format(reward_function=reward_function)

                    model_start_time = time.time()
                    llm, chat_prompt = _build_llm_and_prompt(model_name, prompt, language)
                    messages = chat_prompt.format_prompt().to_messages()

                    try:
                        result = llm.invoke(messages)
                        elapsed = time.time() - model_start_time
                        response_times[reward_name][model_name] = elapsed
                    except Exception as exc:
                        print(f"⚠️ Failed to call model {model_name}: {exc}")
                        response_times[reward_name][model_name] = -1
                        continue

                    parsed = _safe_parse_score(parser, model_name, result.content)
                    if parsed is None:
                        continue

                    total_score = sum(int(parsed[key]) for key in OUTPUT_KEYS)
                    score_list[model_name] = total_score
                    pbar_inner.update(1)

            scores_by_reward_function[reward_name] = score_list
            avg_score_by_reward_function[reward_name] = sum(score_list.values()) / len(score_list) if score_list else 0

    total_time = time.time() - start_time

    return {
        "scores_by_reward_function": scores_by_reward_function,
        "avg_score_by_reward_function": avg_score_by_reward_function,
        "response_times": response_times,
        "total_time": total_time,
    }


def save_reports(result: Dict[str, Any], output_dir: str = ".") -> None:
    """Persist evaluation artifacts as CSV reports.

    Args:
        result: Output dictionary returned by ``run_evaluation``.
        output_dir: Directory to store generated report files.
    """
    os.makedirs(output_dir, exist_ok=True)
    response_times_path = os.path.join(output_dir, sanitize_filename("auto_eval_response_times_by_reward_function.csv", fallback="response_times"))
    avg_response_times_path = os.path.join(output_dir, sanitize_filename("auto_eval_average_response_time_by_model.csv", fallback="avg_response_times"))
    model_scores_path = os.path.join(output_dir, sanitize_filename("auto_eval_scores_by_reward_function.csv", fallback="scores"))
    ranking_path = os.path.join(output_dir, sanitize_filename("auto_eval_reward_function_ranking.csv", fallback="ranking"))

    response_times_df = pd.DataFrame.from_dict(result["response_times"], orient="index")
    response_times_df.to_csv(response_times_path, index=True, index_label="Reward_Function")

    avg_response_times = {}
    for model in response_times_df.columns:
        valid_times = response_times_df[model][response_times_df[model] != -1]
        avg_response_times[model] = valid_times.mean() if not valid_times.empty else -1

    avg_times_df = pd.DataFrame.from_dict(avg_response_times, orient="index", columns=["Average_Response_Time"])
    avg_times_df.sort_values("Average_Response_Time", ascending=True).to_csv(avg_response_times_path)

    df = pd.DataFrame.from_dict(result["scores_by_reward_function"], orient="index").fillna(0)
    df.to_csv(model_scores_path, index=True, index_label="Reward_Function")

    df_avg = pd.DataFrame(
        list(result["avg_score_by_reward_function"].items()),
        columns=["Reward_Function", "Average_Score"],
    )
    df_avg.sort_values(by="Average_Score", ascending=False).to_csv(ranking_path, index=False)
