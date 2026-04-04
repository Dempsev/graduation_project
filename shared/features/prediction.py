from __future__ import annotations

PARAMETER_FEATURES = [
    'a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0',
]

SHAPE_BASE_FEATURES = [
    'shape_area', 'shape_perimeter', 'shape_bbox_width', 'shape_bbox_height',
    'shape_bbox_aspect_ratio', 'shape_centroid_x', 'shape_centroid_y', 'shape_point_count',
]

SHAPE_EXTENDED_FEATURES = [
    'shape_compactness', 'shape_extent', 'shape_mean_radius', 'shape_std_radius',
    'shape_min_radius', 'shape_max_radius', 'shape_radius_cv',
    'shape_edge_mean', 'shape_edge_std', 'shape_edge_cv',
]

PURE_STRUCTURAL_CORE_FEATURES = [
    *PARAMETER_FEATURES,
    *SHAPE_BASE_FEATURES,
]

PURE_STRUCTURAL_EXTENDED_FEATURES = [
    *PURE_STRUCTURAL_CORE_FEATURES,
    *SHAPE_EXTENDED_FEATURES,
]

PREDICTION_FEATURE_PRESETS = {
    'pure_structural_core': PURE_STRUCTURAL_CORE_FEATURES,
    'pure_structural_extended': PURE_STRUCTURAL_EXTENDED_FEATURES,
}

ALLOWED_GROUP_KEYS = ['shape_id', 'shape_family', 'none']

