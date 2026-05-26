"""Export Chapter 2.6 figures through shared MATLAB engine."""

from __future__ import annotations

from pathlib import Path

import matlab.engine


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    engines = matlab.engine.find_matlab()
    print(f"available MATLAB engines: {engines}")
    if not engines:
        raise RuntimeError("No shared MATLAB engine found.")
    eng = matlab.engine.connect_matlab("comsol_matlab" if "comsol_matlab" in engines else engines[0])
    eng.addpath(str(ROOT / "research_validation" / "ch2_typical_dispersion"), nargout=0)
    eng.export_ch2_typical_figures_v1(nargout=0)


if __name__ == "__main__":
    main()
