/**
 * Compute model-based depth and surroundings for the shipped acupoint study references.
 *
 *   node scripts/compute-acupoint-depth.mjs          # write public/acupoint-depth.json
 *   node scripts/compute-acupoint-depth.mjs --check  # recompute, compare with the file, run sanity checks
 *
 * Scope: geometry of the Z-Anatomy / Vanatome GLB meshes only: the bundled muscular and
 * skeletal atlases plus the shoulder add-on (z-anatomy-1.4.0-shoulder-addon.glb: trapezius,
 * latissimus dorsi, teres major, triceps brachii and other shoulder-region muscles, exported
 * by site/build/atlas/ in the same coordinate frame). Skin, subcutaneous fat, fascia, nerves,
 * vessels and bursae are not in the model. The output is a study aid; it is not a needling
 * path, a needling depth or a clinically validated acupoint location.
 *
 * The GLB reader is dependency-free so the check can run without node_modules. It reads
 * node TRS/matrix transforms (including the add-on's mirrored left-side nodes: a 180° rotation
 * with scale -1), non-normalized float32 POSITION with or without byteStride (the bundled
 * atlases interleave at 24 bytes, the add-on packs at 12) and uint8/16/32 indices, and applies
 * the same Matrix4.compose arithmetic as three.js. `--check` proves this by reproducing every
 * ray count and surface distance stored in public/geometry-validation.json, which
 * validate-reference-geometry.mjs produced with three.js GLTFLoader + Raycaster for meshes of
 * all three files.
 */
import { readFile, writeFile } from 'node:fs/promises';
import { isDeepStrictEqual } from 'node:util';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const projectRoot = new URL('../', import.meta.url);
const outputFile = new URL('public/acupoint-depth.json', projectRoot);
const referenceFile = new URL('src/model-references.json', projectRoot);
const dataFile = new URL('src/data.ts', projectRoot);
const modelFile = new URL('src/model.ts', projectRoot);
const referencesTsFile = new URL('src/references.ts', projectRoot);
const geometryValidationFile = new URL('public/geometry-validation.json', projectRoot);
const addonFile = 'z-anatomy-1.4.0-shoulder-addon.glb';
const modelFiles = ['z-anatomy-1.4.0-muscular.glb', 'z-anatomy-1.4.0-skeletal.glb', addonFile];

const SCHEMA_VERSION = 1;
const REACH_M = 0.3; // Rays start 30 cm outside the reference, far outside the body surface.
const DUPLICATE_HIT_M = 1e-6; // Hits closer than this along the ray are one surface crossing.
const PATCH_RADIUS_M = 0.025; // Outer-surface patch used for the surface normal (skin-scale smoothing).
const SENSITIVITY_RADII_M = [0.015, 0.02, 0.025, 0.03];
const NEARBY_LIMIT_CM = 3;
const GAP_STOP_CM = 1.5; // Stop listing layers after an unmodeled gap longer than this.
const MAX_LAYER_DEPTH_CM = 8;
const PROBE_OUTSIDE_CM = 1; // Drawn probe starts this far outside the first modeled surface.
const PROBE_BONE_SHOWN_CM = 1; // Drawn probe shows at most this much of the last (bony) layer.
const PROBE_MARGIN_CM = 0.3;
const DIRECTION_TERM_MIN = 0.45; // Component of the unit vector needed to name a direction.

/**
 * Approach directions are written for the RIGHT side as outward unit vectors (pointing from
 * the reference toward the outside). The model is y-up, +z anterior, right side at x < 0 (see
 * axisConventions), so "lateral" on the right is -x; the left side mirrors x.
 *
 * outerSurface is the first modeled surface the nominal line must meet (an anatomy-ID prefix).
 * patchScope 'part' takes the surface normal from that one mesh; 'muscle' pools every mesh of
 * that muscle on the same side, for a muscle sheet the source model splits into parts.
 */
const pointPlans = {
  SI11: {
    approach: { en: 'Posterior', zh: '后方' },
    nominalOutwardRight: [0, 0, -1],
    outerSurface: 'rotator-cuff-muscles-infraspinatus-muscle',
    patchScope: 'part',
    rationale: {
      en: 'Tianzong lies in the infraspinous fossa; the probe enters from posterior and is turned to run perpendicular to the modeled outer surface (the infraspinatus) over the fossa. In this model the edge of the lower trapezius lies just medial to the probe, so the probe meets the infraspinatus first.',
      zh: '天宗位于冈下窝；探针自后方进入，并按模型外表面（冈下肌）法线调整为垂直于该处外表面。本模型中斜方肌下部的边缘恰在探针内侧，因此探针首先遇到冈下肌。',
    },
  },
  SI12: {
    approach: { en: 'Posterior', zh: '后方' },
    nominalOutwardRight: [0, 0, -1],
    outerSurface: 'trapezius-muscles-',
    patchScope: 'muscle',
    rationale: {
      en: 'Bingfeng lies in the supraspinous fossa above the midpoint of the scapular spine; the probe enters from posterior and is turned to run perpendicular to the modeled outer surface, which is now the trapezius covering the supraspinatus. The source model splits the trapezius into three meshes and the split passes this spot, so the surface normal is taken from all trapezius meshes of that side rather than from one part.',
      zh: '秉风位于肩胛冈中点上方的冈上窝；探针自后方进入，并按模型外表面法线调整为垂直于该处外表面；现在该外表面是覆盖冈上肌的斜方肌。原始模型把斜方肌分成三个网格，分界线正好经过此处，因此表面法线取同侧全部斜方肌网格，而不是其中一部分。',
    },
  },
  SI9: {
    approach: { en: 'Posterior', zh: '后方' },
    nominalOutwardRight: [0, 0, -1],
    outerSurface: 'deltoid-muscles-',
    patchScope: 'part',
    rationale: {
      en: 'Jianzhen lies posteroinferior to the shoulder joint; the probe enters from posterior and is turned to run perpendicular to the modeled outer surface (the posterior deltoid).',
      zh: '肩贞位于肩关节后下方；探针自后方进入，并按模型外表面（三角肌后部）法线调整为垂直于该处外表面。',
    },
  },
  LI15: {
    approach: { en: 'Lateral', zh: '外侧' },
    nominalOutwardRight: [-1, 0, 0],
    outerSurface: 'deltoid-muscles-',
    patchScope: 'part',
    rationale: {
      en: 'Jianyu lies in the hollow between the anterolateral acromion and the greater tubercle; the probe starts from lateral and is turned to run perpendicular to the modeled outer surface (the deltoid). With the arm adducted in this model, that surface faces superolaterally, so the probe runs inferomedially toward the greater tubercle.',
      zh: '肩髃位于肩峰前外侧端与肱骨大结节之间的凹陷；探针自外侧开始，并按模型外表面（三角肌）法线调整为垂直于该处外表面。本模型上臂内收，该处外表面朝向外上方，因此探针向内下方指向大结节。',
    },
  },
  TE14: {
    approach: { en: 'Lateral', zh: '外侧' },
    nominalOutwardRight: [-1, 0, 0],
    outerSurface: 'deltoid-muscles-',
    patchScope: 'part',
    rationale: {
      en: 'Jianliao lies between the posterolateral acromion and the greater tubercle; the probe starts from lateral and is turned to run perpendicular to the modeled outer surface (the deltoid). With the arm adducted in this model, that surface faces superolaterally and posteriorly.',
      zh: '肩髎位于肩峰后外侧角与肱骨大结节之间；探针自外侧开始，并按模型外表面（三角肌）法线调整为垂直于该处外表面。本模型上臂内收，该处外表面朝向外上后方。',
    },
  },
};

/**
 * Structures that standard regional anatomy places in these layers but that this model does
 * not contain. Listed only where the relation is textbook-level and not point-specific depth.
 */
const notModeledByPoint = {
  SI11: [
    { english: 'Suprascapular nerve and vessels', chinese: '肩胛上神经与血管', note: { en: 'Reach the infraspinous fossa deep to the infraspinatus.', zh: '在冈下肌深面进入冈下窝。' } },
    { english: 'Circumflex scapular vessels', chinese: '旋肩胛血管', note: { en: 'Supply the infraspinous region.', zh: '分布于冈下区。' } },
  ],
  SI12: [
    { english: 'Suprascapular nerve and vessels', chinese: '肩胛上神经与血管', note: { en: 'Run in the supraspinous fossa deep to the supraspinatus.', zh: '在冈上肌深面行于冈上窝。' } },
  ],
  SI9: [
    { english: 'Axillary nerve and posterior circumflex humeral vessels', chinese: '腋神经与旋肱后血管', note: { en: 'Pass through the quadrangular space (teres minor, teres major, long head of triceps, humerus).', zh: '穿过四边孔（小圆肌、大圆肌、肱三头肌长头、肱骨围成）。' } },
    { english: 'Axillary fat, vessels and nerves', chinese: '腋窝脂肪、血管与神经', note: { en: 'The source layer description says a deep path here can reach the axilla; the space deep to the modeled muscles is empty in this model.', zh: '资料的层次描述称此处深刺可达腋腔；模型中肌肉深面的这一空间没有建模结构。' } },
  ],
  LI15: [
    { english: 'Subacromial (subdeltoid) bursa', chinese: '肩峰下（三角肌下）滑囊', note: { en: 'Lies between the deltoid and the supraspinatus tendon.', zh: '位于三角肌与冈上肌腱之间。' } },
  ],
  TE14: [],
};
const notModeledEverywhere = {
  en: 'Skin, subcutaneous fat, fascia, nerves, vessels and bursae are not modeled. Muscles come from the bundled atlas plus the shoulder add-on (trapezius, latissimus dorsi, teres major, triceps brachii and other shoulder-region muscles); muscles outside both, such as the intercostal muscles, are not modeled.',
  zh: '模型不含皮肤、皮下脂肪、筋膜、神经、血管和滑囊。肌肉来自自带模型和肩部附加模型（斜方肌、背阔肌、大圆肌、肱三头肌等肩部肌肉）；两者都没有的肌肉（如肋间肌）未建模。',
};
const thoracicWallNote = {
  en: 'Deep to the ribs lie the intercostal muscles, pleura and lung, which are not modeled.',
  zh: '肋的深面为肋间肌、胸膜和肺，模型未包含。',
};

