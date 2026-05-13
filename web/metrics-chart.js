/**
 * Canvas-based rolling time-series chart for simulation metrics.
 *
 * Displays pitch (blue), roll (red), and torque magnitude (yellow) over time.
 * Keeps a rolling buffer of ~300 points (~10 seconds at 30fps).
 * Auto-scales Y axes.
 *
 * Usage:
 *   import { updateChart, clearChart } from '/static/metrics-chart.js';
 *   updateChart(metrics);  // called each frame
 *   clearChart();          // called on sim start / strategy change
 */

const MAX_POINTS = 300;

/** @type {{time: number, pitch: number, roll: number, torque: number}[]} */
let buffer = [];

/** @type {HTMLCanvasElement | null} */
let canvas = null;

/** @type {CanvasRenderingContext2D | null} */
let ctx = null;

function ensureCanvas() {
  if (!canvas) {
    canvas = document.getElementById('metrics-chart');
    if (canvas) {
      ctx = canvas.getContext('2d');
    }
  }
  return ctx !== null;
}

/**
 * Add a data point from the current frame's metrics and redraw the chart.
 * @param {{tilt_pitch_deg: number, tilt_roll_deg: number, actuator_torque_pitch?: number, actuator_torque_roll?: number}} metrics
 * @param {number} time - simulation time in seconds
 */
export function updateChart(metrics, time) {
  if (!ensureCanvas()) return;

  const torquePitch = metrics.actuator_torque_pitch || 0;
  const torqueRoll = metrics.actuator_torque_roll || 0;
  const torqueMag = Math.sqrt(torquePitch * torquePitch + torqueRoll * torqueRoll);

  buffer.push({
    time: time,
    pitch: metrics.tilt_pitch_deg,
    roll: metrics.tilt_roll_deg,
    torque: torqueMag,
  });

  if (buffer.length > MAX_POINTS) {
    buffer = buffer.slice(buffer.length - MAX_POINTS);
  }

  draw();
}

/**
 * Clear the chart buffer and redraw (empty).
 */
export function clearChart() {
  buffer = [];
  if (ensureCanvas()) {
    draw();
  }
}

// --- Drawing ---

const COLORS = {
  pitch: '#60a5fa',   // blue
  roll: '#f87171',    // red
  torque: '#facc15',  // yellow
  grid: '#1a2744',
  text: '#888',
  bg: '#0a0a1a',
};

const MARGIN = { top: 12, right: 54, bottom: 20, left: 48 };

