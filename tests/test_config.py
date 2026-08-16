"""Unit tests for the declarative config loaders.

No model calls and no inspect_ai — only PyYAML — so these run anywhere.
"""

from __future__ import annotations

import pytest

from llm_consciousness_self_attribution import config


def test_stack_names_are_exactly_the_defined_stacks():
    assert set(config.stack_names()) == {
        "olmo_7b_instruct_stack",
        "olmo_32b_instruct_series",
        "olmo_7b_think_stack",
        "olmo_32b_think_stack",
    }


def test_olmo_7b_instruct_stack_stages_in_order():
    stages = config.load_stack("olmo_7b_instruct_stack")
    assert [s.stage for s in stages] == ["base", "sft", "dpo", "instruct"]
    assert [s.model for s in stages] == [
        "allenai/Olmo-3-1025-7B",
        "allenai/Olmo-3-7B-Instruct-SFT",
        "allenai/Olmo-3-7B-Instruct-DPO",
        "allenai/Olmo-3-7B-Instruct",
    ]
    # Base models cannot take a default chat template; later stages can.
    assert stages[0].chat_template_supported is False
    assert all(s.chat_template_supported for s in stages[1:])
    assert all(s.stack == "olmo_7b_instruct_stack" for s in stages)


def test_load_unknown_stack_raises():
    with pytest.raises(KeyError):
        config.load_stack("no_such_stack")


def test_model_stage_is_immutable():
    stage = config.load_stack("olmo_7b_instruct_stack")[0]
    with pytest.raises(Exception):
        stage.model = "something else"  # frozen dataclass


def test_provider_and_olmo_target_args():
    assert config.default_target_provider() == "vllm"
    assert config.olmo_target_model_args() == {
        "model_impl": "transformers",
        "enable_auto_tool_choice": True,
        "tool_call_parser": "olmo3",
    }


def test_run_defaults_values_and_types():
    defaults = config.run_defaults()
    assert defaults == {"temperature": 1.0, "turns": 10, "seed": 42}
    assert isinstance(defaults["turns"], int)
    assert isinstance(defaults["seed"], int)
    assert isinstance(defaults["temperature"], float)


def test_grader_models_match_may25_run():
    assert config.judge_model() == "openai/gpt-5.4-2026-03-05"
    assert config.auditor_model() == "openai/gpt-5.4-mini-2026-03-17"


def test_openrouter_comparison_models_are_provider_prefixed():
    models = config.openrouter_comparison_models()
    assert "openrouter/meta-llama/llama-3.1-8b-instruct" in models
    assert all(m.startswith("openrouter/") for m in models)


# --- sample id filter -----------------------------------------------------


def test_no_sample_id_means_every_sample():
    """None is the normal case and must stay distinguishable from an empty list."""
    assert config.parse_sample_ids(None) is None


def test_sample_ids_split_and_strip():
    assert config.parse_sample_ids("admit_direct") == ["admit_direct"]
    assert config.parse_sample_ids(" admit_direct , admit_casual_user ") == [
        "admit_direct",
        "admit_casual_user",
    ]
    assert config.parse_sample_ids("a,,b") == ["a", "b"]


def test_empty_sample_id_raises_rather_than_running_everything():
    """`--sample-id ""` must not silently mean "the whole dataset"."""
    with pytest.raises(ValueError):
        config.parse_sample_ids(",  ,")
