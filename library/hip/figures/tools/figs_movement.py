#!/usr/bin/env python3
"""Hip movement figures 15–17 (single-leg stance lever, lumbopelvic rhythm, gait muscle timeline).
Numbers and texts come from the sourced movement research (chapter 03-movement); no unsourced values.
Registered by build-figures.py through register(fig)."""
import math
from hipfig import (Fig, Stage, COLOR, LM, INK, GREY, RED, BLUE, ZH, BONE, BONE_E, GOLD, label, esc)

W_COL = '#3d4f63'        # body-weight vector
JRF_COL = '#7a5aa6'      # joint reaction force (text only)
LUMB = '#365e91'         # lumbar flexion
HIPC = '#c0603a'         # hip flexion / pelvic tilt


def tw(s, size):
    """Rough text width (Arial / PingFang)."""
    w = 0.0
    for ch in s:
        if ord(ch) > 0x2e80: w += size * 1.0
        elif ch in 'mwMW@': w += size * 0.83
        elif ch.isupper(): w += size * 0.66
        elif ch in 'il.,;:!|\'()[] ': w += size * 0.28
        else: w += size * 0.53
    return w


def wrap(s, size, width):
    lines, cur = [], ''
    cjk = any(ord(c) > 0x2e80 for c in s)
    tokens = list(s) if cjk else s.split(' ')
    sep = '' if cjk else ' '
    for t in tokens:
        nxt = (cur + sep + t) if cur else t
        if tw(nxt, size) > width and cur:
            lines.append(cur); cur = t.lstrip() if cjk else t
        else:
            cur = nxt
    if cur: lines.append(cur)
    return lines


def para(f, x, y, s, size, width, col=INK, weight='400', lead=None, anchor='start'):
    """Wrapped single-language paragraph; returns the y of the next line."""
    lead = lead or size + 5
    for ln in wrap(s, size, width):
        f.text(x, y, ln, size, col, anchor, weight, 'zh-CN' if any(ord(c) > 0x2e80 for c in ln) else 'en')
        y += lead
    return y


def bipara(f, x, y, en, zh, size, width, col=INK, weight='400', gap=4, anchor='start'):
    y = para(f, x, y, en, size, width, col, weight, anchor=anchor)
    return para(f, x, y + gap - 5 + 5, zh, size, width, ZH, '400', anchor=anchor)


def dim(f, x1, x2, y, col, w=2):
    """Horizontal dimension line with end ticks."""
    f.path(f'M{x1:.1f},{y:.1f} L{x2:.1f},{y:.1f}', col, w, rough=False)
    for x in (x1, x2): f.path(f'M{x:.1f},{y - 8:.1f} L{x:.1f},{y + 8:.1f}', col, w, rough=False)


