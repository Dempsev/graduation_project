# Stage4 Mainline Modularization TODO

This repository now uses shared stage4 validation helpers for the current mainline routes:

- `stage4_validation_ab_v10`
- `stage4_validation_ab_v11`
- `stage4_validation_ab_ga_v1`

Legacy routes remain on the older implementation path for now:

- `stage4_validation_ab_v1`
- `stage4_validation_ab_v2`
- `stage4_validation_ab_v3`
- `stage4_validation_ab_v4`
- `stage4_validation_ab_v5`
- `stage4_validation_ab_v6`
- `stage4_validation_ab_v7`
- `stage4_validation_ab_v8`
- `stage4_validation_ab_v9`

Current status:

- mainline config/result behavior is preserved
- legacy routes are still compatible and runnable
- no attempt was made in this round to structurally unify `v1~v9`

Recommended later follow-up:

1. move `v2~v9` onto `build_stage4_validation_config.m`
2. move `v2~v9` runners onto `run_stage4_validation_from_manifest.m`
3. only then consider legacy result schema cleanup
