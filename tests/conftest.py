"""Make the repo root importable so ``import llm_consciousness_self_attribution``
works when running pytest from anywhere in the repo.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
