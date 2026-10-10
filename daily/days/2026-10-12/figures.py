#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Week 1 Monday 2026-10-12, published early as a trial on 2026-10-09: SI14, SI15, TE15, LI14 and the rotator cuff.
Run via pipeline (figures step) or: python3 figures.py <out_dir>."""
import pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from engine.figlib import *
from engine.figlib import posterior as P

REPO = pathlib.Path(__file__).resolve().parents[3]
SI_C, TE_C, LI_C = RED, "#7a5aa6", TEAL
LEV_C, RHO_C, SUP_C = ("#d9c48f", "#9a7b1c"), ("#c9d6b2", "#5c7a3a"), ("#e9a596", RED)

LEVATOR = "M684,170 C700,166 714,178 714,198 C718,258 736,330 752,394 L752,446 C744,420 728,360 708,302 C694,252 684,210 684,170 Z"
RHO_MIN = "M664,322 L664,368 L752,452 L750,420 Z"
RHO_MAJ = "M664,394 L664,512 L772,592 L756,462 Z"
SUPRA = "M752,398 C800,388 850,382 878,380 L910,372 C860,400 800,428 752,446 Z"
SI15, SI14, TE15 = (715, 343), (750, 378), (768, 388)


def dot(f, x, y, col, r=8):
    f.circle(x, y, r, col, "#fff", 2.4)


# ------------------------------------------------------------------ 01 posterior overlay
def f01():
    f = Fig("01", 1400, 980, "SI14, SI15 and TE15 on the muscles beneath", "肩外俞、肩中俞、天髎与深面的肌肉（右侧后面观）")
    S, X0, Y0 = 1.5, 60 - 600 * 1.5, 120 - 150 * 1.5
    p = lambda x, y: (X0 + S * x, Y0 + S * y)
    f.raw(f'<clipPath id="{f.id("crop")}"><rect x="600" y="150" width="420" height="510"/></clipPath>')
    f.g(f"translate({X0:.1f},{Y0:.1f}) scale({S})"); f.raw(f'<g clip-path="url(#{f.id("crop")})">')
    P.posterior_base(f, both=False, labels=False)
    f.path(SUPRA, SUP_C[1], 1.6, SUP_C[0], op=0.85)
    f.path(RHO_MAJ, RHO_C[1], 1.6, RHO_C[0], op=0.85)
    f.path(RHO_MIN, RHO_C[1], 1.6, "#b7c99a", op=0.9)
    f.path(LEVATOR, LEV_C[1], 1.6, LEV_C[0], op=0.9)
    for d in (P.TRAP_UP_R, P.TRAP_MID_R, P.TRAP_LOW_R):           # trapezius drawn as a see-through outline (it covers all three points)
        f.path(d, "#8f4a3c", 1.4, "#e9a596", dash="6 5", op=0.22)
    f.path(f"M{P.MID},300 L748,300", INK, 1.4, rough=False)          # 3-cun ruler: posterior midline → medial border
    for k in range(4):
        x = P.MID + k * 98 / 3
        f.path(f"M{x:.1f},294 L{x:.1f},306", INK, 1.4, rough=False)
    for lv in ("C7", "T1", "T2"):
        f.path(f"M{P.MID + 14},{P.sp_y(lv)} L{P.MID + 22},{P.sp_y(lv)}", INK, 1.2, rough=False)
    f.raw("</g>"); f.end()
    for k in range(4):
        x, y = p(P.MID + k * 98 / 3, 300); f.text(x, y - 14, f"{k}", 13, INK, "middle", "700")
    x, y = p(P.MID + 49, 300); f.bi(x, y - 62, "cun from the midline", "距后正中线（寸）", 13, INK, "middle", "700")
    for lv in ("C7", "T1", "T2", "T4"):
        x, y = p(P.MID - 20, P.sp_y(lv) + 5); f.text(x, y, lv, 15, "#6b6458", "end", "700")
    # points
    for (bx, by), col in ((SI15, SI_C), (SI14, SI_C), (TE15, TE_C)):
        x, y = p(bx, by); dot(f, x, y, col)
    for (bx, by), (lx, ly), en, zh, col in [(SI15, (700, 170), "SI15 Jianzhongshu: below C7, 2 cun lateral", "肩中俞：第 7 颈椎棘突下，旁开 2 寸", SI_C),
                                           (SI14, (700, 250), "SI14 Jianwaishu: below T1, 3 cun lateral", "肩外俞：第 1 胸椎棘突下，旁开 3 寸", SI_C),
                                           (TE15, (700, 330), "TE15 Tianliao: depression at the superior angle", "天髎：肩胛骨上角骨际凹陷中", TE_C)]:
        x, y = p(bx, by); f.leader(x + 9, y, lx - 8, ly - 5, col); f.bi(lx, ly, en, zh, 16, col)
    # muscles (labels in the order of their targets, top to bottom, so leaders don't cross)
    for (bx, by), (lx, ly), en, zh, col in [((700, 240), (930, 470), "Levator scapulae (deep to trapezius)", "肩胛提肌（在斜方肌深面）", LEV_C[1]),
                                           ((800, 330), (930, 550), "Trapezius (dashed): the superficial layer over all three", "斜方肌（虚线）：三个穴位的浅层", "#8f4a3c"),
                                           ((715, 390), (930, 630), "Rhomboid minor (C7–T1 → root of spine)", "小菱形肌（C7–T1 → 肩胛冈根部）", RHO_C[1]),
                                           ((850, 395), (930, 710), "Supraspinatus in the supraspinous fossa", "冈上肌（冈上窝内）", SUP_C[1]),
                                           ((720, 500), (930, 790), "Rhomboid major", "大菱形肌", RHO_C[1])]:
        x, y = p(bx, by); f.leader(x, y, lx - 8, ly - 5, col); f.bi(lx, ly, en, zh, 15, col)
    f.bi(700, 900, "Schematic. The base art places the scapula a little low; on a real back the superior angle is near T2, about 1 cun from SI14.",
         "示意图。底图的肩胛骨略偏低；真人身上肩胛骨上角约平 T2，与肩外俞相距约 1 寸。", 13, "#6b706a", "middle", "400")
    f.save("肩外俞肩中俞天髎-叠加图")


# ------------------------------------------------------------------ 02 LI14 on the lateral arm
def f02():
    f = Fig("02", 1200, 1000, "LI14 Binao on the lateral arm", "臂臑：右臂外侧面观")
    f.bi(40, 120, "Right arm, lateral view: anterior is to the right.", "右臂外侧面观：右边是前面。", 15, INK, weight="400")
    cun = lambda k: 800 - k * 52                                                  # elbow crease y=800; 9 cun to the axillary fold
    f.path("M520,190 C470,260 470,420 488,560 C496,660 500,740 512,820 L700,820 C708,740 716,660 722,560 C732,420 740,300 716,210 Z", "#b9b2a3", 1.6, "#f8f3e8")
    f.path("M520,250 C520,420 540,620 556,800", "#c9a98f", 1.4, "#f1e2cf", op=0.0)
    f.path("M500,330 C490,450 500,600 540,800 L580,800 C560,620 556,450 560,330 Z", "#c9a98f", 1.4, "#ead8c4")      # triceps lateral head
    f.path("M690,360 C716,460 716,620 690,800 L640,800 C660,620 664,470 650,380 Z", "#c9a98f", 1.4, "#f3e6d6")      # biceps
    f.path("M520,190 C560,170 640,166 712,200 C700,260 660,360 616,460 C580,380 540,300 520,190 Z", "#a59b88", 1.8, "#ece4d4")  # deltoid
    f.path("M520,190 C560,170 640,166 712,200", BONE_E, 10); f.path("M520,190 C560,170 640,166 712,200", BONE, 7, rough=False)  # acromion
    f.path(f"M470,{cun(0)} L740,{cun(0)}", "#9a958a", 1.4, dash="5 5", rough=False)                       # elbow crease
    f.path(f"M470,{cun(9)} L740,{cun(9)}", "#9a958a", 1.4, dash="5 5", rough=False)                       # axillary fold level
    f.path(f"M420,{cun(0)} L420,{cun(9)}", INK, 1.6, rough=False)
    for k in range(10):
        f.path(f"M412,{cun(k)} L428,{cun(k)}", INK, 1.4, rough=False); f.text(406, cun(k) + 5, str(k), 13, INK, "end", "700")
    f.bi(60, 860, "Ruler: upper arm = 9 cun", "标尺：上臂 9 寸", 15, INK)
    f.bi(60, 900, "axillary fold (9) → elbow crease (0)", "腋前纹头（9）→ 肘横纹（0）", 13, "#6b706a", weight="400")
    li15, li11, li14 = (690, 214), (712, cun(0)), (680, cun(7))
    f.path(f"M{li15[0]},{li15[1]} L{li11[0]},{li11[1]}", LI_C, 2, dash="8 6", rough=False)
    for (x, y), txt in ((li15, "LI15"), (li11, "LI11")):
        dot(f, x, y, "#7fa9b3", 7); f.text(x + 14, y + 5, txt, 14, LI_C, weight="700")
    dot(f, *li14, LI_C, 10)
    f.leader(li14[0] + 10, li14[1], 820, 420, LI_C); f.bi(828, 425, "LI14 Binao", "臂臑", 20, LI_C, weight="700")
    f.bi(828, 480, "On the LI11–LI15 line, 7 cun above LI11,", "在曲池与肩髃连线上，曲池上 7 寸，", 14, INK, weight="400")
    f.bi(828, 524, "just anterior to the deltoid's border.", "三角肌前缘处。", 14, INK, weight="400")
    f.path(f"M760,{cun(0)} L760,{cun(7)}", LI_C, 1.6, rough=False)
    f.text(770, cun(0) - 40, "7 cun · 7 寸", 15, LI_C, weight="700")
    for (x, y), (lx, ly), en, zh in [((580, 280), (60, 250), "Deltoid", "三角肌"), ((680, 620), (828, 660), "Biceps brachii", "肱二头肌"),
                                     ((520, 560), (60, 560), "Triceps brachii (lateral head)", "肱三头肌外侧头"), ((620, 182), (828, 200), "Acromion", "肩峰")]:
        f.leader(x, y, lx - 8 if lx > x else lx + (80 if en == "Deltoid" else 240), ly - 5); f.bi(lx, ly, en, zh, 15, INK)
    f.bi(828, 860, "Feel it: abduct the arm against resistance; the lower", "摸法：手臂抗阻外展，三角肌下端前缘", 13, "#6b706a", weight="400")
    f.bi(828, 900, "anterior edge of the deltoid stands out.", "会鼓起来，穴位就在它前方。", 13, "#6b706a", weight="400")
    f.save("臂臑-上臂外侧")


# ------------------------------------------------------------------ 03 layers
def f03():
    f = Fig("03", 1300, 660, "What lies beneath SI14 and TE15", "肩外俞、天髎深面有什么：层次示意")
    f.bi(38, 116, "Not to scale; layers only, not needling depth or direction.", "不按比例，只表示层次，不表示进针深度或方向。", 14, RED, weight="400")
    stack2(f, 40, 170, 580, "Jianwaishu (SI14) · below T1, 3 cun lateral", "肩外俞 · 第 1 胸椎棘突下旁开 3 寸",
           [("Skin", "皮肤", 40, "#f6e7da", "#d8c3ae", ""),
            ("Subcutaneous: medial cutaneous branch of T1 posterior ramus", "皮下组织：第 1 胸神经后支内侧皮支", 56, "#fbf2e3", "#e0d2b8", ""),
            ("Trapezius (accessory nerve)", "斜方肌（副神经）", 48, "#f4d6cd", "#c9897a", ""),
            ("Levator scapulae, rhomboid minor; dorsal scapular nerve, transverse cervical vessels", "肩胛提肌、小菱形肌；肩胛背神经，颈横动、静脉", 60, "#e9e1c4", "#9a7b1c", ""),
            ("Deeper: chest wall, pleura and the lung", "更深：胸壁、胸膜与肺", 52, "#f2c9c3", RED, "危险")],
           "Textbook: oblique insertion 0.3–0.5 cun.", "教材：斜刺 0.3～0.5 寸。")
    stack2(f, 680, 170, 580, "Tianliao (TE15) · superior angle of the scapula", "天髎 · 肩胛骨上角",
           [("Skin", "皮肤", 40, "#f6e7da", "#d8c3ae", ""),
            ("Subcutaneous: lateral cutaneous branch of T1 posterior ramus", "皮下组织：第 1 胸神经后支外侧皮支", 56, "#fbf2e3", "#e0d2b8", ""),
            ("Trapezius; descending branch of transverse cervical a.", "斜方肌；颈横动脉降支", 52, "#f4d6cd", "#c9897a", ""),
            ("Supraspinatus; muscular branches of suprascapular a. and n.", "冈上肌；肩胛上动脉、肩胛上神经肌支", 56, "#e9a596", RED, "留意"),
            ("Scapula (bone near the superior angle)", "肩胛骨上角附近骨面", 44, "#efe5cf", "#9a958a", "")],
           "Textbook: perpendicular 0.5–0.8 cun.", "教材：直刺 0.5～0.8 寸。")
    f.save("肩外俞天髎-层次示意")


# ------------------------------------------------------------------ 04 rotator cuff (library chapter figure, reused: DL-03)
def f04(out):
    src = REPO / "library" / "shoulder" / "figures" / "01-右肩的后面观与前面观.svg"
    svg = src.read_text(encoding="utf-8")
    svg = re.sub(r"<filter\b.*?</filter>", "", svg, flags=re.S)                      # the daily checks reject displacement filters
    svg = re.sub(r'\s*filter="url\(#[^)]*\)"', "", svg)
    svg = re.sub(r'<tspan x="(\d+)" dy="18" font-size="20"', r'<tspan dx="12" dy="0" font-size="20"', svg)   # view titles: Chinese on the same line (no overlap)
    (pathlib.Path(out) / "04-肩袖四肌-后面观与前面观.svg").write_text(svg, encoding="utf-8")


def build(out_dir):
    set_out(out_dir)
    f01(); f02(); f03(); f04(out_dir)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent / "资源")
