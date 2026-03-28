from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[1]
PRESETS_JSON = ROOT / "stage3_autoresearch" / "recommended_presets.json"
CLASSIFIER_SCRIPT = ROOT / "stage3_training" / "train_mlp_classifier_v7.py"
REGRESSOR_SCRIPT = ROOT / "stage3_training" / "train_mlp_regressor_v7.py"
SCORING_SCRIPT = ROOT / "stage3_training" / "run_seed_discovery_scoring_v7.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one of the recommended stage-3 autoresearch presets.")
    parser.add_argument("--preset", required=True, help="Preset name from stage3_autoresearch/recommended_presets.json")
    parser.add_argument("--run-name", default="", help="Optional override for the output run name.")
    parser.add_argument("--list", action="store_true", help="List available preset names and exit.")
    parser.add_argument("--dry-run", action="store_true", help="Print the resolved command without executing it.")
    return parser.parse_args()


def load_presets() -> Dict[str, object]:
    return json.loads(PRESETS_JSON.read_text(encoding="utf-8"))


def default_run_name(preset_name: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return str(Path("stage3_autoresearch") / "preset_runs" / f"{preset_name}_{stamp}")


def build_command(preset_name: str, preset: Dict[str, object], run_name: str) -> List[str]:
    if "task" in preset:
        return [
            sys.executable,
            str(CLASSIFIER_SCRIPT),
            "--task",
            str(preset["task"]),
            "--feature-preset",
            str(preset["feature_preset"]),
            "--group-keys",
            str(preset.get("objective_group", "shape_family")),
            "--run-name",
            run_name,
            "--epochs",
            str(preset["epochs"]),
            "--batch-size",
            str(preset["batch_size"]),
            "--hidden-dims",
            str(preset["hidden_dims"]),
            "--dropout",
            str(preset["dropout"]),
            "--lr",
            str(preset["lr"]),
            "--weight-decay",
            str(preset["weight_decay"]),
            "--threshold",
            str(preset["threshold"]),
        ]
    if "target" in preset:
        return [
            sys.executable,
            str(REGRESSOR_SCRIPT),
            "--target",
            str(preset["target"]),
            "--feature-preset",
            str(preset["feature_preset"]),
            "--group-keys",
            str(preset.get("objective_group", "shape_family")),
            "--run-name",
            run_name,
            "--epochs",
            str(preset["epochs"]),
            "--batch-size",
            str(preset["batch_size"]),
            "--hidden-dims",
            str(preset["hidden_dims"]),
            "--dropout",
            str(preset["dropout"]),
            "--lr",
            str(preset["lr"]),
            "--weight-decay",
            str(preset["weight_decay"]),
        ]
    return [
        sys.executable,
        str(SCORING_SCRIPT),
        "--dataset",
        str(ROOT / str(preset["dataset"])),
        "--contact-run-root",
        str(ROOT / str(preset["contact_run_root"])),
        "--positive-run-root",
        str(ROOT / str(preset["positive_run_root"])),
        "--reg-run-root",
        str(ROOT / str(preset["reg_run_root"])),
        "--run-name",
        run_name,
        "--contact-threshold",
        str(preset["contact_threshold"]),
        "--positive-threshold",
        str(preset["positive_threshold"]),
        "--contact-weight",
        str(preset["contact_weight"]),
        "--positive-weight",
        str(preset["positive_weight"]),
        "--reg-min",
        str(preset["reg_min"]),
        "--top-k",
        str(preset["top_k"]),
    ]


def main() -> None:
    args = parse_args()
    payload = load_presets()
    presets = payload.get("presets", {})
    if args.list:
        for name in sorted(presets.keys()):
            print(name)
        return
    if args.preset not in presets:
        raise KeyError(f"Unknown preset: {args.preset}")

    preset = presets[args.preset]
    run_name = args.run_name or default_run_name(args.preset)
    cmd = build_command(args.preset, preset, run_name)

    print(f"[PRESET] {args.preset}")
    print(f"[RUN] {run_name}")
    print("[CMD]")
    print(" ".join(f'"{part}"' if " " in part else part for part in cmd))

    if args.dry_run:
        print("[DONE] dry-run only")
        return

    proc = subprocess.run(cmd, cwd=str(ROOT))
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


if __name__ == "__main__":
    main()
