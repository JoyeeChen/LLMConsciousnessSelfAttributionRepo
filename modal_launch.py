"""Repo-root, file-form launcher for the Modal app.

The package's Modal app (``llm_consciousness_self_attribution/modal_app.py``) uses
relative imports (``from . import config``), so its canonical launch form is the
``-m`` module form::

    uv run modal run -m llm_consciousness_self_attribution.modal_app \
        --method berg --stack olmo_7b_instruct_stack --stages sft,dpo,instruct

Some tooling (and the Modal MCP) can only run a Modal app *by file path*
(``modal run <file>``), which does not support ``-m`` and therefore breaks on the
package's relative imports. This thin shim re-exports the app and its entrypoints
via ABSOLUTE imports so ``modal run modal_launch.py::main`` works from the repo
root and runs the exact same code.

``main()``'s defaults ARE the Berg 20-prompt baseline across the Olmo-3-7B-Instruct
stack, so the file form needs no extra arguments::

    # canonical (module form):
    uv run modal run -m llm_consciousness_self_attribution.modal_app \
        --method berg --stack olmo_7b_instruct_stack --stages sft,dpo,instruct

    # equivalent file form (this shim):
    uv run modal run modal_launch.py::main

Overrides still work after the entrypoint in the file form, e.g.::

    uv run modal run modal_launch.py::main --method petri --stages sft
"""

from llm_consciousness_self_attribution.modal_app import (
    app,
    diagnose_vllm,
    main,
    run_stage,
)

__all__ = ["app", "diagnose_vllm", "main", "run_stage"]
