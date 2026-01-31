import os


def _find_project_root(start: str) -> str:
    cur = os.path.abspath(start)
    while True:
        if os.path.isdir(os.path.join(cur, "data")) or os.path.isdir(os.path.join(cur, ".git")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return os.path.abspath(start)
        cur = parent


PROJECT_ROOT = _find_project_root(os.path.dirname(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

SNAKE_STATES_DIR = os.path.join(DATA_DIR, "snake_states")
SNAKE_CHECKPOINTS_DIR = os.path.join(DATA_DIR, "snake_checkpoints")
SNAKE_CHECKPOINT_FILE = os.path.join(SNAKE_CHECKPOINTS_DIR, "checkpoint.json")

SHAPE_POINTS_DIR = os.path.join(DATA_DIR, "shape_points")
SHAPE_PREVIEWS_DIR = os.path.join(DATA_DIR, "shape_previews")