/**
 * The trapezius is one muscle sheet that the source model splits into three meshes, and the
 * model's part boundaries are only approximate (atlas-addon.json mappingNotes: the lower mesh
 * reaches up to about T2 at the midline). Where the probe enters one trapezius mesh close to
 * another, the layer is named as the whole muscle and a note gives the mesh it entered.
 */
const SPLIT_SHEET_NEAR_CM = 0.5;
const splitSheets = {
  'trapezius-muscles-': {
    whole: { english: 'Trapezius', chinese: '斜方肌' },
    en: (crossed, other, distanceCm) => `The source model splits the trapezius into three meshes; here the probe enters the ${crossed} mesh ${distanceCm.toFixed(1)} cm from the ${other} mesh. The model's part boundaries are approximate, so this layer is named as the whole trapezius. Standard descriptions attach the middle fibres to the acromion and the superior crest of the scapular spine and the lower fibres to the medial end of the spine (Kenhub).`,
    zh: (crossed, other, distanceCm) => `原始模型把斜方肌分成三个网格；探针在距${other}网格 ${distanceCm.toFixed(1)} cm 处进入${crossed}网格。模型中各部分的分界只是近似，因此这一层按整块斜方肌命名。标准描述中，中部纤维止于肩峰和肩胛冈上嵴，下部纤维止于肩胛冈内侧端（Kenhub）。`,
  },
};

/**
 * Published layer descriptions for the points, compared with the modeled probe. `muscles` are
 * anatomy-ID prefixes (same side added at run time); each must match a mesh in the model.
 * Only sources that were opened and read are listed (accessed 2026-10-09).
 */
const ACCESSED = '2026-10-09';
const kenhubTrapezius = {
  title: 'Trapezius muscle', publisher: 'Kenhub (Gordana Sendić; reviewed 2023-10-30)', url: 'https://www.kenhub.com/en/library/anatomy/trapezius-muscle', accessed: ACCESSED,
  supports: { en: 'Transverse (middle) fibres insert on the medial margin of the acromion and the superior crest of the scapular spine; ascending (lower) fibres insert by an aponeurosis on a tubercle at the medial end of the spine.', zh: '横部（中部）纤维止于肩峰内侧缘和肩胛冈上嵴；升部（下部）纤维以腱膜止于肩胛冈内侧端的结节。' },
};
const sourceLayersByPoint = {
  SI11: {
    sequence: { en: 'Skin → subcutaneous tissue → trapezius fascia → trapezius → infraspinatus', zh: '皮肤 → 皮下组织 → 斜方肌筋膜 → 斜方肌 → 冈下肌' },
    muscles: [
      { match: 'trapezius-muscles-', english: 'Trapezius', chinese: '斜方肌' },
      { match: 'rotator-cuff-muscles-infraspinatus-muscle', english: 'Infraspinatus', chinese: '冈下肌' },
    ],
    notes: [
      { en: 'In this model the probe meets the infraspinatus without crossing the trapezius: the border of the lower trapezius runs just medial to the probe, outside the first modeled surface. The sources list the trapezius over the infraspinatus at Tianzong, so here the modeled trapezius border falls just short of covering the probe.', zh: '本模型中探针未穿过斜方肌即到达冈下肌：斜方肌下部的边缘就在探针内侧、第一个建模表面之外。资料在天宗处把斜方肌列在冈下肌浅面，模型中的斜方肌边缘在这里恰好没有盖到探针。' },
    ],
    sources: [
      { title: '天宗穴 · 穴位解剖', publisher: '医学百科 (yixue.com), revision 43196', url: 'https://www.yixue.com/%E5%A4%A9%E5%AE%97%E7%A9%B4', accessed: ACCESSED, supports: { en: 'Layers under the point: skin, subcutaneous tissue, trapezius fascia, trapezius, infraspinatus.', zh: '穴下为皮肤、皮下组织、斜方肌筋膜、斜方肌、冈下肌。' } },
      { title: 'Infraspinatus muscle', publisher: 'Kenhub (Gordana Sendić; reviewed 2023-11-03)', url: 'https://www.kenhub.com/en/library/anatomy/infraspinatus-muscle', accessed: ACCESSED, supports: { en: 'The infraspinatus lies on the dorsal surface of the scapula, deep to the trapezius and to parts of the deltoid and latissimus dorsi.', zh: '冈下肌位于肩胛骨背面，在斜方肌及部分三角肌、背阔肌的深面。' } },
    ],
  },
  SI12: {
    sequence: { en: 'Skin → subcutaneous tissue → trapezius fascia → trapezius → supraspinatus', zh: '皮肤 → 皮下组织 → 斜方肌筋膜 → 斜方肌 → 冈上肌' },
    muscles: [
      { match: 'trapezius-muscles-', english: 'Trapezius', chinese: '斜方肌' },
      { match: 'rotator-cuff-muscles-supraspinatus-muscle', english: 'Supraspinatus', chinese: '冈上肌' },
    ],
    notes: [],
    sources: [
      { title: '秉风穴 · 穴位解剖', publisher: '医学百科 (yixue.com), revision 43050', url: 'https://www.yixue.com/%E7%A7%89%E9%A3%8E%E7%A9%B4', accessed: ACCESSED, supports: { en: 'Layers under the point: skin, subcutaneous tissue, trapezius fascia, trapezius, supraspinatus.', zh: '穴下为皮肤、皮下组织、斜方肌筋膜、斜方肌、冈上肌。' } },
      { title: 'Supraspinatus muscle', publisher: 'Kenhub (Niamh Gorman; reviewed 2022-12-05)', url: 'https://www.kenhub.com/en/library/anatomy/supraspinatus-muscle', accessed: ACCESSED, supports: { en: 'The supraspinatus lies deep to the trapezius, superior to the spine of the scapula.', zh: '冈上肌位于斜方肌深面、肩胛冈上方。' } },
      { title: 'Shoulder Pain: The Supraspinatous Muscle, Part 2', publisher: 'Acupuncture Today (Whitfield Reaves, Chad Bong; May 2010)', url: 'https://acupuncturetoday.com/article/32206-shoulder-pain-the-supraspinatous-muscle-part-2', accessed: ACCESSED, supports: { en: 'At SI 12 the path runs through the superficial layer of the trapezius to the supraspinatus, with the supraspinous fossa as the bony floor.', zh: '秉风处经斜方肌浅层到达冈上肌，冈上窝骨面为底。' } },
      kenhubTrapezius,
    ],
  },
  SI9: {
    sequence: { en: 'Skin → subcutaneous tissue → deltoid fascia → deltoid (posterior part) → long head of triceps brachii → teres major → latissimus dorsi (tendon)', zh: '皮肤 → 皮下组织 → 三角肌筋膜 → 三角肌（后部） → 肱三头肌长头 → 大圆肌 → 背阔肌（腱）' },
    muscles: [
      { match: 'deltoid-muscles-', english: 'Deltoid', chinese: '三角肌' },
      { match: 'triceps-brachii-muscles-long-head-of-triceps-brachii', english: 'Triceps brachii · long head', chinese: '肱三头肌长头' },
      { match: 'teres-major-muscles-teres-major-muscle', english: 'Teres major', chinese: '大圆肌' },
      { match: 'latissimus-dorsi-muscles-latissimus-dorsi-muscle', english: 'Latissimus dorsi', chinese: '背阔肌' },
    ],
    notes: [
      { en: 'The model probe passes through the teres minor (the study reference) and then the long head of triceps; the teres major and latissimus dorsi lie inferior to it. This order matches the relations in the anatomy sources (teres minor deep to the deltoid and posterior to the long head of triceps; teres major anterior to the long head and inferior to the teres minor), but the source layer description for Jianzhen runs lower, through the teres major and latissimus dorsi.', zh: '模型探针穿过小圆肌（学习参照所在）后到达肱三头肌长头；大圆肌和背阔肌位于其下方。此顺序符合解剖资料中的关系（小圆肌在三角肌深面、肱三头肌长头后方；大圆肌在长头前方、小圆肌下方），但资料中肩贞的层次路径更低，经过大圆肌和背阔肌。' },
    ],
    sources: [
      { title: '肩贞穴 · 穴位解剖', publisher: '医学百科 (yixue.com), revision 43051', url: 'https://www.yixue.com/%E8%82%A9%E8%B4%9E%E7%A9%B4', accessed: ACCESSED, supports: { en: 'Layers under the point: skin, subcutaneous tissue, deltoid fascia, deltoid, triceps brachii, teres major, latissimus dorsi; the path enters the posterior deltoid, then the long head of triceps, the teres major and the latissimus dorsi (tendon), and may reach the axilla.', zh: '穴下为皮肤、皮下组织、三角肌筋膜、三角肌、肱三头肌、大圆肌、背阔肌；针经三角肌后部，依次入肱三头肌长头、大圆肌和背阔肌（腱），可深达腋腔。' } },
      { title: 'Triceps brachii', publisher: 'Radiopaedia', url: 'https://radiopaedia.org/articles/triceps-brachii?lang=gb', accessed: ACCESSED, supports: { en: 'The teres minor lies posterior to the long head of triceps near its origin; the teres major lies anterior to the long head.', zh: '小圆肌在肱三头肌长头起点附近位于其后方；大圆肌位于长头前方。' } },
      { title: 'Anatomy, Shoulder and Upper Limb, Teres Minor Muscle', publisher: 'StatPearls (Pallavi Juneja, John B. Hubbard; updated 2023-05-08)', url: 'https://www.ncbi.nlm.nih.gov/books/NBK513324/', accessed: ACCESSED, supports: { en: 'The teres minor is deep to the deltoid; the long head of triceps runs inferior to it; the quadrangular space is bounded by the teres minor, teres major, long head of triceps and surgical neck of the humerus.', zh: '小圆肌位于三角肌深面；肱三头肌长头在其下方；四边孔由小圆肌、大圆肌、肱三头肌长头和肱骨外科颈围成。' } },
    ],
  },
};

