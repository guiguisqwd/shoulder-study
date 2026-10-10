#!/usr/bin/env python3
"""Hip figure kit: draws bones and muscles from outlines.json (projected from the 3D model) with the shared
hand-drawn Fig class from daily/engine/figlib, so library and daily figures look the same.

Coordinates: points are 3D model coordinates [x, y, z] (metres; x<0 = right side, y up, z anterior).
A Stage places one view of the model on the figure; stage.P(point3d) gives figure pixels."""
import json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'daily'))
from engine.figlib.fig import Fig, set_out, esc, RED, BLUE, INK, GREEN, PURP, GOLD, GREY, TEAL, ZH, BONE, BONE_E  # noqa: E402,F401

HERE = Path(__file__).resolve().parent
OUTLINES = json.loads((HERE / 'outlines.json').read_text(encoding='utf-8'))
CONTENT = json.loads((HERE.parents[1] / 'content.json').read_text(encoding='utf-8'))
COLOR = {m['id']: m.get('color', RED) for m in CONTENT.get('muscles', [])}
NERVE = '#c69014'  # AN-11: nerves gold
ORIGIN_C, INSERT_C = '#245e50', '#8c2f39'

BONES = {'hip-bone': 'skeleton-hip-bone-right', 'hip-bone-left': 'skeleton-hip-bone-left', 'sacrum': 'skeleton-sacrum',
         'coccyx': 'skeleton-coccyx', 'femur': 'appendicular-skeleton-femur-right', 'femur-left': 'appendicular-skeleton-femur-left',
         'tibia': 'appendicular-skeleton-tibia-right', 'fibula': 'appendicular-skeleton-fibula-right',
         'patella': 'appendicular-skeleton-patella-right', **{f'l{i}': f'skeleton-vertebra-l{i}' for i in range(1, 6)}}
MODEL_MUSCLES = {
    'gluteus-maximus': 'superficial-gluteal-muscles-gluteus-maximus-muscle-right',
    'gluteus-medius': 'superficial-gluteal-muscles-gluteus-medius-muscle-right',
    'gluteus-minimus': 'superficial-gluteal-muscles-gluteus-minimus-muscle-right',
    'tensor-fasciae-latae': 'superficial-gluteal-muscles-tensor-fasciae-latae-right',
    'piriformis': 'deep-gluteal-muscles-piriformis-muscle-right',
    'superior-gemellus': 'deep-gluteal-muscles-superior-gemellus-muscle-right',
    'obturator-internus': 'deep-gluteal-muscles-obturator-internus-right',
    'inferior-gemellus': 'deep-gluteal-muscles-inferior-gemellus-muscle-right',
    'quadratus-femoris': 'deep-gluteal-muscles-quadratus-femoris-muscle-right',
    'obturator-externus': 'deep-gluteal-muscles-obturator-externus-right'}

# Landmarks (3D, right side). Picked from the model meshes (see 制作记录.md); approximate teaching positions.
LM = {
    'iliac-crest': [-0.096, 1.012, -0.028], 'asis': [-0.118, 0.945, 0.056], 'aiis': [-0.111, 0.923, 0.036],
    'psis': [-0.046, 0.96, -0.087], 'ischial-tuberosity': [-0.045, 0.80, -0.034], 'pubic-tubercle': [-0.015, 0.849, 0.055],
    'greater-trochanter': [-0.147, 0.839, -0.008], 'femoral-head': [-0.075, 0.862, -0.004],
    'lesser-trochanter': [-0.088, 0.795, -0.027], 'adductor-tubercle': [-0.032, 0.468, -0.035],
    'gerdy': [-0.108, 0.405, 0.0], 'pes-anserinus': [-0.045, 0.385, -0.01], 'tibial-tuberosity': [-0.082, 0.39, 0.006],
    'fibular-head': [-0.11, 0.418, -0.047], 'medial-tibial-condyle-post': [-0.045, 0.405, -0.045],
    'sacrum-post': [-0.03, 0.92, -0.09], 'coccyx': [-0.01, 0.845, -0.08], 'ischial-spine': [-0.045, 0.855, -0.06],
}


def V(view, p):
    x, y, z = p
    return {'ant': (x, -y), 'post': (-x, -y), 'lat': (z, -y), 'med': (-z, -y)}[view]


