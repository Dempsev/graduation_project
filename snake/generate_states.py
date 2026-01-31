# -*- coding: utf-8 -*-
import argparse
import os
import random
import sys
from typing import Optional

from snake_env import SnakeEnv
from agent import QLearningAgent, extract_features
from agent_dqn import DQNAgent
from utils import should_write_state, write_matrix_to_file

_PREPROCESS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "preprocess"))
if _PREPROCESS_DIR not in sys.path:
    sys.path.insert(0, _PREPROCESS_DIR)
from paths import SNAKE_STATES_DIR


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate snake states without HTTP/UI.")
    parser.add_argument("--episodes", type=int, default=200, help="Number of episodes to run.")
    parser.add_argument("--max-steps", type=int, default=500, help="Max steps per episode.")
    parser.add_argument("--n", type=int, default=32, help="Board size (n x n).")
    parser.add_argument("--agent", choices=["random", "q", "dqn"], default="q", help="Agent type.")
    parser.add_argument("--out-dir", default=SNAKE_STATES_DIR, help="Output directory for states.")
    parser.add_argument("--a", type=float, default=0.05, help="Physical domain size (meters).")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--warmup-episodes", type=int, default=0, help="Episodes to run before writing files.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    random.seed(args.seed)

    env = SnakeEnv(n=args.n)
    agent_type = args.agent
    if agent_type == "dqn":
        agent = DQNAgent(board_size=env.n)
    elif agent_type == "q":
        agent = QLearningAgent()
    else:
        agent = None

    episode_counter = 0
    for _ in range(args.episodes):
        env.reset()
        episode_counter += 1
        done = False
        steps = 0
        write_enabled = episode_counter > args.warmup_episodes

        if agent_type == "dqn":
            s_matrix = env.get_matrix()
            while not done and steps < args.max_steps:
                a = agent.choose_action(s_matrix)
                reward, done = env.step(a)
                s_next_matrix = env.get_matrix()
                agent.remember(s_matrix, a, reward, s_next_matrix, done)
                agent.optimize()
                s_matrix = s_next_matrix
                steps += 1

                if write_enabled and should_write_state(s_matrix, episode_counter, steps, reward, len(env.snake)):
                    write_matrix_to_file(
                        s_matrix,
                        episode_counter,
                        steps,
                        base_dir=args.out_dir,
                        meta={"a": args.a, "n": env.n, "center_origin": True},
                    )
            agent.end_episode()
        elif agent_type == "q":
            s = extract_features(env)
            while not done and steps < args.max_steps:
                a = agent.choose_action(s)
                reward, done = env.step(a)
                s_next = extract_features(env)
                agent.learn(s, a, reward, s_next, done)
                s = s_next
                steps += 1

                matrix = env.get_matrix()
                if write_enabled and should_write_state(matrix, episode_counter, steps, reward, len(env.snake)):
                    write_matrix_to_file(
                        matrix,
                        episode_counter,
                        steps,
                        base_dir=args.out_dir,
                        meta={"a": args.a, "n": env.n, "center_origin": True},
                    )
            agent.end_episode()
        else:
            while not done and steps < args.max_steps:
                a = random.randrange(4)
                reward, done = env.step(a)
                steps += 1

                matrix = env.get_matrix()
                if write_enabled and should_write_state(matrix, episode_counter, steps, reward, len(env.snake)):
                    write_matrix_to_file(
                        matrix,
                        episode_counter,
                        steps,
                        base_dir=args.out_dir,
                        meta={"a": args.a, "n": env.n, "center_origin": True},
                    )


if __name__ == "__main__":
    main()
