from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


@dataclass
class RunStats:
    name: str
    history_csvs: list[Path]
    search_summary_csvs: list[Path]
    evaluated_count: int
    best_gain_hz: float
    solve_success_count: int
    positive_gain_count: int


def read_history_best_curve(path: Path, prior_best: float = float("-inf")) -> tuple[list[float], float]:
    curve: list[float] = []
    best = prior_best
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                gain = float(row["gap34_gain_Hz"])
            except Exception:
                gain = float("-inf")
            if gain > best:
                best = gain
            curve.append(best)
    return curve, best


def read_search_summary(path: Path) -> tuple[int, float, int, int]:
    evaluated = 0
    best = float("-inf")
    solve_success = 0
    positive = 0
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            evaluated += int(float(row.get("solve_success_count", 0))) if "solve_success_count" in row else 0
            solve_success += int(float(row.get("solve_success_count", 0)))
            positive += int(float(row.get("positive_gain_count", 0)))
            try:
                best = max(best, float(row["best_gap34_gain_Hz"]))
            except Exception:
                pass
    return evaluated, best, solve_success, positive


def summarize_run(name: str, run_dirs: list[Path]) -> tuple[RunStats, list[float]]:
    history_csvs = [run_dir / "ga_history_v1.csv" for run_dir in run_dirs]
    search_summary_csvs = [run_dir / "ga_search_summary_v1.csv" for run_dir in run_dirs]

    curve: list[float] = []
    best = float("-inf")
    solve_success = 0
    positive = 0
    stage_best = float("-inf")
    for history_csv, search_summary_csv in zip(history_csvs, search_summary_csvs):
        stage_curve, best = read_history_best_curve(history_csv, best)
        curve.extend(stage_curve)
        _, stage_best, stage_solve_success, stage_positive = read_search_summary(search_summary_csv)
        solve_success += stage_solve_success
        positive += stage_positive

    return RunStats(
        name=name,
        history_csvs=history_csvs,
        search_summary_csvs=search_summary_csvs,
        evaluated_count=len(curve),
        best_gain_hz=best if best > stage_best else stage_best,
        solve_success_count=solve_success,
        positive_gain_count=positive,
    ), curve


def print_curve_checkpoints(name: str, curve: list[float], checkpoints: list[int]) -> None:
    print(f"[{name}] best-so-far checkpoints")
    for cp in checkpoints:
        idx = min(cp, len(curve)) - 1
        if idx < 0:
            continue
        print(f"  eval {cp:4d}: {curve[idx]:.6f} Hz")


def main() -> None:
    runs = {
        "true_global_ga_v1": [
            ROOT / "data" / "comsol_batch" / "comsol_in_loop_true_global_ga_v1",
        ],
        "champion_funnel_v1": [
            ROOT / "data" / "comsol_batch" / "comsol_in_loop_ga_optimization_funnel_probe_v1",
            ROOT / "data" / "comsol_batch" / "comsol_in_loop_ga_optimization_expansion_v1",
            ROOT / "data" / "comsol_batch" / "comsol_in_loop_ga_optimization_duel_v1",
            ROOT / "data" / "comsol_batch" / "comsol_in_loop_ga_optimization_champion_v1",
        ],
    }

    checkpoints = [72, 144, 216, 360, 560, 728, 1000]
    curves: dict[str, list[float]] = {}
    stats: list[RunStats] = []

    for name, run_dirs in runs.items():
        item, curve = summarize_run(name, run_dirs)
        stats.append(item)
        curves[name] = curve

    print("=== Final summary ===")
    for item in stats:
        print(
            f"{item.name}: evals={item.evaluated_count}, "
            f"best={item.best_gain_hz:.6f} Hz, "
            f"solve_success={item.solve_success_count}, "
            f"positive_gain={item.positive_gain_count}"
        )

    print()
    for name, curve in curves.items():
        print_curve_checkpoints(name, curve, checkpoints)
        print()


if __name__ == "__main__":
    main()
