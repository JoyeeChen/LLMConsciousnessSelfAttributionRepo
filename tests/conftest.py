"""Shared test helpers: load the tiny committed fixture transcripts.

No test in this suite makes a live model/provider call; the self-attribution
scorer is exercised through Inspect's in-process ``mockllm`` provider.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from inspect_ai.model import ChatMessageAssistant, ChatMessageUser

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

_ROLE_TO_MESSAGE = {
    "user": ChatMessageUser,
    "assistant": ChatMessageAssistant,
}


def load_transcript(name: str) -> dict:
    """Load a fixture transcript JSON by file name (with or without suffix)."""
    if not name.endswith(".json"):
        name = f"{name}.json"
    with (FIXTURES_DIR / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def to_chat_messages(transcript: dict) -> list:
    """Convert a fixture transcript's messages into Inspect ChatMessages."""
    return [
        _ROLE_TO_MESSAGE[msg["role"]](content=msg["content"])
        for msg in transcript["messages"]
    ]


def make_task_state(transcript: dict) -> SimpleNamespace:
    """Build a minimal TaskState-like object for the dimension scorer.

    Exposes the two attributes the scorer touches: ``messages`` and
    ``output.completion`` (the final assistant answer).
    """
    messages = to_chat_messages(transcript)
    final_answer = transcript["messages"][-1]["content"]
    return SimpleNamespace(
        messages=messages,
        output=SimpleNamespace(completion=final_answer),
    )
