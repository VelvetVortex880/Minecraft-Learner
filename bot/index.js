const mineflayer = require('mineflayer');
const { pathfinder, Movements, goals } = require('mineflayer-pathfinder');
const autoeat = require('mineflayer-auto-eat').plugin;
const pvp = require('mineflayer-pvp').plugin;
const { Viewer } = require('prismarine-viewer');
const WebSocket = require('ws');
const { Vec3 } = require('vec3');

const bot = mineflayer.createBot({
  host: process.env.MC_HOST || 'localhost',
  port: parseInt(process.env.MC_PORT, 10) || 25565,
  username: process.env.MC_USER || 'LearnerBot'
});

bot.loadPlugin(pathfinder);
bot.loadPlugin(autoeat);
bot.loadPlugin(pvp);

const ws = new WebSocket(process.env.SERVER_WS || 'ws://localhost:8765');

function getObservation() {
  const pos = bot.entity.position;
  return {
    type: 'obs',
    position: { x: pos.x, y: pos.y, z: pos.z },
    health: bot.health,
    food: bot.food,
    inventory: bot.inventory.items().map(i => ({ name: i.name, count: i.count }))
  };
}

function sendObservation() {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(getObservation()));
  }
}

function clearControls() {
  ['forward','back','left','right','jump','sprint'].forEach(c => bot.setControlState(c, false));
}

function handleAction(msg) {
  clearControls();
  switch (msg.name) {
    case 'forward':
    case 'back':
    case 'left':
    case 'right':
      bot.setControlState(msg.name, true);
      break;
    case 'jump':
      bot.setControlState('jump', true);
      setTimeout(() => bot.setControlState('jump', false), 500);
      break;
    case 'attack':
      const target = bot.nearestEntity(e => e.type === 'mob');
      if (target) bot.attack(target);
      break;
    case 'eat':
      if (bot.autoEat) bot.autoEat.eat();
      break;
    case 'stop':
    default:
      break;
  }
}

ws.on('open', () => {
  console.log('Connected to instruction server');
  setInterval(sendObservation, 1000);
});

ws.on('message', (data) => {
  try {
    const msg = JSON.parse(data.toString());
    if (msg.type === 'action') handleAction(msg);
  } catch (err) {
    console.error('Bad message from server', err);
  }
});

bot.once('spawn', () => {
  const mcData = require('minecraft-data')(bot.version);
  const defaultMove = new Movements(bot, mcData);
  bot.on('autoeat_started', ()=> console.log('Auto Eat started')); 
  bot.on('autoeat_finished', ()=> console.log('Auto Eat finished')); 
  bot.on('chat', (username, message) => {
    if (username === bot.username) return;
    if (message.startsWith('!')) {
      const command = message.slice(1);
      bot.chat(`/`+command);
    } else if (message === 'follow') {
      const target = bot.players[username]?.entity;
      if (!target) return bot.chat("I can't see you.");
      bot.pathfinder.setGoal(new goals.GoalFollow(target, 1));
    }
  });
  Viewer(bot, {port: 3007, firstPerson: true});
});

bot.on('error', console.log);
bot.on('kicked', console.log);
