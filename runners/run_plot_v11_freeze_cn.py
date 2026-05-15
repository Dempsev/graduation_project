from __future__ import annotations

import matlab.engine


def main() -> None:
    eng = matlab.engine.connect_matlab("comsol_matlab")
    eng.eval(
        "run('D:/graduation_project/coad/postprocess/plot_v11_freeze_cn.m')",
        nargout=0,
    )


if __name__ == "__main__":
    main()
