from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def list_tbl1_files(tbl1_dir: Path) -> list[Path]:
    return sorted(tbl1_dir.glob("*_tbl1.csv"))


def parse_real_value(x: object) -> float:
    if pd.isna(x):
        return np.nan

    s = str(x).strip().replace("i", "j")
    try:
        return float(np.real(complex(s)))
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return np.nan


def detect_param_name(csv_path: Path) -> str:
    try:
        with csv_path.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line.startswith("%"):
                    continue
                raw = line.lstrip("%").strip()
                fields = [part.strip() for part in raw.split(",")]
                if len(fields) >= 2 and fields[0].lower() == "k" and fields[1]:
                    return fields[1]
    except OSError:
        pass

    return "param"


def model_name_from_path(csv_path: Path) -> str:
    stem = csv_path.stem
    return stem[:-5] if stem.endswith("_tbl1") else stem


def load_tbl1_data(csv_path: Path, param_name: str | None = None) -> tuple[pd.DataFrame, str]:
    resolved_param_name = param_name or detect_param_name(csv_path)
    df = pd.read_csv(
        csv_path,
        header=None,
        comment="%",
        sep=r"\s*,\s*|\s+",
        engine="python",
        names=["k", resolved_param_name, "eigfreq", "freq"],
    )

    df["k"] = pd.to_numeric(df["k"], errors="coerce")
    df[resolved_param_name] = pd.to_numeric(df[resolved_param_name], errors="coerce")
    df["freq_real"] = df["freq"].apply(parse_real_value)

    df = df.dropna(subset=["k", resolved_param_name, "freq_real"]).copy()
    if df.empty:
        return df, resolved_param_name

    df = df.sort_values([resolved_param_name, "k", "freq_real"]).copy()
    df["band_index"] = df.groupby([resolved_param_name, "k"]).cumcount() + 1
    return df, resolved_param_name


def build_band_table(df: pd.DataFrame, param_name: str) -> pd.DataFrame:
    bands = (
        df.pivot_table(
            index=[param_name, "k"],
            columns="band_index",
            values="freq_real",
            aggfunc="min",
        )
        .reset_index()
        .sort_values([param_name, "k"])
    )
    bands.columns = [param_name, "k"] + [f"band{int(c)}" for c in bands.columns[2:]]
    return bands


def infer_manual_plot_dir(csv_path: Path) -> Path:
    root = project_root()
    default_out_dir = root / "data" / "postprocess_out" / "manual_band_diagrams"

    if len(csv_path.parents) >= 3 and csv_path.parents[2].name == "data":
        return csv_path.parents[2] / "postprocess_out" / "manual_band_diagrams"

    return default_out_dir
