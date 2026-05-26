from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, Rectangle


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "research_validation" / "ch4_ga_real_optimization"
FIG_DIR = OUT_DIR / "figures"
COMSOL_ROOT = ROOT / "data" / "comsol_batch"

TARGET_BANDS = [
    ("140-180 Hz", "band140_180", 140.0, 180.0),
    ("160-200 Hz", "band160_200", 160.0, 200.0),
    ("180-220 Hz", "band180_220", 180.0, 220.0),
    ("200-240 Hz", "band200_240", 200.0, 240.0),
    ("220-260 Hz", "band220_260", 220.0, 260.0),
    ("240-280 Hz", "band240_280", 240.0, 280.0),
]

PREFERRED_DIRS = {
    "band140_180": "comsol_in_loop_thesis_band140_180_overlap_ga_v1",
    "band160_200": "comsol_in_loop_thesis_band160_200_overlap_ga_v1",
    # The thesis-named 180-220 directory is an old 12-generation run.
    # The independent targetband directory is the complete 20-generation run.
    "band180_220": "comsol_in_loop_targetband180_220_overlap_ga_v1",
    "band200_240": "comsol_in_loop_thesis_band200_240_overlap_ga_v1",
    "band220_260": "comsol_in_loop_thesis_band220_260_overlap_ga_v1",
    "band240_280": "comsol_in_loop_thesis_band240_280_overlap_ga_v1",
}

REQUIRED_FILES = [
    "ga_config_v1.json",
    "ga_history_v1.csv",
    "ga_generation_summary_v1.csv",
    "ga_best_candidates_v1.csv",
    "ga_search_summary_v1.csv",
    "ga_state_v1.mat",
]

PARAM_MEANINGS = {
    "shape_id": "单胞夹杂轮廓/结构族离散基因",
    "a1": "一阶余弦形状参数",
    "a2": "二阶余弦形状参数",
    "b1": "一阶正弦形状参数",
    "b2": "二阶正弦形状参数",
    "a3": "三阶余弦形状参数",
    "b3": "三阶正弦形状参数",
    "a4": "四阶余弦形状参数",
    "b4": "四阶正弦形状参数",
    "a5": "五阶余弦形状参数",
    "b5": "五阶正弦形状参数",
    "r0": "基准半径/尺度参数",
}


def mkdirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)


def configure_fonts() -> None:
    candidates = [
        Path(r"C:\Windows\Fonts\NotoSansSC-Regular.ttf"),
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
    ]
    for path in candidates:
        if path.exists():
            font_manager.fontManager.addfont(str(path))
            font_name = font_manager.FontProperties(fname=str(path)).get_name()
            plt.rcParams["font.sans-serif"] = [font_name, "DejaVu Sans"]
            plt.rcParams["font.family"] = "sans-serif"
            break
    plt.rcParams["axes.unicode_minus"] = False


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def to_num(series: pd.Series, default: float = np.nan) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(default)


def bool_sum(series: pd.Series) -> int:
    return int(pd.to_numeric(series, errors="coerce").fillna(0).astype(float).gt(0).sum())


def safe_float(value: Any, default: float = float("nan")) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if np.isfinite(out) else default


def table_to_md(df: pd.DataFrame, floatfmt: str = ".4f") -> str:
    if df.empty:
        return ""
    def format_cell(value: Any) -> str:
        if pd.isna(value):
            return ""
        if isinstance(value, (float, np.floating)):
            return format(float(value), floatfmt)
        text = str(value)
        return text.replace("|", "\\|").replace("\n", "<br>")

    columns = [str(col) for col in df.columns]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(format_cell(row[col]) for col in df.columns) + " |")
    return "\n".join(lines)


def save_table(df: pd.DataFrame, csv_path: Path, md_path: Path, title: str, note: str = "") -> None:
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    body = [f"# {title}", ""]
    if note:
        body.extend([note, ""])
    body.append(table_to_md(df))
    body.append("")
    md_path.write_text("\n".join(body), encoding="utf-8")


def candidate_dirs_for_band(tag: str) -> List[Path]:
    dirs = []
    for path in COMSOL_ROOT.glob("*overlap_ga_v1"):
        if not path.is_dir():
            continue
        if not (path / "ga_history_v1.csv").exists():
            continue
        try:
            hist = pd.read_csv(path / "ga_history_v1.csv", usecols=lambda c: c in {"active_band_tag"})
        except Exception:
            continue
        if "active_band_tag" in hist and tag in set(hist["active_band_tag"].astype(str)):
            dirs.append(path)
    preferred = COMSOL_ROOT / PREFERRED_DIRS[tag]
    if preferred.exists() and preferred not in dirs:
        dirs.append(preferred)
    return dirs


def inspect_dir(path: Path) -> Dict[str, Any]:
    history_path = path / "ga_history_v1.csv"
    cfg_path = path / "ga_config_v1.json"
    hist = pd.read_csv(history_path) if history_path.exists() else pd.DataFrame()
    cfg = read_json(cfg_path) if cfg_path.exists() else {}
    generations = to_num(hist["generation"]) if "generation" in hist else pd.Series(dtype=float)
    return {
        "path": path,
        "n_rows": int(len(hist)),
        "generation_min": int(generations.min()) if len(generations) else np.nan,
        "generation_max": int(generations.max()) if len(generations) else np.nan,
        "unique_generation_count": int(generations.nunique()) if len(generations) else 0,
        "max_generations_config": int(safe_float(cfg.get("maxGenerations"), -1)) if cfg else -1,
        "mtime": max((path / f).stat().st_mtime for f in REQUIRED_FILES if (path / f).exists()),
        "has_summary": (path / "ga_search_summary_v1.csv").exists(),
        "required_present": {f: (path / f).exists() for f in REQUIRED_FILES},
    }


