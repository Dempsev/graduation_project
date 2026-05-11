from __future__ import annotations

import json
import shutil
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, Rectangle


ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = ROOT / "data" / "analysis"
CATALOG_PATH = ROOT / "prediction_targetband_param_v1" / "configs" / "thesis_band_catalog_v2.json"
DATASET_INFO_PATH = (
    ROOT
    / "data"
    / "prediction_targetband_param_v1"
    / "v1"
    / "windows_dense_v8_truth_plus_exploratory_aug_v1"
    / "dataset_info.json"
)
COVERAGE_CSV = (
    ANALYSIS_DIR
    / "targetband_band_coverage_v1"
    / "thesis_band_catalog_v2_after_exploratory_v2"
    / "band_coverage_summary_v1.csv"
)
CLS_RUN_ROOT = (
    ROOT
    / "data"
    / "prediction_targetband_param_v1_runs"
    / "param_targetband_cls_rf_dense_v8_cmp_v1"
    / "stratified_group_kfold"
)
REG_RUN_ROOT = (
    ROOT
    / "data"
    / "prediction_targetband_param_v1_runs"
    / "param_targetband_cover_hgb_dense_v8_cmp_v1"
    / "stratified_group_kfold"
)
READINESS_DIR = ANALYSIS_DIR / "predictor_readiness_v1"
CH6_DIR = ANALYSIS_DIR / "thesis_ch6_v1"

FONT_CANDIDATES = ["Microsoft YaHei", "SimHei", "SimSun", "DejaVu Sans"]


def set_plot_style() -> None:
    plt.rcParams["font.sans-serif"] = FONT_CANDIDATES
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.facecolor"] = "white"
    plt.rcParams["savefig.facecolor"] = "white"
    plt.rcParams["axes.titleweight"] = "bold"


def chapter_dir(chapter: int) -> Path:
    return ANALYSIS_DIR / f"thesis_ch{chapter}_v1"


def ensure_chapter(chapter: int) -> tuple[Path, Path, Path]:
    root = chapter_dir(chapter)
    fig_dir = root / "figures"
    tab_dir = root / "tables"
    fig_dir.mkdir(parents=True, exist_ok=True)
    tab_dir.mkdir(parents=True, exist_ok=True)
    return root, fig_dir, tab_dir


def load_catalog() -> list[dict[str, object]]:
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return list(payload["bands"])


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def fmt_value(value: object, digits: int = 4) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.{digits}f}"
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return str(value)


def df_to_markdown(df: pd.DataFrame, digits: int = 4) -> str:
    columns = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(columns) + " |"]
    lines.append("| " + " | ".join(["---"] * len(columns)) + " |")
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(fmt_value(row[c], digits) for c in df.columns) + " |")
    return "\n".join(lines) + "\n"


def write_table(df: pd.DataFrame, tab_dir: Path, stem: str, digits: int = 4) -> tuple[Path, Path]:
    csv_path = tab_dir / f"{stem}.csv"
    md_path = tab_dir / f"{stem}.md"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    md_path.write_text(df_to_markdown(df, digits), encoding="utf-8")
    return csv_path, md_path


def wrap_label(text: str, width: int = 18) -> str:
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False, replace_whitespace=False))


def draw_box(
    ax: plt.Axes,
    xy: tuple[float, float],
    w: float,
    h: float,
    text: str,
    *,
    fc: str = "#eef5ff",
    ec: str = "#315f8c",
    fontsize: int = 10,
    lw: float = 1.6,
) -> None:
    ax.add_patch(Rectangle(xy, w, h, facecolor=fc, edgecolor=ec, linewidth=lw))
    ax.text(
        xy[0] + w / 2,
        xy[1] + h / 2,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        color="#1e2b36",
    )


def draw_arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float], color: str = "#375a7f") -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=14,
            linewidth=1.5,
            color=color,
            shrinkA=4,
            shrinkB=4,
        )
    )


def save_current(fig: plt.Figure, path: Path) -> Path:
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return path


def make_overall_framework(fig_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(12.8, 4.8))
    ax.set_xlim(0, 12.8)
    ax.set_ylim(0, 4.8)
    ax.axis("off")

    labels = [
        "物理真值生产\nCOMSOL / MATLAB",
        "Target-band\n数据集构建",
        "条件预测器\nRF + HGB",
        "预测引导搜索\nshape-aware\nlocal GA",
        "Stage4 真实验证\n可用设计确认",
    ]
    xs = [0.35, 2.85, 5.35, 7.85, 10.35]
    colors = ["#e8f2f7", "#eaf4e7", "#fff4d8", "#f7e8e5", "#e9e6f5"]
    for i, (x, label) in enumerate(zip(xs, labels)):
        draw_box(ax, (x, 2.35), 1.85, 1.35, label, fc=colors[i])
        if i < len(xs) - 1:
            draw_arrow(ax, (x + 1.85, 3.03), (xs[i + 1], 3.03))

    draw_box(ax, (0.45, 0.75), 3.25, 0.9, "truth layer\n保证标签来自真实物理计算", fc="#f5f8fa", ec="#8aa4b5", fontsize=9)
    draw_box(ax, (4.75, 0.75), 3.25, 0.9, "model layer\n把“结构 + 目标频带”映射到可排序分数", fc="#f5f8fa", ec="#8aa4b5", fontsize=9)
    draw_box(ax, (9.05, 0.75), 3.25, 0.9, "search layer\n把候选推进到真实验证闭环", fc="#f5f8fa", ec="#8aa4b5", fontsize=9)
    ax.text(0.35, 4.25, "图 1-1  本文 target-band 逆向设计总体框架", fontsize=15, weight="bold", color="#17212b")
    return save_current(fig, fig_dir / "figure_1_1_overall_framework.png")


