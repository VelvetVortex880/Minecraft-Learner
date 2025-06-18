# Minecraft-Learner

This project provides a Mineflayer bot controlled by a Python server running a lightweight PPO reinforcement learning agent. The bot sends observations (position, health and inventory) to the server over WebSockets and receives movement, jump, attack and other actions in response. It can follow players, pathfind, auto-eat, engage in PvP and visualise the world using `prismarine-viewer`.

**Note**: Due to environment limitations the npm dependencies are not installed here. You must run `npm install` yourself before using the bot. The Python server requires Python 3.8+ and PyTorch 2.2.

## Directory structure

- `bot/` – Node.js bot implementation
- `server/` – Python WebSocket server with a simple PPO agent storing its learning data in `rl.db`

## Installation

1. Install Node.js and Python 3.8 or newer.
2. From the `bot` directory run `npm install` to install dependencies (requires internet).
3. From the `server` directory create a virtual environment and install Python dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

This will install `websockets` and `torch`. GPU acceleration will be used automatically if available.

## Running

1. Start the Python server:

```bash
python server/server.py
```

2. In another terminal start the bot:

```bash
cd bot
node index.js
```

Set environment variables `MC_HOST`, `MC_PORT`, `MC_USER` to configure the Minecraft connection. `SERVER_WS` can specify the WebSocket URL of the server.

## Usage

Once the bot is online it logs into the Minecraft server and starts sending observations to the Python server. The server chooses an action with its PPO policy and sends it back to the bot. Transitions are recorded in the `rl.db` database and the model is updated regularly. You can adapt `server.py` to plug in language models or additional reward logic.

## Building a Windows installer

A simple approach is to use `pyinstaller` for the Python server and `pkg` for the Node.js bot. After building each executable, bundle them with a script or installer framework such as Inno Setup. Detailed instructions are omitted here.
