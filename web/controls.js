/**
 * UI controls: read slider values, bind events, send config to server.
 */

export function readConfig() {
  return {
    arm_length: parseFloat(document.getElementById('arm-length').value),
    arm_splay_angle: parseFloat(document.getElementById('splay-angle').value) * Math.PI / 180,
    brace_position: parseFloat(document.getElementById('brace-pos').value),
    wheel_radius: parseFloat(document.getElementById('wheel-radius').value),
    clearance: parseFloat(document.getElementById('clearance').value),
    arm_height: parseFloat(document.getElementById('arm-height-viz').value),
  };
}

export function setupControls(onChange) {
  const sliders = ['arm-length', 'splay-angle', 'brace-pos', 'wheel-radius', 'clearance', 'arm-height-viz'];
  const valEls = {
    'arm-length': 'val-arm-length',
    'splay-angle': 'val-splay',
    'brace-pos': 'val-brace-pos',
    'wheel-radius': 'val-wheel-r',
    'clearance': 'val-clearance',
    'arm-height-viz': 'val-arm-height',
  };
  const formatters = {
    'arm-length': v => v.toFixed(2) + ' m',
    'splay-angle': v => v.toFixed(0) + '\u00B0',
    'brace-pos': v => v.toFixed(2),
    'wheel-radius': v => v.toFixed(2) + ' m',
    'clearance': v => v.toFixed(3) + ' m',
    'arm-height-viz': v => v.toFixed(3) + ' m',
  };

  for (const id of sliders) {
    const el = document.getElementById(id);
    el.addEventListener('input', () => {
      const v = parseFloat(el.value);
      document.getElementById(valEls[id]).textContent = formatters[id](v);
      onChange(readConfig());
    });
  }
}

export function updateInfoBar(frame) {
  const marginEl = document.getElementById('info-margin');
  if (frame.stability_margin !== undefined) {
    const m = frame.stability_margin;
    marginEl.textContent = m.toFixed(3);
    marginEl.className = 'value ' + (m > 0 ? 'stable' : 'unstable');
  }

  // Display pitch and roll in degrees
  if (frame.metrics) {
    document.getElementById('info-pitch').textContent =
      frame.metrics.tilt_pitch_deg.toFixed(1) + '\u00B0';
    document.getElementById('info-roll').textContent =
      frame.metrics.tilt_roll_deg.toFixed(1) + '\u00B0';
  } else if (frame.tilt_pitch !== undefined && frame.tilt_roll !== undefined) {
    // Fallback for non-sim frames (solve_ik, get_frame) -- convert radians to degrees
    document.getElementById('info-pitch').textContent =
      (frame.tilt_pitch * 180 / Math.PI).toFixed(1) + '\u00B0';
    document.getElementById('info-roll').textContent =
      (frame.tilt_roll * 180 / Math.PI).toFixed(1) + '\u00B0';
  }

  if (frame.time !== undefined) {
    document.getElementById('info-time').textContent = frame.time.toFixed(2) + ' s';
  }
}
