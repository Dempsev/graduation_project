from __future__ import annotations

import csv
import math
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np
from matplotlib.patches import Circle, Polygon, Rectangle


ROOT = Path(__file__).resolve().parents[4]
SHAPE_ID = "ep100_step18"
SHAPE_CSV = ROOT / "data" / "shape_contours" / f"{SHAPE_ID}_contour_xy.csv"
OUT_DIR = ROOT / "data" / "analysis" / "thesis_ch2_v1" / "figures"
OUT_BASE = OUT_DIR / "figure_2_x_snake_fourier_overlay_workflow_v1"


def configure_matplotlib() -> None:
    font_candidates = [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
    ]
    font_path = next((Path(p) for p in font_candidates if Path(p).is_file()), None)
    if font_path is not None:
        mpl.font_manager.fontManager.addfont(str(font_path))
        font_name = mpl.font_manager.FontProperties(fname=str(font_path)).get_name()
        mpl.rcParams["font.family"] = font_name
        mpl.rcParams["font.sans-serif"] = [font_name]
    mpl.rcParams.update(
        {
            "axes.unicode_minus": False,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "font.size": 8.5,
            "axes.linewidth": 0.7,
        }
    )


def read_xy(path: Path) -> np.ndarray:
    rows: list[tuple[float, float]] = []
    if path.exists():
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append((float(row["x"]), float(row["y"])))
    if not rows:
        return fallback_snake_boundary()
    xy = np.asarray(rows, dtype=float)
    if np.linalg.norm(xy[0] - xy[-1]) > 1e-12:
        xy = np.vstack([xy, xy[0]])
    return xy


def fallback_snake_boundary(n: int = 160) -> np.ndarray:
    t = np.linspace(0, 2 * math.pi, n, endpoint=True)
    r = 0.30 + 0.05 * np.sin(3 * t) + 0.035 * np.cos(5 * t)
    return np.column_stack([r * np.cos(t), 0.75 * r * np.sin(t)])


def normalize_polygon(xy: np.ndarray, width: float, center: tuple[float, float]) -> np.ndarray:
    work = xy.copy()
    work -= work.mean(axis=0)
    span = np.ptp(work, axis=0)
    scale = width / max(float(span[0]), float(span[1]), 1e-12)
    work *= scale
    work += np.asarray(center, dtype=float)
    return work


def fourier_boundary(n: int = 420) -> np.ndarray:
    t = np.linspace(0, 2 * math.pi, n, endpoint=True)
    coeffs = {
        1: (0.18, 0.05),
        2: (0.14, -0.06),
        3: (0.06, -0.05),
        4: (0.04, -0.02),
        5: (0.03, 0.01),
    }
    amp = np.ones_like(t)
    for k, (ak, bk) in coeffs.items():
        amp += ak * np.cos(k * t) + bk * np.sin(k * t)
    r = 0.34 * amp
    return np.column_stack([r * np.cos(t), r * np.sin(t)])


def panel_frame(ax: plt.Axes, title: str, letter: str) -> None:
    ax.set_aspect("equal")
    ax.set_xlim(-0.58, 0.58)
    ax.set_ylim(-0.58, 0.58)
    ax.axis("off")
    ax.text(-0.55, 0.54, letter, ha="left", va="top", weight="bold", fontsize=10)
    ax.text(0, -0.54, title, ha="center", va="bottom", fontsize=8.5)


def draw_unit_cell(ax: plt.Axes) -> None:
    ax.add_patch(
        Rectangle(
            (-0.5, -0.5),
            1.0,
            1.0,
            facecolor="#f4f6f8",
            edgecolor="#6b7280",
            linewidth=0.75,
            zorder=0,
        )
    )


def draw_fourier(ax: plt.Axes, xy: np.ndarray, fill: str = "#f3b2ad", edge: str = "#d84a3a") -> None:
    ax.add_patch(Polygon(xy, closed=True, facecolor=fill, edgecolor=edge, linewidth=1.3, alpha=0.82, zorder=2))


def draw_snake(ax: plt.Axes, xy: np.ndarray, fill: str = "#f7c948", edge: str = "#245a9a") -> None:
    ax.add_patch(Polygon(xy, closed=True, facecolor=fill, edgecolor=edge, linewidth=1.1, alpha=0.95, zorder=3))


def draw_binary_grid(ax: plt.Axes, snake_xy: np.ndarray) -> None:
    ax.add_patch(Rectangle((-0.42, -0.42), 0.84, 0.84, facecolor="#231942", edgecolor="#404056", linewidth=0.6))
    for i in range(13):
        x = -0.42 + i * 0.07
        y = -0.42 + i * 0.07
        ax.plot([x, x], [-0.42, 0.42], color="#3e3262", linewidth=0.25)
        ax.plot([-0.42, 0.42], [y, y], color="#3e3262", linewidth=0.25)
    draw_snake(ax, snake_xy, fill="#f7c948", edge="#f59e0b")
    ax.plot(snake_xy[:, 0], snake_xy[:, 1], color="#5aa7ff", linewidth=1.05, zorder=4)
    ax.text(-0.38, -0.36, SHAPE_ID, ha="left", va="center", fontsize=6.8, color="#cbd5e1")


