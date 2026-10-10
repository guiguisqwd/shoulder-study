#!/usr/bin/env python3
"""Hip nerve figures: 11 (lumbar and sacral plexus flow chart, supplementary to the anatomical figures, AN-12)
and 18 (nerve injuries around the hip: approximate skin areas on the model's body outline + motor / gait signs).
Registered by build-figures.py through register(fig)."""
import math
from hipfig import (Fig, Stage, OUTLINES, COLOR, NERVE, INK, GREY, ZH, BONE_E, CONTENT, esc, text_width)

NERVE_DARK = '#8a6208'


def name_of(mid):
    return next(m['name'] for m in CONTENT['muscles'] if m['id'] == mid)


def wrap(s, width, size, zh=False):
    """Greedy wrap to `width` px (rough Arial / PingFang widths)."""
    if zh:
        import re
        toks = re.findall(r'[A-Za-z0-9–\-\.]+ ?|.', s)
        cw = lambda t: sum(size * (0.56 if ord(c) < 0x2000 else 1.0) for c in t)
        out, cur = [], ''
        for t in toks:
            if cur and cw(cur + t) > width and t not in '，。；：、）':
                out.append(cur); cur = t.lstrip()
            else:
                cur += t
        return out + ([cur] if cur else [])
    out, cur = [], ''
    for w in s.split(' '):
        t = (cur + ' ' + w).strip()
        if cur and len(t) * size * 0.5 > width:
            out.append(cur); cur = w
        else:
            cur = t
    return out + ([cur] if cur else [])


def lines(f, x, y, items, size=13, lh=17, anchor='start'):
    """items: [(text, colour, weight, lang)] drawn one per line; returns y after the last line."""
    for txt, col, wt, lang in items:
        f.text(x, y, txt, size, col, anchor, wt, lang)
        y += lh
    return y


# ---------------------------------------------------------------- figure 11: plexus flow chart
ROOTS = ['T12', 'L1', 'L2', 'L3', 'L4', 'L5', 'S1', 'S2', 'S3']
ROOT_ZH = {'T12': '胸 12', 'L1': '腰 1', 'L2': '腰 2', 'L3': '腰 3', 'L4': '腰 4', 'L5': '腰 5', 'S1': '骶 1', 'S2': '骶 2', 'S3': '骶 3'}

# (key, plexus, name en, name zh, segments + division en, zh, [(muscle id, en suffix, zh suffix)], extra grey chips)
BRANCHES = [
    ('direct', 'L', 'Direct branches', '直接分支', 'L1–L3', 'L1–L3', [('psoas-major', '', '')], []),
    ('femoral', 'L', 'Femoral nerve', '股神经', 'L2–L4 · posterior divisions', 'L2–L4 · 后股',
     [('iliacus', '', ''), ('sartorius', '', ''), ('rectus-femoris', '', ''), ('pectineus', '', '')], [('Vasti (knee)', '股内/外/中间肌（膝）')]),
    ('obturator', 'L', 'Obturator nerve', '闭孔神经', 'L2–L4 · anterior divisions', 'L2–L4 · 前股',
     [('adductor-longus', '', ''), ('adductor-brevis', '', ''), ('gracilis', '', ''), ('obturator-externus', '', ''),
      ('adductor-magnus', ' (adductor part)', '（收肌部）'), ('pectineus', ' (sometimes)', '（有时）')], []),
    ('lfcn', 'L', 'Lateral femoral cutaneous n.', '股外侧皮神经', 'L2–L3 · sensory only', 'L2–L3 · 纯感觉', [],
     [('No muscles: skin of lateral thigh', '不支配肌肉：大腿外侧皮肤')]),
    ('supglut', 'S', 'Superior gluteal nerve', '臀上神经', 'L4–S1 · posterior divisions', 'L4–S1 · 后股',
     [('gluteus-medius', '', ''), ('gluteus-minimus', '', ''), ('tensor-fasciae-latae', '', '')], []),
    ('infglut', 'S', 'Inferior gluteal nerve', '臀下神经', 'L5–S2 · posterior divisions', 'L5–S2 · 后股', [('gluteus-maximus', '', '')], []),
    ('pir', 'S', 'Nerve to piriformis', '梨状肌神经', 'S1–S2', 'S1–S2', [('piriformis', '', '')], []),
    ('oi', 'S', 'Nerve to obturator internus', '闭孔内肌神经', 'L5–S2 · anterior divisions', 'L5–S2 · 前股',
     [('obturator-internus', '', ''), ('superior-gemellus', '', '')], []),
    ('qf', 'S', 'Nerve to quadratus femoris', '股方肌神经', 'L4–S1 · anterior divisions', 'L4–S1 · 前股',
     [('quadratus-femoris', '', ''), ('inferior-gemellus', '', '')], []),
    ('tib', 'S', 'Tibial division', '胫神经部', 'anterior divisions', '前股',
     [('semitendinosus', '', ''), ('semimembranosus', '', ''), ('biceps-femoris', ' (long head)', '（长头）'),
      ('adductor-magnus', ' (hamstring part)', '（腘绳肌部）')], []),
    ('cf', 'S', 'Common fibular division', '腓总神经部', 'posterior divisions', '后股', [('biceps-femoris', ' (short head)', '（短头）')], []),
]


