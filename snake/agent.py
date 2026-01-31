import random
from typing import Dict, List, Tuple

from snake_env import SnakeEnv


def _sign(v: int) -> int:
    return 0 if v == 0 else (1 if v > 0 else -1)


def extract_features(env: SnakeEnv) -> str:
    """
    将环境压缩成一个较小的特征状态字符串：
    - 食物相对头部的方向（dx_sign, dy_sign）
    - 四个方向的危险（如果朝该方向走一步会撞墙/撞身体）
    该特征用于Q表索引，避免01矩阵带来的巨大状态空间。
    """
    n = env.n
    head_x, head_y = env.snake[0]
    food_x, food_y = env.food if env.food else (head_x, head_y)

    dx_sign = _sign(food_x - head_x)
    dy_sign = _sign(food_y - head_y)

    # 下一个位置是否危险（墙或身体）
    occupied_now = set(env.snake)

    def danger_if_move(dx: int, dy: int) -> bool:
        nx, ny = head_x + dx, head_y + dy
        if not (0 <= nx < n and 0 <= ny < n):
            return True
        # 如果不是吃到食物的情况，尾巴会移动，理论上尾巴原位置可以安全
        # 简化：认为当前尾巴位置安全可占用（保守近似）
        tail = env.snake[-1]
        occupied = occupied_now - {tail}
        return (nx, ny) in occupied

    dl = danger_if_move(-1, 0)
    dr = danger_if_move(1, 0)
    du = danger_if_move(0, -1)
    dd = danger_if_move(0, 1)

    return f"fdx={dx_sign}|fdy={dy_sign}|dl={int(dl)}|dr={int(dr)}|du={int(du)}|dd={int(dd)}"


class QLearningAgent:
    def __init__(self, actions: int = 4, alpha: float = 0.2, gamma: float = 0.95, epsilon: float = 0.2, epsilon_min: float = 0.05, epsilon_decay: float = 0.995):
        self.actions = actions
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.Q: Dict[str, List[float]] = {}

    def _ensure_state(self, s: str):
        if s not in self.Q:
            self.Q[s] = [0.0 for _ in range(self.actions)]

    def choose_action(self, s: str) -> int:
        self._ensure_state(s)
        if random.random() < self.epsilon:
            return random.randrange(self.actions)
        q = self.Q[s]
        # 选择最大Q值的动作
        return max(range(self.actions), key=lambda a: q[a])

    def learn(self, s: str, a: int, r: float, s_next: str, done: bool):
        self._ensure_state(s)
        self._ensure_state(s_next)
        q_sa = self.Q[s][a]
        if done:
            target = r
        else:
            target = r + self.gamma * max(self.Q[s_next])
        self.Q[s][a] = (1 - self.alpha) * q_sa + self.alpha * target

    def end_episode(self):
        # 衰减探索率
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)