def make_problem_boundary(fig_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(11.5, 5.2))
    ax.set_xlim(0, 11.5)
    ax.set_ylim(0, 5.2)
    ax.axis("off")
    ax.add_patch(Rectangle((0.35, 0.45), 10.8, 4.25, fill=False, edgecolor="#465a69", linewidth=2.0))
    ax.text(0.55, 4.38, "论文成立边界：thesis band catalog + 当前参数化结构族 + 固定材料/求解配置", fontsize=12, weight="bold")

    draw_box(ax, (0.85, 2.8), 2.2, 1.0, "输入\n结构参数/shape 特征\n目标频带区间", fc="#eaf4e7")
    draw_box(ax, (3.75, 2.8), 2.1, 1.0, "条件预测\nopen probability\ncover ratio", fc="#fff4d8")
    draw_box(ax, (6.5, 2.8), 2.0, 1.0, "候选推进\nranking/refinement", fc="#f7e8e5")
    draw_box(ax, (9.05, 2.8), 1.65, 1.0, "输出\n可验证设计", fc="#e9e6f5")
    for start, end in [((3.05, 3.3), (3.75, 3.3)), ((5.85, 3.3), (6.5, 3.3)), ((8.5, 3.3), (9.05, 3.3))]:
        draw_arrow(ax, start, end)

    draw_box(ax, (0.85, 1.15), 2.2, 0.85, "不是任意结构\n不是任意材料", fc="#f7f7f7", ec="#a0a0a0", fontsize=9)
    draw_box(ax, (3.75, 1.15), 2.1, 0.85, "predictor 是\nshortlist engine\n不是求解器替代品", fc="#f7f7f7", ec="#a0a0a0", fontsize=9)
    draw_box(ax, (6.5, 1.15), 2.0, 0.85, "local GA 负责局部推进\n不是全局最优保证", fc="#f7f7f7", ec="#a0a0a0", fontsize=9)
    draw_box(ax, (9.05, 1.15), 1.65, 0.85, "Stage4 给出\n最终物理确认", fc="#f7f7f7", ec="#a0a0a0", fontsize=9)
    ax.text(0.35, 4.9, "图 2-1  目标频带逆向设计问题定义与边界", fontsize=15, weight="bold")
    return save_current(fig, fig_dir / "figure_2_1_problem_boundary.png")


def make_shape_atlas(fig_dir: Path) -> Path:
    shape_ids = [
        "ep100_step18_contour_xy",
        "ep193_step51_contour_xy",
        "ep248_step27_contour_xy",
        "ep253_step54_contour_xy",
        "ep571_step57_contour_xy",
        "ep239_step27_contour_xy",
    ]
    fig, axes = plt.subplots(2, 3, figsize=(10.8, 6.4))
    for ax, shape_id in zip(axes.flat, shape_ids):
        path = ROOT / "data" / "shape_contours" / f"{shape_id}.csv"
        df = pd.read_csv(path)
        ax.plot(df["x"], df["y"], color="#2d5f73", linewidth=2.0)
        ax.fill(df["x"], df["y"], color="#8fc3d9", alpha=0.35)
        ax.scatter(df["x"], df["y"], s=12, color="#244655")
        ax.set_aspect("equal", adjustable="box")
        ax.set_title(shape_id.replace("_contour_xy", ""), fontsize=9)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_edgecolor("#c7d3d8")
    fig.suptitle("图 3-1  典型结构族与参数化几何示意图", fontsize=15, weight="bold", y=0.98)
    return save_current(fig, fig_dir / "figure_3_1_shape_family_atlas.png")


def make_band_coverage_figure(fig_dir: Path, coverage: pd.DataFrame) -> Path:
    fig, ax1 = plt.subplots(figsize=(11.5, 5.2))
    df = coverage.sort_values("target_band_low_Hz").copy()
    x = np.arange(len(df))
    bars = ax1.bar(x - 0.18, df["positive_rows"], width=0.36, color="#4c78a8", label="positive rows")
    ax1.set_ylabel("positive rows")
    ax1.set_xticks(x)
    ax1.set_xticklabels(df["target_band_tag"], rotation=25, ha="right")
    ax2 = ax1.twinx()
    ax2.plot(x + 0.18, df["cover_ratio_mean_positive"], marker="o", color="#f58518", linewidth=2.2, label="mean cover ratio")
    ax2.set_ylabel("mean positive cover ratio")
    ax1.set_title("图 3-2  thesis band catalog 覆盖度与正样本质量", fontsize=15, weight="bold")
    for bar in bars:
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2, h + max(df["positive_rows"]) * 0.015, f"{int(h)}", ha="center", va="bottom", fontsize=8)
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc="upper right")
    ax1.grid(axis="y", alpha=0.25)
    return save_current(fig, fig_dir / "figure_3_2_band_catalog_coverage.png")


def make_conditional_prediction_task(fig_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(11.8, 4.6))
    ax.set_xlim(0, 11.8)
    ax.set_ylim(0, 4.6)
    ax.axis("off")
    draw_box(ax, (0.5, 2.55), 2.4, 1.0, "结构特征\n几何参数\nshape descriptors", fc="#e8f2f7")
    draw_box(ax, (0.5, 1.15), 2.4, 1.0, "目标频带条件\nlow / high / center / width", fc="#eaf4e7")
    draw_box(ax, (4.0, 1.85), 2.4, 1.05, "条件预测模型\nclassifier + regressor", fc="#fff4d8")
    draw_box(ax, (7.5, 2.55), 2.35, 1.0, "打开概率\nP(open | s, band)", fc="#f7e8e5")
    draw_box(ax, (7.5, 1.15), 2.35, 1.0, "覆盖质量\ncover ratio / overlap", fc="#f7e8e5")
    draw_box(ax, (10.2, 1.85), 1.15, 1.05, "shortlist\nscore", fc="#e9e6f5")
    for start, end in [((2.9, 3.05), (4.0, 2.55)), ((2.9, 1.65), (4.0, 2.2)), ((6.4, 2.4), (7.5, 3.05)), ((6.4, 2.25), (7.5, 1.65)), ((9.85, 3.05), (10.2, 2.55)), ((9.85, 1.65), (10.2, 2.2))]:
        draw_arrow(ax, start, end)
    ax.text(0.45, 4.15, "图 4-1  面向目标频带的条件预测任务定义", fontsize=15, weight="bold")
    return save_current(fig, fig_dir / "figure_4_1_conditional_prediction_task.png")


def make_inverse_design_workflow(fig_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(14.0, 5.2))
    ax.set_xlim(0, 14.0)
    ax.set_ylim(0, 5.2)
    ax.axis("off")
    steps = [
        ("候选池", "candidate pool\n结构族/参数空间"),
        ("预测评分", "seed scoring\nP(open) x cover"),
        ("形状感知筛选", "family-balanced\nshortlist"),
        ("局部细化", "local GA\nrefinement"),
        ("验证清单", "manifest\nPython -> MATLAB"),
        ("真实验证", "Stage4 COMSOL\n物理确认"),
    ]
    xs = [0.35, 2.6, 4.85, 7.1, 9.35, 11.6]
    for i, (title, body) in enumerate(steps):
        draw_box(ax, (xs[i], 2.7), 1.75, 1.25, f"{title}\n{body}", fc=["#e8f2f7", "#fff4d8", "#eaf4e7", "#f7e8e5", "#f5f5f5", "#e9e6f5"][i], fontsize=8.5)
        if i < len(steps) - 1:
            draw_arrow(ax, (xs[i] + 1.75, 3.32), (xs[i + 1], 3.32))
    ax.add_patch(Rectangle((2.0, 0.85), 5.0, 0.9, facecolor="#fafafa", edgecolor="#a7a7a7", linewidth=1.2))
    ax.text(4.5, 1.3, "predictor 提供方向感：先排序，再进入真实搜索", ha="center", va="center", fontsize=10)
    ax.add_patch(Rectangle((7.65, 0.85), 5.2, 0.9, facecolor="#fafafa", edgecolor="#a7a7a7", linewidth=1.2))
    ax.text(10.25, 1.3, "real validation 决定最终可信度：模型分数不是最终结果", ha="center", va="center", fontsize=10)
    ax.text(0.35, 4.65, "图 5-1  prediction-guided target-band inverse-design workflow", fontsize=15, weight="bold")
    return save_current(fig, fig_dir / "figure_5_1_inverse_design_workflow.png")