def flow_chart():
    W, H = 1600, 1440
    f = Fig('11', W, H, 'Lumbar and sacral plexuses: roots to hip nerves (supplementary flow chart)',
            '腰丛与骶丛：从神经根到髋部神经（补充流程图）')
    # column headers
    hy = 140
    for x, en, zh in [(40, 'Spinal nerves', '脊神经'), (240, 'Plexus', '神经丛'),
                      (520, 'Nerve and root levels', '神经与节段'), (1030, 'Muscles supplied in this chapter', '本章所支配的肌肉')]:
        f.bi(x, hy, en, zh, 16, INK, 'start', '700', zsize=14)
    f.bi(800, hy, 'Sciatic nerve divisions', '坐骨神经分部', 16, INK, 'start', '700', zsize=14)

    # branch rows: chips laid out first to know each row's height
    CHX, CHW = 1030, 1570
    rows, y = [], 210
    for b in BRANCHES:
        key, plx, en, zh, seg_en, seg_zh, mus, extra = b
        chips = [(name_of(m)['en'] + se, name_of(m)['zh'] + sz, COLOR[m]) for m, se, sz in mus] + [(e, z, GREY) for e, z in extra]
        placed, cx, line = [], CHX, 0
        for cen, czh, col in chips:
            w = text_width(cen, czh, 14) + 26
            if cx + w > CHW and cx > CHX:
                line += 1; cx = CHX
            placed.append((cx, line, cen, czh, col)); cx += w
        nl = line + 1
        h = max(88, nl * 44 + 22)
        rows.append(dict(b=b, y=y, h=h, chips=placed))
        y += h + (14 if key != 'lfcn' else 40)
    bottom = y

    # root boxes
    lum = [r for r in rows if r['b'][1] == 'L']; sac = [r for r in rows if r['b'][1] == 'S']
    lum_top, lum_bot = lum[0]['y'], lum[-1]['y'] + lum[-1]['h']
    sac_top, sac_bot = sac[0]['y'], sac[-1]['y'] + sac[-1]['h']
    ry = {}
    for i, r in enumerate(['T12', 'L1', 'L2', 'L3', 'L4']):
        ry[r] = lum_top + 30 + i * (lum_bot - lum_top - 60) / 4
    ry['L5'] = sac_top + 50
    for i, r in enumerate(['S1', 'S2', 'S3']):
        ry[r] = sac_top + 190 + i * 110
    for r in ROOTS:
        f.box(40, ry[r] - 22, 118, 46, NERVE, '#fdf6e3')
        f.bi(99, ry[r] - 3, r + ' nerve', ROOT_ZH[r] + ' 神经', 15, NERVE_DARK, 'middle', '700', zsize=13, gap=18)

    # plexus boxes
    LPX, LPW = 240, 170
    lp = (LPX, lum_top + 4, LPW, lum_bot - lum_top - 8)
    f.box(*lp, NERVE, '#fbefd0', sw=2.2)
    f.bi(LPX + LPW / 2, lp[1] + lp[3] / 2 - 18, 'Lumbar plexus', '腰丛', 17, NERVE_DARK, 'middle', '700', zsize=15)
    f.bi(LPX + LPW / 2, lp[1] + lp[3] / 2 + 26, 'Roots (T12) L1–L4', '来源：（T12）L1–L4', 14, NERVE_DARK, 'middle', '600', zsize=13)
    lst = (LPX, ry['L5'] - 34, LPW, 68)
    f.box(*lst, NERVE, '#fdf6e3', dash='6 4', sw=2)
    f.bi(LPX + LPW / 2, ry['L5'] - 8, 'Lumbosacral trunk', '腰骶干（L4–L5）', 14, NERVE_DARK, 'middle', '700', zsize=13)
    sp = (LPX, ry['L5'] + 70, LPW, sac_bot - ry['L5'] - 74)
    f.box(*sp, NERVE, '#fbefd0', sw=2.2)
    f.bi(LPX + LPW / 2, sp[1] + sp[3] / 2 - 18, 'Sacral plexus', '骶丛', 17, NERVE_DARK, 'middle', '700', zsize=15)
    f.bi(LPX + LPW / 2, sp[1] + sp[3] / 2 + 26, 'Roots L4–S3 (S4)', '来源：L4–S3（S4）', 14, NERVE_DARK, 'middle', '600', zsize=13)

    # root → plexus
    for r in ['T12', 'L1', 'L2', 'L3', 'L4']:
        f.arrow(f'M158,{ry[r]:.1f} L{LPX - 4},{ry[r]:.1f}', NERVE, 2.2)
    # L4 also joins L5 as the lumbosacral trunk
    f.arrow(f'M190,{ry["L4"]:.1f} C215,{ry["L4"] + 30:.1f} 215,{ry["L5"] - 40:.1f} {LPX - 4},{ry["L5"] - 10:.1f}', NERVE, 2.2)
    f.raw(f'<circle cx="190" cy="{ry["L4"]:.1f}" r="3.5" fill="{NERVE}"/>')
    f.arrow(f'M158,{ry["L5"] + 12:.1f} L{LPX - 4},{ry["L5"] + 12:.1f}', NERVE, 2.2)
    f.arrow(f'M{LPX + LPW / 2},{ry["L5"] + 34:.1f} L{LPX + LPW / 2},{sp[1] - 4:.1f}', NERVE, 2.4)
    for r in ['S1', 'S2', 'S3']:
        f.arrow(f'M158,{ry[r]:.1f} L{LPX - 4},{ry[r]:.1f}', NERVE, 2.2)

    # nerve boxes, plexus → nerve curves, nerve → muscles
    BX, BW = 520, 250
    sci = [r for r in rows if r['b'][0] in ('tib', 'cf')]
    sci_y0, sci_y1 = sci[0]['y'], sci[-1]['y'] + sci[-1]['h']
    for r in rows:
        key, plx, en, zh, seg_en, seg_zh, mus, extra = r['b']
        cy = r['y'] + r['h'] / 2
        src = lp if plx == 'L' else sp
        sx = src[0] + src[2]
        sy = min(max(cy, src[1] + 12), src[1] + src[3] - 12)
        if key in ('tib', 'cf'):
            dx, col = 800, NERVE
            f.box(dx, r['y'], 200, r['h'], NERVE, '#fdf6e3')
            lines(f, dx + 12, r['y'] + 22, [(en, NERVE_DARK, '700', 'en'), (zh, ZH, '400', 'zh-CN'),
                                              (seg_en, NERVE_DARK, '400', 'en'), (seg_zh, ZH, '400', 'zh-CN')], 13, 17)
            f.arrow(f'M{BX + BW},{cy:.1f} L{dx - 4},{cy:.1f}', NERVE, 2)
            start = dx + 200
        else:
            f.box(BX, r['y'], BW, r['h'], NERVE, '#fdf6e3')
            items = [(en, NERVE_DARK, '700', 'en'), (zh, ZH, '400', 'zh-CN'), (seg_en, NERVE_DARK, '400', 'en')]
            if seg_zh != seg_en: items.append((seg_zh, ZH, '400', 'zh-CN'))
            lines(f, BX + 12, r['y'] + 22, items, 14 if len(en) < 26 else 13, 17)
            f.path(f'M{sx},{sy:.1f} C{sx + 60},{sy:.1f} {BX - 60},{cy:.1f} {BX - 4},{cy:.1f}', NERVE, 2.2, rough=False)
            start = BX + BW
        # chips
        for cx, line, cen, czh, col in r['chips']:
            f.bi(cx, r['y'] + 26 + line * 44, cen, czh, 14, col, 'start', '700', zcol=col, zsize=13, gap=18)
        if r['chips']:
            f.arrow(f'M{start + 2},{cy:.1f} L{CHX - 8},{cy:.1f}', NERVE, 2)
    # sciatic nerve box spanning its two divisions
    f.box(BX, sci_y0, BW, sci_y1 - sci_y0, NERVE, '#fbefd0', sw=2.2)
    scy = (sci_y0 + sci_y1) / 2
    lines(f, BX + 12, scy - 22, [('Sciatic nerve', NERVE_DARK, '700', 'en'), ('坐骨神经', ZH, '400', 'zh-CN'),
                                  ('L4–S3', NERVE_DARK, '400', 'en'), ('two divisions in one sheath', NERVE_DARK, '400', 'en'),
                                  ('一个鞘内含两部', ZH, '400', 'zh-CN')], 14, 18)
    f.path(f'M{sp[0] + sp[2]},{scy:.1f} C{sp[0] + sp[2] + 50},{scy:.1f} {BX - 50},{scy:.1f} {BX - 4},{scy:.1f}', NERVE, 2.2, rough=False)

    # AN-04 box (bottom left, below the sacral plexus)
    bx, by, bw = 40, bottom + 6, 700
    en = ('T12, L1–L5 and S1–S3 here are spinal nerve levels (T = thoracic, L = lumbar, S = sacral): the spinal nerves '
          'that give fibres to each plexus, not vertebrae. "L4 vertebra" is a bone; "L2–L4" in a nerve supply means '
          'the L2, L3 and L4 spinal nerves.')
    zh = ('这里的 T12、L1–L5、S1–S3 指脊神经节段（T = 胸，L = 腰，S = 骶），即向神经丛提供纤维的脊神经，不是椎骨。'
          '“第 4 腰椎”是骨；神经支配中的“L2–L4”指 L2、L3、L4 脊神经。')
    el, zl = wrap(en, bw - 36, 14), wrap(zh, bw - 36, 14, zh=True)
    bh = 50 + 19 * (len(el) + len(zl)) + 8
    f.box(bx, by, bw, bh, INK, '#f4efe2')
    f.text(bx + 18, by + 28, 'Nerve levels, not vertebrae  ·  神经节段，不是椎骨', 15, INK, 'start', '700')
    yy = lines(f, bx + 18, by + 54, [(t, INK, '400', 'en') for t in el], 14, 19)
    lines(f, bx + 18, yy + 2, [(t, ZH, '400', 'zh-CN') for t in zl], 14, 19)
    # supplementary note (right)
    nx = 780
    nen = wrap('Supplementary flow chart (AN-12): the nerves themselves are drawn on the anatomy in the chapter\'s '
               'nerve figures. Root levels are typical and vary between people.', 780, 14)
    nzh = wrap('补充流程图（AN-12）：神经本身画在本章解剖神经图上。节段为常见情况，个体间有差异。', 780, 14, zh=True)
    yy = lines(f, nx, by + 28, [(t, GREY, '400', 'en') for t in nen], 14, 19)
    lines(f, nx, yy + 2, [(t, ZH, '400', 'zh-CN') for t in nzh], 14, 19)
    f.h = int(by + bh + 80)
    f.save('腰丛与骶丛')
    return f


