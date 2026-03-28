from __future__ import annotations

import argparse
import csv
import itertools
import json
import random
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Sequence


ROOT = Path(__file__).resolve().parents[1]
ML_RUNS_ROOT = ROOT / "data" / "ml_runs"
SESSION_PARENT = ML_RUNS_ROOT / "stage3_autoresearch"
CLASSIFIER_SCRIPT = ROOT / "stage3_training" / "train_mlp_classifier_v7.py"
REGRESSOR_SCRIPT = ROOT / "stage3_training" / "train_mlp_regressor_v7.py"
SCORING_SCRIPT = ROOT / "stage3_training" / "run_seed_discovery_scoring_v7.py"
DEFAULT_SCORING_DATASET = ROOT / "data" / "ml_dataset" / "v10" / "candidate_pool_v10_seed_only_refined" / "candidate_pool_v10.csv"
DEFAULT_CONTACT_RUN_ROOT = ML_RUNS_ROOT / "mlp_contact_valid_parametric_seed_discovery_v7_full"
DEFAULT_POSITIVE_RUN_ROOT = ML_RUNS_ROOT / "mlp_is_positive_shape_parametric_seed_discovery_v7_full"
DEFAULT_REG_RUN_ROOT = ML_RUNS_ROOT / "mlp_gap34_gain_surrogate_v7_full"

CLASSIFIER_FEATURE_PRESETS = [
    "parametric_core",
    "parametric_directional",
    "parametric_seed_discovery",
]

REGRESSOR_FEATURE_PRESETS = [
    "surrogate_core",
    "surrogate_directional",
    "surrogate_seed_discovery",
    "surrogate_directional_geo_augmented",
]

HIDDEN_DIMS_OPTIONS = ["64,64", "128,64", "128,128,64", "256,128"]
DROPOUT_OPTIONS = [0.0, 0.05, 0.10, 0.15]
LR_OPTIONS = [3e-4, 1e-3, 2e-3]
WEIGHT_DECAY_OPTIONS = [1e-6, 1e-5, 1e-4]
BATCH_SIZE_OPTIONS = [32, 64]
CLASSIFIER_THRESHOLD_OPTIONS = [0.45, 0.50, 0.55]
SCORING_CONTACT_THRESHOLD_OPTIONS = [0.45, 0.50, 0.55, 0.60]
SCORING_POSITIVE_THRESHOLD_OPTIONS = [0.40, 0.45, 0.50, 0.55]
SCORING_CONTACT_WEIGHT_OPTIONS = [0.55, 0.65, 0.70, 0.75, 0.80]
SCORING_REG_MIN_OPTIONS = [0.0, 5.0, 10.0, 20.0]
SCORING_TOP_K_OPTIONS = [12, 16]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a small stage-3 autoresearch loop over existing training scripts.")
    parser.add_argument("--mode", required=True, choices=["classifier", "regressor", "scoring"])
    parser.add_argument("--task", default="contact_valid", choices=["contact_valid", "is_positive_shape"])
    parser.add_argument("--target", default="gap34_gain_Hz", choices=["gap34_gain_Hz", "gap34_Hz", "gap34_rel", "gap34_gain_rel"])
    parser.add_argument("--objective-group", default="shape_family", choices=["shape_id", "shape_family", "none"])
    parser.add_argument("--dataset", type=Path, default=DEFAULT_SCORING_DATASET)
    parser.add_argument("--contact-run-root", type=Path, default=DEFAULT_CONTACT_RUN_ROOT)
    parser.add_argument("--positive-run-root", type=Path, default=DEFAULT_POSITIVE_RUN_ROOT)
    parser.add_argument("--reg-run-root", type=Path, default=DEFAULT_REG_RUN_ROOT)
    parser.add_argument("--trials", type=int, default=6)
    parser.add_argument("--epochs", type=int, default=120)
    parser.add_argument("--seed", type=int, default=20260325)
    parser.add_argument("--session-name", default="")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def build_session_name(args: argparse.Namespace) -> str:
    if args.session_name:
        return args.session_name
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.mode == "classifier":
        return f"{stamp}_{args.mode}_{args.task}"
    if args.mode == "scoring":
        return f"{stamp}_{args.mode}_seed_discovery"
    return f"{stamp}_{args.mode}_{args.target}"


