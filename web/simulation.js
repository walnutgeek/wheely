/**
 * Main entry point: connects WebSocket, wires controls to scene, runs render loop.
 */
import { createScene } from '/static/scene.js';
import { createPlatformGroup, updatePlatform } from '/static/platform-viz.js';
import { createTerrainMesh } from '/static/terrain-viz.js';
import { setupControls, readConfig, updateInfoBar } from '/static/controls.js';

let ws = null;
let platformViz = null;
let terrainMesh = null;
let currentConfig = null;
let simRunning = false;

const viewport = document.getElementById('viewport');
const { scene, camera, renderer, controls } = createScene(viewport);

platformViz = createPlatformGroup();
scene.add(platformViz.group);

function connect() {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(`${protocol}//${location.host}/ws`);

  ws.onopen = () => {
    document.getElementById('conn-status').textContent = 'Connected';
    sendConfig(readConfig());
    sendTerrainRequest();
    ws.send(JSON.stringify({ type: 'solve_ik' }));
  };

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === 'frame') {
      updatePlatform(platformViz, msg, currentConfig);
      updateInfoBar(msg);
    } else if (msg.type === 'terrain_grid') {
      if (terrainMesh) scene.remove(terrainMesh);
      terrainMesh = createTerrainMesh(msg);
      scene.add(terrainMesh);
    } else if (msg.type === 'error') {
      console.error('Server error:', msg.errors);
    }
  };

  ws.onclose = () => {
    document.getElementById('conn-status').textContent = 'Disconnected';
    setTimeout(connect, 2000);
  };
}

function send(msg) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(msg));
  }
}

function sendConfig(config) {
  currentConfig = config;
  send({ type: 'set_config', params: config });
}

function sendTerrainRequest() {
  send({ type: 'get_terrain_grid', size: 6, resolution: 40 });
}

setupControls((config) => {
  sendConfig(config);
  send({ type: 'solve_ik' });
});

document.getElementById('terrain-select').addEventListener('change', (e) => {
  send({ type: 'set_terrain', name: e.target.value });
  sendTerrainRequest();
  send({ type: 'solve_ik' });
});

document.getElementById('strategy-select').addEventListener('change', (e) => {
  send({ type: 'set_strategy', name: e.target.value });
});

document.getElementById('btn-ik').addEventListener('click', () => {
  send({ type: 'solve_ik' });
});

document.getElementById('btn-sim').addEventListener('click', () => {
  const btn = document.getElementById('btn-sim');
  if (simRunning) {
    send({ type: 'stop_sim' });
    btn.classList.remove('active');
    btn.textContent = 'Run Sim';
    simRunning = false;
  } else {
    send({ type: 'start_sim' });
    btn.classList.add('active');
    btn.textContent = 'Stop';
    simRunning = true;
  }
});

function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}

connect();
animate();
