"""Run Chapter 2 mesh validation through a shared MATLAB engine."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import matlab.engine


ROOT = Path(__file__).resolve().parents[1]


def connect_engine():
    engines = matlab.engine.find_matlab()
    print(f"available MATLAB engines: {engines}")
    if not engines:
        raise RuntimeError("No shared MATLAB engine is available. Please share a MATLAB session first.")
    preferred = "comsol_matlab" if "comsol_matlab" in engines else engines[0]
    print(f"connecting MATLAB engine: {preferred}")
    return matlab.engine.connect_matlab(preferred)


def main() -> None:
    eng = connect_engine()
    eng.addpath(str(ROOT / "research_validation"), nargout=0)
    eng.addpath(str(ROOT / "model_core"), nargout=0)
    eng.addpath(str(ROOT / "stage2_harmonics"), nargout=0)
    eng.addpath(str(ROOT / "stage2_harmonics_refine"), nargout=0)
    eng.addpath(str(ROOT / "optimization" / "real_comsol_ga"), nargout=0)
    eng.addpath(str(ROOT / "shared" / "optimization_matlab"), nargout=0)
    eng.run_ch2_mesh_independence_validation_v1(nargout=0)
    print("MATLAB mesh validation completed.")

    stats_script = ROOT / "research_validation" / "build_ch2_reliability_stats_v1.py"
    subprocess.run([sys.executable, str(stats_script)], cwd=ROOT, check=True)

    marker = {
        "mesh_output_dir": str(ROOT / "data" / "research_validation" / "ch2_mesh_reliability_v1"),
    }
    print(json.dumps(marker, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
