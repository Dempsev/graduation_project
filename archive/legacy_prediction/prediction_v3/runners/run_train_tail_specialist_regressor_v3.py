from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from prediction_v3.models.train_tail_specialist_regressor_v3 import main


if __name__ == '__main__':
    main()
