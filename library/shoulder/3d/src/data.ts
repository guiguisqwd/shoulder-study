export { loadAtlases, modelPosition, modelScale, modelVersion } from './model';

export type PointKind = 'unconfirmed' | 'surface-reference' | 'deep-reference';
export type Placement = { position: [number, number, number]; anatomyId: string; kind: PointKind; note: string };
export type Placements = Record<string, Placement>;
export const storageKey = 'shoulder-spatial-study-v1';

export const points = [
  { id: 'SI11', name: '天宗', english: 'Tianzong', color: '#e6b96b', anatomy: 'rotator-cuff-muscles-infraspinatus-muscle', location: '肩胛冈中点至肩胛下角连线，上 1/3 与下 2/3 交界的凹陷。', cue: '先在模型中辨认肩胛冈与下角，再核对位置。', related: '冈下窝、冈下肌、肩胛骨', page: '93' },
  { id: 'SI12', name: '秉风', english: 'Bingfeng', color: '#ed8a79', anatomy: 'rotator-cuff-muscles-supraspinatus-muscle', location: '冈上窝内，肩胛冈中点上方。', cue: '肩胛冈是区分冈上窝与冈下窝的关键标志。', related: '冈上窝、冈上肌、肩胛冈', page: '93' },
  { id: 'SI9', name: '肩贞', english: 'Jianzhen', color: '#85bfad', anatomy: 'rotator-cuff-muscles-teres-minor-muscle', location: '肩关节后下方，腋后纹上 1 骨度分寸。', cue: '标准定位涉及上臂内收姿势与腋后纹。', related: '肩后区、小圆肌、三角肌后部', page: '92' },
  { id: 'LI15', name: '肩髃', english: 'Jianyu', color: '#8cb5e8', anatomy: 'deltoid-muscles-acromial-part-of-deltoid-muscle', location: '肩峰外侧缘前端与肱骨大结节之间的凹陷。', cue: '标准定位涉及上臂外展姿势；需要核对姿势差异。', related: '肩峰前外侧、肱骨大结节、三角肌', page: '41' },
  { id: 'TE14', name: '肩髎', english: 'Jianliao', color: '#ba9ad9', anatomy: 'deltoid-muscles-scapular-spinal-part-of-deltoid-muscle', location: '肩峰角与肱骨大结节之间的凹陷。', cue: '标准定位涉及屈肘、上臂外展姿势。', related: '肩峰后外侧、肱骨大结节、三角肌后部', page: '164' },
] as const;

export const anatomyNames: Record<string, string> = {
  'rotator-cuff-muscles-supraspinatus-muscle': '冈上肌',
  'rotator-cuff-muscles-infraspinatus-muscle': '冈下肌',
  'rotator-cuff-muscles-teres-minor-muscle': '小圆肌',
  'rotator-cuff-muscles-subscapularis-muscle': '肩胛下肌',
  'deltoid-muscles-acromial-part-of-deltoid-muscle': '三角肌 · 肩峰部',
  'deltoid-muscles-clavicular-part-of-deltoid-muscle': '三角肌 · 锁骨部',
  'deltoid-muscles-scapular-spinal-part-of-deltoid-muscle': '三角肌 · 肩胛冈部',
  'appendicular-skeleton-scapula': '肩胛骨',
  'appendicular-skeleton-clavicle': '锁骨',
  'appendicular-skeleton-humerus': '肱骨',
  // Shoulder add-on muscles (public/models/shoulder-addon.metadata.json)
  'trapezius-muscles-descending-part-of-trapezius-muscle': '上斜方肌',
  'trapezius-muscles-transverse-part-of-trapezius-muscle': '中斜方肌',
  'trapezius-muscles-ascending-part-of-trapezius-muscle': '下斜方肌',
  'latissimus-dorsi-muscles-latissimus-dorsi-muscle': '背阔肌',
  'levator-scapulae-muscles-levator-scapulae': '肩胛提肌',
  'rhomboid-muscles-rhomboid-major-muscle': '大菱形肌',
  'rhomboid-muscles-rhomboid-minor-muscle': '小菱形肌',
  'pectoralis-major-muscles-clavicular-head-of-pectoralis-major-muscle': '胸大肌 · 锁骨部',
  'pectoralis-major-muscles-sternocostal-head-of-pectoralis-major-muscle': '胸大肌 · 胸肋部',
  'pectoralis-major-muscles-abdominal-part-of-pectoralis-major-muscle': '胸大肌 · 腹部',
  'pectoralis-minor-muscles-pectoralis-minor-muscle': '胸小肌',
  'subclavius-muscles-subclavius-muscle': '锁骨下肌',
  'serratus-anterior-muscles-serratus-anterior-muscle': '前锯肌',
  'teres-major-muscles-teres-major-muscle': '大圆肌',
  'biceps-brachii-muscles-long-head-of-biceps-brachii': '肱二头肌 · 长头',
  'biceps-brachii-muscles-short-head-of-biceps-brachii': '肱二头肌 · 短头',
  'triceps-brachii-muscles-long-head-of-triceps-brachii': '肱三头肌 · 长头',
  'triceps-brachii-muscles-lateral-head-of-triceps-brachii': '肱三头肌 · 外侧头',
  'triceps-brachii-muscles-medial-head-of-triceps-brachii': '肱三头肌 · 内侧头',
  'coracobrachialis-muscles-coracobrachialis-muscle': '喙肱肌',
  'brachialis-muscles-brachialis-muscle': '肱肌',
};