# ---------------------------------------------------------------- figure 18: nerve injuries
AREA = {'lfcn': '#e07b39', 'fem': '#3f74b5', 'obt': '#2a9d8f', 'pfcn': '#8e5ea2', 'sci': '#b03a48'}


def span(view, Y):
    """Skin outline crossings (view 2D x) at model height Y: (min, max)."""
    r = OUTLINES[view]['skin'][0]
    Y = min(max(Y, 0.045), 1.14)
    xs = []
    for i in range(len(r)):
        a, b = r[i], r[(i + 1) % len(r)]
        if (a[1] + Y) * (b[1] + Y) < 0:
            t = (-Y - a[1]) / (b[1] - a[1]); xs.append(a[0] + t * (b[0] - a[0]))
    return min(xs), max(xs)


def region(st, left, right, y0, y1, n=24):
    """Closed path between two boundary functions of Y (view 2D x), from Y=y0 down to y1."""
    ys = [y0 + (y1 - y0) * k / n for k in range(n + 1)]
    pts = [(left(Y), -Y) for Y in ys] + [(right(Y), -Y) for Y in reversed(ys)]
    return 'M' + ' L'.join('%.1f,%.1f' % st.P2(*p) for p in pts) + 'Z'


def shade(f, st, d, col, clip, clip2=None):
    if clip2: f.raw(f'<g clip-path="url(#{clip2})">')
    f.raw(f'<path d="{d}" fill="{col}" fill-opacity=".36" stroke="{col}" stroke-width="1.6" stroke-opacity=".8" '
          f'stroke-dasharray="5 3" clip-path="url(#{clip})"/>')
    if clip2: f.end()


