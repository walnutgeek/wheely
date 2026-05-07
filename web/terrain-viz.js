/**
 * Render terrain as a mesh from server-provided heightmap grid.
 */
import * as THREE from 'three';

export function createTerrainMesh(gridData) {
  const { size, resolution, heights } = gridData;
  const rows = heights.length;
  const cols = heights[0].length;
  const geo = new THREE.PlaneGeometry(size, size, cols - 1, rows - 1);

  const pos = geo.attributes.position;
  for (let j = 0; j < rows; j++) {
    for (let i = 0; i < cols; i++) {
      const idx = j * cols + i;
      const x = pos.getX(idx);
      const y = pos.getY(idx);
      const h = heights[j][i];
      pos.setXYZ(idx, x, h, -y);
    }
  }

  geo.computeVertexNormals();

  const mat = new THREE.MeshStandardMaterial({
    color: 0x2d5a27,
    roughness: 0.9,
    flatShading: true,
    side: THREE.DoubleSide,
  });

  return new THREE.Mesh(geo, mat);
}