export const anatomyEnglish: Record<string, string> = {
  'rotator-cuff-muscles-supraspinatus-muscle': 'Supraspinatus',
  'rotator-cuff-muscles-infraspinatus-muscle': 'Infraspinatus',
  'rotator-cuff-muscles-teres-minor-muscle': 'Teres minor',
  'rotator-cuff-muscles-subscapularis-muscle': 'Subscapularis',
  'deltoid-muscles-acromial-part-of-deltoid-muscle': 'Deltoid · acromial part',
  'deltoid-muscles-clavicular-part-of-deltoid-muscle': 'Deltoid · clavicular part',
  'deltoid-muscles-scapular-spinal-part-of-deltoid-muscle': 'Deltoid · spinal part',
  'appendicular-skeleton-scapula': 'Scapula',
  'appendicular-skeleton-clavicle': 'Clavicle',
  'appendicular-skeleton-humerus': 'Humerus',
  // Shoulder add-on muscles (public/models/shoulder-addon.metadata.json)
  'trapezius-muscles-descending-part-of-trapezius-muscle': 'Upper trapezius',
  'trapezius-muscles-transverse-part-of-trapezius-muscle': 'Middle trapezius',
  'trapezius-muscles-ascending-part-of-trapezius-muscle': 'Lower trapezius',
  'latissimus-dorsi-muscles-latissimus-dorsi-muscle': 'Latissimus dorsi',
  'levator-scapulae-muscles-levator-scapulae': 'Levator scapulae',
  'rhomboid-muscles-rhomboid-major-muscle': 'Rhomboid major',
  'rhomboid-muscles-rhomboid-minor-muscle': 'Rhomboid minor',
  'pectoralis-major-muscles-clavicular-head-of-pectoralis-major-muscle': 'Pectoralis major · clavicular head',
  'pectoralis-major-muscles-sternocostal-head-of-pectoralis-major-muscle': 'Pectoralis major · sternocostal head',
  'pectoralis-major-muscles-abdominal-part-of-pectoralis-major-muscle': 'Pectoralis major · abdominal part',
  'pectoralis-minor-muscles-pectoralis-minor-muscle': 'Pectoralis minor',
  'subclavius-muscles-subclavius-muscle': 'Subclavius',
  'serratus-anterior-muscles-serratus-anterior-muscle': 'Serratus anterior',
  'teres-major-muscles-teres-major-muscle': 'Teres major',
  'biceps-brachii-muscles-long-head-of-biceps-brachii': 'Biceps brachii · long head',
  'biceps-brachii-muscles-short-head-of-biceps-brachii': 'Biceps brachii · short head',
  'triceps-brachii-muscles-long-head-of-triceps-brachii': 'Triceps brachii · long head',
  'triceps-brachii-muscles-lateral-head-of-triceps-brachii': 'Triceps brachii · lateral head',
  'triceps-brachii-muscles-medial-head-of-triceps-brachii': 'Triceps brachii · medial head',
  'coracobrachialis-muscles-coracobrachialis-muscle': 'Coracobrachialis',
  'brachialis-muscles-brachialis-muscle': 'Brachialis',
};
/** Muscle groups of the shoulder page's layer bar. Each lists the model group ids it shows (both sides). */
export type MuscleGroupId = 'cuff' | 'deltoid' | 'back' | 'chest' | 'teres-major' | 'upper-arm';
export const muscleGroups: { id: MuscleGroupId; en: string; zh: string; groupIds: string[]; initial: boolean }[] = [
  { id: 'cuff', en: 'Rotator cuff', zh: '肩袖', groupIds: ['rotator-cuff-muscles'], initial: true },
  { id: 'deltoid', en: 'Deltoid', zh: '三角肌', groupIds: ['deltoid-muscles'], initial: true },
  // Shoulder add-on muscles: off until the learner turns them on or chooses one of their words.
  { id: 'back', en: 'Back', zh: '背部', groupIds: ['trapezius-muscles', 'latissimus-dorsi-muscles', 'levator-scapulae-muscles', 'rhomboid-muscles'], initial: false },
  { id: 'chest', en: 'Chest', zh: '胸部', groupIds: ['pectoralis-major-muscles', 'pectoralis-minor-muscles', 'subclavius-muscles', 'serratus-anterior-muscles'], initial: false },
  { id: 'teres-major', en: 'Teres major', zh: '大圆肌', groupIds: ['teres-major-muscles'], initial: false },
  { id: 'upper-arm', en: 'Upper arm', zh: '上臂', groupIds: ['biceps-brachii-muscles', 'triceps-brachii-muscles', 'coracobrachialis-muscles', 'brachialis-muscles'], initial: false },
];
export const initialMuscleGroups = Object.fromEntries(muscleGroups.map(group => [group.id, group.initial])) as Record<MuscleGroupId, boolean>;
/** The model group id ('trapezius-muscles') of a group id, a part id or a part id with its side. */
export function modelGroupOf(id: string): string | undefined {
  return muscleGroups.flatMap(group => group.groupIds).find(groupId => id === groupId || id.startsWith(groupId + '-'));
}
/** The layer-bar group that shows a structure, if any. */
export function muscleGroupOf(id: string): MuscleGroupId | undefined {
  const groupId = modelGroupOf(id);
  return groupId ? muscleGroups.find(group => group.groupIds.includes(groupId))?.id : undefined;
}