def mlabel(f, x, y, en_lines, zh_lines, col, anchor, to, size=14):
    """Multi-line bilingual label with a leader from its nearest side to `to`."""
    w = max([text_width(t, '', size) for t in en_lines] + [len(t) * (size - 1) for t in zh_lines])
    left = x - w if anchor == 'end' else x
    n = len(en_lines) + len(zh_lines)
    mid = y - size * 0.35 + (n - 1) * (size + 3) / 2
    lx = left - 6 if to[0] < left else left + w + 6
    f.leader(lx, mid, to[0], to[1], col)
    f.circle(to[0], to[1], 3.4, col, '#fff', 1.2)
    yy = y
    for t in en_lines:
        f.text(x, yy, t, size, col, anchor, '700', 'en'); yy += size + 3
    for t in zh_lines:
        f.text(x, yy, t, size - 1, ZH, anchor, '400', 'zh-CN'); yy += size + 3


CARDS = {
    'femoral-nerve': ('Femoral nerve (L2–L4)', '股神经（L2–L4）', 'fem',
                      ('Anterior and medial thigh; medial leg and foot (saphenous).', '大腿前内侧；小腿和足内侧（隐神经）。'),
                      ('Weak knee extension; hip flexion also weak if above the inguinal ligament.', '伸膝无力；病变在腹股沟韧带以上时屈髋也无力。'),
                      ('Knee buckles in stance; patellar reflex reduced or absent.', '支撑期膝打软；膝反射减弱或消失。')),
    'obturator-nerve': ('Obturator nerve (L2–L4)', '闭孔神经（L2–L4）', 'obt',
                        ('Patch on the middle of the medial thigh.', '大腿内侧中部一小片皮肤。'),
                        ('Weak hip adduction.', '髋内收无力。'),
                        ('Unstable leg; circumducting gait with the hip externally rotated.', '下肢不稳；髋外旋的划圈步态。')),
    'lateral-femoral-cutaneous-nerve': ('Lateral femoral cutaneous n. (L2–L3)', '股外侧皮神经（L2–L3）', 'lfcn',
                                        ('Burning, numb oval, anterolateral thigh (meralgia paresthetica).', '大腿前外侧椭圆区烧灼、麻木（感觉异常性股痛）。'),
                                        ('None: purely sensory; weakness points to another diagnosis.', '无：纯感觉神经；如有无力应考虑其他诊断。'),
                                        ('Normal; long standing or walking with the hip extended may worsen it.', '正常；久站或伸髋行走可加重症状。')),
    'superior-gluteal-nerve': ('Superior gluteal nerve (L4–S1)', '臀上神经（L4–S1）', None,
                               ('No skin area: sensation normal.', '无皮肤感觉区：感觉正常。'),
                               ('Weak hip abduction and internal rotation (gluteus medius, minimus, TFL).', '髋外展、内旋无力（臀中肌、臀小肌、阔筋膜张肌）。'),
                               ('Pelvis drops on the swing side: positive Trendelenburg sign and gait.', '摆动侧骨盆下沉：Trendelenburg 征阳性及其步态。')),
    'inferior-gluteal-nerve': ('Inferior gluteal nerve (L5–S2)', '臀下神经（L5–S2）', None,
                               ('No skin area of its own: sensation usually normal.', '无自己的皮肤感觉区：感觉通常正常。'),
                               ('Weak hip extension (supplies gluteus maximus only).', '伸髋无力（只支配臀大肌）。'),
                               ('Trunk lurches back at heel strike; stairs and rising from a chair are hard.', '足跟着地时躯干后倾；上楼和从椅子站起困难。')),
    'sciatic-nerve': ('Sciatic nerve (L4–S3)', '坐骨神经（L4–S3）', 'sci',
                      ('Most of the leg below the knee and the foot, sparing the medial leg.', '膝以下小腿大部分和足部，小腿内侧除外。'),
                      ('Weak knee flexion and all ankle and foot movement.', '屈膝及踝、足全部运动无力。'),
                      ('Foot drop → steppage gait (hip and knee lifted high); ankle jerk may drop.', '足下垂 → 跨阈步态（高抬髋膝）；跟腱反射可减弱。')),
}


