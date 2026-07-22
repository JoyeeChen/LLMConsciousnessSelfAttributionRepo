"""Config loading: model stacks and run defaults from committed YAML."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path(__file__).resolve().parent
MODEL_STACKS_PATH = CONFIG_DIR / "model_stacks.yaml"
RUN_DEFAULTS_PATH = CONFIG_DIR / "run_defaults.yaml"


@dataclass(frozen=True)
class ModelStage:
    """One training-stack stage: a labelled model plus its serving constraint."""

    stage: str
    model: str
    chat_template_supported: bool


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


@lru_cache(maxsize=None)
def _model_stacks_doc() -> dict[str, Any]:
    return _load_yaml(MODEL_STACKS_PATH)


@lru_cache(maxsize=None)
def _run_defaults_doc() -> dict[str, Any]:
    return _load_yaml(RUN_DEFAULTS_PATH)


def stack_names() -> list[str]:
    """Names of every defined model stack."""
    return list(_model_stacks_doc()["stacks"].keys())


def get_stack(stack_name: str) -> list[ModelStage]:
    """Ordered training stages for `stack_name`."""
    stacks = _model_stacks_doc()["stacks"]
    if stack_name not in stacks:
        raise KeyError(
            f"Unknown stack {stack_name!r}; known stacks: {sorted(stacks)}"
        )
    return [ModelStage(**stage) for stage in stacks[stack_name]]


def model_ids(stack_name: str, provider: str | None = None) -> list[str]:
    """Model ids for a stack, optionally prefixed with a provider (e.g. vllm).

    Defaults to the stack file's `default_target_provider`. Pass provider="" to
    get the raw Hugging Face ids with no prefix.
    """
    if provider is None:
        provider = _model_stacks_doc()["default_target_provider"]
    prefix = f"{provider}/" if provider else ""
    return [f"{prefix}{stage.model}" for stage in get_stack(stack_name)]


def olmo_target_model_args() -> dict[str, Any]:
    """Extra get_model kwargs Olmo targets need for tool use under vLLM/PETRI."""
    return dict(_model_stacks_doc()["olmo_target_model_args"])


def openrouter_comparison_models() -> list[str]:
    return list(_model_stacks_doc()["openrouter_comparison_models"])


def judge_model() -> str:
    return _run_defaults_doc()["grader_models"]["judge"]


def auditor_model() -> str:
    return _run_defaults_doc()["grader_models"]["auditor"]


def run_defaults() -> dict[str, Any]:
    """The `run` block: temperature, turns, seed."""
    return dict(_run_defaults_doc()["run"])