const ordinals = ['first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth', 'eleventh', 'twelfth'];
const extraNames = {
  // Standard anatomical names for structures outside the shoulder name maps in src/data.ts.
  ...Object.fromEntries(ordinals.map((word, i) => [`skeleton-${word}-rib`, { english: `${word[0].toUpperCase()}${word.slice(1)} rib`, chinese: `第${i + 1}肋` }])),
  ...Object.fromEntries(Array.from({ length: 12 }, (_, i) => [`skeleton-vertebra-t${i + 1}`, { english: `Vertebra T${i + 1}`, chinese: `第${i + 1}胸椎` }])),
  ...Object.fromEntries([3, 4, 5, 6, 7].map(n => [`skeleton-vertebra-c${n}`, { english: `Vertebra C${n}`, chinese: `第${n}颈椎` }])),
  'skeleton-manubrium-of-sternum': { english: 'Manubrium of sternum', chinese: '胸骨柄' },
  'skeleton-body-of-sternum': { english: 'Body of sternum', chinese: '胸骨体' },
  'neck-muscles-omohyoid-muscle': { english: 'Omohyoid', chinese: '肩胛舌骨肌' },
  'neck-muscles-sternocleidomastoid-muscle': { english: 'Sternocleidomastoid', chinese: '胸锁乳突肌' },
  'neck-muscles-scalenus-anterior-muscle': { english: 'Scalenus anterior', chinese: '前斜角肌' },
  'neck-muscles-scalenus-medius-muscle': { english: 'Scalenus medius', chinese: '中斜角肌' },
  'neck-muscles-scalenus-posterior-muscle': { english: 'Scalenus posterior', chinese: '后斜角肌' },
  'neck-muscles-platysma': { english: 'Platysma', chinese: '颈阔肌' },
};
const directionWords = {
  superior: ['Superior', '上方'], inferior: ['Inferior', '下方'],
  medial: ['Medial', '内侧'], lateral: ['Lateral', '外侧'],
  anterior: ['Anterior', '前方'], posterior: ['Posterior', '后方'],
};
const probeRelationWords = {
  deep: ['deeper along the probe', '沿探针更深'],
  superficial: ['more superficial along the probe', '沿探针更浅'],
  level: ['beside the probe', '探针侧旁'],
};

// ---------- small vector helpers ----------
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const scale = (a, s) => [a[0] * s, a[1] * s, a[2] * s];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const length = a => Math.hypot(a[0], a[1], a[2]);
const normalize = a => scale(a, 1 / length(a));
const angleDeg = (a, b) => Math.acos(Math.max(-1, Math.min(1, dot(normalize(a), normalize(b))))) * 180 / Math.PI;
const round = (value, digits) => { const f = 10 ** digits; const r = Math.round(value * f) / f; return Object.is(r, -0) ? 0 : r; };
const roundVec = (v, digits = 7) => v.map(x => round(x, digits));
const cm = metres => round(metres * 100, 2);

// ---------- GLB reading ----------
function compose(t = [0, 0, 0], q = [0, 0, 0, 1], s = [1, 1, 1]) {
  // Same arithmetic as three.js Matrix4.compose; column-major.
  const [x, y, z, w] = q;
  const x2 = x + x, y2 = y + y, z2 = z + z;
  const xx = x * x2, xy = x * y2, xz = x * z2, yy = y * y2, yz = y * z2, zz = z * z2;
  const wx = w * x2, wy = w * y2, wz = w * z2;
  return [
    (1 - (yy + zz)) * s[0], (xy + wz) * s[0], (xz - wy) * s[0], 0,
    (xy - wz) * s[1], (1 - (xx + zz)) * s[1], (yz + wx) * s[1], 0,
    (xz + wy) * s[2], (yz - wx) * s[2], (1 - (xx + yy)) * s[2], 0,
    t[0], t[1], t[2], 1,
  ];
}
const multiply = (a, b) => {
  const out = new Array(16).fill(0);
  for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) for (let k = 0; k < 4; k++) out[c * 4 + r] += a[k * 4 + r] * b[c * 4 + k];
  return out;
};

async function loadGlb(filename) {
  const bytes = await readFile(new URL(`public/models/${filename}`, projectRoot));
  if (bytes.readUInt32LE(0) !== 0x46546c67 || bytes.readUInt32LE(4) !== 2) throw new Error(`${filename}: not a glTF 2.0 binary`);
  const jsonLength = bytes.readUInt32LE(12);
  const json = JSON.parse(bytes.subarray(20, 20 + jsonLength).toString('utf8'));
  if (json.extensionsRequired?.length) throw new Error(`${filename}: unsupported required extensions ${json.extensionsRequired.join(', ')}`);
  const binOffset = 20 + jsonLength + 8;
  const bin = bytes.subarray(binOffset, binOffset + bytes.readUInt32LE(20 + jsonLength));
  const structures = new Map();
  const visit = (index, parent) => {
    const node = json.nodes[index];
    const world = multiply(parent, node.matrix ?? compose(node.translation, node.rotation, node.scale));
    const id = node.extras?.anatomyId;
    if (id && node.mesh !== undefined) {
      const triangles = [];
      for (const primitive of json.meshes[node.mesh].primitives) {
        if ((primitive.mode ?? 4) !== 4) throw new Error(`${id}: only triangle primitives are supported`);
        const accessor = json.accessors[primitive.attributes.POSITION];
        if (accessor.componentType !== 5126 || accessor.type !== 'VEC3' || accessor.normalized || accessor.sparse || accessor.bufferView === undefined) throw new Error(`${id}: unsupported POSITION layout`);
        if (primitive.indices === undefined || primitive.extensions || primitive.targets) throw new Error(`${id}: only indexed primitives without extensions or morph targets are supported`);
        const view = json.bufferViews[accessor.bufferView];
        const stride = view.byteStride ?? 12;
        const base = (view.byteOffset ?? 0) + (accessor.byteOffset ?? 0);
        const vertices = new Float64Array(accessor.count * 3);
        for (let i = 0; i < accessor.count; i++) {
          const o = base + i * stride;
          const x = bin.readFloatLE(o), y = bin.readFloatLE(o + 4), z = bin.readFloatLE(o + 8);
          vertices[i * 3] = world[0] * x + world[4] * y + world[8] * z + world[12];
          vertices[i * 3 + 1] = world[1] * x + world[5] * y + world[9] * z + world[13];
          vertices[i * 3 + 2] = world[2] * x + world[6] * y + world[10] * z + world[14];
        }
        const indexAccessor = json.accessors[primitive.indices];
        const indexView = json.bufferViews[indexAccessor.bufferView];
        const indexBase = (indexView.byteOffset ?? 0) + (indexAccessor.byteOffset ?? 0);
        const size = { 5121: 1, 5123: 2, 5125: 4 }[indexAccessor.componentType];
        if (!size) throw new Error(`${id}: unsupported index type`);
        const indexAt = i => size === 4 ? bin.readUInt32LE(indexBase + i * 4) : size === 2 ? bin.readUInt16LE(indexBase + i * 2) : bin.readUInt8(indexBase + i);
        for (let i = 0; i + 2 < indexAccessor.count; i += 3) {
          for (const v of [indexAt(i), indexAt(i + 1), indexAt(i + 2)]) triangles.push(vertices[v * 3], vertices[v * 3 + 1], vertices[v * 3 + 2]);
        }
      }
      const tris = Float64Array.from(triangles);
      const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
      let signedVolume = 0;
      for (let i = 0; i < tris.length; i += 9) {
        for (let v = 0; v < 9; v += 3) for (let k = 0; k < 3; k++) { min[k] = Math.min(min[k], tris[i + v + k]); max[k] = Math.max(max[k], tris[i + v + k]); }
        signedVolume += tris[i] * (tris[i + 4] * tris[i + 8] - tris[i + 5] * tris[i + 7]) - tris[i + 1] * (tris[i + 3] * tris[i + 8] - tris[i + 5] * tris[i + 6]) + tris[i + 2] * (tris[i + 3] * tris[i + 7] - tris[i + 4] * tris[i + 6]);
      }
      structures.set(id, { id, sourceName: node.extras.sourceName, system: node.extras.anatomySystem, tris, min, max, orientation: Math.sign(signedVolume) || 1 });
    }
    for (const child of node.children ?? []) visit(child, world);
  };
  const identity = compose();
  for (const index of json.scenes[json.scene ?? 0].nodes) visit(index, identity);
  return structures;
}