def card(f, x, y, w, nid):
    en, zh, area, skin, motor, gait = CARDS[nid]
    pad, tw = 14, w - 28
    body = []
    for head_en, head_zh, (ten, tzh) in [('Skin', '感觉', skin), ('Motor', '运动', motor), ('Gait', '步态', gait)]:
        el = wrap(f'{head_en}: {ten}', tw, 13)
        zl = wrap(f'{head_zh}：{tzh}', tw, 13, zh=True)
        if len(el) > 2 or len(zl) > 2: print('LONG', nid, el, zl)
        body.append((el, zl))
    h = 50 + sum(17 * (len(a) + len(b)) + 8 for a, b in body) + 4
    f.box(x, y, w, h, NERVE, '#fffdf7')
    if area:
        f.raw(f'<rect x="{x + w - 34}" y="{y + 12}" width="20" height="20" rx="4" fill="{AREA[area]}" fill-opacity=".45" '
              f'stroke="{AREA[area]}" stroke-width="1.6" stroke-dasharray="5 3"/>')
    else:
        f.raw(f'<rect x="{x + w - 34}" y="{y + 12}" width="20" height="20" rx="4" fill="none" stroke="{GREY}" stroke-width="1.4"/>')
    f.text(x + pad, y + 24, en, 14, NERVE_DARK, 'start', '700')
    f.text(x + pad, y + 42, zh, 13, ZH, 'start', '400', 'zh-CN')
    yy = y + 64
    for el, zl in body:
        for i, t in enumerate(el + zl):
            col, lang = (INK, 'en') if i < len(el) else (ZH, 'zh-CN')
            if i in (0, len(el)):
                k = t.index(':' if i == 0 else '：') + 1
                f.raw(f'<text x="{x + pad}" y="{yy}" font-size="13" fill="{col}" lang="{lang}"><tspan font-weight="700">{esc(t[:k])}</tspan>{esc(t[k:])}</text>')
            else:
                f.text(x + pad, yy, t, 13, col, 'start', '400', lang)
            yy += 17
        yy += 8
    return y + h


