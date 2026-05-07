/**
 * Build and update the 3D platform mesh from simulation data.
 * Coordinate mapping: simulation uses Z-up, Three.js uses Y-up.
 * sim(x,y,z) -> three(x, z, -y)
 */
import * as THREE from 'three';

function toThree(v) {
  return new THREE.Vector3(v[0], v[2], -v[1]);
}

export function createPlatformGroup() {
  const group = new THREE.Group();

  const wheelGeo = new THREE.CylinderGeometry(0.15, 0.15, 0.08, 16);
  const wheelMat = new THREE.MeshStandardMaterial({ color: 0x333333, roughness: 0.8 });
  const hubMat = new THREE.MeshStandardMaterial({ color: 0xe94560 });
  const braceMat = new THREE.MeshStandardMaterial({ color: 0x44aa66, roughness: 0.5 });

  const wheels = {};
  for (const name of ['A', 'B', 'C']) {
    const wheel = new THREE.Mesh(wheelGeo, wheelMat);
    const hubGeo = new THREE.SphereGeometry(0.03, 8, 8);
    const hub = new THREE.Mesh(hubGeo, hubMat);
    wheel.add(hub);
    wheels[name] = wheel;
    group.add(wheel);
  }

  const armLineGeo1 = new THREE.BufferGeometry();
  const armLine1 = new THREE.Line(armLineGeo1, new THREE.LineBasicMaterial({ color: 0x4488aa, linewidth: 2 }));
  const armLineGeo2 = new THREE.BufferGeometry();
  const armLine2 = new THREE.Line(armLineGeo2, new THREE.LineBasicMaterial({ color: 0x4488aa, linewidth: 2 }));
  group.add(armLine1, armLine2);

  const braceLineGeo = new THREE.BufferGeometry();
  const braceLine = new THREE.Line(braceLineGeo, new THREE.LineBasicMaterial({ color: 0x44aa66, linewidth: 2 }));
  group.add(braceLine);

  const cargoGeo = new THREE.BoxGeometry(0.1, 0.05, 0.1);
  const cargo = new THREE.Mesh(cargoGeo, braceMat);
  group.add(cargo);

  const triGeo = new THREE.BufferGeometry();
  const triVerts = new Float32Array(9);
  triGeo.setAttribute('position', new THREE.BufferAttribute(triVerts, 3));
  const triMat = new THREE.MeshBasicMaterial({
    color: 0x4ade80, transparent: true, opacity: 0.2, side: THREE.DoubleSide
  });
  const triMesh = new THREE.Mesh(triGeo, triMat);
  group.add(triMesh);

  return {
    group, wheels,
    armLine1, armLine2, braceLine,
    cargo, triMesh,
    _wheelGeo: wheelGeo,
  };
}

export function updatePlatform(viz, frame, config) {
  const { wheels, armLine1, armLine2, braceLine, cargo, triMesh } = viz;

  for (const name of ['A', 'B', 'C']) {
    const pos = toThree(frame.wheels[name]);
    wheels[name].position.copy(pos);
  }

  if (config && config.wheel_radius) {
    const r = config.wheel_radius;
    const w = config.wheel_width || 0.08;
    const newGeo = new THREE.CylinderGeometry(r, r, w, 16);
    for (const name of ['A', 'B', 'C']) {
      wheels[name].geometry.dispose();
      wheels[name].geometry = newGeo;
    }
  }

  const a = toThree(frame.wheels.A);
  const b = toThree(frame.wheels.B);
  const c = toThree(frame.wheels.C);

  armLine1.geometry.dispose();
  armLine1.geometry = new THREE.BufferGeometry().setFromPoints([a, b]);
  armLine2.geometry.dispose();
  armLine2.geometry = new THREE.BufferGeometry().setFromPoints([a, c]);

  const bc = toThree(frame.brace_center);
  const halfBrace = new THREE.Vector3().subVectors(b, c).multiplyScalar(0.25);
  const braceL = new THREE.Vector3().copy(bc).add(halfBrace);
  const braceR = new THREE.Vector3().copy(bc).sub(halfBrace);
  braceLine.geometry.dispose();
  braceLine.geometry = new THREE.BufferGeometry().setFromPoints([braceL, braceR]);

  cargo.position.copy(bc);

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
