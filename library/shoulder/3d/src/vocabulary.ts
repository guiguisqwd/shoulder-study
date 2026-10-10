export type VocabularyTerm = {
  id: string;
  english: string;
  chinese: string;
  pronunciation?: string;
  stress: string;
  group: 'Muscles' | 'Bones' | 'Landmarks' | 'Acupoints';
  anatomy?: string;
  pointId?: string;
  sources: string[];
  pronunciationNote?: string;
};
const mw = (word: string) => `https://www.merriam-webster.com/dictionary/${encodeURIComponent(word)}`;
const medical = (word: string) => `https://www.merriam-webster.com/medical/${encodeURIComponent(word)}`;
const cambridge = (word: string) => `https://dictionary.cambridge.org/us/pronunciation/english/${word}`;
const cuff = (name: string) => `rotator-cuff-muscles-${name}-muscle`;
const bone = (name: string) => `appendicular-skeleton-${name}`;
const deltoid = (part: string) => `deltoid-muscles-${part}-part-of-deltoid-muscle`;
const trapezius = (part: string) => `trapezius-muscles-${part}-part-of-trapezius-muscle`;

export const vocabulary: VocabularyTerm[] = [
  { id: 'supraspinatus', english: 'Supraspinatus', chinese: '冈上肌', stress: 'soo-pruh-spy-NAY-tuhs', group: 'Muscles', anatomy: cuff('supraspinatus'), sources: [medical('supraspinatus'), mw('supra')], pronunciationNote: '重音提示依据词典缩略标音；此项不补写完整 IPA。' },
  { id: 'infraspinatus', english: 'Infraspinatus', chinese: '冈下肌', pronunciation: '/ˌɪnfrəspaɪˈneɪtəs/', stress: 'in-fruh-spy-NAY-tuhs', group: 'Muscles', anatomy: cuff('infraspinatus'), sources: [medical('infraspinatus')] },
  { id: 'teres-minor', english: 'Teres minor', chinese: '小圆肌', pronunciation: '/ˈtɪrˌiːz ˈmaɪnər/', stress: 'TEER-eez MY-ner', group: 'Muscles', anatomy: cuff('teres-minor'), sources: [medical('pronator teres'), mw('minor')], pronunciationNote: '词组音标按 teres 与 minor 的词典读音组合。' },
  { id: 'subscapularis', english: 'Subscapularis', chinese: '肩胛下肌', pronunciation: '/ˌsʌb.skæp.jəˈler.ɪs/', stress: 'sub-skap-yuh-LAIR-iss', group: 'Muscles', anatomy: cuff('subscapularis'), sources: [cambridge('subscapularis')] },
  { id: 'rotator-cuff', english: 'Rotator cuff', chinese: '肩袖', pronunciation: '/ˈroʊ.teɪ.t̬ɚ ˌkʌf/', stress: 'ROH-tay-ter kuf', group: 'Muscles', anatomy: 'rotator-cuff-muscles', sources: ['https://dictionary.cambridge.org/us/dictionary/english/rotator-cuff'] },
  { id: 'deltoid', english: 'Deltoid', chinese: '三角肌', pronunciation: '/ˈdel.tɔɪd/', stress: 'DEL-toyd', group: 'Muscles', anatomy: 'deltoid-muscles', sources: [cambridge('deltoid')] },
  { id: 'acromial-part', english: 'Acromial part', chinese: '三角肌肩峰部', pronunciation: '/əˈkroʊ.mi.əl/ + part', stress: 'uh-KROH-mee-uhl part', group: 'Muscles', anatomy: deltoid('acromial'), sources: [cambridge('acromial')], pronunciationNote: '音标展示核心形容词 acromial；音频朗读完整词组。' },
  { id: 'clavicular-part', english: 'Clavicular part', chinese: '三角肌锁骨部', pronunciation: '/kləˈvɪk.jə.lɚ/ + part', stress: 'kluh-VIK-yuh-ler part', group: 'Muscles', anatomy: deltoid('clavicular'), sources: ['https://dictionary.cambridge.org/us/dictionary/english/clavicular'], pronunciationNote: '音标展示 clavicular；音频朗读完整词组。' },
  { id: 'spinal-part', english: 'Spinal part', chinese: '三角肌肩胛冈部', pronunciation: '/ˈspaɪ.nəl/ + part', stress: 'SPY-nuhl part', group: 'Muscles', anatomy: deltoid('scapular-spinal'), sources: [cambridge('spinal')], pronunciationNote: '此处 spinal 指肩胛冈相关部分，不译为三角肌脊柱部。' },
  // Shoulder-region muscles from the shoulder add-on model (public/models/shoulder-addon.metadata.json).
  // Trapezius parts follow Terminologia Anatomica: descending = upper, transverse = middle, ascending = lower.
  { id: 'trapezius', english: 'Trapezius', chinese: '斜方肌', pronunciation: '/trəˈpiziəs/', stress: 'truh-PEE-zee-uhs', group: 'Muscles', anatomy: 'trapezius-muscles', sources: [medical('trapezius')] },
  { id: 'upper-trapezius', english: 'Upper trapezius', chinese: '上斜方肌', pronunciation: '/ˈʌpər trəˈpiziəs/', stress: 'UP-er truh-PEE-zee-uhs', group: 'Muscles', anatomy: trapezius('descending'), sources: [mw('upper'), medical('trapezius')], pronunciationNote: 'The phrase IPA combines the dictionary pronunciations of upper and trapezius. Upper trapezius is the descending part of the trapezius (upper fibers). 词组音标按 upper 与 trapezius 的词典读音组合；即斜方肌降部（上部纤维）。' },
  { id: 'middle-trapezius', english: 'Middle trapezius', chinese: '中斜方肌', pronunciation: '/ˈmɪdəl trəˈpiziəs/', stress: 'MID-uhl truh-PEE-zee-uhs', group: 'Muscles', anatomy: trapezius('transverse'), sources: [mw('middle'), medical('trapezius')], pronunciationNote: 'The phrase IPA combines the dictionary pronunciations of middle and trapezius. Middle trapezius is the transverse part of the trapezius (middle fibers). 词组音标按 middle 与 trapezius 的词典读音组合；即斜方肌横部（中部纤维）。' },
  { id: 'lower-trapezius', english: 'Lower trapezius', chinese: '下斜方肌', pronunciation: '/ˈloʊər trəˈpiziəs/', stress: 'LOH-er truh-PEE-zee-uhs', group: 'Muscles', anatomy: trapezius('ascending'), sources: [mw('lower'), medical('trapezius')], pronunciationNote: 'The phrase IPA combines the dictionary pronunciations of lower and trapezius; lower is the adjective (comparative of low, \\ˈlō-ər\\), not the verb “to frown” listed first on the same page. Lower trapezius is the ascending part of the trapezius (lower fibers). 词组音标按 lower 与 trapezius 的词典读音组合；lower 取形容词（low 的比较级，\\ˈlō-ər\\），不是同页最先列出的“皱眉”义动词。即斜方肌升部（下部纤维）。' },
  { id: 'latissimus-dorsi', english: 'Latissimus dorsi', chinese: '背阔肌', pronunciation: '/ləˈtɪsəməs ˈdɔrˌsaɪ/', stress: 'luh-TISS-uh-muhs DOR-sye', group: 'Muscles', anatomy: 'latissimus-dorsi-muscles-latissimus-dorsi-muscle', sources: [medical('latissimus dorsi')] },
  { id: 'levator-scapulae', english: 'Levator scapulae', chinese: '肩胛提肌', pronunciation: '/lɪˈveɪtər ˈskæpjəˌli/', stress: 'lih-VAY-ter SKAP-yuh-lee', group: 'Muscles', anatomy: 'levator-scapulae-muscles-levator-scapulae', sources: [medical('levator scapulae'), medical('levator')], pronunciationNote: 'The Merriam-Webster entry for levator scapulae marks only scapulae; levator follows the levator entry. 词典的 levator scapulae 词条只标 scapulae 的读音；levator 按 levator 词条。' },
  { id: 'rhomboid-major', english: 'Rhomboid major', chinese: '大菱形肌', pronunciation: '/ˈrɑmˌbɔɪd ˈmeɪdʒər/', stress: 'RAHM-boyd MAY-jer', group: 'Muscles', anatomy: 'rhomboid-muscles-rhomboid-major-muscle', sources: [mw('rhomboid'), mw('major')], pronunciationNote: 'The Merriam-Webster entry for rhomboid major gives no pronunciation, so the phrase IPA combines the dictionary pronunciations of rhomboid and major. 词典的 rhomboid major 词条没有标音，词组音标按 rhomboid 与 major 的词典读音组合。' },
  { id: 'rhomboid-minor', english: 'Rhomboid minor', chinese: '小菱形肌', pronunciation: '/ˈrɑmˌbɔɪd ˈmaɪnər/', stress: 'RAHM-boyd MY-ner', group: 'Muscles', anatomy: 'rhomboid-muscles-rhomboid-minor-muscle', sources: [mw('rhomboid'), mw('minor')], pronunciationNote: 'The Merriam-Webster entry for rhomboid minor gives no pronunciation, so the phrase IPA combines the dictionary pronunciations of rhomboid and minor. 词典的 rhomboid minor 词条没有标音，词组音标按 rhomboid 与 minor 的词典读音组合。' },
  { id: 'pectoralis-major', english: 'Pectoralis major', chinese: '胸大肌', pronunciation: '/ˌpɛktəˈreɪləs ˈmeɪdʒər/', stress: 'pek-tuh-RAY-luhs MAY-jer', group: 'Muscles', anatomy: 'pectoralis-major-muscles', sources: [medical('pectoralis'), mw('major')], pronunciationNote: 'The Merriam-Webster entry for pectoralis major gives no pronunciation, so the phrase IPA combines the dictionary pronunciations of pectoralis and major. 词典的 pectoralis major 词条没有标音，词组音标按 pectoralis 与 major 的词典读音组合。' },
  { id: 'pectoralis-minor', english: 'Pectoralis minor', chinese: '胸小肌', pronunciation: '/ˌpɛktəˈreɪləs ˈmaɪnər/', stress: 'pek-tuh-RAY-luhs MY-ner', group: 'Muscles', anatomy: 'pectoralis-minor-muscles-pectoralis-minor-muscle', sources: [medical('pectoralis'), mw('minor')], pronunciationNote: 'The Merriam-Webster entry for pectoralis minor gives no pronunciation, so the phrase IPA combines the dictionary pronunciations of pectoralis and minor. 词典的 pectoralis minor 词条没有标音，词组音标按 pectoralis 与 minor 的词典读音组合。' },
  { id: 'subclavius', english: 'Subclavius', chinese: '锁骨下肌', pronunciation: '/ˌsʌbˈkleɪviəs/', stress: 'sub-KLAY-vee-uhs', group: 'Muscles', anatomy: 'subclavius-muscles-subclavius-muscle', sources: [medical('subclavius')] },
  { id: 'serratus-anterior', english: 'Serratus anterior', chinese: '前锯肌', pronunciation: '/sɛˈreɪtəs ænˈtɪriər/', stress: 'seh-RAY-tuhs an-TEER-ee-er', group: 'Muscles', anatomy: 'serratus-anterior-muscles-serratus-anterior-muscle', sources: [medical('serratus'), mw('anterior')], pronunciationNote: 'The Merriam-Webster entry for serratus anterior gives no pronunciation, so the phrase IPA combines the dictionary pronunciations of serratus and anterior. 词典的 serratus anterior 词条没有标音，词组音标按 serratus 与 anterior 的词典读音组合。' },
  { id: 'teres-major', english: 'Teres major', chinese: '大圆肌', pronunciation: '/ˈtɪriz ˈmeɪdʒər/', stress: 'TEER-eez MAY-jer', group: 'Muscles', anatomy: 'teres-major-muscles-teres-major-muscle', sources: [medical('teres major'), mw('major')], pronunciationNote: 'Merriam-Webster gives two pronunciations of teres in teres major, \\ˈter-ēz\\ (TER-eez) first and \\ˈtir-ēz\\ (TEER-eez) second. This site uses TEER-eez for both teres major and teres minor so that they match the teres minor recording, as recorded in the shoulder sign-off; both are correct. 词典给 teres major 的 teres 两种读音，先列 \\ˈter-ēz\\（TER-eez），后列 \\ˈtir-ēz\\（TEER-eez）。本站大圆肌、小圆肌都用 TEER-eez，与小圆肌录音一致（见肩部发布签核）；两种都对。' },
  { id: 'biceps-brachii', english: 'Biceps brachii', chinese: '肱二头肌', pronunciation: '/ˈbaɪˌsɛps ˈbreɪkiˌaɪ/', stress: 'BY-seps BRAY-kee-eye', group: 'Muscles', anatomy: 'biceps-brachii-muscles', sources: [mw('biceps')], pronunciationNote: 'Merriam-Webster lists biceps brachii as \\ˈbī-ˌseps-ˈbrā-kē-ˌī\\ first and also \\ˈbī-ˌseps-ˈbrā-kē-ˌē\\ (BRAY-kee-ee); this card uses the first. 词典先列 \\ˈbī-ˌseps-ˈbrā-kē-ˌī\\，也收 \\ˈbī-ˌseps-ˈbrā-kē-ˌē\\（BRAY-kee-ee）；此处取第一种。' },
  { id: 'triceps-brachii', english: 'Triceps brachii', chinese: '肱三头肌', pronunciation: '/ˈtraɪˌsɛps ˈbreɪkiˌaɪ/', stress: 'TRY-seps BRAY-kee-eye', group: 'Muscles', anatomy: 'triceps-brachii-muscles', sources: [medical('triceps brachii'), medical('triceps')], pronunciationNote: 'The Merriam-Webster entry for triceps brachii marks only brachii; triceps follows the triceps entry. 词典的 triceps brachii 词条只标 brachii 的读音；triceps 按 triceps 词条。' },
  { id: 'triceps-long-head', english: 'Long head of triceps', chinese: '肱三头肌长头', pronunciation: '/lɔŋ hɛd əv ˈtraɪˌsɛps/', stress: 'LAWNG HED uhv TRY-seps', group: 'Muscles', anatomy: 'triceps-brachii-muscles-long-head-of-triceps-brachii', sources: [medical('triceps'), mw('long'), mw('head')], pronunciationNote: 'The phrase IPA combines the dictionary pronunciations of long, head and triceps. 词组音标按 long、head、triceps 的词典读音组合。' },
  { id: 'coracobrachialis', english: 'Coracobrachialis', chinese: '喙肱肌', pronunciation: '/ˌkɔrəkoʊˌbreɪkiˈeɪləs/', stress: 'kor-uh-koh-bray-kee-AY-luhs', group: 'Muscles', anatomy: 'coracobrachialis-muscles-coracobrachialis-muscle', sources: [medical('coracobrachialis')] },
  { id: 'brachialis', english: 'Brachialis', chinese: '肱肌', pronunciation: '/ˌbreɪkiˈæləs/', stress: 'bray-kee-AL-uhs', group: 'Muscles', anatomy: 'brachialis-muscles-brachialis-muscle', sources: [medical('brachialis')], pronunciationNote: 'Merriam-Webster lists \\ˌbrā-kē-ˈal-əs\\ first and also -ˈāl- and -ˈäl- (bray-kee-AY-luhs, bray-kee-AH-luhs); this card uses the first. 词典先列 \\ˌbrā-kē-ˈal-əs\\，也收 -ˈāl-、-ˈäl-（bray-kee-AY-luhs、bray-kee-AH-luhs）；此处取第一种。' },
  { id: 'scapula', english: 'Scapula', chinese: '肩胛骨', pronunciation: '/ˈskæpjələ/', stress: 'SKAP-yuh-luh', group: 'Bones', anatomy: bone('scapula'), sources: [mw('scapula')] },
  { id: 'clavicle', english: 'Clavicle', chinese: '锁骨', pronunciation: '/ˈklævɪkəl/', stress: 'KLAV-ih-kuhl', group: 'Bones', anatomy: bone('clavicle'), sources: [mw('clavicle')] },
  { id: 'humerus', english: 'Humerus', chinese: '肱骨', pronunciation: '/ˈhjuːmərəs/', stress: 'HYOO-muh-ruhs', group: 'Bones', anatomy: bone('humerus'), sources: [cambridge('humerus')] },
  { id: 'scapular-spine', english: 'Scapular spine', chinese: '肩胛冈', pronunciation: '/ˈskæpjələr spaɪn/', stress: 'SKAP-yuh-ler SPYNE', group: 'Landmarks', anatomy: bone('scapula'), sources: [mw('scapular'), mw('spine')] },
  { id: 'inferior-angle', english: 'Inferior angle', chinese: '肩胛骨下角', pronunciation: '/ɪnˈfɪriər ˈæŋɡəl/', stress: 'in-FEER-ee-er ANG-guhl', group: 'Landmarks', anatomy: bone('scapula'), sources: [mw('inferior'), mw('angle')] },
  { id: 'acromion', english: 'Acromion', chinese: '肩峰', pronunciation: '/əˈkroʊmiən/', stress: 'uh-KROH-mee-uhn', group: 'Landmarks', anatomy: bone('scapula'), sources: [medical('acromion')] },
  { id: 'greater-tubercle', english: 'Greater tubercle', chinese: '肱骨大结节', pronunciation: '/ˈɡreɪtər ˈtuːbərkəl/', stress: 'GRAY-ter TOO-ber-kuhl', group: 'Landmarks', anatomy: bone('humerus'), sources: [mw('greater'), mw('tubercle')] },
  { id: 'infraspinous-fossa', english: 'Infraspinous fossa', chinese: '冈下窝', pronunciation: '/ˌɪnfrəˈspaɪnəs ˈfɑːsə/', stress: 'in-fruh-SPY-nuhs FAH-suh', group: 'Landmarks', anatomy: bone('scapula'), sources: [medical('infraspinous'), mw('fossa')] },
  { id: 'supraspinous-fossa', english: 'Supraspinous fossa', chinese: '冈上窝', pronunciation: '/ˌsuːprəˈspaɪnəs ˈfɑːsə/', stress: 'soo-pruh-SPY-nuhs FAH-suh', group: 'Landmarks', anatomy: bone('scapula'), sources: [cambridge('supraspinous-fossa')] },
  { id: 'posterior-shoulder', english: 'Posterior shoulder', chinese: '肩后区', pronunciation: '/pɑːˈstɪr.i.ɚ ˈʃoʊl.dɚ/', stress: 'pah-STEER-ee-er SHOHL-der', group: 'Landmarks', anatomy: cuff('teres-minor'), sources: ['https://dictionary.cambridge.org/us/dictionary/english/posterior', cambridge('shoulder')], pronunciationNote: '词组音标按 posterior 与 shoulder 的美式词典读音组合。' },
  { id: 'anterolateral-acromion', english: 'Anterolateral acromion', chinese: '肩峰前外侧', pronunciation: '/ˌæn.tə.roʊˈlæt̬.ɚ.əl əˈkroʊmiən/', stress: 'an-tuh-roh-LAT-er-uhl uh-KROH-mee-uhn', group: 'Landmarks', anatomy: bone('scapula'), sources: ['https://dictionary.cambridge.org/pronunciation/english/anterolateral', medical('acromion')], pronunciationNote: '词组音标按单词读音组合；anterolateral 采用 Cambridge 美式音标，acromion 由 Merriam-Webster 标音转写。' },
  { id: 'posterolateral-acromion', english: 'Posterolateral acromion', chinese: '肩峰后外侧', pronunciation: '/ˌpɑːs.tə.roʊˈlæt̬.ɚ.əl əˈkroʊmiən/', stress: 'pah-stuh-roh-LAT-er-uhl uh-KROH-mee-uhn', group: 'Landmarks', anatomy: bone('scapula'), sources: ['https://dictionary.cambridge.org/us/dictionary/english/posterolateral', medical('acromion')], pronunciationNote: '词组音标按单词读音组合；posterolateral 采用 Cambridge 美式音标，acromion 由 Merriam-Webster 标音转写。' },
  { id: 'posterior-deltoid', english: 'Posterior deltoid', chinese: '三角肌后部', pronunciation: '/pɑːˈstɪr.i.ɚ ˈdel.tɔɪd/', stress: 'pah-STEER-ee-er DEL-toyd', group: 'Muscles', anatomy: deltoid('scapular-spinal'), sources: ['https://dictionary.cambridge.org/us/dictionary/english/posterior', cambridge('deltoid')], pronunciationNote: '词组音标按 posterior 与 deltoid 的美式词典读音组合。' },
  ...[
    ['si11','Tianzong','天宗','tiān zōng','SI11'],
    ['si12','Bingfeng','秉风','bǐng fēng','SI12'],
    ['si9','Jianzhen','肩贞','jiān zhēn','SI9'],
    ['li15','Jianyu','肩髃','jiān yú','LI15'],
    ['te14','Jianliao','肩髎','jiān liáo','TE14'],
  ].map(([id, english, chinese, stress, pointId]) => ({ id, english, chinese, stress, pointId, group: 'Acupoints' as const, sources: ['https://www.medbox.org/index.php/dl/627a4de115110145a1723f64'], pronunciationNote: 'This is a Chinese pinyin name. Audio uses Mandarin, not English. 穴名采用汉语拼音，发音为普通话。' })),
];
export const vocabularyById = Object.fromEntries(vocabulary.map(term => [term.id, term]));
export const termForAnatomy = (anatomy: string) => {
  const base = anatomy.replace(/-(right|left)$/, '');
  // A part without its own word (e.g. a biceps head) falls back to its muscle group's word.
  return vocabulary.find(term => term.anatomy === base)
    || vocabulary.find(term => term.anatomy?.endsWith('-muscles') && base.startsWith(term.anatomy + '-'));
};
// Add-on muscle words follow the published layer descriptions recorded per point in
// public/acupoint-depth.json (sourceComparison.sources): trapezius over SI11 and SI12;
// long head of triceps, teres major and latissimus dorsi at SI9.
export const pointRelatedTerms: Record<string,string[]> = {
  SI11: ['infraspinatus','scapular-spine','inferior-angle','infraspinous-fossa','trapezius'],
  SI12: ['supraspinatus','scapular-spine','supraspinous-fossa','trapezius'],
  SI9: ['teres-minor','posterior-shoulder','posterior-deltoid','triceps-long-head','teres-major','latissimus-dorsi'],
  LI15: ['deltoid','acromion','greater-tubercle','anterolateral-acromion'],
  TE14: ['posterior-deltoid','acromion','greater-tubercle','posterolateral-acromion'],
};
