import random
from typing import List, Tuple, Dict


class SnakeEnv:
    """
    贪吃蛇环境：
    - 网格大小 n*n
    - 状态矩阵为 0/1（1 表示蛇身体占据的格子）
    - 食物单独记录坐标（不在 0/1 矩阵中）
    - 动作: 0=左, 1=右, 2=上, 3=下
    """

    def __init__(self, n: int = 15):
        self.n = n
        self.directions: Dict[int, Tuple[int, int]] = {
            0: (-1, 0),  # left (x-1)
            1: (1, 0),   # right (x+1)
            2: (0, -1),  # up (y-1)
            3: (0, 1),   # down (y+1)
        }

        self.reset()

    def reset(self) -> List[List[int]]:
        # 初始蛇身体：水平朝右，长度3，位于中央
        cx = self.n // 2
        cy = self.n // 2
        self.snake: List[Tuple[int, int]] = [
            (cx, cy), (cx - 1, cy), (cx - 2, cy)
        ]
        self.direction = 1  # 初始向右
        self.steps = 0
        self.score = 0
        self.done = False

        self._place_food()
        return self.get_matrix()

    def _place_food(self):
        occupied = set(self.snake)
        free_cells = [(x, y) for x in range(self.n) for y in range(self.n) if (x, y) not in occupied]
        self.food = random.choice(free_cells) if free_cells else None

    def step(self, action: int) -> Tuple[float, bool]:
        if self.done:
            return 0.0, True

        # 限制动作在 0..3
        action = int(action) % 4
        self.direction = action

        dx, dy = self.directions[action]
        head_x, head_y = self.snake[0]
        new_head = (head_x + dx, head_y + dy)

        # 撞墙
        if not (0 <= new_head[0] < self.n and 0 <= new_head[1] < self.n):
            self.done = True
            return -1.0, True

        # 撞到自己
        if new_head in self.snake:
            self.done = True
            return -1.0, True

        reward = -0.01  # 每步微小惩罚，鼓励尽快吃到食物

        # 奖励塑形：朝食物靠近给予微弱正奖励
        if self.food:
            prev_dist = abs(self.food[0] - head_x) + abs(self.food[1] - head_y)
            new_dist = abs(self.food[0] - new_head[0]) + abs(self.food[1] - new_head[1])
            shaping = 0.005 * (prev_dist - new_dist)  # 靠近为正，远离为负
            reward += shaping

        # 吃到食物
        if self.food and new_head == self.food:
            # 增长：头部前进，不移除尾巴
            self.snake.insert(0, new_head)
            self.score += 1
            reward = 1.0
            self._place_food()
        else:
            # 普通移动：头部前进，同时移除尾巴
            self.snake.insert(0, new_head)
            self.snake.pop()

        self.steps += 1
        return reward, False

    def get_matrix(self) -> List[List[int]]:
        # 返回 0/1 状态矩阵（仅蛇身体为 1）
        grid = [[0 for _ in range(self.n)] for _ in range(self.n)]
        for (x, y) in self.snake:
            grid[y][x] = 1
        return grid

    def as_dict(self) -> Dict:
        # 提供给前端的完整状态信息
        return {
            "n": self.n,
            "matrix": self.get_matrix(),
            "snake": self.snake,
            "food": self.food,
            "score": self.score,
            "steps": self.steps,
            "done": self.done,
        }