import asyncio
import json
import websockets
import sqlite3
import torch
from torch import nn

DB_FILE = 'rl.db'

class RLModel(nn.Module):
    def __init__(self, input_size=10, hidden=64, output_size=10):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, hidden), nn.ReLU(),
            nn.Linear(hidden, output_size)
        )
    def forward(self, x):
        return self.net(x)

def load_model():
    model = RLModel()
    try:
        model.load_state_dict(torch.load('model.pt'))
    except FileNotFoundError:
        pass
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    return model.to(device)

def save_model(model):
    torch.save(model.state_dict(), 'model.pt')

async def process(msg, websocket, model):
    # Very naive: echo message back as command
    if msg == 'train':
        optim = torch.optim.Adam(model.parameters(), lr=1e-3)
        for _ in range(10):
            data = torch.randn(1, 10, device=model.net[0].weight.device)
            target = torch.randn(1, 10, device=model.net[0].weight.device)
            loss = nn.functional.mse_loss(model(data), target)
            optim.zero_grad(); loss.backward(); optim.step()
        save_model(model)
        await websocket.send("console.log('trained')")
    else:
        await websocket.send(msg)

async def handler(websocket):
    model = load_model()
    async for message in websocket:
        await process(message, websocket, model)

async def main():
    async with websockets.serve(handler, '0.0.0.0', 8765):
        print('Server started on ws://0.0.0.0:8765')
        await asyncio.Future()

if __name__ == '__main__':
    asyncio.run(main())
