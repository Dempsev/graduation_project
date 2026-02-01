# -*- coding: utf-8 -*-
import numpy as np
from skimage import measure


def pad_matrix(A: np.ndarray, pad: int) -> np.ndarray:
    if pad <= 0:
        return A
    return np.pad(A, pad, mode="constant", constant_values=0)


def remove_padding(contour_rc: np.ndarray, pad: int) -> np.ndarray:
    if pad <= 0:
        return contour_rc
    out = contour_rc.copy()
    out[:, 0] -= pad
    out[:, 1] -= pad
    return out


def is_closed(points: np.ndarray, max_gap: float) -> bool:
    if len(points) < 2:
        return True
    return np.linalg.norm(points[0] - points[-1]) <= max_gap


def polygon_area(points: np.ndarray) -> float:
    if len(points) < 3:
        return 0.0
    x = points[:, 0]
    y = points[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def contour_to_xy(contour_rc: np.ndarray, shape_hw, pixel_size: float, center_origin: bool) -> np.ndarray:
    H, W = shape_hw
    r = contour_rc[:, 0]
    c = contour_rc[:, 1]
    if center_origin:
        x = (c - (W - 1) / 2.0) * pixel_size
        y = -(r - (H - 1) / 2.0) * pixel_size
    else:
        x = c * pixel_size
        y = -r * pixel_size
    return np.column_stack([x, y])


def xy_to_rc(points_xy: np.ndarray, shape_hw, pixel_size: float, center_origin: bool) -> np.ndarray:
    H, W = shape_hw
    x = points_xy[:, 0]
    y = points_xy[:, 1]
    if center_origin:
        c = x / pixel_size + (W - 1) / 2.0
        r = -y / pixel_size + (H - 1) / 2.0
    else:
        c = x / pixel_size
        r = -y / pixel_size
    return np.column_stack([r, c])


def find_contours_padded(A: np.ndarray, level: float, pad: int) -> list[np.ndarray]:
    A_pad = pad_matrix(A, pad)
    contours = measure.find_contours(A_pad, level=level)
    if pad > 0:
        contours = [remove_padding(c, pad) for c in contours]
    return contours


def largest_component(A: np.ndarray) -> np.ndarray:
    labels = measure.label(A > 0.5, connectivity=1)
    if labels.max() == 0:
        return A
    counts = np.bincount(labels.ravel())
    counts[0] = 0
    target = int(np.argmax(counts))
    return (labels == target).astype(float)


def choose_main_contour(
    contours: list[np.ndarray],
    max_gap: float,
    min_points: int,
    prefer_closed: bool,
) -> np.ndarray | None:
    candidates = [c for c in contours if len(c) >= min_points]
    if not candidates:
        return None

    closed = [c for c in candidates if is_closed(c, max_gap)]
    if prefer_closed and closed:
        candidates = closed

    # Use max absolute area as primary selection criterion
    areas = [abs(polygon_area(c[:, [1, 0]])) for c in candidates]
    idx = int(np.argmax(areas))
    return candidates[idx]


def _edge_key(p0: tuple[int, int], p1: tuple[int, int]) -> tuple[tuple[int, int], tuple[int, int]]:
    return (p0, p1) if p0 <= p1 else (p1, p0)


def _trace_loops(edges: list[tuple[tuple[int, int], tuple[int, int]]]) -> list[list[tuple[int, int]]]:
    adj: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for p0, p1 in edges:
        adj.setdefault(p0, []).append(p1)
        adj.setdefault(p1, []).append(p0)

    used: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    loops: list[list[tuple[int, int]]] = []

    for p0, p1 in edges:
        key = _edge_key(p0, p1)
        if key in used:
            continue
        used.add(key)
        loop = [p0, p1]

        while True:
            cur = loop[-1]
            prev = loop[-2]
            neighbors = adj.get(cur, [])
            if not neighbors:
                break
            if len(neighbors) == 1:
                nxt = neighbors[0]
            else:
                nxt = neighbors[0] if neighbors[0] != prev else neighbors[1]

            edge_key = _edge_key(cur, nxt)
            if edge_key in used:
                if nxt == loop[0]:
                    loop.append(nxt)
                break
            used.add(edge_key)
            loop.append(nxt)
            if nxt == loop[0]:
                break

        if len(loop) >= 4:
            loops.append(loop)

    return loops


def find_pixel_boundaries(A: np.ndarray) -> list[np.ndarray]:
    on = np.argwhere(A > 0.5)
    if on.size == 0:
        return []

    edge_counts: dict[tuple[tuple[int, int], tuple[int, int]], int] = {}
    for r, c in on:
        r2 = int(r) * 2
        c2 = int(c) * 2
        tl = (r2 - 1, c2 - 1)
        tr = (r2 - 1, c2 + 1)
        br = (r2 + 1, c2 + 1)
        bl = (r2 + 1, c2 - 1)
        for p0, p1 in ((tl, tr), (tr, br), (br, bl), (bl, tl)):
            key = _edge_key(p0, p1)
            edge_counts[key] = edge_counts.get(key, 0) + 1

    boundary_edges = [edge for edge, count in edge_counts.items() if count == 1]
    loops = _trace_loops(boundary_edges)

    out = []
    for loop in loops:
        pts = np.array(loop, dtype=float) / 2.0
        out.append(pts)
    return out
