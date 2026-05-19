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
    """Per-model API routing information."""

    name: str
    api_key_env: str
    base_url_env: str


# API credentials used by evaluation/runtime routing
GROUP1_KEY = os.getenv("GROUP1_API_KEY")
GROUP1_URL = os.getenv("GROUP1_BASE_URL")
GROUP2_KEY = os.getenv("GROUP2_API_KEY")
GROUP2_URL = os.getenv("GROUP2_BASE_URL")
GROUP3_KEY = os.getenv("HUNYUAN_API_KEY")
GROUP3_URL = os.getenv("HUNYUAN_BASE_URL")
GROUP4_KEY = os.getenv("DOUBAO_API_KEY")
GROUP4_URL = os.getenv("DOUBAO_BASE_URL")

# Models participating in generation/evaluation
EVALUATION_MODELS = [
    "gemini-2.5-pro-thinking",
    "o3-mini",
    "deepseek-r1",
    "qwq-plus",
    "grok-3",
    "cc-3-7-sonnet-20250219-thinking",
    "doubao-1-5-thinking-pro-250415",
]

# Model -> env routing for stage1 generation clients
MODEL_ENV_OVERRIDES: dict[str, tuple[str, str]] = {
    "qwq-plus": ("GROUP2_API_KEY", "GROUP2_BASE_URL"),
    "doubao-1-5-thinking-pro-250415": ("DOUBAO_API_KEY", "DOUBAO_BASE_URL"),
}
DEFAULT_MODEL_ENV: tuple[str, str] = ("GROUP1_API_KEY", "GROUP1_BASE_URL")

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
    """Validate required API settings for evaluation and generation."""
    required = {
        "GROUP1_API_KEY": GROUP1_KEY,
        "GROUP1_BASE_URL": GROUP1_URL,
        "GROUP2_API_KEY": GROUP2_KEY,
        "GROUP2_BASE_URL": GROUP2_URL,
        "HUNYUAN_API_KEY": GROUP3_KEY,
        "HUNYUAN_BASE_URL": GROUP3_URL,
        "DOUBAO_API_KEY": GROUP4_KEY,
        "DOUBAO_BASE_URL": GROUP4_URL,
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
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def build_spec_list() -> list[ModelSpec]:
    specs: list[ModelSpec] = []
    for model_name in EVALUATION_MODELS:
        key_env, url_env = MODEL_ENV_OVERRIDES.get(model_name, DEFAULT_MODEL_ENV)
        specs.append(ModelSpec(model_name, key_env, url_env))
    return specs
