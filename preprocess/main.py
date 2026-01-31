# -*- coding: utf-8 -*-
import argparse
import os
import random
import numpy as np

import io_utils
import contour
import simplify
import viz
from paths import SNAKE_STATES_DIR, SHAPE_POINTS_DIR, SHAPE_PREVIEWS_DIR


TXT_DIR = SNAKE_STATES_DIR


def parse_int_bool(value: str) -> bool:
    v = value.strip().lower()
    if v in {"1", "true", "yes", "y"}:
        return True
    if v in {"0", "false", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError("Expected 0/1 or true/false.")


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"1", "true", "yes", "y"}:
            return True
        if v in {"0", "false", "no", "n"}:
            return False
    return None


def process_one(path: str, cfg: dict) -> dict:
    base_name = os.path.splitext(os.path.basename(path))[0]
    out_csv, out_png = io_utils.output_paths(base_name, cfg["csv_dir"], cfg["png_dir"])

    A = io_utils.load_binary_txt(path)
    meta = io_utils.load_meta_for_txt(path)
    cfg_eff = dict(cfg)
    if meta:
        a = meta.get("a")
        n = meta.get("n")
        try:
            a_val = float(a)
            n_val = float(n)
            if a_val > 0 and n_val > 0:
                cfg_eff["pixel_size"] = a_val / n_val
        except Exception:
            pass
        co = _as_bool(meta.get("center_origin"))
        if co is not None:
            cfg_eff["center_origin"] = co
    if meta:
        print(
            f"[meta] {base_name}: pixel_size={cfg_eff['pixel_size']:.6g}, "
            f"center_origin={cfg_eff['center_origin']}"
        )
    else:
        print(
            f"[meta] {base_name}: meta not found, "
            f"pixel_size={cfg_eff['pixel_size']:.6g}, "
            f"center_origin={cfg_eff['center_origin']}"
        )
    if cfg_eff["largest_component"]:
        A = contour.largest_component(A)

    contours = contour.find_contours_padded(A, level=cfg_eff["level"], pad=cfg_eff["pad"])
    main = contour.choose_main_contour(
        contours,
        max_gap=cfg_eff["close_gap_px"],
        min_points=cfg_eff["min_points"],
        prefer_closed=cfg_eff["prefer_closed"],
    )
    if main is None:
        raise RuntimeError("No valid contour found.")

    raw_rc = main
    approx_rc = raw_rc
    if cfg_eff["simplify"]:
        approx_rc = simplify.approximate(raw_rc, cfg_eff["approx_tol"])

    xy = contour.contour_to_xy(approx_rc, A.shape, cfg_eff["pixel_size"], cfg_eff["center_origin"])
    close_gap_xy = cfg_eff["close_gap_px"] * cfg_eff["pixel_size"]
    close_ok = np.linalg.norm(xy[0] - xy[-1]) <= close_gap_xy if len(xy) > 1 else True
    if cfg_eff["require_closed"] and not close_ok:
        raise RuntimeError("Open contour detected; adjust padding/selection or close-gap.")

    if cfg_eff["enable_postprocess"]:
        xy = simplify.postprocess(xy, cfg_eff["n_dense"], close_ok, close_gap_xy)

    if cfg_eff["require_closed"]:
        xy = simplify.ensure_closed(xy, close_gap_xy)

    io_utils.save_csv_xy(out_csv, xy)

    post_rc = contour.xy_to_rc(xy, A.shape, cfg_eff["pixel_size"], cfg_eff["center_origin"])
    area = abs(contour.polygon_area(post_rc[:, [1, 0]]))
    title = (
        f"raw:{len(raw_rc)} approx:{len(approx_rc)} post:{len(xy)} "
        f"area:{area:.2f} closed:{np.allclose(xy[0], xy[-1])} "
        f"prefer_closed:{cfg_eff['prefer_closed']}"
    )

    if cfg_eff["preview"]:
        viz.plot_preview(
            A=A,
            raw_rc=raw_rc if cfg_eff["preview_show_original"] else None,
            approx_rc=approx_rc if cfg_eff["preview_show_original"] else None,
            post_rc=post_rc if cfg_eff["enable_postprocess"] else None,
            out_png=out_png,
            title=title,
            show_legend=cfg_eff["preview_show_original"] or cfg_eff["enable_postprocess"],
        )

    return {
        "name": base_name,
        "raw": len(raw_rc),
        "approx": len(approx_rc),
        "post": len(xy),
        "area": area,
        "closed": np.allclose(xy[0], xy[-1]),
        "out_csv": out_csv,
        "out_png": out_png,
        "pixel_size": cfg_eff["pixel_size"],
        "center_origin": cfg_eff["center_origin"],
        "meta_used": bool(meta),
    }


