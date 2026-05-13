/**
 * Build and update the 3D platform mesh from simulation data.
 * Coordinate mapping: simulation uses Z-up, Three.js uses Y-up.
 * sim(x,y,z) -> three(x, z, -y)
 *
 * Structure per wheel: sphere wheel, vertical shaft.
 * Parallelogram arms connect body (wheel A) to wheels B and C.
 * Cross brace connects the two arms at brace_position fraction.
 */
import * as THREE from 'three';

const BAR_RADIUS = 0.008;
const JOINT_RADIUS = 0.012;

// --- Materials ---
const WHEEL_MAT = new THREE.MeshStandardMaterial({ color: 0x333333, roughness: 0.9 });
const SHAFT_MAT = new THREE.MeshStandardMaterial({ color: 0x888888, metalness: 0.6, roughness: 0.3 });
const ARM_BAR_MAT = new THREE.MeshStandardMaterial({ color: 0x4488aa, metalness: 0.3, roughness: 0.5 });
const BRACE_BAR_MAT = new THREE.MeshStandardMaterial({ color: 0x44aa66, metalness: 0.3, roughness: 0.5 });
const JOINT_MAT = new THREE.MeshStandardMaterial({ color: 0xe94560 });
const CARGO_MAT = new THREE.MeshStandardMaterial({ color: 0x44aa66, roughness: 0.5 });

// Shared geometries (unit-height cylinder scaled per frame)
const barGeo = new THREE.CylinderGeometry(BAR_RADIUS, BAR_RADIUS, 1, 8);
const jointGeo = new THREE.SphereGeometry(JOINT_RADIUS, 8, 8);

function toThree(v) {
  return new THREE.Vector3(v[0], v[2], -v[1]);
}

function makeBar(material) {
  return new THREE.Mesh(barGeo, material);
}

function makeJoint() {
  return new THREE.Mesh(jointGeo, JOINT_MAT);
}

/**
 * Position a unit-height cylinder mesh between two points.
 */
function positionBar(mesh, from, to) {
  const dir = new THREE.Vector3().subVectors(to, from);
  const len = dir.length();
  if (len < 1e-6) {
    mesh.visible = false;
    return;
  }
  mesh.visible = true;
  mesh.scale.set(1, len, 1);
  mesh.position.copy(from).add(to).multiplyScalar(0.5);
  const up = new THREE.Vector3(0, 1, 0);
  const quat = new THREE.Quaternion().setFromUnitVectors(up, dir.normalize());
  mesh.quaternion.copy(quat);
}

export function createPlatformGroup() {
  const group = new THREE.Group();

  // --- Wheels (3 spheres) ---
  const defaultRadius = 0.15;
  let wheelGeo = new THREE.SphereGeometry(defaultRadius, 16, 16);
  const wheels = {};
  for (const name of ['A', 'B', 'C']) {
    const wheel = new THREE.Mesh(wheelGeo, WHEEL_MAT);
    wheels[name] = wheel;
    group.add(wheel);
  }

  // --- Shafts / vertical tubes (3) ---
  const shafts = {};
  for (const name of ['A', 'B', 'C']) {
    const shaft = makeBar(SHAFT_MAT);
    shafts[name] = shaft;
    group.add(shaft);
  }

  // --- Arm bars (4: lower+upper for B arm, lower+upper for C arm) ---
  const armBars = {
    B_lower: makeBar(ARM_BAR_MAT),
    B_upper: makeBar(ARM_BAR_MAT),
    C_lower: makeBar(ARM_BAR_MAT),
    C_upper: makeBar(ARM_BAR_MAT),
  };
  for (const bar of Object.values(armBars)) group.add(bar);

  // --- Brace bars (4: lower, upper, vert_B, vert_C) ---
  const braceBars = {
    lower: makeBar(BRACE_BAR_MAT),
    upper: makeBar(BRACE_BAR_MAT),
    vert_B: makeBar(BRACE_BAR_MAT),
    vert_C: makeBar(BRACE_BAR_MAT),
  };
  for (const bar of Object.values(braceBars)) group.add(bar);

  // --- Joints (~10 connection points) ---
  const joints = [];
  for (let i = 0; i < 10; i++) {
    const j = makeJoint();
    joints.push(j);
    group.add(j);
  }

  // --- Cargo box ---
  const cargoGeo = new THREE.BoxGeometry(0.1, 0.05, 0.1);
  const cargo = new THREE.Mesh(cargoGeo, CARGO_MAT);
  group.add(cargo);

  // --- Support triangle (ground overlay) ---
  const triGeo = new THREE.BufferGeometry();
  const triVerts = new Float32Array(9);
  triGeo.setAttribute('position', new THREE.BufferAttribute(triVerts, 3));
  const triMat = new THREE.MeshBasicMaterial({
    color: 0x4ade80, transparent: true, opacity: 0.2, side: THREE.DoubleSide
  });
  const triMesh = new THREE.Mesh(triGeo, triMat);
  group.add(triMesh);

  return {
    group,
    wheels,
    shafts,
    armBars,
    braceBars,
    joints,
    cargo,
    triMesh,
    _wheelGeo: wheelGeo,
    _lastRadius: defaultRadius,
  };
}

