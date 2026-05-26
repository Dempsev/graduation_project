from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matlab.engine


ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "research_validation" / "ch4_ga_real_optimization"
FIG_DIR = EXPORT_DIR / "figures"

ALL_BANDS = [
    "band140_180",
    "band160_200",
    "band180_220",
    "band200_240",
    "band220_260",
    "band240_280",
]


def matlab_cell_literal(items: list[str]) -> str:
    quoted = ",".join(f"'{item}'" for item in items)
    return "{" + quoted + "}"


def connect_or_start(name: str):
    sessions = set(matlab.engine.find_matlab())
    if name in sessions:
        return matlab.engine.connect_matlab(name)
    return matlab.engine.start_matlab()


def run_export(
    test_one: bool = False,
    bands: list[str] | None = None,
    session: str | None = None,
    worker: str | None = None,
) -> list[Path]:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    if bands:
        jobs = [(worker or "custom", bands, session or "comsol_matlab")]
    elif test_one:
        jobs = [("test_one", ["band140_180"], "comsol_matlab")]
    else:
        jobs = [
            ("worker1", ["band140_180", "band160_200", "band180_220"], "comsol_matlab"),
            ("worker2", ["band200_240", "band220_260", "band240_280"], "comsol_matlab_2"),
        ]

    futures = []
    engines = []
    for worker, bands, session in jobs:
        eng = connect_or_start(session)
        engines.append(eng)
        eng.cd(str(ROOT), nargout=0)
        eng.addpath(str(EXPORT_DIR), nargout=0)
        cmd = (
            "export_ch4_best_unit_cell_comsol_geometry_v1"
            f"({matlab_cell_literal(bands)}, '{worker}')"
        )
        futures.append((worker, eng.eval(cmd, nargout=1, background=True)))

    manifests: list[Path] = []
    for worker, future in futures:
        manifest = Path(str(future.result()))
        manifests.append(manifest)
        print(f"[{worker}] manifest: {manifest}")
    return manifests


def merge_manifests(manifests: list[Path]) -> Path:
    rows: list[dict[str, str]] = []
    fieldnames: list[str] | None = None
    for path in manifests:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if fieldnames is None:
                fieldnames = list(reader.fieldnames or [])
            rows.extend(reader)
    rows.sort(key=lambda row: ALL_BANDS.index(row["target_band_tag"]))
    out_path = FIG_DIR / "ch4_fig4_6_comsol_unit_cell_export_manifest.csv"
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[MERGED] {out_path}")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-one", action="store_true")
    parser.add_argument("--bands", nargs="*", choices=ALL_BANDS)
    parser.add_argument("--session", default=None)
    parser.add_argument("--worker", default=None)
    args = parser.parse_args()
    manifests = run_export(
        test_one=args.test_one,
        bands=args.bands,
        session=args.session,
        worker=args.worker,
    )
    if not args.test_one and not args.bands:
        merge_manifests(manifests)


if __name__ == "__main__":
    main()
