from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REPRESENTATIVES = (
    ROOT
    / "data"
    / "ml_runs"
    / "shape_archetype_targetband_pilot_v1"
    / "validation_manifest_v1"
    / "shape_archetype_targetband_pilot_representatives_v1.csv"
)
DEFAULT_SHAPE_DIR = ROOT / "data" / "shape_contours"
DEFAULT_OUT = (
    ROOT
    / "data"
    / "ml_runs"
    / "fourier_only_real_ga_v1"
    / "fourier_only_real_ga_shape_pool_v1.csv"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the Fourier-boundary-only shape pool for COMSOL-in-loop GA ablation."
    )
    parser.add_argument("--representatives", type=Path, default=DEFAULT_REPRESENTATIVES)
    parser.add_argument("--shape-dir", type=Path, default=DEFAULT_SHAPE_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def main() -> None:
    args = parse_args()
    representatives = resolve(args.representatives)
    shape_dir = resolve(args.shape_dir)
    out_path = resolve(args.out)

    if not representatives.exists():
        raise FileNotFoundError(representatives)
    if not shape_dir.exists():
        raise FileNotFoundError(shape_dir)

    df = pd.read_csv(representatives, encoding="utf-8-sig")
    required = ["shape_id", "gap_gain_Hz", "archetype_tag", "seed_family"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"{representatives} is missing required columns: {missing}")

    pool = df.copy()
    pool["gap_gain_Hz"] = pd.to_numeric(pool["gap_gain_Hz"], errors="coerce").fillna(0.0)
    pool["shape_file"] = pool["shape_id"].astype(str).map(lambda sid: shape_dir / f"{sid}.csv")
    missing_shapes = pool.loc[~pool["shape_file"].map(Path.exists), "shape_file"].astype(str).tolist()
    if missing_shapes:
        raise FileNotFoundError("Missing Fourier-only shape contour files:\n" + "\n".join(missing_shapes))

    out = (
        pool.sort_values(["gap_gain_Hz", "shape_id"], ascending=[False, True])
        .drop_duplicates("shape_id", keep="first")
        .loc[:, ["shape_id", "gap_gain_Hz", "archetype_tag", "seed_family"]]
        .rename(columns={"archetype_tag": "fourier_archetype_tag", "seed_family": "source_seed_family"})
    )
    out["candidate_tier"] = "strong_positive"
    out["geometry_valid"] = True
    out["contact_valid"] = True
    out["solve_success"] = True
    out["pool_source"] = "fourier_only_shape_archetype_pilot_v1"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False, encoding="utf-8")
    print(f"[DONE] wrote Fourier-only real-GA shape pool: {out_path}")
    print(f"[ROWS] {len(out)} unique Fourier-boundary shapes")
    print(out[["shape_id", "gap_gain_Hz", "fourier_archetype_tag"]].to_string(index=False))


if __name__ == "__main__":
    main()
