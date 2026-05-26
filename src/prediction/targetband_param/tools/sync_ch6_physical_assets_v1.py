from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
CH6_DISPLAY_DIR = ROOT / "output" / "thesis_charts" / "chapter6"
MECH_DIR = CH6_DISPLAY_DIR / "physical_mechanism"


@dataclass(frozen=True)
class CopySpec:
    src: Path
    dst: Path


def copy_file(src: Path, dst: Path) -> bool:
    if not src.is_file():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def copy_tree_pngs(src_dir: Path, dst_dir: Path) -> list[dict[str, str]]:
    copied: list[dict[str, str]] = []
    if not src_dir.exists():
        return copied
    for path in src_dir.rglob("*"):
        if not path.exists() or not path.is_file():
            continue
        rel = path.relative_to(src_dir)
        dst = dst_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(path, dst)
        except OSError:
            continue
        copied.append({"src": str(path), "dst": str(dst)})
    return copied


def sync_static_assets() -> list[dict[str, str]]:
    copied: list[dict[str, str]] = []

    # Canonical mode shapes
    copied.extend(copy_tree_pngs(ROOT / "data" / "analysis" / "canonical_mode_shapes_v1", MECH_DIR / "canonical_mode_shapes_v1"))

    # Shape archetype mode shapes
    copied.extend(copy_tree_pngs(ROOT / "data" / "analysis" / "shape_archetype_targetband_mode_shapes_v1", MECH_DIR / "shape_archetype_targetband_mode_shapes_v1"))

    # ep17 witness dispersion and any mode shapes already exported
    copied.extend(copy_tree_pngs(ROOT / "data" / "analysis" / "ep17_bilobe_witness_case_v1" / "dispersion", MECH_DIR / "ep17_bilobe_witness_case_v1" / "dispersion"))
    copied.extend(copy_tree_pngs(ROOT / "data" / "analysis" / "ep17_bilobe_witness_case_v1" / "mode_shapes", MECH_DIR / "ep17_bilobe_witness_case_v1" / "mode_shapes"))

    # Canonical local robustness dispersion panels
    copied.extend(copy_tree_pngs(ROOT / "data" / "analysis" / "canonical_local_robustness_v1" / "dispersion_plots", MECH_DIR / "canonical_local_robustness_v1" / "dispersion_plots"))

    # Chapter 6 mechanism field maps
    copied.extend(copy_tree_pngs(ROOT / "data" / "analysis" / "ch6_mechanism_field_maps_v1", MECH_DIR / "ch6_mechanism_field_maps_v1"))

    return copied


def main() -> None:
    MECH_DIR.mkdir(parents=True, exist_ok=True)
    copied = sync_static_assets()
    manifest = {
        "chapter_dir": str(CH6_DISPLAY_DIR),
        "mechanism_dir": str(MECH_DIR),
        "copied_count": len(copied),
        "copies": copied,
    }
    (MECH_DIR / "physical_mechanism_manifest_v1.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(MECH_DIR)


if __name__ == "__main__":
    main()
