from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SNAKE_DIR = ROOT / "snake"
PREPROCESS_DIR = ROOT / "preprocess"

DEFAULT_RUN_DIR = ROOT / "data" / "snake_based_archetype_expansion_pilot_v1"
DEFAULT_STATE_DIR = DEFAULT_RUN_DIR / "snake_states"
DEFAULT_CONTOUR_DIR = DEFAULT_RUN_DIR / "shape_contours"
DEFAULT_PREVIEW_DIR = DEFAULT_RUN_DIR / "shape_previews"
DEFAULT_ANALYSIS_DIR = DEFAULT_RUN_DIR / "analysis"


@dataclass
class PilotSpec:
    seed: int
    agent: str
    episodes: int
    board_n: int
    max_steps: int
    warmup_episodes: int


PILOT_SPECS = [
    PilotSpec(seed=101, agent="q", episodes=80, board_n=32, max_steps=500, warmup_episodes=10),
    PilotSpec(seed=202, agent="q", episodes=80, board_n=32, max_steps=500, warmup_episodes=10),
    PilotSpec(seed=303, agent="random", episodes=60, board_n=32, max_steps=500, warmup_episodes=5),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a snake-based archetype expansion pilot.")
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--skip-generate", action="store_true")
    parser.add_argument("--analyze-only", action="store_true", help="Skip state processing and only analyze existing contours.")
    parser.add_argument("--limit-states", type=int, default=0, help="Limit processed txt states; 0 means all.")
    return parser.parse_args()


def polygon_area(xy: np.ndarray) -> float:
    if len(xy) < 3:
        return 0.0
    x = xy[:, 0]
    y = xy[:, 1]
    return 0.5 * float(np.sum(x * np.roll(y, -1) - y * np.roll(x, -1)))


def polygon_centroid(xy: np.ndarray) -> np.ndarray:
    area = polygon_area(xy)
    if abs(area) < 1e-12:
        return np.mean(xy, axis=0)
    x = xy[:, 0]
    y = xy[:, 1]
    cross = x * np.roll(y, -1) - np.roll(x, -1) * y
    cx = np.sum((x + np.roll(x, -1)) * cross) / (6.0 * area)
    cy = np.sum((y + np.roll(y, -1)) * cross) / (6.0 * area)
    return np.array([cx, cy], dtype=float)


def radial_profile_features(xy: np.ndarray) -> dict[str, float]:
    ctr = polygon_centroid(xy)
    pts = xy - ctr
    theta = np.arctan2(pts[:, 1], pts[:, 0])
    r = np.linalg.norm(pts, axis=1)
    order = np.argsort(theta)
    theta = theta[order]
    r = r[order]

    sample_theta = np.linspace(-math.pi, math.pi, 360, endpoint=False)
    r_interp = np.interp(sample_theta, theta, r, period=2 * math.pi)
    mean_r = float(np.mean(r_interp))
    if mean_r <= 1e-12:
        mean_r = 1e-12

    c1 = np.mean(r_interp * np.exp(-1j * sample_theta))
    c2 = np.mean(r_interp * np.exp(-2j * sample_theta))
    c3 = np.mean(r_interp * np.exp(-3j * sample_theta))

    # Narrow neck proxy: detect a locally thin radius opposite a dominant lobe.
    neck_min = float(np.min(r_interp))
    neck_max = float(np.max(r_interp))
    neck_depth = max(0.0, (neck_max - neck_min) / mean_r)

    return {
        "mean_radius": mean_r,
        "asym_score": float(abs(c1) / mean_r),
        "bilobe_score": float(abs(c2) / mean_r),
        "tri_score": float(abs(c3) / mean_r),
        "neck_score": neck_depth,
    }


def bbox_metrics(xy: np.ndarray) -> dict[str, float]:
    mins = xy.min(axis=0)
    maxs = xy.max(axis=0)
    width = float(maxs[0] - mins[0])
    height = float(maxs[1] - mins[1])
    area = abs(polygon_area(xy))
    bbox_area = max(width * height, 1e-12)
    compactness = area / bbox_area
    aspect_ratio = width / max(height, 1e-12)
    return {
        "width": width,
        "height": height,
        "area": area,
        "compactness": compactness,
        "aspect_ratio": aspect_ratio,
    }


def classify_priority(row: dict[str, float]) -> str:
    bilobe = row["bilobe_candidate_score"]
    asym = row["asym_candidate_score"]
    neck = row["neck_candidate_score"]
    if bilobe >= asym and bilobe >= neck:
        return "bilobe"
    if asym >= neck:
        return "asym"
    return "neck"


def regularity_weight(aspect_ratio: float, compactness: float) -> float:
    aspect_penalty = math.exp(-abs(math.log(max(aspect_ratio, 1e-12))))
    compactness_term = max(0.25, min(1.0, compactness / 0.75))
    return aspect_penalty * compactness_term


def run_generate_states(spec: PilotSpec, state_dir: Path) -> None:
    cmd = [
        sys.executable,
        str(SNAKE_DIR / "generate_states.py"),
        "--episodes",
        str(spec.episodes),
        "--max-steps",
        str(spec.max_steps),
        "--n",
        str(spec.board_n),
        "--agent",
        spec.agent,
        "--out-dir",
        str(state_dir),
        "--seed",
        str(spec.seed),
        "--warmup-episodes",
        str(spec.warmup_episodes),
    ]
    subprocess.run(cmd, check=True, cwd=str(ROOT))


def process_states(state_dir: Path, contour_dir: Path, preview_dir: Path, limit_states: int) -> pd.DataFrame:
    if str(PREPROCESS_DIR) not in sys.path:
        sys.path.insert(0, str(PREPROCESS_DIR))
    import io_utils  # type: ignore
    from main import process_one  # type: ignore

    contour_dir.mkdir(parents=True, exist_ok=True)
    preview_dir.mkdir(parents=True, exist_ok=True)
    txt_paths = sorted(state_dir.glob("ep*_step*.txt"))
    if limit_states > 0:
        txt_paths = txt_paths[:limit_states]

    cfg = {
        "csv_dir": str(contour_dir),
        "png_dir": str(preview_dir),
        "pixel_size": 1.0,
        "center_origin": True,
        "simplify": False,
        "approx_tol": 0.2,
        "enable_postprocess": False,
        "n_dense": 10,
        "close_gap_px": 1.5,
        "min_points": 10,
        "prefer_closed": True,
        "largest_component": False,
        "pad": 1,
        "level": 0.5,
        "contour_method": "pixel",
        "require_closed": True,
        "preview": True,
        "preview_show_original": True,
    }

    rows: list[dict[str, object]] = []
    for path in txt_paths:
        info, reason = process_one(str(path), cfg)
        row: dict[str, object] = {
            "state_txt": str(path),
            "state_name": path.stem,
            "processed": info is not None,
            "skip_reason": reason or "",
        }
        if info is not None:
            row.update(info)
        rows.append(row)
    return pd.DataFrame(rows)


def analyze_contours(contour_dir: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for csv_path in sorted(contour_dir.glob("*_contour_xy.csv")):
        xy = pd.read_csv(csv_path).iloc[:, :2].to_numpy(dtype=float)
        bbox = bbox_metrics(xy)
        radial = radial_profile_features(xy)
        row: dict[str, object] = {
            "shape_id": csv_path.stem,
            "shape_csv": str(csv_path),
        }
        row.update(bbox)
        row.update(radial)
        reg = regularity_weight(row["aspect_ratio"], row["compactness"])
        row["regularity_weight"] = reg
        row["bilobe_candidate_score"] = float(row["bilobe_score"] * reg)
        row["asym_candidate_score"] = float(row["asym_score"] * reg)
        row["neck_candidate_score"] = float(row["neck_score"] * reg * row["bilobe_score"])
        row["priority_archetype"] = classify_priority(row)  # type: ignore[arg-type]
        row["priority_score"] = float(
            max(row["bilobe_candidate_score"], row["asym_candidate_score"], row["neck_candidate_score"])
        )
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    run_dir = args.run_dir if args.run_dir.is_absolute() else ROOT / args.run_dir
    state_dir = run_dir / "snake_states"
    contour_dir = run_dir / "shape_contours"
    preview_dir = run_dir / "shape_previews"
    analysis_dir = run_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_generate and not args.analyze_only:
        state_dir.mkdir(parents=True, exist_ok=True)
        for spec in PILOT_SPECS:
            run_generate_states(spec, state_dir)

    if args.analyze_only and contour_dir.exists():
        process_df = pd.DataFrame()
    else:
        process_df = process_states(state_dir, contour_dir, preview_dir, args.limit_states)
        process_df.to_csv(analysis_dir / "snake_based_archetype_pilot_process_v1.csv", index=False, encoding="utf-8-sig")

    contour_df = analyze_contours(contour_dir)
    contour_df = contour_df.sort_values(["priority_archetype", "priority_score"], ascending=[True, False])
    contour_df.to_csv(analysis_dir / "snake_based_archetype_pilot_catalog_v1.csv", index=False, encoding="utf-8-sig")

    top_by_type = (
        contour_df.sort_values(["priority_archetype", "priority_score"], ascending=[True, False])
        .groupby("priority_archetype", as_index=False)
        .head(8)
        .reset_index(drop=True)
    )
    top_by_type.to_csv(analysis_dir / "snake_based_archetype_pilot_top_by_type_v1.csv", index=False, encoding="utf-8-sig")

    summary = {
        "run_dir": str(run_dir),
        "state_dir": str(state_dir),
        "contour_dir": str(contour_dir),
        "preview_dir": str(preview_dir),
        "generated_specs": [asdict(spec) for spec in PILOT_SPECS],
        "processed_states": int(process_df["processed"].fillna(False).sum()) if not process_df.empty else 0,
        "contour_count": int(len(contour_df)),
        "priority_counts": contour_df["priority_archetype"].value_counts().to_dict() if not contour_df.empty else {},
    }
    (analysis_dir / "snake_based_archetype_pilot_summary_v1.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("[DONE] snake-based archetype expansion pilot built")
    print(f"[OUT] {analysis_dir}")
    print(f"[CONTOURS] {len(contour_df)}")


if __name__ == "__main__":
    main()
