"""Shared helpers for chapter 3D add-on models (ST-7, AN-44).

Pure Python (no numpy, no Blender) so CI can check a shipped add-on: read GLB
nodes and world bounds, build add-on metadata from the exporter report, and run
the position checks a chapter's atlas-addon.json declares.
"""
import json
import math
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ATLAS = ROOT / 'site/build/atlas'
APP = ROOT / 'library/shoulder/3d'          # the shared 3D app (hip borrows it)
MODELS = APP / 'public/models'
SOURCE = json.loads((ATLAS / 'source.json').read_text(encoding='utf-8'))
BASE_METADATA = {'muscular': MODELS / 'muscular.metadata.json', 'skeletal': MODELS / 'skeletal.metadata.json'}
BASE_GLB = {'muscular': MODELS / 'z-anatomy-1.4.0-muscular.glb', 'skeletal': MODELS / 'z-anatomy-1.4.0-skeletal.glb'}
SCALE, OFFSET_Y = 7, -6.1                     # model.ts modelScale / modelPosition


def chapter_config(chapter):
    path = ROOT / 'library' / chapter / '3d/atlas-addon.json'
    return path, json.loads(path.read_text(encoding='utf-8'))


def output_paths(chapter, config):
    out = config['output']
    return {key: APP / out[key] for key in ('glb', 'metadata', 'provenance')}


def read_glb(path):
    data = Path(path).read_bytes()
    if data[:4] != b'glTF':
        raise ValueError(f'{path}: not a GLB file')
    json_len = struct.unpack_from('<I', data, 12)[0]
    gltf = json.loads(data[20:20 + json_len])
    bin_start = 20 + json_len
    binary = b''
    if bin_start < len(data):
        bin_len = struct.unpack_from('<I', data, bin_start)[0]
        binary = data[bin_start + 8:bin_start + 8 + bin_len]
    return gltf, binary


_COMPONENT = {5126: ('f', 4, None), 5122: ('h', 2, 32767), 5123: ('H', 2, 65535), 5120: ('b', 1, 127), 5121: ('B', 1, 255)}


def _positions(gltf, binary, accessor_index):
    accessor = gltf['accessors'][accessor_index]
    view = gltf['bufferViews'][accessor['bufferView']]
    code, size, norm = _COMPONENT[accessor['componentType']]
    stride = view.get('byteStride', 3 * size)
    offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    fmt = '<' + code * 3
    normalise = accessor.get('normalized') and norm
    for i in range(accessor['count']):
        x, y, z = struct.unpack_from(fmt, binary, offset + i * stride)
        yield (x / norm, y / norm, z / norm) if normalise else (x, y, z)


def _matrix(node):
    if 'matrix' in node:
        m = node['matrix']
        return [[m[c * 4 + r] for c in range(4)] for r in range(4)]
    qx, qy, qz, qw = node.get('rotation', [0, 0, 0, 1])
    sx, sy, sz = node.get('scale', [1, 1, 1])
    tx, ty, tz = node.get('translation', [0, 0, 0])
    r = [[1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw), 2 * (qx * qz + qy * qw)],
         [2 * (qx * qy + qz * qw), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qw)],
         [2 * (qx * qz - qy * qw), 2 * (qy * qz + qx * qw), 1 - 2 * (qx * qx + qy * qy)]]
    return [[r[0][0] * sx, r[0][1] * sy, r[0][2] * sz, tx],
            [r[1][0] * sx, r[1][1] * sy, r[1][2] * sz, ty],
            [r[2][0] * sx, r[2][1] * sy, r[2][2] * sz, tz],
            [0, 0, 0, 1]]


def _mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def mesh_nodes(path, wanted=None):
    """Return {source name: {'anatomyId', 'extras', 'min', 'max', 'center'}} in world metres (glTF y-up).

    `wanted` limits the work to a set of source names (the part after '__' in the node name)."""
    gltf, binary = read_glb(path)
    nodes = gltf['nodes']
    parent = {child: i for i, node in enumerate(nodes) for child in node.get('children', [])}
    result = {}
    for i, node in enumerate(nodes):
        if 'mesh' not in node:
            continue
        name = node.get('name', '')
        source = name.split('__', 1)[-1]
        if wanted is not None and source not in wanted:
            continue
        matrix, k = _matrix(node), i
        while k in parent:
            k = parent[k]
            matrix = _mul(_matrix(nodes[k]), matrix)
        lo, hi = [math.inf] * 3, [-math.inf] * 3
        for primitive in gltf['meshes'][node['mesh']]['primitives']:
            for x, y, z in _positions(gltf, binary, primitive['attributes']['POSITION']):
                w = [matrix[r][0] * x + matrix[r][1] * y + matrix[r][2] * z + matrix[r][3] for r in range(3)]
                for axis in range(3):
                    lo[axis] = min(lo[axis], w[axis]); hi[axis] = max(hi[axis], w[axis])
        extras = node.get('extras', {})
        result[source] = {'node': name, 'anatomyId': extras.get('anatomyId'), 'extras': extras,
                          'min': lo, 'max': hi, 'center': [(lo[a] + hi[a]) / 2 for a in range(3)]}
    return result


