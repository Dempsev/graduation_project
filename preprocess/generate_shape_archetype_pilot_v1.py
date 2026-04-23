from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SHAPE_DIR = ROOT / "data" / "shape_contours"
OUT_ANALYSIS_DIR = ROOT / "data" / "analysis" / "shape_archetype_pilot_v1"

SEED_SHAPES: List[Dict[str, str]] = [
    {"seed_shape_id": "ep130_step66_contour_xy", "seed_family": "ep130"},
    {"seed_shape_id": "ep183_step60_contour_xy", "seed_family": "ep183"},
    {"seed_shape_id": "ep195_step9_contour_xy", "seed_family": "ep195"},
    {"seed_shape_id": "ep253_step54_contour_xy", "seed_family": "ep253"},
]

STRENGTH_LEVELS: List[Tuple[str, int, float]] = [
    ("mild", 12, 0.60),
    ("medium", 24, 1.00),
    ("strong", 36, 1.40),
]


def ensure_closed(xy: np.ndarray) -> np.ndarray:
    if xy.shape[0] < 2:
        return xy
    if np.linalg.norm(xy[0] - xy[-1]) > 1e-12:
        xy = np.vstack([xy, xy[0]])
    return xy


def load_contour(shape_id: str) -> np.ndarray:
    path = SHAPE_DIR / f"{shape_id}.csv"
    df = pd.read_csv(path)
    xy = df[["x", "y"]].to_numpy(dtype=float)
    return ensure_closed(xy)


def save_contour(path: Path, xy: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"x": xy[:, 0], "y": xy[:, 1]}).to_csv(path, index=False)


def bbox_stats(xy: np.ndarray) -> Tuple[float, float, float, float, float, float]:
    x = xy[:, 0]
    y = xy[:, 1]
    xmin, xmax = float(x.min()), float(x.max())
    ymin, ymax = float(y.min()), float(y.max())
    sx = max(1e-9, xmax - xmin)
    sy = max(1e-9, ymax - ymin)
    cx = 0.5 * (xmin + xmax)
    cy = 0.5 * (ymin + ymax)
    return xmin, xmax, ymin, ymax, sx, sy, cx, cy


def normalize_to_seed_bbox(original: np.ndarray, transformed: np.ndarray) -> np.ndarray:
    _, _, _, _, sx0, sy0, cx0, cy0 = bbox_stats(original)
    _, _, _, _, sx1, sy1, cx1, cy1 = bbox_stats(transformed)
    sx1 = max(sx1, 1e-12)
    sy1 = max(sy1, 1e-12)
    x_new = cx0 + (transformed[:, 0] - cx1) * (sx0 / sx1)
    y_new = cy0 + (transformed[:, 1] - cy1) * (sy0 / sy1)
    return np.column_stack([x_new, y_new])


def polygon_area(xy: np.ndarray) -> float:
    if xy.shape[0] < 3:
        return 0.0
    x = xy[:, 0]
    y = xy[:, 1]
    return float(0.5 * np.abs(np.dot(x[:-1], y[1:]) - np.dot(y[:-1], x[1:])))


def match_seed_area_floor(
    original: np.ndarray,
    transformed: np.ndarray,
    target_ratio: float = 0.88,
    max_iter: int = 28,
) -> np.ndarray:
    """Relax a transformed contour toward the seed until its area is not too small.

    The final contour still keeps the seed bbox normalization, but avoids making the
    pilot archetype look much smaller than the snake-generated library.
    """

    area0 = max(1e-12, polygon_area(original))
    area1 = polygon_area(transformed)
    if area1 / area0 >= target_ratio:
        return transformed

    lo, hi = 0.0, 1.0
    best = original
    delta = transformed - original
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        candidate = original + mid * delta
        candidate = normalize_to_seed_bbox(original, candidate)
        ratio = polygon_area(candidate) / area0
        if ratio >= target_ratio:
            best = candidate
            lo = mid
        else:
            hi = mid
    return best


def transform_asymmetry(xy: np.ndarray, strength: float) -> np.ndarray:
    _, _, _, _, sx, sy, cx, cy = bbox_stats(xy)
    xn = (xy[:, 0] - cx) / sx
    yn = (xy[:, 1] - cy) / sy
    x_new = xy[:, 0] + strength * sx * (0.12 * yn + 0.04 * np.sign(yn) * yn**2)
    y_new = cy + (xy[:, 1] - cy) * (1.0 + strength * 0.07 * np.clip(xn, -0.4, 1.0))
    out = np.column_stack([x_new, y_new])
    out = normalize_to_seed_bbox(xy, out)
    return match_seed_area_floor(xy, out, target_ratio=0.88)


def transform_neck_bridge(xy: np.ndarray, strength: float) -> np.ndarray:
    _, _, _, _, sx, sy, cx, cy = bbox_stats(xy)
    yn = (xy[:, 1] - cy) / sy
    squeeze = 1.0 - strength * 0.12 * np.exp(-((yn / 0.28) ** 2))
    x_new = cx + (xy[:, 0] - cx) * squeeze
    y_new = cy + (xy[:, 1] - cy) * (1.0 + strength * 0.03 * (1.0 - np.abs(yn)))
    out = np.column_stack([x_new, y_new])
    out = normalize_to_seed_bbox(xy, out)
    return match_seed_area_floor(xy, out, target_ratio=0.90)


