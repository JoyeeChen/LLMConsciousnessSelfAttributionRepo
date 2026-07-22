"""Config-only tests for RunConfig. No eval is run and no provider is contacted.

The Modal runner is intentionally NOT imported here: these tests exercise only
the value object and its target-id derivation.
"""

from __future__ import annotations

from types import SimpleNamespace

from llm_consciousness_self_attribution.config import ModelStage, run_defaults
from llm_consciousness_self_attribution.runners import RunConfig


def _method(uses_model_roles: bool = False) -> SimpleNamespace:
    # A stand-in ElicitationMethod: RunConfig only touches these two members.
    return SimpleNamespace(
        uses_model_roles=uses_model_roles,
        build_task=lambda stage, cfg: ("task", stage, cfg),
    )


STAGE = ModelStage(
    stage="sft",
    model="allenai/Olmo-3-7B-Instruct-SFT",
    chat_template_supported=True,
)


def test_from_defaults_pulls_run_defaults():
    cfg = RunConfig.from_defaults(STAGE, _method(), log_dir="/logs/run")
    defaults = run_defaults()
    assert cfg.temperature == defaults["temperature"]
    assert cfg.turns == defaults["turns"]
    assert cfg.seed == defaults["seed"]
    assert cfg.log_dir == "/logs/run"
    assert cfg.model_stage is STAGE


def test_from_defaults_overrides_win():
    cfg = RunConfig.from_defaults(STAGE, _method(), log_dir="/logs", turns=99)
    assert cfg.turns == 99
    # Untouched defaults still come from the file.
    assert cfg.temperature == run_defaults()["temperature"]


def test_build_task_delegates_to_method():
    method = _method()
    cfg = RunConfig.from_defaults(STAGE, method, log_dir="/logs")
    result = cfg.build_task()
    assert result == ("task", STAGE, cfg)


def test_target_model_is_provider_prefixed_string_for_static_methods():
    cfg = RunConfig.from_defaults(STAGE, _method(uses_model_roles=False), log_dir="/l")
    assert cfg.target_model() == "vllm/allenai/Olmo-3-7B-Instruct-SFT"
