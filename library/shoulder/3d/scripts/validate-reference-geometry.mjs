/**
 * Check the shipped study-reference points against the actual GLB triangle meshes.
 * This checks geometric containment only. It does not validate clinical acupoint
 * location, needling depth, treatment efficacy, or anatomical model accuracy.
 * Run from any directory: node /path/to/project/scripts/validate-reference-geometry.mjs
 * With --write it also stores the result in public/geometry-validation.json, which
 * compute-acupoint-depth.mjs --check reproduces with its own GLB reader. Besides the labeled
 * muscle, scapula and humerus, each result records the shoulder add-on meshes of the same side
 * within 3 cm of the reference (three.js measurements for that cross-check); they do not
 * change pass/fail.
 */
import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { DoubleSide, Raycaster, Triangle, Vector3 } from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

const projectRoot = new URL('../', import.meta.url);
const referenceFile = new URL('src/model-references.json', projectRoot);
const outputFile = new URL('public/geometry-validation.json', projectRoot);
const addonFile = 'z-anatomy-1.4.0-shoulder-addon.glb';
const ADDON_NEAR_M = 0.03;
const tolerance = 1e-6; // Metres in the original GLB coordinate system.
const directions = [
  [1, 0.131, 0.173], [-0.239, 1, 0.317], [0.419, -0.227, 1],
  [-1, 0.371, -0.193], [0.271, -1, 0.413], [-0.337, 0.233, -1],
  [0.521, 0.677, -0.439],
].map(v => new Vector3(...v).normalize());
const expectedKeys = ['SI11', 'SI12', 'SI9', 'LI15', 'TE14']
  .flatMap(id => ['right', 'left'].map(side => `${id}-${side}`));

async function loadModel(filename, isNeeded, meshes) {
  const bytes = await readFile(new URL(`public/models/${filename}`, projectRoot));
  const buffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
  const gltf = await new GLTFLoader().parseAsync(buffer, '');
  gltf.scene.updateMatrixWorld(true);
  gltf.scene.traverse(mesh => {
    const id = mesh.userData.anatomyId;
    if (!mesh.isMesh || !isNeeded(id)) return;
    for (const material of Array.isArray(mesh.material) ? mesh.material : [mesh.material]) {
      material.side = DoubleSide;
    }
    const entry = meshes.get(id) ?? { meshes: [], triangles: [], file: filename };
    entry.meshes.push(mesh);
    const positions = mesh.geometry.attributes.position;
    const indices = mesh.geometry.index;
    const count = indices ? indices.count : positions.count;
    const vertexAt = index => new Vector3()
      .fromBufferAttribute(positions, indices ? indices.getX(index) : index)
      .applyMatrix4(mesh.matrixWorld);
    for (let i = 0; i < count; i += 3) {
      entry.triangles.push(new Triangle(vertexAt(i), vertexAt(i + 1), vertexAt(i + 2)));
    }
    meshes.set(id, entry);
  });
}

function inspectContainment(point, entry) {
  const rayCounts = directions.map(direction => {
    const hits = new Raycaster(point, direction, tolerance)
      .intersectObjects(entry.meshes, false)
      .map(hit => hit.distance)
      .sort((a, b) => a - b);
    const uniqueDistances = hits.filter((distance, i) => i === 0 || distance - hits[i - 1] > tolerance);
    return uniqueDistances.length;
  });
  const votes = rayCounts.map(count => count % 2 === 1);
  const unanimous = votes.every(value => value === votes[0]);
  const a = new Vector3(), b = new Vector3(), c = new Vector3(), cross = new Vector3();
  const closest = new Vector3();
  let solidAngle = 0, nearestDistanceSquared = Infinity;
  for (const triangle of entry.triangles) {
    triangle.closestPointToPoint(point, closest);
    nearestDistanceSquared = Math.min(nearestDistanceSquared, point.distanceToSquared(closest));
    a.subVectors(triangle.a, point);
    b.subVectors(triangle.b, point);
    c.subVectors(triangle.c, point);
    const la = a.length(), lb = b.length(), lc = c.length();
    const determinant = a.dot(cross.crossVectors(b, c));
    const denominator = la * lb * lc + a.dot(b) * lc + b.dot(c) * la + c.dot(a) * lb;
    solidAngle += 2 * Math.atan2(determinant, denominator);
  }
  const windingNumber = solidAngle / (4 * Math.PI);
  const windingInside = Math.abs(windingNumber) > 0.5;
  const rayInside = votes.filter(Boolean).length > votes.length / 2;
  const distance = Math.sqrt(nearestDistanceSquared);
  return {
    inside: rayInside,
    unanimousRays: unanimous,
    windingAgrees: windingInside === rayInside,
    windingNumber: Number(windingNumber.toFixed(9)),
    rayIntersectionCounts: rayCounts,
    distanceToSurfaceMetres: Number(distance.toFixed(9)),
    onBoundary: distance <= tolerance,
    reliable: unanimous && windingInside === rayInside && distance > tolerance,
  };
}

