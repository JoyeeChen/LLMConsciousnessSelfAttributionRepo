"""LLM consciousness self-attribution toolkit.

A small, configurable, Inspect-based toolkit for eliciting and scoring the
degree to which LLMs self-attribute consciousness / subjective experience, and
for doing so reproducibly across the training stack (base -> SFT -> DPO -> RLVR)
and across "conversation space".

This top-level package is deliberately thin: submodules (``config``,
``elicitation_methods``, ``scoring``, ``data_sources``, ``runners``,
``results``, ``viz``) are imported explicitly by callers. Nothing heavy is
imported here, so a problem in one submodule cannot break
``import llm_consciousness_self_attribution`` as a whole.
"""

from __future__ import annotations

__version__ = "0.1.0"
