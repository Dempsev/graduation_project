from __future__ import annotations

# Archived in the public refactor because the original file is encoding-damaged.

import json
import shutil
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, Rectangle


ROOT = Path(__file__).resolve().parents[4]
ANALYSIS_DIR = ROOT / "data" / "analysis"
CATALOG_PATH = ROOT / "src" / "prediction" / "targetband_param" / "configs" / "thesis_band_catalog_v2.json"
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
        "闁绘せ鏅濋幃濠囨儑閻斿皝鍋撻懖鈺傛櫢濞存粠婀COMSOL / MATLAB",
        "Target-band\n闁轰胶澧楀畵渚€姊块崱妯尖偓顖氼嚈?,
        "闁哄鈧弶顐藉Λ鏉垮缁佹挳宕抽埡姒F + HGB",
        "濡澘瀚粊鏉戭嚕閺囩儐鍤ら柟鍏肩矌閸屸晿nshape-aware\nlocal GA",
        "Stage4 闁活亞鍠庨悿鍕殽瀹€鍐\n闁告瑯鍨抽弫銈囨媼閹规劦鍚€缁绢収鍠涢?,
    ]
    xs = [0.35, 2.85, 5.35, 7.85, 10.35]
    colors = ["#e8f2f7", "#eaf4e7", "#fff4d8", "#f7e8e5", "#e9e6f5"]
    for i, (x, label) in enumerate(zip(xs, labels)):
        draw_box(ax, (x, 2.35), 1.85, 1.35, label, fc=colors[i])
        if i < len(xs) - 1:
            draw_arrow(ax, (x + 1.85, 3.03), (xs[i + 1], 3.03))

    draw_box(ax, (0.45, 0.75), 3.25, 0.9, "truth layer\n濞ｅ洦绻嗛惁澶愬冀閸モ晩鍔柡澶堝劥閸ゆ粓鎯囬悢椋庢澖闁绘せ鏅濋幃濠勬媼閿涘嫮鏆?, fc="#f5f8fa", ec="#8aa4b5", fontsize=9)
    draw_box(ax, (4.75, 0.75), 3.25, 0.9, "model layer\n闁硅泛艌閳ь剚绮庣划銊╁几?+ 闁烩晩鍠楅悥锝嗭紣閹存繄鏁ㄩ柍銉︾箖濡惭呬焊閸曨偄鐓傞柛娆樺灡鐢挻鎯旇箛鎾崇€婚柡?, fc="#f5f8fa", ec="#8aa4b5", fontsize=9)
    draw_box(ax, (9.05, 0.75), 3.25, 0.9, "search layer\n闁硅泛锕ら埀顒佺懇閳ь剙顦扮敮瑙勬交濞戞ê鐓傞柣顏嗗枎閻ゅ嫭顨ュ畝鍐闂傚偆鍘鹃獮?, fc="#f5f8fa", ec="#8aa4b5", fontsize=9)
    ax.text(0.35, 4.25, "闁?1-1  闁哄牜鍓氶弸?target-band 闂侇偄妫楅幃婊呮媼閹规劦鍚€闁诡剝顔婄紞瀣浖閸℃浠?, fontsize=15, weight="bold", color="#17212b")
    return save_current(fig, fig_dir / "figure_1_1_overall_framework.png")


def make_problem_boundary(fig_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(11.5, 5.2))
    ax.set_xlim(0, 11.5)
    ax.set_ylim(0, 5.2)
    ax.axis("off")
    ax.add_patch(Rectangle((0.35, 0.45), 10.8, 4.25, fill=False, edgecolor="#465a69", linewidth=2.0))
    ax.text(0.55, 4.38, "閻犱胶鍎ら弸鍐箣閹邦喚褰岄弶鍫濇贡閺咁偊鏁嶅绀筫sis band catalog + 鐟滅増鎸告晶鐘诲矗閸屾稒娈堕柛鏍ㄧ墱缁劑寮搁崟顒侇棏 + 闁搞儱鎼悾楣冨级閹邦厽鐏?婵懓鍊借闂佹澘绉堕悿?, fontsize=12, weight="bold")

    draw_box(ax, (0.85, 2.8), 2.2, 1.0, "閺夊牊鎸搁崣鍝眓缂備焦鎸婚悗顖炲矗閸屾稒娈?shape 闁绘鎳撶欢娌憂闁烩晩鍠楅悥锝嗭紣閹存繄鏁ㄩ柛鏍ㄦそ濡?, fc="#eaf4e7")
    draw_box(ax, (3.75, 2.8), 2.1, 1.0, "闁哄鈧弶顐藉Λ鏉垮缁佺⒍nopen probability\ncover ratio", fc="#fff4d8")
    draw_box(ax, (6.5, 2.8), 2.0, 1.0, "闁稿﹥鐟╅埀顒€顦扮敮瑙勬交濞屾唫ranking/refinement", fc="#f7e8e5")
    draw_box(ax, (9.05, 2.8), 1.65, 1.0, "閺夊牊鎸搁崵鐠闁告瑯鍨堕悰娆戞嫚娴ｇ瓔鍟庨悹?, fc="#e9e6f5")
    for start, end in [((3.05, 3.3), (3.75, 3.3)), ((5.85, 3.3), (6.5, 3.3)), ((8.5, 3.3), (9.05, 3.3))]:
        draw_arrow(ax, start, end)

    draw_box(ax, (0.85, 1.15), 2.2, 0.85, "濞戞挸绉靛Σ鍛婄缂佹ê澹堢紓浣规尰閻庣棆n濞戞挸绉靛Σ鍛婄缂佹ê澹堥柡澶嬪姈閺?, fc="#f7f7f7", ec="#a0a0a0", fontsize=9)
    draw_box(ax, (3.75, 1.15), 2.1, 0.85, "predictor 闁哄嫮妫唍shortlist engine\n濞戞挸绉靛Σ绋啃ч崒婢帡宕抽妸锔界濞寸媴绲介幖?, fc="#f7f7f7", ec="#a0a0a0", fontsize=9)
    draw_box(ax, (6.5, 1.15), 2.0, 0.85, "local GA 閻犳劗鍠曢惌妤冧沪閳ь剟鏌堥妸锕€鑵归弶鈺傜煇n濞戞挸绉靛Σ鎼佸礂閵娿儳婀伴柡鍫氬亾濞村吋眉缁绘氨鎷?, fc="#f7f7f7", ec="#a0a0a0", fontsize=9)
    draw_box(ax, (9.05, 1.15), 1.65, 0.85, "Stage4 缂備焦鐟ラ崵鐠闁哄牃鍋撶紓浣哥墢婢у潡鎮堕崱娆屸偓妯兼媼?, fc="#f7f7f7", ec="#a0a0a0", fontsize=9)
    ax.text(0.35, 4.9, "闁?2-1  闁烩晩鍠楅悥锝嗭紣閹存繄鏁ㄩ梺顐㈡閹粎鎷嬮幑鎰靛悁闂傚偆鍣ｉ。鐣屸偓瑙勭煯缁犵喐绋夋惔銈囩彾闁?, fontsize=15, weight="bold")
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
    fig.suptitle("闁?3-1  闁稿繒顭堥悗椋庣磼閹惧鈧垶寮箛搴ｇ憿闁告瑥鍊归弳鐔煎礌閺嵮冩濞达絾娲滈妵姘跺箛韫囨挻绂?, fontsize=15, weight="bold", y=0.98)
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
    ax1.set_title("闁?3-2  thesis band catalog 閻熸洖妫涘ú濠冩償閿旇法鐟㈡慨婵撶稻閻楅亶寮甸鍐ㄧ獩闂?, fontsize=15, weight="bold")
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
    draw_box(ax, (0.5, 2.55), 2.4, 1.0, "缂備焦鎸婚悗顖炴偋閻熸壆绐橽n闁告垹濮崇紞宥夊矗閸屾稒娈禱nshape descriptors", fc="#e8f2f7")
    draw_box(ax, (0.5, 1.15), 2.4, 1.0, "闁烩晩鍠楅悥锝嗭紣閹存繄鏁ㄩ柡澶嗏偓鍙夘偨\nlow / high / center / width", fc="#eaf4e7")
    draw_box(ax, (4.0, 1.85), 2.4, 1.05, "闁哄鈧弶顐藉Λ鏉垮缁佹潙螣閳ュ磭鈧﹥nclassifier + regressor", fc="#fff4d8")
    draw_box(ax, (7.5, 2.55), 2.35, 1.0, "闁瑰灚鎸哥槐鎴濐潡閸屾粌鑺砛nP(open | s, band)", fc="#f7e8e5")
    draw_box(ax, (7.5, 1.15), 2.35, 1.0, "閻熸洖妫涘ú濠勬嫻閵娾晛娅ncover ratio / overlap", fc="#f7e8e5")
    draw_box(ax, (10.2, 1.85), 1.15, 1.05, "shortlist\nscore", fc="#e9e6f5")
    for start, end in [((2.9, 3.05), (4.0, 2.55)), ((2.9, 1.65), (4.0, 2.2)), ((6.4, 2.4), (7.5, 3.05)), ((6.4, 2.25), (7.5, 1.65)), ((9.85, 3.05), (10.2, 2.55)), ((9.85, 1.65), (10.2, 2.2))]:
        draw_arrow(ax, start, end)
    ax.text(0.45, 4.15, "闁?4-1  闂傚牄鍨归幃婊堟儎椤旂晫鍨煎Λ鐗堝灥閻㈩偊鎯冮崟顒佽拫濞寸姴鐖奸。鈺伱圭€ｂ晜宕查柛鏂衡偓宕囨毎濞?, fontsize=15, weight="bold")
    return save_current(fig, fig_dir / "figure_4_1_conditional_prediction_task.png")


def make_inverse_design_workflow(fig_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(14.0, 5.2))
    ax.set_xlim(0, 14.0)
    ax.set_ylim(0, 5.2)
    ax.axis("off")
    steps = [
        ("闁稿﹥鐟╅埀顒€顦伴惈?, "candidate pool\n缂備焦鎸婚悗顖炲籍?闁告瑥鍊归弳鐔虹矚濞差亝锛?),
        ("濡澘瀚粊瀵告嫚閸曨偄鐎?, "seed scoring\nP(open) x cover"),
        ("鐟滆埇鍨绘慨鎼佸箛閻旇櫣鍙€缂佹稒鐩埀?, "family-balanced\nshortlist"),
        ("閻忕偐鍋撻梺顔哄妿缁繘宕?, "local GA\nrefinement"),
        ("濡ょ姴鐭侀惁澶娿€掗崨顓炵", "manifest\nPython -> MATLAB"),
        ("闁活亞鍠庨悿鍕殽瀹€鍐", "Stage4 COMSOL\n闁绘せ鏅濋幃濠勬兜椤旀鍚?),
    ]
    xs = [0.35, 2.6, 4.85, 7.1, 9.35, 11.6]
    for i, (title, body) in enumerate(steps):
        draw_box(ax, (xs[i], 2.7), 1.75, 1.25, f"{title}\n{body}", fc=["#e8f2f7", "#fff4d8", "#eaf4e7", "#f7e8e5", "#f5f5f5", "#e9e6f5"][i], fontsize=8.5)
        if i < len(steps) - 1:
            draw_arrow(ax, (xs[i] + 1.75, 3.32), (xs[i + 1], 3.32))
    ax.add_patch(Rectangle((2.0, 0.85), 5.0, 0.9, facecolor="#fafafa", edgecolor="#a7a7a7", linewidth=1.2))
    ax.text(4.5, 1.3, "predictor 闁圭粯鍔掔欢鐢稿棘閻熺増鍊婚柟鎵櫐缁变即宕楅崼鐔风瑩閹兼潙楠忕槐婵嬪礃瀹ュ牏绠婚柛蹇嬪劤濠€锛勨偓鍦仦閹磭妲?, ha="center", va="center", fontsize=10)
    ax.add_patch(Rectangle((7.65, 0.85), 5.2, 0.9, facecolor="#fafafa", edgecolor="#a7a7a7", linewidth=1.2))
    ax.text(10.25, 1.3, "real validation 闁告劕鍟块悾楣冨嫉閳ь剛绱掗崼婵嗚濞ｅ洠鈧啿顔婇柨娑欑鑶╅柛銊ヮ儏閸ㄥ酣寮０浣虹憹闁哄嫷鍨卞〒鍓佺磼閸垻娉㈤柡?, ha="center", va="center", fontsize=10)
    ax.text(0.35, 4.65, "闁?5-1  prediction-guided target-band inverse-design workflow", fontsize=15, weight="bold")
    return save_current(fig, fig_dir / "figure_5_1_inverse_design_workflow.png")


def make_baseline_positioning(fig_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(11.5, 4.8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")
    rows = [
        (4.1, "闁告ê妫楄ぐ?baseline", "generic prior / old GA\n闁活潿鍔嬬花顒傛嫚鐎涙ɑ顫栭柡鍐勫棛鐔呯紒鎹愬劵閸忔﹢宕濆☉妤冪憿缂傚倸鎼ぐ?, "#f0f0f0"),
        (3.0, "闁告劘宕电划銊︾▔閼姐倕娈?, "target-band predictor + shape-aware + local refinement\n閻犱胶鍎ら弸鍐潰閿濆懐纭€濞戞捁宕甸崵?, "#eaf4e7"),
        (1.9, "闁活亞鍠庨悿鍕殽瀹€鍐", "Stage4 / COMSOL\n閻犳劗鍠曢惌妤呭嫉閳ь剛绱掗崼銏犫挅闁荤偛妫涢垾妯兼媼?, "#e9e6f5"),
        (0.8, "闂傚嫬瀚紞宥夊绩椤栨稒瀚?, "runbook / manifest / smoke checks\n閻犳劗鍠曢惌妤呭矗椤栨凹妲婚柣婊呭閳ь儸鍡╁殯闁?, "#fff4d8"),
    ]
    for y, left, right, color in rows:
        draw_box(ax, (0.6, y - 0.35), 2.0, 0.7, left, fc=color)
        draw_box(ax, (3.2, y - 0.35), 6.2, 0.7, right, fc=color, ec="#6f7f89")
        draw_arrow(ax, (2.6, y), (3.2, y), color="#6f7f89")
    ax.text(0.5, 4.75, "闁?5-2  濞戞捁宕甸崵搴㈢▔?baseline / 鐎规悶鍎抽埢濂稿绩椤栨稒瀚奸柣銊ュ椤鎳濋幓鎺旀毎濞?, fontsize=15, weight="bold")
    return save_current(fig, fig_dir / "figure_5_2_mainline_baseline_positioning.png")


def make_validity_scope(fig_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(9.5, 6.0))
    ax.set_xlim(0, 9.5)
    ax.set_ylim(0, 6)
    ax.axis("off")
    boxes = [
        ((0.9, 4.1), 7.7, 1.0, "闁瑰瓨鍔楅悵娑㈡嚑閸愩劍绾?1闁挎稒顒甴esis band catalog 闁告劕鎳愬▓鎴︽儎椤旂晫鍨煎Λ鐗堝灥閻㈩偆鎷犻柨瀣勾", "#eaf4e7"),
        ((1.4, 3.0), 6.7, 0.85, "闁瑰瓨鍔楅悵娑㈡嚑閸愩劍绾?2闁挎稒鑹剧紞瀣礈瀹ュ懎妫橀柡浣规緲鐎佃尙绱掗幘瀵糕偓顖炲籍韫囧海鐟?shape-aware 闁稿﹥鐟╅埀顒€顦伴悗顖炴焻?, "#e8f2f7"),
        ((1.9, 2.0), 5.7, 0.75, "闁瑰瓨鍔楅悵娑㈡嚑閸愩劍绾?3闁挎稒鑹惧ù鎰偓瑙勭濞兼寮▎鎾冲赋缂傚喚鍠曠粭宀冦亹閹惧啿顤呴柣妞绘櫇閹﹤效閸屾粳鎺旀媼閸撗呮瀭", "#fff4d8"),
        ((2.4, 1.1), 4.7, 0.65, "闁哄牃鍋撶紓浣哥墢閳ユ鎷嬮妶蹇曠獥Stage4 real validation", "#e9e6f5"),
    ]
    for xy, w, h, text, color in boxes:
        draw_box(ax, xy, w, h, text, fc=color, ec="#476270")
    ax.text(0.6, 5.55, "闁?7-1  闁哄倽顫夌涵鍫曞箣閹邦喚褰岄柤鐓庡暙濞叉寧绋夋惔锛勬拱闂傚嫭鍔栭埀顑棛鐝堕柣?, fontsize=15, weight="bold")
    ax.text(0.9, 0.45, "闁告劖鐟ょ紞鏃傛啺娴ｅ搫浠柨娑欎亢缁旂喖鎮惧畝鍐ㄦ繛鎾虫噺椤ㄧ喖鏁嶅畝鍐惧晥闁哄倸娲ｇ€靛苯顕ｉ悩铏剐ㄩ柛娆樺灟娣囧﹪鏁嶅☉妤冪憹閻熸洑鐒︽俊?predictor 闁告劖鐟﹂崹姘舵焻濮樿鲸鏆忛柣妞绘櫇閹﹤效閸屾粳鎺楀闯閵婏絺鍋?, fontsize=11, color="#38454f")
    return save_current(fig, fig_dir / "figure_7_1_validity_scope.png")


def make_conclusion_roadmap(fig_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(12.0, 4.9))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 4.9)
    ax.axis("off")
    draw_box(ax, (0.45, 2.65), 2.05, 1.0, "鐎瑰憡褰冮悾顒勫箣閹单闂傚偆鍘鹃獮?workflow", fc="#eaf4e7")
    draw_box(ax, (3.0, 2.65), 2.05, 1.0, "鐟滅増鎸告晶鐘垫嫻閿涘嫬鐩€\ncatalog 闁告劕鎳庤ぐ鍙夘殽瀹€鍐闂侇偄妫滈?, fc="#e8f2f7")
    draw_box(ax, (5.55, 2.65), 2.05, 1.0, "鐟滅増鎸告晶鐘虫綇閸︻厽娅昞n闂傚牏鍋橀幑銏ゅ箛?band / 闂傚牏鍋橀幑銏ゅ箛韫囨洜娉㈤柡?, fc="#fff4d8")
    draw_box(ax, (8.1, 2.65), 3.25, 1.0, "闁哄牜浜濆鐢稿箥閳轰胶娼擻n闁哄洦娼欓妵?catalog / 闁哄洨绻濈挧瀵糕偓闈涚灱缁劑寮?/ 闁哄洦娼欏鍗炩枖濞戞ê顕?, fc="#f7e8e5")
    for start, end in [((2.5, 3.15), (3.0, 3.15)), ((5.05, 3.15), (5.55, 3.15)), ((7.6, 3.15), (8.1, 3.15))]:
        draw_arrow(ax, start, end)
    topics = ["闁圭鏅涢妵鍥儎椤旂晫鍨煎Λ鐗堝灥閻㈩偊鎯勯鑲╃Э", "闁告梻濮村?weak-band truth harvesting", "闁圭粯鍔曞畷宀€鎹?band 婵炲绋戠€?, "闁圭鏅涢惈宥囩磼閹惧鈧垳鎮伴妸褋浠涢柤瀹犳婵?, "闁规亽鍎遍崣鍡涘即閺夋垹鏆氶柡浣规綑娴兼劗绮欑€ｎ亝绨氶柡?]
    for i, topic in enumerate(topics):
        draw_box(ax, (0.55 + i * 2.25, 1.0), 1.8, 0.65, topic, fc="#fafafa", ec="#9aa8b0", fontsize=9)
    ax.text(0.45, 4.35, "闁?8-1  闁稿繈鍔嶉弸鍐磼閹捐鍟堝☉鎾抽閹绱掗鐐扮矗濞达絾绮忛惌鍓х棯閸喗绂?, fontsize=15, weight="bold")
    return save_current(fig, fig_dir / "figure_8_1_conclusion_roadmap.png")


def copy_if_exists(src: Path, dst: Path) -> Path | None:
    if not src.exists():
        return None
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return dst


CH6_DISPLAY_NAMES = {
    "figure_6_2_canonical_cases": "闁?6-2 canonical inverse-design cases 闁活亞鍠庨悿鍕磼閹惧浜柛?,
    "figure_6_3_baseline_comparison": "闁?6-3 baseline comparison 閻庨潧婀遍崣搴ㄥ炊?,
    "figure_6_4_weak_band_dashboard": "闁?6-4 weak-band coverage / shortlist 濞寸姴鍢查埀顒傚帶濞?,
    "figure_6_5_stage4_validation": "闁?6-5 stage4 real validation 缂備焦鎸婚悘澶岀磼閻旀椿鍚€闁?,
    "figure_6_6_local_robustness": "闁?6-6 local robustness 闁告帒妫欓悗浠嬪炊?,
    "table_6_1_experiment_lines": "閻?6-1 闁稿繈鍔戦崕瀵糕偓鍦仱閻涙瑧鐥径鍝ョ憿濞达絾绮庨弫銈団偓瑙勭煯缂?,
    "table_6_2_canonical_cases": "閻?6-2 canonical inverse-design cases 婵懓娲﹂埀?,
    "table_6_3_baseline_comparison": "閻?6-3 baseline comparison 婵懓娲﹂埀?,
    "table_6_4_stage4_validation": "閻?6-4 stage4 real validation 婵懓娲﹂埀?,
    "table_6_5_local_robustness_summary": "閻?6-5 local robustness 婵懓娲﹂埀?,
}


DETAILED_GUIDANCE = {
    "figure_1_1_overall_framework": {
        "content": "閺夆晜鐟ョ槐鍫曞炊閻愵剙惟闁稿繈鍔嶉弸鍐╃▔閼姐倕娈犻柛妯侯儑缂傚骞嬮幇顏嗗畨濞戞搩浜ｇ换娑氱磼椤撶唽渚€宕稿Δ瀣獥闁绘せ鏅濋幃濠囨儑閻斿皝鍋撻懖鈺傛櫢濞存籂浣插亾娑旂嘲rget-band 闁轰胶澧楀畵渚€姊块崱妯尖偓顖氼嚈閹巻鍋撴担瑙勮拫濞寸姴鐖奸。鈺伱圭€ｎ亝鐝ら柕鍡曠窔椤ｂ晛霉鐎ｎ亞绌块悗闈涘悑閹磭妲愰姀鐘冲 Stage4 闁活亞鍠庨悿鍕殽瀹€鍐闁挎稒绋愮粭鍛村棘闁稓鐟忛悘鐐插€归悥锝呪枖閵婎煈鍤涢柡?truth layer闁靛棔娌無del layer闁靛棔澶焑arch layer 闁汇劌瀚～妤呮嚌閹绘帒鐎荤€规悶鍎埀?,
        "read": "濞寸姴楠告稊蹇涘触閹存繂绀侀柣顏勵儐閺嗙喖骞戦鍏煎閻犲洣鐒﹀畵浣逛繆閸屾瑧绉挎繛缈犵婵晠鏁嶅顒€顤呭☉鎾卞€栭鐐哄炊閻愮數鎽曢柍銉︾矌濠€锟犲磹閻撳孩瀚查柡浣哄瀹撲焦绂掓惔鈩冩喛闂佹彃鏈鐢稿灳濠垫挾绀夊☉鎿冨弮濡寧绋夐埀顒€顫㈤妷銉︾缂佹稒鏌￠埀顒佺redictor 濠碘€冲€风紞宥夊箣閹邦亣绀?shortlist engine闁炽儲绻愮槐婵嬪触鎼存繆鈷堟慨婵勫劚濞叉牜绮甸弬琛″亾濠婂啠鍋撳▎鎾亾婢跺娲ゅù锝嗘礉椤箓骞掗妸銊х妤犵偞鍎奸～锕傛儑閻旈鏉介柣妞绘櫇閹﹦娑甸娆惧悋闁炽儲绺块埀?,
        "use": "闁衡偓閹勮含 1.4 闁瑰灈鍋撻柡鍫灥閻墽鐥幐搴＄仐 1.5 濞戞挻妲掗々锕€顔忛妷銈囩▕濞戞柨顑呮晶鐘绘晬瀹€鈧弫銈夊级閵夛箑绲归柛鎾崇Т缂傛挾绮╃€ｎ亜寮块柡鍌氭搐瑜板﹥绂嶇€ｃ劉鍋撻崒娑卞妧闁哄倸娲ｇ粭澶屾啺娴ｅ摜娼旂€殿喒鍋撻柡浣规緲閳ь剛銆嬬槐婵嬫煂瀹ュ洤浠悹鍥х摠濡叉垿寮甸浣圭€☉鎾崇У濡叉悂宕￠弴鐔屼線宕圭€ｎ収鍟堥柡鍌氭祫缁辨繈鎳撶仦鐐﹀☉鎾亾闁哄绻濆Λ鎾偝?workflow闁?,
    },
    "table_1_1_contribution_map": {
        "content": "閻犲洢鍎撮妴鍐箮婵犲嫬宕曢悹浣芥〃閼垫垿鎯冮崟顏勭槣閻熸洑绀佹导鎰媴濠婂懎浠柡鍕Т閻ㄧ娀宕氶弶鎸庡€甸柡鍌氭川閻濈兘鎳為崒姘閻犲洣鐒﹀畵渚€寮堕妷锔剧埍闁挎稑鑻€垫﹢骞忛浣硅拫濞寸姴鐖奸。鈺伱圭€ｃ劉鍋撴笟鈧。鈺伱圭€ｎ亞绌块悗闈涖偢閳ь剙妫楅幃婊呮媼閹规劦鍚€闁靛棔鑳跺﹢锛勨偓鍦仧婢у潡鎮堕崱娑氬矗閻犲洣绀侀幏鐗堢▔閼姐倕娈犻弶鍫濇贡閺咁偊寮ㄧ捄鍝勭稉闁?,
        "read": "闁圭顦埀顒佺矊娴兼劖鎷呭鍛化 -> 閻犱胶鍎ら弸鍐触椤愶紕鐤?-> 濞戞挻妲掗々锕傛媰閻ｅ苯浠?-> 闁告劖鐟ょ紞鏃€鎷呭鍛殢闁炽儲绻堝Σ鍕嫚娴兼瑧绀夌痪顓у枦椤撹袙韫囧酣鍤嬮柛鎺撶⊕閺屽﹪鎮欓悷鐗堝€甸梻鍫涘灲閸忔﹢寮垫径濠勬澖濡ょ姴鏈崹銊╁棘鐟欏嫮銆婄紒鏃傚Ь婵☆參寮ㄩ娑欏闁?,
        "use": "闂侇偄鍊搁幃搴ㄥ绩閹勮含 1.5 濞戞挻妲掗々锕€顔忛妷銈囩▕濞戞挸楠搁崹閬嶅棘閹殿喖浠柛姘嚱缁辨繃鎷呭鈧拹鐔煎礆濞戞瑦鐓€闁绘劕婀卞▓鎴犳嫚娴ｇ懓绁﹂悗浣冨閸╁懐鎮伴妸锝傚亾閸屾艾鏅稿ù锝嗙矋濡炲倿宕ｉ鐐╁亾閹邦垼鏀介弶鐑嗗墯閸ㄦ岸宕跺☉妤呭殝閻犳劧绱曠亸鐐测枔娴ｅ啯鍎伴柕?,
    },
    "figure_2_1_problem_boundary": {
        "content": "閺夆晜鐟ョ槐鍫曞炊閹呮毎濞戞柨顦卞ú浼村冀閸ヮ剦鏆ラ悽顖ょ畵閳ь剙妫楅幃婊呮媼閹规劦鍚€闂傚偆鍣ｉ。浠嬫儍閸曨喚缈婚柛蹇嬪劘閳ь兛鐒﹁啯闁搞劌顑勯懙鎴︽⒒绾惧缈婚柛鎴炰航閳ь兛绀侀埀顒佺懇閳ь剙顦扮敮瑙勬交濞戞ɑ瀚查柡鍫氬亾缂備礁鐗嗚ぐ鍙夘殽瀹€鍐閻犱焦宕橀鎼佹晬鐏炶姤鍊遍柡鍐煐婵℃悂骞嬮幇顔惧綄閺夊牆婀遍弲顐㈩浖閸℃韬?thesis band catalog 濞戞挸楠哥紞瀣礈瀹ュ洨娉㈤柡瀣濡矂宕橀崨顐熷亾?,
        "read": "闂佹彃绉堕崑锝夋儑鐎ｎ兛绱楅柤纭呭蔼缁旂喖鎮剧仦缁㈡敱闁告粌濂旂粭鍛村棘瑜版帗顎欓柛鎺撳劶椤曗晠寮版惔顖滅獥predictor 闁告瑯浜ｇ粈瀣嫻閿濆棗绗撻幖鏉戠箣缁楀瞼绮靛☉鈶╁亾婢舵稓绀塖tage4 闁归潧绉风粈瀣嫻閿濆棙浠樼紓浣哥墢婢у潡鎮堕崱娆屸偓妯兼媼閵堝啠鍋?,
        "use": "闁衡偓閹勮含 2.1 闁?2.2闁挎稑鐬奸弫銈夊级閵夆晜些婵縿鍨奸浼存嚀閸涱喖惟濞寸姾顕ф慨鐔兼偠閸℃鎺楀箣閹般劉鍋撳鈧幑銏ゅ箛韫囨洜娉㈤柡瀣閹广垽骞囪箛娑辨殽閻㈩垽濡囧▓鎴︽焻濮樿鲸鏆忛梺顐㈡閹粎鎷嬮幑鎰靛悁闁炽儲绺块埀?,
    },
    "table_2_1_problem_io_boundary": {
        "content": "閻犲洢鍎撮妴鍐偨閵婏附鐎柡鍫墮閼告澘顕ｈ箛鎾崇仚闁告垿缂氱欢顓㈠礂閵夛絺鍋撴担鐤幀闂傚倻顥愮欢顓㈠礄閹巻鍋撴担瑙勪粯缂備礁鐗愮欢顓㈠礄閸濆嫭瀚查弶鍫濇贡閺咁偊鏁嶇仦鐐﹂柛?2-1 闁汇劌瀚ぐ鎻掝嚕閺囩姵鏆忛悶娑栧妽閻楁悂鎮ч崼娑掑亾?,
        "read": "闁绘鎳撻崺鍡椻枖閵婏箑澹堥柍銉︾矆閼垫垿姊荤壕瀣炕闁告垼銆€閳ь剚绻傞幏浼村灳濠婂嫭浠樼紓浣哥墣缁额參宕欑悰鈾€鍋撳┑鍫熺暠闁告牕鎼崺鍡涙晬濮橆収娲ら柣婊冩储閳ь兛鎭璷ver ratio 闁?shortlist score 濞戞挸绉靛Σ鎼佸嫉閳ь剛绱掗崼銏犫挅闁荤偛妫涚划銊ф媼閹巻鍋?,
        "use": "闁衡偓閹勮含闂傚偆鍣ｉ。鐣屸偓瑙勭煯缁犵喐绋婄€ｎ亝鍊甸柨娑樻湰椤掓粓寮崶褍璁查柟绋款槸濞叉挾鎮扮仦钘夌€婚柛鎺濆亯琚欓梺鎻掞龚缁额參宕楅妷褉鏁勯梻鍌涚暘閳ь兛鑳跺ú浼村冀閸パ冩瘣闁轰浇鍩囬埀顑挎祰缁额參宕欓崫鍕煂闁诡兛绀侀幏浼存⒔閹邦剙鐓戦柡澶嗏偓鍙夘偨闁?,
    },
    "table_2_2_module_contract": {
        "content": "閻犲洢鍎撮妴鍐箮婵犲拋鍟堥柡鍌氭处濠€宕囨嫚椤撶儐鍤犻幖瀛樻煥閸╁矂鎯囬悢椋庢澖濞寸媴绲块悥婊堝礂閵夈儱缍撻柛婊冩湰濞煎牊绻涙担鐣岀炕闁告垼娅ｅú鎷屻亹閺囶亞绀夐悷鏇炴濞?truth production闁靛棔榫歛taset闁靛棔鍨edictor闁靛棔澶焑ed scoring闁靛棔鍕緊cal refinement 闁?real validation闁?,
        "read": "閻犲洦妲掗妴鍐籍閸撲焦绠欐慨锝呯箣闁叉粓寮甸婵愬殧闁哄嫷鍨伴幆渚€寮垫径瀣潠缁绢収鍠氬▓鎴﹀礂閵夈儱缍撻柛婊冪焷缁额參宕欓悮瀵稿耿閺夆晜鐟ㄩ崗妯兼嫚娴ｈ顫栭悹浣哄劋閺嬪啯绋夊鍡樞﹂柟璺衡偓鐔绘澖闁哄倽顫夌涵鍫曟晬瀹€鍐ｅ亾鐏炵偓笑濞寸姵鎸哥花杈ㄧ▔椤撶偛璁插璺虹Ф楠炲洭鎯冮崟顒傘偊缂佸顑冮埀?,
        "use": "闂侇偄鍊搁幃搴ㄥ绩閹勮含 2.3 缂侇垵宕电划鍝勵浖閸℃浠搁柨娑樺缁″啴宕ｉ姘含闂傚嫬瀚紞?C 濠㈣泛绉堕弫銈夊Υ閸屾侗鍔€闁哄倸娲ｉ懙鎴︽偨閵娿儳鏆婇柡鈧娑欏闁炽儲绮堢€靛瞼鐥幐搴㈡毆闁告瑱绲洪埀顒佺箓閹蜂即鍨惧鍐ㄨ濠㈣泛绉堕獮鍥箑瑜夐埀顒佺缚閳?,
    },
    "figure_3_1_shape_family_atlas": {
        "content": "閺夆晜鐟ョ槐鍫曞炊閸欍儳鐭?`data/shape_contours` 閻犲洩顕цぐ鍥儑閻旈鏉?contour 闁哄倸娲ｅ▎銏ゆ晬鐏炵晫娼旂紒鈧崫鍕倎闁?shape family 闁汇劌瀚崵鎴炴媴閺囩偠鍩岄柟顑跨筏缁辨繈宕犻崨顔碱仾闁告艾娴烽悽?canonical cases 濞戞搩鍘烘繛鍥偨閵娧勭暠 ep193闁靛棔韬琾248闁靛棔韬琾253 缂佹稑顦辩划銊╁几閸曗斁鍋?,
        "read": "濞戞挸绉烽々锕傚箮婵犲倻鏆婄憸鐗堟尫缂嶆棃骞€瑜戦崗姗€宕堕幘鍛耿閻庣懓鍟板▓鎴炴媴濠婂懏鏆忛柡鍕靛灥椤斺偓閻犲洦妲掗埀顒€鎳愬ú璺ㄦ喆閸屾粍绠欓柛?shape family 濞戞挸楠稿顒勫极閺夊灝顕ч柛鎴犲С缂嶅秹鎯冮崟顐ゆ澖闂傚嫬鎳庨懜浼村箑娓氬﹦绀夐柣鐐叉琚欑紓浣规尰閻庮垶寮箛鎾粹枙鐎殿喖鍊瑰Σ鎼佹儑閻旈鏉介悗娑櫭﹢顏堟儍閸曗斁鍋?,
        "use": "闁衡偓閹勮含 3.1 闁告瑥鍊归弳鐔煎礌閺嶎偆娉㈤柡瀣閵嗗啰绮堥崫鍕瘓闁煎搫鍊堕埀顒€鍊归婊堝棘閸パ冨弗閻犲洤鐡ㄥΣ鎴炴交濞嗗海鏄?contour 闁哄嫷鍨辫啯闁搞劌顑堢欢顓㈠礂閵壯冾棗鐎甸妞掔粭宀勫触鎼达絿鏁鹃柣妞绘櫇閹﹥顨ュ畝鍐闁汇劌瀚崣锟犲触鐏炶棄娈ゅù锝嗘礀閻斺偓缁绢厸鍋撻柕?,
    },
    "figure_3_2_band_catalog_coverage": {
        "content": "閺夆晜鐟ョ槐鍫曞炊閻愵剙惟闁稿浚鍘洪柌?thesis bands 闁?positive rows 闁告粌鏈婊堝冀闁垮鎷?mean cover ratio 闁衡偓閹勮含闁告艾濂旂粩鏉戭嚕閻樺弶绂堝☉鎿冨弿缁辨繄浠﹂弴鐘粵闁轰胶澧楀畵浣烘啺閸℃瑦纾伴梺鎻掔箣缁楀苯顫㈤敐鍡欏闁哄牜鍓濆婵嬫煂韫囨捁瀚欏☉鎾崇Т閻ｎ剟宕楅妸銈囶伇闁奸攱鐣埀?,
        "read": "闁藉啯绻嗘竟濠囧蓟閸楃偟鎽嶉柣顏勵儐椤掓粓寮介柨瀣嫳闁轰椒鍗抽崳娲晬鐏炵虎鐓婚柤鐟板级婵瞼鐥捄銊︾畽妤犵偛鍟垮搴ｆ啺閸℃瑦纾伴悹鎰╁姂閸ｆ椽鏁嶅☉妯烩偓?band 闁汇劌瀚ú鍫曟⒕妤ｅ啠鍋撳顒傚煑濞达絾鎸鹃獮鍥捶閵婎煈娲柣鈺傜墳瀹告繈鏌岃箛瀣у亾娴ｈ　鏋呴柣銈呯箲閳ь儸鍕仐閻炴稏鍎遍崢鏍ㄥ濡搫甯ョ紒鐙欏倻鐟愰柕?,
        "use": "闁衡偓閹勮含 3.4 闁?3.5闁挎稑鐬奸弫銈夊级閵夈剱鎺楁煂婵犱浇绀嬪ù鐘亾濞戞柨鐗嗛幃妤冪磼椤撱垺浠橀悷?predictor readiness闁靛棔绨歟ak-band 闁告帒妫欓悗浠嬪椽瀹€鈧﹢锛勨偓鍦仱閻涙瑧鎷犳笟濠勭闁兼澘濂旂粭澶愬及椤栨艾娑ч柣顏勵儐閺嗙喖骞戦鈧崳娲Υ?,
    },
    "table_3_1_thesis_band_catalog_stats": {
        "content": "閻犲洢鍎撮妴鍐ㄐч崶銊㈠亾鐠囨彃褰嬪☉?thesis bands 闁汇劌瀚伴。鍫曟偝閸ヮ亜鐦遍柛銉︾暘閳ь兛娴囬～妤呮嚌鐏炲倵鍋撴担鍦闁哄牜鍓氶埀顒傜帛閺嗙喖濡存担璇″妧闁哄秹鏀卞﹢浼村极閼割兘鍋撴担璇″妧闁哄秹鏀卞﹢浼存偝閸ャ儮鍋撴稊绔渟itive families 闁告粌鑻柦鈺呭锤?cover ratio闁?,
        "read": "濞村吋锚閸樻盯鎯?role闁靛棔鍨sitive_rate闁靛棔鍨sitive_families 濞?cover_ratio_mean_positive闁挎稒鑹鹃悾鐘崇椤掆偓閸欙繝宕ュ畝鍐惧殯闁哄嫬瀛╅惁鈩冪▔?band 闁革负鍔忛鎴﹀棘閸ワ箒鍘柣銊ュ闂娾晜绂掗挊澶嬪闂傚懏鍎崇€规娊濡?,
        "use": "闁衡偓閹勮含 3.3 target-band 闁轰胶澧楀畵渚€姊块崱妯尖偓顖氼嚈閸濆嫮姣堥柤鍝勫亰缁辨繈寮伴婊庡剳濞戞挸顦遍悵鐑藉嫉閳ь剟寮界粙璺ㄥ闁汇劌瀚弳鐔煎箲椤旇￥鈧啴濡撮崒娑卞妧闁哄倸娲よぐ鏌ユ焻?band 閻熸瑱缍侀崳瀛樼▔鏉炴壆鐭嗗☉?`band180_220` 闁?showcase闁挎稑鐭侀埀顒€鐭傞悵顔斤紣?bands 闁哄嫷鍨伴幀?band 闂佹彃绉堕崑锝夊Υ?,
    },
    "table_3_2_dataset_inventory": {
        "content": "閻犲洢鍎撮妴鍐磼濞嗗繐姣?v8 target-band 闁告瑥鍊归弳鐔煎礌閺嶃劍娈堕柟璇″櫍濞夛箓鎯冮崟顑藉亾閺勫浚鏀介柡浣藉焽閳ь兛鑿噉ique designs闁靛棔鑿噉ique families闁靛棔绶氱划顖滄媼閵堝棙娈堕柟璇″櫍濞?tag 闁告粌鏈鍫熺箾?CSV 閻犱警鍨扮欢鐐哄Υ?,
        "read": "閻庣懓鍟ú鏍驳閺傝　鍋撳鍡╁敳缂備礁鍟幏浼村礆閸℃鈧粙宕氶弶璺ㄤ亢闁糕晞妗ㄧ花顒勫传椤忓啴鍤嬮柡浣哄瀹撲線姊块崱鎰ㄥ亾娴ｇ瓔娼愭俊顖椻偓鎰佹▼濠㈠爢鈧埀顒佺缚閳?,
        "use": "闁衡偓閹勮含 3.2 闁?3.4闁挎稑鐬奸弫銈嗘媴濠婂嫭娈堕柟璇″枛閻斺偓缁绢厸鍋撻柟顒佹椤秹鏁嶅☉婊庡殜缂備礁妫楅悺褍鈻撻棃娑樿闁衡偓妤ｅ啯顎嶇憸鐗堟穿缁辨繂顫㈤敐鍡樼€ǎ鍥ㄧ箘閺嗏偓闁诡剙顭烽崳娲椽瀹€鍐唴鐎垫澘瀚畵鍡涘矗椤栨ǚ鍋?,
    },
    "figure_4_1_conditional_prediction_task": {
        "content": "閺夆晜鐟ョ槐鍫曞炊閻愵剙惟闁哄鈧弶顐藉Λ鏉垮缁佹挳骞忛崱妯虹亣缂備焦鎸婚悗顖炴偋閻熸壆绐欓柕鍡曡兌濞蹭即寮介崶顒夋殽閻㈩垽闄勫顖涚闊祴鍋撴担绋跨€荤紒顐ヮ嚙濞呮帗娼忛幘鍐叉瘔闁靛棔绀佸ú鏍亹閹烘垶鐝ら弶鍫熸尭閸ゎ參宕仦鐐粯缂?shortlist score闁?,
        "read": "闁稿繑濞婇弫顓㈠及椤栨粍绠欓柣鈺婂枟閻栵絾锛愰幋婵堟暔闁哄鈧弶顐介弶鈺傜☉閸欏棗螣閳ュ磭鈧攱娼忛幘鍐插汲闁挎稑鐭侀埀顒€濂旂粭澶愬及椤栨繍鍞茬紓浣稿暕缁斿瓨绋夐鍛骏闁哄鈧弶顐界紓浣规尰閻庮垶骞€瑜戦崗妯伙紣閸曨剛銈撮柛锝庣厜缁辫鲸娼诲▎蹇旂殤闁?target-band-conditioned 闁汇劌瀚悧瀹犵疀閸愶腹鍋?,
        "use": "闁衡偓閹勮含 4.1 濞寸姾顕ф慨鐔衡偓瑙勭煯缁犵喓浜歌箛姘濋柨娑樼灱閺併倗鈧懓鍟槐鈺呭礄閸濆嫬鐎荤紒顐ヮ嚙濞呮帡宕仦鑺ョ鐟滅増甯掑▍鎺撶▔鏉炴壆鐭嗗☉鏂跨墣椤╋箓鐛幆閭︽斀閻庢稒锚濠€顏堝Υ?,
    },
    "figure_4_2_predictor_readiness_summary": {
        "content": "閻犲洢鍎卞ù姗€寮堕妷銊ユ闁哄啨鍨哄﹢?predictor readiness 闁告帒妫欓悗浠嬫晬鐏炲墽婀介柟?family-CV 濞戞挸顑呴崹搴ｇ尵濮瑰洠鍋撴担鍛婄鐟滅増甯囬埀顑胯緶op-k shortlist 缂佹稑顦伴悧瀹犵疀閸愵厹鈧啴鎮抽懜顑藉亾?,
        "read": "濞戞挸绉烽々锕傚矗椤忓棙绠?accuracy闁挎稒绋戠花鏌ュ触鐏炵偓顦ч柣?balanced accuracy闁靛棔绀佸ú鏍亹閹烘洦鍤栫€瑰壊鍠栭幏?top-k cover lift闁挎稑鑻ú婊勭▔?predictor 闁汇劌瀚鎴﹀棘閸ヮ亶娼￠柤鐟板级濡叉悂骞掗幒鎴犵闁告挸绉堕顒勫Υ?,
        "use": "闁衡偓閹勮含 4.4 闁哄倽顫夌涵鍓佹嫚閸曨亞骞嗛柟瀛樼墱椤?6.3 缂備焦鎸婚悘澶屼焊韫囨艾螡闁秆冩搐瑜版煡濡撮崒婊庡剳闁搞儲绋撻悵閿嬫媴鐠恒劍鏆忛柡鍐硾娴滄悂寮憴鍕€婇柡鍫濐槹閺呫儵骞€瑜濈槐婵堢箔椤掆偓閸欐氨绮╅悩鍗炩枏闁活潿鍔嶅鍌炲磻韫囨挾鏉藉Δ鐘茬焷閻﹀骞戦琛″亾?,
    },
    "table_4_1_training_config": {
        "content": "閻犲洢鍎撮妴鍐炊閸濆嫮鏆伴柛鎺戞鐞氼偊宕抽妸銉﹀闁搞儳鍋涚紞濠囧闯閵娧勭暠婵☆垪鈧磭鈧兘寮箛瀣у亾娓氣偓椤ｂ晛霉鐎ｎ剚绐楅柡宥呮储閳ь兛娴囬惁搴㈠閻楀牊鐓欑€殿喖绻堥埀顑跨閸ㄥ海绱掗崟顖涙殯濞戞挸瀛╁鍫熺箾娴ｇ晫缈婚柛鎴ｆ濞叉媽銇愰弴妯峰亾?,
        "read": "闁活亜顑呴悾鐘诲及椤栨碍鍎婇悹鍥х摠濡叉垵銆掗崨顕呮 RF 閻犳劗鍠曢惌?open/not-open闁挎稑鐡汫B 閻犳劗鍠曢惌?cover ratio闁挎稒骞秗oup key 濞?shape_family闁挎稑鑻杈╂嫬閸愨晜寮撻悷娆庤兌缁劑寮搁崟顒侇棏閻犲洤瀚崣濠囧Υ?,
        "use": "闁衡偓閹勮含 4.3 閻犱緡鍘剧划灞剧▔鎼淬倗妲戝ù鍏煎椤旀洜绱旈鑲╂瘓闁煎搫鍊堕埀顒€鍊归婊堝棘閸パ冭闁活潿鍔嬬粩鏉戔枔娴ｅ喚鍤涢柡鍕凹鐠愮喐鎷?family-CV 婵絾妫冨▓銏ゅ嫉閸濆嫬鐎奸柛鎺戞濞插潡鏌呴崒姘€ら柡鍫墲椤旀垿寮崶銉㈠亾?,
    },
    "table_4_2_predictor_readiness_core_metrics": {
        "content": "閻犲洢鍎撮妴鍐ㄐч崶銊㈠亾鐠囨彃鐎荤紒顐ヮ嚙濞?accuracy闁靛棔鍨ecision闁靛棔璐璭call闁靛棔绗?闁靛棔鏀籥lanced accuracy闁挎稑濂旀禍鎺楀矗婵犲倹绀€鐟滅増甯掑▍?MAE闁靛棔闃淢SE闁靛棔闃?闁?,
        "read": "闁告帒妫涚悮顐﹀箰閸ャ劎鍨奸柣?screening 闁哄嫷鍨伴幆渚€宕ｉ鐐存祮闁挎稒绋戝ú鏍亹閹烘挸鐦归柡宥呮川濠€?cover ratio ranking 闁哄嫷鍨伴幆渚€宕ｉ婊勬殢闁挎稒绋愮悮閬嶆嚀閸涱剛顏遍悹褔鏀辨晶鐘诲绩椤栨稒瀚?shortlist engine闁?,
        "use": "闁衡偓閹勮含 4.4 闁?6.3闁靛棗鍊归婊堝棘閸パ呭畨闁告劖鐟﹂崹姘跺灳濠婂棗鍠曞ù鐘劥缁绘﹢宕?workflow闁炽儲绻愮槐婵嬫嚀鐏炶偐鐟濋柡鍕靛灙閳ь剚绮嶈啯闁搞劌顑呴崙锛勭磼韫囨挾鏆氱紓鍥х岸閳ь剚绺块埀?,
    },
    "table_4_3_by_band_readiness": {
        "content": "閻犲洢鍎撮妴鍐焻?thesis band 閻忕偞娲滈妵姘跺礆閸℃瑨顫﹂柛婊冭嫰濞叉牞銇愰幒鏇樷偓鍐偝鐢喚绀夐悽顖ｅ枛婵亞鎷犻崱妤€鐒奸柛婵愪簷缁?band 閻庣顫夊Σ妤呭Υ娴ｅ憡鎲垮ù?band 闁哄洦娼欏ú鍫曟⒕娣囨墎鍋?,
        "read": "婵☆垼浜滈幃婊冃掗弮鍥╃獩濞戞挸绉撮幃?band 闁?f1闁靛棔鏀籥lanced_accuracy 闁?mae闁挎稒绋戦幐銊╁礂鐠哄搫褰犳繛澶堝姂閻濐喗锛愰幋娆屽亾娴ｅ憡鈧?band 闁汇劌瀚粩鐔兼偩鐏炵儵鍋?,
        "use": "闁衡偓閹勮含 4.4.1 闁告艾鍑界槐婵囨媴濠娾偓鐠愮喖骞€鐠佸磭绉奸柟绋挎处閻栵絾绋婄€ｎ亶妯嗛柣銊ュ閸?band 閻熸瑱缍侀崳鎾Υ閸屾侗鍔€闁哄倸娲よぐ鏌ユ偨閵娿儳鏆婇悹鍥х摠濡?predictor 闁汇劌瀚ぐ鏌ユ偨閵娿劌鐦遍柛銉︽綑閹风増绌卞┑鍫熸畬濡炪倕绠嶉埀?,
    },
    "table_4_4_topk_shortlist_quality": {
        "content": "閻犲洢鍎撮妴鍐沪閺囩姰浠?top-5闁靛棔杈渙p-10闁靛棔杈渙p-20闁靛棔杈渙p-50 闁稿﹥鐟╅埀顒€顦卞▓?hit rate闁靛棔娌焑an cover 闁告粌鐬煎ù澶屸偓闈涚秺濞堛垽寮甸崫鍕秵闁稿﹨鍋愬▓?lift闁?,
        "read": "闂佹彃绉堕崑锝夋儑?top-k mean cover 闁?lift_mean_cover闁挎稒绋栫换鏍掗弬鍨缂佺虎鍨伴崹搴ｇ尵閼姐倗缈遍幖杈鹃檮濞插潡骞掗妷銊х闂侇偄妫楅幃婊呮媼閹规劦鍚€闁革妇鍎ゅ▍娆撳Υ?,
        "use": "闁衡偓閹勮含 4.4.3 闁?6.3闁挎稑濂旂紞鏃€绋?predictor 闁稿繐鍢查ˇ?shortlist value 闁汇劌瀚ú鍧楀箳閵夈劎妲堥柟璇″枔閳?,
    },
    "figure_5_1_inverse_design_workflow": {
        "content": "閺夆晜鐟ョ槐鍫曞炊閹呮綌缂佲偓閾忚鍎戝ù婊勬⒒閻濈兘寮憴鍕€婂☉鎾瑰吹閸ゅ酣鏁嶅顑藉亾濞嗘挴鍋撴径瀣建闁靛棔绶氶。鈺伱圭€ｎ厾妲戦柛鎺戞閳ь兛绀侀懜浼存偐閼搁潧濡抽柣顓滃劤閻☆偊鏌呮径鍫氬亾娴ｅ摜婀伴梺顔哄妿缁繘宕犻弽銉㈠亾娓氣偓閻涙瑧鎷犳担鍦伕闁告娲忛埀顑胯tage4 闁活亞鍠庨悿鍕殽瀹€鍐闁?,
        "read": "濞寸姴楠告稊蹇涘礆閺夊灝绀侀柣?predictor 濠碘€冲€风紞宥夊礂閸喎绲瑰〒姘⊕閺岀喖宕ラ幋顖滅闁告劕绉堕弫?local refinement 闁规亽鍔忕换姗€鏁嶇仦鐐粯闁告艾娴烽弫?manifest 濞存嚎鍊楃划?MATLAB/COMSOL 濡ょ姴鐭侀惁澶愬Υ?,
        "use": "闁衡偓閹勮含 5.1 闁诡剝顔婄紞瀣棘鐟欏嫮銆婄€殿喒鍋撳鎯版彧缁辨繈寮伴婊庡剳濞存粍姊婚悵鐑藉嫉閳ь剟鏌屽鍫矗闁汇劌瀚粊锔剧矙鐎ｎ亝绂堥柕鍡楀€归婊堝棘閸パ勭函缂備焦娲橀惁鈩冪▔椤忓拋鏀遍悘鐐存礀缁辨垶绋夐埀顒佺▔椤忓嫮姣堥柤鍝勫€稿畵鍡涘矗椤栨ǚ鍋?,
    },
    "figure_5_2_mainline_baseline_positioning": {
        "content": "閺夆晜鐟ョ槐鍫曞炊閻愵剙惟婵繐绲界槐鈩冪▔閼姐倕娈犻柕鍡曠瀹稿宕?baseline闁靛棔鑳跺﹢锛勨偓鍦仱閻涙瑧鎷犳担鍛婂闂傚嫬瀚紞宥夊绩椤栨稒瀚奸柛鎺戞閻即鏁嶅畝鍐惧殯闁哄嫬楠搁悾鐘崇椤掆偓濠€顏嗘媼閻戞ɑ鐎柛娆愮懁缁ㄣ劍绋夐鐘崇暠闂婎剦鍋傞崬銈嗙▔瀹ュ懏鍊遍柕?,
        "read": "闁活亜顑傞埀顒佺矊閸犳洜绱掗幘鎻掔槣缂佹儳绨遍埀顒佺箑缁楀矂鍨惧鍐ㄥ潑闁?baseline闁炽儲绻勫▓鎴﹀礆閸℃瑯鐎查柨娑欑摤aseline 闁哄嫷鍨伴顕€鎮¤缁辨繃绋夊鍛畨閻炴凹鍋勯崯鎾诲箣閹邦剛绉奸柛鎾崇Ч缁垳鎷?workflow闁?,
        "use": "闁衡偓閹勮含 5.1 闁?5.5闁挎稑鐬奸弫銈夊级閵壯呭煚濞戞挴鍋撶紒妤婂厸缁ㄨ尙绮╅悩鍙夊缂佹鍓欓崣姘辩博閻樺灚鐣遍悹渚灣閸ゅ酣宕ｉ敐鍛獮闁?,
    },
    "table_5_1_mainline_vs_baselines": {
        "content": "閻犲洢鍎撮妴鍐礆濡も偓閸?frozen mainline闁靛棔瀹玡neric prior闁靛棔鏀籥nd-catalog real GA闁靛棔鍕緊cal robustness 缂佹稑顦抽惌鍓х棯鐠恒劍鐣遍悹浣哄劋閺嬪啴鐓鈥虫暅闁告粌濂旀繛鍥偨閵婏附鐓欑€殿喖绻堥埀?,
        "read": "闂佹彃绉堕崑锝夋儑鐎Ｑ€鍋撳鍡╁晥闁哄倸娲╅棅鈺傜鐟欙絺鍋撳┑鍡楃仚闁挎稒纰嶉婊冾嚕韫囧骸鐦滅紒鎹愶骏閳ь兛鏀籥seline闁靛棔鑳跺﹢锛勨偓鍦仦閹磭妲?baseline闁靛棔娴囪棢闁稿繐鎳忛弫顕€骞橀幋鐘崇暠閻熸瑦甯熸竟濠冪▔瀹ュ牆鍘存繛锝夋敱缁岊垶濡?,
        "use": "闁衡偓閹勮含缂佹鍏涚花鑼博閻樿櫕鐓欐繛澶嬫礉缁旂喖鎮剧仦鎯х仐缂佹鍓欓崣姘辩博閻樿尙鏉藉Δ鐘茬焷椤旀洜绱旈鐓庮枀闁挎稑鐭傛导鈺呭礂瀹ュ洨娉㈤柡瀣矌閻濈兘鎳為崒娑欌枖鐎电増顨呴崕姘舵嚇濮橆厽鎷遍柛顐㈡瑜版棃濡?,
    },
    "table_5_2_workflow_artifacts": {
        "content": "閻犲洢鍎撮妴鍐礆濡も偓閸?seed scoring闁靛棔鍕緊cal refinement闁靛棔绠峚lidation manifest闁靛棔澶焧age4 validation 闁汇劌瀚崣鍡涘矗閿濆嫮鐟㈤柛蹇斿▕閺侇厽娼忛幘鍐叉瘔闁?,
        "read": "閻庣懓鍟Σ鎼佸棘鐟欏嫮銆婃繛缈犺兌閳诲ジ鎯冮崟顐㈣濠㈣泛绉堕獮鍥╂嫚娴ｇ懓绁﹂柨娑欑⊕閻︹剝绋夐埀顒€顫㈤妷鈺佸幋闁哄牆顦板Σ鎴犳兜椤斿灝澹栭柡鍫墮閹蜂即寮崶锔筋偨闁解偓閻ｅ苯浠柕?,
        "use": "闁衡偓閹勮含 5.4 闁瑰瓨鐗犲顔裤亹閺囩偞鍤掑ù鐘€涢妴鍐Υ閸屾侗鍔€闁哄倸娲ｉ懙鎴﹀矗椤栨粍鏆忛悗鐟板暢椤曗晠寮?Python 闁?MATLAB 闁?manifest contract闁?,
    },
    "figure_6_1_predictor_readiness": {
        "content": "閻犲洢鍎卞ù姗€骞嶉幐搴″缂?6.3 闁煎搫鍋婄槐婵嬫⒖閸℃洝鍘悘鐐存礈閵?predictor 闁哄嫷鍨伴幆浣割啅閼碱剛鐥呴柛蹇撳槻椤︻剚娼诲☉妯哄汲閻庡湱鍋ら悰娆愮▔閼姐倕娈犻柣?readiness闁?,
        "read": "闁硅泛锕ら悾鐘诲椽瀹€鍐︹偓?4-2闁靛棔娴囬妴?4-4 闁艰鲸鏌ㄩ幃搴ㄦ儑鐎ｅ墎绐楅柟顒冾唺缂嶅骞愰崶銊у灱閻犲洤鐡ㄥΣ鎴澪熼垾宕団偓椋庣矙閸愯尙鏆伴柨娑橆啌op-k 閻犳劑鍔戦崳铏规嫚鐎涙ɑ顫栭悗鐟板暢閸忔﹢寮ㄩ悷鐗堟緰闁稿﹥鐟╅埀顒€顦扮敮鎾存償韫囧鍋?,
        "use": "闁衡偓閹勮含 6.3 鐎殿喒鍋撳璺虹摠閸ㄣ劎绱掗幘宕囧暡闁挎稑鏈婊堝棘閸モ晜鏆忛悗鐟板暙缁堕亶宕欑悰鈾€鍋撳〒娉乪dictor 闁告瑯鍨禍鎺撴媴濠娾偓鐠?workflow-ready shortlist engine闁炽儲绻勫▓鎴犵磼閹捐鍟堥柕?,
    },
    "figure_6_2_canonical_cases": {
        "content": "閻犲洢鍎卞ù妯间沪閺囩姰浠涢柛銉︾◥闁?canonical inverse-design cases 闁?base-vs-best refinement 闁硅姤顭堥々锕傛晬瀹€鍐炬船闁?`band180_220`闁靛棔姊梑and200_240`闁靛棔姊梑and220_260`闁靛棔姊梑and240_280`闁?,
        "read": "闁活亜顑嗛惁鈩冪▔?case 闁?targetband score闁靛棔鍨edicted cover/overlap 闁哄嫷鍨伴幆渚€宕?refinement 闁告艾瀛╅弫濂稿窗閸曨剙鐏楀ǎ鍥ㄧ箖鐎垫梹顨囧Ο鍦Т闁挎稒绋栫换鏍嫚鐎涙ɑ顫?workflow 闁煎疇濮ゆ竟姗€宕氶弶鍨濡ょ姴鐭侀惁澶愬磹濞嗘挴鍋撴径鍫氬亾?,
        "use": "闁衡偓閹勮含 6.4闁挎稑濂旂粭宀€鎮?6-2 闁圭⒈鍙冮崢銈夊Υ閸屾侗鍔€闁哄倸娲︾€?case 闂侇偅鍔栭宀€鎲撮敐澶婃珵闁挎稑濂旂粭澶屾啺娴ｇ娑ч悹鍥╄ˉ閳ь剚绮嶅﹢渚€宕跺☉妤呭殝婵℃鐗呯欢銉╁灳濠靛嫧鍋?,
    },
    "figure_6_3_baseline_comparison": {
        "content": "閻犲洢鍎卞ù姗€骞?seed discovery闁靛棔绗〢 闁瑰吋绮庨崒銊╁椽瀹€鈧ú鍧楀箳閵夆晝宕ｉ悹鍥﹁兌濞?baseline 閻庨潧婀遍崣搴ㄦ⒖閸℃洝鍘悘鐐存礈閵囨岸鏁嶅畝鈧弫銈嗙鎼淬値鍤涢柡鍕缂嶅宕滃鍕槣缂佹崘娉曞ù澶屸偓浣冾潐濡偆鎹勯婊冩疇闁汇劌瀚幃锝夊触閸粎鍠橀柛鏃囷骏閳?,
        "read": "闂佹彃绉堕崑锝呅掗弮鍥╃獩濞戞挸绉撮幃鎾舵崉椤栨粌娈犻柛锔哄妼閳ь剚鐟╅埀顒€顦ぐ鍌炴偝閼割兘鍋撴担鐑樺焸閻庡湱鍋ら悰娆戞嫚娴ｈ姤绁柛鏍ㄧ墪閹?best/mean gain 濞戞挸锕﹀▓鎴濐啅椤旇偐纾介柨娑欑☉閻ｇ姵绋夊鍡樞﹂柛妤佹磻缁旀挳骞愰崶銊у灱闁告劗濮撮崯妤呭炊娣囨墎鍋?,
        "use": "闁衡偓閹勮含 6.5闁靛棗鍊归婊堝棘閸パ呭畨鐎殿噣缂氶惃?frozen target-band mainline 闁革负鍔岀紞瀣礈瀹ュ洤顔婇柡澶屽枍缁楀懘寮撮幘顔瑰亾閸屾碍鍊ゅù锝嗙矆鐠愮喎顫㈤敐鍛濞戞捁宕甸崵搴ㄦ晬瀹€鍐ｅ亾鐏炶偐鐟濋柡鍕靛灠椤撹櫣绮旈悧鍫濐暡闁哄牆顦扮€垫岸寮介崶鈺冨崪閻庝絻顫夊〒鑸靛濡硶鍋?,
    },
    "figure_6_4_weak_band_dashboard": {
        "content": "閻犲洢鍎卞ù姗€宕剁€靛摜鎼忕€?band 閻忕偞娲滈妵姘辨啺閸℃瑦纾伴幖瀛樻尭閻°劑濡存稊绫琽rtlist lift 闁告粌濂旂€靛瞼鐥崹顔艰闁活潿鍔嶉埀顑秶绀夐柡鍕靛灥閻﹀寮版惔銊у蒋濡?闁搞儰鍗冲В?band 鐎电増顨呴崺宀€鈧湱鍋犲婵嬪箳閵娿劎绠婚柣銊ュ閻楀疇绠涢崘顏嗩槺闁哄鍔戦埀?,
        "read": "闁稿繐鐗忓﹢?coverage闁挎稑鑻崯鈧柣?predictor top-k 闁哄嫷鍨伴幆渚€骞撻幇鎵蒋闁稿﹥鐟╅埀顒€顦冲婵嬫煂韫囥儳绀夐柡鍫氬亾闁告艾娴峰﹢?canonical/refinement 闁哄嫷鍨伴幆浣姐亹閵忊€崇亣闁告瑯鍨堕悰娆戞嫚娴ｇ懓鑵归弶鈺傜◤閳?,
        "use": "闁衡偓閹勮含 6.6闁靛棗鍊归婊堝棘閸モ晜鏆忛悗鐟板暞閺侇噣骞橀幋鏂哄亾濞撯暋ak-band design discovery 鐎电増顨呴崺宀勫箳閵娿劎绠婚柨娑樺缁查箖寮甸鍥舵蕉閻庣懓鑻崣蹇曟喆閿濆懎鏋€闁炽儲绻勫▓鎴﹀礂鐎ｎ亜鐓戦悶娑栧姀閸亪濡?,
    },
    "figure_6_5_stage4_validation": {
        "content": "閻犲洢鍎卞ù妯间沪閺囩姰浠?Stage4 validation 闁汇劌瀚伴悰娆戞嫚娴ｅ湱纭€闁哄倹銇滈埀顑垮灑ositive gain 闁诡垰鎳庨崰宀勫椽?gain 闁告帒妫楃粩鐑芥晬瀹€鈧弫銈嗙鎼淬倗妲堥柡鍕濞撳墎绱掗崼銏㈡尝闁哄绮庣划鈩冩交閸モ晜鍩傞悗鍦仧婢у潡鎮堕崱娑欙紨闁绘粠鍨埀?,
        "read": "闁?solve_success闁靛棔瀹玡ometry_valid/contact_valid闁靛棔鍨sitive gain 缂佹稑顦扮€垫岸寮介崶椋庡耿閺夆晜鐟ょ花鍝勑?predictor score 闁哄洤鐡ㄧ敮瀛樻交閹寸偞浠樼紓浣哥墕瑜板弶绌遍敍鍕尝閻犱焦浜介埀?,
        "use": "闁衡偓閹勮含 6.7闁靛棗鍊归婊堝棘閸パ呭畨闁硅泛锕ら悾鐘诲礃濞嗘劕鐏囬柛蹇嬪姀椤旀垿寮崶顏呭劙闁绘劗娅㈢槐浼村棘鐟欏嫮銆婂ù鐘插閺嗙喖骞戦鍏煎濡澘瀚粊瀵告導閺夊灝鐓傚ù婊冩濠€锛勨偓?COMSOL 濡ょ姴鐭侀惁澶愬Υ?,
    },
    "figure_6_6_local_robustness": {
        "content": "閻犲洢鍎卞ù姗€寮€靛憡鍊?canonical cases 闁汇劌瀚惇顒勬焾?edge-drift / perturbation 閻炴稏鍔庨獮鍥晬瀹€鍐惧殯闁哄嫬姘﹂鏇犳媼閿涘嫬浠梻鍕缁诲酣寮伴姘剨濞ｅ洦绻冪€?target-band 閻炴稑濂旂拹鐔煎Υ?,
        "read": "闁稿繗娅曢弫鐐寸▔椤撶偟濡囬柣鎰攰椤╊偊鎯勯弽銉㈠亾娴ｅ摜婀伴梺顔哄妺缁绘岸骞愭担鍝勮姵闁靛棔娴囩粩鐔兼偩鐏炲墽纾界紒澶庮嚙閹蜂即寮甸埀顒€顔忛鐓庣秮濞达絾鎼槐杈┾偓鐟板暙濞叉牜绮甸弮鍌涚暠闁哄嫷鍨宠彊閻庤纰嶉埀顑秶绀夊☉鎾崇У濡叉悂鏌屽鍡樼厐閻犲洣鐒﹀Σ鎴炵▔閼姐倗娉㈤柡瀣殠閳?,
        "use": "闁衡偓閹勮含 6.8 闁瑰瓨鐗犲顔裤亹?D闁靛棗鍊归婊堝棘閸ワ箒鍘柟璺猴工閻ｇ姵鎷呭鈧拹?canonical cases 闁汇劌瀚棢闁稿繐鎳忛弫顕€骞橀幋顖滅闁兼澘濂旂粭澶愬及椤栨艾缍楅悹褑娓圭粩鎾级閳ユ彃鐦滅紒鎹愶骏閳?,
    },
    "table_6_1_experiment_lines": {
        "content": "閻犲洢鍎撮妴鍐礆濡も偓閸ゎ厾绮鈧崣姘辩博閻樺磭妲ㄩ柡澶嗏偓宕囨澖濡ょ姴鐬奸崵搴ㄦ儍閸曨亞绋婇柣顫妼閻ｇ偓鎷呭蹇曠闁告牕鎳忕€?predictor readiness闁靛棔鎭璦nonical cases闁靛棔鏀籥seline comparison闁靛棔绨歟ak-band闁靛棔澶焧age4 validation 闁?robustness闁?,
        "read": "闁?section 闁活亜顑嗛惁鈩冪▔椤忓嫮鏉藉Δ鐘茶嫰濞硷繝宕堕悙鐢垫憰濞寸姭鍋撳☉鏂跨墦濡埖锛愬鍫㈢闂侇剙鐏濋崢銈囩箔椤掆偓閸欐氨绮╅悩鎻掓櫢闁瑰瓨鍔栫粊锕€顫濈壕瀣槱闁?,
        "use": "闁衡偓閹勮含 6.1 闁?6.2闁挎稑鏈Σ鍝ョ箔椤掆偓閸欐氨绮╅悩鏂ュ亾閺勫浚娼旈悶娑栧妸閳ь剙鍊归婊堝棘閸パ冭闁稿繐鐗嗙槐鈺呮偨閵娿儳鏆婇悹鍥х摠濡叉垿寮甸鍌滃娇闁圭顦抽惁澶愬箲椤曗偓閹借偐绱掗崟顓犵煆闁?,
    },
    "table_6_2_canonical_cases": {
        "content": "閻犲洢鍎撮妴鍐磼濞嗗繐姣夐柛銉︾◥闁?canonical cases 闁?target band闁靛棔澶焗ape identity闁靛棔鏀籥se score闁靛棔鏀籩st score闁靛棔鍨edicted cover/overlap 濞戞挸瀛╄ぐ渚€宕￠崶顒€娅ら柕?,
        "read": "闁稿繐鐗忓﹢?target_band_tag 闁?shape_id闁挎稑鑻崯鈧柣?base 濞?best 闁汇劌瀚Ο濠傤嚕閸岋妇骞elta 闁告帗顨夐鈺呭及?refinement 闁哄嫷鍨伴幆浣圭瑜忛弫鎾存櫠閻愬灚鎶勯柕?,
        "use": "闁衡偓閹勮含 6.4闁挎稑濂旂粭宀勫炊?6-2 闂佹澘绉撮〃婊堝Υ閸屾侗鍔€闁哄倸娲埀顒€鍊搁幃搴ㄥ箰婢跺妲ㄥ☉?case 闁告劖鐟㈤埀顒佺矌缁劑寮搁崟顕€鐓╁ù?-> 闁活亞鍠庨悿鍕磼閹惧浜?-> 濞戞挸瀛╁Λ顐ゆ崉椤栨粌娈犻悗浣冾潐閻?-> 闁规澘绻嬬粻鐔煎灳濠靛嫧鍋?,
    },
    "table_6_3_baseline_comparison": {
        "content": "閻犲洢鍎撮妴鍐ㄐч崶銊㈠亾?baseline comparison 闁汇劌瀚ˇ璺ㄧ尵缂佹ê鐦归柡宥呮祫缁辨繈宕犻崨顔碱仾 seed family summary闁靛棔绗〢/seed 濡ょ姴鐭侀惁澶愭偝閸ャ儮鍋撴稊鐞n 閻庝絻顫夐惁顔剧驳婢跺牃鍋?,
        "read": "閻炴稏鍔忕欢婵堚偓瑙勬灮缁辨繂顫㈤敐鍡樼€☉鎾崇Х椤╋箓鏌呴幇顒€鐏欓悷娆欑秮閸ｆ挳鏁嶅☉妤冨枠闁稿繐鐗婅ぐ渚€宕ｉ弽锔剧憿闁?6-3 閻庣數鎳撶花鏌ユ儍閸曨偄褰犻梺娆惧枟鐎垫岸寮介崶椋庣閻犲浄濡囩划蹇涘礆濡や焦鏉归梻鍕缂嶅秵绋婇悢宄拌濞寸姰鍎埀?,
        "use": "闁衡偓閹勮含 6.5 闁瑰瓨鐗犲顔裤亹閺囨ǚ鍋撻崒娆忕槣闁哄倸娲ょ槐鈺呮偨閵婏附顦ч柣顫妼閻ｇ娀寮ㄩ娑欏闁稿繗娓圭紞瀣极閺夊簱鍋撶涵椋庣闁?6-3 閻犳劗鍠曢惌妤呭极缂堢姷绉奸柛娆樺灥椤曚即骞€瑜嬮埀?,
    },
    "table_6_4_stage4_validation": {
        "content": "閻犲洢鍎撮妴鍐焻閹邦垼鏀介柛鎺擃殔閸?top6 Stage4 validation 闁哄秹鏀卞﹢浼存儍?solve_success闁靛棔瀹玡ometry_valid闁靛棔鎭璷ntact_valid闁靛棔鍨obability闁靛棔鎭璦scade score闁靛棔瀹玜p34 gain 闁告粌鐭佺粩鐔兼偩瀹€鍕垫殽闁绘粌娲㈤埀?,
        "read": "闁稿繐鐗忛悺?solve_success/contact_valid闁挎稑鑻崯鈧柣?gap34_gain_Hz 闁?gap edges闁挎稒绋掑﹢顓炐ч崒婢帡骞嬮幇顒€顫犻柣銊ュ椤㈡垶绋夊鍫濆幋鐟滅増鎸风紞鏂款潰閿濆懏鍊婚柣妞绘櫇閹﹦绱掗幘瀵镐函闁?,
        "use": "闁衡偓閹勮含 6.7闁靛棗鍊归婊堝棘閸パ冭婵懓娲﹂埀顒傜帛閸ㄦ岸宕濋悢鍝勮姵闁告粌鏈婊堝触?gain闁挎稑鑻崯鈧柣顫妺缁斿瓨绋夐妶鍕殝濞寸媴缍€閵嗗啴寮介柨瀣嫳閻熸瑱缍侀崳瀛樻綇閸︻厽娅曞Λ鐗堝灩瀹稿ジ鎷冮悾灞戒化闁?,
    },
    "table_6_5_local_robustness_summary": {
        "content": "閻犲洢鍎撮妴鍐ㄐч崶銊㈠亾缂佹妲ㄥ☉?canonical case 闁汇劌瀚懙鎴ｇ疀?cover闁靛棔绠峚riant cover闁靛棔妞掔换姘跺箰娴ｅ搫鑺抽柛婊冨缁楀倹绋夌€ｎ厾鐝堕柣锝呮湰缁辨挾绮斿Ч鍥ｅ亾?,
        "read": "闂佹彃绉堕崑锝夋儑?variants_ge_90pct_center闁靛棔绠峚riants_ge_80pct_center闁靛棔娌焑an/max edge shift闁挎稒绋栫换鏍ㄧ濞戞ê鍐€闁哄嫮濮鹃鏇犳媼閿涘嫬浠梻鍕缁诲酣鎯冮崟顓€鏃傗偓瑙勭閳ь儸浣插亾?,
        "use": "闁衡偓閹勮含 6.8 闁瑰瓨鐗犲顔裤亹?D闁靛棗鍊风€靛矂寮崶褍璁查柛妯侯儑缂傚骞嬮幇顏嗩伇婵炲牏顣槐婵嗩嚕妤﹁法娈堕悗鐟板暞濡插憡绋夐懡銈囨尝闁哄绮岃ぐ鍙夌┍閳ュ啿顔婇柣銊ュ钘熼柛蹇撴嚀閻﹀骞戦琛″亾?,
    },
    "figure_7_1_validity_scope": {
        "content": "閻犲洢鍎卞ù姗€鎮介妸銉ф勾閻忕偛鍊界粩鐔兼偩鐏炵晫娼旂紒鈧悜妯绘嫳闁哄倸娲﹂弻鐔封枖閺囩姵鍩傛慨婵撶稻閸ㄦ氨绮╃€ｎ剚鐣遍柤鐓庡暙濞插潡鏁嶅婕歵alog闁靛棔鑳剁划銊╁几閸曨剚顥戦柕鍡曠劍濞兼寮?婵懓鍊借闂佹澘绉堕悿鍡涘椽?Stage4 缁绢収鍠涢濠氬Υ?,
        "read": "闁汇垹宕ˇ濠氬礆閺夊灝鏁堕柣顏勵儔濡炬椽宕氶崼鏇楀亾閹邦厾鐟ら柡鈧崜浣瑰經闁挎稒绋栫粔娲閻樻彃鏁堕悺鎺戯攻鐢瓨娼婚幋鐐翠粯缂備礁鐗嗚ぐ鍙夌┍閿涘嫮娉㈤悹浣逛航閳?,
        "use": "闁衡偓閹勮含 7.1闁靛棗鍊归婊堝棘閸モ晜鏆忛悗鐟板暙鎼存粓宕濋埡浣告櫢闁告垵鎼崢鐘诲礆閹壆鐝堕柣锝呯焿缁辨繈鏌嗛崹顔煎赋閺夆晛娲ょ€瑰磭鈧櫢绲胯ⅷ闁?,
    },
    "table_7_1_scope_and_limitations": {
        "content": "閻犲洢鍎撮妴鍐箮婵犲啫鐏囩紒鏂款儓鐎垫牠宕堕弶鎴炲閻忕偐鍋撻梻鍕姈閳ь儸鍥ｅ亾閹拌埇鈧秹宕氬Δ鈧崵顓㈡晬鐏炲€熷珯缂備焦鐟ラ崵顓犳媼閻戞ɑ鐎☉鎿冨幖缁ㄨ尙鎷犻妷鈺佹珰闁活潿鍔庡▓鎴﹀礃濞嗘劗銆婇柕?,
        "read": "闂佹彃绉堕崑锝夋儑鐎ｎ偅浠橀柛姘凹缁旀挳宕氬Δ瀣閻庣懓鍟板ú鍧楀箳閵夘煈娼愰悗瑙勮壘閹姐垺绂嶅☉婊呮▓闁煎疇妫勯崯鎾诲Υ娴ｅ憡鎲垮ù婊勭閻﹁姤绋夊鍫濆幋闁告劖鐟ㄧ换鍐╁緞濞ｎ兘鍋?,
        "use": "闁衡偓閹勮含 7.1-7.2闁靛棗鍊搁崯鎾舵媼閵婎煈鍟堢紒鏃傚У濡炲倿宕ｉ娑樼樆閻炴稏鍔嶉悧绋啃掕箛姘兼斀闁圭鏅滈崹姘▔閳ь剚绋夐鍥ф闁绘帟鍩栭宀勫Υ?,
    },
    "figure_8_1_conclusion_roadmap": {
        "content": "閺夆晜鐟ョ槐鍫曞炊閻愵剙惟鐎瑰憡褰冮悾顒勫箣閹扮増锛旈柣婊庡灛閳ь兛绀佺紞瀣礈瀹ュ牏顢呴柣姘煎枔閳ь兛绀佺紞瀣礈瀹ュ牏鐝堕柣锝呰嫰閹蜂即寮甸鍛檷闁圭鏅涢惈宥嗙▔閸欏鐏囧☉鎾亾闁哄绱曠划銊ф媼妤﹁法鐔呯紒鎹愶骏閳?,
        "read": "濞寸姴楠告稊蹇涘礆閺夊灝绀侀柣顏勵儑缁劎鎷嬮崫鍕垫搐濞达絾娲戠划鐘诲灳濠婂啫鍤掗悗鐟版湰閸ㄦ碍绂掗埀顒佺▕閸埃鍋撳┑濠勭畺婵炴挴鈧啿鐓傞柍銉︾矎缁绘洟鎳楅懞銉モ挅閻忕偞娲戠划鍫熺▕閸埃鍋撳┑鎾跺耿濞戞挸顑嗛弻鐔哥閺傞箖鍤嬮柡鍌滄嚀閹粓寮伴姘辨綌闁哄牊绋撶粈宀勫级閹扳斁鍋?,
        "use": "闁衡偓閹勮含 8.2 闁?8.3闁靛棗鍊归婊堝棘閸モ晜鏆忛悗鐟板暞閺佸綊寮堕悢宄板伎闁哄倸娴勭槐婵囩▔瀹ュ懎鏅欑€殿喗娲栭崣鍡涘棘閹殿喗鐣遍悗鍦仱閻涙瑧绱掗幘瀵镐函闁?,
    },
    "table_8_1_conclusion_and_future_work": {
        "content": "閻犲洢鍎撮妴鍐箮婵犲啯鎷遍柡鍌氭川缁劎鎷嬮幁鎺嗗亾娴ｅ嘲鐦滈悷鏇氭祰閻﹀骞戦鍏煎闁告艾娴烽悽濠氬棘閻熺増鍊诲☉鎾亾濞戞挴鍋撻悗鐢垫嚀缁ㄦ煡濡?,
        "read": "婵絽绻嬬粩瀵告偘瀹€鍕幋闁告瑯鍨禍鎺楀矗濡鐏囩紓浣规崄椤旀垹绮╅悩鍨暠濞戞挴鍋撴繛鍫㈩暜缁变即宕楅崼鐔插亾閼姐倗娉㈤柡鍫墯閺嬪啴宕戝顐ゅ晩濞寸姭鍋撳☉鏂跨墳缁辨繈宕樺鍫殯闁哄嫬姘﹂惁澶愬箲椤斿吋韬柛婵愪悍缁辨繈寮甸埀顒勫触鎼淬倕娈伴柣鎺撳劶缁诲啫銆掗垾鍐茬厒闁哄牜浜濆闈涱啅閵夈倗绋婇柕?,
        "use": "闁衡偓閹勮含 8.1-8.3闁靛棗鍊块埀顒€鍊搁幃搴ㄦ儎鐎涙ê澶嶅ù锝嗙矆鐠愮喓绱掗幘璇″晥缂佹梻濮甸宀勬媰娴犲鈧洭寮搁煬娴嬪亾?,
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
    artifacts[1].append({"name": "闁?1-1 闁哄牜鍓氶弸?target-band 闂侇偄妫楅幃婊呮媼閹规劦鍚€闁诡剝顔婄紞瀣浖閸℃浠?, "path": str(fig), "kind": "figure", "note": "閻忕偞娲滈妵姘辨媼閻戞ɑ鐎柣銊ュ缁ㄦ彃鈻撻棃娑氱濞戞捁宕甸崵搴ㄥ椽鐏炶偐鐟忛悘鐐插€块埀顒佹缁额偊濡?})
    df = pd.DataFrame(
        [
            ["闁烩晩鍠楅悥锝嗭紣閹存繄鏁ㄩ柡澶嗏偓鍙夘偨濡澘瀚粊?, "闁硅泛锕︾划銊╁几閸曨亞鐟㈤柟绋挎搐閻?band 闁稿繐宕幃鎾存媴濠娾偓鐠愮喐娼忛幘鍐插汲", "缂?4 缂佹梻濮甸弻鐔封枖閺囨氨鐟㈢紒?6.3 闁?readiness", "闁搞儳鍋熼悺?predictor 闁哄嫷鍨伴幆渚€寮?shortlist value"],
            ["濡澘瀚粊鏉戭嚕閺囩儐鍤ら梺顐㈡閹粎鎷嬮幑鎰靛悁", "闁?predictor 闁圭儤甯掔花顓㈢嵁鐠鸿櫣绌块悗鐢靛帶閳ь剚鐟╅埀顒€顦扮敮瑙勬交?, "缂?5 缂?workflow 濞戞挸娴烽?6.4-6.6 闁?, "闁搞儳鍋熼悺鐔肺熼垾宕団偓鐑藉礆閸℃ɑ娈堕柡鍕靛灠閹線鎳楅崐鐔哥ギ闁告牗鐗旂拹鐔兼儑閻旈鏉介悹浣瑰礃椤撴悂宕ｉ幋鐘茬疀"],
            ["闁活亞鍠庨悿鍕偋閳哄啯鍊炲Δ鐘茬焷閻﹀姊婚鐘茬畾", "Stage4 / COMSOL 閻?shortlist 闁稿纰嶅〒鍓佺磼閸懇鈧鎷?, "缂?6.7 闁?, "闂侇剙鐏濋崢銈夊箮?surrogate 缂備焦鎸婚悘澶屾嫚椤栨艾鏅搁柟瀛樺姈濞撳墎绱掗崼銏犫挅闁荤偛妫涚划銊╁几?],
            ["濞戞捁宕甸崵搴㈡綇閸︻厽娅曢柡鈧捄鍝勭稉", "闁告劘宕电划?thesis band catalog 濞?baseline 闁稿繐纾柈?, "缂?2闁? 缂?, "閻犱讲鏅為鎴﹀棘閸ワ箑鐦滅€殿喚濮撮崢鐘诲礆闊祴鍋撴担绋胯濠㈣泛绉堕獮鍥Υ娴ｇ璁插ǎ?],
        ],
        columns=["鐎规悶鍎扮紞鏃堟倷?, "閻犱胶鍎ら弸鍐╃▔椤撶姵鐣遍柛姘煎亗缁?, "濞戞挻妲掗々锕傛媰閻ｅ苯浠?, "闁告劖鐟ょ紞鏃€鎷呭鍛殢"],
    )
    _, md = write_table(df, tab_dir, "table_1_1_contribution_map")
    artifacts[1].append({"name": "閻?1-1 闁哄牜鍓氶弸鍐╃▔閺勫浚娲ｇ€规悶鍎扮紞鏃€绋夋惔锝囧娇闁煎搫鍊介惁澶愬箲椤旂⒈鍤犻幖?, "path": str(md), "kind": "table", "note": "缂備緡浜ｉ鎴炵▔椤撶噥娲ら柟濂夊墮閸ㄩ亶寮幍顔间化闁告粌鑻幃妤呭棘閸ヮ亞妲堥柟璇″櫍閹藉ジ濡?})

    # Chapter 2
    root, fig_dir, tab_dir = ensure_chapter(2)
    fig = make_problem_boundary(fig_dir)
    artifacts[2].append({"name": "闁?2-1 闁烩晩鍠楅悥锝嗭紣閹存繄鏁ㄩ梺顐㈡閹粎鎷嬮幑鎰靛悁闂傚偆鍣ｉ。鐣屸偓瑙勭煯缁犵喐绋夋惔銈囩彾闁?, "path": str(fig), "kind": "figure", "note": "闁活潿鍔嬬花顒勬偩鐏炵晫鏆伴弶鍫熸尭閸欏棝濡存担鐣岀炕闁告垶浜介埀顑跨劍鑶╅柛銊ヮ儓椤鎳濋幓鎺撳闁活亞鍠庨悿鍕殽瀹€鍐閺夊牆婀遍弲顐﹀Υ?})
    df = pd.DataFrame(
        [
            ["閺夊牊鎸搁崣?, "缂備焦鎸婚悗顖炲矗閸屾稒娈堕柕鍡曞hape descriptors闁靛棔杈渁rget band low/high/center/width", "闁哄鍎撮崵?target-band parametric dataset"],
            ["濞戞搩鍙冨Λ鎸庢綇閹惧啿姣?, "闁瑰灚鎸哥槐鎴濐潡閸屾粌鑺抽柕鍡曟祰椤╊偊鎯勯弽銊фХ濞撴艾顑冮埀顑跨嫍verlap闁靛棔澶焗ortlist score", "闁活潿鍔嬬花顒勫磹濞嗘挴鍋撴径瀣瑩閹兼潙楠忕槐婵囩▔瀹ュ嫮绋婂☉鎾跺劋濞撳墎绱掗崼銏犫挅闁荤偛妫涚划銊ф媼?],
            ["闁哄牃鍋撶紓浣哥墣缁额參宕?, "缂備礁绻楃换?Stage4 real validation 闁汇劌瀚ぐ鏌ユ偨?target-band 閻犱焦宕橀?, "閻犱胶鍎ら弸鍐嫉閳ь剛绱掗崼婵嗚濞ｅ浄绱曠划銊╁几?],
            ["閺夊牆婀遍弲?, "thesis band catalog闁靛棔绀佺紞瀣礈瀹ュ洨娉㈤柡瀣濡矂濡存担鍛婄ゼ閻庤纰嶅妤呭棘濞嗗海鐟㈡慨鐟板€借闂佹澘绉堕悿?, "闂傚啫寮堕娑欐交閸パ冾唺閻庣櫢绲胯ⅷ闂侇偅姘ㄩ弫銈夊箑?],
        ],
        columns=["閻庣數顢婇挅?, "闁告劕鎳庨?, "閻犱胶鍎ら弸鍐喆閿濆娅?],
    )
    _, md = write_table(df, tab_dir, "table_2_1_problem_io_boundary")
    artifacts[2].append({"name": "閻?2-1 闂傚偆鍣ｉ。鑺ユ綇閹惧啿寮抽弶鍫熸尭閸ゎ厽绋夋惔銏犵亣缂佹柨顑堢粩鐔兼偩?, "path": str(md), "kind": "table", "note": "闁衡偓閹勮含闂傚偆鍣ｉ。鐣屸偓瑙勭煯缁犵喓浜歌箛姘濋柨娑樿嫰鎼存粓宕濋埡鍕靛殺闁兼澘鎳庨崢娑㈡偠閸℃鎺撶鐠囨彃顫ら弶鍫濇贡閺咁偊濡?})
    df = pd.DataFrame(
        [
            ["truth production", "physics_pipeline/闁靛棔澶焧age1/闁靛棔澶焧age2/", "data/comsol_batch/", "闁绘せ鏅濋幃濠囨儑閻斿皝鍋撻崗鍏奸檷婵?],
            ["target-band dataset", "run_build_parametric_targetband_dataset_v1.py", "targetband_parametric_v1.csv", "闁烩晜鍨瑰杈┾偓娑崇細缁″嫰寮悧鍫濈ウ闁糕晞娅ｉ、?],
            ["conditional predictor", "RF classifier + HGB regressor", "prediction_targetband_param_v1_runs/", "shortlist engine"],
            ["seed scoring / local refinement", "optimization/runners/", "data/ml_runs/targetband_*", "闁硅泛锕。鈺伱圭€ｎ亜鐎婚柡浣瑰濞村棝骞嬮幇顑藉亾濞嗘挴鍋撴径瀣吂閺?],
            ["real validation", "runners/run_stage4_validation_targetband_v1.m", "data/comsol_batch/stage4_validation_targetband_v1/", "闁哄牃鍋撶紓浣哥墢婢у潡鎮堕崱娆屸偓妯兼媼?],
        ],
        columns=["閻犱胶鍎ら弸鍐嫉椤栨繍鍤?, "濞寸媴绲块悥婊堝礂閵夈儱缍?, "闁哄鍟埢澶嬫綇閹惧啿姣?, "闁革负鍔庨柈瀵哥磼閻旀儼鍘柣銊ュ椤鎳?],
    )
    _, md = write_table(df, tab_dir, "table_2_2_module_contract")
    artifacts[2].append({"name": "閻?2-2 閻犱胶鍎ら弸鍐嫉椤栨繍鍤旈柕鍡曟閸烆剟鎯嶆担绋垮汲闁告瑱绲肩粭宀勫级閸愩劉鏋嗛弶鍫熸尭閸ゎ厾鈧潧婀遍崣?, "path": str(md), "kind": "table", "note": "缂侇垵宕电划鍝勵浖閸℃浠哥紒鏃傚Т閹蜂即姊介崟顐ょЭ闁告稒鍨濋幎銈囨偘閵娾晛鍘撮柛娆樺灠缁扁晠鎮介妸锝傚亾?})

    # Chapter 3
    root, fig_dir, tab_dir = ensure_chapter(3)
    fig = make_shape_atlas(fig_dir)
    artifacts[3].append({"name": "闁?3-1 闁稿繒顭堥悗椋庣磼閹惧鈧垶寮箛搴ｇ憿闁告瑥鍊归弳鐔煎礌閺嵮冩濞达絾娲滈妵姘跺箛韫囨挻绂?, "path": str(fig), "kind": "figure", "note": "闁活潿鍔庡﹢锛勨偓?contour 闁哄倸娲ｅ▎銏沪閺囩姰浠涚紓浣规尰閻庮垶寮箛搴ｇ憹闁哄嫷鍨辨繛濠勬寬閳ュ啿缍侀梺鎻掔箞閳?})
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
    artifacts[3].append({"name": "閻?3-1 thesis band catalog 濞戞挸瀛╅悧閬嶅嫉椤掑倻鍩犻悹?, "path": str(md), "kind": "table", "note": "濞存嚎鍊撻崬顒勫礂椤撴繈鍤?thesis bands 闁汇劌瀚～妤呮嚌鐏炲倵鍋撴担鍦闁哄牜鍓濋々顐︽儎閺嵮勫闂傚懏鍎崇€规娊濡?})
    if not coverage.empty:
        fig = make_band_coverage_figure(fig_dir, coverage)
        artifacts[3].append({"name": "闁?3-2 thesis band catalog 閻熸洖妫涘ú濠冩償閿旇法鐟㈡慨婵撶稻閻楅亶寮甸鍐ㄧ獩闂?, "path": str(fig), "kind": "figure", "note": "闁?positive rows 濞?mean cover ratio 閻忕偞娲滈妵姘跺极閻楀牆绁﹂柛鈺勬椤㈠懘濡?})
    df = pd.DataFrame(
        [
            ["闁诡剚妲掗、鎴﹀极?, dataset_info.get("rows", "")],
            ["unique designs", dataset_info.get("unique_designs", "")],
            ["unique families", dataset_info.get("unique_families", "")],
            ["濮掓稒顭堥濠氬极閻楀牆绁﹂梻?tag", "windows_dense_v8_truth_plus_exploratory_aug_v1"],
            ["闁哄鍟埢?CSV", str(Path(dataset_info.get("dataset_csv", "")))],
        ],
        columns=["闁圭娲﹂悥?, "闁?],
    )
    _, md = write_table(df, tab_dir, "table_3_2_dataset_inventory", digits=0)
    artifacts[3].append({"name": "閻?3-2 target-band 闁告瑥鍊归弳鐔煎礌閺嶃劍娈堕柟璇″櫍濞夛箓骞€閺勫浚娼?, "path": str(md), "kind": "table", "note": "缂備焦鐟ч鍥ㄧ▔婢跺瞼褰块柡浣哄瀹撲線宕洪搹璇℃敤濞戞挴鍋撳☉鎿冧簻瑜版彃顕ｉ弴鐘虫殢闁汇劌瀚埀顒€顭烽崳铏规嫚鐎涙ɑ顫栭柕?})

    # Chapter 4
    root, fig_dir, tab_dir = ensure_chapter(4)
    fig = make_conditional_prediction_task(fig_dir)
    artifacts[4].append({"name": "闁?4-1 闂傚牄鍨归幃婊堟儎椤旂晫鍨煎Λ鐗堝灥閻㈩偊鎯冮崟顒佽拫濞寸姴鐖奸。鈺伱圭€ｂ晜宕查柛鏂衡偓宕囨毎濞?, "path": str(fig), "kind": "figure", "note": "閻熸瑱缍侀崳鎾礆閸℃瑨顫﹂柛锝冨妸閳ь兛绀佸ú鏍亹閹烘垶鐝ら柛?shortlist score 闁汇劌瀚幑銏ゅ礉閳╁啫顎曢柛鎺戞閳?})
    copied = copy_if_exists(READINESS_DIR / "figures" / "family_cv_readiness_summary.png", fig_dir / "figure_4_2_predictor_readiness_summary.png")
    if copied:
        artifacts[4].append({"name": "闁?4-2 predictor readiness 闁哄秶顭堢缓楣冨箰閸ャ劎鍨奸柛?, "path": str(copied), "kind": "figure", "note": "濞寸姴瀛╁Λ锕傚嫉?readiness 闁告帒妫欓悗浠嬪极鐎靛憡鍊為柨娑樼灱閺併倖绂嶆惔锛勬綌缂佲偓?family-CV 闁诡剝顔婄紞瀣偘閵娧冪疀闁?})
    df = pd.DataFrame(
        [
            ["闁告帒妫涚悮顐﹀闯?, "Random Forest", "target_gap_is_open", "stratified_group_kfold", "shape_family", str(CLS_RUN_ROOT)],
            ["闁搞儳鍋涚紞濠囧闯?, "HistGradientBoosting", "target_gap_cover_ratio", "stratified_group_kfold", "shape_family", str(REG_RUN_ROOT)],
        ],
        columns=["婵☆垪鈧磭鈧?, "婵☆垪鈧磭鈧兘寮?, "濡澘瀚粊鎾儎椤旂晫鍨?, "閻犲洤瀚崣濠囧棘閻熸壆纭€", "闁告帒妫涚划宥夋煥?, "闁哄鍟埢澶嬫綇閹惧啿姣夐柣鈺婂枛缂?],
    )
    _, md = write_table(df, tab_dir, "table_4_1_training_config")
    artifacts[4].append({"name": "閻?4-1 闁告帒妫涚悮顐﹀闯閵娿倗鐟㈤柛銉у仜缂嶅﹪宕抽妸顭戝敳缂備礁鍟撮崢銈囩磾?, "path": str(md), "kind": "table", "note": "闁哄倽顫夌涵鍓佺博閻樹警鍤涢柡鍕鑶╅柛銊ヮ儓椤旀洜绱旈鑺ヮ槯闁烩晛鐡ㄧ敮鏉戭嚕閺囩姵鏆忛柕?})
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
        columns=["闁圭娲﹂悥?, "闁轰焦婢橀埀?],
    )
    _, md = write_table(df, tab_dir, "table_4_2_predictor_readiness_core_metrics")
    artifacts[4].append({"name": "閻?4-2 predictor readiness 闁哄秶顭堢缓楣冨箰閸ャ劎鍨?, "path": str(md), "kind": "table", "note": "闁衡偓椤栨稒瀚?predictor 鐎瑰憡褰冭ぐ鍙夋媴濠娾偓鐠?shortlist engine 闁汇劌瀚崹浠嬪棘椤撴壕鍋?})
    if not cls_by_band.empty and not reg_by_band.empty:
        by_band = cls_by_band.merge(reg_by_band, on="target_band_tag", how="left", suffixes=("_cls", "_reg"))
        cols = ["target_band_tag", "positive_rate", "accuracy", "precision", "recall", "f1", "balanced_accuracy", "mean_true_cover", "mean_pred_cover", "mae"]
        _, md = write_table(by_band[[c for c in cols if c in by_band.columns]], tab_dir, "table_4_3_by_band_readiness")
        artifacts[4].append({"name": "閻?4-3 thesis bands 闂?band readiness", "path": str(md), "kind": "table", "note": "閻熸瑱缍侀崳瀛樼▔瀹ュ懏鍊遍柣鈺婂枟閻栵絾锛愰幋婵堟暔闂傚懏鍎崇€规娊宕仦鐏镐線宕圭€ｎ厾鐝堕柣锝呰閳?})
    if not topk.empty:
        _, md = write_table(topk, tab_dir, "table_4_4_topk_shortlist_quality")
        artifacts[4].append({"name": "閻?4-4 top-k shortlist 閻犳劑鍔戦崳?, "path": str(md), "kind": "table", "note": "閻犲洤鐡ㄥΣ?predictor 闁汇劌瀚悳顖炲磹闂傛潙鐦滈悷鏇氭缂嶅鎮抽弶鎸庤含闁圭儤甯掔花顓㈠礈瀹ュ懎鐏欓柛濠冪懇閳ь剙顦冲婵嬫煂韫囧鍋?})

    # Chapter 5
    root, fig_dir, tab_dir = ensure_chapter(5)
    fig = make_inverse_design_workflow(fig_dir)
    artifacts[5].append({"name": "闁?5-1 prediction-guided target-band inverse-design workflow", "path": str(fig), "kind": "figure", "note": "缂佹鍏涚花鑼博閻樿尙纾诲鍓侇棎椤曗晠寮版惔銏″仢缂侀硸婢€缁楀本顨ュ畝鍐婵炵繝鑳堕埢濂稿Υ?})
    fig = make_baseline_positioning(fig_dir)
    artifacts[5].append({"name": "闁?5-2 濞戞捁宕甸崵搴㈢▔?baseline / 鐎规悶鍎抽埢濂稿绩椤栨稒瀚奸柣銊ュ椤鎳濋幓鎺旀毎濞?, "path": str(fig), "kind": "figure", "note": "闂侇剙鐏濋崢銈夊箮婵犲倸鍧婇柛娆掑蔼閻墽鐥崹顔藉婵繐绲界槐鈩冪▔閼姐倕娈犳繛锝呭槻濠€顏呯▔閳ь剛鎸ч弸顐熷亾?})
    df = pd.DataFrame(
        [
            ["frozen target-band mainline", "婵繐绲界槐锛勬媼閻戞ɑ鐎☉鎾瑰吹閸?, "闁哄鈧弶顐藉Λ鏉垮缁?+ shape-aware + local refinement + Stage4", "缂?5 缂佹梻濞€閸ｆ悂鎮欓悷鎵綌鐎殿喒鍋?],
            ["generic prior / historical bridge", "baseline", "闁?seed discovery / v10/v11 缂?, "缂?6 缂佹梻濮撮顕€鎮¤琚欓梺鎻掝煭缁辨繃绋夊鍕▕濞戞挻妞界划顖滄媼閵堝嫬鐦滅紒?],
            ["band-catalog real GA", "闁活亞鍠庨悿鍕箹濠婂懎鍋?baseline", "濞磋偐濮风划?COMSOL-in-loop 闁瑰吋绮庨崒?, "闁活潿鍔嬬花顒傛嫚鐎涙ɑ顫栧Λ鏉垮閻ｅ宕仦鐐珡闁绘粌娲ゅΟ濠傤嚕?],
            ["local robustness", "閻炴稏鍎遍崢鏍绩椤栨稒瀚?, "闁搞儱顕划?canonical cases 闁汇劌瀚惇顒勬焾閵婏箑顥嶉柛鏂诲妼閸ㄥ酣寮?, "闁告瑯鍨€靛矂寮崶褍绔剧紓鍌楁櫔缁辨繄绱掗崱姘濋柡鈧ィ鍐╊€嶇憸?],
        ],
        columns=["閻犱警鍨抽崵?, "閻犱胶鍎ら弸鍐叕椤愨€虫暅", "濞戞挻妲掗々锕傚礃閸涱収鍟?, "濞达綀娉曢弫銈夊棘閻熸壆纭€"],
    )
    _, md = write_table(df, tab_dir, "table_5_1_mainline_vs_baselines")
    artifacts[5].append({"name": "閻?5-1 濞戞捁宕甸崵搴㈢▔?baseline 閻犱警鍨抽崵搴ｂ偓瑙勭煯缂嶅懐鈧潧婀遍崣?, "path": str(md), "kind": "table", "note": "闁活潿鍔嬬花顒傜箔椤戣法瀹夌紒鏃傚У閸ㄣ劎绮鈧崣姘辩博閻樿尙鏉藉Δ鐘茬焷椤旀洜绱旈鐓庮枀缂備胶鍠嶇粩鎾矗閿濆懐绐為柕?})
    df = pd.DataFrame(
        [
            ["seed scoring", "scripts/run_ga/score_targetband_candidates_v1.py", "targetband_seed_predictions.csv", "濡澘瀚粊鎾闯閵娧屽剳濞戞挴鍋撴繛鍠°倗绠婚柛蹇嬪劚閳ь剚鐟╅埀顒€顦扮敮鎾存償?],
            ["local refinement", "scripts/run_ga/run_targetband_local_ga_v1.py", "targetband_ga_candidate_manifest_v1.csv", "闁硅泛锕悵顕€宕氶崱妞诲亾濞嗘挴鍋撴径瀣吂闁告碍鍨甸惇顒勬焾閵婏附绾ù?],
            ["validation manifest", "scripts/run_ga/build_targetband_validation_manifest_v1.py", "targetband_ga_validation_manifest_v1.csv", "Python 闁?MATLAB 闁汇劌瀚崣鈩冪椤愩埄娈╃紒?],
            ["stage4 validation", "runners/run_stage4_validation_targetband_v1.m", "stage4_validation_results.csv", "闁活亞鍠庨悿鍕偋閳哄啯鍊炵紓浣规尰閻忓鎷冮悾灞戒化"],
        ],
        columns=["婵縿鍎甸?, "闁稿繈鍎辫ぐ?, "闁稿繑濞婇弫顓熸綇閹惧啿姣?, "閻犱胶鍎ら弸鍐喆閿濆娅?],
    )
    _, md = write_table(df, tab_dir, "table_5_2_workflow_artifacts")
    artifacts[5].append({"name": "閻?5-2 prediction-guided workflow 闁稿繈鍎辫ぐ娑欑▔鎼淬倗缈婚柛?, "path": str(md), "kind": "table", "note": "闁哄倽顫夌涵鍓佺博閻樺弶瀚查梻鍕缂嶅秹鏌堥挊澶婅闁活潿鍔婇埀?})

    # Chapter 6
    root, fig_dir, tab_dir = ensure_chapter(6)
    copied = copy_if_exists(READINESS_DIR / "figures" / "family_cv_readiness_summary.png", fig_dir / "figure_6_1_predictor_readiness.png")
    if copied:
        artifacts[6].append({"name": "闁?6-1 predictor readiness 缂備焦鎸婚悘澶愬炊?, "path": str(copied), "kind": "figure", "note": "閻炴稏鍎电紞鍫㈢箔椤掆偓閸欐氨绮╅悩鍙夌闁告瑥鍤栫槐婵嬪箥閹稿骸澶?6.3 闁煎搫鍊堕埀?})
    for path in sorted((CH6_DIR / "figures").glob("figure_6_*.png")):
        if path.name != "figure_6_1_predictor_readiness.png":
            artifacts[6].append({"name": CH6_DISPLAY_NAMES.get(path.stem, path.stem.replace("_", " ")), "path": str(path), "kind": "figure", "note": "闁哄啨鍨哄﹢浣虹箔椤掆偓閸欐氨绮╅悩鐢垫尝闁哄绮屽ù姗€濡?})
    for path in sorted((CH6_DIR / "tables").glob("table_6_*.md")):
        artifacts[6].append({"name": CH6_DISPLAY_NAMES.get(path.stem, path.stem.replace("_", " ")), "path": str(path), "kind": "table", "note": "闁哄啨鍨哄﹢浣虹箔椤掆偓閸欐氨绮╅悩鐢垫尝闁哄绮忛妴鍐Υ?})

    # Chapter 7
    root, fig_dir, tab_dir = ensure_chapter(7)
    fig = make_validity_scope(fig_dir)
    artifacts[7].append({"name": "闁?7-1 闁哄倽顫夌涵鍫曞箣閹邦喚褰岄柤鐓庡暙濞叉寧绋夋惔锛勬拱闂傚嫭鍔栭埀顑棛鐝堕柣?, "path": str(fig), "kind": "figure", "note": "閻犱降鍔忛鎴犵博閻樺灚鏆忓ù婊冮閸樼娀宕氱捄鐑樺嬀闁伙絽鑻悾鍓ф媼閻戞ɑ鐎☉鎾诡嚙缁卞爼濡?})
    df = pd.DataFrame(
        [
            ["闁瑰瓨鍔楅悵娑㈡嚑閸愩劍绾?, "thesis band catalog 闁?, "闁稿浚鍘洪柌婊堝礃閼姐倗娉㈤柣鈺婂枟閻栵絾锛愰幋婵堟暔", "濞戞挸绉烽々锕傚礃濞嗘劕鐏囧ù鐘电帛閸撶増娼婚悙鐢垫暰 band 鐎规瓕灏闁?],
            ["闁瑰瓨鍔楅悵娑㈡嚑閸愩劍绾?, "鐟滅増鎸告晶鐘电磼閹惧鈧垶寮箛搴ｇ憿闁告瑥鍊归弳鐔煎礌閺嶎兙鈧啯娼?, "shape_contours 濞?v8 闁轰胶澧楀畵渚€姊块崱姘兼船闁烩晜鐗滃▓鎴﹀籍?, "濞戞挸绉烽々锕€鈻斿☉妯侯嚙闁告帡顣﹂幑銏ゅ箛韫囨柨鐝栭柟鍨灩缁劑寮?],
            ["闁瑰瓨鍔楅悵娑㈡嚑閸愩劍绾?, "闁搞儱鎼悾楣冨级閹邦厽鐏愰柛婊冩湰閻壆鎲撮敐澶婂赋缂?, "鐟滅増鎸告晶?COMSOL/MATLAB 闂佹澘绉堕悿?, "闁哄鍔栭弸锟犲矗濡搫顕ч梻鍥ｅ亾閻熸洑绶氶崳鎼佸棘娴煎宕ｉ悹?],
            ["閻忕偐鍋撻梻鍕姈閳?, "weak band 濞寸姴绉瑰〒鍫曞极閻楀牆绁﹂柛鏃傚Т閻?, "閻忓繈鍊曢崣鐐殗濮椻偓椤ｅ墎绮欓埀顒勬偪?band", "闁告劖鐟﹂崹姘啅閹绘帞鏉介悹鎰╁妽鐢娼诲☉宕囩闁兼澘鐭傚顏嗏偓鐟拌嫰閸欏繒鎲撮敐鍛瀫"],
            ["閻忕偐鍋撻梻鍕姈閳?, "predictor 濞戞挸绉靛Σ鎼佸嫉閳ь剛绱掗崼鐔烘勾閻熸瑱绲藉▍?, "shortlist engine", "闁哄牃鍋撶紓浣哥墢缁劎鎷嬫潪鎵穿閻?Stage4"],
        ],
        columns=["缂侇偉顕ч悗?, "閺夊牆婀遍弲?閻忕偐鍋撻梻?, "閻犲洣鐒﹀畵渚€骞嬮弽褜鍤犻悹?, "閻犱胶鍎ら弸鍐礃濞嗘劗銆?],
    )
    _, md = write_table(df, tab_dir, "table_7_1_scope_and_limitations")
    artifacts[7].append({"name": "閻?7-1 闁哄倽顫夌涵鍫曞箣閹邦喚褰岄柤鐓庡暙濞叉寧绋夋惔锛勬拱闂傚嫭鍔栭埀?, "path": str(md), "kind": "table", "note": "閻犱降鍔忛鎴犵博閻樿櫕浠橀柛蹇斿▕閺侇參鎯冮崟顔剧彾闁伙絽鐭侀妴鍐Υ?})

    # Chapter 8
    root, fig_dir, tab_dir = ensure_chapter(8)
    fig = make_conclusion_roadmap(fig_dir)
    artifacts[8].append({"name": "闁?8-1 闁稿繈鍔嶉弸鍐磼閹捐鍟堝☉鎾抽閹绱掗鐐扮矗濞达絾绮忛惌鍓х棯閸喗绂?, "path": str(fig), "kind": "figure", "note": "缂備焦鎹侀鎴犵博閻樺啿惟閻犳劧绱曠亸鐐哄Υ娴ｇ晫鐝堕柣锝呰嫰閹蜂即寮甸鍛檷闁哄倻鎳撻幃婊堝绩閼稿灚灏嗛柛鎺楊暒缁旀潙顕ｉ悩鍙夌闁?})
    df = pd.DataFrame(
        [
            ["闁绘せ鏅濋幃濠囨儑閻斿皝鍋撻梻瀵哥憿闁轰胶澧楀畵渚€宕洪搹璇℃敤", "鐎点倛娅ｉ悵?target-band 闁轰胶澧楀畵渚€姊?, "缂?3 缂?+ 閻?3-1/3-2", "闁圭鏅涢妵?truth harvesting"],
            ["闁哄鈧弶顐藉Λ鏉垮缁?, "鐟滆埇鍨洪崹姘跺矗椤栨粍鏆忓ù?shortlist 闁?predictor", "缂?4 缂?+ 缂?6.3 闁?, "闁圭粯鍔曞畷宀€鎹?band 婵炲绋戠€?],
            ["闂侇偄妫楅幃婊呮媼閹规劦鍚€ workflow", "閻庣懓鏈崹姘紣閸曨剛銈寸€殿喗娲栭閬嶅箹濠婂懎鍋嶉柕鍡曠閻剟鏌堥妸褏鐭庨柛鏍ㄧ墪閹蜂即鎯囬悢椋庢澖濡ょ姴鐭侀惁?, "缂?5-6 缂?, "闁圭鏅涢惈宥囩磼閹惧鈧垳鎮伴妸褋浠涢柛婊冭嫰娴兼劗绮欑€ｎ剙顔婇柡?],
            ["閻犱胶鍎ら弸鍐╃▔鐠囪尙鐐婇弶鍫濇贡閺?, "闁哄嫬娴烽垾?catalog 闁告劕鎳忛崹姘辩博鐎ｅ墎绀夊☉鎾崇Т閵囨ɑ寰勮鐠愮喖鏌呭杈ㄦ殢婵懓鍊借闁?, "缂?7 缂?, "闁哄洦娼欓妵?catalog 濞戞挸顑夐崳鎼佸棘閺夊灝鏋欑紓浣规尫鐎靛瞼鐥?],
        ],
        columns=["闁诡剝宕电划銊р偓鐢殿攰閽?, "闁哄牜鍓氶弸鍐磼閹捐鍟?, "濞戞挻妲掗々锔炬嫚娴ｇ懓绁?, "闁告艾娴烽悽濠氬棘閻熺増鍊?],
    )
    _, md = write_table(df, tab_dir, "table_8_1_conclusion_and_future_work")
    artifacts[8].append({"name": "閻?8-1 闁稿繈鍔嶉弸鍐啅閵夈倗绋婇柟顒冨吹缁劍绋夋惔锛勬綌闁哄牊绋戦顔芥償?, "path": str(md), "kind": "table", "note": "缂備焦鎹侀鎴犵博閻樻彃璁查柟绋款槹椤掓繄鎮伴妸鈹惧亾閹邦収鍞介柡鈧懜鍨皢闁?})

    return artifacts


def write_guides(artifacts: dict[int, list[dict[str, str]]]) -> None:
    chapter_titles = {
        1: "缂備緡浜ｉ?,
        2: "闂傚偆鍣ｉ。鐣屸偓瑙勭煯缁犵喐绋夋惔锝夊厙缂備胶鍠愰、瀣几?,
        3: "闁绘せ鏅濋幃濠囨儑閻斿皝鍋撻懖鈺傛櫢濞存籂鍌滅憿闁烩晩鍠楅悥锝嗭紣閹存繄鏁ㄩ柡浣哄瀹撲線宕洪搹璇℃敤",
        4: "闂傚牄鍨归幃婊堟儎椤旂晫鍨煎Λ鐗堝灥閻㈩偊鎯冮崟顒佽拫濞寸姴鐖奸。鈺伱圭€ｎ偅鐓欐繛?,
        5: "濡澘瀚粊瀛樸仚閸楃偛袟闁汇劌瀚ú浼村冀閸ヮ剦鏆ラ悽顖ょ畵閳ь剙妫楅幃婊呮媼閹规劦鍚€闁哄倽顫夌涵?,
        6: "閻庡湱鍋ら悰娆戞媼閹规劦鍚€濞戞挸娴风划銊╁几濠婂啫鐎婚柡?,
        7: "閻犱降鍔忛鎴炵▔鎼达紕婀伴梻鍕姈閳ь儸鍐ㄧ€婚柡?,
        8: "缂備焦鎹侀鎴炵▔鎼达紕娼旈柡?,
    }
    for chapter, items in artifacts.items():
        root = chapter_dir(chapter)
        index_lines = [
            f"# 缂佹鎲hapter}缂佹梻濮村ù妯兼偘閵娧冨亶鐎殿喗娲╃槐鐨梒hapter_titles[chapter]}",
            "",
            f"闁哄牜鍓涘ú鎷屻亹閺囩喐娈婚柣鐐叉椤?{chapter} 缂佹梻濮鹃鎴﹀棘閸パ冩櫢濞达絾绮岃ぐ鏌ユ儎鐎涙ê澶嶅ù锝堟硶閺併倝鎯冮崟顐ｇ閻炴稏鍔庣粈宀勫级閹扳斁鍋?,
            "",
        ]
        guide_lines = [
            f"# 缂佹鎲hapter}缂佹梻濮村ù妯兼偘閵娿倕鈻忛柣顫姀椤曗晠寮版惔顖滅獥{chapter_titles[chapter]}",
            "",
            "閺夆晜鐟ら崬銈囨嫚鐎涙ɑ顫栭柟绋款槴閳ь剚绮屽ù妯兼偘閵娿儱鏁堕悗鐟扮畭閳ь兛鐒﹂埀顒€绨肩粻鐐烘儑鐎ｃ劉鍋撴担绛嬪晥闁哄倸娲ｉ懙鎴﹀箑鎼淬垻澹夊ù锝堟硶閺併倝鍨惧┑鍥ㄦ闁荤偛妫庨埀顒€鍊搁崯鎾愁潰閿濆棙鐎柡鍐╂构缁鳖參宕楅崼婵堢┛闁活潿鍔嶅﹢浼村棘閸ワ附顐藉☉鎿冨幘濞堟垿宕堕幆褎鍊抽柛婊冪焷琚欓梺鎻掞工瑜版稑顕ラ崟鈹惧亾?,
            "",
        ]
        for item in items:
            stem = Path(item["path"]).stem
            detailed = DETAILED_GUIDANCE.get(stem, {})
            content = detailed.get("content", item["note"])
            read = detailed.get("read", "闁稿繐鐗忓﹢鍛偓鐟板暙濠€顏堝嫉椤掑倻褰垮☉鎿冨幖濞叉牜绮甸弮鍌涚暠闁哄秶顭堢缓楣冩⒒椤曗偓椤ｄ粙鏁嶇仦钘夋櫃闁活亜顑呰ぐ澶愭煂韫囧鍋撴担鍦偊缂佸顑嗛崹銊╁箰閸ャ劎鍨煎☉鏂款儔濡潡鎯冮崟顓熺ゲ閻庣數鎳撻崣褏鍖栨导娆戝耿濞戞挸绉烽々锕傚矗椤忓懏鍠呴柛妤佹磻闁叉粓寮弶璺ㄦ憻闁挎稑鐭侀埀顒€鐭侀々锕傚嫉瀹ュ懎顫ょ紒鏃傚Ь婵☆厾鎷嬫ウ璺ㄦ闁?)
            use = detailed.get("use", f"闁衡偓閹勮含缂?{chapter} 缂佹梻濮撮顔芥償閺傝法姣堥柤鍝勫€块々璇测枎閳╁啫绲归柛鎴︾細椤曟岸姊婚鈧。鑺ョ▕鐎ｎ亝鍊甸柨娑樼灱閺併倕顫㈤敐鍡樼€柛蹇撶墣椤曗晠寮版惔婵婄濞寸姭鍋撳☉鏂跨墦濞撳墎鎲版担鐣岀鐎殿喚濮村ù姗€骞嬮弽顑锯偓鍐晬鐏炶棄鏅欓柣顫妺缁旀挳宕氭０浣解拡婵炲牅绲昏闂佹彃锕ら悾鐘诲绩椤栨稒瀚煎ù婊冩缁牊绋婇崼銏㈡尝閻犱焦浜介埀?)
            index_lines.append(f"- **{item['name']}**")
            index_lines.append(f"  - 缂侇偉顕ч悗鐑芥晬濮濈袱tem['kind']}")
            index_lines.append(f"  - 閻犱警鍨扮欢鐐烘晬濮濇item['path']}`")
            index_lines.append(f"  - 濠㈣泛娲﹂弫鐐烘晬濮濈笧ontent}")
            guide_lines.append(f"## {item['name']}")
            guide_lines.append("")
            guide_lines.append(f"- 闁哄倸娲ｅ▎銏㈡崉椤栨氨绐為柨娑欑摢{item['path']}`")
            guide_lines.append(f"- 闁告劕鎳庨鎰版晬濮濈笧ontent}")
            guide_lines.append(f"- 闁诡剙绨肩粻鐐烘儑鐎ｅ墎绐梴read}")
            guide_lines.append(f"- 閻犱胶鍎ら弸鍐╃▔椤撶啿鍋撴惔銏㈠濞达綀娉曢弫銈夋晬濮濈赴se}")
            guide_lines.append("")
        (root / f"chapter{chapter}_artifact_index.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
        (root / f"chapter{chapter}_artifact_guide.md").write_text("\n".join(guide_lines) + "\n", encoding="utf-8")

    master = [
        "# 閻犱胶鍎ら弸鍐触閸曨厾褰块柛銉﹀礃閵嗗啰妲愰悩铏稄闁诡剝宕甸崒銊ヮ嚕?,
        "",
        "闁哄牜鍓涢崒銊ヮ嚕閺囩姵鏆?`src/prediction/targetband_param/tools/build_thesis_chapter_artifacts_v1.py` 闁汇垻鍠愰崹姘跺Υ?,
        "婵絽绻嬬粩瀵哥博閻樺弶缍嗛柡鍫濐槺鐎氼厾绮╃€ｎ偅鐎ù鐘烘硾閵囨瑩濡存稊顤琲gures/`闁靛棔姊梩ables/`闁靛棔鑳堕崒銊ヮ嚕閺囩喐鐎ù鐘烘硾閹锋壆鎷犻敂鍓х煄閻犲洤鐡ㄥΣ鎴﹀棘閸ワ附顐介柕?,
        "",
    ]
    for chapter in range(1, 9):
        root = chapter_dir(chapter)
        master.append(f"## 缂佹鎲hapter}缂?{chapter_titles[chapter]}")
        master.append(f"- 闁烩晩鍠栫紞宥夋晬濮濇root}`")
        master.append(f"- 缂佷究鍨圭槐鈺呮晬濮濇root / f'chapter{chapter}_artifact_index.md'}`")
        master.append(f"- 閻犲洤鐡ㄥΣ鎴︽晬濮濇root / f'chapter{chapter}_artifact_guide.md'}`")
        for item in artifacts[chapter]:
            master.append(f"- {item['name']}闁挎稒鐡獅item['path']}`")
        master.append("")
    (ANALYSIS_DIR / "thesis_chapter_artifacts_index.md").write_text("\n".join(master), encoding="utf-8")


def main() -> None:
    set_plot_style()
    artifacts = build_static_tables()
    write_guides(artifacts)
    print(f"Wrote chapter artifacts under {ANALYSIS_DIR}")


if __name__ == "__main__":
    main()