// ---------- geometry ----------
/** Double-sided Möller–Trumbore, the same tests as three.js Ray.intersectTriangle(..., false). */
function rayHits(origin, direction, tris, near = 0, far = Infinity) {
  const hits = [];
  const [ox, oy, oz] = origin, [dx, dy, dz] = direction;
  for (let i = 0; i < tris.length; i += 9) {
    const ax = tris[i], ay = tris[i + 1], az = tris[i + 2];
    const e1x = tris[i + 3] - ax, e1y = tris[i + 4] - ay, e1z = tris[i + 5] - az;
    const e2x = tris[i + 6] - ax, e2y = tris[i + 7] - ay, e2z = tris[i + 8] - az;
    const nx = e1y * e2z - e1z * e2y, ny = e1z * e2x - e1x * e2z, nz = e1x * e2y - e1y * e2x;
    let ddn = dx * nx + dy * ny + dz * nz, sign;
    if (ddn > 0) sign = 1; else if (ddn < 0) { sign = -1; ddn = -ddn; } else continue;
    const qx = ox - ax, qy = oy - ay, qz = oz - az;
    const b1 = sign * (dx * (qy * e2z - qz * e2y) + dy * (qz * e2x - qx * e2z) + dz * (qx * e2y - qy * e2x));
    if (b1 < 0) continue;
    const b2 = sign * (dx * (e1y * qz - e1z * qy) + dy * (e1z * qx - e1x * qz) + dz * (e1x * qy - e1y * qx));
    if (b2 < 0 || b1 + b2 > ddn) continue;
    const qdn = -sign * (qx * nx + qy * ny + qz * nz);
    if (qdn < 0) continue;
    const t = qdn / ddn;
    if (t < near || t > far) continue;
    hits.push({ t, normal: [nx, ny, nz] });
  }
  return hits.sort((a, b) => a.t - b.t);
}

function closestOnTriangle(p, t, i) {
  // Ericson, Real-Time Collision Detection 5.1.5 (as three.js Triangle.closestPointToPoint).
  const a = [t[i], t[i + 1], t[i + 2]], b = [t[i + 3], t[i + 4], t[i + 5]], c = [t[i + 6], t[i + 7], t[i + 8]];
  const ab = sub(b, a), ac = sub(c, a), ap = sub(p, a);
  const d1 = dot(ab, ap), d2 = dot(ac, ap);
  if (d1 <= 0 && d2 <= 0) return a;
  const bp = sub(p, b), d3 = dot(ab, bp), d4 = dot(ac, bp);
  if (d3 >= 0 && d4 <= d3) return b;
  const vc = d1 * d4 - d3 * d2;
  if (vc <= 0 && d1 >= 0 && d3 <= 0) return add(a, scale(ab, d1 / (d1 - d3)));
  const cp = sub(p, c), d5 = dot(ab, cp), d6 = dot(ac, cp);
  if (d6 >= 0 && d5 <= d6) return c;
  const vb = d5 * d2 - d1 * d6;
  if (vb <= 0 && d2 >= 0 && d6 <= 0) return add(a, scale(ac, d2 / (d2 - d6)));
  const va = d3 * d6 - d5 * d4;
  if (va <= 0 && d4 - d3 >= 0 && d5 - d6 >= 0) return add(b, scale(sub(c, b), (d4 - d3) / ((d4 - d3) + (d5 - d6))));
  const denominator = 1 / (va + vb + vc);
  return add(a, add(scale(ab, vb * denominator), scale(ac, vc * denominator)));
}
function closestPoint(p, tris) {
  let best = Infinity, point = null;
  for (let i = 0; i < tris.length; i += 9) {
    const q = closestOnTriangle(p, tris, i);
    const d = (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2 + (q[2] - p[2]) ** 2;
    if (d < best) { best = d; point = q; }
  }
  return { distance: Math.sqrt(best), point };
}
function windingNumber(p, t) {
  let solidAngle = 0;
  for (let i = 0; i < t.length; i += 9) {
    const a = sub([t[i], t[i + 1], t[i + 2]], p), b = sub([t[i + 3], t[i + 4], t[i + 5]], p), c = sub([t[i + 6], t[i + 7], t[i + 8]], p);
    const la = length(a), lb = length(b), lc = length(c);
    const det = a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0]) + a[2] * (b[0] * c[1] - b[1] * c[0]);
    solidAngle += 2 * Math.atan2(det, la * lb * lc + dot(a, b) * lc + dot(b, c) * la + dot(c, a) * lb);
  }
  return solidAngle / (4 * Math.PI);
}
function rayBox(origin, direction, min, max) {
  let t0 = -Infinity, t1 = Infinity;
  for (let k = 0; k < 3; k++) {
    if (Math.abs(direction[k]) < 1e-15) { if (origin[k] < min[k] || origin[k] > max[k]) return false; continue; }
    let a = (min[k] - origin[k]) / direction[k], b = (max[k] - origin[k]) / direction[k];
    if (a > b) [a, b] = [b, a];
    t0 = Math.max(t0, a); t1 = Math.min(t1, b);
  }
  return t1 >= Math.max(t0, 0);
}
const boxDistance = (p, s) => Math.hypot(...[0, 1, 2].map(k => Math.max(s.min[k] - p[k], 0, p[k] - s.max[k])));

/** Every crossing of the line through `point` along `inward`, as per-structure intervals. */
function lineIntervals(structures, point, inward) {
  const origin = sub(point, scale(inward, REACH_M));
  const intervals = [], irregular = [];
  for (const s of structures.values()) {
    if (!rayBox(origin, inward, s.min, s.max)) continue;
    const raw = rayHits(origin, inward, s.tris, 0, 2 * REACH_M);
    const hits = raw.filter((hit, i) => i === 0 || hit.t - raw[i - 1].t > DUPLICATE_HIT_M); // merge duplicate edge hits
    if (!hits.length) continue;
    if (hits.length % 2) irregular.push({ id: s.id, firstHit: hits[0].t });
    for (let i = 0; i + 1 < hits.length; i += 2) {
      // Parity pairs hits into entry/exit; outward normals must agree (entry faces against the ray).
      const entryFacesRay = dot(hits[i].normal, inward) * s.orientation < 0;
      const exitFacesAway = dot(hits[i + 1].normal, inward) * s.orientation > 0;
      intervals.push({ id: s.id, entry: hits[i].t, exit: hits[i + 1].t, normalsAgree: entryFacesRay && exitFacesAway });
    }
  }
  intervals.sort((a, b) => a.entry - b.entry || a.exit - b.exit);
  return { origin, intervals, irregular: irregular.sort((a, b) => a.firstHit - b.firstHit) };
}

/** Area-weighted outward normal of the outward-facing triangles near `centre` of one or more structures. */
function patchNormal(structureOrList, centre, outwardHint, radius) {
  const list = Array.isArray(structureOrList) ? structureOrList : [structureOrList];
  let sum = [0, 0, 0], count = 0;
  for (const structure of list) {
    const t = structure.tris;
    for (let i = 0; i < t.length; i += 9) {
      const centroid = [(t[i] + t[i + 3] + t[i + 6]) / 3, (t[i + 1] + t[i + 4] + t[i + 7]) / 3, (t[i + 2] + t[i + 5] + t[i + 8]) / 3];
      if (length(sub(centroid, centre)) > radius) continue;
      const e1 = [t[i + 3] - t[i], t[i + 4] - t[i + 1], t[i + 5] - t[i + 2]], e2 = [t[i + 6] - t[i], t[i + 7] - t[i + 1], t[i + 8] - t[i + 2]];
      const areaNormal = scale([e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0]], structure.orientation);
      if (dot(areaNormal, outwardHint) <= 0) continue; // keep the surface facing the outside
      sum = add(sum, areaNormal); count++;
    }
  }
  if (!count) throw new Error(`${list.map(s => s.id).join(', ')}: no outward-facing triangles near ${centre}`);
  return { normal: normalize(sum), triangles: count };
}

/** Every mesh of one side whose ID starts with `prefix` (all parts of a muscle). */
const sameSideParts = (structures, prefix, side) => [...structures.values()].filter(s => s.id.startsWith(prefix) && s.id.endsWith(`-${side}`)).sort((a, b) => a.id.localeCompare(b.id));

