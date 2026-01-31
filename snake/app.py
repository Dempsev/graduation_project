import os
import sys
import threading
import time
from typing import Optional

from fastapi import FastAPI, Body
from fastapi.responses import FileResponse, JSONResponse
from starlette.staticfiles import StaticFiles

from snake_env import SnakeEnv
from agent import QLearningAgent, extract_features
from agent_dqn import DQNAgent
from utils import should_write_state, write_matrix_to_file, save_checkpoint, load_checkpoint, list_checkpoints, get_record_counts, get_record_targets

_PREPROCESS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "preprocess"))
if _PREPROCESS_DIR not in sys.path:
    sys.path.insert(0, _PREPROCESS_DIR)
from paths import SNAKE_CHECKPOINTS_DIR, SNAKE_CHECKPOINT_FILE


app = FastAPI(title="RL Snake")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# 静态页面
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

DEFAULT_N = 32  # multi-fidelity stage A: prioritize search efficiency
DOMAIN_A = 0.05  # meters, matches model_core a
env = SnakeEnv(n=DEFAULT_N)
AGENT_TYPE = "q"  # q | dqn
agent = QLearningAgent()

training_thread: Optional[threading.Thread] = None
training_running = False
episode_counter = 0
latest_state = env.as_dict()
episode_lengths = []  # 记录每个回合的最终蛇长度
episode_records = []  # 保存每回合最后一帧（用于Top3预览）
CHECKPOINT_DIR = SNAKE_CHECKPOINTS_DIR
DEFAULT_CHECKPOINT = SNAKE_CHECKPOINT_FILE


def training_loop():
    global training_running, episode_counter, latest_state
    while training_running:
        # 每个回合重置环境
        env.reset()
        episode_counter += 1
        steps = 0
        done = False
        if AGENT_TYPE == "dqn":
            s_matrix = env.get_matrix()
            while not done and training_running:
                a = agent.choose_action(s_matrix)
                reward, done = env.step(a)
                s_next_matrix = env.get_matrix()
                agent.remember(s_matrix, a, reward, s_next_matrix, done)
                agent.optimize()
                s_matrix = s_next_matrix
                steps += 1

                # 条件写入01矩阵到文件
                matrix = s_matrix
                if should_write_state(matrix, episode_counter, steps, reward, len(env.snake)):
                    write_matrix_to_file(
                        matrix,
                        episode_counter,
                        steps,
                        meta={"a": DOMAIN_A, "n": env.n, "center_origin": True},
                    )

                latest_state = env.as_dict()
                time.sleep(0.02)
        else:
            s = extract_features(env)
            while not done and training_running:
                a = agent.choose_action(s)
                reward, done = env.step(a)
                s_next = extract_features(env)
                agent.learn(s, a, reward, s_next, done)
                s = s_next
                steps += 1

                # 条件写入01矩阵到文件
                matrix = env.get_matrix()
                if should_write_state(matrix, episode_counter, steps, reward, len(env.snake)):
                    write_matrix_to_file(
                        matrix,
                        episode_counter,
                        steps,
                        meta={"a": DOMAIN_A, "n": env.n, "center_origin": True},
                    )

                latest_state = env.as_dict()
                time.sleep(0.02)

        agent.end_episode()
        # 记录该回合的最终长度
        episode_lengths.append(len(env.snake))
        # 保存该回合的最终帧
        episode_records.append({
            "episode": episode_counter,
            "length": len(env.snake),
            "state": env.as_dict(),
        })
        # 控制记录数量，避免内存过大
        if len(episode_records) > 5000:
            episode_records.pop(0)


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/state")
def get_state(limit: int = 200):
    # 记录计数与目标：填充缺失长度为0，保证前端始终可显示
    targets = get_record_targets(10)  # 默认展示长度4..10
    counts_raw = get_record_counts()
    counts_filled = {L: int(counts_raw.get(L, 0)) for L in targets.keys()}

    payload = {
        **latest_state,
        "episode": episode_counter,
        "running": training_running,
        "epsilon": agent.epsilon,
        "agent_type": AGENT_TYPE,
        # 返回最近 limit 个点，limit<=0 时返回全部
        "lengths": (episode_lengths if limit <= 0 else episode_lengths[-limit:]),
        "record_counts": counts_filled,
        "record_targets": targets,
    }
    return JSONResponse(payload)