async function main() {
  const references = JSON.parse(await readFile(referenceFile, 'utf8'));
  const keys = Object.keys(references);
  const missing = expectedKeys.filter(key => !keys.includes(key));
  const unexpected = keys.filter(key => !expectedKeys.includes(key));
  if (missing.length || unexpected.length) {
    throw new Error(`Expected exactly 10 bilateral references. Missing: ${missing.join(', ') || 'none'}; unexpected: ${unexpected.join(', ') || 'none'}`);
  }
  const neededIds = new Set();
  for (const key of expectedKeys) {
    const reference = references[key];
    if (!Array.isArray(reference.position) || reference.position.length !== 3 || !reference.position.every(Number.isFinite)) {
      throw new Error(`${key}: position must contain three finite numbers`);
    }
    if (typeof reference.anatomyId !== 'string') throw new Error(`${key}: missing anatomyId`);
    const side = key.endsWith('-right') ? 'right' : 'left';
    if (!reference.anatomyId.endsWith(`-${side}`)) throw new Error(`${key}: anatomyId side does not match`);
    if (Math.sign(reference.position[0]) !== (side === 'right' ? -1 : 1)) throw new Error(`${key}: position side does not match`);
    neededIds.add(reference.anatomyId);
    neededIds.add(`appendicular-skeleton-scapula-${side}`);
    neededIds.add(`appendicular-skeleton-humerus-${side}`);
  }
  const meshes = new Map();
  await Promise.all([
    loadModel('z-anatomy-1.4.0-muscular.glb', id => neededIds.has(id), meshes),
    loadModel('z-anatomy-1.4.0-skeletal.glb', id => neededIds.has(id), meshes),
    loadModel(addonFile, id => typeof id === 'string', meshes),
  ]);
  for (const id of neededIds) if (!meshes.has(id)) throw new Error(`Mesh missing: ${id}`);
  const addonIds = [...meshes.keys()].filter(id => meshes.get(id).file === addonFile).sort();
  if (!addonIds.length) throw new Error(`No meshes read from ${addonFile}`);
  const results = expectedKeys.map(key => {
    const reference = references[key];
    const side = key.endsWith('-right') ? 'right' : 'left';
    const point = new Vector3(...reference.position);
    const muscle = inspectContainment(point, meshes.get(reference.anatomyId));
    const scapula = inspectContainment(point, meshes.get(`appendicular-skeleton-scapula-${side}`));
    const humerus = inspectContainment(point, meshes.get(`appendicular-skeleton-humerus-${side}`));
    const passed = muscle.reliable && muscle.inside && scapula.reliable && !scapula.inside && humerus.reliable && !humerus.inside;
    const addonMeshes = addonIds.filter(id => id.endsWith(`-${side}`)).map(id => ({ anatomyId: id, ...inspectContainment(point, meshes.get(id)) }))
      .filter(item => item.distanceToSurfaceMetres <= ADDON_NEAR_M || item.inside)
      .map(({ anatomyId, inside, unanimousRays, windingAgrees, windingNumber, rayIntersectionCounts, distanceToSurfaceMetres }) => ({ anatomyId, inside, unanimousRays, windingAgrees, windingNumber, rayIntersectionCounts, distanceToSurfaceMetres }));
    return { id: key, anatomyId: reference.anatomyId, position: reference.position, passed, muscle, scapula, humerus, addonMeshes };
  });
  const passed = results.every(result => result.passed);
  const report = {
    passed,
    scope: 'Geometric containment only; this does not establish clinical acupoint accuracy.',
    referenceFile: fileURLToPath(referenceFile),
    method: 'Shared GLB coordinates; 7 skew-ray parity checks plus signed solid-angle winding number; double-sided triangles; 1e-6 m boundary tolerance.',
    addonMeshesMethod: `addonMeshes: the same measurements for every ${addonFile} mesh of the same side whose surface lies within ${ADDON_NEAR_M * 100} cm of the reference (or contains it). Recorded so compute-acupoint-depth.mjs --check can reproduce them; they do not affect pass/fail.`,
    passedCount: results.filter(result => result.passed).length,
    totalCount: results.length,
    results,
  };
  console.log(JSON.stringify(report, null, 2));
  if (process.argv.includes('--write')) {
    if (!passed) throw new Error('Not writing public/geometry-validation.json: the check failed');
    await writeFile(outputFile, JSON.stringify({ ...report, referenceFile: 'src/model-references.json' }, null, 2) + '\n');
  }
  if (!passed) process.exitCode = 1;
}

main().catch(error => {
  console.log(JSON.stringify({ passed: false, error: error instanceof Error ? error.message : String(error) }, null, 2));
  process.exitCode = 1;
});