def main():
    parser = argparse.ArgumentParser(description="Extract contour points from binary matrices.")
    parser.add_argument("--txt", default=None, help="Single txt file path.")
    parser.add_argument("--dir", default=TXT_DIR, help="Directory of txt files.")
    parser.add_argument("--sample", type=int, default=10, help="Random sample size (0 means all).")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for sampling.")

    parser.add_argument("--pixel-size", type=float, default=1.0, help="Pixel size in physical units.")
    parser.add_argument("--center-origin", type=parse_int_bool, default=True, help="1: origin at center.")
    parser.add_argument("--simplify", type=parse_int_bool, default=True, help="Enable approximation.")
    parser.add_argument("--approx-tol", type=float, default=0.2, help="approximate_polygon tolerance.")
    parser.add_argument("--enable-postprocess", type=parse_int_bool, default=True, help="Enable postprocess.")
    parser.add_argument("--n-dense", type=int, default=10, help="Insert N points per segment.")
    parser.add_argument("--close-gap", type=float, default=1.5, help="Max gap in pixels to close.")
    parser.add_argument("--min-points", type=int, default=10, help="Min points for a contour candidate.")
    parser.add_argument("--prefer-closed", type=parse_int_bool, default=True, help="Prefer closed contour.")
    parser.add_argument("--largest-component", type=parse_int_bool, default=False, help="Keep largest component.")
    parser.add_argument("--pad", type=int, default=1, help="Padding size before find_contours.")
    parser.add_argument("--level", type=float, default=0.5, help="find_contours level.")
    parser.add_argument("--require-closed", type=parse_int_bool, default=True, help="Require closed output.")
    parser.add_argument("--preview", type=parse_int_bool, default=True, help="Save preview image.")
    parser.add_argument("--preview-show-original", type=parse_int_bool, default=True, help="Show raw/approx.")

    parser.add_argument("--selftest", type=parse_int_bool, default=False, help="Run quick self test.")
    parser.add_argument("--selftest-n", type=int, default=3, help="Number of samples for self test.")

    args = parser.parse_args()

    csv_dir = SHAPE_POINTS_DIR
    png_dir = SHAPE_PREVIEWS_DIR
    io_utils.ensure_dirs(csv_dir, png_dir)

    cfg = {
        "csv_dir": csv_dir,
        "png_dir": png_dir,
        "pixel_size": args.pixel_size,
        "center_origin": args.center_origin,
        "simplify": args.simplify,
        "approx_tol": args.approx_tol,
        "enable_postprocess": args.enable_postprocess,
        "n_dense": args.n_dense,
        "close_gap_px": args.close_gap,
        "min_points": args.min_points,
        "prefer_closed": args.prefer_closed,
        "largest_component": args.largest_component,
        "pad": args.pad,
        "level": args.level,
        "require_closed": args.require_closed,
        "preview": args.preview,
        "preview_show_original": args.preview_show_original,
    }

    if args.txt:
        if not os.path.isfile(args.txt):
            raise RuntimeError(f"--txt file not found: {args.txt}")
        paths = [args.txt]
    else:
        paths = io_utils.list_txt_files(args.dir)

    if args.sample < 0:
        raise ValueError("--sample must be >= 0")

    if not args.txt:
        total = len(paths)
        if total == 0:
            raise RuntimeError("No txt files found to process.")
        if args.sample == 0 or args.sample >= total:
            chosen = paths
        else:
            rng = random.Random(args.seed)
            chosen = rng.sample(paths, args.sample)
        paths = chosen

    if args.selftest:
        if not paths:
            raise RuntimeError("No txt files found for selftest.")
        rng = random.Random(args.seed)
        picks = rng.sample(paths, min(args.selftest_n, len(paths)))
        for p in picks:
            info = process_one(p, cfg)
            print(
                f"[selftest] {info['name']} raw:{info['raw']} approx:{info['approx']} "
                f"post:{info['post']} area:{info['area']:.2f} closed:{info['closed']}"
            )
        return

    if not paths:
        raise RuntimeError("No txt files found to process.")

    print(f"Processing {len(paths)} file(s).")
    for path in paths:
        info = process_one(path, cfg)
        print(
            f"Done: {info['name']} raw:{info['raw']} approx:{info['approx']} "
            f"post:{info['post']} area:{info['area']:.2f} closed:{info['closed']}"
        )


if __name__ == "__main__":
    main()