def transform_bilobe_offset(xy: np.ndarray, strength: float) -> np.ndarray:
    _, _, _, _, sx, sy, cx, cy = bbox_stats(xy)
    xn = (xy[:, 0] - cx) / sx
    yn = (xy[:, 1] - cy) / sy
    x_new = xy[:, 0] + strength * sx * (0.10 * np.tanh(3.0 * yn) + 0.03 * np.sign(yn) * (1.0 - yn**2))
    y_new = cy + (xy[:, 1] - cy) * (1.0 + strength * 0.06 * np.clip(np.abs(xn), 0.0, 1.0))
    out = np.column_stack([x_new, y_new])
    out = normalize_to_seed_bbox(xy, out)
    return match_seed_area_floor(xy, out, target_ratio=0.88)


ARCHETYPES: List[Dict[str, object]] = [
    {
        "archetype_tag": "asym",
        "family_prefix": "pas",
        "title": "Asymmetry",
        "transform": transform_asymmetry,
    },
    {
        "archetype_tag": "neck",
        "family_prefix": "pne",
        "title": "NeckBridge",
        "transform": transform_neck_bridge,
    },
    {
        "archetype_tag": "bilobe",
        "family_prefix": "pbi",
        "title": "BilobeOffset",
        "transform": transform_bilobe_offset,
    },
]


def build_shape_id(prefix: str, seed_family: str, step_num: int) -> Tuple[str, str]:
    family = f"{prefix}{seed_family[-3:]}"
    shape_id = f"{family}_step{step_num}_contour_xy"
    return family, shape_id


def render_preview(rows: List[Dict[str, object]], out_path: Path, archetype_tag: str) -> None:
    part = [row for row in rows if row["archetype_tag"] == archetype_tag]
    if not part:
        return
    fig, axes = plt.subplots(4, 3, figsize=(8, 10), constrained_layout=True)
    for ax, row in zip(axes.flat, part):
        xy = pd.read_csv(row["shape_csv"])[["x", "y"]].to_numpy(dtype=float)
        ax.plot(xy[:, 0], xy[:, 1], color="#1f4e79", linewidth=2)
        ax.fill(xy[:, 0], xy[:, 1], color="#9ecae1", alpha=0.35)
        ax.set_title(f"{row['shape_family']} / {row['strength_label']}", fontsize=9)
        ax.set_aspect("equal")
        ax.axis("off")
    for ax in axes.flat[len(part):]:
        ax.axis("off")
    fig.suptitle(f"Shape Archetype Pilot: {archetype_tag}", fontsize=14)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def main() -> None:
    OUT_ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    catalog_rows: List[Dict[str, object]] = []
    whitelist_ids: List[str] = []

    for archetype in ARCHETYPES:
        transform: Callable[[np.ndarray, float], np.ndarray] = archetype["transform"]  # type: ignore[assignment]
        for seed in SEED_SHAPES:
            original = load_contour(seed["seed_shape_id"])
            for strength_label, step_num, strength in STRENGTH_LEVELS:
                family, shape_id = build_shape_id(str(archetype["family_prefix"]), seed["seed_family"], step_num)
                transformed = transform(original, strength)
                transformed = ensure_closed(transformed)
                csv_path = SHAPE_DIR / f"{shape_id}.csv"
                save_contour(csv_path, transformed)
                whitelist_ids.append(shape_id)
                catalog_rows.append(
                    {
                        "archetype_tag": archetype["archetype_tag"],
                        "archetype_title": archetype["title"],
                        "seed_shape_id": seed["seed_shape_id"],
                        "seed_family": seed["seed_family"],
                        "shape_family": family,
                        "shape_id": shape_id,
                        "strength_label": strength_label,
                        "strength_value": strength,
                        "step_num": step_num,
                        "shape_csv": str(csv_path),
                    }
                )

    catalog = pd.DataFrame(catalog_rows).sort_values(
        ["archetype_tag", "seed_family", "step_num"], ascending=[True, True, True]
    )
    catalog.to_csv(OUT_ANALYSIS_DIR / "shape_archetype_pilot_catalog_v1.csv", index=False, encoding="utf-8-sig")

    whitelist_payload = {
        "enabled_shape_ids": whitelist_ids,
        "notes": [
            "Pilot shape sublibrary for step-2 archetype exploration.",
            "Families are grouped by archetype prefix: pas=asym, pne=neck, pbi=bilobe.",
        ],
    }
    (OUT_ANALYSIS_DIR / "shape_archetype_pilot_whitelist_v1.json").write_text(
        json.dumps(whitelist_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    summary = {
        "archetype_count": len(ARCHETYPES),
        "seed_shape_count": len(SEED_SHAPES),
        "strength_levels": [label for label, _, _ in STRENGTH_LEVELS],
        "generated_shape_count": len(catalog_rows),
        "generated_family_count": int(catalog["shape_family"].nunique()),
    }
    (OUT_ANALYSIS_DIR / "shape_archetype_pilot_summary_v1.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    for archetype in ARCHETYPES:
        render_preview(
            catalog_rows,
            OUT_ANALYSIS_DIR / f"shape_archetype_{archetype['archetype_tag']}_preview_v1.png",
            str(archetype["archetype_tag"]),
        )

    print("[DONE] shape archetype pilot generated")
    print(f"[OUT] {OUT_ANALYSIS_DIR}")
    print(f"[SHAPES] {len(catalog_rows)} generated")


if __name__ == "__main__":
    main()
