"""Run Chapter 2.6 typical local perturbation validation via shared MATLAB engine."""

from __future__ import annotations

import argparse
from pathlib import Path

import matlab.engine


ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", default="comsol_matlab")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--max-count", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    engines = matlab.engine.find_matlab()
    print(f"available MATLAB engines: {engines}")
    if not engines:
        raise RuntimeError("No shared MATLAB engine found.")
    engine_name = args.engine if args.engine in engines else engines[0]
    print(f"connecting MATLAB engine: {engine_name}")
    eng = matlab.engine.connect_matlab(engine_name)

    paths = [
        ROOT / "research_validation" / "ch2_typical_dispersion",
        ROOT / "model_core",
        ROOT / "stage2_harmonics",
        ROOT / "stage2_harmonics_refine",
        ROOT / "optimization" / "real_comsol_ga",
        ROOT / "shared" / "optimization_matlab",
    ]
    for path in paths:
        eng.addpath(str(path), nargout=0)

    eng.run_ch2_typical_local_perturb_validation_v1(float(args.start), float(args.max_count), nargout=0)


if __name__ == "__main__":
    main()