// ---------- names and directions ----------
async function loadNameMaps() {
  const source = await readFile(dataFile, 'utf8');
  const block = name => {
    const match = source.match(new RegExp(`export const ${name}: Record<string, string> = \\{([\\s\\S]*?)\\};`));
    if (!match) throw new Error(`src/data.ts: ${name} map not found`);
    return Object.fromEntries([...match[1].matchAll(/'([^']+)':\s*'([^']*)'/g)].map(m => [m[1], m[2]]));
  };
  return { english: block('anatomyEnglish'), chinese: block('anatomyNames') };
}
function nameFor(id, maps, structures) {
  const base = id.replace(/-(right|left)$/, '');
  const english = maps.english[base] ?? extraNames[base]?.english;
  const chinese = maps.chinese[base] ?? extraNames[base]?.chinese ?? '';
  if (english) return { english, chinese };
  const source = structures.get(id)?.sourceName?.replace(/\.(r|l)$/, '').replace(/ muscle$/, '');
  if (!source) throw new Error(`No English name for ${id}`);
  return { english: source, chinese };
}
function describeDirection(vector, side, inward) {
  const v = normalize(vector);
  const components = { superior: v[1], lateral: side === 'right' ? -v[0] : v[0], anterior: v[2], deep: dot(v, inward) };
  const named = [
    [Math.abs(components.superior), components.superior >= 0 ? 'superior' : 'inferior'],
    [Math.abs(components.lateral), components.lateral >= 0 ? 'lateral' : 'medial'],
    [Math.abs(components.anterior), components.anterior >= 0 ? 'anterior' : 'posterior'],
  ].sort((a, b) => b[0] - a[0]).filter(([value], i) => i === 0 || value >= DIRECTION_TERM_MIN).slice(0, 2).map(([, term]) => term);
  const relation = components.deep >= DIRECTION_TERM_MIN ? 'deep' : components.deep <= -DIRECTION_TERM_MIN ? 'superficial' : 'level';
  return {
    terms: named,
    en: named.map((term, i) => i ? directionWords[term][0].toLowerCase() : directionWords[term][0]).join(', '),
    zh: named.map(term => directionWords[term][1]).join('、'),
    probeRelation: relation,
    probeRelationEn: probeRelationWords[relation][0],
    probeRelationZh: probeRelationWords[relation][1],
    components: Object.fromEntries(Object.entries(components).map(([k, value]) => [k, round(value, 3)])),
  };
}
const approachLabel = (outward, side) => {
  const d = describeDirection(outward, side, outward);
  return { en: `From ${d.en.toLowerCase()}`, zh: `自${d.zh}` };
};

// ---------- main computation ----------
const isRib = id => /^skeleton-.*-rib-(right|left)$/.test(id);
const isBone = (id, structures) => structures.get(id)?.system === 'skeletal';

/** Steps 1–3: nominal line → outer-surface patch normal → final axis through the reference. */
function axisFor(structures, P, nominalOutward, patchRadius, key, plan, side) {
  const nominalInward = scale(nominalOutward, -1);
  // 1. The nominal line through the reference meets the outermost modeled surface at Q0.
  const nominal = lineIntervals(structures, P, nominalInward);
  const firstNominal = nominal.intervals[0];
  if (!firstNominal) throw new Error(`${key}: nominal line meets no modeled structure`);
  if (!firstNominal.id.startsWith(plan.outerSurface)) throw new Error(`${key}: the nominal line first meets ${firstNominal.id}, not the planned outer surface ${plan.outerSurface}; review pointPlans`);
  const q0 = add(nominal.origin, scale(nominalInward, firstNominal.entry));
  // 2. Outward surface normal of that structure (or of every part of that muscle) around Q0 sets the axis; the axis passes through P.
  const patchStructures = plan.patchScope === 'muscle' ? sameSideParts(structures, plan.outerSurface, side) : [structures.get(firstNominal.id)];
  const patch = patchNormal(patchStructures, q0, nominalOutward, patchRadius);
  const inward = scale(patch.normal, -1);
  // 3. All crossings along the final axis; depth 0 is the first modeled surface.
  const line = lineIntervals(structures, P, inward);
  const surfaceT = line.intervals[0].entry;
  return { nominalInward, firstNominal, q0, patch, patchStructures, inward, line, surfaceT, surfacePoint: add(line.origin, scale(inward, surfaceT)), referenceDepth: REACH_M - surfaceT };
}

/** Step 4: the layers worth listing, with the reason the list stops. */
function selectLayers(axis) {
  const selected = [];
  let deepestExit = 0, stopReason = 'no-further-structure';
  for (const interval of axis.line.intervals) {
    const entry = interval.entry - axis.surfaceT, exit = interval.exit - axis.surfaceT;
    // A long unmodeled gap is named as such, also when the next structure lies beyond the depth limit.
    if (selected.length && (entry - deepestExit) * 100 > GAP_STOP_CM && deepestExit >= axis.referenceDepth) { stopReason = 'unmodeled-gap'; break; }
    if (entry * 100 > MAX_LAYER_DEPTH_CM) { stopReason = 'max-depth'; break; }
    selected.push({ interval, entry, exit, gapBefore: selected.length ? Math.max(0, entry - deepestExit) : 0, overlap: selected.length ? Math.max(0, Math.min(deepestExit, exit) - entry) : 0 });
    deepestExit = Math.max(deepestExit, exit);
    if (isRib(interval.id)) { stopReason = 'thoracic-wall'; break; }
    if (interval.id.startsWith('appendicular-skeleton-humerus-')) { stopReason = 'humerus'; break; }
  }
  return { selected, stopReason };
}

