from __future__ import annotations

"""Legacy baseline bridge for the old v11 seed-only candidate-pool line."""

from seed_discovery_pipeline import build_candidate_pool_for_profile
from seed_discovery_profiles import get_profile


if __name__ == '__main__':
    result = build_candidate_pool_for_profile(get_profile('candidate_pool_v11_seed_only_refined'))
    print(f"[DONE] excluded families: {len(result['excluded_families'])}")
    print(f"[DONE] seed candidates: {len(result['seed_manifest'])}")
    print(f"[DONE] point specs: {len(get_profile('candidate_pool_v11_seed_only_refined')['point_specs'])}")
    print(f"[OUT] {result['point_manifest_path']}")
    print(f"[OUT] {result['seed_manifest_path']}")
    print(f"[OUT] {result['pool_csv_path']}")
    print(f"[OUT] {result['info_json_path']}")
