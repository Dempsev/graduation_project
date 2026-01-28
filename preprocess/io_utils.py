# -*- coding: utf-8 -*-
import os
import numpy as np


def get_repo_dirs(this_file: str) -> tuple[str, str, str]:
    this_dir = os.path.dirname(os.path.abspath(this_file))
    root_dir = os.path.dirname(this_dir)
    data_dir = os.path.join(root_dir, "data")
    return this_dir, root_dir, data_dir


def ensure_dirs(*dirs: str) -> None:
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def load_binary_txt(path: str) -> np.ndarray:
    """Load a 0/1 matrix from txt (whitespace separated)."""
    A = np.loadtxt(path)
    return (A > 0.5).astype(float)


def list_txt_files(folder: str) -> list[str]:
    names = [n for n in os.listdir(folder) if n.lower().endswith(".txt")]
    return [os.path.join(folder, n) for n in sorted(names)]


def output_paths(base_name: str, csv_dir: str, png_dir: str) -> tuple[str, str]:
    out_csv = os.path.join(csv_dir, f"{base_name}_contour_xy.csv")
    out_png = os.path.join(png_dir, f"{base_name}_preview.png")
    return out_csv, out_png


def save_csv_xy(path: str, xy: np.ndarray) -> None:
    np.savetxt(path, xy, delimiter=",", header="x,y", comments="", fmt="%.8g")
