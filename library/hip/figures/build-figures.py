#!/usr/bin/env python3
"""Build the hip chapter's numbered SVG figures (AN-10..AN-17) into library/hip/figures/.
Run from the repo root:  python3 library/hip/figures/build-figures.py [figure numbers...]
Base art comes from tools/outlines.json (projected from the 3D model by tools/project-outlines.py)."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'tools'))
from hipfig import *  # noqa: F401,F403

OUT_DIR = Path(sys.argv[sys.argv.index('--out') + 1]) if '--out' in sys.argv else Path(__file__).resolve().parent
set_out(OUT_DIR)
FIGS = {}


def fig(num):
    def wrap(fn): FIGS[num] = fn; return fn
    return wrap


@fig('01')
def bones_overview():
    f = Fig('01', 1740, 1080, 'Right hip bone and femur: anterior, posterior and lateral views', '右侧髋骨与股骨：前面观、后面观与外侧面观')
    K = 1120
    a = Stage(f, 'ant', -0.06, -0.73, 330, 620, K)
    a.bones(('hip-bone', 'sacrum', 'coccyx', 'femur'))
    p = Stage(f, 'post', 0.06, -0.73, 850, 620, K)
    p.bones(('sacrum', 'coccyx', 'hip-bone', 'femur'))
    l = Stage(f, 'lat', -0.01, -0.90, 1500, 470, 1900)
    l.bones(('hip-bone',))
    ac = l.P([-0.12, 0.862, -0.004])
    f.raw(f'<circle cx="{ac[0]:.1f}" cy="{ac[1]:.1f}" r="44" fill="#efe4cc" stroke="{BONE_E}" stroke-width="1.6" stroke-dasharray="5 4"/>')
    for x, y, en, zh in [(-0.03, 0.965, 'Ilium', '髂骨'), (-0.03, 0.825, 'Ischium', '坐骨'), (0.035, 0.84, 'Pubis', '耻骨')]:
        q = l.P([-0.12, y, x]); f.bi(q[0], q[1], en, zh, 15, GREY, 'middle', '700')
    f.bi(330, 150, 'Anterior view', '前面观', 18, INK, 'middle', '700')
    f.bi(850, 150, 'Posterior view', '后面观', 18, INK, 'middle', '700')
    f.bi(1500, 150, 'Lateral view of the hip bone', '髋骨外侧面观', 18, INK, 'middle', '700')
    # anterior labels (person's right = image left)
    label(f, 40, 250, 'Iliac crest', '髂嵴', to=a.at('iliac-crest'))
    label(f, 40, 320, 'ASIS', '髂前上棘', to=a.at('asis'))
    label(f, 40, 390, 'AIIS', '髂前下棘', to=a.at('aiis'))
    label(f, 40, 450, 'Femoral head', '股骨头', to=a.at('femoral-head'))
    label(f, 40, 520, 'Greater trochanter', '大转子', to=a.at('greater-trochanter'))
    label(f, 40, 590, 'Femoral neck', '股骨颈', to=a.P([-0.105, 0.845, 0.0]))
    label(f, 40, 660, 'Lesser trochanter', '小转子', to=a.at('lesser-trochanter'))
    label(f, 440, 250, 'Iliac fossa', '髂窝', to=a.P([-0.075, 0.955, 0.0]))
    label(f, 440, 470, 'Pubic tubercle', '耻骨结节', to=a.at('pubic-tubercle'))
    label(f, 440, 560, 'Obturator foramen', '闭孔', to=a.P([-0.045, 0.825, 0.03]))
    label(f, 440, 630, 'Ischiopubic ramus', '坐耻骨支', to=a.P([-0.03, 0.805, 0.02]))
    label(f, 440, 880, 'Adductor tubercle', '收肌结节', to=a.at('adductor-tubercle'))
    # posterior labels (person's right = image right)
    label(f, 985, 250, 'Iliac crest', '髂嵴', to=p.at('iliac-crest'))
    label(f, 690, 320, 'PSIS', '髂后上棘', anchor='end', to=p.at('psis'))
    label(f, 690, 420, 'Greater sciatic notch', '坐骨大切迹', anchor='end', to=p.P([-0.06, 0.885, -0.07]))
    label(f, 690, 600, 'Ischial tuberosity', '坐骨结节', anchor='end', to=p.at('ischial-tuberosity'))
    label(f, 985, 480, 'Greater trochanter', '大转子', to=p.at('greater-trochanter'))
    label(f, 985, 600, 'Intertrochanteric crest', '转子间嵴', to=p.P([-0.115, 0.82, -0.03]))
    label(f, 985, 720, 'Gluteal tuberosity', '臀肌粗隆', to=p.P([-0.118, 0.76, -0.03]))
    label(f, 985, 860, 'Linea aspera', '股骨粗线', to=p.P([-0.085, 0.62, -0.035]))
    # lateral labels
    label(f, 1700, 760, 'Acetabulum', '髋臼', anchor='end', to=(ac[0] + 20, ac[1] + 20))
    label(f, 1330, 470, 'Greater sciatic notch', '坐骨大切迹', anchor='end', to=l.P([-0.12, 0.89, -0.045]))
    label(f, 1330, 560, 'Ischial spine', '坐骨棘', anchor='end', to=l.P([-0.12, 0.86, -0.061]))
    label(f, 1330, 640, 'Lesser sciatic notch', '坐骨小切迹', anchor='end', to=l.P([-0.12, 0.848, -0.064]))
    label(f, 1700, 250, 'ASIS', '髂前上棘', anchor='end', to=l.at('asis'))
    note(f, 1240, 960, ['Sciatic notches + ligaments = foramina (see 02).'], ['坐骨切迹加上韧带围成坐骨大孔、小孔（见图 02）。'])
    f.save('右侧髋骨与股骨')


LABELS = {}  # figure number → O/I legend rows; written to figure-labels.json for content.json diagram labels


def oi_figure(num, name, en, zh, w, h, panels, rows, legend_at):
    f = Fig(num, w, h, en, zh)
    for pnl in panels: panel(f, **pnl)
    key_oi(f, 40, 130)
    legend_oi(f, legend_at[0], legend_at[1], rows)
    LABELS[num] = rows
    f.save(name)
    return f


PELVIS = ('hip-bone', 'sacrum', 'coccyx', 'femur')
POST_C = (0.075, -0.88)


# 3D attachment points (right side). Schematic areas (AN-14), placed on the model bones.
A = {
    'gmax-o': [[-0.088, 1.0, -0.06], [-0.062, 0.985, -0.08], [-0.046, 0.955, -0.088], [-0.033, 0.915, -0.09], [-0.02, 0.875, -0.088], [-0.008, 0.848, -0.08]],
    'gmax-i': [[-0.124, 0.79, -0.03], [-0.119, 0.75, -0.032]],
    'gmed-o': [[-0.12, 0.985, 0.03], [-0.12, 0.998, 0.0], [-0.12, 0.985, -0.03], [-0.12, 0.955, -0.035]],
    'gmed-i': [[-0.15, 0.86, -0.012], [-0.15, 0.84, -0.006]],
    'gmin-o': [[-0.12, 0.93, 0.035], [-0.12, 0.955, 0.012], [-0.12, 0.95, -0.02], [-0.12, 0.925, -0.03]],
    'gmin-i': [[-0.14, 0.855, 0.012], [-0.14, 0.84, 0.014]],
    'tfl-o': [[-0.12, 0.96, 0.05], [-0.118, 0.945, 0.056]],
    'tfl-i': [[-0.108, 0.41, 0.0], [-0.108, 0.40, 0.002]],
    'pir-o': [[-0.03, 0.935, -0.075], [-0.028, 0.905, -0.078]],
    'pir-i': [[-0.135, 0.868, -0.01]],
    'sg-o': [[-0.047, 0.858, -0.062]],
    'oi-o': [[-0.04, 0.84, 0.01], [-0.05, 0.82, 0.0], [-0.035, 0.81, 0.02]],
    'ig-o': [[-0.048, 0.828, -0.05]],
    'gem-i': [[-0.128, 0.853, -0.02]],
    'qf-o': [[-0.058, 0.815, -0.04], [-0.058, 0.80, -0.038]],
    'qf-i': [[-0.112, 0.825, -0.035], [-0.108, 0.805, -0.035]],
    'oe-o': [[-0.04, 0.84, 0.035], [-0.05, 0.822, 0.03], [-0.032, 0.812, 0.04]],
    'oe-i': [[-0.122, 0.858, -0.02]],
    'pm-o': [[-0.028, 1.13, 0.0], [-0.034, 1.09, 0.0], [-0.04, 1.05, 0.0], [-0.044, 1.015, 0.0]],
    'il-o': [[-0.118, 0.985, 0.0], [-0.1, 1.0, 0.0], [-0.075, 0.99, 0.0], [-0.058, 0.965, 0.0]],
    'lt-i': [[-0.083, 0.80, -0.02], [-0.087, 0.79, -0.02]],
    'sar-o': [[-0.119, 0.946, 0.056]],
    'pes-i': [[-0.043, 0.39, -0.008], [-0.046, 0.375, -0.006]],
    'rf-o': [[-0.108, 0.922, 0.036]],
    'rf-i': [[-0.09, 0.465, 0.012], [-0.08, 0.466, 0.012]],
    'pec-o': [[-0.045, 0.858, 0.04], [-0.025, 0.855, 0.05]],
    'pec-i': [[-0.083, 0.782, -0.02], [-0.081, 0.762, -0.022]],
    'al-o': [[-0.018, 0.842, 0.05]],
    'al-i': [[-0.08, 0.68, -0.032], [-0.07, 0.60, -0.034]],
    'ab-o': [[-0.022, 0.83, 0.045], [-0.026, 0.815, 0.04]],
    'ab-i': [[-0.086, 0.76, -0.03], [-0.081, 0.69, -0.031]],
    'am-o': [[-0.022, 0.815, 0.035], [-0.035, 0.80, 0.01], [-0.045, 0.80, -0.03]],
    'am-i': [[-0.105, 0.78, -0.03], [-0.085, 0.65, -0.034], [-0.06, 0.53, -0.036], [-0.034, 0.47, -0.035]],
    'gr-o': [[-0.012, 0.835, 0.05], [-0.022, 0.81, 0.035]],
    'it-o': [[-0.045, 0.80, -0.042]],
    'bf-i': [[-0.11, 0.418, -0.047]],
    'st-o': [[-0.04, 0.805, -0.045]],
    'sm-o': [[-0.052, 0.81, -0.042]],
    'sm-i': [[-0.045, 0.405, -0.045]],
}
LEG = 'Femur', '股骨'


def lab(en, zh, key, x, y, anchor='start'):
    return (en, zh, LM[key] if isinstance(key, str) else key, x, y, anchor)


@fig('03')
def gluteus_maximus():
    oi_figure('03', '臀大肌起点与止点', 'Gluteus maximus: origin and insertion', '臀大肌：起点与止点', 1180, 1000,
              [dict(view='post', center=POST_C, at=(380, 540), K=1850, bones=PELVIS, model=['gluteus-maximus'], clip=(0, 180, 760, 750),
                    attach=[('gluteus-maximus', A['gmax-o'], A['gmax-i'])],
                    labels=[lab('PSIS', '髂后上棘', 'psis', 100, 330, 'start'), lab('Coccyx', '尾骨', 'coccyx', 100, 650),
                            lab('Greater trochanter', '大转子', 'greater-trochanter', 600, 470),
                            lab('Gluteal tuberosity', '臀肌粗隆', [-0.119, 0.75, -0.032], 600, 820)])],
              [('gluteus-maximus', 'posterior ilium, sacrum and coccyx', '髂骨后部、骶骨和尾骨',
                'iliotibial tract and gluteal tuberosity', '髂胫束和臀肌粗隆')],
              (760, 300))


@fig('04')
def gluteus_medius_minimus():
    bones = ('hip-bone', 'femur')
    oi_figure('04', '臀中肌与臀小肌起点与止点', 'Gluteus medius and gluteus minimus: origins and insertions', '臀中肌与臀小肌：起点与止点', 1400, 1000,
              [dict(view='lat', center=(0.0, -0.9), at=(260, 560), K=2100, bones=bones, model=['gluteus-medius'], clip=(20, 200, 480, 700),
                    attach=[('gluteus-medius', A['gmed-o'], A['gmed-i'])], title=('Gluteus medius (lateral view)', '臀中肌（外侧面观）', 210)),
               dict(view='lat', center=(0.0, -0.9), at=(740, 560), K=2100, bones=bones, model=['gluteus-minimus'], ghost=['gluteus-medius'], clip=(500, 200, 480, 700),
                    attach=[('gluteus-minimus', A['gmin-o'], A['gmin-i'])], title=('Gluteus minimus, deep to medius', '臀小肌（在臀中肌深面）', 210))],
              [('gluteus-medius', 'outer ilium between anterior and posterior gluteal lines', '髂骨外面臀前线与臀后线之间', 'lateral surface of greater trochanter', '大转子外侧面'),
               ('gluteus-minimus', 'outer ilium between anterior and inferior gluteal lines', '髂骨外面臀前线与臀下线之间', 'anterior border of greater trochanter', '大转子前缘')],
              (1000, 300))


@fig('05')
def tfl():
    oi_figure('05', '阔筋膜张肌与髂胫束', 'Tensor fasciae latae and the iliotibial tract', '阔筋膜张肌与髂胫束', 1180, 1200,
              [dict(view='lat', center=(0.0, -0.70), at=(330, 640), K=1050, bones=('hip-bone', 'femur', 'tibia', 'fibula', 'patella'),
                    model=['tensor-fasciae-latae'], ghost=['gluteus-maximus'], clip=(0, 180, 700, 960),
                    bands=[('tensor-fasciae-latae', [[-0.14, 0.84, 0.03], [-0.15, 0.84, 0.0]], [[-0.108, 0.41, 0.006], [-0.11, 0.41, -0.006]])],
                    attach=[('tensor-fasciae-latae', A['tfl-o'], A['tfl-i'])],
                    labels=[lab('ASIS', '髂前上棘', 'asis', 520, 250), lab('Iliotibial tract', '髂胫束', [-0.13, 0.62, 0.0], 520, 640),
                            lab("Gerdy's tubercle", 'Gerdy 结节', 'gerdy', 520, 980),
                            lab('Gluteus maximus (outline)', '臀大肌（轮廓）', [-0.1, 0.86, -0.08], 40, 300)])],
              [('tensor-fasciae-latae', 'ASIS and anterior iliac crest', '髂前上棘和髂嵴前部',
                "iliotibial tract → Gerdy's tubercle", '髂胫束 → Gerdy 结节')],
              (720, 300))


@fig('06')
def deep_rotators():
    oi_figure('06', '深层外旋肌起点与止点', 'Deep lateral rotators: origins and insertions', '深层外旋肌：起点与止点', 1500, 1180,
              [dict(view='post', center=(0.085, -0.86), at=(340, 640), K=2150, bones=PELVIS, clip=(10, 250, 650, 800),
                    model=['piriformis', 'superior-gemellus', 'obturator-internus', 'inferior-gemellus', 'quadratus-femoris'],
                    attach=[('piriformis', A['pir-o'], A['pir-i']), ('superior-gemellus', A['sg-o'], A['gem-i']),
                            ('obturator-internus', [[-0.042, 0.842, -0.03]], A['gem-i']),
                            ('inferior-gemellus', A['ig-o'], A['gem-i']), ('quadratus-femoris', A['qf-o'], A['qf-i'])],
                    title=('Posterior view', '后面观', 200)),
               dict(view='ant', center=(-0.085, -0.85), at=(880, 640), K=2150, bones=('hip-bone', 'femur'), clip=(670, 250, 430, 800),
                    model=['obturator-externus'],
                    attach=[('obturator-externus', A['oe-o'], A['oe-i'])],
                    title=('Anterior view', '前面观', 200))],
              [('piriformis', 'anterior sacrum (S2–S4)', '骶骨前面（S2–S4）', 'apex of greater trochanter', '大转子尖'),
               ('superior-gemellus', 'ischial spine', '坐骨棘', 'medial greater trochanter', '大转子内侧面'),
               ('obturator-internus', 'inner obturator membrane', '闭孔膜内面', 'medial greater trochanter', '大转子内侧面'),
               ('inferior-gemellus', 'upper ischial tuberosity', '坐骨结节上部', 'medial greater trochanter', '大转子内侧面'),
               ('quadratus-femoris', 'lateral ischial tuberosity', '坐骨结节外侧缘', 'quadrate tubercle', '股方肌结节'),
               ('obturator-externus', 'outer obturator membrane', '闭孔膜外面', 'trochanteric fossa', '转子窝')],
              (1120, 260))


@fig('07')
def iliopsoas():
    oi_figure('07', '髂腰肌起点与止点', 'Iliopsoas (psoas major and iliacus): origins and insertion', '髂腰肌（腰大肌与髂肌）：起点与止点', 1180, 1150,
              [dict(view='ant', center=(-0.06, -0.93), at=(360, 640), K=1700, bones=('l1', 'l2', 'l3', 'l4', 'l5', 'hip-bone', 'sacrum', 'femur'),
                    clip=(10, 180, 700, 880),
                    bands=[('iliacus', A['il-o'], [[-0.083, 0.805, -0.01], [-0.088, 0.795, -0.01]]),
                           ('psoas-major', A['pm-o'], [[-0.08, 0.81, -0.01], [-0.086, 0.80, -0.01]])],
                    attach=[('psoas-major', A['pm-o'], A['lt-i']), ('iliacus', A['il-o'], A['lt-i'])],
                    labels=[lab('Lesser trochanter', '小转子', 'lesser-trochanter', 40, 960), lab('Iliac fossa', '髂窝', [-0.09, 0.96, 0.0], 40, 600),
                            lab('T12–L4 bodies', 'T12–L4 椎体', [-0.03, 1.11, 0.0], 520, 260)])],
              [('psoas-major', 'T12–L4 bodies, discs, transverse processes', 'T12–L4 椎体、椎间盘、横突', 'lesser trochanter', '小转子'),
               ('iliacus', 'iliac fossa and inner iliac crest', '髂窝和髂嵴内唇', 'lesser trochanter (shared tendon)', '小转子（共同肌腱）')],
              (740, 300))


@fig('08')
def sartorius_rectus():
    oi_figure('08', '缝匠肌与股直肌起点与止点', 'Sartorius and rectus femoris: origins and insertions', '缝匠肌与股直肌：起点与止点', 1180, 1250,
              [dict(view='ant', center=(-0.075, -0.68), at=(360, 700), K=1150, bones=('hip-bone', 'sacrum', 'femur', 'tibia', 'fibula', 'patella'), clip=(0, 180, 740, 1000),
                    bands=[('rectus-femoris', [[-0.104, 0.915, 0.036], [-0.112, 0.915, 0.036]], [[-0.093, 0.465, 0.012], [-0.077, 0.466, 0.012]]),
                           ('sartorius', [[-0.116, 0.95, 0.056], [-0.121, 0.94, 0.056]], [[-0.05, 0.375, -0.006], [-0.04, 0.39, -0.008]])],
                    attach=[('sartorius', A['sar-o'], A['pes-i']), ('rectus-femoris', A['rf-o'], A['rf-i'])],
                    labels=[lab('ASIS', '髂前上棘', 'asis', 40, 300), lab('AIIS', '髂前下棘', 'aiis', 40, 380),
                            lab('Patella', '髌骨', [-0.085, 0.445, 0.015], 600, 960), lab('Pes anserinus', '鹅足', 'pes-anserinus', 600, 1070)])],
              [('sartorius', 'ASIS', '髂前上棘', 'pes anserinus (medial tibia)', '鹅足（胫骨内侧面）'),
               ('rectus-femoris', 'AIIS and above the acetabulum', '髂前下棘和髋臼上沟', 'patella → tibial tuberosity', '髌骨 → 胫骨粗隆')],
              (760, 300))


@fig('09')
def adductors():
    bones = ('hip-bone', 'sacrum', 'femur', 'tibia', 'patella')
    oi_figure('09', '内收肌群起点与止点', 'Adductor group: origins and insertions', '内收肌群：起点与止点', 1560, 1250,
              [dict(view='ant', center=(-0.06, -0.68), at=(270, 700), K=1150, bones=bones, clip=(10, 200, 500, 980),
                    bands=[('pectineus', A['pec-o'], A['pec-i']), ('adductor-longus', [[-0.015, 0.845, 0.05], [-0.021, 0.838, 0.05]], A['al-i']),
                           ('gracilis', A['gr-o'], [[-0.046, 0.375, -0.006], [-0.042, 0.39, -0.008]], 14)],
                    attach=[('pectineus', A['pec-o'], A['pec-i']), ('adductor-longus', A['al-o'], A['al-i']), ('gracilis', A['gr-o'], A['pes-i'])],
                    title=('Superficial layer', '浅层', 220)),
               dict(view='ant', center=(-0.06, -0.68), at=(770, 700), K=1150, bones=bones, clip=(510, 200, 500, 980),
                    bands=[('adductor-magnus', A['am-o'], A['am-i'], 60), ('adductor-brevis', A['ab-o'], A['ab-i'])],
                    attach=[('adductor-brevis', A['ab-o'], A['ab-i']), ('adductor-magnus', A['am-o'], A['am-i'])],
                    title=('Deep layer', '深层', 220))],
              [('pectineus', 'pecten of superior pubic ramus', '耻骨上支耻骨梳', 'pectineal line of femur', '股骨耻骨肌线'),
               ('adductor-longus', 'body of pubis', '耻骨体', 'middle third of linea aspera', '股骨粗线中 1/3'),
               ('gracilis', 'body and inferior ramus of pubis', '耻骨体和耻骨下支', 'pes anserinus', '鹅足'),
               ('adductor-brevis', 'body and inferior ramus of pubis', '耻骨体和耻骨下支', 'upper linea aspera', '股骨粗线上部'),
               ('adductor-magnus', 'ischiopubic ramus, ischial tuberosity', '坐耻骨支、坐骨结节', 'linea aspera, adductor tubercle', '股骨粗线、收肌结节')],
              (1040, 260))


@fig('10')
def hamstrings():
    bones = ('hip-bone', 'sacrum', 'coccyx', 'femur', 'tibia', 'fibula')
    oi_figure('10', '腘绳肌起点与止点', 'Hamstrings: origins and insertions', '腘绳肌：起点与止点', 1180, 1250,
              [dict(view='post', center=(0.075, -0.66), at=(360, 700), K=1150, bones=bones, clip=(0, 180, 740, 1000),
                    bands=[('semimembranosus', [[-0.05, 0.808, -0.042], [-0.056, 0.812, -0.042]], [[-0.048, 0.405, -0.045], [-0.04, 0.405, -0.045]], 22),
                           ('semitendinosus', [[-0.04, 0.80, -0.045], [-0.046, 0.795, -0.045]], [[-0.046, 0.375, -0.006], [-0.042, 0.39, -0.008]], 16),
                           ('biceps-femoris', [[-0.046, 0.80, -0.042], [-0.052, 0.795, -0.042]], [[-0.106, 0.42, -0.047], [-0.112, 0.41, -0.047]], 24)],
                    attach=[('biceps-femoris', A['it-o'], A['bf-i']), ('semitendinosus', A['st-o'], A['pes-i']), ('semimembranosus', A['sm-o'], A['sm-i'])],
                    labels=[lab('Ischial tuberosity', '坐骨结节', 'ischial-tuberosity', 40, 470), lab('Head of fibula', '腓骨头', 'fibular-head', 620, 1050)])],
              [('biceps-femoris', 'ischial tuberosity (long head)', '坐骨结节（长头）', 'head of fibula', '腓骨头'),
               ('semitendinosus', 'ischial tuberosity', '坐骨结节', 'pes anserinus', '鹅足'),
               ('semimembranosus', 'ischial tuberosity (upper lateral)', '坐骨结节上外侧', 'posterior medial tibial condyle', '胫骨内侧髁后面')],
              (760, 300))


LIG, LIG_F = '#7d6a4f', '#e6d7b8'


def lig(f, st, pts, w=16):
    d = 'M' + ' L'.join('%.1f,%.1f' % st.P(p) for p in pts)
    f.raw(f'<path d="{d}" fill="none" stroke="{LIG}" stroke-width="{w + 3}" stroke-linecap="round" stroke-linejoin="round" opacity=".75"/>')
    f.raw(f'<path d="{d}" fill="none" stroke="{LIG_F}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')
    f.raw(f'<path d="{d}" fill="none" stroke="{LIG}" stroke-width="1" stroke-dasharray="2 5" stroke-linecap="round"/>')


@fig('02')
def joint_ligaments():
    f = Fig('02', 1500, 1000, 'Hip joint: capsular ligaments, labrum and ligament of the head', '髋关节：关节囊韧带、髋臼唇与股骨头韧带')
    a = Stage(f, 'ant', -0.085, -0.86, 300, 590, 2000)
    cid = f.id('c02'); f.raw(f'<clipPath id="{cid}"><rect x="20" y="250" width="1000" height="620"/></clipPath><g clip-path="url(#{cid})">')
    a.bones(('hip-bone', 'femur'))
    lig(f, a, [[-0.106, 0.912, 0.036], [-0.118, 0.875, 0.02], [-0.13, 0.842, 0.01]], 13)
    lig(f, a, [[-0.104, 0.912, 0.036], [-0.097, 0.86, 0.02], [-0.094, 0.81, 0.0]], 13)
    lig(f, a, [[-0.05, 0.856, 0.04], [-0.07, 0.835, 0.03], [-0.09, 0.815, 0.0]], 11)
    f.end()
    f.bi(300, 200, 'Anterior view', '前面观', 17, INK, 'middle', '700')
    label(f, 40, 300, 'AIIS', '髂前下棘', GREY, size=13, to=a.at('aiis'))
    label(f, 40, 640, 'Iliofemoral ligament (Y)', '髂股韧带（Y 形）', LIG, to=a.P([-0.116, 0.872, 0.02]))
    label(f, 420, 800, 'Pubofemoral ligament', '耻股韧带', LIG, to=a.P([-0.075, 0.832, 0.03]))
    label(f, 40, 790, 'Intertrochanteric line', '转子间线', GREY, size=13, to=a.P([-0.11, 0.825, 0.0]))
    p = Stage(f, 'post', 0.085, -0.86, 800, 590, 2000)
    f.raw(f'<g clip-path="url(#{cid})">'); p.bones(('hip-bone', 'femur'))
    lig(f, p, [[-0.06, 0.845, -0.045], [-0.09, 0.86, -0.03], [-0.125, 0.86, -0.015]], 12)
    f.end()
    f.bi(800, 200, 'Posterior view', '后面观', 17, INK, 'middle', '700')
    label(f, 640, 830, 'Ischiofemoral ligament', '坐股韧带', LIG, 'start', to=p.P([-0.09, 0.858, -0.03]))
    label(f, 560, 760, 'Ischium', '坐骨', GREY, size=13, to=p.P([-0.05, 0.83, -0.04]))
    # lateral inset: acetabulum, labrum and ligament of the head
    cx, cy = 1250, 520
    f.raw(f'<circle cx="{cx}" cy="{cy}" r="150" fill="{BONE}" stroke="{BONE_E}" stroke-width="2"/>')
    f.raw(f'<path d="M{cx - 70},{cy + 110} A130,130 0 1,1 {cx + 70},{cy + 110}" fill="none" stroke="#3c7a8c" stroke-width="16" stroke-linecap="round" opacity=".85"/>')
    f.raw(f'<path d="M{cx - 70},{cy + 110} A130,130 0 1,1 {cx + 70},{cy + 110}" fill="none" stroke="{BONE_E}" stroke-width="1.6"/>')
    f.raw(f'<path d="M{cx - 105},{cy + 75} A125,125 0 1,1 {cx + 105},{cy + 75}" fill="#efe4cc" stroke="{BONE_E}" stroke-width="1.4" stroke-dasharray="4 4"/>')
    f.raw(f'<path d="M{cx - 30},{cy + 30} Q{cx},{cy - 10} {cx + 30},{cy + 30} L{cx + 40},{cy + 140} L{cx - 40},{cy + 140} Z" fill="#d9c7a6" stroke="{BONE_E}" stroke-width="1.4"/>')
    f.path(f'M{cx},{cy + 20} L{cx},{cy + 135}', '#8c2f39', 6)
    f.bi(cx, 290, 'Acetabulum seen from the side', '从外侧看髋臼', 17, INK, 'middle', '700')
    label(f, 1300, 280 + 470, 'Acetabular labrum', '髋臼唇', '#3c7a8c', 'start', to=(cx + 92, cy - 92))
    label(f, 1060, 880, 'Ligament of the head of the femur', '股骨头韧带', '#8c2f39', 'start', to=(cx, cy + 90))
    label(f, 1060, 360, 'Lunate (articular) surface', '月状面（关节面）', GREY, 'start', size=13, to=(cx - 80, cy - 40))
    label(f, 1300, 840, 'Acetabular fossa', '髋臼窝', GREY, 'start', size=13, to=(cx + 20, cy + 70))
    note(f, 40, 910, ['The three capsular ligaments spiral around the neck and tighten in extension.'],
         ['三条关节囊韧带绕股骨颈呈螺旋走行，伸髋时一起拉紧。'], INK, 14)
    f.save('髋关节韧带与髋臼唇')


NERVE_W = 7


def nerve(f, st, pts, w=NERVE_W, dash=None):
    xy = [st.P(p) for p in pts]
    d = 'M%.1f,%.1f' % xy[0]
    for k in range(1, len(xy) - 1):
        mx, my = (xy[k][0] + xy[k + 1][0]) / 2, (xy[k][1] + xy[k + 1][1]) / 2
        d += ' Q%.1f,%.1f %.1f,%.1f' % (*xy[k], mx, my)
    d += ' L%.1f,%.1f' % xy[-1]
    f.raw(f'<path d="{d}" fill="none" stroke="#8a6a10" stroke-width="{w + 2.5}" stroke-linecap="round" stroke-linejoin="round"' + (f' stroke-dasharray="{dash}"' if dash else '') + '/>')
    f.raw(f'<path d="{d}" fill="none" stroke="{NERVE}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"' + (f' stroke-dasharray="{dash}"' if dash else '') + '/>')
    return xy


def step_cards(f, x, y, steps, w=420):
    yy = y
    for n, (en, zh) in enumerate(steps, 1):
        f.step(x + 14, yy - 6, n)
        f.bi(x + 38, yy, en, zh, 14, INK, 'start', '600', gap=19)
        yy += 64
    return yy


@fig('12')
def posterior_nerves():
    f = Fig('12', 1500, 1180, 'Superior gluteal, inferior gluteal and sciatic nerves: posterior anatomy', '臀上神经、臀下神经与坐骨神经：后面实体解剖')
    st = Stage(f, 'post', 0.08, -0.71, 380, 640, 1150)
    cid = f.id('clip12')
    f.raw(f'<clipPath id="{cid}"><rect x="20" y="170" width="700" height="940"/></clipPath><g clip-path="url(#{cid})">')
    st.bones(('hip-bone', 'sacrum', 'coccyx', 'femur', 'tibia', 'fibula'))
    for mid in ('gluteus-medius', 'piriformis', 'superior-gemellus', 'obturator-internus', 'inferior-gemellus', 'quadratus-femoris'):
        st.muscle(mid, op=0.75)
    st.muscle('gluteus-maximus', op=0.25, dash='6 5')
    sgn = nerve(f, st, [[-0.05, 0.895, -0.07], [-0.08, 0.91, -0.06], [-0.11, 0.925, -0.04], [-0.13, 0.92, 0.0]], 5)
    ign = nerve(f, st, [[-0.05, 0.862, -0.072], [-0.065, 0.855, -0.08], [-0.085, 0.85, -0.09]], 5)
    sci = nerve(f, st, [[-0.045, 0.875, -0.07], [-0.065, 0.855, -0.065], [-0.083, 0.81, -0.05], [-0.085, 0.70, -0.05], [-0.08, 0.53, -0.05]])
    nerve(f, st, [[-0.08, 0.53, -0.05], [-0.072, 0.47, -0.05], [-0.068, 0.40, -0.05]], 5)
    nerve(f, st, [[-0.08, 0.53, -0.05], [-0.098, 0.47, -0.05], [-0.112, 0.42, -0.05]], 4)
    f.end()
    for n, (x, y) in enumerate([sgn[0], sgn[-1], ign[-1], sci[1], sci[2], (st.P([-0.08, 0.53, -0.05]))], 1):
        f.step(x + 18, y - 14, n)
    label(f, 560, 230, 'Superior gluteal nerve', '臀上神经', '#8a6a10', 'start', 14, to=sgn[2])
    label(f, 40, 300, 'Inferior gluteal nerve', '臀下神经', '#8a6a10', 'start', 14, to=ign[1])
    label(f, 40, 650, 'Sciatic nerve', '坐骨神经', '#8a6a10', 'start', 14, to=st.P([-0.085, 0.72, -0.05]))
    label(f, 40, 980, 'Tibial nerve', '胫神经', '#8a6a10', 'start', 14, to=st.P([-0.07, 0.43, -0.05]))
    label(f, 560, 1000, 'Common fibular nerve', '腓总神经', '#8a6a10', 'start', 14, to=st.P([-0.106, 0.44, -0.05]))
    label(f, 40, 430, 'Piriformis', '梨状肌', COLOR['piriformis'], 'start', 14, to=st.P([-0.06, 0.875, -0.07]))
    label(f, 560, 560, 'Gemelli, obturator internus, quadratus femoris', '孖肌、闭孔内肌、股方肌', COLOR['quadratus-femoris'], 'start', 13, to=st.P([-0.09, 0.83, -0.04]))
    label(f, 560, 300, 'Gluteus medius', '臀中肌', COLOR['gluteus-medius'], 'start', 13, to=st.P([-0.11, 0.95, -0.05]))
    label(f, 560, 400, 'Gluteus maximus (transparent)', '臀大肌（半透明）', COLOR['gluteus-maximus'], 'start', 13, to=st.P([-0.12, 0.80, -0.05]))
    f.bi(1000, 200, 'Course, step by step', '走行步骤', 18, INK, 'start', '700')
    step_cards(f, 1000, 250, [
        ('Superior gluteal nerve (L4–S1) leaves the pelvis', '臀上神经（L4–S1）出盆'),
        ('above piriformis; runs between gluteus medius', '于梨状肌上方，在臀中肌与臀小肌之间'),
        ('and minimus to TFL. Inferior gluteal (L5–S2)', '走到阔筋膜张肌。臀下神经（L5–S2）'),
        ('exits below piriformis into gluteus maximus.', '在梨状肌下方出盆，进入臀大肌。'),
        ('Sciatic nerve (L4–S3) exits below piriformis,', '坐骨神经（L4–S3）在梨状肌下方出盆，'),
        ('crosses the deep rotators between the greater', '越过深层外旋肌，经大转子与'),
        ('trochanter and ischial tuberosity, descends', '坐骨结节之间下行，'),
        ('and splits into tibial and common fibular nerves.', '在腘窝上方分为胫神经和腓总神经。')][:0])
    yy = 250
    for n, (en, zh) in enumerate([
            ('Superior gluteal nerve (L4–S1) leaves the pelvis above piriformis.', '臀上神经（L4–S1）在梨状肌上方出盆。'),
            ('It runs between gluteus medius and minimus to TFL.', '它在臀中肌与臀小肌之间走到阔筋膜张肌。'),
            ('Inferior gluteal nerve (L5–S2) exits below piriformis into gluteus maximus.', '臀下神经（L5–S2）在梨状肌下方出盆，进入臀大肌。'),
            ('Sciatic nerve (L4–S3) exits below piriformis.', '坐骨神经（L4–S3）在梨状肌下方出盆。'),
            ('It crosses the gemelli, obturator internus and quadratus femoris,', '它越过孖肌、闭孔内肌和股方肌，'),
            ('then splits above the knee into tibial and common fibular nerves.', '在膝上方分为胫神经和腓总神经。')], 1):
        f.step(1014, yy - 6, n)
        for k, chunk in enumerate(wrap(en, 44)): f.text(1038, yy + k * 18, chunk, 14, INK, weight='600')
        lines = len(wrap(en, 44))
        f.text(1038, yy + lines * 18 + 2, zh, 13, ZH, lang='zh-CN')
        yy += lines * 18 + 40
    note(f, 1000, yy + 20, ['Step 1–2 = superior gluteal; 3 = inferior gluteal;', '4–6 = sciatic nerve.'],
         ['第 1–2 步为臀上神经；第 3 步为臀下神经；', '第 4–6 步为坐骨神经。'], GREY, 13)
    f.save('臀部神经后面实体解剖')


def wrap(text, n):
    words, lines, cur = text.split(), [], ''
    for w in words:
        if len(cur) + len(w) + 1 > n and cur: lines.append(cur); cur = w
        else: cur = (cur + ' ' + w).strip()
    return lines + [cur]


@fig('13')
def anterior_nerves():
    f = Fig('13', 1500, 1180, 'Femoral, obturator and lateral femoral cutaneous nerves: anterior anatomy', '股神经、闭孔神经与股外侧皮神经：前面实体解剖')
    st = Stage(f, 'ant', -0.06, -0.80, 400, 640, 1450)
    cid = f.id('clip13')
    f.raw(f'<clipPath id="{cid}"><rect x="20" y="170" width="740" height="940"/></clipPath><g clip-path="url(#{cid})">')
    st.bones(('l2', 'l3', 'l4', 'l5', 'hip-bone', 'sacrum', 'femur'))
    st.band('iliacus', A['il-o'], [[-0.083, 0.805, -0.01], [-0.088, 0.795, -0.01]], op=0.4)
    st.band('psoas-major', A['pm-o'][1:], [[-0.08, 0.81, -0.01], [-0.086, 0.80, -0.01]], op=0.4)
    a, b = st.at('asis'), st.at('pubic-tubercle')
    f.path(f'M{a[0]:.1f},{a[1]:.1f} Q{(a[0] + b[0]) / 2:.1f},{(a[1] + b[1]) / 2 + 30:.1f} {b[0]:.1f},{b[1]:.1f}', '#6b706a', 3)
    art = [st.P(p) for p in [[-0.075, 0.93, 0.02], [-0.072, 0.87, 0.05], [-0.07, 0.75, 0.04]]]
    f.path('M' + ' L'.join('%.1f,%.1f' % p for p in art), RED, 5, rough=False, op=0.8)
    vein = [(x + 14, y) for x, y in art]
    f.path('M' + ' L'.join('%.1f,%.1f' % p for p in vein), BLUE, 5, rough=False, op=0.7)
    fem = nerve(f, st, [[-0.055, 1.02, 0.0], [-0.07, 0.96, 0.01], [-0.082, 0.91, 0.03], [-0.086, 0.868, 0.05], [-0.09, 0.82, 0.04]], 5)
    for end in ([-0.11, 0.70, 0.03], [-0.085, 0.68, 0.04], [-0.07, 0.62, 0.03]):
        nerve(f, st, [[-0.09, 0.82, 0.04], [(-0.09 + end[0]) / 2, 0.76, 0.04], end], 3)
    obt = nerve(f, st, [[-0.04, 1.0, -0.01], [-0.035, 0.94, -0.01], [-0.04, 0.88, 0.0], [-0.045, 0.848, 0.03], [-0.05, 0.80, 0.03]], 4)
    nerve(f, st, [[-0.05, 0.80, 0.03], [-0.05, 0.72, 0.03], [-0.052, 0.66, 0.02]], 3)
    lfc = nerve(f, st, [[-0.065, 1.0, 0.0], [-0.095, 0.975, 0.02], [-0.112, 0.945, 0.055], [-0.12, 0.90, 0.05], [-0.135, 0.80, 0.04]], 4)
    f.end()
    for n, (x, y) in enumerate([fem[1], fem[3], fem[4], obt[1], obt[3], lfc[2]], 1):
        f.step(x - 20, y - 14, n)
    label(f, 560, 250, 'Femoral nerve', '股神经', '#8a6a10', 'start', 14, to=fem[2])
    label(f, 560, 330, 'Obturator nerve', '闭孔神经', '#8a6a10', 'start', 14, to=obt[2])
    label(f, 40, 300, 'Lateral femoral cutaneous nerve', '股外侧皮神经', '#8a6a10', 'start', 14, to=lfc[1])
    label(f, 40, 420, 'Inguinal ligament', '腹股沟韧带', '#6b706a', 'start', 13, to=((a[0] * 2 + b[0]) / 3, (a[1] * 2 + b[1]) / 3 + 12))
    label(f, 560, 640, 'Femoral artery and vein', '股动脉与股静脉', RED, 'start', 13, to=art[2])
    label(f, 560, 480, 'Obturator canal', '闭膜管', GREY, 'start', 13, to=obt[3])
    label(f, 40, 560, 'Iliacus and psoas major', '髂肌与腰大肌', COLOR['iliacus'], 'start', 13, to=st.P([-0.075, 0.95, 0.0]))
    f.bi(1000, 200, 'Course, step by step', '走行步骤', 18, INK, 'start', '700')
    yy = 250
    for n, (en, zh) in enumerate([
            ('Femoral nerve (L2–L4) leaves the lateral border of psoas major.', '股神经（L2–L4）从腰大肌外侧缘穿出。'),
            ('It passes under the inguinal ligament, lateral to the femoral artery.', '它在腹股沟韧带深面、股动脉外侧通过。'),
            ('In the femoral triangle it splits into muscular and skin branches.', '在股三角内分为肌支和皮支。'),
            ('Obturator nerve (L2–L4) leaves the medial border of psoas major.', '闭孔神经（L2–L4）从腰大肌内侧缘穿出。'),
            ('It runs along the pelvic wall and exits through the obturator canal to the adductors.', '沿盆壁下行，经闭膜管到内收肌群。'),
            ('Lateral femoral cutaneous nerve (L2–L3) passes just medial to the ASIS.', '股外侧皮神经（L2–L3）在髂前上棘内侧穿出。')], 1):
        f.step(1014, yy - 6, n)
        ls = wrap(en, 44)
        for k, chunk in enumerate(ls): f.text(1038, yy + k * 18, chunk, 14, INK, weight='600')
        f.text(1038, yy + len(ls) * 18 + 2, zh, 13, ZH, lang='zh-CN')
        yy += len(ls) * 18 + 40
    note(f, 1000, yy + 20, ['Order in the groin, lateral to medial: nerve, artery, vein (NAV).'],
         ['腹股沟处从外到内：神经、动脉、静脉。'], GREY, 13)
    f.save('股神经与闭孔神经前面实体解剖')


@fig('14')
def lines_of_pull():
    f = Fig('14', 1500, 1060, 'Line of pull and hip actions', '拉力线与髋关节动作')
    def arrows(st, items):
        hc = st.at('femoral-head')
        f.circle(hc[0], hc[1], 9, INK, '#fff', 2)
        for mid, o, i in items:
            oc = centroid([st.P(p) for p in A[o]]); ic = centroid([st.P(p) for p in A[i]])
            f.arrow(f'M{ic[0]:.1f},{ic[1]:.1f} L{oc[0]:.1f},{oc[1]:.1f}', COLOR[mid], 3.4)
        return hc
    l = Stage(f, 'lat', -0.01, -0.76, 330, 590, 1050)
    cid = f.id('clip14')
    f.raw(f'<clipPath id="{cid}"><rect x="20" y="300" width="640" height="620"/></clipPath><g clip-path="url(#{cid})">')
    l.bones(('l3', 'l4', 'l5', 'hip-bone', 'sacrum', 'femur', 'tibia', 'patella'))
    hc = arrows(l, [('psoas-major', 'pm-o', 'lt-i'), ('rectus-femoris', 'rf-o', 'rf-i'), ('sartorius', 'sar-o', 'pes-i'),
                    ('gluteus-maximus', 'gmax-o', 'gmax-i'), ('biceps-femoris', 'it-o', 'bf-i'), ('semimembranosus', 'sm-o', 'sm-i')])
    f.path(f'M{hc[0]:.1f},{hc[1] - 330} L{hc[0]:.1f},{hc[1] + 420}', GREY, 1.4, dash='6 6', rough=False)
    f.end()
    f.bi(330, 200, 'Lateral view: flexors in front, extensors behind', '外侧面观：屈肌在前，伸肌在后', 17, INK, 'middle', '700')
    f.bi(hc[0] + 60, 270, 'Front → flexion', '前方 → 屈', 14, COLOR['rectus-femoris'], 'start', '700')
    f.bi(hc[0] - 60, 270, 'Behind → extension', '后方 → 伸', 14, COLOR['gluteus-maximus'], 'end', '700')
    a = Stage(f, 'ant', -0.07, -0.76, 1000, 590, 1050)
    f.raw(f'<clipPath id="{cid}b"><rect x="700" y="300" width="560" height="620"/></clipPath><g clip-path="url(#{cid}b)">')
    a.bones(('hip-bone', 'sacrum', 'femur', 'tibia', 'patella'))
    hc2 = arrows(a, [('gluteus-medius', 'gmed-o', 'gmed-i'), ('tensor-fasciae-latae', 'tfl-o', 'tfl-i'),
                     ('adductor-longus', 'al-o', 'al-i'), ('gracilis', 'gr-o', 'pes-i'), ('adductor-magnus', 'am-o', 'am-i')])
    f.path(f'M{hc2[0] - 260},{hc2[1]:.1f} L{hc2[0] + 260},{hc2[1]:.1f}', GREY, 1.4, dash='6 6', rough=False)
    f.end()
    f.bi(1000, 200, 'Anterior view: abductors lateral, adductors medial', '前面观：外展肌在外，内收肌在内', 17, INK, 'middle', '700')
    yy = 300
    for mid in ['psoas-major', 'rectus-femoris', 'sartorius', 'gluteus-maximus', 'biceps-femoris', 'semimembranosus',
                'gluteus-medius', 'tensor-fasciae-latae', 'adductor-longus', 'gracilis', 'adductor-magnus']:
        n = name_of(mid)
        f.path(f'M1290,{yy - 6} L1330,{yy - 6}', COLOR[mid], 4, rough=False)
        f.bi(1340, yy, n['en'], n['zh'], 13, COLOR[mid], 'start', '700', gap=16)
        yy += 48
    note(f, 40, 1060 - 115, ['Arrows point from insertion toward origin (direction of pull); the dot is the hip joint centre.'],
         ['箭头从止点指向起点（拉力方向）；圆点是髋关节中心。'], INK, 13)
    f.save('拉力线与髋关节动作')


ACU = {  # schematic surface positions (3D) following GB/T 12346-2021 descriptions; learning reference only (AN-22)
    'GB30': [-0.098, 0.851, -0.09], 'BL54': [-0.07, 0.885, -0.1], 'BL36': [-0.072, 0.77, -0.08], 'BL37': [-0.075, 0.64, -0.07],
    'GB29': [-0.15, 0.892, 0.024], 'GB31': [-0.15, 0.62, -0.01], 'ST31': [-0.112, 0.86, 0.06], 'ST32': [-0.1, 0.594, 0.05],
    'LR11': [-0.035, 0.817, 0.05]}


@fig('19')
def acupoints():
    f = Fig('19', 1560, 1150, 'Acupoints of the hip and thigh over the anatomy', '髋部与大腿穴位与局部解剖叠加图')
    views = [('post', 0.07, 270, ['gluteus-maximus'], ['GB30', 'BL54', 'BL36', 'BL37'], 'Posterior view', '后面观'),
             ('lat', 0.0, 780, ['tensor-fasciae-latae', 'gluteus-medius'], ['GB29', 'GB31'], 'Lateral view', '外侧面观'),
             ('ant', -0.07, 1290, [], ['ST31', 'ST32', 'LR11'], 'Anterior view', '前面观')]
    for view, mx, fx, mus, pts, en, zh in views:
        st = Stage(f, view, mx, -0.74, fx, 620, 1050)
        cid = f.id('c' + view)
        f.raw(f'<clipPath id="{cid}"><rect x="{fx - 250}" y="300" width="500" height="730"/></clipPath><g clip-path="url(#{cid})">')
        st.skin()
        st.bones(('hip-bone', 'sacrum', 'coccyx', 'femur', 'tibia', 'fibula', 'patella') if view != 'lat' else ('hip-bone', 'femur', 'tibia', 'fibula', 'patella'), w=1.2, op=0.55)
        for mid in mus: st.muscle(mid, op=0.45)
        if view == 'ant':
            st.band('sartorius', [[-0.116, 0.95, 0.056], [-0.121, 0.94, 0.056]], [[-0.05, 0.375, -0.006], [-0.04, 0.39, -0.008]], op=0.4)
            st.band('rectus-femoris', [[-0.104, 0.915, 0.036], [-0.112, 0.915, 0.036]], [[-0.093, 0.465, 0.012], [-0.077, 0.466, 0.012]], op=0.4)
            st.band('adductor-longus', [[-0.015, 0.845, 0.05], [-0.021, 0.838, 0.05]], A['al-i'], op=0.4)
        if view == 'post':
            nerve(f, st, [[-0.045, 0.875, -0.07], [-0.065, 0.855, -0.065], [-0.083, 0.81, -0.05], [-0.085, 0.70, -0.05], [-0.08, 0.53, -0.05]], 5)
        if view == 'ant':
            nerve(f, st, [[-0.082, 0.91, 0.03], [-0.086, 0.868, 0.05], [-0.09, 0.82, 0.04]], 4)
            f.path('M' + ' L'.join('%.1f,%.1f' % st.P(p) for p in [[-0.072, 0.87, 0.05], [-0.07, 0.75, 0.04]]), RED, 4, rough=False, op=0.7)
        f.end()
        f.bi(fx, 250, en, zh, 17, INK, 'middle', '700')
        for k, code in enumerate(pts):
            x, y = st.P(ACU[code])
            f.circle(x, y, 8, RED, '#fff', 2.5)
            point = next(p for p in CONTENT_ACU if p['code'] == code)
            side = 1 if (view != 'ant') else -1
            lx = x + side * 70
            f.leader(x + side * 9, y, lx - side * 4, y, RED)
            f.bi(lx, y + 5, code + ' ' + point['name']['en'], point['name']['zh'], 14, RED, 'start' if side > 0 else 'end', '700')
    note(f, 40, 1150 - 100, ['Learning reference: positions follow the GB/T 12346-2021 descriptions on a schematic body; not clinically calibrated, and not a needling depth, direction or path.'],
         ['学习参照：位置按 GB/T 12346-2021 的描述画在示意人体上；未经临床校准，不表示进针深度、方向或路径。'], RED, 13)
    f.save('髋部穴位叠加图')


try:
    CONTENT_ACU = json.loads((Path(__file__).resolve().parent.parent / 'content.json').read_text(encoding='utf-8')).get('acupoints', [])
except Exception:
    CONTENT_ACU = []


for _mod in ('figs_movement', 'figs_nerves'):  # figures kept in their own modules under tools/
    if (Path(__file__).resolve().parent / 'tools' / (_mod + '.py')).exists():
        __import__(_mod).register(fig)


if __name__ == '__main__':
    want = [a for a in sys.argv[1:] if a[:1].isdigit()] or sorted(FIGS)
    for n in want:
        FIGS[n](); print('built', n)
    if '--out' not in sys.argv:
        (Path(__file__).resolve().parent / 'figure-labels.json').write_text(json.dumps(LABELS, ensure_ascii=False, indent=1), encoding='utf-8')
