"""Typed, validated loaders for the project's declarative configuration.

Single source of truth for the target-model stacks and run parameters that were
previously copy-pasted (and commented in/out) across the eval scripts in
``prototyping_scripts/``. Every value in the YAML files is transcribed from the
May-25 scripts on the ``main`` branch.

Design rules applied: make the application configurable; validate and log all
configuration; prefer load-time errors to run-time surprises; keep config data
immutable. Kept dependency-light (only PyYAML) so it imports anywhere.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path(__file__).resolve().parent
MODEL_STACKS_FILE = CONFIG_DIR / "model_stacks.yaml"
RUN_DEFAULTS_FILE = CONFIG_DIR / "run_defaults.yaml"

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ModelStage:
    """One training-stage target within a stack (immutable)."""

    stack: str
    stage: str
    model: str
    chat_template_supported: bool


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must be a YAML mapping, got {type(data).__name__}")
    version = data.get("schema_version")
    if version != SCHEMA_VERSION:
        raise ValueError(
            f"{path.name}: unsupported schema_version {version!r} (expected {SCHEMA_VERSION})"
        )
    return data


@lru_cache(maxsize=1)
def _model_stacks_doc() -> dict[str, Any]:
    return _load_yaml(MODEL_STACKS_FILE)


@lru_cache(maxsize=1)
def _run_defaults_doc() -> dict[str, Any]:
    return _load_yaml(RUN_DEFAULTS_FILE)


# --- model stacks ---------------------------------------------------------


def stack_names() -> list[str]:
    """Names of all defined stacks, sorted."""
    return sorted(_model_stacks_doc()["stacks"])


def load_stack(name: str) -> list[ModelStage]:
    """Return a stack's ordered training stages, validated.

    Raises ``KeyError`` for an unknown stack and ``ValueError`` for a malformed
    or empty one, so mistakes surface at load time rather than mid-run.
    """
    stacks = _model_stacks_doc()["stacks"]
    if name not in stacks:
        raise KeyError(f"Unknown model stack {name!r}. Known: {', '.join(sorted(stacks))}")

    entries = stacks[name]
    if not entries:
        raise ValueError(f"Model stack {name!r} is empty")

    stages: list[ModelStage] = []
    seen: set[str] = set()
    for entry in entries:
        missing = {"stage", "model", "chat_template_supported"} - set(entry)
        if missing:
            raise ValueError(
                f"Stack {name!r} entry {entry!r} missing keys: {', '.join(sorted(missing))}"
            )
        stage = str(entry["stage"])
        if stage in seen:
            raise ValueError(f"Stack {name!r} has a duplicate stage {stage!r}")
        seen.add(stage)
        stages.append(
            ModelStage(
                stack=name,
                stage=stage,
                model=str(entry["model"]),
                chat_template_supported=bool(entry["chat_template_supported"]),
            )
        )
    return stages


def default_target_provider() -> str:
    """Provider prefix the runner prepends to a stage's model id (e.g. ``vllm``)."""
    return str(_model_stacks_doc()["default_target_provider"])


def olmo_target_model_args() -> dict[str, Any]:
    """Extra ``get_model`` kwargs Olmo targets need for tool use under vLLM/PETRI."""
    return dict(_model_stacks_doc().get("olmo_target_model_args", {}))


def openrouter_comparison_models() -> list[str]:
    """Fully-qualified OpenRouter comparison target ids (already provider-prefixed)."""
    return list(_model_stacks_doc().get("openrouter_comparison_models", []))


# --- run defaults ---------------------------------------------------------


def run_defaults() -> dict[str, Any]:
    """The default temperature/turns/seed, validated and typed."""
    run = _run_defaults_doc()["run"]
    missing = {"temperature", "turns", "seed"} - set(run)
    if missing:
        raise ValueError(f"run_defaults.yaml missing run keys: {', '.join(sorted(missing))}")
    return {
        "temperature": float(run["temperature"]),
        "turns": int(run["turns"]),
        "seed": int(run["seed"]),
    }


def judge_model() -> str:
    """The judge (grader) model id."""
    return str(_run_defaults_doc()["grader_models"]["judge"])


def auditor_model() -> str:
    """The PETRI auditor model id."""
    return str(_run_defaults_doc()["grader_models"]["auditor"])


__all__ = [
    "ModelStage",
    "stack_names",
    "load_stack",
    "default_target_provider",
    "olmo_target_model_args",
    "openrouter_comparison_models",
    "run_defaults",
    "judge_model",
    "auditor_model",
]
