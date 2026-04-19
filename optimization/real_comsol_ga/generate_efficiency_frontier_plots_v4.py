from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(r"d:\graduation_project\coad")
ANALYSIS_DIR = ROOT / "data" / "analysis" / "optimization_efficiency_frontier_v4"


RUN_LABELS = {
    "true_global_ga_v1": "True Global GA",
    "champion_funnel_v1": "Funnel v1",
    "champion_funnel_v2": "Funnel v2",
    "champion_funnel_v3": "Funnel v3",
    "champion_funnel_v4": "Funnel v4",
}

RUN_ORDER = [
    "true_global_ga_v1",
    "champion_funnel_v1",
    "champion_funnel_v2",
    "champion_funnel_v3",
    "champion_funnel_v4",
]

RUN_COLORS = {
    "true_global_ga_v1": "#222222",
    "champion_funnel_v1": "#4C78A8",
    "champion_funnel_v2": "#F58518",
    "champion_funnel_v3": "#54A24B",
    "champion_funnel_v4": "#E45756",
}


def style_axes(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, axis="y", color="#d9d9d9", linewidth=0.8, alpha=0.7)
    ax.set_axisbelow(True)


def plot_best_so_far() -> Path:
    df = pd.read_csv(ANALYSIS_DIR / "best_so_far_vs_evaluations.csv")
    fig, ax = plt.subplots(figsize=(10, 6))

    for run in RUN_ORDER:
        ax.plot(
            df["evaluations"],
            df[run],
            marker="o",
            linewidth=2.2,
            markersize=5,
            color=RUN_COLORS[run],
            label=RUN_LABELS[run],
        )

    style_axes(ax)
    ax.set_title("Best-so-far vs COMSOL Evaluations")
    ax.set_xlabel("COMSOL evaluations")
    ax.set_ylabel("Best gap gain (Hz)")
    ax.legend(frameon=False, loc="lower right")

    out_path = ANALYSIS_DIR / "best_so_far_vs_evaluations.png"
    fig.tight_layout()
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_thresholds() -> Path:
    df = pd.read_csv(ANALYSIS_DIR / "evals_to_thresholds.csv")
    long_rows = []
    for _, row in df.iterrows():
        threshold = row["threshold_hz"]
        for run in RUN_ORDER:
            value = row.get(run)
            if pd.notna(value):
                long_rows.append(
                    {
                        "threshold_hz": threshold,
                        "run": run,
                        "evaluations": float(value),
                    }
                )

    plot_df = pd.DataFrame(long_rows)

    fig, ax = plt.subplots(figsize=(10, 6))
    thresholds = sorted(plot_df["threshold_hz"].unique())
    bar_width = 0.16
    x_positions = list(range(len(thresholds)))

    for idx, run in enumerate(RUN_ORDER):
        subset = plot_df[plot_df["run"] == run]
        xs = [x + (idx - 2) * bar_width for x in x_positions]
        ys = []
        for threshold in thresholds:
            match = subset[subset["threshold_hz"] == threshold]
            ys.append(float(match["evaluations"].iloc[0]) if not match.empty else float("nan"))
        ax.bar(
            xs,
            ys,
            width=bar_width,
            color=RUN_COLORS[run],
            label=RUN_LABELS[run],
        )

    style_axes(ax)
    ax.set_title("Evaluations Needed to Reach Target Thresholds")
    ax.set_xlabel("Target threshold (Hz)")
    ax.set_ylabel("COMSOL evaluations")
    ax.set_xticks(x_positions)
    ax.set_xticklabels([f"{int(t)} Hz" for t in thresholds])
    ax.legend(frameon=False, loc="upper left", ncol=2)

    out_path = ANALYSIS_DIR / "evals_to_thresholds.png"
    fig.tight_layout()
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_final_best() -> Path:
    df = pd.read_csv(ANALYSIS_DIR / "final_best_vs_budget.csv")
    df["label"] = df["run_name"].map(RUN_LABELS)

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.bar(
        df["label"],
        df["final_best_hz"],
        color=[RUN_COLORS[run] for run in df["run_name"]],
        width=0.65,
    )
    style_axes(ax)
    ax.set_title("Final Best vs Total Budget")
    ax.set_xlabel("Optimization strategy")
    ax.set_ylabel("Final best gap gain (Hz)")
    ax.tick_params(axis="x", rotation=20)

    for idx, value in enumerate(df["final_best_hz"]):
        ax.text(idx, value + 0.15, f"{value:.2f}", ha="center", va="bottom", fontsize=9)

    out_path = ANALYSIS_DIR / "final_best_vs_budget.png"
    fig.tight_layout()
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return out_path


def write_manifest(paths: list[Path]) -> Path:
    summary = json.loads((ANALYSIS_DIR / "summary.json").read_text(encoding="utf-8"))
    payload = {
        "plots": [str(path) for path in paths],
        "available_runs": summary["available_runs"],
        "thresholds_hz": summary["thresholds_hz"],
        "checkpoints": summary["checkpoints"],
    }
    out_path = ANALYSIS_DIR / "plot_manifest_v4.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def main() -> None:
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    paths = [
        plot_best_so_far(),
        plot_thresholds(),
        plot_final_best(),
    ]
    manifest = write_manifest(paths)
    print(f"[DONE] wrote plots to {ANALYSIS_DIR}")
    print(f"[DONE] manifest: {manifest}")


if __name__ == "__main__":
    main()