def make_baseline_positioning(fig_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(11.5, 4.8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")
    rows = [
        (4.1, "历史 baseline", "generic prior / old GA\n用于说明旧路线能力与缺口", "#f0f0f0"),
        (3.0, "冻结主线", "target-band predictor + shape-aware + local refinement\n论文正式主线", "#eaf4e7"),
        (1.9, "真实验证", "Stage4 / COMSOL\n负责最终物理确认", "#e9e6f5"),
        (0.8, "附录支撑", "runbook / manifest / smoke checks\n负责可复现性说明", "#fff4d8"),
    ]
    for y, left, right, color in rows:
        draw_box(ax, (0.6, y - 0.35), 2.0, 0.7, left, fc=color)
        draw_box(ax, (3.2, y - 0.35), 6.2, 0.7, right, fc=color, ec="#6f7f89")
        draw_arrow(ax, (2.6, y), (3.2, y), color="#6f7f89")
    ax.text(0.5, 4.75, "图 5-2  主线与 baseline / 工程支撑的角色定位", fontsize=15, weight="bold")
    return save_current(fig, fig_dir / "figure_5_2_mainline_baseline_positioning.png")


def make_validity_scope(fig_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(9.5, 6.0))
    ax.set_xlim(0, 9.5)
    ax.set_ylim(0, 6)
    ax.axis("off")
    boxes = [
        ((0.9, 4.1), 7.7, 1.0, "成立范围 1：thesis band catalog 内的目标频带请求", "#eaf4e7"),
        ((1.4, 3.0), 6.7, 0.85, "成立范围 2：当前参数化结构族与 shape-aware 候选构造", "#e8f2f7"),
        ((1.9, 2.0), 5.7, 0.75, "成立范围 3：固定材料配置与当前物理求解设置", "#fff4d8"),
        ((2.4, 1.1), 4.7, 0.65, "最终确认：Stage4 real validation", "#e9e6f5"),
    ]
    for xy, w, h, text, color in boxes:
        draw_box(ax, xy, w, h, text, fc=color, ec="#476270")
    ax.text(0.6, 5.55, "图 7-1  方法成立范围与局限性边界", fontsize=15, weight="bold")
    ax.text(0.9, 0.45, "写作要点：边界越清楚，论文主张越可信；不要把 predictor 写成通用物理求解器。", fontsize=11, color="#38454f")
    return save_current(fig, fig_dir / "figure_7_1_validity_scope.png")


def make_conclusion_roadmap(fig_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(12.0, 4.9))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 4.9)
    ax.axis("off")
    draw_box(ax, (0.45, 2.65), 2.05, 1.0, "已完成\n闭环 workflow", fc="#eaf4e7")
    draw_box(ax, (3.0, 2.65), 2.05, 1.0, "当前贡献\ncatalog 内可验证逆设", fc="#e8f2f7")
    draw_box(ax, (5.55, 2.65), 2.05, 1.0, "当前边界\n非任意 band / 非任意结构", fc="#fff4d8")
    draw_box(ax, (8.1, 2.65), 3.25, 1.0, "未来扩展\n更大 catalog / 更丰富结构 / 更强泛化", fc="#f7e8e5")
    for start, end in [((2.5, 3.15), (3.0, 3.15)), ((5.05, 3.15), (5.55, 3.15)), ((7.6, 3.15), (8.1, 3.15))]:
        draw_arrow(ax, start, end)
    topics = ["扩大目标频带目录", "加强 weak-band truth harvesting", "提升跨 band 泛化", "扩展结构表示能力", "接入更完整工程场景"]
    for i, topic in enumerate(topics):
        draw_box(ax, (0.55 + i * 2.25, 1.0), 1.8, 0.65, topic, fc="#fafafa", ec="#9aa8b0", fontsize=9)
    ax.text(0.45, 4.35, "图 8-1  全文结论与后续工作路线图", fontsize=15, weight="bold")
    return save_current(fig, fig_dir / "figure_8_1_conclusion_roadmap.png")


def copy_if_exists(src: Path, dst: Path) -> Path | None:
    if not src.exists():
        return None
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return dst


CH6_DISPLAY_NAMES = {
    "figure_6_2_canonical_cases": "图 6-2 canonical inverse-design cases 真实结果图",
    "figure_6_3_baseline_comparison": "图 6-3 baseline comparison 对照图",
    "figure_6_4_weak_band_dashboard": "图 6-4 weak-band coverage / shortlist 价值图",
    "figure_6_5_stage4_validation": "图 6-5 stage4 real validation 结果统计图",
    "figure_6_6_local_robustness": "图 6-6 local robustness 分析图",
    "table_6_1_experiment_lines": "表 6-1 全部实验线与作用定位",
    "table_6_2_canonical_cases": "表 6-2 canonical inverse-design cases 汇总",
    "table_6_3_baseline_comparison": "表 6-3 baseline comparison 汇总",
    "table_6_4_stage4_validation": "表 6-4 stage4 real validation 汇总",
    "table_6_5_local_robustness_summary": "表 6-5 local robustness 汇总",
}


DETAILED_GUIDANCE = {
    "figure_1_1_overall_framework": {
        "content": "这张图把全文主线压缩成五个连续模块：物理真值生产、target-band 数据集构建、条件预测器、预测引导搜索和 Stage4 真实验证；下方三层标注说明 truth layer、model layer、search layer 的角色分工。",
        "read": "从左向右看数据和证据如何流动：前两步回答“真值和数据从哪里来”，中间一步回答“predictor 如何成为 shortlist engine”，后两步回答“候选如何被推进并被真实物理确认”。",
        "use": "放在 1.4 技术路线或 1.5 主要工作之前，用来提前建立全文叙事。正文不要展开数值，重点说明本文不是单模型论文，而是一条闭环 workflow。",
    },
    "table_1_1_contribution_map": {
        "content": "该表把绪论中的主要工作点映射到后文章节和证据来源，包括条件预测、预测引导逆向设计、真实物理验证和主线边界收口。",
        "read": "按“工作点 -> 论文含义 -> 主要落点 -> 写作作用”阅读，确认每个创新点后面都有实验或方法章节支撑。",
        "use": "适合放在 1.5 主要工作与创新点后，作为创新点的证据导航表。写作时可逐行转成四个贡献段落。",
    },
    "figure_2_1_problem_boundary": {
        "content": "这张图定义目标频带逆向设计问题的输入、模型中间输出、候选推进和最终可验证设计，同时把成立边界框在 thesis band catalog 与当前结构族内。",
        "read": "重点看灰色边界框和下方限制说明：predictor 只负责排序与筛选，Stage4 才负责最终物理确认。",
        "use": "放在 2.1 或 2.2，用来防止读者把任务理解成“任意结构任意频带的通用逆向设计”。",
    },
    "table_2_1_problem_io_boundary": {
        "content": "该表用文本形式列出输入、中间输出、最终输出和边界，是图 2-1 的可引用表格版。",
        "read": "特别注意“中间输出”和“最终输出”的区别：概率、cover ratio 和 shortlist score 不是最终物理结论。",
        "use": "放在问题定义之后，正文可按四行分别解释输入空间、目标函数、输出形态和限制条件。",
    },
    "table_2_2_module_contract": {
        "content": "该表把论文术语对应到真实代码入口和权威输出目录，覆盖 truth production、dataset、predictor、seed scoring、local refinement 和 real validation。",
        "read": "读表时看每个术语是否有明确的入口和输出；这能证明论文不是抽象方法，而是仓库中可复现的流程。",
        "use": "适合放在 2.3 系统框架，也可在附录 C 复用。正文中用它支撑“主线收口”和“可复现性”。",
    },
    "figure_3_1_shape_family_atlas": {
        "content": "这张图从 `data/shape_contours` 读取真实 contour 文件，展示典型 shape family 的几何形态，包括后续 canonical cases 中使用的 ep193、ep248、ep253 等结构。",
        "read": "不要把它当作性能图；它的作用是让读者直观看到 shape family 与参数化几何的实际形态，理解结构族差异是真实存在的。",
        "use": "放在 3.1 参数化结构表示小节。正文先说明这些 contour 是模型输入特征与后续物理验证的共同几何基础。",
    },
    "figure_3_2_band_catalog_coverage": {
        "content": "这张图把六个 thesis bands 的 positive rows 和正样本 mean cover ratio 放在同一张图中，展示数据覆盖量与正样本质量并不完全一致。",
        "read": "蓝色柱子看正样本数量，橙色折线看平均覆盖质量；弱 band 的困难通常体现在覆盖质量、稀疏性或补充优先级上。",
        "use": "放在 3.4 或 3.5，用来解释为什么后续需要 predictor readiness、weak-band 分析和真实验证，而不是只看数据量。",
    },
    "table_3_1_thesis_band_catalog_stats": {
        "content": "该表汇总六个 thesis bands 的频率范围、角色、样本总数、正样本数、正样本率、positive families 和平均 cover ratio。",
        "read": "优先看 role、positive_rate、positive_families 与 cover_ratio_mean_positive：它们共同说明每个 band 在论文中的身份和难度。",
        "use": "放在 3.3 target-band 数据集构建小节，是第三章最核心的数据表。正文可逐 band 解释为什么 `band180_220` 是 showcase，而高频 bands 是弱 band 重点。",
    },
    "table_3_2_dataset_inventory": {
        "content": "该表给出 v8 target-band 参数化数据集的总行数、unique designs、unique families、默认数据集 tag 和权威 CSV 路径。",
        "read": "它回答“训练和分析到底基于哪个数据集、规模多大”。",
        "use": "放在 3.2 或 3.4，用作数据基础总览；详细字段可放附录，正文保留总量和路径即可。",
    },
    "figure_4_1_conditional_prediction_task": {
        "content": "这张图把条件预测拆成结构特征、目标频带条件、分类器输出、回归器输出和最终 shortlist score。",
        "read": "关键是看目标频带条件进入模型输入，而不是训练一个无条件结构性能预测器；这就是 target-band-conditioned 的核心。",
        "use": "放在 4.1 任务定义小节，用它引出分类器和回归器为什么要并行存在。",
    },
    "figure_4_2_predictor_readiness_summary": {
        "content": "该图来自既有 predictor readiness 分析，汇总 family-CV 下分类、回归、top-k shortlist 等核心表现。",
        "read": "不要只看 accuracy；应同时看 balanced accuracy、回归误差和 top-k cover lift，因为 predictor 的论文角色是排序前端。",
        "use": "放在 4.4 方法评价或第 6.3 结果小节均可。第四章使用时偏方法有效性，第六章使用时偏实验证据。",
    },
    "table_4_1_training_config": {
        "content": "该表固定分类器和回归器的模型族、预测目标、评估方式、分组键与权威输出目录。",
        "read": "看它是否说明清楚 RF 负责 open/not-open，HGB 负责 cover ratio；group key 为 shape_family，强调未见结构族评估。",
        "use": "放在 4.3 训练与评估设置小节。正文可用一段说明为何 family-CV 比随机切分更适合本论文。",
    },
    "table_4_2_predictor_readiness_core_metrics": {
        "content": "该表汇总分类器 accuracy、precision、recall、F1、balanced accuracy，以及回归器 MAE、RMSE、R2。",
        "read": "分类指标看 screening 是否可靠；回归指标看 cover ratio ranking 是否可用；两者一起才支撑 shortlist engine。",
        "use": "放在 4.4 或 6.3。正文应写成“足以进入 workflow”，而不是“模型已经完美”。",
    },
    "table_4_3_by_band_readiness": {
        "content": "该表逐 thesis band 展示分类和回归表现，帮助识别哪些 band 容易、哪些 band 更困难。",
        "read": "横向比较不同 band 的 f1、balanced_accuracy 和 mae；尤其关注高频、弱 band 的边界。",
        "use": "放在 4.4.1 后，作为总体指标之外的分 band 解释。正文可用它说明 predictor 的可用范围和保留项。",
    },
    "table_4_4_topk_shortlist_quality": {
        "content": "该表展示 top-5、top-10、top-20、top-50 候选的 hit rate、mean cover 和相对随机均值的 lift。",
        "read": "重点看 top-k mean cover 和 lift_mean_cover；这比单纯分类精度更接近逆向设计场景。",
        "use": "放在 4.4.3 或 6.3，作为 predictor 具备 shortlist value 的直接证据。",
    },
    "figure_5_1_inverse_design_workflow": {
        "content": "这张图展示第五章方法主线：候选池、预测评分、形状感知筛选、局部细化、验证清单、Stage4 真实验证。",
        "read": "从左到右看 predictor 如何先提供方向，再由 local refinement 推进，最后由 manifest 交给 MATLAB/COMSOL 验证。",
        "use": "放在 5.1 总体方法开头，是第五章最重要的流程图。正文围绕每个框展开一个小节即可。",
    },
    "figure_5_2_mainline_baseline_positioning": {
        "content": "这张图把正式主线、历史 baseline、真实验证和附录支撑分层，说明它们在论文叙事中的身份不同。",
        "read": "看“冻结主线”与“历史 baseline”的分离：baseline 是对照，不应被写成当前默认 workflow。",
        "use": "放在 5.1 或 5.5，用来统一第五章和第六章的路线口径。",
    },
    "table_5_1_mainline_vs_baselines": {
        "content": "该表列出 frozen mainline、generic prior、band-catalog real GA、local robustness 等路线的论文身份和使用方式。",
        "read": "重点看“论文身份”列：正式主线、baseline、真实搜索 baseline、补充支撑的角色不能混淆。",
        "use": "放在第五章方法边界或第六章实验设置前，避免结果章节显得像脚本堆叠。",
    },
    "table_5_2_workflow_artifacts": {
        "content": "该表列出 seed scoring、local refinement、validation manifest、stage4 validation 的入口与关键输出。",
        "read": "它是方法流程的可复现证据；每一步都有明确脚本和文件落点。",
        "use": "放在 5.4 或附录命令表。正文中可用它说明 Python 到 MATLAB 的 manifest contract。",
    },
    "figure_6_1_predictor_readiness": {
        "content": "该图承接第 6.3 节，集中展示 predictor 是否已经具备进入实验主线的 readiness。",
        "read": "把它和表 4-2、表 4-4 联合看：总体指标说明模型稳定，top-k 质量说明它能改善候选排序。",
        "use": "放在 6.3 开头或结尾，正文用它得出“predictor 可以作为 workflow-ready shortlist engine”的结论。",
    },
    "figure_6_2_canonical_cases": {
        "content": "该图展示四个 canonical inverse-design cases 的 base-vs-best refinement 摘要，覆盖 `band180_220`、`band200_240`、`band220_260`、`band240_280`。",
        "read": "看每个 case 的 targetband score、predicted cover/overlap 是否在 refinement 后改善或保持高位；这说明 workflow 能找到可验证候选。",
        "use": "放在 6.4，与表 6-2 搭配。正文按 case 逐段解释，不要只说“有四个案例”。",
    },
    "figure_6_3_baseline_comparison": {
        "content": "该图把 seed discovery、GA 搜索和直接验证的 baseline 对照集中展示，用于说明当前主线相对旧路线的综合优势。",
        "read": "重点比较不同路线在候选发现、真实验证转化和 best/mean gain 上的差异；它不是单一指标冠军图。",
        "use": "放在 6.5。正文应强调 frozen target-band mainline 在当前约束下更适合作为正式主线，而不是宣称所有指标绝对最优。",
    },
    "figure_6_4_weak_band_dashboard": {
        "content": "该图围绕弱 band 展示覆盖库存、shortlist lift 和主线可用性，是证明高频/困难 band 得到实质推进的核心素材。",
        "read": "先看 coverage，再看 predictor top-k 是否提高候选质量，最后看 canonical/refinement 是否形成可验证推进。",
        "use": "放在 6.6。正文用它支撑“weak-band design discovery 得到推进，但未被完全解决”的克制表述。",
    },
    "figure_6_5_stage4_validation": {
        "content": "该图展示 Stage4 validation 的验证漏斗、positive gain 情况和 gain 分布，用于证明最终结果经过真实物理闭环。",
        "read": "看 solve_success、geometry_valid/contact_valid、positive gain 等指标；这些比 predictor score 更接近最终可信结论。",
        "use": "放在 6.7。正文应把它写成全论文落点：方法从数据和预测走到了真实 COMSOL 验证。",
    },
    "figure_6_6_local_robustness": {
        "content": "该图整理 canonical cases 的局部 edge-drift / perturbation 表现，说明设计点附近是否保持 target-band 行为。",
        "read": "关注中心点覆盖、局部保持率、边界漂移和最差变体；它回答的是稳定性，不是重新证明主结果。",
        "use": "放在 6.8 或附录 D。正文中把它作为 canonical cases 的补充支撑，而不是另起一条主线。",
    },
    "table_6_1_experiment_lines": {
        "content": "该表列出第六章每条实验线的作用定位，包括 predictor readiness、canonical cases、baseline comparison、weak-band、stage4 validation 和 robustness。",
        "read": "按 section 看每个实验块回答什么问题，避免第六章写成流水账。",
        "use": "放在 6.1 或 6.2，是第六章总览表。正文可先引用它说明本章按证据链组织。",
    },
    "table_6_2_canonical_cases": {
        "content": "该表给出四个 canonical cases 的 target band、shape identity、base score、best score、predicted cover/overlap 与提升量。",
        "read": "先看 target_band_tag 和 shape_id，再看 base 与 best 的差异；delta 列说明 refinement 是否产生增益。",
        "use": "放在 6.4，与图 6-2 配套。正文适合按每个 case 写“结构身份 -> 真实结果 -> 与旧路线对比 -> 意义”。",
    },
    "table_6_3_baseline_comparison": {
        "content": "该表汇总 baseline comparison 的多类指标，包括 seed family summary、GA/seed 验证率、gain 对比等。",
        "read": "表较宽，正文不要逐列解释；优先提取与图 6-3 对应的关键指标，详细列放附录也可以。",
        "use": "放在 6.5 或附录。主文引用时用它支撑具体数值，图 6-3 负责整体可读性。",
    },
    "table_6_4_stage4_validation": {
        "content": "该表逐行列出 top6 Stage4 validation 样本的 solve_success、geometry_valid、contact_valid、probability、cascade score、gap34 gain 和边界频率。",
        "read": "先筛 solve_success/contact_valid，再看 gap34_gain_Hz 和 gap edges；未求解成功的行不能当作正向物理结果。",
        "use": "放在 6.7。正文可汇总成功率和正向 gain，再用一两个代表样本解释边界频率落点。",
    },
    "table_6_5_local_robustness_summary": {
        "content": "该表汇总每个 canonical case 的中心 cover、variant cover、保持率和上下边界漂移。",
        "read": "重点看 variants_ge_90pct_center、variants_ge_80pct_center、mean/max edge shift；这些反映设计点附近的稳定性。",
        "use": "放在 6.8 或附录 D。主文可压缩成一段，强调它是主结果可信度的补充证据。",
    },
    "figure_7_1_validity_scope": {
        "content": "该图用层层边界展示本文方法真正成立的范围：catalog、结构族、材料/求解配置和 Stage4 确认。",
        "read": "由外到内看限制逐渐收紧；越靠内越接近最终可信结论。",
        "use": "放在 7.1。正文用它帮助写出克制边界，避免过度宣称。",
    },
    "table_7_1_scope_and_limitations": {
        "content": "该表把成立范围和局限性逐项列出，并给出论文中应该采用的写法。",
        "read": "重点看最后一列，它直接规定哪些话能写、哪些话不能写过头。",
        "use": "放在 7.1-7.2。写讨论章时可按表格每行扩成一个自然段。",
    },
    "figure_8_1_conclusion_roadmap": {
        "content": "这张图把已完成闭环、当前贡献、当前边界和未来扩展串成一条结论路线。",
        "read": "从左到右看结论如何从“已完成什么”过渡到“还能扩展什么”；下方五个方向是展望素材。",
        "use": "放在 8.2 或 8.3。正文用它收束全文，不再引入新的实验结果。",
    },
    "table_8_1_conclusion_and_future_work": {
        "content": "该表把本文结论、主要证据和后续方向一一对应。",
        "read": "每一行都可以变成结论章的一段：先总结本文做了什么，再说明证据在哪，最后自然过渡到未来工作。",
        "use": "放在 8.1-8.3。适合直接作为结论章段落骨架。",
    },
}


def build_static_tables() -> dict[int, list[dict[str, str]]]:
    catalog = load_catalog()
    dataset_info = load_json(DATASET_INFO_PATH)
    coverage = safe_read_csv(COVERAGE_CSV)
    cls_metrics = load_json(CLS_RUN_ROOT / "metrics_summary.json")
    reg_metrics = load_json(REG_RUN_ROOT / "metrics_summary.json")
    cls_by_band = safe_read_csv(READINESS_DIR / "family_cv_classifier_by_band.csv")
    reg_by_band = safe_read_csv(READINESS_DIR / "family_cv_regressor_by_band.csv")
    topk = safe_read_csv(READINESS_DIR / "family_cv_topk_summary.csv")
    artifacts: dict[int, list[dict[str, str]]] = {i: [] for i in range(1, 9)}

    for chapter in range(1, 9):
        ensure_chapter(chapter)

    # Chapter 1
    root, fig_dir, tab_dir = ensure_chapter(1)
    fig = make_overall_framework(fig_dir)
    artifacts[1].append({"name": "图 1-1 本文 target-band 逆向设计总体框架", "path": str(fig), "kind": "figure", "note": "展示论文的五段式主线和三层逻辑。"})
    df = pd.DataFrame(
        [
            ["目标频带条件预测", "把结构与指定 band 共同作为输入", "第 4 章方法与第 6.3 节 readiness", "回答 predictor 是否有 shortlist value"],
            ["预测引导逆向设计", "用 predictor 排序并引导候选推进", "第 5 章 workflow 与第 6.4-6.6 节", "回答模型分数是否能转化为真实设计发现"],
            ["真实物理验证闭环", "Stage4 / COMSOL 对 shortlist 做最终确认", "第 6.7 节", "避免把 surrogate 结果误写成最终物理结果"],
            ["主线边界收口", "冻结 thesis band catalog 与 baseline 关系", "第 2、7 章", "让论文主张克制、可复现、可信"],
        ],
        columns=["工作点", "论文中的含义", "主要落点", "写作作用"],
    )
    _, md = write_table(df, tab_dir, "table_1_1_contribution_map")
    artifacts[1].append({"name": "表 1-1 本文主要工作与章节证据对应", "path": str(md), "kind": "table", "note": "绪论中概括创新点和后文证据链。"})

    # Chapter 2
    root, fig_dir, tab_dir = ensure_chapter(2)
    fig = make_problem_boundary(fig_dir)
    artifacts[2].append({"name": "图 2-1 目标频带逆向设计问题定义与边界", "path": str(fig), "kind": "figure", "note": "用于界定输入、输出、模型角色和真实验证边界。"})
    df = pd.DataFrame(
        [
            ["输入", "结构参数、shape descriptors、target band low/high/center/width", "来自 target-band parametric dataset"],
            ["中间输出", "打开概率、覆盖比例、overlap、shortlist score", "用于候选排序，不作为最终物理结论"],
            ["最终输出", "经过 Stage4 real validation 的可用 target-band 设计", "论文最终可信结果"],
            ["边界", "thesis band catalog、当前结构族、固定材料与求解配置", "防止过度宣称通用性"],
        ],
        columns=["对象", "内容", "论文解释"],
    )
    _, md = write_table(df, tab_dir, "table_2_1_problem_io_boundary")
    artifacts[2].append({"name": "表 2-1 问题输入输出与成立边界", "path": str(md), "kind": "table", "note": "放在问题定义小节，帮助读者先理解任务边界。"})
    df = pd.DataFrame(
        [
            ["truth production", "physics_pipeline/、stage1/、stage2/", "data/comsol_batch/", "物理真值来源"],
            ["target-band dataset", "run_build_parametric_targetband_dataset_v1.py", "targetband_parametric_v1.csv", "监督学习数据基础"],
            ["conditional predictor", "RF classifier + HGB regressor", "prediction_targetband_param_v1_runs/", "shortlist engine"],
            ["seed scoring / local refinement", "optimization/runners/", "data/ml_runs/targetband_*", "把预测分数转成候选推进"],
            ["real validation", "runners/run_stage4_validation_targetband_v1.m", "data/comsol_batch/stage4_validation_targetband_v1/", "最终物理确认"],
        ],
        columns=["论文术语", "代码入口", "权威输出", "在系统中的角色"],
    )
    _, md = write_table(df, tab_dir, "table_2_2_module_contract")
    artifacts[2].append({"name": "表 2-2 论文术语、代码入口与权威输出对照", "path": str(md), "kind": "table", "note": "系统框架章和附录命令表都可引用。"})

    # Chapter 3
    root, fig_dir, tab_dir = ensure_chapter(3)
    fig = make_shape_atlas(fig_dir)
    artifacts[3].append({"name": "图 3-1 典型结构族与参数化几何示意图", "path": str(fig), "kind": "figure", "note": "用真实 contour 文件展示结构族不是抽象变量。"})
    catalog_df = pd.DataFrame(catalog)
    if not coverage.empty:
        stats = coverage.rename(columns={"target_band_tag": "target_band_tag"})
        catalog_df = catalog_df.merge(stats, on="target_band_tag", how="left")
    keep_cols = [
        "target_band_tag",
        "band_low_Hz",
        "band_high_Hz",
        "label",
        "role",
        "rows_total",
        "positive_rows",
        "positive_rate",
        "positive_families",
        "cover_ratio_mean_positive",
        "reason",
    ]
    table3 = catalog_df[[c for c in keep_cols if c in catalog_df.columns]].copy()
    _, md = write_table(table3, tab_dir, "table_3_1_thesis_band_catalog_stats")
    artifacts[3].append({"name": "表 3-1 thesis band catalog 与样本统计", "path": str(md), "kind": "table", "note": "交代六个 thesis bands 的角色、样本覆盖和难度。"})
    if not coverage.empty:
        fig = make_band_coverage_figure(fig_dir, coverage)
        artifacts[3].append({"name": "图 3-2 thesis band catalog 覆盖度与正样本质量", "path": str(fig), "kind": "figure", "note": "用 positive rows 与 mean cover ratio 展示数据基础。"})
    df = pd.DataFrame(
        [
            ["总行数", dataset_info.get("rows", "")],
            ["unique designs", dataset_info.get("unique_designs", "")],
            ["unique families", dataset_info.get("unique_families", "")],
            ["默认数据集 tag", "windows_dense_v8_truth_plus_exploratory_aug_v1"],
            ["权威 CSV", str(Path(dataset_info.get("dataset_csv", "")))],
        ],
        columns=["指标", "值"],
    )
    _, md = write_table(df, tab_dir, "table_3_2_dataset_inventory", digits=0)
    artifacts[3].append({"name": "表 3-2 target-band 参数化数据集总览", "path": str(md), "kind": "table", "note": "给第三章数据基础一个可引用的总量说明。"})

    # Chapter 4
    root, fig_dir, tab_dir = ensure_chapter(4)
    fig = make_conditional_prediction_task(fig_dir)
    artifacts[4].append({"name": "图 4-1 面向目标频带的条件预测任务定义", "path": str(fig), "kind": "figure", "note": "解释分类器、回归器和 shortlist score 的任务拆分。"})
    copied = copy_if_exists(READINESS_DIR / "figures" / "family_cv_readiness_summary.png", fig_dir / "figure_4_2_predictor_readiness_summary.png")
    if copied:
        artifacts[4].append({"name": "图 4-2 predictor readiness 核心指标图", "path": str(copied), "kind": "figure", "note": "从既有 readiness 分析整理，用于展示 family-CV 总体表现。"})
    df = pd.DataFrame(
        [
            ["分类器", "Random Forest", "target_gap_is_open", "stratified_group_kfold", "shape_family", str(CLS_RUN_ROOT)],
            ["回归器", "HistGradientBoosting", "target_gap_cover_ratio", "stratified_group_kfold", "shape_family", str(REG_RUN_ROOT)],
        ],
        columns=["模型", "模型族", "预测目标", "评估方式", "分组键", "权威输出目录"],
    )
    _, md = write_table(df, tab_dir, "table_4_1_training_config")
    artifacts[4].append({"name": "表 4-1 分类器与回归器训练配置", "path": str(md), "kind": "table", "note": "方法章说明模型设置时直接引用。"})
    df = pd.DataFrame(
        [
            ["classifier accuracy", cls_metrics.get("accuracy_mean", "")],
            ["classifier precision", cls_metrics.get("precision_mean", "")],
            ["classifier recall", cls_metrics.get("recall_mean", "")],
            ["classifier f1", cls_metrics.get("f1_mean", "")],
            ["classifier balanced accuracy", cls_metrics.get("balanced_accuracy_mean", "")],
            ["regressor MAE", reg_metrics.get("overall", {}).get("mae", "")],
            ["regressor RMSE", reg_metrics.get("overall", {}).get("rmse", "")],
            ["regressor R2", reg_metrics.get("overall", {}).get("r2", "")],
        ],
        columns=["指标", "数值"],
    )
    _, md = write_table(df, tab_dir, "table_4_2_predictor_readiness_core_metrics")
    artifacts[4].append({"name": "表 4-2 predictor readiness 核心指标", "path": str(md), "kind": "table", "note": "支撑 predictor 已可作为 shortlist engine 的判断。"})
    if not cls_by_band.empty and not reg_by_band.empty:
        by_band = cls_by_band.merge(reg_by_band, on="target_band_tag", how="left", suffixes=("_cls", "_reg"))
        cols = ["target_band_tag", "positive_rate", "accuracy", "precision", "recall", "f1", "balanced_accuracy", "mean_true_cover", "mean_pred_cover", "mae"]
        _, md = write_table(by_band[[c for c in cols if c in by_band.columns]], tab_dir, "table_4_3_by_band_readiness")
        artifacts[4].append({"name": "表 4-3 thesis bands 逐 band readiness", "path": str(md), "kind": "table", "note": "解释不同目标频带难度和模型边界。"})
    if not topk.empty:
        _, md = write_table(topk, tab_dir, "table_4_4_topk_shortlist_quality")
        artifacts[4].append({"name": "表 4-4 top-k shortlist 质量", "path": str(md), "kind": "table", "note": "说明 predictor 的价值主要体现在排序前列候选质量。"})

    # Chapter 5
    root, fig_dir, tab_dir = ensure_chapter(5)
    fig = make_inverse_design_workflow(fig_dir)
    artifacts[5].append({"name": "图 5-1 prediction-guided target-band inverse-design workflow", "path": str(fig), "kind": "figure", "note": "第五章开头说明搜索与验证流程。"})
    fig = make_baseline_positioning(fig_dir)
    artifacts[5].append({"name": "图 5-2 主线与 baseline / 工程支撑的角色定位", "path": str(fig), "kind": "figure", "note": "避免把历史路线和正式主线混在一起。"})
    df = pd.DataFrame(
        [
            ["frozen target-band mainline", "正式论文主线", "条件预测 + shape-aware + local refinement + Stage4", "第 5 章重点展开"],
            ["generic prior / historical bridge", "baseline", "旧 seed discovery / v10/v11 线", "第 6 章对照解释，不作为默认主线"],
            ["band-catalog real GA", "真实搜索 baseline", "传统 COMSOL-in-loop 搜索", "用于说明预算和效率差异"],
            ["local robustness", "补充支撑", "围绕 canonical cases 的局部扰动分析", "可主文压缩，细节放附录"],
        ],
        columns=["路线", "论文身份", "主要内容", "使用方式"],
    )
    _, md = write_table(df, tab_dir, "table_5_1_mainline_vs_baselines")
    artifacts[5].append({"name": "表 5-1 主线与 baseline 路线定位对照", "path": str(md), "kind": "table", "note": "用于第五章或第六章实验设置前统一口径。"})
    df = pd.DataFrame(
        [
            ["seed scoring", "optimization/runners/run_targetband_seed_scoring_v1.py", "targetband_seed_predictions.csv", "预测器第一次进入候选排序"],
            ["local refinement", "optimization/runners/run_targetband_local_ga_v1.py", "targetband_ga_candidate_manifest_v1.csv", "把高分候选推向局部更优"],
            ["validation manifest", "optimization/runners/run_targetband_validation_manifest_v1.py", "targetband_ga_validation_manifest_v1.csv", "Python 到 MATLAB 的共享契约"],
            ["stage4 validation", "runners/run_stage4_validation_targetband_v1.m", "stage4_validation_results.csv", "真实物理结果落点"],
        ],
        columns=["步骤", "入口", "关键输出", "论文解释"],
    )
    _, md = write_table(df, tab_dir, "table_5_2_workflow_artifacts")
    artifacts[5].append({"name": "表 5-2 prediction-guided workflow 入口与输出", "path": str(md), "kind": "table", "note": "方法章和附录都可用。"})

    # Chapter 6
    root, fig_dir, tab_dir = ensure_chapter(6)
    copied = copy_if_exists(READINESS_DIR / "figures" / "family_cv_readiness_summary.png", fig_dir / "figure_6_1_predictor_readiness.png")
    if copied:
        artifacts[6].append({"name": "图 6-1 predictor readiness 结果图", "path": str(copied), "kind": "figure", "note": "补齐第六章图号，承接 6.3 节。"})
    for path in sorted((CH6_DIR / "figures").glob("figure_6_*.png")):
        if path.name != "figure_6_1_predictor_readiness.png":
            artifacts[6].append({"name": CH6_DISPLAY_NAMES.get(path.stem, path.stem.replace("_", " ")), "path": str(path), "kind": "figure", "note": "既有第六章结果图。"})
    for path in sorted((CH6_DIR / "tables").glob("table_6_*.md")):
        artifacts[6].append({"name": CH6_DISPLAY_NAMES.get(path.stem, path.stem.replace("_", " ")), "path": str(path), "kind": "table", "note": "既有第六章结果表。"})

    # Chapter 7
    root, fig_dir, tab_dir = ensure_chapter(7)
    fig = make_validity_scope(fig_dir)
    artifacts[7].append({"name": "图 7-1 方法成立范围与局限性边界", "path": str(fig), "kind": "figure", "note": "讨论章用于克制地界定论文主张。"})
    df = pd.DataFrame(
        [
            ["成立范围", "thesis band catalog 内", "六个冻结目标频带", "不要写成任意连续 band 已解决"],
            ["成立范围", "当前结构族与参数化表达", "shape_contours 与 v8 数据集覆盖的族", "不要泛化到任意拓扑结构"],
            ["成立范围", "固定材料和求解配置", "当前 COMSOL/MATLAB 配置", "材料变化需要重新验证"],
            ["局限性", "weak band 仍需数据加密", "尤其高频稀疏 band", "写成已实质推进，而非完全解决"],
            ["局限性", "predictor 不是最终求解器", "shortlist engine", "最终结论依赖 Stage4"],
        ],
        columns=["类型", "边界/局限", "证据或对象", "论文写法"],
    )
    _, md = write_table(df, tab_dir, "table_7_1_scope_and_limitations")
    artifacts[7].append({"name": "表 7-1 方法成立范围与局限性", "path": str(md), "kind": "table", "note": "讨论章最关键的边界表。"})

    # Chapter 8
    root, fig_dir, tab_dir = ensure_chapter(8)
    fig = make_conclusion_roadmap(fig_dir)
    artifacts[8].append({"name": "图 8-1 全文结论与后续工作路线图", "path": str(fig), "kind": "figure", "note": "结论章把贡献、边界和未来方向收束到一张图。"})
    df = pd.DataFrame(
        [
            ["物理真值与数据基础", "建立 target-band 数据集", "第 3 章 + 表 3-1/3-2", "扩大 truth harvesting"],
            ["条件预测", "形成可用于 shortlist 的 predictor", "第 4 章 + 第 6.3 节", "提升跨 band 泛化"],
            ["逆向设计 workflow", "完成预测引导搜索、局部细化和真实验证", "第 5-6 章", "扩展结构表示和工程约束"],
            ["论文主张边界", "明确 catalog 内成立，不夸大为通用求解器", "第 7 章", "更大 catalog 下重新冻结主线"],
        ],
        columns=["总结对象", "本文结论", "主要证据", "后续方向"],
    )
    _, md = write_table(df, tab_dir, "table_8_1_conclusion_and_future_work")
    artifacts[8].append({"name": "表 8-1 全文工作总结与展望对应", "path": str(md), "kind": "table", "note": "结论章可按此表逐段收束。"})

    return artifacts


def write_guides(artifacts: dict[int, list[dict[str, str]]]) -> None:
    chapter_titles = {
        1: "绪论",
        2: "问题定义与系统框架",
        3: "物理真值生产与目标频带数据基础",
        4: "面向目标频带的条件预测方法",
        5: "预测驱动的目标频带逆向设计方法",
        6: "实验设计与结果分析",
        7: "讨论与局限性分析",
        8: "结论与展望",
    }
    for chapter, items in artifacts.items():
        root = chapter_dir(chapter)
        index_lines = [
            f"# 第{chapter}章图表索引：{chapter_titles[chapter]}",
            "",
            f"本目录整理第 {chapter} 章论文写作可直接使用的图表素材。",
            "",
        ]
        guide_lines = [
            f"# 第{chapter}章图表使用说明：{chapter_titles[chapter]}",
            "",
            "这份说明按“图表内容、怎么看、论文中怎样使用”整理。写正文时优先引用本文件中的图名和解释口径。",
            "",
        ]
        for item in items:
            stem = Path(item["path"]).stem
            detailed = DETAILED_GUIDANCE.get(stem, {})
            content = detailed.get("content", item["note"])
            read = detailed.get("read", "先看它在本章中回答的核心问题，再看变量、流程或指标之间的相对关系；不要只摘单个数字，而要服务章节论证。")
            use = detailed.get("use", f"放在第 {chapter} 章对应小节首次提出该问题之后，用正文先说明为什么需要这张图或表，再用一到两段解释它支撑了什么结论。")
            index_lines.append(f"- **{item['name']}**")
            index_lines.append(f"  - 类型：{item['kind']}")
            index_lines.append(f"  - 路径：`{item['path']}`")
            index_lines.append(f"  - 备注：{content}")
            guide_lines.append(f"## {item['name']}")
            guide_lines.append("")
            guide_lines.append(f"- 文件路径：`{item['path']}`")
            guide_lines.append(f"- 内容：{content}")
            guide_lines.append(f"- 怎么看：{read}")
            guide_lines.append(f"- 论文中怎样使用：{use}")
            guide_lines.append("")
        (root / f"chapter{chapter}_artifact_index.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
        (root / f"chapter{chapter}_artifact_guide.md").write_text("\n".join(guide_lines) + "\n", encoding="utf-8")

    master = [
        "# 论文各章图表素材总索引",
        "",
        "本索引由 `prediction_targetband_param_v1/tools/build_thesis_chapter_artifacts_v1.py` 生成。",
        "每一章均有独立文件夹、`figures/`、`tables/`、索引文件和详细说明文件。",
        "",
    ]
    for chapter in range(1, 9):
        root = chapter_dir(chapter)
        master.append(f"## 第{chapter}章 {chapter_titles[chapter]}")
        master.append(f"- 目录：`{root}`")
        master.append(f"- 索引：`{root / f'chapter{chapter}_artifact_index.md'}`")
        master.append(f"- 说明：`{root / f'chapter{chapter}_artifact_guide.md'}`")
        for item in artifacts[chapter]:
            master.append(f"- {item['name']}：`{item['path']}`")
        master.append("")
    (ANALYSIS_DIR / "thesis_chapter_artifacts_index.md").write_text("\n".join(master), encoding="utf-8")


def main() -> None:
    set_plot_style()
    artifacts = build_static_tables()
    write_guides(artifacts)
    print(f"Wrote chapter artifacts under {ANALYSIS_DIR}")


if __name__ == "__main__":
    main()
