import os
import sys
from typing import List, Tuple, Dict, Any, Optional
import json
import torch

_PREPROCESS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "preprocess"))
if _PREPROCESS_DIR not in sys.path:
    sys.path.insert(0, _PREPROCESS_DIR)
from paths import SNAKE_STATES_DIR, SNAKE_CHECKPOINTS_DIR

# 全局采样控制：按蛇长度每3步记录，长度L的总记录数为 (L-3)*10000
# 例如：长度4 → 10000，长度5 → 20000，长度6 → 30000，依次类推
RECORD_INTERVAL_STEPS = 3
RECORDS_PER_LENGTH_BASE = 10000
# 记录计数（进程内全局），键为蛇长度，值为已记录次数
_RECORDED_COUNTS: Dict[int, int] = {}


def should_write_state(matrix: List[List[int]], episode: int, step: int, reward: float, snake_length: int) -> bool:
    """
    采样策略（使用全局计数器）：
    - 当蛇长度 >= 4 时，每隔 3 步记录一次当前状态；
    - 对于每个具体长度 L，最多记录 (L - 3) * 10000 次；
    - 示例：长度4记录10000次，长度5记录20000次，长度6记录30000次，依次类推；
    - 计数在进程内持续（重启服务后会重置）。
    """
    global _RECORDED_COUNTS
    if snake_length < 4:
        return False

    # 限制每个长度的最大记录次数
    target_max = (snake_length - 3) * RECORDS_PER_LENGTH_BASE
    current_count = _RECORDED_COUNTS.get(snake_length, 0)
    if current_count >= target_max:
        return False

    # 每隔固定步数采样
    if step % RECORD_INTERVAL_STEPS != 0:
        return False

    # 满足条件：增加计数并允许写入
    _RECORDED_COUNTS[snake_length] = current_count + 1
    return True


def get_record_counts() -> Dict[int, int]:
    """返回当前记录的计数（副本），键为蛇长度，值为记录次数。"""
    return dict(_RECORDED_COUNTS)

def get_record_targets(max_length: int = 10) -> Dict[int, int]:
    """
    返回每个长度的目标记录次数：长度 L 的目标为 (L-3) * RECORDS_PER_LENGTH_BASE。
    默认覆盖长度 4..max_length。
    """
    if max_length < 4:
        max_length = 4
    return {L: (L - 3) * RECORDS_PER_LENGTH_BASE for L in range(4, max_length + 1)}


def write_matrix_to_file(
    matrix: List[List[int]],
    episode: int,
    step: int,
    base_dir: str = SNAKE_STATES_DIR,
    meta: Optional[Dict[str, Any]] = None,
) -> str:
    os.makedirs(base_dir, exist_ok=True)
    path = os.path.join(base_dir, f"ep{episode}_step{step}.txt")
    with open(path, "w", encoding="utf-8") as f:
        for row in matrix:
            f.write(" ".join(str(x) for x in row) + "\n")
    if meta is not None:
        meta_path = os.path.join(base_dir, f"ep{episode}_step{step}.meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f)
    return path


def save_checkpoint(path: str, agent: Any, env: Any, episode_counter: int, episode_lengths: List[int]) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # 支持DQN：如果agent提供save_state()，直接使用其序列化；否则按Q-learning字段保存
    if hasattr(agent, "save_state") and callable(getattr(agent, "save_state")):
        agent_payload = agent.save_state()
        agent_type = agent_payload.get("agent_type", "unknown")
    else:
        agent_payload = {
            "agent_type": "q",
            "alpha": getattr(agent, "alpha", None),
            "gamma": getattr(agent, "gamma", None),
            "epsilon": getattr(agent, "epsilon", None),
            "epsilon_min": getattr(agent, "epsilon_min", None),
            "epsilon_decay": getattr(agent, "epsilon_decay", None),
            "Q": getattr(agent, "Q", {}),
        }
        agent_type = "q"

    data: Dict[str, Any] = {
        "agent_type": agent_type,
        "agent": agent_payload,
        "env": {
            "n": getattr(env, "n", None),
            "snake": getattr(env, "snake", []),
            "food": getattr(env, "food", None),
            "score": getattr(env, "score", 0),
            "steps": getattr(env, "steps", 0),
        },
        "episode_counter": episode_counter,
        "episode_lengths": episode_lengths,
    }
    # DQN包含张量权重，使用torch.save；Q-learning使用JSON
    if agent_type == "dqn" or path.endswith('.pt'):
        torch.save(data, path)
    else:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    return path


def load_checkpoint(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    # 根据扩展名或内容尝试不同加载方式
    try:
        if path.endswith('.pt'):
            data = torch.load(path, map_location='cpu')
        else:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
    except Exception:
        # 回退尝试torch.load（兼容用.pt保存但命名.json的情况）
        try:
            data = torch.load(path, map_location='cpu')
        except Exception:
            return {}
    return data


def list_checkpoints(base_dir: str = SNAKE_CHECKPOINTS_DIR) -> List[Dict[str, Any]]:
    os.makedirs(base_dir, exist_ok=True)
    files = []
    for name in os.listdir(base_dir):
        if name.endswith('.json') or name.endswith('.pt'):
            full = os.path.join(base_dir, name)
            try:
                stat = os.stat(full)
                files.append({"name": name, "size": stat.st_size, "mtime": stat.st_mtime})
            except Exception:
                files.append({"name": name, "size": 0, "mtime": 0})
    # 按修改时间倒序
    files.sort(key=lambda x: x["mtime"], reverse=True)
    return files