function computeEntry(key, reference, structures, names) {
  const pointId = key.replace(/-(right|left)$/, '');
  const side = key.endsWith('-right') ? 'right' : 'left';
  const plan = pointPlans[pointId];
  const P = reference.position;
  const mirror = v => side === 'right' ? v : [-v[0], v[1], v[2]];
  const nominalOutward = normalize(mirror(plan.nominalOutwardRight));
  const axis = axisFor(structures, P, nominalOutward, PATCH_RADIUS_M, key, plan, side);
  const { nominalInward, firstNominal, q0, patch, patchStructures, inward, line, surfacePoint, referenceDepth } = axis;
  const depthOf = t => t - axis.surfaceT;
  const entryId = line.intervals[0].id;
  const entryStructures = plan.patchScope === 'muscle' && entryId.startsWith(plan.outerSurface) ? patchStructures : [structures.get(entryId)];
  const entryPatch = patchNormal(entryStructures, surfacePoint, scale(inward, -1), PATCH_RADIUS_M);
  const pointAt = depthM => add(surfacePoint, scale(inward, depthM));

  // 4. Relevant layers (see method text in the output).
  const { selected, stopReason } = selectLayers(axis);
  const layers = selected.map(({ interval, entry, exit, gapBefore, overlap }) => {
    const split = isRib(interval.id) ? null : splitSheetNote(interval.id, pointAt(entry), structures, names);
    const name = split?.name ?? names(interval.id);
    return {
      anatomyId: interval.id,
      english: name.english,
      chinese: name.chinese,
      kind: isBone(interval.id, structures) ? 'bone' : 'muscle',
      entryCm: cm(entry),
      exitCm: cm(exit),
      thicknessCm: cm(exit - entry),
      gapBeforeCm: cm(gapBefore),
      overlapsPreviousCm: cm(overlap),
      containsReference: entry < referenceDepth && referenceDepth < exit,
      normalsAgree: interval.normalsAgree,
      ...(isRib(interval.id) ? { note: thoracicWallNote } : split ? { note: split.note } : {}),
    };
  });

  // Sensitivity: the same construction with other surface-patch sizes.
  const variants = SENSITIVITY_RADII_M.map(radius => {
    const alternative = axisFor(structures, P, nominalOutward, radius, key, plan, side);
    return { radius, referenceDepth: alternative.referenceDepth, sequence: selectLayers(alternative).selected.map(item => item.interval.id) };
  });
  const sequence = layers.map(layer => layer.anatomyId);
  const sensitivity = {
    patchRadiiCm: SENSITIVITY_RADII_M.map(cm),
    referenceDepthCm: { min: cm(Math.min(...variants.map(v => v.referenceDepth))), max: cm(Math.max(...variants.map(v => v.referenceDepth))) },
    layerSequences: [...new Set(variants.map(v => v.sequence.map(id => layers.find(layer => layer.anatomyId === id)?.english ?? names(id).english).join(' → ')))],
    sameLayerSequence: variants.every(v => isDeepStrictEqual(v.sequence, sequence)),
  };
  const referenceLayer = layers.find(layer => layer.anatomyId === reference.anatomyId && layer.containsReference);
  const last = layers.at(-1);
  const probeEnd = last.kind === 'bone' ? Math.min(last.exitCm, last.entryCm + PROBE_BONE_SHOWN_CM) : last.exitCm;
  const firstBone = layers.find(layer => layer.kind === 'bone');
  let firstBoneSurface;
  if (firstBone) {
    const bonePoint = add(surfacePoint, scale(inward, firstBone.entryCm / 100));
    const bonePatch = patchNormal(structures.get(firstBone.anatomyId), bonePoint, scale(inward, -1), PATCH_RADIUS_M);
    firstBoneSurface = { anatomyId: firstBone.anatomyId, angleToSurfaceNormalDeg: round(angleDeg(bonePatch.normal, scale(inward, -1)), 1) };
  }

  // 5. Nearby structures: nearest surface of every other structure within NEARBY_LIMIT_CM.
  const nearby = [];
  const alsoInside = [];
  for (const s of structures.values()) {
    if (s.id === reference.anatomyId || boxDistance(P, s) * 100 > NEARBY_LIMIT_CM) continue;
    const { distance, point } = closestPoint(P, s.tris);
    if (distance * 100 > NEARBY_LIMIT_CM) continue;
    const inside = Math.abs(windingNumber(P, s.tris)) > 0.5;
    const name = names(s.id);
    if (inside) alsoInside.push(s.id);
    nearby.push({
      anatomyId: s.id,
      english: name.english,
      chinese: name.chinese,
      kind: isBone(s.id, structures) ? 'bone' : 'muscle',
      distanceCm: inside ? 0 : cm(distance),
      overlapsReference: inside,
      direction: inside ? null : describeDirection(sub(point, P), side, inward),
      closestPoint: roundVec(point),
    });
  }
  nearby.sort((a, b) => a.distanceCm - b.distanceCm || a.anatomyId.localeCompare(b.anatomyId));

  const limitations = [
    { en: 'Depths start at the first modeled surface (outer muscle or bone), not at the skin. Skin and subcutaneous fat are not in the model, so a depth from the skin would be larger and varies between people.', zh: '深度从第一个建模表面（肌肉或骨的外表面）起算，而不是从皮肤起算。模型不含皮肤和皮下脂肪，从皮肤量起的深度会更大，并且因人而异。' },
    notModeledEverywhere,
    { en: 'One adult atlas in a fixed pose (arm adducted). Standard locations for some of these points use abduction or other positions, which change the relations shown here.', zh: '单一成人模型、固定姿势（上臂内收）。部分穴位的标准定位使用外展等姿势，姿势改变会改变此处显示的关系。' },
    { en: 'This probe is a geometric study axis through the model reference. It is not a needling path, needling direction or needling depth.', zh: '此探针是穿过模型参照点的几何学习轴线，不是进针路径、进针方向或进针深度。' },
  ];
  const overlaps = layers.filter(layer => layer.overlapsPreviousCm > 0);
  if (overlaps.length || alsoInside.length) {
    limitations.push({
      en: `Source meshes interpenetrate here (${[...new Set([...overlaps.map(l => l.english), ...alsoInside.map(id => names(id).english)])].join(', ')}); overlapping ranges are shown as modeled, not as real tissue sharing space.`,
      zh: `此处原始网格存在互相穿插（${[...new Set([...overlaps.map(l => l.chinese || l.english), ...alsoInside.map(id => names(id).chinese || names(id).english)])].join('、')}）；重叠范围按模型显示，不代表真实组织共占同一空间。`,
    });
  }

  return {
    pointId,
    side,
    referenceAnatomyId: reference.anatomyId,
    referencePosition: roundVec(P),
    axis: {
      approach: plan.approach,
      rationale: plan.rationale,
      method: 'outer-surface-normal',
      nominalOutward: roundVec(nominalOutward, 6),
      nominalSurface: { anatomyId: firstNominal.id, point: roundVec(q0), patchRadiusCm: cm(PATCH_RADIUS_M), triangles: patch.triangles, patchScope: plan.patchScope, patchStructures: patchStructures.map(item => item.id) },
      directionInward: roundVec(inward, 6),
      origin: roundVec(surfacePoint),
      originDescription: { en: 'First modeled surface along the axis (depth 0)', zh: '轴线上第一个建模表面（深度 0）' },
      approachLabel: approachLabel(scale(inward, -1), side),
      angleFromNominalDeg: round(angleDeg(inward, nominalInward), 1),
      angleToEntrySurfaceNormalDeg: round(angleDeg(entryPatch.normal, scale(inward, -1)), 1),
      referenceOffsetMm: round(length(sub(P, add(surfacePoint, scale(inward, referenceDepth)))) * 1000, 3),
      probeStartCm: -PROBE_OUTSIDE_CM,
      probeEndCm: round(probeEnd + PROBE_MARGIN_CM, 2),
      layerStopReason: stopReason,
      sensitivity,
      ...(firstBoneSurface ? { firstBoneSurface } : {}),
      // Structures with an odd number of crossings (open or self-touching meshes) along the whole line.
      irregularStructures: line.irregular.map(item => ({ anatomyId: item.id, firstHitCm: cm(depthOf(item.firstHit)) })),
    },
    referenceDepthCm: cm(referenceDepth),
    referenceLayer: referenceLayer ? { anatomyId: referenceLayer.anatomyId, english: referenceLayer.english, chinese: referenceLayer.chinese } : null,
    layers,
    alsoInsideReference: alsoInside.sort(),
    nearby,
    notModeled: notModeledByPoint[pointId],
    sourceComparison: compareWithSources(pointId, side, layers, { surfacePoint, inward, probeStartCm: -PROBE_OUTSIDE_CM }, structures, names),
    limitations,
  };
}

/**
 * For a layer that is one mesh of a split muscle sheet, entered next to another part: the whole
 * muscle's name and a note naming the mesh. Null when the probe enters the mesh away from the split.
 */
function splitSheetNote(id, entryPoint, structures, names) {
  const prefix = Object.keys(splitSheets).find(item => id.startsWith(item));
  if (!prefix) return null;
  const side = id.endsWith('-right') ? 'right' : 'left';
  let nearest = null;
  for (const other of sameSideParts(structures, prefix, side)) {
    if (other.id === id) continue;
    const { distance } = closestPoint(entryPoint, other.tris);
    if (!nearest || distance < nearest.distance) nearest = { id: other.id, distance };
  }
  if (!nearest || nearest.distance * 100 > SPLIT_SHEET_NEAR_CM) return null;
  const distanceCm = round(nearest.distance * 100, 1);
  const crossed = names(id), other = names(nearest.id);
  return { name: splitSheets[prefix].whole, note: {
    en: splitSheets[prefix].en(crossed.english.toLowerCase(), other.english.toLowerCase(), distanceCm),
    zh: splitSheets[prefix].zh(crossed.chinese || crossed.english, other.chinese || other.english, distanceCm),
  } };
}

/**
 * Compare the probe with a published layer description: each listed muscle is either on the
 * probe (depth range) or not (closest approach of the axis between the probe start and the
 * layer depth limit, with its direction).
 */
function compareWithSources(pointId, side, layers, axis, structures, names) {
  const plan = sourceLayersByPoint[pointId];
  if (!plan) return null;
  const SAMPLE_CM = 0.05;
  const muscles = plan.muscles.map(muscle => {
    const parts = sameSideParts(structures, muscle.match, side);
    if (!parts.length) throw new Error(`${pointId}-${side}: source muscle ${muscle.match} matches no mesh`);
    const onProbe = layers.filter(layer => layer.anatomyId.startsWith(muscle.match));
    const base = { match: muscle.match, english: muscle.english, chinese: muscle.chinese, anatomyIds: parts.map(part => part.id) };
    if (onProbe.length) return { ...base, onProbe: true, layerIds: onProbe.map(layer => layer.anatomyId), entryCm: Math.min(...onProbe.map(l => l.entryCm)), exitCm: Math.max(...onProbe.map(l => l.exitCm)) };
    let best = null;
    for (let depthCm = axis.probeStartCm; depthCm <= MAX_LAYER_DEPTH_CM + 1e-9; depthCm = round(depthCm + SAMPLE_CM, 2)) {
      const p = add(axis.surfacePoint, scale(axis.inward, depthCm / 100));
      for (const part of parts) {
        if (best && boxDistance(p, part) >= best.distance) continue;
        const { distance, point } = closestPoint(p, part.tris);
        if (!best || distance < best.distance) best = { distance, point, p, depthCm, id: part.id };
      }
    }
    return { ...base, onProbe: false, closestPartId: best.id, closestPartEnglish: names(best.id).english, distanceToProbeCm: cm(best.distance), atProbeDepthCm: best.depthCm, direction: describeDirection(sub(best.point, best.p), side, axis.inward) };
  });
  const onProbeOrder = muscles.filter(m => m.onProbe);
  const inSourceOrder = onProbeOrder.every((m, i) => !i || m.entryCm >= onProbeOrder[i - 1].entryCm);
  const listed = muscles.flatMap(m => m.onProbe ? m.layerIds : []);
  // Muscles the probe crosses before the first bone that the description does not list (the descriptions end at the bone).
  const firstBoneEntry = layers.find(layer => layer.kind === 'bone')?.entryCm ?? Infinity;
  const modelOnly = layers.filter(layer => layer.kind === 'muscle' && layer.entryCm < firstBoneEntry && !listed.includes(layer.anatomyId)).map(layer => ({ anatomyId: layer.anatomyId, english: layer.english, chinese: layer.chinese, entryCm: layer.entryCm, exitCm: layer.exitCm }));
  return {
    sequence: plan.sequence,
    agreement: onProbeOrder.length === muscles.length && inSourceOrder ? 'same-order' : 'differs',
    muscles,
    modelOnlyMuscles: modelOnly,
    notes: plan.notes ?? [],
    sources: plan.sources,
  };
}