export const relatedEnglish: Record<string,string> = {
  SI11: 'Infraspinous fossa · Infraspinatus · Scapula',
  SI12: 'Supraspinous fossa · Supraspinatus · Spine of scapula',
  SI9: 'Posterior shoulder · Teres minor · Posterior deltoid',
  LI15: 'Anterolateral acromion · Greater tubercle of humerus · Deltoid',
  TE14: 'Posterolateral acromion · Greater tubercle of humerus · Posterior deltoid',
};

export function anatomyLabel(id: string, showChinese = true) {
  const side = id.endsWith('-right') ? 'Right · ' : id.endsWith('-left') ? 'Left · ' : '';
  const base = id.replace(/-(right|left)$/, '');
  return side + (anatomyEnglish[base] || base) + (showChinese && anatomyNames[base] ? '\n' + anatomyNames[base] : '');
}
export function validatePlacements(value: unknown): Placements {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('位置数据格式不正确');
  const result: Placements = {};
  for (const [id, raw] of Object.entries(value)) {
    if (!points.some(p => id === p.id + '-right' || id === p.id + '-left')) throw new Error('包含未知标记');
    if (!raw || typeof raw !== 'object') throw new Error('标记格式不正确');
    const point = raw as Placement;
    if (!Array.isArray(point.position) || point.position.length !== 3 || !point.position.every(v => typeof v === 'number' && Number.isFinite(v))) throw new Error('坐标必须包含三个有限数值');
    const [x, y, z] = point.position;
    if (Math.abs(x) > 0.7 || y < 0 || y > 2 || Math.abs(z) > 0.7) throw new Error('坐标超出此人体模型的范围');
    if (!['unconfirmed', 'surface-reference', 'deep-reference'].includes(point.kind)) throw new Error('标记类型不正确');
    if (typeof point.anatomyId !== 'string' || typeof point.note !== 'string') throw new Error('标记说明不完整');
    const side = id.endsWith('-right') ? 'right' : 'left';
    if (!Object.keys(anatomyNames).some(base => point.anatomyId === `${base}-${side}`)) throw new Error('起点结构不属于该侧肩部');
    if ((side === 'right' && x > 0) || (side === 'left' && x < 0)) throw new Error('坐标与左右侧别不一致');
    result[id] = { position: [...point.position], anatomyId: point.anatomyId, kind: point.kind, note: point.note.slice(0, 3000) };
  }
  return result;
}
