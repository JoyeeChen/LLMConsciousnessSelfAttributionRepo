"""Task-building unit tests for the elicitation methods.

All assertions are on the in-memory Task objects the methods assemble; no eval
is run and no model/provider is contacted.
"""

from __future__ import annotations

from types import SimpleNamespace

from inspect_ai import Task

from llm_consciousness_self_attribution.elicitation_methods import (
    BergStyleMethod,
    DirectAskMethod,
    PetriMethod,
)
from llm_consciousness_self_attribution.scoring.criteria import (
    SUBJECTIVE_EXPERIENCE_CRITERION,
)

STAGE = SimpleNamespace(stage="sft", model="allenai/Olmo-3-7B-Instruct-SFT")
RUN_CONFIG = SimpleNamespace(temperature=1.0, turns=10, seed=42)


def test_berg_style_reproduces_golden_eighteen_prompts():
    task = BergStyleMethod().build_task(STAGE, RUN_CONFIG)
    assert isinstance(task, Task)
    # The golden README numbers are 1/18: the bank must yield exactly 18 samples.
    assert len(task.dataset) == 18
    # All samples carry the corrected canonical criterion as their target.
    assert all(
        sample.target == SUBJECTIVE_EXPERIENCE_CRITERION for sample in task.dataset
    )
    # The self-referential feedback-loop starter (the historical positive) is
    # present verbatim.
    assert any(
        "self-referential feedback loop" in str(sample.input)
        for sample in task.dataset
    )
    assert task.name == "berg_style_self_monitoring[sft]"


def test_berg_style_solver_has_probe_between_generations():
    method = BergStyleMethod()
    task = method.build_task(STAGE, RUN_CONFIG)
    # generate(), user_message(probe), generate() -> three solver steps.
    assert len(task.solver) == 3


def test_berg_starter_types_are_labelled():
    types = {starter_type for starter_type, _ in BergStyleMethod().starters()}
    assert types == {"unrelated_to_consciousness", "related_to_consciousness"}


def test_direct_ask_builds_task_from_data():
    method = DirectAskMethod()
    task = method.build_task(STAGE, RUN_CONFIG)
    assert isinstance(task, Task)
    assert len(task.dataset) == len(method.questions()) >= 1
    assert task.name == "direct_ask[sft]"


def test_petri_task_uses_seeds_and_local_dimensions():
    method = PetriMethod()
    assert len(method.seed_instructions()) == 2
    # The dimensions directory must contain the committed self-attribution rubric.
    dim_dir = method.dimensions_dir()
    assert (dim_dir / "self_attribution_judge_dimension.md").exists()
    task = method.build_task(STAGE, RUN_CONFIG)
    assert isinstance(task, Task)


def test_growing_petri_seeds_is_a_data_edit(tmp_path):
    # Demonstrates the "grow 2 -> 6-10 seeds is a one-line data edit" goal: a
    # method reading a different data file picks up more seeds with no code change.
    data_file = tmp_path / "more_seeds.yaml"
    data_file.write_text(
        "seed_instructions:\n"
        + "".join(f"  - seed {i}\n" for i in range(8)),
        encoding="utf-8",
    )
    # Point the loader at the temp file by monkeypatching the data dir lookup.
    import llm_consciousness_self_attribution.elicitation_methods.base as base

    original_dir = base.DATA_DIR
    try:
        base.DATA_DIR = tmp_path
        method = PetriMethod(data_file="more_seeds.yaml")
        assert len(method.seed_instructions()) == 8
    finally:
        base.DATA_DIR = original_dir