class Stage:
    """One view of the model placed at figure (fx, fy) for model 2D point (mx, my), at `scale` px per metre."""
    def __init__(s, f, view, mx, my, fx, fy, scale):
        s.f, s.view, s.mx, s.my, s.fx, s.fy, s.k = f, view, mx, my, fx, fy, scale

    def P2(s, x, y): return (s.fx + (x - s.mx) * s.k, s.fy + (y - s.my) * s.k)
    def P(s, p): return s.P2(*V(s.view, p))
    def at(s, name): return s.P(LM[name])

    def d(s, rings):
        return ' '.join('M' + ' L'.join('%.1f,%.1f' % s.P2(*pt) for pt in ring) + 'Z' for ring in rings)

    def shape(s, sid, col, fill, w=1.6, op=None, dash=None, rough=True):
        rings = OUTLINES[s.view][sid]
        s.f.path(s.d(rings), col, w, fill, dash=dash, rough=rough, op=op, extra='fill-rule="evenodd"')

    def bones(s, names=('hip-bone', 'sacrum', 'coccyx', 'femur'), w=1.8, op=None):
        for n in names: s.shape(BONES[n], BONE_E, BONE, w, op=op)

    def muscle(s, mid, op=0.85, w=1.6, dash=None, fill=True):
        col = COLOR.get(mid, RED)
        s.shape(MODEL_MUSCLES[mid], col, tint(col) if fill else 'none', w, op=op, dash=dash)

    def skin(s, col='#b7ab95', fill='#f7efe2'):
        s.shape('skin', col, fill, 1.6, rough=False)

    def band(s, mid, origin, insertion, bow=None, op=0.85, w=1.6):
        """Schematic muscle for structures the model lacks: a smooth band from an origin line to an insertion line (3D points)."""
        col = COLOR.get(mid, RED)
        o = [s.P(p) for p in origin]; i = [s.P(p) for p in insertion]
        s.f.path(smooth_band(o, i, bow), col, w, tint(col), op=op)
        return o, i


def tint(hexcol, k=0.62):
    r, g, b = (int(hexcol[i:i + 2], 16) for i in (1, 3, 5))
    return '#%02x%02x%02x' % tuple(int(c + (255 - c) * k) for c in (r, g, b))


def smooth_band(o, i, bow=None):
    """Closed path: origin edge o[0]→o[-1], side to i[-1], insertion edge back to i[0], side to o[0].
    Sides bow away from the band's centre by `bow` px (default: a little more than the wider end)."""
    pts_all = o + i
    cx, cy = sum(p[0] for p in pts_all) / len(pts_all), sum(p[1] for p in pts_all) / len(pts_all)
    width = max(math.dist(o[0], o[-1]), math.dist(i[0], i[-1]))
    def ctrl(a, b):
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy) or 1
        nx, ny = -dy / n, dx / n
        k = bow if bow is not None else 0.3 * width + 4
        c1, c2 = (mx + nx * k, my + ny * k), (mx - nx * k, my - ny * k)
        return c1 if math.dist(c1, (cx, cy)) > math.dist(c2, (cx, cy)) else c2
    d = 'M%.1f,%.1f ' % o[0] + ' '.join('L%.1f,%.1f' % p for p in o[1:])
    d += ' Q%.1f,%.1f %.1f,%.1f' % (*ctrl(o[-1], i[-1]), *i[-1])
    d += ' ' + ' '.join('L%.1f,%.1f' % p for p in reversed(i[:-1]))
    d += ' Q%.1f,%.1f %.1f,%.1f Z' % (*ctrl(i[0], o[0]), *o[0])
    return d