def metadata_from_report(report, chapter):
    """Vanatome-style metadata for an add-on bundle (positions as in release-lib.mjs)."""
    def position(center):
        x, y, z = center
        return [round(x * SCALE, 4), round(z * SCALE + OFFSET_Y, 4), round(-y * SCALE, 4)]
    structures, node_count = [], 0
    for group_id, group in report['groups'].items():
        if group['missing']:
            raise ValueError(f'{group_id}: source objects not found: {group["missing"]}')
        for structure_id, s in sorted(group['structures'].items(), key=lambda item: (item[0] != group_id, item[0])):
            entry = {'id': structure_id, 'name': s['name'], 'kind': s['kind'], 'parentId': s['parentId'],
                     'system': s['system'], 'layer': s['system'], 'selectable': s['selectable'],
                     'position': position(s['centerBlender']), 'objectCount': len(s['nodes'])}
            structures.append(entry)
            node_count += len(s['nodes'])
    return {'schemaVersion': 1, 'atlasId': 'vanatome-human', 'atlasVersion': SOURCE['frame']['atlasVersion'],
            'buildId': SOURCE['frame']['buildId'], 'bundleId': f'{chapter}-addon', 'nodeCount': node_count,
            'structures': structures}


def _bone_box(bones, name):
    if name not in bones:
        raise ValueError(f'check refers to unknown skeletal mesh "{name}"')
    return bones[name]


def _overlaps(a, b, tolerance):
    return all(a['min'][i] - tolerance <= b['max'][i] and b['min'][i] - tolerance <= a['max'][i] for i in range(3))


RULES = {
    # vertical extent (y is up, metres)
    'topAbove': lambda s, b, t: s['max'][1] > b['max'][1] + t,
    'topBelow': lambda s, b, t: s['max'][1] < b['max'][1] - t,
    'bottomBelow': lambda s, b, t: s['min'][1] < b['min'][1] - t,
    'bottomAbove': lambda s, b, t: s['min'][1] > b['min'][1] + t,
    # bounding boxes touch, allowing `tolerance` metres of gap
    'overlaps': lambda s, b, t: _overlaps(s, b, t),
}


def check_addon(chapter, glb=None, metadata=None):
    """Return a list of problems (empty = pass) for a chapter's add-on files."""
    config_path, config = chapter_config(chapter)
    paths = output_paths(chapter, config)
    glb, metadata = Path(glb or paths['glb']), Path(metadata or paths['metadata'])
    problems = []
    meta = json.loads(metadata.read_text(encoding='utf-8'))
    base = {key: json.loads(p.read_text(encoding='utf-8')) for key, p in BASE_METADATA.items()}
    for key, b in base.items():
        if meta['atlasVersion'] != b['atlasVersion']:
            problems.append(f'atlasVersion {meta["atlasVersion"]} differs from the {key} base {b["atlasVersion"]}')
    if meta['buildId'] != base['muscular']['buildId']:
        problems.append(f'buildId {meta["buildId"]} differs from the base {base["muscular"]["buildId"]} (composition.ts refuses mixed builds)')
    base_ids = {s['id'] for b in base.values() for s in b['structures']}
    ids = [s['id'] for s in meta['structures']]
    for duplicate in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(f'structure {duplicate} appears twice')
    for clash in sorted(set(ids) & base_ids):
        problems.append(f'structure {clash} already exists in the base model (composition.ts refuses duplicates)')
    known = set(ids) | base_ids
    for s in meta['structures']:
        if s.get('parentId') and s['parentId'] not in known:
            problems.append(f'{s["id"]}: parent {s["parentId"]} is not defined')

    parts = mesh_nodes(glb)
    by_id = {}
    for source, part in parts.items():
        if not part['anatomyId']:
            problems.append(f'GLB node {part["node"]} has no anatomyId extra')
        by_id.setdefault(part['anatomyId'], []).append(part)
    for s in meta['structures']:
        found = len(by_id.get(s['id'], []))
        if found != s['objectCount']:
            problems.append(f'{s["id"]}: metadata says {s["objectCount"]} mesh(es), GLB has {found}')
    for anatomy_id in by_id:
        if anatomy_id not in set(ids):
            problems.append(f'GLB mesh {anatomy_id} is not in the metadata')

    # sides: Z-Anatomy ".l" is the body's left, which is +x in this frame (as for the bundled deltoid)
    for anatomy_id, found in by_id.items():
        for part in found:
            if anatomy_id.endswith('-left') and part['center'][0] <= 0:
                problems.append(f'{anatomy_id}: a left-side mesh sits right of the midline')
            if anatomy_id.endswith('-right') and part['center'][0] >= 0:
                problems.append(f'{anatomy_id}: a right-side mesh sits left of the midline')
    for anatomy_id, found in by_id.items():
        if not anatomy_id.endswith('-left'):
            continue
        twin = by_id.get(anatomy_id[:-5] + '-right')
        if not twin:
            problems.append(f'{anatomy_id}: no right-side twin')
            continue
        l, r = found[0], twin[0]
        gap = max(max(abs(l['min'][1] - r['min'][1]), abs(l['max'][1] - r['max'][1])),
                  max(abs(l['min'][2] - r['min'][2]), abs(l['max'][2] - r['max'][2])),
                  max(abs(l['max'][0] + r['min'][0]), abs(l['min'][0] + r['max'][0])))
        if gap > 0.01:
            problems.append(f'{anatomy_id}: left and right meshes are not mirror images ({gap * 100:.1f} cm apart)')

    # AN-42: declared position checks against bones, both sides
    checks = config.get('checks', [])
    bone_names = {c['bone'].replace('{side}', side) for c in checks for side in ('.l', '.r')}
    bones = mesh_nodes(BASE_GLB['skeletal'], bone_names)
    for c in checks:
        for side, suffix in (('.l', 'left'), ('.r', 'right')):
            structure_id = c['structure'].replace('{side}', suffix)
            bone = c['bone'].replace('{side}', side)
            meshes = by_id.get(structure_id)
            if not meshes:
                problems.append(f'check {c["rule"]}: {structure_id} not in the GLB')
                continue
            if not RULES[c['rule']](meshes[0], _bone_box(bones, bone), c.get('tolerance', 0.0)):
                problems.append(f'{structure_id}: expected {c["rule"]} {bone} ({c.get("why", "")})')
    return problems