def add_arrow(fig: plt.Figure, start: tuple[float, float], end: tuple[float, float]) -> None:
    ax = fig.add_axes([0, 0, 1, 1], zorder=-1)
    ax.axis("off")
    ax.annotate(
        "",
        xy=end,
        xycoords="figure fraction",
        xytext=start,
        textcoords="figure fraction",
        arrowprops=dict(arrowstyle="->", color="#344054", linewidth=1.1, shrinkA=0, shrinkB=0),
    )


def draw_mesh(ax: plt.Axes, fourier_xy: np.ndarray, snake_xy: np.ndarray) -> None:
    grid = np.linspace(-0.5, 0.5, 18)
    gx, gy = np.meshgrid(grid, grid)
    pts = np.column_stack([gx.ravel(), gy.ravel()])
    focus = np.array([[0.18, 0.18], [0.22, 0.24], [0.26, 0.18], [0.30, 0.28], [0.12, 0.30]])
    rng = np.random.default_rng(7)
    cloud = rng.normal(loc=(0.22, 0.21), scale=(0.11, 0.10), size=(95, 2))
    cloud = cloud[(np.abs(cloud[:, 0]) <= 0.5) & (np.abs(cloud[:, 1]) <= 0.5)]
    pts = np.vstack([pts, focus, cloud, fourier_xy[::18], snake_xy[::2]])
    tri = mtri.Triangulation(pts[:, 0], pts[:, 1])
    ax.triplot(tri, color="#7a7a7a", linewidth=0.35, alpha=0.85, zorder=1)
    draw_fourier(ax, fourier_xy, fill="#f3b2ad", edge="#d84a3a")
    draw_snake(ax, snake_xy, fill="#f7c948", edge="#d84a3a")


def main() -> None:
    configure_matplotlib()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    fourier_xy = fourier_boundary()
    raw_snake = read_xy(SHAPE_CSV)
    snake_panel = normalize_polygon(raw_snake, width=0.32, center=(0.08, 0.08))
    snake_overlay = normalize_polygon(raw_snake, width=0.22, center=(-0.26, 0.20))

    fig, axes = plt.subplots(1, 5, figsize=(12.8, 3.0), constrained_layout=False)
    fig.subplots_adjust(left=0.025, right=0.985, top=0.84, bottom=0.16, wspace=0.34)
    fig.text(
        0.5,
        0.95,
        "Snake-Fourier unit-cell construction and COMSOL mesh workflow",
        ha="center",
        va="top",
        fontsize=13,
        weight="bold",
    )

    panel_frame(axes[0], "Fourier base cell", "a")
    draw_unit_cell(axes[0])
    draw_fourier(axes[0], fourier_xy)
    axes[0].text(0.02, 0.02, r"$\Omega_F$", ha="center", va="center", fontsize=11, color="#8a1f11")
    axes[0].text(0, 0.47, "parametric contour", ha="center", va="center", fontsize=7.5)

    panel_frame(axes[1], "Snake raster contour", "b")
    draw_binary_grid(axes[1], snake_panel)
    axes[1].text(0, 0.47, "binary mask + contour", ha="center", va="center", fontsize=7.5)

    panel_frame(axes[2], "Overlay and merge", "c")
    draw_unit_cell(axes[2])
    draw_fourier(axes[2], fourier_xy)
    draw_snake(axes[2], snake_overlay)
    axes[2].add_patch(Circle((-0.24, 0.20), 0.085, fill=False, edgecolor="#1d4ed8", linewidth=0.9, linestyle="--"))
    axes[2].text(-0.13, 0.37, "local feature", ha="center", va="center", color="#1d4ed8", fontsize=7.4)

    panel_frame(axes[3], "Boolean unit cell", "d")
    draw_unit_cell(axes[3])
    draw_fourier(axes[3], fourier_xy, fill="#f2a7a1", edge="#cf3f32")
    draw_snake(axes[3], snake_overlay, fill="#f2a7a1", edge="#cf3f32")
    axes[3].text(0, 0.48, r"$\Omega=(\Omega_F\cup\Omega_S)\cap\Omega_{cell}$", ha="center", va="center", fontsize=8.5)

    panel_frame(axes[4], "Mesh and solve", "e")
    draw_unit_cell(axes[4])
    draw_mesh(axes[4], fourier_xy, snake_overlay)
    axes[4].text(0, 0.48, "COMSOL mesh", ha="center", va="center", fontsize=7.7)

    for x0, x1 in [(0.205, 0.235), (0.397, 0.427), (0.590, 0.620), (0.782, 0.812)]:
        add_arrow(fig, (x0, 0.50), (x1, 0.50))

    fig.text(
        0.5,
        0.055,
        "A Fourier contour and a snake-derived contour are combined before meshing and COMSOL dispersion calculation.",
        ha="center",
        va="center",
        fontsize=7.2,
        color="#475467",
    )

    fig.savefig(OUT_BASE.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(OUT_BASE.with_suffix(".png"), dpi=450, bbox_inches="tight")
    print(f"[SVG] {OUT_BASE.with_suffix('.svg')}")
    print(f"[PNG] {OUT_BASE.with_suffix('.png')}")


if __name__ == "__main__":
    main()