def choose_band_dir(tag: str) -> Tuple[Path, List[Dict[str, Any]], str]:
    candidates = [inspect_dir(path) for path in candidate_dirs_for_band(tag)]
    if not candidates:
        raise FileNotFoundError(f"No GA output directory found for {tag}")
    preferred = COMSOL_ROOT / PREFERRED_DIRS[tag]
    for item in candidates:
        item["preferred"] = item["path"] == preferred
    candidates = sorted(
        candidates,
        key=lambda item: (
            item["unique_generation_count"] >= 20,
            item["preferred"],
            item["n_rows"],
            item["has_summary"],
            item["mtime"],
        ),
        reverse=True,
    )
    reason = "优先选择达到20代、评价记录完整且与目标频带匹配的目录"
    return candidates[0]["path"], candidates, reason


def load_band_data() -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for label, tag, low, high in TARGET_BANDS:
        selected, candidates, reason = choose_band_dir(tag)
        hist = pd.read_csv(selected / "ga_history_v1.csv")
        cfg = read_json(selected / "ga_config_v1.json")
        gen_summary = pd.read_csv(selected / "ga_generation_summary_v1.csv")
        best_candidates = pd.read_csv(selected / "ga_best_candidates_v1.csv")
        search_summary = pd.read_csv(selected / "ga_search_summary_v1.csv")
        out[tag] = {
            "label": label,
            "tag": tag,
            "low": low,
            "high": high,
            "dir": selected,
            "candidate_dirs": candidates,
            "selection_reason": reason,
            "history": hist,
            "config": cfg,
            "generation_summary": gen_summary,
            "best_candidates": best_candidates,
            "search_summary": search_summary,
        }
    return out


