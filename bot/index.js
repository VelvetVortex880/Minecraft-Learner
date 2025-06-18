const mineflayer = require('mineflayer');
const {pathfinder, Movements, goals: {GoalBlock}} = require('mineflayer-pathfinder');
const autoeat = require('mineflayer-auto-eat').plugin;
const pvp = require('mineflayer-pvp').plugin;
const {Viewer} = require('prismarine-viewer');
const WebSocket = require('ws');

const bot = mineflayer.createBot({
  host: process.env.MC_HOST || 'localhost',
  port: parseInt(process.env.MC_PORT, 10) || 25565,
  username: process.env.MC_USER || 'LearnerBot'
});

bot.loadPlugin(pathfinder);
bot.loadPlugin(autoeat);
bot.loadPlugin(pvp);

const ws = new WebSocket(process.env.SERVER_WS || 'ws://localhost:8765');

ws.on('open', () => {
  console.log('Connected to instruction server');
});

ws.on('message', (data) => {
  try {
    const cmd = data.toString();
    console.log('Executing', cmd);
    eval(cmd); // caution: executed commands must be safe
  } catch (err) {
    console.error('Failed to execute command', err);
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
      bot.pathfinder.setGoal(new GoalBlock(target.position.x, target.position.y, target.position.z));
    }
  });
  Viewer(bot, {port: 3007, firstPerson: true});
});

bot.on('error', console.log);
bot.on('kicked', console.log);