function draw() {
  const w = canvas.width;
  const h = canvas.height;
  const plotW = w - MARGIN.left - MARGIN.right;
  const plotH = h - MARGIN.top - MARGIN.bottom;

  // Clear
  ctx.fillStyle = COLORS.bg;
  ctx.fillRect(0, 0, w, h);

  if (buffer.length < 2) {
    // Not enough data to draw
    ctx.fillStyle = COLORS.text;
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Waiting for simulation data...', w / 2, h / 2);
    return;
  }

  // Compute ranges
  let minAngle = Infinity, maxAngle = -Infinity;
  let minTorque = Infinity, maxTorque = -Infinity;
  const tStart = buffer[0].time;
  const tEnd = buffer[buffer.length - 1].time;

  for (const pt of buffer) {
    if (pt.pitch < minAngle) minAngle = pt.pitch;
    if (pt.pitch > maxAngle) maxAngle = pt.pitch;
    if (pt.roll < minAngle) minAngle = pt.roll;
    if (pt.roll > maxAngle) maxAngle = pt.roll;
    if (pt.torque < minTorque) minTorque = pt.torque;
    if (pt.torque > maxTorque) maxTorque = pt.torque;
  }

  // Add padding to ranges
  const anglePad = Math.max((maxAngle - minAngle) * 0.1, 0.5);
  minAngle -= anglePad;
  maxAngle += anglePad;

  const torquePad = Math.max((maxTorque - minTorque) * 0.1, 0.1);
  minTorque = Math.max(0, minTorque - torquePad);
  maxTorque += torquePad;

  const tRange = tEnd - tStart || 1;
  const angleRange = maxAngle - minAngle || 1;
  const torqueRange = maxTorque - minTorque || 1;

  // Helper to map coordinates
  function xOf(t) {
    return MARGIN.left + ((t - tStart) / tRange) * plotW;
  }
  function yAngle(v) {
    return MARGIN.top + (1 - (v - minAngle) / angleRange) * plotH;
  }
  function yTorque(v) {
    return MARGIN.top + (1 - (v - minTorque) / torqueRange) * plotH;
  }

  // Draw grid lines (horizontal)
  ctx.strokeStyle = COLORS.grid;
  ctx.lineWidth = 1;
  const numGridLines = 4;
  for (let i = 0; i <= numGridLines; i++) {
    const y = MARGIN.top + (i / numGridLines) * plotH;
    ctx.beginPath();
    ctx.moveTo(MARGIN.left, y);
    ctx.lineTo(MARGIN.left + plotW, y);
    ctx.stroke();
  }

  // Draw zero line for angle axis if it falls in range
  if (minAngle <= 0 && maxAngle >= 0) {
    const y0 = yAngle(0);
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(MARGIN.left, y0);
    ctx.lineTo(MARGIN.left + plotW, y0);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  // Draw lines
  function drawLine(key, colorKey, yFn) {
    ctx.strokeStyle = COLORS[colorKey];
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    for (let i = 0; i < buffer.length; i++) {
      const x = xOf(buffer[i].time);
      const y = yFn(buffer[i][key]);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }

  drawLine('pitch', 'pitch', yAngle);
  drawLine('roll', 'roll', yAngle);
  drawLine('torque', 'torque', yTorque);

  // Axis labels - left (angle)
  ctx.fillStyle = COLORS.text;
  ctx.font = '10px sans-serif';
  ctx.textAlign = 'right';
  ctx.textBaseline = 'top';
  ctx.fillText(maxAngle.toFixed(1) + '\u00B0', MARGIN.left - 4, MARGIN.top);
  ctx.textBaseline = 'bottom';
  ctx.fillText(minAngle.toFixed(1) + '\u00B0', MARGIN.left - 4, MARGIN.top + plotH);

  // Axis labels - right (torque)
  ctx.textAlign = 'left';
  ctx.fillStyle = COLORS.torque;
  ctx.textBaseline = 'top';
  ctx.fillText(maxTorque.toFixed(1) + ' Nm', MARGIN.left + plotW + 4, MARGIN.top);
  ctx.textBaseline = 'bottom';
  ctx.fillText(minTorque.toFixed(1) + ' Nm', MARGIN.left + plotW + 4, MARGIN.top + plotH);

  // Time axis labels
  ctx.fillStyle = COLORS.text;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';
  ctx.fillText(tStart.toFixed(1) + 's', MARGIN.left, MARGIN.top + plotH + 4);
  ctx.fillText(tEnd.toFixed(1) + 's', MARGIN.left + plotW, MARGIN.top + plotH + 4);

  // Legend
  const legendX = MARGIN.left + 8;
  const legendY = MARGIN.top + 4;
  ctx.font = '10px sans-serif';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'top';

  ctx.fillStyle = COLORS.pitch;
  ctx.fillRect(legendX, legendY, 10, 3);
  ctx.fillText('Pitch', legendX + 14, legendY - 3);

  ctx.fillStyle = COLORS.roll;
  ctx.fillRect(legendX + 55, legendY, 10, 3);
  ctx.fillText('Roll', legendX + 69, legendY - 3);

  ctx.fillStyle = COLORS.torque;
  ctx.fillRect(legendX + 103, legendY, 10, 3);
  ctx.fillText('Torque', legendX + 117, legendY - 3);
}
