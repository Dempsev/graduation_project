from __future__ import annotations

import matlab.engine


def main() -> None:
    eng = matlab.engine.connect_matlab("comsol_matlab")
    eng.eval(
        "run('D:/graduation_project/coad/runners/run_stage4_validation_multiband_predictor_top1_v1.m')",
        nargout=0,
    )


if __name__ == "__main__":
    main()