def injuries():
    W, H, K = 1600, 1330, 880
    f = Fig('18', W, H, 'Nerve injuries around the hip: sensory areas and motor signs', '髋部神经损伤：感觉区与运动表现')
    FY, MY = 700, -0.6
    a = Stage(f, 'ant', -0.10, MY, 560, FY, K)
    p = Stage(f, 'post', 0.10, MY, 1040, FY, K)
    for st, cid in ((a, 'skA'), (p, 'skP')):
        f.raw(f'<clipPath id="{f.id(cid)}"><path d="{st.d(OUTLINES[st.view]["skin"])}"/></clipPath>')
        st.skin()
        st.bones(('hip-bone', 'sacrum', 'coccyx', 'femur', 'tibia', 'fibula', 'patella'), w=1.2, op=0.3)
    cA, cP = f.id('skA'), f.id('skP')

    # ---- anterior view areas (view x = model x; lateral = min)
    lat = lambda Y: span('ant', Y)[0]
    med = lambda Y: span('ant', Y)[1] if Y < 0.76 else -0.06
    lf_in = lambda Y: lat(Y) + 0.072 * (0.08 + 0.44 * math.sin(math.pi * min(max((0.885 - Y) / 0.39, 0), 1)) ** 0.7)
    out = lambda d: (lambda Y: d)
    # femoral (anterior cutaneous) — anterior thigh, medial of the LFCN oval
    ing = [a.P2(x, -y) for x, y in [(-0.25, 0.86), (-0.13, 0.86), (-0.02, 0.775), (0.2, 0.775), (0.2, 0.0), (-0.25, 0.0)]]
    f.raw(f'<clipPath id="{f.id("ing")}"><path d="M' + ' L'.join('%.1f,%.1f' % q for q in ing) + 'Z"/></clipPath>')
    shade(f, a, region(a, lambda Y: lf_in(Y) if Y > 0.5 else lat(Y) + 0.01, lambda Y: med(Y) + 0.02, 0.88, 0.455), AREA['fem'], cA, f.id('ing'))
    # saphenous — medial leg and foot
    sa_in = lambda Y: med(Y) - 0.32 * (med(Y) - lat(Y)) if Y > 0.07 else -0.105
    shade(f, a, region(a, sa_in, lambda Y: med(Y) + 0.02, 0.44, 0.0), AREA['fem'], cA)
    # sciatic territory — rest of the leg below the knee
    shade(f, a, region(a, lambda Y: lat(Y) - 0.03, sa_in, 0.425, 0.0), AREA['sci'], cA)
    # LFCN oval
    shade(f, a, region(a, lambda Y: lat(Y) - 0.03, lf_in, 0.885, 0.495), AREA['lfcn'], cA)
    # obturator patch, medial mid-thigh
    shade(f, a, region(a, lambda Y: med(Y) - 0.016, lambda Y: med(Y) + 0.02, 0.70, 0.56), AREA['obt'], cA)
    a.skin(fill='none')

    # ---- posterior view areas (view x = -model x; lateral = max)
    plat = lambda Y: span('post', Y)[1]
    pmed = lambda Y: span('post', Y)[0] if Y < 0.76 else 0.0
    shade(f, p, region(p, lambda Y: pmed(Y) - 0.02, lambda Y: plat(Y) + 0.03, 0.845, 0.37), AREA['pfcn'], cP)
    ps_in = lambda Y: pmed(Y) + 0.22 * (plat(Y) - pmed(Y)) if Y > 0.07 else 0.09
    shade(f, p, region(p, lambda Y: pmed(Y) - 0.02, ps_in, 0.37, 0.0), AREA['fem'], cP)
    shade(f, p, region(p, ps_in, lambda Y: plat(Y) + 0.03, 0.37, 0.0), AREA['sci'], cP)
    for mid in ('gluteus-medius', 'gluteus-maximus'):
        p.muscle(mid, op=0.75, w=1.4, dash='6 4', fill=False)
    p.skin(fill='none')

    # panel titles
    f.bi(560, 150, 'Anterior view (right lower limb)', '前面观（右下肢）', 17, INK, 'middle', '700', zsize=15)
    f.bi(1040, 150, 'Posterior view', '后面观', 17, INK, 'middle', '700', zsize=15)

    # labels — anterior view: lateral on the left, medial in the middle gap
    A2 = lambda x, y: a.P2(x, -y)
    P2 = lambda x, y: p.P2(x, -y)
    mlabel(f, 488, 470, ['Lateral femoral', 'cutaneous n.'], ['股外侧皮神经'], AREA['lfcn'], 'end', A2(lat(0.70) + 0.012, 0.70))
    mlabel(f, 488, 940, ['Sciatic n.', '(tibial and', 'fibular branches)'], ['坐骨神经', '（胫、腓神经分支）'], AREA['sci'], 'end', A2(-0.115, 0.26))
    mlabel(f, 640, 560, ['Femoral n.:', 'anterior cutaneous', 'branches'], ['股神经前皮支'], AREA['fem'], 'start', A2(-0.104, 0.75))
    mlabel(f, 640, 700, ['Obturator n.'], ['闭孔神经'], AREA['obt'], 'start', A2(med(0.63) - 0.006, 0.63))
    mlabel(f, 640, 860, ['Saphenous n.', '(femoral)'], ['隐神经（股神经）'], AREA['fem'], 'start', A2(-0.068, 0.28))
    # posterior view: lateral on the right
    mlabel(f, 1112, 640, ['Posterior', 'femoral', 'cutaneous n.'], ['股后皮神经'], AREA['pfcn'], 'start', P2(0.112, 0.62))
    mlabel(f, 1112, 960, ['Sciatic n.'], ['坐骨神经'], AREA['sci'], 'start', P2(0.112, 0.22))
    mlabel(f, 900, 1040, ['Saphenous n.'], ['隐神经'], AREA['fem'], 'end', P2(ps_in(0.16) - 0.008, 0.16))
    gmx = COLOR['gluteus-maximus']; gmd = COLOR['gluteus-medius']
    mlabel(f, 1112, 300, ['Gluteus medius'], ['臀中肌'], gmd, 'start', P2(0.13, 0.95))
    mlabel(f, 1112, 400, ['Gluteus maximus'], ['臀大肌'], gmx, 'start', P2(0.15, 0.86))

    # cards beside each view
    CW = 300
    y = 210
    for nid in ('lateral-femoral-cutaneous-nerve', 'femoral-nerve', 'obturator-nerve'):
        y = card(f, 30, y, CW, nid) + 18
    y = 210
    for nid in ('superior-gluteal-nerve', 'inferior-gluteal-nerve', 'sciatic-nerve'):
        y = card(f, W - 30 - CW, y, CW, nid) + 18

    # note
    ny = 1250
    f.text(38, ny, 'Shaded skin areas are approximate: borders overlap and vary between people. '
                   'The superior and inferior gluteal nerves have no skin area (outlined muscles show what they supply).', 14, GREY)
    f.text(38, ny + 20, '阴影皮肤区为大致范围：边界相互重叠，个体间有差异。臀上、臀下神经没有皮肤感觉区（虚线轮廓为其支配的肌肉）。', 14, ZH, lang='zh-CN')
    f.save('髋部神经损伤的感觉区与运动表现')
    return f


def register(fig):
    fig('11')(flow_chart)
    fig('18')(injuries)
