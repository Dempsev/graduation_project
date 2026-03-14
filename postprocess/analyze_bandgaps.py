from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

try:
    from .tbl1_post_utils import (
        build_band_table,
        list_tbl1_files,
        load_tbl1_data,
        model_name_from_path,
        project_root,
    )
except ImportError:
    from tbl1_post_utils import (
        build_band_table,
        list_tbl1_files,
        load_tbl1_data,
        model_name_from_path,
        project_root,
    )


@dataclass(frozen=True)
class Config:
    tbl1_dir: Path
    out_dir: Path
    export_band_tables: bool = True


def build_default_config() -> Config:
    root = project_root()
    return Config(
        tbl1_dir=root / "data" / "shape_batch" / "tbl1_exports",
        out_dir=root / "data" / "post_out",
        export_band_tables=True,
    )


def iter_gap_candidates(group: pd.DataFrame) -> Iterable[tuple[int, float, float, float]]:
    band_cols = [c for c in group.columns if c.startswith("band")]
    for idx in range(1, len(band_cols)):
        lower = group[f"band{idx}"].to_numpy(dtype=float)
        upper = group[f"band{idx + 1}"].to_numpy(dtype=float)
        if np.all(np.isnan(lower)) or np.all(np.isnan(upper)):
            continue
        lower_max = float(np.nanmax(lower))
        upper_min = float(np.nanmin(upper))
        yield idx, upper_min - lower_max, lower_max, upper_min


def compute_case_summary(
    model_name: str,
    param_name: str,
    param_value: float,
    group: pd.DataFrame,
) -> dict[str, object]:
    positive_gaps = [row for row in iter_gap_candidates(group) if row[1] > 0]
    if not positive_gaps:
        return {
            "model": model_name,
            "param_name": param_name,
            "param_value": param_value,
            "has_gap": False,
            "max_gap_Hz": 0.0,
            "gap_between_bands": "",
            "gap_lower_edge_Hz": np.nan,
            "gap_upper_edge_Hz": np.nan,
            "gap_center_Hz": np.nan,
            "relative_gap": np.nan,
        }

    band_idx, gap, lower_edge, upper_edge = max(positive_gaps, key=lambda row: row[1])
    center = 0.5 * (lower_edge + upper_edge)

    return {
        "model": model_name,
        "param_name": param_name,
        "param_value": param_value,
        "has_gap": True,
        "max_gap_Hz": gap,
        "gap_between_bands": f"{band_idx}-{band_idx + 1}",
        "gap_lower_edge_Hz": lower_edge,
        "gap_upper_edge_Hz": upper_edge,
        "gap_center_Hz": center,
        "relative_gap": gap / center if center != 0 else np.nan,
    }


def analyze_one_model(
    csv_path: Path,
    out_bands_dir: Path,
    export_band_tables: bool,
) -> list[dict[str, object]]:
    model_name = model_name_from_path(csv_path)
    df, param_name = load_tbl1_data(csv_path)
    if df.empty:
        return []

    bands = build_band_table(df, param_name)
    results: list[dict[str, object]] = []

    for param_value, group in bands.groupby(param_name):
        group = group.sort_values("k").reset_index(drop=True)
        results.append(compute_case_summary(model_name, param_name, float(param_value), group))

        if export_band_tables:
            case_name = f"{model_name}_{param_name}_{param_value:g}".replace(".", "p")
            group.to_csv(out_bands_dir / f"bands_{case_name}.csv", index=False)

    return results


def summarize_by_model(case_df: pd.DataFrame) -> pd.DataFrame:
    if case_df.empty:
        return case_df

    idx = case_df.groupby("model")["max_gap_Hz"].idxmax()
    return case_df.loc[idx].sort_values("max_gap_Hz", ascending=False).reset_index(drop=True)


def save_outputs(case_df: pd.DataFrame, model_df: pd.DataFrame, out_dir: Path) -> None:
    case_df.to_csv(out_dir / "bandgap_by_case.csv", index=False)
    model_df.to_csv(out_dir / "bandgap_by_model.csv", index=False)

    best_path = out_dir / "best_model.txt"
    if model_df.empty:
        best_path.write_text("No valid model with gap data.\n", encoding="utf-8")
        return

    best = model_df.iloc[0]
    pos_df = model_df[model_df["max_gap_Hz"] > 0]
    best_pos = pos_df.iloc[0] if not pos_df.empty else None
    best_text = (
        f"best_model={best['model']}\n"
        f"max_gap_Hz={best['max_gap_Hz']:.12g}\n"
        f"param_name={best['param_name']}\n"
        f"param_value={best['param_value']:.12g}\n"
        f"gap_between_bands={best['gap_between_bands']}\n"
    )
    if best_pos is None:
        best_text += "best_positive_model=\nbest_positive_gap_Hz=0\n"
    else:
        best_text += (
            f"best_positive_model={best_pos['model']}\n"
            f"best_positive_gap_Hz={best_pos['max_gap_Hz']:.12g}\n"
            f"best_positive_param_name={best_pos['param_name']}\n"
            f"best_positive_param_value={best_pos['param_value']:.12g}\n"
        )
    best_path.write_text(best_text, encoding="utf-8")


def run(config: Config) -> None:
    if not config.tbl1_dir.is_dir():
        raise FileNotFoundError(f"tbl1 directory not found: {config.tbl1_dir}")

    config.out_dir.mkdir(parents=True, exist_ok=True)
    out_bands_dir = config.out_dir / "bands_by_case"
    out_bands_dir.mkdir(parents=True, exist_ok=True)

    tbl1_files = list_tbl1_files(config.tbl1_dir)
    if not tbl1_files:
        raise FileNotFoundError(f"No *_tbl1.csv found in: {config.tbl1_dir}")

    all_rows: list[dict[str, object]] = []
    for csv_path in tbl1_files:
        all_rows.extend(analyze_one_model(csv_path, out_bands_dir, config.export_band_tables))

    case_df = pd.DataFrame(all_rows)
    if case_df.empty:
        raise RuntimeError("No valid numeric rows found in tbl1 csv files.")

    case_df = case_df.sort_values(["model", "param_name", "param_value"]).reset_index(drop=True)
    model_df = summarize_by_model(case_df)
    save_outputs(case_df, model_df, config.out_dir)

    best = model_df.iloc[0]
    pos_df = model_df[model_df["max_gap_Hz"] > 0]
    if pos_df.empty:
        pos_msg = "none"
    else:
        best_positive = pos_df.iloc[0]
        pos_msg = f"{best_positive['model']} ({best_positive['max_gap_Hz']:.6f} Hz)"

    print(f"[DONE] cases: {len(case_df)}, models: {len(model_df)}")
    print(
        "[BEST] "
        f"model={best['model']}, "
        f"max_gap_Hz={best['max_gap_Hz']:.6f}, "
        f"{best['param_name']}={best['param_value']:.6g}"
    )
    print(f"[BEST_POSITIVE] {pos_msg}")
    print(f"[OUT] {config.out_dir}")


if __name__ == "__main__":
    run(build_default_config())