def classifier_candidates() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for feature_preset, hidden_dims, dropout, lr, weight_decay, batch_size, threshold in itertools.product(
        CLASSIFIER_FEATURE_PRESETS,
        HIDDEN_DIMS_OPTIONS,
        DROPOUT_OPTIONS,
        LR_OPTIONS,
        WEIGHT_DECAY_OPTIONS,
        BATCH_SIZE_OPTIONS,
        CLASSIFIER_THRESHOLD_OPTIONS,
    ):
        rows.append(
            {
                "feature_preset": feature_preset,
                "hidden_dims": hidden_dims,
                "dropout": dropout,
                "lr": lr,
                "weight_decay": weight_decay,
                "batch_size": batch_size,
                "threshold": threshold,
            }
        )
    return rows


def regressor_candidates() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for feature_preset, hidden_dims, dropout, lr, weight_decay, batch_size in itertools.product(
        REGRESSOR_FEATURE_PRESETS,
        HIDDEN_DIMS_OPTIONS,
        DROPOUT_OPTIONS,
        LR_OPTIONS,
        WEIGHT_DECAY_OPTIONS,
        BATCH_SIZE_OPTIONS,
    ):
        rows.append(
            {
                "feature_preset": feature_preset,
                "hidden_dims": hidden_dims,
                "dropout": dropout,
                "lr": lr,
                "weight_decay": weight_decay,
                "batch_size": batch_size,
            }
        )
    return rows


def scoring_candidates() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for contact_threshold, positive_threshold, contact_weight, reg_min, top_k in itertools.product(
        SCORING_CONTACT_THRESHOLD_OPTIONS,
        SCORING_POSITIVE_THRESHOLD_OPTIONS,
        SCORING_CONTACT_WEIGHT_OPTIONS,
        SCORING_REG_MIN_OPTIONS,
        SCORING_TOP_K_OPTIONS,
    ):
        rows.append(
            {
                "contact_threshold": contact_threshold,
                "positive_threshold": positive_threshold,
                "contact_weight": contact_weight,
                "positive_weight": round(1.0 - contact_weight, 6),
                "reg_min": reg_min,
                "top_k": top_k,
            }
        )
    return rows


def choose_trials(args: argparse.Namespace) -> List[Dict[str, object]]:
    if args.mode == "classifier":
        space = classifier_candidates()
    elif args.mode == "regressor":
        space = regressor_candidates()
    else:
        space = scoring_candidates()
    rng = random.Random(args.seed)
    rng.shuffle(space)
    return space[: max(1, min(args.trials, len(space)))]


