import asyncio
import json
import sqlite3
from dataclasses import dataclass

import torch
from torch import nn

DB_FILE = 'rl.db'
ACTIONS = ['forward', 'back', 'left', 'right', 'jump', 'stop', 'attack', 'eat']


class RLModel(nn.Module):
    """Simple policy network used by the PPO agent."""

    def __init__(self, input_size=6, hidden=64, output_size=len(ACTIONS)):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, hidden),
            nn.ReLU(),
            nn.Linear(hidden, output_size),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def setup_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS transitions (obs TEXT, action INTEGER, reward REAL)"
    )
    conn.commit()
    return conn


def save_model(model: nn.Module) -> None:
    torch.save(model.state_dict(), "model.pt")


def load_model(device: str) -> nn.Module:
    model = RLModel().to(device)
    try:
        model.load_state_dict(torch.load("model.pt", map_location=device))
    except FileNotFoundError:
        pass
    return model


@dataclass
class PPOAgent:
    model: nn.Module
    optimizer: torch.optim.Optimizer
    conn: sqlite3.Connection
    device: str

    def preprocess(self, obs: dict) -> torch.Tensor:
        inv_count = sum(item["count"] for item in obs.get("inventory", []))
        data = [
            obs["position"]["x"],
            obs["position"]["y"],
            obs["position"]["z"],
            obs.get("health", 0),
            obs.get("food", 0),
            inv_count,
        ]
        return torch.tensor(data, dtype=torch.float32, device=self.device)

    def select_action(self, obs_tensor: torch.Tensor) -> tuple[int, torch.Tensor]:
        logits = self.model(obs_tensor)
        dist = torch.distributions.Categorical(logits=logits)
        action = dist.sample()
        return int(action.item()), dist.log_prob(action)

    def store_transition(self, obs: torch.Tensor, action: int, reward: float) -> None:
        self.conn.execute(
            "INSERT INTO transitions (obs, action, reward) VALUES (?, ?, ?)",
            (json.dumps(obs.tolist()), int(action), float(reward)),
        )
        self.conn.commit()

    def update(self) -> None:
        rows = self.conn.execute(
            "SELECT obs, action, reward FROM transitions ORDER BY rowid DESC LIMIT 32"
        ).fetchall()
        if not rows:
            return
        obs_batch = torch.stack(
            [torch.tensor(json.loads(r[0]), device=self.device) for r in rows]
        )
        act_batch = torch.tensor([r[1] for r in rows], device=self.device)
        rew_batch = torch.tensor([r[2] for r in rows], device=self.device)

        logits = self.model(obs_batch)
        dist = torch.distributions.Categorical(logits=logits)
        log_probs = dist.log_prob(act_batch)
        ratios = torch.exp(log_probs)
        clipped = torch.clamp(ratios, 0.8, 1.2) * rew_batch
        loss = -(torch.min(ratios * rew_batch, clipped)).mean()
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        save_model(self.model)


async def handle_message(agent: PPOAgent, msg: str, websocket):
    try:
        data = json.loads(msg)
    except json.JSONDecodeError:
        return

    if data.get("type") == "obs":
        obs_tensor = agent.preprocess(data)
        action_id, log_prob = agent.select_action(obs_tensor)
        reward = 0.0
        agent.store_transition(obs_tensor, action_id, reward)
        agent.update()
        await websocket.send(json.dumps({"type": "action", "name": ACTIONS[action_id]}))


async def handler(websocket):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    conn = setup_db()
    model = load_model(device)
    agent = PPOAgent(model, torch.optim.Adam(model.parameters(), lr=1e-3), conn, device)
    async for message in websocket:
        await handle_message(agent, message, websocket)


async def main() -> None:
    async with websockets.serve(handler, "0.0.0.0", 8765):
        print("Server started on ws://0.0.0.0:8765")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())

