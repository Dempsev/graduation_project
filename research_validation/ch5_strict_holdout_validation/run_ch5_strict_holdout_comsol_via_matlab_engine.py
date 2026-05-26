from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matlab.engine

ROOT = Path(r"D:\graduation_project\coad")
WORK_DIR = ROOT / "research_validation" / "ch5_strict_holdout_validation"
MANIFEST = WORK_DIR / "ch5_strict_holdout_comsol_manifest_top5_random5.csv"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", default="comsol_matlab")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=0)
    parser.add_argument("--result-name", default="ch5_strict_holdout_comsol_results_top5_random5.csv")
    args = parser.parse_args()

    end_arg = "inf" if args.end <= 0 else str(args.end)
    result_csv = WORK_DIR / args.result_name

    eng = matlab.engine.connect_matlab(args.engine)
    print(f"[CONNECTED] {args.engine}", flush=True)
    eng.cd(str(ROOT), nargout=0)
    eng.addpath(str(WORK_DIR), nargout=0)
    cmd = (
        "run_ch5_strict_holdout_comsol_manifest_v1("
        f"'{str(MANIFEST)}',"
        f"'{str(result_csv)}',"
        f"{args.start},"
        f"{end_arg});"
    )
    print(f"[RUN] {cmd}", flush=True)
    eng.eval(cmd, nargout=0)
    print(f"[DONE] {args.engine} rows {args.start}:{end_arg}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr, flush=True)
        raise
