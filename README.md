# Minecraft-Learner

This project provides a simple Mineflayer based bot controlled via a Python server. The server uses a small RL model and WebSockets to communicate with the bot. The bot can follow players, pathfind, auto-eat, use PVP, and react to chat. A basic environment viewer is provided via prismarine-viewer.

**Note**: Due to environment limitations the npm dependencies are not installed here. You must run `npm install` yourself before using the bot. The Python server requires Python 3.8+ and PyTorch 2.2.

## Directory structure

- `bot/` – Node.js bot implementation
- `server/` – Python WebSocket server and RL stub

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

Once the bot is online it will log into the Minecraft server and connect to the Python server. You can send instructions to the server over WebSockets or modify `server.py` to use GPT/TogetherAI for natural language conversion. Sending the message `train` will run a dummy training loop for the RL model and save it to `model.pt`.

## Building a Windows installer

A simple approach is to use `pyinstaller` for the Python server and `pkg` for the Node.js bot. After building each executable, bundle them with a script or installer framework such as Inno Setup. Detailed instructions are omitted here.
