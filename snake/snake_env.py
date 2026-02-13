import random
from typing import Dict, List, Tuple


class SnakeEnv:
    """Grid snake environment for RL training."""

    def __init__(self, n: int = 15):
        self.n = n
        self.directions: Dict[int, Tuple[int, int]] = {
            0: (-1, 0),  # left
            1: (1, 0),   # right
            2: (0, -1),  # up
            3: (0, 1),   # down
        }
        self.reset()

    def reset(self) -> List[List[int]]:
        cx = self.n // 2
        cy = self.n // 2
        self.snake: List[Tuple[int, int]] = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.direction = 1
        self.steps = 0
        self.steps_since_food = 0
        # Guard rails: end stalled or overlong episodes.
        self.max_steps_without_food = max(80, 4 * self.n * self.n)
        self.max_episode_steps = max(200, 8 * self.n * self.n)
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

        action = int(action) % 4
        # Prevent direct reversal when length > 1.
        if len(self.snake) > 1 and is_opposite_direction(self.direction, action):
            action = self.direction
        self.direction = action

        dx, dy = self.directions[action]
        head_x, head_y = self.snake[0]
        new_head = (head_x + dx, head_y + dy)

        if not (0 <= new_head[0] < self.n and 0 <= new_head[1] < self.n):
            self.done = True
            return -1.0, True

        if new_head in self.snake:
            self.done = True
            return -1.0, True

        reward = -0.01
        if self.food:
            prev_dist = abs(self.food[0] - head_x) + abs(self.food[1] - head_y)
            new_dist = abs(self.food[0] - new_head[0]) + abs(self.food[1] - new_head[1])
            reward += 0.005 * (prev_dist - new_dist)

        if self.food and new_head == self.food:
            self.snake.insert(0, new_head)
            self.score += 1
            reward = 1.0
            self._place_food()
            self.steps_since_food = 0
            # Board filled.
            if self.food is None:
                self.done = True
                return 2.0, True
        else:
            self.snake.insert(0, new_head)
            self.snake.pop()
            self.steps_since_food += 1

        self.steps += 1
        if self.steps_since_food >= self.max_steps_without_food:
            self.done = True
            return -0.5, True
        if self.steps >= self.max_episode_steps:
            self.done = True
            return -0.5, True

        return reward, False

    def get_matrix(self) -> List[List[int]]:
        grid = [[0 for _ in range(self.n)] for _ in range(self.n)]
        for (x, y) in self.snake:
            grid[y][x] = 1
        return grid

    def as_dict(self) -> Dict:
        return {
            "n": self.n,
            "matrix": self.get_matrix(),
            "snake": self.snake,
            "food": self.food,
            "score": self.score,
            "steps": self.steps,
            "done": self.done,
        }


def is_opposite_direction(old_action: int, new_action: int) -> bool:
    opposite = {0: 1, 1: 0, 2: 3, 3: 2}
    return opposite.get(old_action) == new_action
