# -*- coding: utf-8 -*-
import numpy as np
from skimage import measure


def dedupe_consecutive(points: np.ndarray) -> np.ndarray:
    if len(points) == 0:
        return points
    out = [points[0]]
    for p in points[1:]:
        if not np.allclose(p, out[-1]):
            out.append(p)
    return np.vstack(out)


def approximate(points: np.ndarray, tol: float) -> np.ndarray:
    if len(points) < 3:
        return points
    approx = measure.approximate_polygon(points, tolerance=tol)
    return dedupe_consecutive(approx)


def ensure_closed(points: np.ndarray, max_gap: float) -> np.ndarray:
    if len(points) == 0:
        return points
    if np.linalg.norm(points[0] - points[-1]) <= max_gap:
        if not np.allclose(points[0], points[-1]):
            return np.vstack([points, points[0]])
    return points


def densify_linear(points: np.ndarray, n_dense: int, close: bool, max_gap: float) -> np.ndarray:
    if n_dense <= 0 or len(points) < 2:
        return points
    pts = ensure_closed(points, max_gap) if close else points
    out = []
    for i in range(len(pts) - 1):
        p0 = pts[i]
        p1 = pts[i + 1]
        out.append(p0)
        for k in range(1, n_dense + 1):
            t = k / (n_dense + 1)
            out.append(p0 * (1 - t) + p1 * t)
    out.append(pts[-1])
    return np.vstack(out)


def chaikin_once(points: np.ndarray, close: bool, max_gap: float) -> np.ndarray:
    pts = ensure_closed(points, max_gap) if close else points
    if len(pts) < 3:
        return pts
    out = []
    if not close:
        out.append(pts[0])
    for i in range(len(pts) - 1):
        p0 = pts[i]
        p1 = pts[i + 1]
        q = 0.75 * p0 + 0.25 * p1
        r = 0.25 * p0 + 0.75 * p1
        out.extend([q, r])
    if not close:
        out.append(pts[-1])
    out = np.vstack(out)
    return ensure_closed(out, max_gap) if close else out


def postprocess(points: np.ndarray, n_dense: int, close: bool, max_gap: float) -> np.ndarray:
    pts = densify_linear(points, n_dense, close, max_gap)
    pts = chaikin_once(pts, close, max_gap)
    return pts
