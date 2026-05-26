from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matlab.engine


ROOT = Path(__file__).resolve().parents[2]
BASE_DIR = ROOT / "research_validation" / "ch5_fourier_only_ablation"
FIG_DIR = BASE_DIR / "figures"
GEOM_DIR = FIG_DIR / "geometry_exports"
CASE_CSV = BASE_DIR / "fourier_only_ablation_geometry_cases.csv"
MANIFEST_CSV = BASE_DIR / "fourier_only_ablation_geometry_export_manifest.csv"

BANDS = [
    ("band200_240", "200-240 Hz"),
    ("band220_260", "220-260 Hz"),
    ("band240_280", "240-280 Hz"),
]
METHODS = [
    (
        "fourier_only_ga20",
        "仅傅里叶边界 GA20",
        "comsol_in_loop_fourier_pure_boundary_{tag}_ga_v1",
    ),
    (
        "combined_ga20",
        "当前模型 GA20",
        "comsol_in_loop_thesis_{tag}_overlap_ga_v1",
    ),
]
EXPORTER_DIR = BASE_DIR


def read_history(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def numeric(row: dict[str, str], field: str, fallback: float = 0.0) -> float:
    value = row.get(field, "")
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def best_row(rows: list[dict[str, str]]) -> dict[str, str]:
    return max(
        rows,
        key=lambda row: (
            numeric(row, "active_target_overlap_Hz", float("-inf")),
            numeric(row, "generation", -1),
            numeric(row, "individual_index", -1),
        ),
    )


def build_cases() -> Path:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    for band_tag, band_label in BANDS:
        for method, method_label, dir_template in METHODS:
            history_path = (
                ROOT
                / "data"
                / "comsol_batch"
                / dir_template.format(tag=band_tag)
                / "ga_history_v1.csv"
            )
            row = best_row(read_history(history_path))
            rows.append(
                {
                    "target_band": band_label,
                    "target_band_tag": band_tag,
                    "method": method,
                    "method_label": method_label,
                    "sample_id": row["sample_id"],
                    "candidate_id": row["candidate_id"],
                    "shape_id": row["shape_id"],
                    "shape_family": row.get("shape_family", ""),
                    "main_id": row["main_id"],
                    "point_id": row["point_id"],
                    "a1": row["a1"],
                    "a2": row["a2"],
                    "b1": row.get("b1", "0"),
                    "b2": row["b2"],
                    "r0": row["r0"],
                    "a3": row["a3"],
                    "b3": row["b3"],
                    "a4": row["a4"],
                    "b4": row["b4"],
                    "a5": row["a5"],
                    "b5": row["b5"],
                    "generation": row.get("generation", ""),
                    "individual_index": row.get("individual_index", ""),
                    "shape_file": row.get("shape_file", ""),
                    "overlap_Hz": row.get("active_target_overlap_Hz", ""),
                    "cover_ratio": row.get("active_target_cover_ratio", ""),
                }
            )

    fieldnames = list(rows[0].keys())
    with CASE_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[CASES] {CASE_CSV}")
    return CASE_CSV


def connect_or_start(session_name: str):
    sessions = set(matlab.engine.find_matlab())
    if session_name in sessions:
        return matlab.engine.connect_matlab(session_name)
    return matlab.engine.start_matlab()


def run_matlab_export(case_csv: Path, session_name: str) -> Path:
    eng = connect_or_start(session_name)
    eng.cd(str(ROOT), nargout=0)
    eng.addpath(str(EXPORTER_DIR), nargout=0)
    escaped = str(case_csv).replace("'", "''")
    manifest = Path(
        str(
            eng.eval(
                f"export_fourier_only_ablation_unit_cells_v1('{escaped}')",
                nargout=1,
            )
        )
    )
    print(f"[MANIFEST] {manifest}")
    return manifest


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_readme() -> Path:
    rows = read_manifest(MANIFEST_CSV)
    readme = BASE_DIR / "FOURIER_ONLY_ABLATION_GEOMETRY_EXPORT_README_CN.md"
    montage_png = FIG_DIR / "ch5_fourier_only_ablation_final_geometry_compare.png"
    montage_svg = FIG_DIR / "ch5_fourier_only_ablation_final_geometry_compare.svg"
    montage_pdf = FIG_DIR / "ch5_fourier_only_ablation_final_geometry_compare.pdf"
    lines = [
        "# Fourier-only 对比实验最终优化几何模型图",
        "",
        "本目录记录 3 个高频目标频段中，Fourier-only GA20 与当前组合模型 GA20 的最终最佳个体几何导出结果。",
        "导出过程只重建 COMSOL 几何模型，不重新运行频散求解。",
        "",
        f"- 对比拼图 PNG：`{montage_png.relative_to(BASE_DIR)}`",
        f"- 对比拼图 SVG：`{montage_svg.relative_to(BASE_DIR)}`",
        f"- 对比拼图 PDF：`{montage_pdf.relative_to(BASE_DIR)}`",
        f"- 单图目录：`{GEOM_DIR.relative_to(BASE_DIR)}`",
        f"- 导出清单：`{MANIFEST_CSV.name}`",
        f"- 个体清单：`{CASE_CSV.name}`",
        "",
        "| 目标频段 | 方法 | overlap_Hz | shape_id | generation | PNG | SVG | PDF |",
        "| --- | --- | ---: | --- | ---: | --- | --- | --- |",
    ]
    for band_tag, _ in BANDS:
        for method, _, _ in METHODS:
            row = next(item for item in rows if item["target_band_tag"] == band_tag and item["method"] == method)
            lines.append(
                "| "
                f"{row['target_band']} | "
                f"{row['method_label']} | "
                f"{float(row['overlap_Hz']):.3f} | "
                f"`{row['shape_id']}` | "
                f"{float(row['generation']):.0f} | "
                f"`{Path(row['png_path']).name}` | "
                f"`{Path(row['svg_path']).name}` | "
                f"`{Path(row['pdf_path']).name}` |"
            )
    readme.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[README] {readme}")
    return readme


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", default="comsol_matlab")
    parser.add_argument("--skip-comsol", action="store_true")
    args = parser.parse_args()

    case_csv = build_cases()
    manifest = MANIFEST_CSV if args.skip_comsol else run_matlab_export(case_csv, args.session)
    write_readme()
    for ext in ["png", "svg", "pdf"]:
        print(f"[{ext.upper()}] {FIG_DIR / ('ch5_fourier_only_ablation_final_geometry_compare.' + ext)}")


if __name__ == "__main__":
    main()
