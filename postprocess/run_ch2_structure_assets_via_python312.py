from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMSOL_SERVER = Path(r"D:\COMSOL\COMSOL63\Multiphysics\bin\win64\comsolmphserver.exe")
MATLAB_EXE = Path(r"D:\MatlabR2024b\matlab\bin\matlab.exe")
COMSOL_MLI = Path(r"D:\COMSOL\COMSOL63\Multiphysics\mli")
PORT = 2036
OUT_DIR = ROOT / "data" / "analysis" / "thesis_ch2_v1" / "structure_construction_assets_ep100_step18"


def safe_print(text: str) -> None:
    data = text.encode("utf-8", errors="replace")
    sys.stdout.buffer.write(data)
    if not text.endswith("\n"):
        sys.stdout.buffer.write(b"\n")
    sys.stdout.buffer.flush()


def wait_for_port(port: int, timeout_s: float = 90.0) -> None:
    deadline = time.time() + timeout_s
    last_error: OSError | None = None
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1.5):
                return
        except OSError as exc:
            last_error = exc
            time.sleep(1.0)
    raise RuntimeError(f"COMSOL server did not open port {port} within {timeout_s:.0f}s: {last_error}")


def main() -> int:
    for path in (COMSOL_SERVER, MATLAB_EXE, COMSOL_MLI):
        if not path.exists():
            raise FileNotFoundError(path)

    server_cmd = [str(COMSOL_SERVER), "-port", str(PORT), "-silent"]
    print("[START]", " ".join(server_cmd), flush=True)
    server = subprocess.Popen(
        server_cmd,
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    try:
        wait_for_port(PORT)
        print(f"[READY] COMSOL server is listening on port {PORT}", flush=True)

        matlab_expr = (
            f"addpath('{COMSOL_MLI.as_posix()}'); "
            f"mphstart({PORT}); "
            f"addpath(genpath('{ROOT.as_posix()}')); "
            "export_ch2_structure_construction_assets_v1"
        )
        matlab_cmd = [str(MATLAB_EXE), "-batch", matlab_expr]
        print("[MATLAB]", " ".join(matlab_cmd), flush=True)
        result = subprocess.run(
            matlab_cmd,
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=700,
        )
        safe_print(result.stdout)
        if result.returncode != 0:
            print(f"[ERROR] MATLAB exited with {result.returncode}", file=sys.stderr, flush=True)
            return result.returncode

        required = [
            "01_fourier_mother_boundary.png",
            "01_fourier_mother_boundary_comsol.png",
            "02_selected_snake_shape.png",
            "03_overlay_model_geometry.png",
            "04_overlay_comsol_mesh.png",
            "asset_index.txt",
        ]
        missing = [name for name in required if not (OUT_DIR / name).exists()]
        if missing:
            print(f"[ERROR] missing expected assets: {missing}", file=sys.stderr, flush=True)
            return 2
        print(f"[DONE] {OUT_DIR}", flush=True)
        return 0
    finally:
        print("[STOP] terminating COMSOL server", flush=True)
        server.terminate()
        try:
            server.wait(timeout=20)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=20)
        if server.stdout is not None:
            tail = server.stdout.read()
            if tail.strip():
                print("[COMSOL SERVER OUTPUT]")
                safe_print(tail)


if __name__ == "__main__":
    raise SystemExit(main())