export function updatePlatform(viz, frame, config) {
  const {
    wheels, shafts, armBars, braceBars, joints, cargo, triMesh
  } = viz;

  const r = (config && config.wheel_radius) || 0.15;
  const clearance = (config && config.clearance) || 0.03;
  const armHeight = (config && config.arm_height) || 0.06;
  const bracePos = (config && config.brace_position) || 0.5;

  // --- Recreate wheel geometry only when radius changes ---
  if (config && config.wheel_radius && config.wheel_radius !== viz._lastRadius) {
    if (viz._wheelGeo) viz._wheelGeo.dispose();
    viz._wheelGeo = new THREE.SphereGeometry(config.wheel_radius, 16, 16);
    for (const name of ['A', 'B', 'C']) {
      wheels[name].geometry = viz._wheelGeo;
    }
    viz._lastRadius = config.wheel_radius;
  }

  // --- Compute attachment points ---
  // frame.wheels[name] gives contact point (ground level) in sim coords (Z-up)
  // In Three.js (Y-up): wheel center is at contact + (0, r, 0)
  const contact = {};
  const wheelCenter = {};
  const shaftLower = {};  // lower arm bar attachment
  const shaftUpper = {};  // upper arm bar attachment

  for (const name of ['A', 'B', 'C']) {
    contact[name] = toThree(frame.wheels[name]);
    wheelCenter[name] = contact[name].clone().add(new THREE.Vector3(0, r, 0));
    shaftLower[name] = contact[name].clone().add(new THREE.Vector3(0, 2 * r + clearance, 0));
    shaftUpper[name] = contact[name].clone().add(new THREE.Vector3(0, 2 * r + clearance + armHeight, 0));
  }

  // --- Position wheels ---
  for (const name of ['A', 'B', 'C']) {
    wheels[name].position.copy(wheelCenter[name]);
  }

  // --- Position shafts (vertical tubes at each wheel) ---
  for (const name of ['A', 'B', 'C']) {
    positionBar(shafts[name], shaftLower[name], shaftUpper[name]);
  }

  // --- Position arm bars (parallelogram: body A to wheels B, C) ---
  positionBar(armBars.B_lower, shaftLower.A, shaftLower.B);
  positionBar(armBars.B_upper, shaftUpper.A, shaftUpper.B);
  positionBar(armBars.C_lower, shaftLower.A, shaftLower.C);
  positionBar(armBars.C_upper, shaftUpper.A, shaftUpper.C);

  // --- Compute brace attachment points ---
  const t = bracePos;
  const braceBLower = new THREE.Vector3().lerpVectors(shaftLower.A, shaftLower.B, t);
  const braceBUpper = new THREE.Vector3().lerpVectors(shaftUpper.A, shaftUpper.B, t);
  const braceCLower = new THREE.Vector3().lerpVectors(shaftLower.A, shaftLower.C, t);
  const braceCUpper = new THREE.Vector3().lerpVectors(shaftUpper.A, shaftUpper.C, t);

  // --- Position brace bars ---
  positionBar(braceBars.lower, braceBLower, braceCLower);
  positionBar(braceBars.upper, braceBUpper, braceCUpper);
  positionBar(braceBars.vert_B, braceBLower, braceBUpper);
  positionBar(braceBars.vert_C, braceCLower, braceCUpper);

  // --- Position joints at connection points ---
  const jointPositions = [
    shaftLower.A, shaftUpper.A,   // body tube ends
    shaftLower.B, shaftUpper.B,   // shaft B ends
    shaftLower.C, shaftUpper.C,   // shaft C ends
    braceBLower, braceBUpper,     // brace B ends
    braceCLower, braceCUpper,     // brace C ends
  ];
  for (let i = 0; i < joints.length; i++) {
    if (i < jointPositions.length) {
      joints[i].position.copy(jointPositions[i]);
      joints[i].visible = true;
    } else {
      joints[i].visible = false;
    }
  }

  // --- Position cargo at upper brace center ---
  const braceUpperCenter = new THREE.Vector3().addVectors(braceBUpper, braceCUpper).multiplyScalar(0.5);
  cargo.position.copy(braceUpperCenter);

  // --- Support triangle ---
  if (frame.support_triangle) {
    const verts = triMesh.geometry.attributes.position.array;
    for (let i = 0; i < 3; i++) {
      const sv = [frame.support_triangle[i][0], 0.001, -frame.support_triangle[i][1]];
      verts[i * 3] = sv[0];
      verts[i * 3 + 1] = sv[1];
      verts[i * 3 + 2] = sv[2];
    }
    triMesh.geometry.attributes.position.needsUpdate = true;
    triMesh.geometry.computeBoundingSphere();

    const stable = frame.stability_margin > 0;
    triMesh.material.color.setHex(stable ? 0x4ade80 : 0xf87171);
  }
}