def register(fig):

    # ------------------------------------------------------------------ 15
    @fig('15')
    def single_leg_lever():
        f = Fig('15', 1560, 1130, 'Single-leg stance: the hip abductor lever', '单腿站立：髋外展肌杠杆')
        GM = COLOR['gluteus-medius']
        K = 1500
        st = Stage(f, 'ant', 0.0, -0.85, 420, 520, K)
        cid = f.id('clipA')
        f.raw(f'<clipPath id="{cid}"><rect x="20" y="150" width="780" height="820"/></clipPath><g clip-path="url(#{cid})">')
        st.bones(('femur-left',), op=0.55)
        st.bones(('hip-bone', 'hip-bone-left', 'sacrum', 'femur'))
        st.muscle('gluteus-medius', op=0.55)
        f.end()
        # key points
        head = st.at('femoral-head')
        com = st.P([0.0, 1.03, 0.0])
        A = st.P([-0.130, 0.975, 0.0]); B = st.P([-0.134, 0.866, 0.0])
        ydim = 640
        # lines of action (dotted) down to the dimension band
        f.path(f'M{com[0]:.1f},{com[1]:.1f} L{com[0]:.1f},{ydim + 10}', W_COL, 1.3, dash='3 5', rough=False)
        f.path(f'M{head[0]:.1f},{head[1]:.1f} L{head[0]:.1f},{ydim + 10}', INK, 1.3, dash='3 5', rough=False)
        bx = B[0] + (B[0] - A[0]) / (B[1] - A[1]) * (ydim - B[1])
        f.path(f'M{B[0]:.1f},{B[1]:.1f} L{bx:.1f},{ydim + 10}', GM, 1.3, dash='3 5', rough=False)
        # forces (solid arrows, AN-13)
        f.arrow(f'M{com[0]:.1f},{com[1] + 10:.1f} L{com[0]:.1f},{com[1] + 230:.1f}', W_COL, 4)
        f.arrow(f'M{A[0]:.1f},{A[1]:.1f} L{B[0]:.1f},{B[1] - 4:.1f}', GM, 4.5)
        # centre of gravity symbol
        x, y = com
        f.circle(x, y, 11, '#fff', W_COL, 2.2)
        f.raw(f'<path d="M{x},{y - 11} A11,11 0 0,1 {x + 11},{y} L{x},{y} Z M{x},{y + 11} A11,11 0 0,1 {x - 11},{y} L{x},{y} Z" fill="{W_COL}"/>')
        # fulcrum
        f.circle(head[0], head[1], 9, INK, '#fff', 2.5)
        f.raw(f'<path d="M{head[0]:.1f},{head[1] + 12:.1f} l-13,22 l26,0 Z" fill="{GOLD}" stroke="#fff" stroke-width="1.5"/>')
        # lever arms
        dim(f, bx, head[0], ydim, GM, 3)
        dim(f, head[0], com[0], ydim, W_COL, 3)
        f.text((bx + head[0]) / 2, ydim - 14, 'd', 20, GM, 'middle', '700')
        f.text((head[0] + com[0]) / 2, ydim - 14, 'D', 20, W_COL, 'middle', '700')
        # level pelvis reference
        cl, cr = st.P([-0.096, 1.012, 0]), st.P([0.096, 1.012, 0])
        f.path(f'M{cl[0] - 30:.1f},{cl[1]:.1f} L{cr[0] + 30:.1f},{cr[1]:.1f}', GREY, 1.4, dash='8 6', rough=False)
        # labels
        label(f, 40, 300, 'Gluteus medius force (F)', '臀中肌拉力（F）', GM, 'start', 15, to=((A[0] + B[0]) / 2, (A[1] + B[1]) / 2 - 20))
        label(f, 40, 205, 'Pelvis held level', '骨盆保持水平', GREY, 'start', 14, to=(cl[0] - 30, cl[1]))
        label(f, 470, 205, 'Centre of gravity', '重心', W_COL, 'start', 15, to=(com[0] + 12, com[1] - 6))
        label(f, 335, 765, 'Fulcrum: hip joint centre', '支点：髋关节中心', INK, 'start', 15, to=(head[0] + 2, head[1] + 34))
        label(f, 40, 560, 'Greater trochanter', '大转子', GREY, 'start', 14, to=st.at('greater-trochanter'))
        f.bi(head[0] + 32, ydim + 34, 'Body-weight lever arm', '体重力臂', 14, W_COL, 'start', '700')
        f.bi(bx - 20, ydim + 76, 'Abductor lever arm', '外展肌力臂', 14, GM, 'end', '700')
        f.leader(bx - 16, ydim + 70, (bx + head[0]) / 2, ydim + 12, GM)
        label(f, 640, 410, 'Body weight (W)', '体重（W）', W_COL, 'start', 15, to=(com[0] + 4, com[1] + 180))
        label(f, 40, 880, 'Stance leg (right)', '支撑腿（右）', INK, 'start', 15, to=st.P([-0.10, 0.62, 0]))
        label(f, 640, 880, 'Swing leg (left)', '摆动腿（左）', GREY, 'start', 15, to=st.P([0.10, 0.62, 0]))
        f.bi(420, 1010, 'Anterior view; arms drawn schematically', '前面观；力臂长度为示意', 14, GREY, 'middle', '400')

        # ---- right column: lever model and numbers
        X0 = 840
        f.bi(X0, 160, 'Lever model (first-class lever)', '杠杆模型（第一类杠杆）', 17, INK, 'start', '700')
        fx, by = 1010, 300
        d_px, D_px = 72, 180
        f.path(f'M{fx - d_px - 10},{by} L{fx + D_px + 10},{by}', BONE_E, 7, rough=False)
        f.path(f'M{fx - d_px - 10},{by} L{fx + D_px + 10},{by}', BONE, 4, rough=False)
        f.raw(f'<path d="M{fx},{by + 5} l-16,28 l32,0 Z" fill="{GOLD}" stroke="{INK}" stroke-width="1.5"/>')
        f.arrow(f'M{fx - d_px},{by - 74} L{fx - d_px},{by - 6}', GM, 4)
        f.arrow(f'M{fx + D_px},{by - 74} L{fx + D_px},{by - 6}', W_COL, 4)
        f.text(fx - d_px - 12, by - 54, 'F', 18, GM, 'end', '700')
        f.text(fx + D_px + 12, by - 54, 'W', 18, W_COL, 'start', '700')
        f.bi(fx, by + 56, 'Hip joint', '髋关节', 13, INK, 'middle', '600')
        dim(f, fx - d_px, fx, by + 98, GM, 2.5); dim(f, fx, fx + D_px, by + 98, W_COL, 2.5)
        f.text(fx - d_px / 2, by + 124, 'd = 5 cm', 14, GM, 'middle', '700')
        f.text(fx + D_px / 2, by + 124, 'D = 12.5 cm', 14, W_COL, 'middle', '700')
        f.bi(fx + D_px + 50, by + 30, 'D : d ≈ 2.5 : 1', '力臂比约 2.5∶1', 17, INK, 'start', '700')
        bipara(f, fx + D_px + 50, by + 76, 'One lever model; usually about 2–3 : 1', '某杠杆模型；一般约 2–3∶1', 13, 280, GREY)
        y = 470
        rows = [('Abductor force ≈ 1.6–2.5 × body weight (model-dependent)', '外展肌力 ≈ 体重的 1.6–2.5 倍（依模型而异）', GM),
                ('Joint reaction force ≈ 2.4–2.6 × body weight (up to ~4 × in some models)', '关节反作用力 ≈ 体重的 2.4–2.6 倍（部分模型可达约 4 倍）', JRF_COL),
                ('During gait the hip is loaded to ≈ 4–7 × body weight', '步行时髋关节负荷 ≈ 体重的 4–7 倍', JRF_COL)]
        for en, zh, col in rows:
            f.circle(X0 + 6, y - 5, 5, col, '#fff', 1)
            y = bipara(f, X0 + 20, y, en, zh, 14, 660, col, '600') + 10

        # ---- Trendelenburg inset
        ty = 620
        f.box(X0 - 10, ty, 690, 300, '#8c2f39', '#fffaf3', dash='6 4')
        f.bi(X0 + 8, ty + 30, 'Weak abductors → pelvis drops on the swing side (Trendelenburg sign)', '外展肌无力 → 摆动侧骨盆下沉（Trendelenburg 征）', 15, '#8c2f39', 'start', '700')
        k2 = 560
        s2 = Stage(f, 'ant', 0.0, -0.85, X0 + 150, ty + 170, k2)
        h2 = s2.at('femoral-head')
        cid2 = f.id('clipB')
        f.raw(f'<clipPath id="{cid2}"><rect x="{X0}" y="{ty + 60}" width="320" height="180"/></clipPath><g clip-path="url(#{cid2})">')
        s2.bones(('femur',), w=1.4)
        f.g(f'rotate(9 {h2[0]:.1f} {h2[1]:.1f})')
        s2.bones(('femur-left',), w=1.2, op=0.55)
        s2.bones(('hip-bone', 'hip-bone-left', 'sacrum'), w=1.4)
        s2.muscle('gluteus-medius', op=0.45, w=1.2, dash='4 3')
        c1, c2 = s2.P([-0.096, 1.012, 0]), s2.P([0.096, 1.012, 0])
        f.path(f'M{c1[0] - 14:.1f},{c1[1]:.1f} L{c2[0] + 14:.1f},{c2[1]:.1f}', '#8c2f39', 2, rough=False)
        f.end()
        f.path(f'M{c1[0] - 14:.1f},{c1[1]:.1f} L{c2[0] + 30:.1f},{c1[1]:.1f}', GREY, 1.4, dash='6 5', rough=False)
        f.end()
        # rotated crest line end (for the drop arrow)
        ang = math.radians(9)
        def rot(p):
            dx, dy = p[0] - h2[0], p[1] - h2[1]
            return (h2[0] + dx * math.cos(ang) - dy * math.sin(ang), h2[1] + dx * math.sin(ang) + dy * math.cos(ang))
        r2 = rot((c2[0] + 14, c2[1]))
        f.arrow(f'M{r2[0] + 14:.1f},{c1[1] + 2:.1f} L{r2[0] + 14:.1f},{r2[1] + 4:.1f}', '#8c2f39', 2.6)
        tx = X0 + 340
        yy = bipara(f, tx, ty + 82, 'Stance on the weak side: the pelvis drops on the opposite (swing) side — a positive sign; one gait study used a drop of > 4°.',
                    '患侧单腿支撑时对侧（摆动侧）骨盆下沉即为阳性；一项步态研究以下沉 > 4° 为阳性。', 13, 320, INK)
        yy = bipara(f, tx, yy + 10, 'Compensation: the trunk leans over the stance hip, shortening D (gluteus medius gait).',
                    '代偿：躯干向支撑侧倾斜，缩短 D（臀中肌步态）。', 13, 320, INK)
        f.bi(X0 + 8, ty + 270, 'Stance (weak) side', '支撑侧（患侧）', 13, INK, 'start', '600')
        f.bi(X0 + 200, ty + 270, 'Swing side', '摆动侧', 13, '#8c2f39', 'start', '600')

        # ---- cane note
        cy = 945
        f.box(X0 - 10, cy, 690, 128, '#2b6c7c', '#f4f8f6')
        f.bi(X0 + 8, cy + 26, 'Cane in the opposite hand (cane bears ~1/6 body weight)', '对侧手持手杖（手杖承担约 1/6 体重）', 15, '#2b6c7c', 'start', '700')
        bipara(f, X0 + 8, cy + 72, 'Abductor force ~1.6 → ~0.6 × BW; joint force ~2.4 → ~1.3 × BW. Same-side hand: only ~1.3 × and ~2.0 × BW.',
               '外展肌力约 1.6 → 0.6 倍体重；关节力约 2.4 → 1.3 倍体重。同侧手持杖仅降到约 1.3 倍和 2.0 倍。', 13, 660, INK)
        f.save('单腿站立的髋外展杠杆')

    # ------------------------------------------------------------------ 16
    @fig('16')
    def lumbopelvic_rhythm():
        f = Fig('16', 1560, 1030, 'Lumbopelvic rhythm in forward bending', '前屈时的腰椎-骨盆节律')
        # key
        ky = 140
        f.path(f'M40,{ky} L90,{ky}', LUMB, 7, rough=False)
        f.bi(100, ky + 5, 'Lumbar flexion', '腰椎屈曲', 14, LUMB, 'start', '700')
        f.path(f'M300,{ky} L350,{ky}', HIPC, 7, rough=False)
        f.bi(360, ky + 5, 'Hip flexion (anterior pelvic tilt on the femoral heads)', '屈髋（骨盆在股骨头上前倾）', 14, HIPC, 'start', '700')
        f.path(f'M860,{ky} L910,{ky}', GREY, 2, dash='6 5', rough=False)
        f.bi(920, ky + 5, 'Upright start position', '直立起始姿势', 14, GREY, 'start', '600')
        f.bi(1180, ky + 5, 'Thick = leading part', '粗线 = 主导部分', 14, INK, 'start', '600')

        def R(dx, dy, a):
            a = math.radians(a)
            return (dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a))

        PELV = [(30, -38), (6, -60), (-26, -56), (-40, -36), (-42, -12), (-16, 22), (6, 22), (24, 8)]

        def figure(hx, gy, alpha, beta, lw=4, pw=2, ghost=False):
            """Lateral stick figure facing right (anterior = right). alpha: anterior pelvic tilt on the femoral head,
            beta: lumbar flexion (schematic drawing angles, not measured values)."""
            hy = gy - 182
            pp = [(hx + R(x, y, alpha)[0], hy + R(x, y, alpha)[1]) for x, y in PELV]
            n = len(pp)
            d = 'M%.1f,%.1f ' % ((pp[0][0] + pp[1][0]) / 2, (pp[0][1] + pp[1][1]) / 2)
            for k in range(1, n + 1):
                c, nx = pp[k % n], pp[(k + 1) % n]
                d += 'Q%.1f,%.1f %.1f,%.1f ' % (c[0], c[1], (c[0] + nx[0]) / 2, (c[1] + nx[1]) / 2)
            d += 'Z'
            sx, sy = hx + R(-28, -48, alpha)[0], hy + R(-28, -48, alpha)[1]
            th = alpha + 14
            lum = [(sx, sy)]
            for i in range(6):
                th += (-28 + beta) / 6
                a = math.radians(th)
                lum.append((lum[-1][0] + 14 * math.sin(a), lum[-1][1] - 14 * math.cos(a)))
            th += 10; a = math.radians(th)
            sh = (lum[-1][0] + 100 * math.sin(a), lum[-1][1] - 100 * math.cos(a))
            th += 10; a = math.radians(th)
            hd = (sh[0] + 34 * math.sin(a), sh[1] - 34 * math.cos(a))
            ld = 'M' + ' L'.join('%.1f,%.1f' % p for p in lum)
            if ghost:
                f.path(d, GREY, 1.5, 'none', dash='6 5', rough=False)
                f.path(ld + ' L%.1f,%.1f' % sh, GREY, 1.6, dash='6 5', rough=False)
                f.raw(f'<circle cx="{hd[0]:.1f}" cy="{hd[1]:.1f}" r="18" fill="none" stroke="{GREY}" stroke-width="1.5" stroke-dasharray="6 5"/>')
                return
            f.path(f'M{hx},{hy} L{hx - 3},{gy - 8} L{hx + 30},{gy - 4}', INK, 4)
            f.path(d, HIPC, pw, '#f6dccf')
            f.circle(hx, hy, 6, '#fff', INK, 2.2)
            f.path(ld, LUMB, lw)
            f.path('M%.1f,%.1f L%.1f,%.1f' % (*lum[-1], *sh), INK, 4)
            f.circle(hd[0], hd[1], 18, '#fffdf7', INK, 2.4)
            f.path('M%.1f,%.1f L%.1f,%.1f' % (*sh, sh[0] + 4, sh[1] + 105), INK, 3)
            return dict(hip=(hx, hy), lum=lum, sh=sh, head=hd)

        def arc(cx, cy, r, a1, a2, col, w=3):
            p1 = (cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1)))
            p2 = (cx + r * math.cos(math.radians(a2)), cy + r * math.sin(math.radians(a2)))
            sweep = 1 if a2 > a1 else 0
            f.arrow(f'M{p1[0]:.1f},{p1[1]:.1f} A{r},{r} 0 0,{sweep} {p2[0]:.1f},{p2[1]:.1f}', col, w)

        # alpha = pelvic tilt, beta = lumbar flexion (drawing angles only); lw/pw = stroke weight of the leading part
        stages = [dict(alpha=5, beta=42, lw=10, pw=2), dict(alpha=32, beta=50, lw=7, pw=6),
                  dict(alpha=70, beta=52, lw=4, pw=9), dict(alpha=30, beta=52, lw=6, pw=7)]
        pw_ = 372
        gy = 700
        tags = [('Lumbar flexion leads', '腰椎主导', LUMB), ('Both share the motion', '两者共同参与', INK),
                ('Hip flexion dominates', '屈髋主导', HIPC), ('Hips first, then lumbar spine', '先髋后腰', INK)]
        for i, (s, stg) in enumerate(zip(stages, MV['stages'])):
            x0 = 30 + i * (pw_ + 10)
            f.box(x0, 190, pw_, 760, '#d8d1c0', '#fffdf7')
            f.step(x0 + 26, 218, stg['label'])
            hx = x0 + 92
            f.path(f'M{x0 + 14},{gy} L{x0 + pw_ - 14},{gy}', '#b7ab95', 2, rough=False)
            figure(hx, gy, 0, 0, ghost=True)
            if i == 3:
                figure(hx, gy, 70, 52, ghost=True)
            g = figure(hx, gy, s['alpha'], s['beta'], s['lw'], s['pw'])
            hxp, hyp = g['hip']
            if 0 < i < 3:   # anterior pelvic tilt = hip flexion
                arc(hxp, hyp, 62, -40, 25, HIPC)
            if i == 0:      # lumbar flexion arrow
                lm = g['lum'][3]
                arc(lm[0], lm[1], 52, -150, -95, LUMB)
                label(f, x0 + 225, 470, 'Lumbar spine', '腰椎', LUMB, 'start', 14, to=g['lum'][2])
                label(f, x0 + 225, 545, 'Pelvis', '骨盆', HIPC, 'start', 14, to=(hxp + 30, hyp - 20))
                label(f, x0 + 225, 610, 'Hip joint', '髋关节', INK, 'start', 14, to=(hxp + 6, hyp + 2))
                label(f, x0 + 225, 665, 'Thigh', '大腿', GREY, 'start', 14, to=(hxp - 1, hyp + 120))
            if i == 1:
                lm = g['lum'][4]
                arc(lm[0], lm[1], 52, -150, -95, LUMB, 2.4)
            if i == 3:      # return order: 1 hips (posterior tilt), 2 lumbar extension
                arc(hxp, hyp, 62, 25, -40, HIPC)
                p = (hxp + 62 * math.cos(math.radians(40)) + 18, hyp + 62 * math.sin(math.radians(40)) + 4)
                f.step(*p, '1', HIPC)
                lm = g['lum'][4]
                arc(lm[0], lm[1], 52, -60, -130, LUMB)
                f.step(lm[0] - 52, lm[1] - 52, '2', LUMB)
            ty = gy + 40
            f.bi(x0 + 18, ty, tags[i][0], tags[i][1], 15, tags[i][2], 'start', '700')
            yy = para(f, x0 + 18, ty + 46, stg['heading']['en'], 15, pw_ - 36, INK, '700')
            yy = para(f, x0 + 18, yy, stg['heading']['zh'], 14, pw_ - 36, ZH)
            yy = para(f, x0 + 18, yy + 8, SHORT[i][0], 13, pw_ - 36, GREY)
            para(f, x0 + 18, yy, SHORT[i][1], 13, pw_ - 36, GREY)
        f.save('腰椎骨盆节律')

    MV = {'stages': [
        {'label': '1', 'heading': {'en': 'Early forward bending: lumbar flexion leads', 'zh': '前屈早期：腰椎屈曲为主'}},
        {'label': '2', 'heading': {'en': 'Mid range: anterior pelvic tilt joins in', 'zh': '中段：骨盆前倾加入'}},
        {'label': '3', 'heading': {'en': 'End range: hip flexion dominates', 'zh': '末段：屈髋为主'}},
        {'label': '4', 'heading': {'en': 'Return to upright: hips first, then lumbar spine', 'zh': '回到直立：先髋后腰'}}]}
    SHORT = [
        ('Motion starts at the lumbosacral spine; lumbar-to-pelvic ratio > 1.', '动作从腰骶部开始；腰椎/骨盆比值 > 1。'),
        ('The pelvis tilts forward on the femoral heads; the ratio falls. Lumbar and hip extensors (hamstrings, gluteus maximus) lower the trunk eccentrically.',
         '骨盆在股骨头上前倾，比值下降；腰伸肌和伸髋肌（腘绳肌、臀大肌）离心控制躯干下降。'),
        ('Most motion comes from the pelvis and hips; ratio < 1 (about 0.5 in one study). Tight hamstrings limit this phase.',
         '运动主要来自骨盆和髋；比值 < 1（一项研究约 0.5）。腘绳肌紧张会限制这一阶段。'),
        ('① Hip extensors tilt the pelvis back first; ② lumbar extension follows near the end.',
         '① 伸髋肌先使骨盆后倾；② 接近结束时腰椎才伸展。')]


    GAIT_PHASES = [
        ('Initial contact', '初始着地', 0, 2),
        ('Loading response', '承重反应期', 2, 12),
        ('Midstance', '站立中期', 12, 31),
        ('Terminal stance', '站立末期', 31, 50),
        ('Pre-swing', '摆动前期', 50, 62),
        ('Initial swing', '摆动初期', 62, 75),
        ('Mid swing', '摆动中期', 75, 87),
        ('Terminal swing', '摆动末期', 87, 100),
    ]
    GAIT_ROWS = [  # (row id, member ids, windows %, role en, role zh) — from the sourced gait tables
        ('gluteus-maximus', ['gluteus-maximus'], [(87, 100), (0, 12)],
         'Active from terminal swing through loading response. The lower fibres decelerate hip flexion at the end of swing and then hold the hip against the large flexion moment of weight acceptance; the upper fibres help control the opposite pelvis in the frontal plane.',
         '从摆动末期到承重反应期活跃。下部纤维在摆动末期减速屈髋，随后在承重时对抗很大的屈髋力矩；上部纤维帮助在冠状面控制对侧骨盆。'),
        ('gluteus-medius', ['gluteus-medius', 'gluteus-minimus'], [(87, 100), (0, 31)],
         'Switches on in terminal swing in anticipation of loading and stays active through loading response and midstance, working eccentrically and then isometrically to stop the opposite pelvis from dropping; activity may continue into terminal stance.',
         '在摆动末期预先激活，并持续到承重反应期和站立中期，先离心后等长收缩，防止对侧骨盆下沉；活动可延续至站立末期。'),
        ('tensor-fasciae-latae', ['tensor-fasciae-latae'], [(2, 12), (31, 50)],
         'Its posterior part works with the abductors to stabilise the pelvis in loading response, and its anterior part is active in terminal stance to help keep the hip stable.',
         '其后部在承重反应期与外展肌一起稳定骨盆，前部在站立末期活跃，帮助维持髋关节稳定。'),
        ('iliopsoas', ['psoas-major', 'iliacus'], [(31, 87)],
         'Works eccentrically in terminal stance to control the rate of hip extension, then concentrically from pre-swing through mid swing to flex the hip and advance the limb; its burst in initial swing is large and fast.',
         '在站立末期离心收缩以控制伸髋速度，随后从摆动前期到摆动中期向心收缩屈髋、推动下肢向前；摆动初期的爆发大而迅速。'),
        ('adductor-longus', ['adductor-longus'], [(50, 75)],
         'Active in pre-swing and initial swing, where it assists hip flexion as the limb is brought forward.',
         '在摆动前期和摆动初期活跃，协助屈髋，把下肢向前带。'),
        ('adductor-magnus', ['adductor-magnus'], [(87, 100), (0, 12)],
         'Active with the hamstrings and gluteus maximus at the end of swing and in loading response, contributing to hip extension and internal rotation during weight acceptance.',
         '在摆动末期和承重反应期与腘绳肌、臀大肌一同活跃，在承重时参与伸髋和内旋。'),
        ('hamstrings', ['biceps-femoris', 'semitendinosus', 'semimembranosus'], [(75, 100), (0, 12)],
         'Begin in mid swing and peak in terminal swing, decelerating knee extension and hip flexion eccentrically; they then help control hip flexion at initial contact and in loading response.',
         '从摆动中期开始，在摆动末期达到高峰，离心减速伸膝和屈髋；随后在初始着地和承重反应期帮助控制屈髋。'),
        ('rectus-femoris', ['rectus-femoris'], [(50, 75)],
         'Active in pre-swing and initial swing, where it augments hip flexion while limiting excessive knee flexion; as part of the quadriceps it also helps control knee flexion at loading.',
         '在摆动前期和摆动初期活跃，既加强屈髋，又限制过度屈膝；作为股四头肌的一部分，它在承重时也帮助控制屈膝。'),
        ('sartorius-gracilis', ['sartorius', 'gracilis'], [(62, 87)],
         'Sartorius and gracilis join iliacus as concentric hip flexors in initial swing and mid swing.',
         '缝匠肌和股薄肌在摆动初期和摆动中期与髂肌一起向心收缩屈髋。'),
    ]
    ROW_NAME = {'gluteus-maximus': ('Gluteus maximus', '臀大肌'), 'gluteus-medius': ('Gluteus medius & minimus', '臀中肌与臀小肌'),
                'tensor-fasciae-latae': ('Tensor fasciae latae', '阔筋膜张肌'), 'iliopsoas': ('Iliopsoas', '髂腰肌'),
                'adductor-longus': ('Adductor longus', '长收肌'), 'adductor-magnus': ('Adductor magnus', '大收肌'),
                'hamstrings': ('Hamstrings', '腘绳肌'), 'rectus-femoris': ('Rectus femoris', '股直肌'),
                'sartorius-gracilis': ('Sartorius & gracilis', '缝匠肌与股薄肌')}

    # ------------------------------------------------------------------ 17
    @fig('17')
    def gait_timeline():
        TX0, TX1 = 270, 1050           # timeline 0–100 %
        RX, RW = 1080, 445             # role text column
        px = lambda pct: TX0 + (TX1 - TX0) * pct / 100
        # row heights from wrapped role text
        rows = []
        for rid, mem, win, en, zh in GAIT_ROWS:
            le, lz = wrap(en, 13, RW), wrap(zh, 13, RW)
            h = max(70, 18 * (len(le) + len(lz)) + 26)
            rows.append((rid, mem, win, le, lz, h))
        top = 330
        H = top + sum(r[5] for r in rows) + 170
        f = Fig('17', 1560, H, 'Hip muscle activity across the gait cycle', '步态周期中髋部肌肉的发力时间轴')
        # stance / swing band
        sw = GAIT_PHASES[4][3]  # end of pre-swing = toe-off
        f.box(px(0), 130, px(sw) - px(0), 40, '#7d8b8f', '#e9eef0', sw=1.2)
        f.box(px(sw), 130, px(100) - px(sw), 40, '#c69014', '#f8efd9', sw=1.2)
        f.bi((px(0) + px(sw)) / 2, 146, 'Stance phase (0–%d %%)' % sw, '站立相', 14, INK, 'middle', '700', gap=16)
        f.bi((px(sw) + px(100)) / 2, 146, 'Swing phase (%d–100 %%)' % sw, '摆动相', 14, INK, 'middle', '700', gap=16)
        # phase names: two tiers, alternating
        for k, (en, zh, a, b) in enumerate(GAIT_PHASES):
            cx = (px(a) + px(b)) / 2
            yl = 200 if k % 2 == 0 else 252
            if k == 0:
                f.bi(TX0 - 4, yl, en, zh, 13, INK, 'end', '600')
            elif k == 1:
                f.bi(cx - 24, yl, en, zh, 13, INK, 'start', '600')
            else:
                f.bi(cx, yl, en, zh, 13, INK, 'middle', '600')
            f.leader(cx, yl + 22, cx, 296, '#b7ab95')
        # axis
        f.path(f'M{TX0},{300} L{TX1},{300}', INK, 1.4, rough=False)
        for pct in range(0, 101, 10):
            f.path(f'M{px(pct):.1f},{296} L{px(pct):.1f},{306}', INK, 1.2, rough=False)
            f.text(px(pct), 322, '%d%%' % pct, 13, GREY, 'middle', '400')
        y = top + 6
        f.bi(40, 296, 'Muscle', '肌肉', 13, GREY, 'start', '700')
        f.bi(RX, 296, 'Role', '作用', 13, GREY, 'start', '700')
        bottom = top + sum(r[5] for r in rows)
        # phase boundaries
        for en, zh, a, b in GAIT_PHASES[1:]:
            f.path(f'M{px(a):.1f},{top} L{px(a):.1f},{bottom}', '#d8d1c0', 1.2, dash='4 4', rough=False)
        f.path(f'M{px(sw):.1f},{top} L{px(sw):.1f},{bottom}', '#c69014', 1.8, dash='6 4', rough=False)
        for idx, (rid, mem, win, le, lz, h) in enumerate(rows):
            col = COLOR[mem[0]]
            if idx % 2 == 0:
                f.raw(f'<rect x="30" y="{y - 6}" width="1500" height="{h}" fill="#f3eee2" opacity=".55"/>')
            name = ROW_NAME[rid]
            f.bi(40, y + 22, name[0], name[1], 15, col, 'start', '700')
            for a, b in win:
                f.path(f'M{px(a) + 1:.1f},{y + 10} L{px(b) - 1:.1f},{y + 10} L{px(b) - 1:.1f},{y + 34} L{px(a) + 1:.1f},{y + 34} Z', col, 1.6, col, op=0.9)
            yy = y + 16
            for ln in le:
                f.text(RX, yy, ln, 13, INK, 'start', '400'); yy += 18
            for ln in lz:
                f.text(RX, yy, ln, 13, ZH, 'start', '400', 'zh-CN'); yy += 18
            y += h
        f.path(f'M{TX0},{bottom} L{TX1},{bottom}', INK, 1.2, rough=False)
        f.bi(TX0, bottom + 34, 'Approximate windows mapped from phase tables; bars that reach 100 % continue at 0 % of the next cycle.',
             '根据步态分期表映射的大致时间窗；到达 100% 的色条在下一周期的 0% 处延续。', 14, GREY, 'start', '600')
        f.bi(TX0, bottom + 82, 'Gait cycle of one limb, from initial contact to the next initial contact.', '单侧下肢一个步态周期：从初始着地到下一次初始着地。', 13, GREY, 'start', '400')
        f.save('步态周期中髋部肌肉发力时间轴')