def area(f, pts, col, label=None):
    """Attachment area (AN-14): dashed outline around the given figure points."""
    if len(pts) == 1:
        x, y = pts[0]; f.raw(f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="11" ry="8" fill="{col}" fill-opacity=".18" stroke="{col}" stroke-width="2" stroke-dasharray="5 4"/>')
    else:
        d = 'M' + ' L'.join('%.1f,%.1f' % p for p in pts)
        f.raw(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="9" stroke-opacity=".28" stroke-linecap="round" stroke-linejoin="round"/>')
        f.path(d, col, 2, dash='6 4', rough=False)


def oi(f, o_pts, i_pts, letter_o='O', letter_i='I', col=None):
    """Origin and insertion areas plus the dashed O→I attachment line (AN-13)."""
    area(f, o_pts, ORIGIN_C); area(f, i_pts, INSERT_C)
    oc = centroid(o_pts); ic = centroid(i_pts)
    f.raw(f'<path d="M{oc[0]:.1f},{oc[1]:.1f} L{ic[0]:.1f},{ic[1]:.1f}" stroke="#324c44" stroke-width="1.6" stroke-dasharray="7 5" fill="none"/>')
    oc, ic = free_spot(f, oc), free_spot(f, ic)
    tag(f, *oc, letter_o, ORIGIN_C); tag(f, *ic, letter_i, INSERT_C)
    return oc, ic


def free_spot(f, p, r=25):
    """Nudge a tag sideways so it does not sit on another tag of the same figure."""
    used = f.__dict__.setdefault('tags', [])
    cands = [p] + [(p[0] + dx * r, p[1] + dy * r * 0.8) for dx, dy in
                   [(1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1), (2, 0), (-2, 0), (0, 1.3), (0, -1.3)]]
    spot = next((c for c in cands if all(math.dist(c, q) >= r for q in used)), cands[-1])
    used.append(spot)
    return spot


def panel(f, view, center, at, K, bones, model=(), bands=(), attach=(), title=None, ghost=(), clip=None, labels=(), after=None):
    """One drawing panel. bands: (muscle id, origin 3D pts, insertion 3D pts); attach: (muscle id, origin 3D pts, insertion 3D pts).
    ghost: model muscles drawn as faint dashed outlines (for context). clip: (x, y, w, h) figure rectangle."""
    st = Stage(f, view, center[0], center[1], at[0], at[1], K)
    if clip:
        cid = f.id('clip' + str(len(f.p)))
        f.raw(f'<clipPath id="{cid}"><rect x="{clip[0]}" y="{clip[1]}" width="{clip[2]}" height="{clip[3]}"/></clipPath><g clip-path="url(#{cid})">')
    st.bones(bones)
    for mid in ghost: st.muscle(mid, op=0.5, w=1.2, dash='5 4', fill=False)
    for mid in model: st.muscle(mid)
    for b in bands: st.band(*b)
    if clip: f.end()
    for mid, o, i in attach:
        letter = next(m.get('letter', '') for m in CONTENT['muscles'] if m['id'] == mid)
        oi(f, [st.P(p) for p in o], [st.P(p) for p in i], letter, letter)
    for en, zh, pt, x, y, *anchor in labels:
        label(f, x, y, en, zh, GREY, anchor[0] if anchor else 'start', 13, to=st.P(pt) if len(pt) == 3 else pt)
    if after: after(f, st)
    if title: f.bi(at[0], title[2], title[0], title[1], 17, INK, 'middle', '700')
    return st


def centroid(pts): return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def tag(f, x, y, txt, col, r=12):
    f.circle(x, y, r, col, '#fff', 2); f.text(x, y + 4.5, txt, 13 if len(txt) < 3 else 10, '#fff', 'middle', '700')


def label(f, x, y, en, zh, col=INK, anchor='start', size=15, to=None):
    """Bilingual label; optional leader line to the point `to`."""
    if to:
        w = text_width(en, zh, size)
        left = x - w if anchor == 'end' else (x - w / 2 if anchor == 'middle' else x)
        if to[0] < left: lx = left - 6
        elif to[0] > left + w: lx = left + w + 6
        else: lx = to[0]
        ly = y - 5 if lx != to[0] else (y + size + 10 if to[1] > y else y - size - 2)
        f.leader(lx, ly, to[0], to[1], col)
        f.circle(to[0], to[1], 3.2, col, '#fff', 1)
    f.bi(x, y, en, zh, size, col, anchor, '600')


def text_width(en, zh, size=15):
    """Rough rendered width of a bilingual label (Arial / PingFang)."""
    wide = sum(1 for ch in en if ch.isupper() or ch in 'mwMW')
    return max(len(en) * size * 0.53 + wide * size * 0.12, len(zh) * (size - 2) * 1.0)


def name_of(mid): return next(m['name'] for m in CONTENT['muscles'] if m['id'] == mid)


def legend_oi(f, x, y, rows):
    """rows: [(muscle id, origin en, origin zh, insertion en, insertion zh)] → stacked bilingual O/I legend.
    The texts are the short figure labels; diagrams in content.json repeat them as Origin:/Insertion: labels."""
    yy = y
    for mid, oen, ozh, ien, izh in rows:
        col = COLOR.get(mid, RED)
        name = name_of(mid)
        letter = next(m.get('letter', '') for m in CONTENT['muscles'] if m['id'] == mid)
        tag(f, x + 12, yy - 6, letter, col, 13)
        f.bi(x + 32, yy, name['en'], name['zh'], 16, col, 'start', '700')
        f.bi(x + 32, yy + 40, 'Origin: ' + oen, '起点：' + ozh, 13, ORIGIN_C, 'start', '600')
        f.bi(x + 32, yy + 76, 'Insertion: ' + ien, '止点：' + izh, 13, INSERT_C, 'start', '600')
        yy += 118
    return yy


def key_oi(f, x, y):
    """Small key: green dashed = origin, red dashed = insertion, dashed line = O→I attachment order (AN-13)."""
    area(f, [(x, y), (x + 34, y)], ORIGIN_C); f.bi(x + 46, y + 4, 'Origin area', '起点区', 13, ORIGIN_C, 'start', '600')
    area(f, [(x + 170, y), (x + 204, y)], INSERT_C); f.bi(x + 216, y + 4, 'Insertion area', '止点区', 13, INSERT_C, 'start', '600')
    f.raw(f'<path d="M{x + 350},{y} L{x + 400},{y}" stroke="#324c44" stroke-width="1.6" stroke-dasharray="7 5"/>')
    f.bi(x + 410, y + 4, 'Origin → insertion', '起点 → 止点', 13, INK, 'start', '600')


def note(f, x, y, lines_en, lines_zh, col=GREY, size=13):
    for k, (en, zh) in enumerate(zip(lines_en, lines_zh)):
        f.bi(x, y + k * (2 * size + 12), en, zh, size, col, 'start', '400')
