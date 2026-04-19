from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / 'data' / 'analysis' / 'optimization_efficiency_frontier_v4'
OUT_DIR.mkdir(parents=True, exist_ok=True)

THRESHOLDS = [40.0, 42.0, 44.0]
CHECKPOINTS = [72, 144, 216, 360, 560, 728, 1000]


@dataclass
class RunDef:
    name: str
    history_csvs: list[Path]


def read_history_best_curve(path: Path, prior_best: float = float('-inf')) -> tuple[list[float], float]:
    curve: list[float] = []
    best = prior_best
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                gain = float(row['gap34_gain_Hz'])
            except Exception:
                gain = float('-inf')
            if gain > best:
                best = gain
            curve.append(best)
    return curve, best


def summarize_run(run: RunDef) -> tuple[list[float], float]:
    curve: list[float] = []
    best = float('-inf')
    for history_csv in run.history_csvs:
        stage_curve, best = read_history_best_curve(history_csv, best)
        curve.extend(stage_curve)
    return curve, best


def evals_to_threshold(curve: list[float], threshold: float) -> int | None:
    for idx, value in enumerate(curve, 1):
        if value >= threshold:
            return idx
    return None


def checkpoint_rows(curves: dict[str, list[float]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for cp in CHECKPOINTS:
        row = {'evaluations': cp}
        for name, curve in curves.items():
            idx = min(cp, len(curve)) - 1
            row[name] = float(curve[idx]) if idx >= 0 else None
        rows.append(row)
    return rows


def threshold_rows(curves: dict[str, list[float]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for threshold in THRESHOLDS:
        row = {'threshold_hz': threshold}
        for name, curve in curves.items():
            row[name] = evals_to_threshold(curve, threshold)
        rows.append(row)
    return rows


def budget_rows(curves: dict[str, list[float]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for name, curve in curves.items():
        rows.append({
            'run_name': name,
            'evaluated_count': len(curve),
            'final_best_hz': float(curve[-1]) if curve else None,
        })
    return rows


def write_csv(path: Path, rows: Iterable[dict[str, object]]) -> None:
    rows = list(rows)
    if not rows:
        path.write_text('', encoding='utf-8')
        return
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    runs = [
        RunDef('true_global_ga_v1', [ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_true_global_ga_v1' / 'ga_history_v1.csv']),
        RunDef('champion_funnel_v1', [
            ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_ga_optimization_funnel_probe_v1' / 'ga_history_v1.csv',
            ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_ga_optimization_expansion_v1' / 'ga_history_v1.csv',
            ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_ga_optimization_duel_v1' / 'ga_history_v1.csv',
            ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_ga_optimization_champion_v1' / 'ga_history_v1.csv',
        ]),
        RunDef('champion_funnel_v2', [
            ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_ga_optimization_funnel_probe_v1' / 'ga_history_v1.csv',
            ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_ga_optimization_expansion_v1' / 'ga_history_v1.csv',
            ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_ga_optimization_duel_v2' / 'ga_history_v1.csv',
            ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_ga_optimization_champion_v2' / 'ga_history_v1.csv',
        ]),
        RunDef('champion_funnel_v3', [
            ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_ga_optimization_funnel_probe_v1' / 'ga_history_v1.csv',
            ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_ga_optimization_expansion_v1' / 'ga_history_v1.csv',
            ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_ga_optimization_duel_v2' / 'ga_history_v1.csv',
            ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_ga_optimization_champion_v3' / 'ga_history_v1.csv',
        ]),
        RunDef('champion_funnel_v4', [
            ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_ga_optimization_funnel_probe_v4' / 'ga_history_v1.csv',
            ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_ga_optimization_expansion_v4' / 'ga_history_v1.csv',
            ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_ga_optimization_duel_v4' / 'ga_history_v1.csv',
            ROOT / 'data' / 'comsol_batch' / 'comsol_in_loop_ga_optimization_champion_v4' / 'ga_history_v1.csv',
        ]),
    ]

    curves: dict[str, list[float]] = {}
    final_summary: dict[str, float] = {}
    for run in runs:
        if not all(path.is_file() for path in run.history_csvs):
            continue
        curve, best = summarize_run(run)
        curves[run.name] = curve
        final_summary[run.name] = best

    checkpoint = checkpoint_rows(curves)
    threshold = threshold_rows(curves)
    budget = budget_rows(curves)

    write_csv(OUT_DIR / 'best_so_far_vs_evaluations.csv', checkpoint)
    write_csv(OUT_DIR / 'evals_to_thresholds.csv', threshold)
    write_csv(OUT_DIR / 'final_best_vs_budget.csv', budget)

    payload = {
        'checkpoints': CHECKPOINTS,
        'thresholds_hz': THRESHOLDS,
        'available_runs': list(curves.keys()),
        'final_best_hz': final_summary,
    }
    (OUT_DIR / 'summary.json').write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'[DONE] wrote efficiency-frontier comparison to {OUT_DIR}')


if __name__ == '__main__':
    main()