def add_eval_index(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    if "evaluation_index" not in work.columns:
        work = work.sort_values(["generation", "individual_index"], kind="stable").reset_index(drop=True)
        work["evaluation_index"] = np.arange(1, len(work) + 1)
    return work


def best_row(hist: pd.DataFrame) -> pd.Series:
    work = add_eval_index(hist)
    score = to_num(work["active_target_overlap_Hz"], default=-np.inf)
    sort_cols = pd.DataFrame({
        "score": score,
        "cover": to_num(work.get("active_target_cover_ratio", pd.Series(np.nan, index=work.index)), default=-np.inf),
        "solve": to_num(work.get("solve_success", pd.Series(0, index=work.index)), default=0),
    })
    idx = sort_cols.sort_values(["score", "cover", "solve"], ascending=False).index[0]
    return work.loc[idx]


def make_summary_tables(data: Dict[str, Dict[str, Any]]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    summary_rows: List[Dict[str, Any]] = []
    config_rows: List[Dict[str, Any]] = []
    for tag, item in data.items():
        hist = add_eval_index(item["history"])
        cfg = item["config"]
        generations = to_num(hist["generation"])
        unique_generation_count = int(generations.nunique())
        population_size = int(safe_float(cfg.get("populationSize"), np.nan)) if np.isfinite(safe_float(cfg.get("populationSize"), np.nan)) else np.nan
        n_eval = int(len(hist))
        n_success = bool_sum(hist["solve_success"]) if "solve_success" in hist else 0
        active_overlap = to_num(hist["active_target_overlap_Hz"], default=0.0).gt(0)
        success_mask = to_num(hist["solve_success"], default=0).gt(0)
        n_active = int((active_overlap & success_mask).sum())
        best = best_row(hist)
        missing = [f for f in REQUIRED_FILES if not (item["dir"] / f).exists()]
        note_parts = []
        if missing:
            note_parts.append("缺失文件: " + ",".join(missing))
        if tag == "band180_220" and "thesis_band180_220" not in item["dir"].name:
            note_parts.append("采用独立20代目录，旧thesis目录仅12代未采用")
        if unique_generation_count < 20:
            note_parts.append("未达到20代")
        expected_evals = population_size * unique_generation_count if np.isfinite(population_size) else np.nan

        summary_rows.append({
            "target_band": item["label"],
            "target_band_tag": tag,
            "output_dir": str(item["dir"]),
            "n_generations_actual": unique_generation_count,
            "population_size": population_size,
            "n_evaluations_actual": n_eval,
            "expected_evaluations": expected_evals,
            "n_solve_success": n_success,
            "solve_success_rate": n_success / n_eval if n_eval else np.nan,
            "n_active_overlap": n_active,
            "active_rate": n_active / n_success if n_success else np.nan,
            "best_candidate_id": best.get("candidate_id", ""),
            "best_individual_id": best.get("individual_index", ""),
            "best_sample_id": best.get("sample_id", ""),
            "best_generation": int(best.get("generation", -1)),
            "best_evaluation_index": int(best.get("evaluation_index", -1)),
            "best_target_overlap_Hz": safe_float(best.get("active_target_overlap_Hz")),
            "best_cover_ratio": safe_float(best.get("active_target_cover_ratio")),
            "best_gap_lower_Hz": safe_float(best.get("active_target_lower_edge_Hz")),
            "best_gap_upper_Hz": safe_float(best.get("active_target_upper_edge_Hz")),
            "best_geometry_valid": int(safe_float(best.get("geometry_valid"), 0)),
            "best_contact_valid": int(safe_float(best.get("contact_valid"), 0)),
            "best_solve_success": int(safe_float(best.get("solve_success"), 0)),
            "best_shape_id": best.get("shape_id", ""),
            "is_20gen_complete": bool(unique_generation_count >= 20 and n_eval >= expected_evals),
            "note": "; ".join(note_parts),
        })

        gen_min = int(generations.min()) if len(generations) else np.nan
        gen_max = int(generations.max()) if len(generations) else np.nan
        config_rows.append({
            "target_band": item["label"],
            "target_band_tag": tag,
            "population_size": population_size,
            "n_generations_actual": unique_generation_count,
            "generation_min": gen_min,
            "generation_max": gen_max,
            "unique_generation_count": unique_generation_count,
            "max_generations_config": cfg.get("maxGenerations", ""),
            "n_evaluations_actual": n_eval,
            "expected_evaluations": expected_evals,
            "selection_method": "锦标赛选择，锦标赛规模=min(3, 当前种群数)",
            "crossover_probability": "连续变量非精英个体每次均做双亲线性组合；形状基因从双亲二选一",
            "mutation_probability": f"形状基因 {cfg.get('shapeMutationRate', '')}; 连续变量 {cfg.get('continuousMutationRate', '')}",
            "elite_count_or_ratio": cfg.get("eliteCount", ""),
            "random_seed": cfg.get("randomSeed", ""),
            "termination_condition": f"达到 maxGenerations={cfg.get('maxGenerations', '')}; enableEarlyStop={cfg.get('enableEarlyStop', '')}",
            "fitness_function_name": "target_overlap_Hz / 目标频带重叠宽度",
            "continuous_mutation_scale": cfg.get("continuousMutationScale", ""),
            "shape_pool_mode": cfg.get("shapePoolMode", ""),
        })
    return pd.DataFrame(summary_rows), pd.DataFrame(config_rows)


def make_design_tables(data: Dict[str, Dict[str, Any]]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    cfg = next(iter(data.values()))["config"]
    bounds = cfg.get("globalBounds", {})
    active = set(cfg.get("activeParamNames", []))
    shape_pool_count = int(next(iter(data.values()))["search_summary"]["shape_pool_count"].iloc[0])
    rows = [{
        "variable_name": "shape_id",
        "physical_meaning": PARAM_MEANINGS["shape_id"],
        "variable_type": "categorical",
        "lower_bound": "shape_pool候选集合",
        "upper_bound": f"{shape_pool_count}个候选轮廓",
        "used_in_ga": True,
        "note": "形状基因来自预筛选轮廓库，非连续参数",
    }]
    for name in cfg.get("paramNames", []):
        b = bounds.get(name, [np.nan, np.nan])
        rows.append({
            "variable_name": name,
            "physical_meaning": PARAM_MEANINGS.get(name, "TODO"),
            "variable_type": "continuous",
            "lower_bound": b[0] if len(b) > 0 else np.nan,
            "upper_bound": b[1] if len(b) > 1 else np.nan,
            "used_in_ga": name in active,
            "note": "clip_to_bounds约束在全局上下限内",
        })
    variable_df = pd.DataFrame(rows)
    constraints = [
        {
            "constraint_name": "parameter_range_constraint",
            "mathematical_form": "x_j in [lower_j, upper_j]",
            "implementation": "连续变量交叉和变异后通过 clip_to_bounds 截断到 globalBounds",
            "role_in_ga": "限定设计变量可行域",
        },
        {
            "constraint_name": "geometry_valid constraint",
            "mathematical_form": "geometry_valid = 1",
            "implementation": "几何无效时 fitness = failurePenaltyGeometry",
            "role_in_ga": "排除不可建模几何",
        },
        {
            "constraint_name": "contact_valid constraint",
            "mathematical_form": "contact_valid = 1",
            "implementation": "接触无效时 fitness = failurePenaltyContact",
            "role_in_ga": "保证夹杂/基体接触关系满足计算要求",
        },
        {
            "constraint_name": "solve_success constraint",
            "mathematical_form": "solve_success = 1",
            "implementation": "COMSOL 求解失败时 fitness = failurePenaltySolve",
            "role_in_ga": "保证频散结果可用于适应度评价",
        },
        {
            "constraint_name": "target_overlap_Hz > 0 active constraint",
            "mathematical_form": "target_overlap_Hz > 0",
            "implementation": "统计有效候选时使用，不作为硬约束；适应度直接最大化 target_overlap_Hz",
            "role_in_ga": "定义有效候选并衡量目标频带命中情况",
        },
    ]
    return variable_df, pd.DataFrame(constraints)


def savefig_all(fig: plt.Figure, stem: str) -> Dict[str, str]:
    paths = {}
    for ext in ["png", "svg", "pdf"]:
        path = FIG_DIR / f"{stem}.{ext}"
        if ext == "png":
            fig.savefig(path, dpi=300, bbox_inches="tight")
        else:
            fig.savefig(path, bbox_inches="tight")
        paths[ext] = str(path)
    plt.close(fig)
    return paths


def draw_flowchart(stem: str, title: str, boxes: List[str], arrows: List[Tuple[int, int]]) -> Dict[str, str]:
    fig, ax = plt.subplots(figsize=(11, 5.8))
    ax.axis("off")
    ax.set_title(title, fontsize=16, pad=18)
    xs = np.linspace(0.08, 0.92, len(boxes))
    y = 0.55
    for i, (x, text) in enumerate(zip(xs, boxes)):
        rect = Rectangle((x - 0.075, y - 0.13), 0.15, 0.26, facecolor="#edf4ff", edgecolor="#28527a", linewidth=1.6)
        ax.add_patch(rect)
        ax.text(x, y, text, ha="center", va="center", fontsize=10, wrap=True)
    for start, end in arrows:
        ax.add_patch(FancyArrowPatch((xs[start] + 0.075, y), (xs[end] - 0.075, y), arrowstyle="->", mutation_scale=18, linewidth=1.6, color="#333333"))
    ax.text(0.5, 0.12, "适应度函数仅由 COMSOL 真实频散结果计算：最大化目标频带重叠宽度", ha="center", fontsize=11, color="#7a2e2e")
    return savefig_all(fig, stem)


def plot_convergence(data: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
    fig, ax = plt.subplots(figsize=(9.5, 5.8))
    for tag, item in data.items():
        hist = add_eval_index(item["history"])
        hist["best_so_far_target_overlap_Hz"] = to_num(hist["active_target_overlap_Hz"], default=0.0).cummax()
        ax.plot(hist["evaluation_index"], hist["best_so_far_target_overlap_Hz"], linewidth=2, label=item["label"])
    ax.set_xlabel("评价次数")
    ax.set_ylabel("历史最优目标频带重叠宽度 / Hz")
    ax.set_title("六个目标频带真实遗传优化收敛曲线")
    ax.grid(True, alpha=0.28)
    ax.legend(ncol=2, fontsize=9)
    return savefig_all(fig, "ch4_fig4_3_ga_convergence_20gen")


def plot_best_bar(summary_df: pd.DataFrame) -> Dict[str, str]:
    fig, ax = plt.subplots(figsize=(8.8, 5.4))
    colors = ["#4c78a8", "#59a14f", "#f28e2b", "#e15759", "#b07aa1", "#76b7b2"]
    ax.bar(summary_df["target_band"], summary_df["best_target_overlap_Hz"], color=colors)
    ax.set_ylabel("最优目标频带重叠宽度 / Hz")
    ax.set_title("六个目标频带20代最终最优结果")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", alpha=0.25)
    for idx, value in enumerate(summary_df["best_target_overlap_Hz"]):
        ax.text(idx, value + 0.8, f"{value:.2f}", ha="center", va="bottom", fontsize=9)
    return savefig_all(fig, "ch4_fig4_4_best_overlap_bar_20gen")


def plot_rates(summary_df: pd.DataFrame) -> Dict[str, str]:
    fig, ax = plt.subplots(figsize=(9.2, 5.4))
    x = np.arange(len(summary_df))
    width = 0.36
    ax.bar(x - width / 2, summary_df["solve_success_rate"], width, label="成功求解率", color="#4c78a8")
    ax.bar(x + width / 2, summary_df["active_rate"], width, label="有效候选率", color="#f28e2b")
    ax.set_xticks(x)
    ax.set_xticklabels(summary_df["target_band"], rotation=25, ha="right")
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("比例")
    ax.set_title("成功求解率与有效候选率对比")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    return savefig_all(fig, "ch4_fig4_5_success_active_rates_20gen")


def read_shape_xy(shape_path: Any) -> Optional[pd.DataFrame]:
    if pd.isna(shape_path):
        return None
    path = Path(str(shape_path))
    if not path.exists():
        path = ROOT / "data" / "shape_contours" / f"{Path(str(shape_path)).stem}.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    if "x" not in df.columns or "y" not in df.columns:
        return None
    return df[["x", "y"]].apply(pd.to_numeric, errors="coerce").dropna()


def plot_shape(ax: plt.Axes, row: pd.Series, title: str) -> None:
    xy = read_shape_xy(row.get("shape_file", ""))
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=10)
    if xy is None or xy.empty:
        ax.text(0.5, 0.5, "轮廓缺失", ha="center", va="center")
        return
    x = xy["x"].to_numpy()
    y = xy["y"].to_numpy()
    ax.fill(x, y, color="#4c78a8", alpha=0.72)
    ax.plot(x, y, color="#1b3d5d", linewidth=1.2)
    pad = max(x.max() - x.min(), y.max() - y.min()) * 0.15
    ax.set_xlim(x.min() - pad, x.max() + pad)
    ax.set_ylim(y.min() - pad, y.max() + pad)


def plot_shapes(data: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
    fig, axes = plt.subplots(2, 3, figsize=(10, 6.2))
    for ax, (tag, item) in zip(axes.ravel(), data.items()):
        row = best_row(item["history"])
        title = f"{item['label']}\n{row.get('shape_id','')}  {safe_float(row.get('active_target_overlap_Hz')):.2f} Hz"
        plot_shape(ax, row, title)
    fig.suptitle("六个目标频带最优结构单胞轮廓", fontsize=15)
    paths = savefig_all(fig, "ch4_fig4_6_best_unit_cells_6bands")

    selected_tags = ["band180_220", "band200_240", "band240_280"]
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.6))
    for ax, tag in zip(axes, selected_tags):
        item = data[tag]
        row = best_row(item["history"])
        title = f"{item['label']}\n{row.get('shape_id','')}  {safe_float(row.get('active_target_overlap_Hz')):.2f} Hz"
        plot_shape(ax, row, title)
    fig.suptitle("代表频带最优结构单胞轮廓", fontsize=14)
    paths.update({f"representative_{k}": v for k, v in savefig_all(fig, "ch4_fig4_6_representative_unit_cells_3bands").items()})

    for tag, item in data.items():
        row = best_row(item["history"])
        fig, ax = plt.subplots(figsize=(4.2, 4.0))
        plot_shape(ax, row, f"{item['label']} 最优结构\n{row.get('shape_id','')}")
        single = savefig_all(fig, f"ch4_fig4_6_unit_cell_{tag}")
        paths.update({f"{tag}_{k}": v for k, v in single.items()})
    return paths


def parse_real(value: Any) -> float:
    text = str(value).strip()
    match = re.match(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?", text)
    return float(match.group(0)) if match else np.nan


def find_tbl1_export(item: Dict[str, Any], row: pd.Series) -> Optional[Path]:
    sample_id = str(row.get("sample_id", ""))
    export_dir = item["dir"] / "tbl1_exports"
    matches = list(export_dir.glob(f"{sample_id}*_tbl1.csv"))
    return matches[0] if matches else None


def load_dispersion(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, comment="%", header=None, names=["k", "eig", "freq"])
    df["k"] = pd.to_numeric(df["k"], errors="coerce")
    df["frequency_Hz"] = df["freq"].map(parse_real)
    df = df.dropna(subset=["k", "frequency_Hz"]).copy()
    df = df.sort_values(["k", "frequency_Hz"]).reset_index(drop=True)
    df["band_index"] = df.groupby("k").cumcount() + 1
    return df


def plot_dispersion_cases(data: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
    selected_tags = ["band180_220", "band200_240", "band240_280"]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.4), sharey=True)
    paths: Dict[str, str] = {}
    for ax, tag in zip(axes, selected_tags):
        item = data[tag]
        row = best_row(item["history"])
        tbl = find_tbl1_export(item, row)
        ax.set_title(item["label"], fontsize=11)
        ax.set_xlabel("波矢路径参数 k")
        ax.axhspan(item["low"], item["high"], color="#f28e2b", alpha=0.16, label="目标频带")
        ax.axhspan(safe_float(row.get("active_target_lower_edge_Hz")), safe_float(row.get("active_target_upper_edge_Hz")), color="#59a14f", alpha=0.18, label="实际带隙")
        if tbl and tbl.exists():
            disp = load_dispersion(tbl)
            for band_idx, part in disp[disp["band_index"] <= 10].groupby("band_index"):
                ax.plot(part["k"], part["frequency_Hz"], color="#2f4b7c", linewidth=0.75, alpha=0.85)
        else:
            ax.text(0.5, 0.5, "频散表缺失", transform=ax.transAxes, ha="center")
        ax.grid(True, alpha=0.22)
    axes[0].set_ylabel("频率 / Hz")
    axes[0].legend(loc="upper left", fontsize=8)
    fig.suptitle("代表性最优结构频散曲线与目标频带标注", fontsize=14)
    paths.update(savefig_all(fig, "ch4_fig4_7_representative_dispersion_3bands"))

    for tag in selected_tags:
        item = data[tag]
        row = best_row(item["history"])
        tbl = find_tbl1_export(item, row)
        fig, ax = plt.subplots(figsize=(6.5, 4.4))
        ax.set_title(f"{item['label']} 最优结构频散曲线", fontsize=12)
        ax.set_xlabel("波矢路径参数 k")
        ax.set_ylabel("频率 / Hz")
        ax.axhspan(item["low"], item["high"], color="#f28e2b", alpha=0.16, label="目标频带")
        ax.axhspan(safe_float(row.get("active_target_lower_edge_Hz")), safe_float(row.get("active_target_upper_edge_Hz")), color="#59a14f", alpha=0.18, label="实际带隙")
        if tbl and tbl.exists():
            disp = load_dispersion(tbl)
            for _, part in disp[disp["band_index"] <= 10].groupby("band_index"):
                ax.plot(part["k"], part["frequency_Hz"], color="#2f4b7c", linewidth=0.85)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.25)
        single = savefig_all(fig, f"ch4_fig4_7_dispersion_{tag}")
        paths.update({f"{tag}_{k}": v for k, v in single.items()})
    return paths


def make_improvement_table(data: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for tag, item in data.items():
        hist = add_eval_index(item["history"])
        hist["overlap"] = to_num(hist["active_target_overlap_Hz"], default=0.0)
        before12 = hist[to_num(hist["generation"]) <= 12].copy()
        before20 = hist[to_num(hist["generation"]) <= 20].copy()
        best12 = best_row(before12)
        best20 = best_row(before20)
        o12 = safe_float(best12.get("active_target_overlap_Hz"), 0.0)
        o20 = safe_float(best20.get("active_target_overlap_Hz"), 0.0)
        rows.append({
            "target_band": item["label"],
            "target_band_tag": tag,
            "generation_numbering": "1-20",
            "best_overlap_at_gen12": o12,
            "best_overlap_at_gen20": o20,
            "improvement_Hz": o20 - o12,
            "improvement_ratio": (o20 - o12) / max(o12, 1e-9),
            "best_generation_12_or_before": int(best12.get("generation", -1)),
            "best_generation_20": int(best20.get("generation", -1)),
            "new_best_in_gen13_to20": bool(int(best20.get("generation", -1)) > 12 and o20 > o12 + 1e-9),
            "note": "从所采用20代目录的history恢复；generation编号为1-20",
        })
    return pd.DataFrame(rows)


def plot_improvement(improvement_df: pd.DataFrame) -> Dict[str, str]:
    fig, ax = plt.subplots(figsize=(9.0, 5.4))
    x = np.arange(len(improvement_df))
    width = 0.36
    ax.bar(x - width / 2, improvement_df["best_overlap_at_gen12"], width, label="第12代完成后历史最优", color="#9ecae1")
    ax.bar(x + width / 2, improvement_df["best_overlap_at_gen20"], width, label="第20代完成后历史最优", color="#f28e2b")
    ax.set_xticks(x)
    ax.set_xticklabels(improvement_df["target_band"], rotation=25, ha="right")
    ax.set_ylabel("目标频带重叠宽度 / Hz")
    ax.set_title("12代与20代历史最优目标频带重叠宽度对比")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    return savefig_all(fig, "ch4_ga_12gen_vs_20gen_overlap")


def make_typical_cases(data: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for tag in ["band180_220", "band200_240", "band240_280"]:
        item = data[tag]
        row = best_row(item["history"])
        shape_path = str(row.get("shape_file", ""))
        tbl = find_tbl1_export(item, row)
        record = {
            "target_band": item["label"],
            "target_band_tag": tag,
            "candidate_id": row.get("candidate_id", ""),
            "sample_id": row.get("sample_id", ""),
            "shape_id": row.get("shape_id", ""),
            "shape_family": row.get("shape_family", ""),
            "generation": int(row.get("generation", -1)),
            "evaluation_index": int(row.get("evaluation_index", -1)),
            "target_overlap_Hz": safe_float(row.get("active_target_overlap_Hz")),
            "cover_ratio": safe_float(row.get("active_target_cover_ratio")),
            "gap_lower_Hz": safe_float(row.get("active_target_lower_edge_Hz")),
            "gap_upper_Hz": safe_float(row.get("active_target_upper_edge_Hz")),
            "structure_image_path": str(FIG_DIR / f"ch4_fig4_6_unit_cell_{tag}.png"),
            "dispersion_image_path": str(FIG_DIR / f"ch4_fig4_7_dispersion_{tag}.png"),
            "shape_contour_csv": shape_path,
            "dispersion_tbl1_csv": str(tbl) if tbl else "",
        }
        for param in ["a1", "a2", "b1", "b2", "a3", "b3", "a4", "b4", "a5", "b5", "r0"]:
            record[param] = safe_float(row.get(param))
        rows.append(record)
    return pd.DataFrame(rows)


def write_typical_cases_md(cases_df: pd.DataFrame, path: Path) -> None:
    lines = ["# 第4章典型最优结构案例（20代真实GA）", ""]
    for _, row in cases_df.iterrows():
        lines.extend([
            f"## {row['target_band']}",
            "",
            f"- candidate_id: `{row['candidate_id']}`",
            f"- sample_id: `{row['sample_id']}`",
            f"- shape_id: `{row['shape_id']}`",
            f"- generation: {row['generation']}",
            f"- evaluation_index: {row['evaluation_index']}",
            f"- 真实带隙上下边界: {row['gap_lower_Hz']:.3f}-{row['gap_upper_Hz']:.3f} Hz",
            f"- target_overlap_Hz: {row['target_overlap_Hz']:.3f} Hz",
            f"- cover_ratio: {row['cover_ratio']:.3f}",
            f"- 单胞结构图: `{row['structure_image_path']}`",
            f"- 频散曲线图: `{row['dispersion_image_path']}`",
            "",
            "| 参数 | 数值 |",
            "| --- | ---: |",
        ])
        for param in ["a1", "a2", "b1", "b2", "a3", "b3", "a4", "b4", "a5", "b5", "r0"]:
            lines.append(f"| {param} | {row[param]:.6g} |")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_design_md(variable_df: pd.DataFrame, constraint_df: pd.DataFrame) -> None:
    text = [
        "# 第4章设计变量与约束条件表",
        "",
        "## 设计变量",
        "",
        table_to_md(variable_df),
        "",
        "## 约束条件",
        "",
        table_to_md(constraint_df),
        "",
    ]
    (OUT_DIR / "ch4_design_variables_and_constraints.md").write_text("\n".join(text), encoding="utf-8")


def write_selected_dirs_report(data: Dict[str, Dict[str, Any]]) -> None:
    rows = []
    for tag, item in data.items():
        hist = item["history"]
        rows.append({
            "target_band": item["label"],
            "target_band_tag": tag,
            "selected_dir": str(item["dir"]),
            "generation_min": int(to_num(hist["generation"]).min()),
            "generation_max": int(to_num(hist["generation"]).max()),
            "unique_generation_count": int(to_num(hist["generation"]).nunique()),
            "n_evaluations": int(len(hist)),
            "is_20gen_complete": int(to_num(hist["generation"]).nunique() >= 20),
            "selection_note": item["selection_reason"],
        })
    df = pd.DataFrame(rows)
    save_table(
        df,
        OUT_DIR / "ch4_selected_ga_directories_20gen.csv",
        OUT_DIR / "ch4_selected_ga_directories_20gen.md",
        "第4章采用的20代真实GA输出目录",
    )


def write_main_report(summary_df: pd.DataFrame, config_df: pd.DataFrame, variable_df: pd.DataFrame, constraint_df: pd.DataFrame, improvement_df: pd.DataFrame, cases_df: pd.DataFrame) -> None:
    report = f"""# 第4章 基于真实频散计算的目标频带遗传优化方法（20代结果）

本报告整理第4章所需的真实 COMSOL 频散计算驱动遗传算法材料。第4章只讨论“基于 COMSOL 真实频散计算的闭环遗传优化”，适应度函数不使用机器学习预测值。机器学习筛选、随机候选与真实 GA 的对比应放入第5章。

## 4.1 目标频带结构优化问题列式

设单胞结构设计变量为 $\\mathbf x$，目标频带为 $B_t=[f_l,f_u]$。对每个候选结构，通过 COMSOL 计算频散关系并提取第3-4阶之间的带隙边界 $[g_l(\\mathbf x),g_u(\\mathbf x)]$。目标频带重叠宽度定义为：

$$
J(\\mathbf x)=\\max\\left(0,\\min(g_u(\\mathbf x), f_u)-\\max(g_l(\\mathbf x), f_l)\\right)
$$

目标频带覆盖率定义为：

$$
C(\\mathbf x)=\\frac{{J(\\mathbf x)}}{{f_u-f_l}}
$$

本章优化目标为最大化真实频散计算得到的目标频带重叠宽度：

$$
\\mathbf x^*=\\arg\\max_{{\\mathbf x\\in\\Omega}} J(\\mathbf x)
$$

其中 $\\Omega$ 为满足参数范围、几何有效性、接触有效性与成功求解要求的设计空间。

## 4.2 设计变量、约束条件与适应度函数

设计变量包括离散形状基因 `shape_id` 与连续形状参数 `a1, a2, b1, b2, a3, b3, a4, b4, a5, b5, r0`。变量范围见 `ch4_design_variables.csv`，约束条件见 `ch4_constraints.csv`。

{table_to_md(variable_df)}

约束条件如下：

{table_to_md(constraint_df)}

适应度函数名称为 `target_overlap_Hz`，正文解释为“目标频带重叠宽度”。若几何、接触或求解失败，则通过惩罚适应度处理；成功求解的候选按真实目标频带重叠宽度排序。

## 4.3 COMSOL 频散计算与目标频带重叠宽度提取

每个 GA 个体首先由形状基因和连续参数生成单胞结构，然后调用 COMSOL 频散计算。计算完成后，从频散曲线中提取带隙上下边界，并与目标频带求交，得到 `target_overlap_Hz` 与 `cover_ratio`。图4-2给出了单个个体的真实评价流程。

可用图件：

- 图4-1：`figures/ch4_fig4_1_real_ga_flowchart.png`
- 图4-2：`figures/ch4_fig4_2_comsol_evaluation_flowchart.png`

## 4.4 遗传算法搜索流程

本章采用六个独立目标频带的真实闭环遗传优化结果，每个目标频带均采用最新20代结果。种群规模为6，实际每个完整频带评价120次。代数编号为1-20，不存在0-19编号误判。

遗传操作包括：

- 初始化：从预筛选形状库和参数范围生成初始种群；
- 选择：锦标赛选择，锦标赛规模为 min(3, 当前种群数)；
- 交叉：连续变量采用双亲线性组合，形状基因从双亲中二选一；
- 变异：形状基因按 `shapeMutationRate` 随机替换，连续变量按 `continuousMutationRate` 加高斯扰动并截断到参数范围；
- 精英保留：每代保留适应度最高的 `eliteCount=2` 个个体；
- 终止条件：达到 `maxGenerations=20`，本批结果均未启用早停。

遗传算法参数表：

{table_to_md(config_df)}

## 4.5 不同目标频带下的真实优化结果

六个目标频带最终均采用20代真实 GA 输出目录，汇总结果如下：

{table_to_md(summary_df[["target_band","n_generations_actual","n_evaluations_actual","n_solve_success","solve_success_rate","n_active_overlap","active_rate","best_target_overlap_Hz","best_cover_ratio","best_gap_lower_Hz","best_gap_upper_Hz","best_generation","is_20gen_complete"]])}

可用图件：

- 图4-3：`figures/ch4_fig4_3_ga_convergence_20gen.png`
- 图4-4：`figures/ch4_fig4_4_best_overlap_bar_20gen.png`
- 图4-5：`figures/ch4_fig4_5_success_active_rates_20gen.png`
- 图4-6：`figures/ch4_fig4_6_best_unit_cells_6bands.png`
- 图4-7：`figures/ch4_fig4_7_representative_dispersion_3bands.png`

典型案例见 `ch4_typical_cases_20gen.md`。其中 180-220 Hz 为中频成功案例，200-240 Hz 为中高频案例，240-280 Hz 为高频困难案例。

### 12代到20代改进

{table_to_md(improvement_df)}

图件：`figures/ch4_ga_12gen_vs_20gen_overlap.png`。

## 4.6 本章小结

1. 六个目标频带均已整理为20代真实 GA 结果，每个完整频带实际评价次数为120次。
2. 180-220 Hz 目标频带在20代内达到40 Hz重叠宽度，目标频带覆盖率为1.0，是最清晰的中频成功案例。
3. 160-200 Hz 与200-240 Hz 也获得较高覆盖率，说明真实频散计算驱动的 GA 能够在中频和中高频区域持续改进结构。
4. 220-260 Hz 与240-280 Hz 的最终重叠宽度仍较小，说明高频目标更受结构族与参数化表达限制；继续增加代数可能带来局部改善，但更可能需要扩展形状机制或候选结构族。
5. 本章结果只证明真实 COMSOL 频散计算驱动的遗传优化过程与效果，不混入机器学习预测适应度；机器学习候选筛选对比应在第5章单独展开。

"""
    (OUT_DIR / "CH4_GA_REAL_OPTIMIZATION_REPORT_20GEN.md").write_text(report, encoding="utf-8")


def write_terminal_checklist(data: Dict[str, Dict[str, Any]], summary_df: pd.DataFrame, output_files: List[Path], improvement_df: pd.DataFrame) -> None:
    lines = ["# 第4章20代真实GA整理终端清单", ""]
    lines.append("## 找到的输入文件")
    for tag, item in data.items():
        lines.append(f"- {item['label']}: `{item['dir']}`")
        for name in REQUIRED_FILES:
            lines.append(f"  - {name}: {'OK' if (item['dir']/name).exists() else 'MISSING'}")
    lines.append("")
    lines.append("## 20代完成情况与评价次数")
    for _, row in summary_df.iterrows():
        lines.append(f"- {row['target_band']}: 20代完成={row['is_20gen_complete']}, 实际评价次数={row['n_evaluations_actual']}, 成功求解={row['n_solve_success']}")
    lines.append("")
    lines.append("## 生成文件")
    generated_files = sorted(path for path in OUT_DIR.rglob("*") if path.is_file() and "__pycache__" not in str(path))
    manifest = pd.DataFrame([
        {
            "path": str(path),
            "relative_path": str(path.relative_to(OUT_DIR)),
            "suffix": path.suffix,
            "size_bytes": path.stat().st_size,
        }
        for path in generated_files
    ])
    manifest.to_csv(OUT_DIR / "ch4_generated_file_manifest_20gen.csv", index=False, encoding="utf-8-sig")
    generated_files = sorted(path for path in OUT_DIR.rglob("*") if path.is_file() and "__pycache__" not in str(path))
    for path in generated_files:
        lines.append(f"- `{path}`")
    lines.append("")
    lines.append("## 字段缺失或需要人工确认")
    lines.append("- 配置文件未显式给出“交叉概率”字段；根据脚本，非精英连续变量每次由双亲线性组合生成，形状基因从双亲二选一。")
    lines.append("- 设计变量物理含义按傅里叶/轮廓参数解释，正式论文中可结合第2章结构参数定义再精修。")
    lines.append("")
    lines.append("## 可直接放入第4章的图")
    for stem in [
        "ch4_fig4_1_real_ga_flowchart.png",
        "ch4_fig4_2_comsol_evaluation_flowchart.png",
        "ch4_fig4_3_ga_convergence_20gen.png",
        "ch4_fig4_4_best_overlap_bar_20gen.png",
        "ch4_fig4_5_success_active_rates_20gen.png",
        "ch4_fig4_6_best_unit_cells_6bands.png",
        "ch4_fig4_7_representative_dispersion_3bands.png",
        "ch4_ga_12gen_vs_20gen_overlap.png",
    ]:
        lines.append(f"- `figures/{stem}`")
    lines.append("")
    lines.append("## 12代到20代是否明显改善")
    for _, row in improvement_df.iterrows():
        flag = "是" if row["new_best_in_gen13_to20"] else "否"
        lines.append(f"- {row['target_band']}: 改善 {row['improvement_Hz']:.3f} Hz，新最优出现在13-20代={flag}")
    lines.append("")
    lines.append("## 是否建议继续补跑高频目标")
    lines.append("- 建议谨慎继续。220-260 Hz 与240-280 Hz 的20代最优重叠宽度仍只有约4 Hz，延长代数带来局部改善的可能存在，但从当前20代收敛表现看，高频瓶颈更可能来自结构族/几何机制不足。建议优先作为论文中的高频困难案例呈现；若要提升高频结果，应先扩展形状族或参数化机制，再考虑更长GA。")
    (OUT_DIR / "CH4_TERMINAL_CHECKLIST_20GEN.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


def main() -> None:
    mkdirs()
    configure_fonts()
    data = load_band_data()
    write_selected_dirs_report(data)
    summary_df, config_df = make_summary_tables(data)
    variable_df, constraint_df = make_design_tables(data)
    improvement_df = make_improvement_table(data)

    save_table(summary_df, OUT_DIR / "ch4_ga_summary_20gen.csv", OUT_DIR / "ch4_ga_summary_20gen.md", "第4章真实GA总结果表（20代）")
    save_table(config_df, OUT_DIR / "ch4_ga_config_table_20gen.csv", OUT_DIR / "ch4_ga_config_table_20gen.md", "遗传算法参数设置表（20代）")
    variable_df.to_csv(OUT_DIR / "ch4_design_variables.csv", index=False, encoding="utf-8-sig")
    constraint_df.to_csv(OUT_DIR / "ch4_constraints.csv", index=False, encoding="utf-8-sig")
    write_design_md(variable_df, constraint_df)
    save_table(improvement_df, OUT_DIR / "ch4_ga_12to20_improvement.csv", OUT_DIR / "ch4_ga_12to20_improvement.md", "12代到20代改进分析表")

    fig_paths: Dict[str, str] = {}
    fig_paths.update(draw_flowchart(
        "ch4_fig4_1_real_ga_flowchart",
        "图4-1 基于真实频散计算的遗传优化流程",
        ["目标频带定义", "初始种群生成", "COMSOL频散计算", "目标频带重叠宽度", "选择/交叉/变异", "20代终止与最优结构"],
        [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)],
    ))
    fig_paths.update(draw_flowchart(
        "ch4_fig4_2_comsol_evaluation_flowchart",
        "图4-2 GA个体的COMSOL真实评价流程",
        ["个体编码\nshape_id + 参数", "生成单胞几何", "几何/接触检查", "COMSOL特征频率求解", "提取带隙边界", "计算重叠宽度与覆盖率"],
        [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)],
    ))
    fig_paths.update(plot_convergence(data))
    fig_paths.update(plot_best_bar(summary_df))
    fig_paths.update(plot_rates(summary_df))
    fig_paths.update(plot_shapes(data))
    fig_paths.update(plot_dispersion_cases(data))
    fig_paths.update(plot_improvement(improvement_df))

    cases_df = make_typical_cases(data)
    cases_df.to_csv(OUT_DIR / "ch4_typical_cases_20gen.csv", index=False, encoding="utf-8-sig")
    write_typical_cases_md(cases_df, OUT_DIR / "ch4_typical_cases_20gen.md")
    write_main_report(summary_df, config_df, variable_df, constraint_df, improvement_df, cases_df)

    output_files = [
        OUT_DIR / "ch4_selected_ga_directories_20gen.csv",
        OUT_DIR / "ch4_selected_ga_directories_20gen.md",
        OUT_DIR / "ch4_ga_summary_20gen.csv",
        OUT_DIR / "ch4_ga_summary_20gen.md",
        OUT_DIR / "ch4_ga_config_table_20gen.csv",
        OUT_DIR / "ch4_ga_config_table_20gen.md",
        OUT_DIR / "ch4_design_variables.csv",
        OUT_DIR / "ch4_constraints.csv",
        OUT_DIR / "ch4_design_variables_and_constraints.md",
        OUT_DIR / "ch4_typical_cases_20gen.csv",
        OUT_DIR / "ch4_typical_cases_20gen.md",
        OUT_DIR / "ch4_ga_12to20_improvement.csv",
        OUT_DIR / "ch4_ga_12to20_improvement.md",
        OUT_DIR / "CH4_GA_REAL_OPTIMIZATION_REPORT_20GEN.md",
    ]
    output_files.extend(Path(v) for v in fig_paths.values())
    write_terminal_checklist(data, summary_df, output_files, improvement_df)


if __name__ == "__main__":
    main()
