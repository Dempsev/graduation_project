from __future__ import annotations

from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager


ROOT = Path(__file__).resolve().parents[2]
BASE_DIR = ROOT / "research_validation" / "ch4_ga_real_optimization"
FIG_DIR = BASE_DIR / "figures"
MANIFEST = FIG_DIR / "ch4_fig4_6_comsol_unit_cell_export_manifest.csv"

BAND_ORDER = [
    "band140_180",
    "band160_200",
    "band180_220",
    "band200_240",
    "band220_260",
    "band240_280",
]
BAND_LABELS = {
    "band140_180": "140–180 Hz",
    "band160_200": "160–200 Hz",
    "band180_220": "180–220 Hz",
    "band200_240": "200–240 Hz",
    "band220_260": "220–260 Hz",
    "band240_280": "240–280 Hz",
}


def configure_fonts() -> str:
    candidates = [
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
    ]
    font_name = "DejaVu Sans"
    for path in candidates:
        if path.exists():
            font_manager.fontManager.addfont(str(path))
            font_name = font_manager.FontProperties(fname=str(path)).get_name()
            break
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [font_name, "DejaVu Sans"],
            "axes.unicode_minus": False,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
        }
    )
    return font_name


def save_all(fig: plt.Figure, stem: str) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for ext in ["png", "svg", "pdf"]:
        path = FIG_DIR / f"{stem}.{ext}"
        if ext == "png":
            fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
        else:
            fig.savefig(path, bbox_inches="tight", facecolor="white")
        paths[ext] = path
    plt.close(fig)
    return paths


def make_montage(df: pd.DataFrame) -> dict[str, Path]:
    df = df.set_index("target_band_tag").loc[BAND_ORDER].reset_index()
    fig, axes = plt.subplots(2, 3, figsize=(7.6, 6.2))
    for ax, (_, row) in zip(axes.ravel(), df.iterrows()):
        image = mpimg.imread(row["png_path"])
        ax.imshow(image)
        ax.axis("off")
        band = BAND_LABELS[row["target_band_tag"]]
        overlap = float(row["best_target_overlap_Hz"])
        shape_id = row["shape_id"]
        title = f"{band}\n{shape_id}，{overlap:.2f} Hz"
        ax.set_title(title, fontsize=7.2, color="#222222", pad=4)
    fig.suptitle("六个目标频带最优结构完整单胞图", fontsize=12, color="#222222", y=0.97)
    fig.subplots_adjust(left=0.025, right=0.975, bottom=0.035, top=0.88, wspace=0.16, hspace=0.42)
    return save_all(fig, "ch4_fig4_6_best_unit_cells_6bands_comsol")


def write_readme(font_name: str, outputs: dict[str, Path]) -> Path:
    df = pd.read_csv(MANIFEST, encoding="utf-8-sig")
    readme = FIG_DIR / "CH4_COMSOL_UNIT_CELL_EXPORT_README.md"
    lines: list[str] = [
        "# 第4章 COMSOL 完整单胞图导出说明",
        "",
        "本次导出基于六个目标频带 20 代真实 COMSOL-GA 的最优候选记录，重新构建 COMSOL 几何并导出完整单胞图。导出过程只构建几何，不重新运行频散求解，不改动原始 GA 数据。",
        "",
        f"- 拼图 PNG：`{outputs['png'].name}`",
        f"- 拼图 SVG：`{outputs['svg'].name}`",
        f"- 拼图 PDF：`{outputs['pdf'].name}`",
        f"- 导出清单：`{MANIFEST.name}`",
        f"- 拼图字体：{font_name}",
        "",
        "## 单图文件",
        "",
        "| 目标频带 | shape_id | target_overlap_Hz | PNG | SVG | PDF |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    df = df.set_index("target_band_tag").loc[BAND_ORDER].reset_index()
    for _, row in df.iterrows():
        lines.append(
            "| "
            f"{BAND_LABELS[row['target_band_tag']]} | "
            f"`{row['shape_id']}` | "
            f"{float(row['best_target_overlap_Hz']):.2f} | "
            f"`{Path(row['png_path']).name}` | "
            f"`{Path(row['svg_path']).name}` | "
            f"`{Path(row['pdf_path']).name}` |"
        )
    lines.append("")
    lines.append("说明：单图为 MATLAB LiveLink 调用 COMSOL `mphgeom` 导出的几何视图；2×3 拼图由上述 COMSOL 导出 PNG 组版生成。")
    readme.write_text("\n".join(lines), encoding="utf-8")
    return readme


def main() -> None:
    font_name = configure_fonts()
    df = pd.read_csv(MANIFEST, encoding="utf-8-sig")
    outputs = make_montage(df)
    readme = write_readme(font_name, outputs)
    print("# COMSOL 完整单胞图拼图已生成")
    for ext, path in outputs.items():
        print(f"{ext}: {path}")
    print(f"README: {readme}")


if __name__ == "__main__":
    main()