def compute_patience(epochs: int) -> int:
    return max(12, min(80, epochs // 3))


def build_run_name(session_name: str, args: argparse.Namespace, trial_index: int) -> str:
    label = f"{args.mode}_trial_{trial_index:03d}"
    return str(Path("stage3_autoresearch") / session_name / "trials" / label)


def save_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: Sequence[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        fieldnames = ["trial_index"]
    else:
        key_order: List[str] = []
        seen = set()
        for row in rows:
            for key in row.keys():
                if key not in seen:
                    seen.add(key)
                    key_order.append(key)
        fieldnames = key_order
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def load_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def metric_summary(mode: str, metrics: Dict[str, object]) -> Dict[str, float]:
    if mode == "classifier":
        val = metrics["val"]
        test = metrics["test"]
        val_f1 = float(val["f1"])
        val_bal_acc = float(val["balanced_accuracy"])
        if val_bal_acc < 0.55:
            objective = 0.25 * val_f1 + 0.75 * val_bal_acc
        else:
            objective = 0.40 * val_f1 + 0.60 * val_bal_acc
        return {
            "objective": objective,
            "val_f1": val_f1,
            "val_bal_acc": val_bal_acc,
            "test_f1": float(test["f1"]),
            "test_bal_acc": float(test["balanced_accuracy"]),
            "test_accuracy": float(test["accuracy"]),
        }
    if mode == "regressor":
        val = metrics["val"]
        test = metrics["test"]
        return {
            "objective": -float(val["rmse"]),
            "val_rmse": float(val["rmse"]),
            "val_mae": float(val["mae"]),
            "val_r2": float(val["r2"]),
            "test_rmse": float(test["rmse"]),
            "test_mae": float(test["mae"]),
            "test_r2": float(test["r2"]),
        }
    return {
        "objective": float(metrics["objective"]),
        "rows_total": int(metrics["rows_total"]),
        "rows_cascade_gate": int(metrics["rows_cascade_gate"]),
        "cascade_gate_rate": float(metrics["cascade_gate_rate"]),
        "top_k": int(metrics["top_k"]),
        "top_k_gate_count": int(metrics["top_k_gate_count"]),
        "top_k_strong_positive_count": int(metrics["top_k_strong_positive_count"]),
        "top_k_weak_positive_count": int(metrics["top_k_weak_positive_count"]),
        "top_k_mean_stage1_gain": float(metrics["top_k_mean_stage1_gain"]),
    }


def collect_scoring_summary(run_root: Path) -> Dict[str, float]:
    metrics = load_json(run_root / "seed_discovery_metrics.json")
    top_candidates = load_csv_rows(run_root / "seed_discovery_top_candidates.csv")
    gain_values: List[float] = []
    contact_prob_values: List[float] = []
    positive_prob_values: List[float] = []
    cascade_score_values: List[float] = []
    surrogate_values: List[float] = []
    tier_scores: List[float] = []
    for row in top_candidates:
        try:
            gain_raw = str(row.get("stage1_reference_gap_gain_Hz", "")).strip()
            if gain_raw:
                gain_values.append(float(gain_raw))
        except ValueError:
            pass
        try:
            contact_raw = str(row.get("contact_prob", "")).strip()
            if contact_raw:
                contact_prob_values.append(float(contact_raw))
        except ValueError:
            pass
        try:
            positive_raw = str(row.get("positive_prob", "")).strip()
            if positive_raw:
                positive_prob_values.append(float(positive_raw))
        except ValueError:
            pass
        try:
            cascade_raw = str(row.get("cascade_score", "")).strip()
            if cascade_raw:
                cascade_score_values.append(float(cascade_raw))
        except ValueError:
            pass
        try:
            surrogate_raw = str(row.get("surrogate_pred_gap34_gain_Hz", "")).strip()
            if surrogate_raw:
                surrogate_values.append(float(surrogate_raw))
        except ValueError:
            pass
        tier_text = str(row.get("stage1_reference_candidate_tier", "")).strip()
        if tier_text == "strong_positive":
            tier_scores.append(2.0)
        elif tier_text == "weak_positive":
            tier_scores.append(1.0)
        elif tier_text:
            tier_scores.append(0.0)

    top_k_mean_stage1_gain = sum(gain_values) / len(gain_values) if gain_values else 0.0
    mean_contact_prob = sum(contact_prob_values) / len(contact_prob_values) if contact_prob_values else 0.0
    mean_positive_prob = sum(positive_prob_values) / len(positive_prob_values) if positive_prob_values else 0.0
    mean_cascade_score = sum(cascade_score_values) / len(cascade_score_values) if cascade_score_values else 0.0
    mean_surrogate = sum(surrogate_values) / len(surrogate_values) if surrogate_values else 0.0
    mean_tier_score = sum(tier_scores) / len(tier_scores) if tier_scores else 0.0
    objective = (
        float(metrics["top_k_gate_count"])
        + 0.35 * float(metrics["top_k_strong_positive_count"])
        + 0.15 * float(metrics["top_k_weak_positive_count"])
        + 1.20 * mean_cascade_score
        + 0.60 * mean_contact_prob
        + 0.30 * mean_positive_prob
        + 0.20 * mean_tier_score
        + 0.003 * top_k_mean_stage1_gain
        + 0.0005 * mean_surrogate
    )
    return {
        "objective": objective,
        "rows_total": int(metrics["rows_total"]),
        "rows_cascade_gate": int(metrics["rows_cascade_gate"]),
        "cascade_gate_rate": float(metrics["cascade_gate_rate"]),
        "top_k": int(metrics["top_k"]),
        "top_k_gate_count": int(metrics["top_k_gate_count"]),
        "top_k_strong_positive_count": int(metrics["top_k_strong_positive_count"]),
        "top_k_weak_positive_count": int(metrics["top_k_weak_positive_count"]),
        "top_k_mean_stage1_gain": float(top_k_mean_stage1_gain),
        "top_k_mean_contact_prob": float(mean_contact_prob),
        "top_k_mean_positive_prob": float(mean_positive_prob),
        "top_k_mean_cascade_score": float(mean_cascade_score),
        "top_k_mean_surrogate_pred": float(mean_surrogate),
        "top_k_mean_tier_score": float(mean_tier_score),
    }


def load_csv_rows(path: Path) -> List[Dict[str, object]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def run_trial(
    args: argparse.Namespace,
    session_name: str,
    trial_index: int,
    proposal: Dict[str, object],
) -> Dict[str, object]:
    run_name = build_run_name(session_name, args, trial_index)
    run_root = ML_RUNS_ROOT / run_name
    if args.mode == "scoring":
        summary_path = run_root / "seed_discovery_metrics.json"
        base_cmd = [
            sys.executable,
            str(SCORING_SCRIPT),
            "--dataset",
            str(args.dataset),
            "--contact-run-root",
            str(args.contact_run_root),
            "--positive-run-root",
            str(args.positive_run_root),
            "--reg-run-root",
            str(args.reg_run_root),
            "--run-name",
            run_name,
            "--contact-threshold",
            str(proposal["contact_threshold"]),
            "--positive-threshold",
            str(proposal["positive_threshold"]),
            "--contact-weight",
            str(proposal["contact_weight"]),
            "--positive-weight",
            str(proposal["positive_weight"]),
            "--reg-min",
            str(proposal["reg_min"]),
            "--top-k",
            str(proposal["top_k"]),
        ]
    else:
        split_metrics_path = run_root / args.objective_group / "metrics.json"
        base_cmd = [
            sys.executable,
            str(CLASSIFIER_SCRIPT if args.mode == "classifier" else REGRESSOR_SCRIPT),
            "--feature-preset",
            str(proposal["feature_preset"]),
            "--group-keys",
            args.objective_group,
            "--run-name",
            run_name,
            "--epochs",
            str(args.epochs),
            "--batch-size",
            str(proposal["batch_size"]),
            "--hidden-dims",
            str(proposal["hidden_dims"]),
            "--dropout",
            str(proposal["dropout"]),
            "--lr",
            str(proposal["lr"]),
            "--weight-decay",
            str(proposal["weight_decay"]),
            "--patience",
            str(compute_patience(args.epochs)),
            "--seed",
            str(args.seed + trial_index),
        ]
        if args.mode == "classifier":
            base_cmd.extend(["--task", args.task, "--threshold", str(proposal["threshold"])])
        else:
            base_cmd.extend(["--target", args.target])

    started = time.time()
    proc = subprocess.run(
        base_cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    elapsed = time.time() - started

    result: Dict[str, object] = {
        "trial_index": trial_index,
        "mode": args.mode,
        "run_name": run_name,
        "run_root": str(run_root),
        "objective_group": args.objective_group,
        "status": "ok" if proc.returncode == 0 else "failed",
        "return_code": proc.returncode,
        "elapsed_sec": round(elapsed, 3),
        **proposal,
    }

    if proc.stdout:
        (run_root / "autoresearch_stdout.log").write_text(proc.stdout, encoding="utf-8")
    if proc.stderr:
        (run_root / "autoresearch_stderr.log").write_text(proc.stderr, encoding="utf-8")

    if proc.returncode != 0:
        result["error"] = (proc.stderr or proc.stdout or "subprocess failed").strip()[-1200:]
        return result

    if args.mode == "scoring":
        if not summary_path.exists():
            result["status"] = "failed"
            result["error"] = f"Expected scoring metrics file not found: {summary_path}"
            return result
        metrics = collect_scoring_summary(run_root)
        result.update(metric_summary(args.mode, metrics))
    else:
        if not split_metrics_path.exists():
            result["status"] = "failed"
            result["error"] = f"Expected metrics file not found: {split_metrics_path}"
            return result
        metrics = load_json(split_metrics_path)
        result.update(metric_summary(args.mode, metrics))
    return result


def sort_results(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    def key_fn(item: Dict[str, object]) -> tuple:
        status = 1 if item.get("status") == "ok" else 0
        objective = float(item.get("objective", -1e18))
        elapsed = -float(item.get("elapsed_sec", 0.0))
        return (status, objective, elapsed)

    return sorted(rows, key=key_fn, reverse=True)


def main() -> None:
    args = parse_args()
    session_name = build_session_name(args)
    session_root = SESSION_PARENT / session_name
    session_root.mkdir(parents=True, exist_ok=True)

    proposals = choose_trials(args)
    planned_rows: List[Dict[str, object]] = []
    for idx, proposal in enumerate(proposals, start=1):
        planned_rows.append(
            {
                "trial_index": idx,
                "mode": args.mode,
                "objective_group": args.objective_group,
                "epochs": args.epochs,
                "seed": args.seed + idx,
                "run_name": build_run_name(session_name, args, idx),
                **proposal,
            }
        )

    session_config = {
        "mode": args.mode,
        "task": args.task,
        "target": args.target,
        "dataset": str(args.dataset),
        "contact_run_root": str(args.contact_run_root),
        "positive_run_root": str(args.positive_run_root),
        "reg_run_root": str(args.reg_run_root),
        "objective_group": args.objective_group,
        "trials": len(proposals),
        "epochs": args.epochs,
        "seed": args.seed,
        "session_name": session_name,
        "session_root": str(session_root),
        "dry_run": bool(args.dry_run),
        "prototype_version": "v1",
    }
    save_json(session_root / "session_config.json", session_config)
    save_json(session_root / "planned_trials.json", planned_rows)

    print(f"[SESSION] {session_name}")
    print(f"[ROOT] {session_root}")
    print(f"[PLANNED] trials={len(proposals)} mode={args.mode} objective_group={args.objective_group}")

    if args.dry_run:
        for row in planned_rows:
            if args.mode == "scoring":
                print(
                    "[DRY-RUN] "
                    f"trial={row['trial_index']:03d} run={row['run_name']} "
                    f"ct={row['contact_threshold']} pt={row['positive_threshold']} "
                    f"cw={row['contact_weight']} reg_min={row['reg_min']} top_k={row['top_k']}"
                )
            else:
                print(f"[DRY-RUN] trial={row['trial_index']:03d} run={row['run_name']} feature={row['feature_preset']} hidden={row['hidden_dims']}")
        print("[DONE] dry-run only")
        return

    results: List[Dict[str, object]] = []
    for idx, proposal in enumerate(proposals, start=1):
        if args.mode == "scoring":
            print(
                f"[TRIAL] {idx}/{len(proposals)} "
                f"ct={proposal['contact_threshold']} pt={proposal['positive_threshold']} "
                f"cw={proposal['contact_weight']} reg_min={proposal['reg_min']} top_k={proposal['top_k']}"
            )
        else:
            print(f"[TRIAL] {idx}/{len(proposals)} feature={proposal['feature_preset']} hidden={proposal['hidden_dims']} dropout={proposal['dropout']} lr={proposal['lr']}")
        result = run_trial(args, session_name, idx, proposal)
        results.append(result)
        ranked = sort_results(results)
        write_csv(session_root / "leaderboard.csv", ranked)
        save_json(session_root / "results.json", ranked)
        if ranked and ranked[0].get("status") == "ok":
            save_json(session_root / "best_trial.json", ranked[0])

        if result["status"] == "ok":
            objective = float(result["objective"])
            print(f"[RESULT] trial={idx:03d} objective={objective:.6f} run={result['run_name']}")
        else:
            print(f"[RESULT] trial={idx:03d} failed")

    ranked = sort_results(results)
    ok_rows = [row for row in ranked if row.get("status") == "ok"]
    if not ok_rows:
        raise RuntimeError(f"No successful trials completed. See {session_root}")

    best = ok_rows[0]
    save_json(session_root / "best_trial.json", best)

    print("[DONE] stage-3 autoresearch session complete")
    print(f"[BEST] run={best['run_name']} objective={float(best['objective']):.6f}")


if __name__ == "__main__":
    main()
