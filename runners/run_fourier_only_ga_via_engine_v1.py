from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import sys
import time
import traceback
from pathlib import Path

import matlab.engine


ROOT = Path(r"D:\graduation_project\coad")
DEFAULT_BANDS = [
    "band140_180",
    "band160_200",
    "band180_220",
    "band200_240",
    "band220_260",
    "band240_280",
]
DEFAULT_LOG = ROOT / "tmp" / "fourier_only_ga20_via_engine.log"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Fourier-only COMSOL-in-loop GA through shared MATLAB engines.")
    parser.add_argument("--bands", default=",".join(DEFAULT_BANDS))
    parser.add_argument("--generations", type=int, default=20)
    parser.add_argument("--engines", default="comsol_matlab")
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    return parser.parse_args()


def make_logger(log_path: Path):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("", encoding="utf-8")

    def log(message: str) -> None:
        stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{stamp}] {message}"
        print(line, flush=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    return log


def prepare_engine(engine_name: str, log):
    last_exc: Exception | None = None
    for attempt in range(1, 6):
        try:
            log(f"{engine_name}: connect attempt={attempt}; available={matlab.engine.find_matlab()}")
            eng = matlab.engine.connect_matlab(engine_name)
            break
        except Exception as exc:
            last_exc = exc
            log(f"{engine_name}: connect retry after error={exc}")
            time.sleep(3)
    else:
        raise last_exc if last_exc is not None else RuntimeError(f"Could not connect to {engine_name}")

    root = str(ROOT)
    eng.eval(f"cd('{root}')", nargout=0)
    for rel in ["runners", "model_core", "stage2", "stage2_harmonics", "stage2_harmonics_refine", "optimization", "shared"]:
        eng.eval(f"addpath(genpath(fullfile(pwd,'{rel}')))", nargout=0)
    return eng


def run_queue(engine_name: str, bands: list[str], generations: int, log) -> None:
    eng = prepare_engine(engine_name, log)
    log(f"{engine_name}: connected; queue={','.join(bands)}")
    for band in bands:
        log(f"{engine_name}: START {band} -> {generations} generations")
        try:
            eng.run_fourier_only_band_ga_v1(band, float(generations), nargout=0)
        except Exception:
            log(f"{engine_name}: ERROR {band}\n{traceback.format_exc()}")
            raise
        log(f"{engine_name}: DONE {band}")
    log(f"{engine_name}: queue complete")


def split_bands(bands: list[str], engines: list[str]) -> dict[str, list[str]]:
    queues = {name: [] for name in engines}
    for index, band in enumerate(bands):
        queues[engines[index % len(engines)]].append(band)
    return {name: queue for name, queue in queues.items() if queue}


def main() -> None:
    args = parse_args()
    bands = [part.strip() for part in args.bands.split(",") if part.strip()]
    engines = [part.strip() for part in args.engines.split(",") if part.strip()]
    if not bands:
        raise ValueError("No bands requested.")
    if not engines:
        raise ValueError("No MATLAB engines requested.")

    log = make_logger(args.log)
    log(f"available engines: {matlab.engine.find_matlab()}")
    queues = split_bands(bands, engines)
    log(f"queues: {queues}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(queues)) as pool:
        futures = [
            pool.submit(run_queue, engine_name, queue, int(args.generations), log)
            for engine_name, queue in queues.items()
        ]
        for future in concurrent.futures.as_completed(futures):
            future.result()

    log("all queues complete")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr, flush=True)
        raise
