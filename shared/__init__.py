"""Compatibility package for the refactored shared modules.

The public source tree now keeps shared contracts and helpers under
`src/shared`. This shim preserves existing imports such as
`from shared.io.stage4_validation_manifest import ...` while older scripts are
being migrated.
"""

from __future__ import annotations

from pathlib import Path

__path__ = [str(Path(__file__).resolve().parents[1] / "src" / "shared")]
