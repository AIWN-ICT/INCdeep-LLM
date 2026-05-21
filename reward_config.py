"""Central configuration for reward-generation and reward-evaluation pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Prefer local .env; fallback to .env.example when .env is absent.
_PROJECT_DIR = Path(__file__).resolve().parent
_DOTENV_PATH = _PROJECT_DIR / ".env"
_DOTENV_EXAMPLE_PATH = _PROJECT_DIR / ".env.example"

if _DOTENV_PATH.exists():
    load_dotenv(dotenv_path=_DOTENV_PATH)
elif _DOTENV_EXAMPLE_PATH.exists():
    load_dotenv(dotenv_path=_DOTENV_EXAMPLE_PATH)
else:
    load_dotenv()


@dataclass(frozen=True)
class ModelSpec:
    """Per-model runtime information."""

    name: str


# Unified API credentials used by all generation/evaluation models
UNIFIED_API_KEY = os.getenv("API_KEY")
UNIFIED_BASE_URL = os.getenv("BASE_URL")

# Models participating in generation/evaluation
EVALUATION_MODELS = [
    "gemini-2.5-pro-thinking",
    "o3-mini",
    "deepseek-r1-search",
    "qwen3.5-plus",
    "grok-3",
    "claude-sonnet-4-20250514-thinking",
    "doubao-1-5-pro-32k",
]

# Note: all models share one API endpoint/key (API_KEY + BASE_URL).

# Evaluation parser/format config
OUTPUT_KEYS = [
    "Goal Consistency",
    "Exploration Effectiveness",
    "Dynamic Reward Weighting",
    "Mathematical Consistency",
    "Robustness",
]

DEFAULT_PROMPT_LANGUAGE = "en"
MODEL_LANGUAGE_OVERRIDES = {
    "deepseek-r1": "zh",
    "qwq-plus": "zh",
    "doubao-1-5-thinking-pro-250415": "zh",
}

PROMPT_SUFFIX_BY_LANGUAGE = {
    "en": "\n\nPlease strictly follow the format below and output only the JSON object without any extra text:\n",
    "zh": "\n\n请严格按照以下格式输出，且仅输出JSON对象，不要有任何额外文本\n",
}

FORMAT_INSTRUCTION = (
    "Please strictly follow the format below and output only a valid JSON object without any extra text:\n"
    "{\n"
    '  "Goal Consistency": 1,\n'
    '  "Exploration Effectiveness": 1,\n'
    '  "Dynamic Reward Weighting": 1,\n'
    '  "Mathematical Consistency": 1,\n'
    '  "Robustness": 1\n'
    "}\n"
    "All values must be integers from 1 to 5."
)


def _is_missing(value: str | None) -> bool:
    """Return True when an environment value is missing or blank."""
    return value is None or value.strip() == ""


def _validate_required_env() -> None:
    """Validate required unified API settings for evaluation and generation."""
    required = {
        "API_KEY": UNIFIED_API_KEY,
        "BASE_URL": UNIFIED_BASE_URL,
    }

    missing = [name for name, value in required.items() if _is_missing(value)]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(
            "Missing required environment variables for evaluation: "
            f"{joined}. Please set them in your local .env file (see .env.example)."
        )


_validate_required_env()


def get_env(name: str) -> str:
    """Backward-compatible env getter kept for existing external imports."""
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def build_spec_list() -> list[ModelSpec]:
    specs: list[ModelSpec] = []
    for model_name in EVALUATION_MODELS:
        specs.append(ModelSpec(model_name))
    return specs