async function readConstants() {
  const model = await readFile(modelFile, 'utf8');
  const refs = await readFile(referencesTsFile, 'utf8');
  const modelVersion = model.match(/modelVersion = '([^']+)'/)?.[1];
  const referenceVersion = refs.match(/referenceVersion = '([^']+)'/)?.[1];
  if (!modelVersion || !referenceVersion) throw new Error('modelVersion / referenceVersion not found in src/model.ts / src/references.ts');
  return { modelVersion, referenceVersion };
}

async function modelFileHashes() {
  const { createHash } = await import('node:crypto');
  return Promise.all(modelFiles.map(async file => ({ file, sha256: createHash('sha256').update(await readFile(new URL(`public/models/${file}`, projectRoot))).digest('hex') })));
}

async function loadAll() {
  const structures = new Map();
  for (const [filename, meshes] of (await Promise.all(modelFiles.map(async filename => [filename, await loadGlb(filename)])))) {
    for (const [id, structure] of meshes) {
      if (structures.has(id)) throw new Error(`${filename}: ${id} already comes from another model file`);
      structures.set(id, { ...structure, file: filename });
    }
  }
  return structures;
}

/** Determine the model axes from landmarks instead of assuming them; throws if any check fails. */
function verifyAxisConventions(structures) {
  const centre = id => {
    const s = structures.get(id);
    if (!s) throw new Error(`Axis check: ${id} missing`);
    return s.min.map((v, k) => (v + s.max[k]) / 2);
  };
  const f = v => round(v, 3).toFixed(3);
  const manubrium = centre('skeleton-manubrium-of-sternum'), sternum = centre('skeleton-body-of-sternum');
  const c7 = centre('skeleton-vertebra-c7'), sacrum = centre('skeleton-sacrum'), t4 = centre('skeleton-vertebra-t4');
  const rectus = centre('rectus-abdominis-rectus-abdominis-muscle-right'), gluteus = centre('superficial-gluteal-muscles-gluteus-maximus-muscle-right');
  const thumb = centre('appendicular-skeleton-first-metacarpal-bone-right'), little = centre('appendicular-skeleton-fifth-metacarpal-bone-right');
  const sided = [...structures.values()].filter(s => /\.(r|l)$/.test(s.sourceName ?? ''));
  const wrongSide = sided.filter(s => {
    const x = (s.min[0] + s.max[0]) / 2;
    return s.sourceName.endsWith('.r') ? !(x < 0 && s.id.endsWith('-right')) : !(x > 0 && s.id.endsWith('-left'));
  });
  const checks = [
    [manubrium[1] > sternum[1] && c7[1] > sacrum[1], `Superior +y: manubrium of sternum (y ${f(manubrium[1])}) above body of sternum (y ${f(sternum[1])}); vertebra C7 (y ${f(c7[1])}) above sacrum (y ${f(sacrum[1])}).`],
    [sternum[2] > t4[2] && rectus[2] > gluteus[2], `Anterior +z: body of sternum z ${f(sternum[2])} versus vertebra T4 z ${f(t4[2])}; rectus abdominis z ${f(rectus[2])} versus gluteus maximus z ${f(gluteus[2])}.`],
    [wrongSide.length === 0, `Right side x < 0: all ${sided.length} sided meshes agree (Z-Anatomy source names ending ".r" and anatomy IDs ending "-right" lie at x < 0; ".l"/"-left" at x > 0). With +y up and +z anterior in a right-handed glTF frame, the subject's right is forward × up = -x, so names and geometry agree (no mirroring).`],
    [thumb[0] < little[0], `Anatomical position: on the right hand the first metacarpal (thumb, x ${f(thumb[0])}) lies lateral to the fifth (x ${f(little[0])}).`],
  ];
  const failed = checks.filter(([ok]) => !ok);
  if (failed.length) throw new Error(`Axis convention check failed: ${failed.map(([, text]) => text).join(' ')} ${wrongSide.map(s => s.id).join(', ')}`);
  return { up: '+y', anterior: '+z', rightSide: 'x < 0', leftSide: 'x > 0', lateralRight: '-x', lateralLeft: '+x', verifiedBy: checks.map(([, text]) => text) };
}

export async function computeDepth(structures) {
  const references = JSON.parse(await readFile(referenceFile, 'utf8'));
  const maps = await loadNameMaps();
  const names = id => nameFor(id, maps, structures);
  const { modelVersion, referenceVersion } = await readConstants();
  const keys = Object.keys(pointPlans).flatMap(id => ['right', 'left'].map(side => `${id}-${side}`));
  const points = {};
  for (const key of keys) {
    if (!references[key]) throw new Error(`${key}: missing in src/model-references.json`);
    points[key] = computeEntry(key, references[key], structures, names);
  }
  return {
    schemaVersion: SCHEMA_VERSION,
    modelVersion,
    referenceVersion,
    generatedBy: 'scripts/compute-acupoint-depth.mjs',
    scope: {
      en: 'Model-based study reference. Not a needling path or needling depth. Distances come from one anatomical atlas and are not clinical measurements.',
      zh: '模型学习参照，不是进针路径或进针深度。距离来自单一解剖模型，不是临床测量值。',
    },
    units: {
      positions: 'original-model-metres-y-up (before modelScale 7 and modelPosition [0, -6.1, 0])',
      distances: 'centimetres = original model metres × 100, measured along the probe axis from the first modeled surface (depth 0)',
    },
    modelFiles: await modelFileHashes(),
    axisConventions: verifyAxisConventions(structures),
    method: {
      axis: 'For each point a documented approach direction (posterior for SI11, SI12, SI9; lateral for LI15, TE14; mirrored for the left side) is cast through the model reference. Where that line first meets a modeled surface, the area-weighted outward normal of that structure\'s outward-facing triangles within 2.5 cm (a skin-scale patch) sets the probe direction, and the probe passes exactly through the reference. For SI12 that first surface is the trapezius, which the source model splits into three meshes along a boundary that passes the point, so the patch takes all trapezius meshes of that side (axis.nominalSurface.patchStructures). This approximates "perpendicular to the body surface" using the outer muscle surface, because skin is not modeled. The same construction with 1.5–3 cm patches is recorded under axis.sensitivity.',
      crossings: 'Rays start 30 cm outside the reference. Every triangle of every muscle and bone mesh is tested double-sided (Möller–Trumbore); hits closer than 1e-6 m along the ray are merged; per-structure hits are paired into entry/exit by parity and checked against outward triangle normals.',
      layers: `Layers are listed from depth 0 until the axis crosses a rib (thoracic wall) or the humerus, or until the next modeled structure starts more than ${GAP_STOP_CM} cm beyond the deepest layer so far (after the reference), with an ${MAX_LAYER_DEPTH_CM} cm limit. Where the axis enters one trapezius mesh within ${SPLIT_SHEET_NEAR_CM} cm of another, the layer is named as the whole trapezius (the source model's part boundaries are approximate) and its note names the mesh entered.`,
      sourceComparison: `For SI11, SI12 and SI9 a published layer description (sources listed with each point, accessed ${ACCESSED}) is compared with the probe: each listed muscle is either on the probe, with its depth range, or not, with the closest approach of the axis between ${-PROBE_OUTSIDE_CM} cm and ${MAX_LAYER_DEPTH_CM} cm depth (sampled every 0.05 cm) and its direction. The comparison is a study note; neither the sources nor the model are clinical measurements.`,
      nearby: `For every other structure, the nearest surface point to the reference (exhaustive triangle search) within ${NEARBY_LIMIT_CM} cm. Direction names use the components of the unit vector reference→nearest point: the largest anatomical component and a second one if it is at least ${DIRECTION_TERM_MIN}; "deeper/more superficial along the probe" uses the component along the probe axis with the same threshold. A structure whose mesh also contains the reference (winding number) is listed as overlapping.`,
      loaderCheck: 'npm script test:depth reproduces every ray count and surface distance in public/geometry-validation.json (made with three.js, including the shoulder add-on meshes near each reference) before checking this file.',
    },
    points,
  };
}