@app.post("/train/start")
def train_start():
    global training_thread, training_running
    if training_running:
        return {"status": "already_running"}
    # 若存在旧checkpoint，先恢复（兼容老版本）。也可通过filename指定加载
    data = load_checkpoint(DEFAULT_CHECKPOINT)
    if data:
        # 仅当检查点类型与当前选择一致时才恢复智能体，避免覆盖用户选择
        global AGENT_TYPE, agent
        loaded_type = data.get("agent_type") or data.get("agent", {}).get("agent_type")
        if loaded_type and loaded_type == AGENT_TYPE:
            if AGENT_TYPE == "dqn":
                # 根据检查点中的网格大小创建网络并加载权重
                ev = data.get("env", {})
                n_for_net = ev.get("n", env.n)
                agent = DQNAgent(board_size=n_for_net)
                ag = data.get("agent", {})
                agent.load_state(ag)
            else:
                agent = QLearningAgent()
                ag = data.get("agent", {})
                agent.alpha = ag.get("alpha", agent.alpha)
                agent.gamma = ag.get("gamma", agent.gamma)
                agent.epsilon = ag.get("epsilon", agent.epsilon)
                agent.epsilon_min = ag.get("epsilon_min", agent.epsilon_min)
                agent.epsilon_decay = ag.get("epsilon_decay", agent.epsilon_decay)
                agent.Q = ag.get("Q", agent.Q)

        # 恢复env
        ev = data.get("env", {})
        env.n = ev.get("n", env.n)
        snake = ev.get("snake", [])
        env.snake = [tuple(p) for p in snake]
        food = ev.get("food", None)
        env.food = tuple(food) if food else None
        env.score = ev.get("score", 0)
        env.steps = ev.get("steps", 0)
        env.done = False

        # 恢复计数与历史
        global episode_counter, episode_lengths, latest_state
        episode_counter = data.get("episode_counter", episode_counter)
        episode_lengths = data.get("episode_lengths", episode_lengths)
        latest_state = env.as_dict()

    training_running = True
    training_thread = threading.Thread(target=training_loop, daemon=True)
    training_thread.start()
    return {"status": "started"}


@app.post("/train/stop")
def train_stop():
    global training_running, training_thread
    training_running = False
    # 等待线程结束以捕获最后一帧，并立即保存checkpoint
    if training_thread and training_thread.is_alive():
        training_thread.join(timeout=3.0)
    # 命名：checkpoint_ep{episode}_len{maxlen}.json
    max_len = max(episode_lengths) if episode_lengths else len(env.snake)
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    # DQN使用pt格式保存权重
    ext = ".pt" if AGENT_TYPE == "dqn" else ".json"
    filename = f"checkpoint_ep{episode_counter}_len{max_len}{ext}"
    path = os.path.join(CHECKPOINT_DIR, filename)
    save_checkpoint(path, agent, env, episode_counter, episode_lengths)
    return {"status": "stopped_and_saved", "file": filename}


@app.get("/top3")
def get_top3():
    # 选出长度前三的最后帧
    sorted_eps = sorted(episode_records, key=lambda r: r["length"], reverse=True)
    top = sorted_eps[:3]
    return JSONResponse({"top3": top})


@app.get("/checkpoints")
def get_checkpoints():
    return JSONResponse({"files": list_checkpoints(CHECKPOINT_DIR)})


@app.post("/train/load")
def train_load(filename: str = Body(..., embed=True)):
    # 加载指定检查点但不启动训练
    path = os.path.join(CHECKPOINT_DIR, filename)
    data = load_checkpoint(path)
    if not data:
        return {"status": "not_found", "file": filename}
    # 恢复agent类型与具体参数
    global AGENT_TYPE, agent
    loaded_type = data.get("agent_type") or data.get("agent", {}).get("agent_type") or "q"
    AGENT_TYPE = loaded_type
    if AGENT_TYPE == "dqn":
        agent = DQNAgent(board_size=env.n)
        agent.load_state(data.get("agent", {}))
    else:
        agent = QLearningAgent()
        ag = data.get("agent", {})
        agent.alpha = ag.get("alpha", agent.alpha)
        agent.gamma = ag.get("gamma", agent.gamma)
        agent.epsilon = ag.get("epsilon", agent.epsilon)
        agent.epsilon_min = ag.get("epsilon_min", agent.epsilon_min)
        agent.epsilon_decay = ag.get("epsilon_decay", agent.epsilon_decay)
        agent.Q = ag.get("Q", agent.Q)

    # 恢复env
    ev = data.get("env", {})
    env.n = ev.get("n", env.n)
    snake = ev.get("snake", [])
    env.snake = [tuple(p) for p in snake]
    food = ev.get("food", None)
    env.food = tuple(food) if food else None
    env.score = ev.get("score", 0)
    env.steps = ev.get("steps", 0)
    env.done = False

    # 恢复计数与历史
    global episode_counter, episode_lengths, latest_state
    episode_counter = data.get("episode_counter", episode_counter)
    episode_lengths = data.get("episode_lengths", episode_lengths)
    latest_state = env.as_dict()

    return {"status": "loaded", "file": filename}


@app.post("/config")
def set_config(n: int = Body(..., embed=True)):
    global env, latest_state
    # 更改网格大小并重置环境
    env = SnakeEnv(n=n)
    latest_state = env.as_dict()
    return {"status": "ok", "n": n}


@app.post("/agent/set")
def set_agent(type: str = Body(..., embed=True)):
    """切换智能体类型："q" 或 "dqn"。训练进行中时不允许切换。"""
    global AGENT_TYPE, agent
    if training_running:
        return {"status": "fail", "reason": "cannot_switch_while_running"}
    if type not in ("q", "dqn"):
        return {"status": "fail", "reason": "invalid_type"}
    AGENT_TYPE = type
    if AGENT_TYPE == "dqn":
        agent = DQNAgent(board_size=env.n)
    else:
        agent = QLearningAgent()
    return {"status": "ok", "agent_type": AGENT_TYPE}
