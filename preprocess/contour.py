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