// ---------- check mode ----------
async function crossCheckLoader(structures) {
  const validation = JSON.parse(await readFile(geometryValidationFile, 'utf8'));
  const directions = [[1, 0.131, 0.173], [-0.239, 1, 0.317], [0.419, -0.227, 1], [-1, 0.371, -0.193], [0.271, -1, 0.413], [-0.337, 0.233, -1], [0.521, 0.677, -0.439]].map(normalize);
  const problems = [];
  let compared = 0, addonCompared = 0;
  for (const result of validation.results) {
    const side = result.id.endsWith('-right') ? 'right' : 'left';
    for (const [field, id] of [['muscle', result.anatomyId], ['scapula', `appendicular-skeleton-scapula-${side}`], ['humerus', `appendicular-skeleton-humerus-${side}`]]) {
      const tris = structures.get(id).tris;
      const counts = directions.map(direction => {
        const hits = rayHits(result.position, direction, tris, 1e-6).map(hit => hit.t);
        return hits.filter((t, i) => i === 0 || t - hits[i - 1] > 1e-6).length;
      });
      const distance = Number(closestPoint(result.position, tris).distance.toFixed(9));
      compared++;
      if (!isDeepStrictEqual(counts, result[field].rayIntersectionCounts) || Math.abs(distance - result[field].distanceToSurfaceMetres) > 2e-9) {
        problems.push(`${result.id} ${field}: rays ${counts} vs ${result[field].rayIntersectionCounts}, distance ${distance} vs ${result[field].distanceToSurfaceMetres}`);
      }
    }
    // Add-on meshes near this reference (both mirrored left and unmirrored right nodes are covered).
    for (const measured of result.addonMeshes ?? []) {
      const structure = structures.get(measured.anatomyId);
      if (!structure || structure.file !== addonFile) { problems.push(`${result.id}: add-on mesh ${measured.anatomyId} not read from ${addonFile}`); continue; }
      const counts = directions.map(direction => {
        const hits = rayHits(result.position, direction, structure.tris, 1e-6).map(hit => hit.t);
        return hits.filter((t, i) => i === 0 || t - hits[i - 1] > 1e-6).length;
      });
      const distance = Number(closestPoint(result.position, structure.tris).distance.toFixed(9));
      compared++;
      if (!isDeepStrictEqual(counts, measured.rayIntersectionCounts) || Math.abs(distance - measured.distanceToSurfaceMetres) > 2e-9) {
        problems.push(`${result.id} ${measured.anatomyId}: rays ${counts} vs ${measured.rayIntersectionCounts}, distance ${distance} vs ${measured.distanceToSurfaceMetres}`);
      }
    }
    addonCompared += result.addonMeshes?.length ?? 0;
  }
  if (!addonCompared) problems.push('public/geometry-validation.json has no add-on measurements: run `node scripts/validate-reference-geometry.mjs --write`');
  return { compared, addonCompared, problems };
}

function sanityCheck(data) {
  const problems = [];
  const expect = (condition, message) => { if (!condition) problems.push(message); };
  for (const [key, entry] of Object.entries(data.points)) {
    expect(entry.layers.length >= 2, `${key}: fewer than 2 layers`);
    expect(entry.layers[0]?.entryCm === 0, `${key}: first layer does not start at depth 0`);
    entry.layers.forEach((layer, i) => {
      expect(layer.exitCm > layer.entryCm, `${key}: ${layer.anatomyId} exit is not deeper than entry`);
      expect(Math.abs(layer.thicknessCm - (layer.exitCm - layer.entryCm)) <= 0.011, `${key}: ${layer.anatomyId} thickness mismatch`);
      expect(layer.english, `${key}: ${layer.anatomyId} has no English name`);
      expect(layer.normalsAgree, `${key}: ${layer.anatomyId} entry/exit disagrees with triangle normals`);
      if (i) expect(layer.entryCm >= entry.layers[i - 1].entryCm, `${key}: layers not ordered by depth`);
    });
    const own = entry.layers.find(layer => layer.anatomyId === entry.referenceAnatomyId);
    expect(own && own.entryCm < entry.referenceDepthCm && entry.referenceDepthCm < own.exitCm, `${key}: reference depth ${entry.referenceDepthCm} cm is not inside ${entry.referenceAnatomyId}`);
    expect(entry.referenceLayer?.anatomyId === entry.referenceAnatomyId, `${key}: reference layer does not match the labeled structure`);
    expect(entry.axis.referenceOffsetMm <= 1, `${key}: axis misses the reference by ${entry.axis.referenceOffsetMm} mm`);
    expect(Math.abs(length(entry.axis.directionInward) - 1) < 1e-5, `${key}: axis direction is not a unit vector`);
    expect(entry.axis.nominalSurface.anatomyId.startsWith(pointPlans[entry.pointId].outerSurface), `${key}: the axis was set by ${entry.axis.nominalSurface.anatomyId}, not the documented outer surface ${pointPlans[entry.pointId].outerSurface}`);
    const comparison = entry.sourceComparison;
    expect(Boolean(comparison) === Boolean(sourceLayersByPoint[entry.pointId]), `${key}: source comparison missing or unexpected`);
    if (comparison) {
      expect(comparison.sources.length > 0 && comparison.sources.every(source => source.title && /^https:\/\//.test(source.url) && source.accessed && source.supports?.en && source.supports?.zh), `${key}: every compared source needs a title, https URL, access date and bilingual summary`);
      for (const muscle of comparison.muscles) {
        expect(muscle.anatomyIds.length > 0 && muscle.anatomyIds.every(id => id.endsWith(`-${entry.side}`)), `${key}: ${muscle.match} has no mesh on this side`);
        if (muscle.onProbe) expect(muscle.layerIds.every(id => entry.layers.some(layer => layer.anatomyId === id)), `${key}: ${muscle.match} on-probe layers not in the layer list`);
        else expect(muscle.distanceToProbeCm > 0 && !entry.layers.some(layer => layer.anatomyId.startsWith(muscle.match)), `${key}: ${muscle.match} is marked off the probe but crosses it`);
      }
    }
    const notModeledNames = entry.notModeled.map(item => item.english.toLowerCase());
    const modeledMuscleNames = entry.layers.concat(entry.nearby).filter(item => item.kind === 'muscle').map(item => item.english.toLowerCase().split(' · ')[0]);
    expect(!notModeledNames.some(name => modeledMuscleNames.includes(name)), `${key}: a structure listed as not modeled is in the model`);
    const irregularInRange = entry.axis.irregularStructures.filter(item => item.firstHitCm <= entry.axis.probeEndCm);
    expect(irregularInRange.length === 0, `${key}: odd hit counts within the probe for ${irregularInRange.map(item => item.anatomyId).join(', ')}`);
    expect(entry.axis.probeEndCm > entry.referenceDepthCm, `${key}: probe ends before the reference`);
    expect(entry.axis.angleToEntrySurfaceNormalDeg <= 20, `${key}: axis is ${entry.axis.angleToEntrySurfaceNormalDeg}° from the entry surface normal`);
    expect(entry.axis.sensitivity.referenceDepthCm.min <= entry.referenceDepthCm && entry.referenceDepthCm <= entry.axis.sensitivity.referenceDepthCm.max, `${key}: sensitivity range excludes the reported depth`);
    const side = entry.side;
    expect(Math.sign(entry.referencePosition[0]) === (side === 'right' ? -1 : 1), `${key}: reference on the wrong side`);
    expect(entry.nearby.every((item, i) => item.distanceCm <= NEARBY_LIMIT_CM && (!i || item.distanceCm >= entry.nearby[i - 1].distanceCm)), `${key}: nearby list not sorted or out of range`);
    expect(entry.nearby.every(item => item.anatomyId.endsWith(`-${side}`) || !/-(right|left)$/.test(item.anatomyId)), `${key}: nearby structure from the other side`);
    if (side === 'right') {
      const left = data.points[key.replace('-right', '-left')];
      const sameLayers = left && isDeepStrictEqual(left.layers.map(l => l.anatomyId.replace(/-left$/, '')), entry.layers.map(l => l.anatomyId.replace(/-right$/, '')));
      expect(sameLayers, `${key}: left/right layer sequence differs`);
      if (sameLayers) entry.layers.forEach((layer, i) => expect(Math.abs(layer.entryCm - left.layers[i].entryCm) <= 0.05 && Math.abs(layer.exitCm - left.layers[i].exitCm) <= 0.05, `${key}: left/right depths differ for ${layer.anatomyId}`));
      expect(left && Math.abs(left.referenceDepthCm - entry.referenceDepthCm) <= 0.05, `${key}: left/right reference depth differs`);
    }
  }
  return problems;
}

async function main() {
  const check = process.argv.includes('--check');
  const structures = await loadAll();
  const data = await computeDepth(structures);
  const text = JSON.stringify(data, null, 2) + '\n';
  if (!check) {
    await writeFile(outputFile, text);
    const summary = Object.fromEntries(Object.entries(data.points).map(([key, entry]) => [key, `${entry.layers.map(l => `${l.english} ${l.entryCm}-${l.exitCm}`).join(' → ')} | reference ${entry.referenceDepthCm} cm`]));
    console.log(JSON.stringify({ written: 'public/acupoint-depth.json', summary }, null, 2));
    return;
  }
  const problems = [];
  const loader = await crossCheckLoader(structures);
  problems.push(...loader.problems);
  let stored;
  try { stored = JSON.parse(await readFile(outputFile, 'utf8')); } catch (error) { problems.push(`public/acupoint-depth.json unreadable: ${error.message}`); }
  if (stored && !isDeepStrictEqual(stored, data)) problems.push('public/acupoint-depth.json is out of date: run `node scripts/compute-acupoint-depth.mjs`');
  problems.push(...sanityCheck(data));
  console.log(JSON.stringify({
    passed: problems.length === 0,
    scope: 'Model geometry only; not a needling path, needling depth or clinical acupoint location.',
    loaderCrossCheck: `${loader.compared - loader.problems.length}/${loader.compared} geometry-validation.json measurements reproduced (${loader.addonCompared} of them on shoulder add-on meshes)`,
    pointsChecked: Object.keys(data.points).length,
    problems,
  }, null, 2));
  if (problems.length) process.exitCode = 1;
}

if (process.argv[1] && fileURLToPath(import.meta.url) === resolve(process.argv[1])) {
  main().catch(error => {
    console.log(JSON.stringify({ passed: false, error: error instanceof Error ? error.stack : String(error) }, null, 2));
    process.exitCode = 1;
  });
}
