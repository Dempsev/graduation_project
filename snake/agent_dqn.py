import random
from collections import deque
from typing import Tuple, Dict, Any, Optional

import torch
import torch.nn as nn
import torch.optim as optim


class QNetwork(nn.Module):
    def __init__(self, board_size: int, num_actions: int = 4):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((4, 4)),
        )
        self.head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(32 * 4 * 4, 64),
            nn.ReLU(),
            nn.Linear(64, num_actions),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        return self.head(x)


class ReplayBuffer:
    def __init__(self, capacity: int = 10000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state: torch.Tensor, action: int, reward: float, next_state: torch.Tensor, done: bool):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size: int):
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        states = torch.cat(states, dim=0)
        next_states = torch.cat(next_states, dim=0)
        actions = torch.tensor(actions, dtype=torch.long).unsqueeze(1)
        rewards = torch.tensor(rewards, dtype=torch.float32).unsqueeze(1)
        dones = torch.tensor(dones, dtype=torch.bool).unsqueeze(1)
        return states, actions, rewards, next_states, dones

    def __len__(self):
        return len(self.buffer)


class DQNAgent:
    def __init__(
        self,
        board_size: int,
        num_actions: int = 4,
        lr: float = 1e-3,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.05,
        epsilon_decay: float = 0.995,
        buffer_capacity: int = 10000,
        batch_size: int = 64,
        target_update_period: int = 20,
        device: Optional[str] = None,
    ):
        self.board_size = board_size
        self.num_actions = num_actions
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update_period = target_update_period
        self.learn_steps = 0

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.policy_net = QNetwork(board_size, num_actions).to(self.device)
        self.target_net = QNetwork(board_size, num_actions).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=lr)
        self.buffer = ReplayBuffer(capacity=buffer_capacity)
        self.loss_fn = nn.MSELoss()

    def _to_tensor(self, matrix) -> torch.Tensor:
        # matrix: 2D list/array of board_size x board_size with ints
        x = torch.tensor(matrix, dtype=torch.float32, device=self.device)
        x = x.unsqueeze(0).unsqueeze(0)  # (1, 1, H, W)
        # normalize to [0,1]
        x = (x - x.min()) / (x.max() - x.min() + 1e-8)
        return x

    def choose_action(self, matrix) -> int:
        if random.random() < self.epsilon:
            return random.randrange(self.num_actions)
        with torch.no_grad():
            state = self._to_tensor(matrix)
            q_values = self.policy_net(state)
            return int(q_values.argmax(dim=1).item())

    def remember(self, state_matrix, action: int, reward: float, next_state_matrix, done: bool):
        s = self._to_tensor(state_matrix)
        ns = self._to_tensor(next_state_matrix)
        self.buffer.push(s, action, reward, ns, done)

    def optimize(self):
        if len(self.buffer) < self.batch_size:
            return None
        states, actions, rewards, next_states, dones = self.buffer.sample(self.batch_size)

        # Compute current Q(s,a)
        q_values = self.policy_net(states).gather(1, actions)

        # Compute target Q values
        with torch.no_grad():
            next_q_values = self.target_net(next_states).max(dim=1, keepdim=True)[0]
            target_q = rewards + (~dones).float() * (self.gamma * next_q_values)

        loss = self.loss_fn(q_values, target_q)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        self.learn_steps += 1
        if self.learn_steps % self.target_update_period == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())

        return float(loss.item())

    def end_episode(self):
        # Decay epsilon per episode
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

    def save_state(self) -> Dict[str, Any]:
        return {
            "agent_type": "dqn",
            "dqn_policy_state": self.policy_net.state_dict(),
            "dqn_target_state": self.target_net.state_dict(),
            "optimizer_state": self.optimizer.state_dict(),
            "epsilon": self.epsilon,
            "gamma": self.gamma,
            "batch_size": self.batch_size,
            "target_update_period": self.target_update_period,
            "board_size": self.board_size,
            "num_actions": self.num_actions,
        }

    def load_state(self, state: Dict[str, Any]):
        # This assumes nets are already constructed with same shapes
        self.policy_net.load_state_dict(state.get("dqn_policy_state"))
        target_state = state.get("dqn_target_state")
        if target_state:
            self.target_net.load_state_dict(target_state)
        opt_state = state.get("optimizer_state")
        if opt_state:
            self.optimizer.load_state_dict(opt_state)
        self.epsilon = float(state.get("epsilon", self.epsilon))
        self.gamma = float(state.get("gamma", self.gamma))
        self.batch_size = int(state.get("batch_size", self.batch_size))
        self.target_update_period = int(state.get("target_update_period", self.target_update_period))