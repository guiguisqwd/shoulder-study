#!/usr/bin/env python3
"""Project 3D model meshes to 2D outlines, so the chapter's figures sit on the same bones as the 3D viewer.

Run once when the structure list changes (needs: pip install trimesh shapely):
    python3 library/hip/figures/tools/project-outlines.py
Writes outlines.json next to this file: {view: {structureId: [[ [x, y], ... ], ...]}} in model metres,
y pointing down, image-left = viewer's left. build-figures.py only reads that JSON (no 3D libraries needed).
Views: ant (from the front), post (from behind), lat (right side seen from the right), med (right side seen from the left).
To reuse for another chapter, copy this file and change STRUCTURES."""
import json
from pathlib import Path
import numpy as np
import trimesh
from shapely.geometry import Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[4]
MODELS = ROOT / 'library/shoulder/3d/public/models'
STRUCTURES = {
    'skeletal': ['skeleton-hip-bone-right', 'skeleton-hip-bone-left', 'skeleton-sacrum', 'skeleton-coccyx',
                 'appendicular-skeleton-femur-right', 'appendicular-skeleton-femur-left',
                 'appendicular-skeleton-tibia-right', 'appendicular-skeleton-fibula-right', 'appendicular-skeleton-patella-right',
                 'skeleton-vertebra-l1', 'skeleton-vertebra-l2', 'skeleton-vertebra-l3', 'skeleton-vertebra-l4', 'skeleton-vertebra-l5'],
    'muscular': [f'superficial-gluteal-muscles-{m}-right' for m in
                 ['gluteus-maximus-muscle', 'gluteus-medius-muscle', 'gluteus-minimus-muscle', 'tensor-fasciae-latae']]
               + [f'deep-gluteal-muscles-{m}-right' for m in
                  ['piriformis-muscle', 'superior-gemellus-muscle', 'obturator-internus', 'inferior-gemellus-muscle',
                   'quadratus-femoris-muscle', 'obturator-externus']],
}
VIEWS = {'ant': lambda v: np.c_[v[:, 0], -v[:, 1]], 'post': lambda v: np.c_[-v[:, 0], -v[:, 1]],
         'lat': lambda v: np.c_[v[:, 2], -v[:, 1]], 'med': lambda v: np.c_[-v[:, 2], -v[:, 1]]}


def meshes(kind):
    scene = trimesh.load(MODELS / f'z-anatomy-1.4.0-{kind}.glb')
    found = {}
    for node in scene.graph.nodes_geometry:
        sid = node.split('__')[0]
        if sid in STRUCTURES[kind]:
            transform, geom = scene.graph[node]
            mesh = scene.geometry[geom].copy(); mesh.apply_transform(transform); found[sid] = mesh
    missing = set(STRUCTURES[kind]) - set(found)
    if missing: raise SystemExit('Not in the model: ' + ', '.join(sorted(missing)))
    return found


def outline(mesh, view):
    pts = VIEWS[view](mesh.vertices)
    tris = [Polygon(pts[f]) for f in mesh.faces]
    shape = unary_union([t for t in tris if t.is_valid and t.area > 1e-12]).simplify(0.0006)
    rings = []
    for poly in getattr(shape, 'geoms', [shape]):
        for ring in [poly.exterior, *poly.interiors]:
            if Polygon(ring).area > 2e-6: rings.append([[round(x, 5), round(y, 5)] for x, y in ring.coords])
    return rings


def rings_of(shape):
    rings = []
    for poly in getattr(shape, 'geoms', [shape]):
        for ring in [poly.exterior, *poly.interiors]:
            if Polygon(ring).area > 2e-6: rings.append([[round(x, 5), round(y, 5)] for x, y in ring.coords])
    return rings


def main():
    out = {view: {} for view in VIEWS}
    shapes = {view: [] for view in VIEWS}
    for kind in STRUCTURES:
        for sid, mesh in meshes(kind).items():
            for view in VIEWS:
                out[view][sid] = outline(mesh, view)
                if kind == 'muscular':  # thin, folded muscle sheets leave false holes; keep the outer outline only
                    out[view][sid] = [max(out[view][sid], key=lambda r: Polygon(r).area)]
                if 'left' not in sid: shapes[view].append(Polygon(out[view][sid][0]).buffer(0))
    # SKIN: a soft body outline around the right lower limb and pelvis, for surface-anatomy figures (schematic).
    for view in VIEWS:
        body = unary_union(shapes[view]).buffer(0.03, join_style=1).buffer(-0.012, join_style=1).simplify(0.001)
        out[view]['skin'] = rings_of(body)[:1]
    path = Path(__file__).with_name('outlines.json')
    path.write_text(json.dumps({'_note': __doc__.splitlines()[0], 'source': 'Z-Anatomy 1.4.0 via Vanatome (CC BY-SA 4.0)', **out}), encoding='utf-8')
    print('wrote', path.relative_to(ROOT))


if __name__ == '__main__':
    main()
