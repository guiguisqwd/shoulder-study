"""Shared topic contracts, publication gates and renderer (Python standard library)."""
from __future__ import annotations
import hashlib
import html
import json
import math
import re
import shutil
import xml.etree.ElementTree as ET
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode, urlparse

import reading

ROOT = Path(__file__).resolve().parents[3]
ID = re.compile(r'^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$')
SECTIONS = [
    ('anatomy', 'Anatomy', '解剖基础'),
    ('innervation', 'Innervation and nerve course', '神经支配与走行'),
    ('movement', 'Movement and coordination', '动作与配合'),
    ('clinical', 'Clinical and regional anatomy', '临床与局部解剖'),
    ('review', 'Review and complete answers', '复习与完整答案'),
]
# CH-01 (2026-10-09): paper reading left the chapter and became daily content (N-5). Chapters made
# before that still carry a trailing 'papers' section until their own threads move it out.
LEGACY_PAPER_SECTION = set()
STRUCTURE_KINDS = ['muscle', 'nerve', 'bone', 'landmark', 'joint', 'acupoint', 'paper']
QA_CHECKS = ['medicalSources', 'bilingual', 'originInsertionLabels', 'modelLinks',
             'layoutDesktop', 'layoutMobile', 'fullAnswers']
MUSCLE_FIELDS = ['origin', 'insertion', 'course', 'actions', 'innervation']
# QC-06: kinds whose English name is a key term needing IPA + stress + dictionary link (AN-07);
# acupoints need tone-marked pinyin instead; paper titles are not pronunciation terms.
PRONOUNCED_KINDS = ['muscle', 'nerve', 'bone', 'landmark', 'joint']
CJK = re.compile(r'[\u3400-\u9fff\uf900-\ufaff]')
LATIN = re.compile(r'[A-Za-z]')
TONE = re.compile(r'[āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ]')
PAPER_FIELDS = ['question', 'design', 'population', 'methods', 'results', 'limitations', 'applicability']
NERVE_NOTATION = {
    'cervical': {'en': 'C denotes cervical levels.', 'zh': 'C 表示颈部节段。'},
    'thoracic': {'en': 'T denotes thoracic levels.', 'zh': 'T 表示胸部节段。'},
    'lumbar': {'en': 'L denotes lumbar levels.', 'zh': 'L 表示腰部节段。'},
    'sacral': {'en': 'S denotes sacral levels.', 'zh': 'S 表示骶部节段。'},
    'spinalNerveVsVertebra': {'en': 'A spinal nerve level identifies a nerve, whereas a vertebral level identifies a bone. Specify which is being described.', 'zh': '脊神经节段表示神经，椎骨节段表示骨骼；描述时应明确区分。'},
}


def pair(en='', zh=''):
    return {'en': en, 'zh': zh}


def skeleton(topic_id, en, zh, region_en='', region_zh=''):
    if not isinstance(topic_id, str) or not ID.fullmatch(topic_id):
        raise ValueError('Topic id must be a lowercase slug, e.g. hip or knee-joint.')
    manifest = {'schemaVersion': 1, 'id': topic_id, 'title': pair(en, zh),
                'summary': pair('Content is being prepared and has not been reviewed.', '内容正在整理，尚未完成核验。'),
                'region': pair(region_en or en, region_zh or zh), 'status': 'draft', 'adapter': 'standard',
                'viewer': {'enabled': False, 'defaultTerm': None, 'terms': []}, 'structures': []}
    content = {'schemaVersion': 1, 'sections': [
        {'id': sid, 'title': pair(e, z), 'overview': pair(), 'blocks': [], 'diagramIds': []}
        for sid, e, z in SECTIONS], 'muscles': [], 'landmarks': [], 'diagrams': [],
        'review': [], 'sources': [],
        'nerveNotation': json.loads(json.dumps(NERVE_NOTATION)),
        'qa': {'reviewedBy': '', 'reviewedOn': '', 'checks': {k: False for k in QA_CHECKS}}}
    manifest_template = ROOT / 'site/build/platform/templates/topic.json'
    content_template = ROOT / 'site/build/platform/templates/content.json'
    if manifest_template.exists(): manifest = {**read_json(manifest_template), **manifest}
    if content_template.exists(): content = read_json(content_template)
    return manifest, content


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def inside(base, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError('Expected a relative asset path.')
    base = Path(base).resolve()
    target = (base / relative).resolve()
    if not target.is_relative_to(base):
        raise ValueError('Asset path leaves its topic directory.')
    return target


def catalog_models(root=ROOT):
    """Every 3D structure id -> its metadata entry: the shared muscular and skeletal models, plus each
    chapter add-on declared by library/<chapter>/3d/atlas-addon.json (ST-7). Add-on entries carry
    'addon': <chapter>, because only that chapter's viewer loads the add-on (topics.json viewer.addons)."""
    root = Path(root)
    app = root / 'library/shoulder/3d'  # the shared 3D app; add-on outputs are relative to it
    result = {}
    for system in ['skeletal', 'muscular']:
        for s in read_json(app / 'public/models' / (system + '.metadata.json'))['structures']:
            result[s['id']] = s
    for config_path in sorted((root / 'library').glob('*/3d/atlas-addon.json')):
        chapter = config_path.parent.parent.name
        config = read_json(config_path)
        output = config.get('output') if isinstance(config, dict) else None
        # The viewer (src/model.ts loadAtlases) finds an add-on by its chapter id, so the files must use these names.
        expected = {'metadata': 'public/models/' + chapter + '-addon.metadata.json',
                    'glb': 'public/models/z-anatomy-1.4.0-' + chapter + '-addon.glb'}
        for key, relative in expected.items():
            if not isinstance(output, dict) or output.get(key) != relative:
                raise ValueError(chapter + ': atlas-addon.json output.' + key + ' must be ' + relative + ' (the 3D viewer loads that file)')
        path = inside(app, expected['metadata'])
        if not path.is_file():
            raise ValueError(chapter + ': 3D add-on metadata is missing (' + expected['metadata'] + '); run site/build/atlas/build-addon.py ' + chapter)
        for s in read_json(path)['structures']:
            if s['id'] in result:
                raise ValueError(chapter + ': 3D add-on structure ' + s['id'] + ' duplicates an existing model id')
            result[s['id']] = dict(s, addon=chapter)
    return result


def topic_addons(manifest, topic_dir):
    """Add-on models a topic's viewer loads: its own chapter add-on, when library/<id>/3d/atlas-addon.json exists."""
    return [manifest['id']] if (Path(topic_dir) / '3d/atlas-addon.json').is_file() else []


def chapter_3d(topic_dir):
    """Ids a chapter's own 3D part (ST-7, <chapter>/3d/src) defines: vocabulary terms, landmark markers
    (id -> parent bone) and acupoint markers. Chapters that borrow another chapter's viewer define none."""
    src = Path(topic_dir) / '3d/src'
    terms, landmarks, points = set(), {}, set()
    if (src / 'vocabulary.ts').is_file():
        terms = set(re.findall(r"\bid: '([a-z][a-z0-9-]*)'", (src / 'vocabulary.ts').read_text(encoding='utf-8')))
    for path in sorted(src.glob('*-landmarks.json')):
        for item in read_json(path):
            if isinstance(item, dict) and item.get('id'): landmarks[item['id']] = path.name.removesuffix('-landmarks.json')
    if (src / 'data.ts').is_file():
        points = set(re.findall(r"\{ id: '([A-Z]+[0-9]+)'", (src / 'data.ts').read_text(encoding='utf-8')))
    return terms, landmarks, points


def normal_model_name(name):
    return re.sub(r'\s+', ' ', re.sub(r'\s+muscle\b|\.[lr]$', '', name, flags=re.I)).strip().lower()


def content_digest(content, topic_dir):
    digest = hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False).encode())
    for diagram in content.get('diagrams', []):
        path = inside(topic_dir, diagram['file'])
        digest.update(path.read_bytes())
    return digest.hexdigest()


def valid_review_date(value):
    try:
        return bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}', value)) and bool(date.fromisoformat(value))
    except (ValueError, TypeError):
        return False


def valid_source_url(value):
    try:
        parsed = urlparse(value)
        return parsed.scheme == 'https' and bool(parsed.hostname) and not any(c.isspace() for c in value)
    except (ValueError, TypeError):
        return False


def order_problem(en, zh):
    """QC-05 / G-01 for one {en, zh} pair: the English slot holds English, the Chinese slot Chinese."""
    if en.strip() and (CJK.search(en) or not LATIN.search(en)): return 'English slot must hold English, not Chinese: ' + en[:40]
    if zh.strip() and not CJK.search(zh): return 'Chinese slot must hold Chinese: ' + zh[:40]
    return None


class _OrderScan(HTMLParser):
    """QC-05 for rendered reading pages: text marked lang="en" holds no Chinese, and every Chinese
    translation follows English inside the same parent element."""
    VOID = {'br', 'img', 'hr', 'meta', 'link', 'input', 'source', 'wbr', 'col'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []  # [tag, lang, saw_english_child]
        self.problems = []
        self.svg = 0

    def lang(self):
        return next((f[1] for f in reversed(self.stack) if f[1]), '')

    def handle_starttag(self, tag, attrs):
        if tag == 'svg': self.svg += 1
        if tag in self.VOID or self.svg: return
        a = dict(attrs)
        own = a.get('lang') or ('zh' if 'translation' in (a.get('class') or '').split() else '')
        if own.startswith('zh') and self.stack and not self.stack[-1][2] and not self.lang().startswith('zh'):
            self.problems.append('Chinese translation comes before its English in <' + self.stack[-1][0] + '>')
        if own.startswith('en') and self.stack: self.stack[-1][2] = True
        self.stack.append([tag, own, False])

    def handle_endtag(self, tag):
        if self.svg:
            if tag == 'svg': self.svg -= 1
            return
        while self.stack:
            frame = self.stack.pop()
            # English inside an untagged child (e.g. <b>C5 vertebra</b>) counts for the parent too.
            if self.stack and frame[2] and not frame[1].startswith('zh'): self.stack[-1][2] = True
            if frame[0] == tag: break

    def handle_data(self, data):
        text = data.strip()
        if not text or not self.stack or self.svg: return
        lang = self.lang()
        if lang.startswith('en') and CJK.search(text):
            self.problems.append('Chinese inside lang="en": ' + text[:40])
        elif not lang:
            if CJK.search(text) and not LATIN.search(text) and not self.stack[-1][2]:
                self.problems.append('Chinese without English before it in <' + self.stack[-1][0] + '>: ' + text[:40])
            if LATIN.search(text): self.stack[-1][2] = True
            first = re.search(r'[A-Za-z\u3400-\u9fff]', text)
            if first and CJK.match(first.group()) and re.search(r'[A-Za-z]{3,}', text):
                self.problems.append('Chinese before English: ' + text[:40])


def html_order_problems(markup):
    scan = _OrderScan()
    scan.feed(markup)
    return scan.problems


def check_pronunciation(manifest, topic_dir, fail, require):
    """QC-06 / AN-07: <topic>/pronunciation.json covers every key term of the ST-1 structure list."""
    path = Path(topic_dir) / 'pronunciation.json'
    data = {}
    if path.is_file():
        try: data = read_json(path)
        except (ValueError, OSError) as exc: fail('pronunciation.json: ' + str(exc)); return
        if not isinstance(data, dict): fail('pronunciation.json must contain an object'); return
    terms, pinyin = data.get('terms', {}), data.get('pinyin', {})
    if not isinstance(terms, dict) or not isinstance(pinyin, dict):
        fail('pronunciation.json: terms and pinyin must be objects'); return
    for term, entry in terms.items():
        label = 'pronunciation ' + term
        if not (isinstance(entry, list) and len(entry) == 3 and all(isinstance(x, str) for x in entry)):
            fail(label + ': expected ["/IPA/", "STRESS-ed respelling", "https://dictionary link"]'); continue
        ipa, stress, url = entry
        if not re.fullmatch(r'/[^/]+/', ipa.strip()): fail(label + ': IPA must be written between slashes')
        # one-syllable words (SHAM, NURV ROOT) are all capitals; a longer word must also keep unstressed syllables lowercase
        if not re.search(r'\b[A-Z]{2,}\b', stress) or any(len(w.split('-')) > 1 and w == w.upper() for w in stress.split()):
            fail(label + ': respelling must capitalise only the stressed syllable')
        if not valid_source_url(url): fail(label + ': dictionary link must be an HTTPS URL')
    for name, value in pinyin.items():
        if not isinstance(value, str) or not TONE.search(value): fail('pinyin ' + str(name) + ': tone marks are required')
    known = {t.lower() for t in terms}
    for item in manifest.get('structures') or []:
        if not isinstance(item, dict): continue
        en = (item.get('name') or {}).get('en', '') if isinstance(item.get('name'), dict) else ''
        if not en.strip(): continue
        if item.get('kind') in PRONOUNCED_KINDS:
            require(en.lower() in known, 'QC-06 pronunciation missing for key term ' + en + ' (pronunciation.json)')
        elif item.get('kind') == 'acupoint':
            require(en in pinyin, 'QC-06 tone-marked pinyin missing for acupoint ' + en + ' (pronunciation.json)')


def validate_shape(value, schema, label='data'):
    """Check the structural subset used by our checked-in schemas, without dependencies."""
    errors = []
    if 'anyOf' in schema:
        if all(validate_shape(value, choice, label) for choice in schema['anyOf']):
            return [label + ': does not match an allowed field shape']
        return []
    if 'const' in schema and value != schema['const']: errors.append(label + ': unexpected schema version')
    if 'enum' in schema and value not in schema['enum']: errors.append(label + ': unexpected value')
    types = schema.get('type', [])
    if isinstance(types, str): types = [types]
    matched = {'object': isinstance(value, dict), 'array': isinstance(value, list), 'string': isinstance(value, str),
               'number': type(value) in [int, float] and math.isfinite(value), 'integer': type(value) is int,
               'boolean': type(value) is bool, 'null': value is None}
    if types and not any(matched.get(t, False) for t in types): return errors + [label + ': wrong field type']
    if isinstance(value, dict):
        for key in schema.get('required', []):
            if key not in value: errors.append(label + '.' + key + ': required field is missing')
        props = schema.get('properties', {})
        if schema.get('additionalProperties') is False:
            for key in value:
                if key not in props: errors.append(label + '.' + key + ': unexpected field')
        for key, child in props.items():
            if key in value: errors.extend(validate_shape(value[key], child, label + '.' + key))
    elif isinstance(value, list):
        if len(value) < schema.get('minItems', 0) or len(value) > schema.get('maxItems', float('inf')):
            errors.append(label + ': invalid number of items')
        if schema.get('uniqueItems') and len({json.dumps(v, sort_keys=True) for v in value}) != len(value):
            errors.append(label + ': duplicate items')
        for i, item in enumerate(value): errors.extend(validate_shape(item, schema.get('items', {}), label + '[' + str(i) + ']'))
    elif isinstance(value, str):
        if schema.get('pattern') and not re.search(schema['pattern'], value): errors.append(label + ': invalid format')
    elif type(value) in [int, float]:
        if value < schema.get('minimum', -float('inf')) or value > schema.get('maximum', float('inf')):
            errors.append(label + ': number outside allowed range')
    return errors


def validate(manifest, content, topic_dir, models=None, root=ROOT, published_override=False):
    """Return (errors, missing). Draft omissions are visible; unsafe/invalid data always errors."""
    errors, missing = [], []
    models = catalog_models(root) if models is None else models
    topic_dir = Path(topic_dir)
    errors.extend(validate_shape(manifest, read_json(ROOT / 'site/build/platform/topic.schema.json'), 'topic'))
    if isinstance(manifest, dict) and (manifest.get('adapter') == 'standard' or content is not None):
        errors.extend(validate_shape(content, read_json(ROOT / 'site/build/platform/content.schema.json'), 'content'))
    if errors: return errors, missing
    ready = published_override or manifest.get('status') == 'published'

    def fail(message): errors.append(message)
    def require(condition, message):
        if not condition: missing.append(message)
    def bi(value, label, required=True):
        if not isinstance(value, dict) or set(value) != {'en', 'zh'} or any(not isinstance(value.get(k), str) for k in ['en', 'zh']):
            fail(label + ': expected {en: string, zh: string}')
            return
        if required: require(bool(value['en'].strip()) and bool(value['zh'].strip()), label + ': English and Chinese are required')
        problem = order_problem(value['en'], value['zh'])
        if problem: require(False, 'QC-05 ' + label + ': ' + problem)
        # Deliberate visible placeholders cannot pass a publication gate.
        if ready and any(re.search(r'\b(?:TODO|TBD|placeholder)\b|待补|待核|待填', value[k], re.I) for k in ['en', 'zh']):
            fail(label + ': unresolved placeholder')
    def sourced(value, label):
        ids = value.get('sources', [])
        require(bool(ids), label + ': source references required')
        if not isinstance(ids, list) or any(x not in source_ids for x in ids): fail(label + ': unknown source reference')

    def check_structures(chapter_text, model_ids, muscle_ids=None):
        """ST-1 / QC-08: the chapter's structure list exists, is well formed and is covered by the text."""
        items = manifest.get('structures')
        if items is None: items = []
        if not isinstance(items, list): fail('structures must be a list'); return
        require(bool(items), 'ST-1 structure list is missing (topic.json structures)')
        seen = set()
        for item in items:
            if not isinstance(item, dict): fail('structure entries must be objects'); continue
            sid = item.get('id')
            label = 'structure ' + str(sid)
            if not ID.fullmatch(str(sid)) or sid in seen: fail(label + ': invalid or duplicate id')
            seen.add(sid)
            if item.get('kind') not in STRUCTURE_KINDS: fail(label + ': kind must be one of ' + ', '.join(STRUCTURE_KINDS))
            bi(item.get('name'), label + '.name')
            chapters = item.get('chapters')
            if not isinstance(chapters, list) or not chapters or any(c not in chapter_text for c in chapters):
                fail(label + ': chapters must list at least one of ' + ', '.join(chapter_text)); continue
            mapped = item.get('modelTermId')
            if mapped is not None and mapped not in model_ids: fail(label + ': modelTermId is not a real 3D id')
            needles = [item.get('name', {}).get('en', '')] + list(item.get('aliases', []))
            needles = [n.lower() for n in needles if isinstance(n, str) and n.strip()]
            for chapter in chapters:
                require(any(n in chapter_text[chapter] for n in needles), label + ': not mentioned in chapter ' + chapter)
        if muscle_ids is not None:
            listed = {i.get('id') for i in items if isinstance(i, dict) and i.get('kind') == 'muscle'}
            for mid in muscle_ids:
                require(mid in listed, str(mid) + ': muscle record is not in the ST-1 structure list')

    tid = manifest.get('id')
    if not isinstance(tid, str) or not ID.fullmatch(tid): fail('Invalid topic id')
    elif topic_dir.name != tid: fail('Topic id must match its directory')
    if manifest.get('schemaVersion') != 1: fail('Unsupported manifest schemaVersion')
    if manifest.get('status') not in ['draft', 'published']: fail('status must be draft or published')
    if manifest.get('adapter') not in ['shoulder', 'standard']: fail('Unknown adapter')
    for key in ['title', 'summary', 'region']: bi(manifest.get(key), key)
    viewer = manifest.get('viewer', {})
    if not isinstance(viewer, dict):
        fail('viewer must be an object'); viewer = {}
    if type(viewer.get('enabled')) is not bool: fail('viewer.enabled must be boolean')
    terms = viewer.get('terms', [])
    if not isinstance(terms, list): fail('viewer.terms must be a list'); terms = []
    term_ids = set()
    for term in terms:
        label = 'viewer term ' + str(term.get('id'))
        if not ID.fullmatch(str(term.get('id', ''))) or term.get('id') in term_ids: fail(label + ': invalid or duplicate id')
        term_ids.add(term.get('id'))
        bi(term.get('name'), label + '.name')
        kind = term.get('kind')
        if kind not in ['bone', 'muscle']: fail(label + ': invalid tissue kind')
        structures = term.get('structures', {})
        if set(structures) != {'right', 'left'}: fail(label + ': both anatomical sides required')
        for side in ['right', 'left']:
            key = structures.get(side)
            structure = models.get(key)
            if not structure or structure.get('objectCount', 0) < 1:
                fail(label + ': no renderable geometry for ' + side + ' ' + str(key)); continue
            if structure.get('addon') not in (None, tid):
                fail(label + ': ' + key + ' is in the ' + structure['addon'] + ' chapter 3D add-on, which this topic does not load'); continue
            expected_system = 'skeletal' if kind == 'bone' else 'muscular'
            if structure.get('system') != expected_system: fail(label + ': incorrect tissue mapping for ' + str(key))
            if key.endswith(('-right', '-left')) and not key.endswith('-' + side): fail(label + ': swapped anatomical side')
            name = term.get('name', {}).get('en', '')
            if normal_model_name(name) != normal_model_name(structure['name']):
                fail(label + ': name does not match model anatomy ' + structure['name'])
    if viewer.get('enabled'):
        if not terms or viewer.get('defaultTerm') not in term_ids: fail('Enabled viewer needs a mapped defaultTerm')
    elif viewer.get('defaultTerm') is not None: fail('Disabled viewer defaultTerm must be null')
    landmarks = viewer.get('landmarks', [])
    if not isinstance(landmarks, list): fail('viewer.landmarks must be a list'); landmarks = []
    landmark_ids = set()
    for landmark in landmarks:
        label = 'viewer landmark ' + str(landmark.get('id'))
        if not ID.fullmatch(str(landmark.get('id', ''))) or landmark.get('id') in landmark_ids or landmark.get('id') in term_ids:
            fail(label + ': invalid or duplicate id')
        landmark_ids.add(landmark.get('id'))
        bi(landmark.get('name'), label + '.name')
        if landmark.get('reviewStatus') not in ['reviewed', 'pending']: fail(label + ': invalid reviewStatus')
        for side in ['right', 'left']:
            sid = landmark.get('structures', {}).get(side)
            if sid not in {t.get('structures', {}).get(side) for t in terms}: fail(label + ': structure is outside this topic')
            position = landmark.get('positions', {}).get(side)
            if landmark.get('reviewStatus') == 'reviewed' or position is not None:
                if (not isinstance(position, list) or len(position) != 3 or
                    any(type(x) not in [int, float] or not math.isfinite(x) or abs(x) > 20 for x in position)):
                    fail(label + ': invalid finite model coordinates')
        if landmark.get('reviewStatus') == 'reviewed':
            review = landmark.get('review', {})
            if not review.get('reviewedBy', '').strip() or not valid_review_date(review.get('reviewedOn', '')):
                fail(label + ': reviewed coordinates need reviewer/date signoff')
            if not review.get('sourceUrls') or not all(valid_source_url(u) for u in review.get('sourceUrls', [])):
                fail(label + ': reviewed coordinates need anatomical source URLs')

    if manifest.get('adapter') == 'shoulder':
        # One explicit backwards-compatibility adapter for the first chapter's live URLs (reading.html,
        # reading-claude.html, ?term=), never a bypass: its content is checked like every other chapter.
        if tid != 'shoulder': fail('The shoulder adapter is reserved for the existing shoulder topic')
        for relative in ['library/shoulder/3d/public/reading.html', 'library/shoulder/3d/public/reading-claude.html']:
            if not (Path(root) / relative).is_file(): fail('Missing preserved shoulder output: ' + relative)
    app_terms, app_landmarks, app_points = chapter_3d(topic_dir)
    model_ids = set(term_ids) | landmark_ids | app_terms | set(app_landmarks)

    if not isinstance(content, dict): return errors + ['content.json must be an object'], missing
    if content.get('schemaVersion') != 1: fail('Unsupported content schemaVersion')
    for field in ['sections', 'muscles', 'landmarks', 'diagrams', 'review', 'papers', 'sources', 'acupoints', 'modelLinks']:
        if field in ('acupoints', 'modelLinks', 'papers') and field not in content: content = dict(content, **{field: []})
        if not isinstance(content.get(field), list):
            fail(field + ' must be a list')
            content = dict(content, **{field: []})
    source_ids = set()
    for source in content['sources']:
        sid = source.get('id')
        if not ID.fullmatch(str(sid)) or sid in source_ids: fail('Invalid or duplicate source id')
        source_ids.add(sid)
        if not source.get('title', '').strip(): fail('Source requires title')
        if not valid_source_url(source.get('url', '')): fail('Source requires a valid HTTPS URL')
    require(bool(source_ids), 'Evidence sources are missing')
    # AN-04: the C/T/L/S notation is shown in the innervation section; a chapter that writes its own
    # nerve-levels note there does not need the generic nerveNotation text.
    own_note = any(b.get('type') == 'note' and b.get('className') == 'nerve-levels'
                   for s in content['sections'] if isinstance(s, dict) and s.get('id') == 'innervation'
                   for b in reading.iter_blocks(s.get('blocks', [])) if isinstance(b, dict))
    if not own_note:
        for field in NERVE_NOTATION:
            bi(content.get('nerveNotation', {}).get(field), 'nerveNotation.' + field)

    diagrams = {}
    for diagram in content['diagrams']:
        did = diagram.get('id')
        if not ID.fullmatch(str(did)) or did in diagrams: fail('Invalid or duplicate diagram id')
        diagrams[did] = diagram
        bi(diagram.get('alt'), str(did) + '.alt')
        bi(diagram.get('caption'), str(did) + '.caption')
        sourced(diagram, str(did))
        try:
            asset = inside(topic_dir, diagram.get('file'))
            if asset.suffix.lower() != '.svg': raise ValueError('Anatomical diagrams must be editable SVG files')
            if not str(diagram.get('file')).startswith('figures/'):
                raise ValueError('Topic diagrams must be stored under figures/')
            svg = ET.fromstring(asset.read_text())
            if svg.tag.split('}')[-1] != 'svg': raise ValueError('Expected an SVG root element')
            for element in svg.iter():
                if element.tag.split('}')[-1] in ['script', 'foreignObject']:
                    raise ValueError('Active SVG content is not allowed')
                if any(k.lower().startswith('on') for k in element.attrib): raise ValueError('SVG event handlers are not allowed')
                if any(k.split('}')[-1] == 'href' and not v.startswith('#') for k, v in element.attrib.items()):
                    raise ValueError('SVG must not load remote or external assets')
            visible = ' '.join(' '.join(element.itertext()) for element in svg.iter() if element.tag.split('}')[-1] == 'text')
            for label in diagram.get('labels', []):
                bi(label.get('text'), str(did) + '.label')
                for lang in ['en', 'zh']:
                    text = label.get('text', {}).get(lang, '')
                    if text and text not in visible: fail(str(did) + ': declared label is absent from SVG text: ' + text)
            require(bool(diagram.get('labels')), str(did) + ': meaningful structure labels are required')
        except (ValueError, OSError, ET.ParseError, TypeError) as exc: fail(str(did) + ': ' + str(exc))

    def diagram_refs(ids, label, required=False):
        if not isinstance(ids, list) or any(i not in diagrams for i in ids): fail(label + ': unknown diagram reference')
        if required: require(bool(ids), label + ': anatomical diagram required')

    sections = content['sections']
    section_ids, five = [s.get('id') for s in sections], [s[0] for s in SECTIONS]
    if section_ids == five + ['papers'] and tid in LEGACY_PAPER_SECTION: pass  # pending move to daily (CH-01)
    elif section_ids != five: fail('Five sections must appear in the CH-01 order: ' + ', '.join(five))
    records = {'muscles': {m.get('id') for m in content['muscles']}, 'landmarks': {m.get('id') for m in content['landmarks']},
               'acupoints': {m.get('id') for m in content['acupoints']}, 'quiz': {m.get('id') for m in content['review']},
               'paper': {m.get('id') for m in content['papers']}}

    def cell(value, label):
        if isinstance(value, str):  # language-neutral cell: numbers, codes, abbreviations
            if CJK.search(value): require(False, 'QC-05 ' + label + ': Chinese text needs its English first ({en, zh})')
        else: bi(value, label, required=False)

    def check_block(block, label, nested=False):
        """Typed blocks (library/README.md); a block without type is the original heading + body block."""
        t = block.get('type', 'text')
        if t == 'text':
            bi(block.get('heading'), label + '.heading'); bi(block.get('body'), label + '.body')
            if any(x not in model_ids for x in block.get('termIds', [])): fail(label + ': unknown 3D term')
        elif t == 'heading':
            if block.get('level') not in (3, 4): fail(label + ': heading level must be 3 or 4')
            bi(block.get('text'), label + '.text')
        elif t in ('paragraph',): bi(block.get('text'), label + '.text')
        elif t == 'figure': diagram_refs([block.get('diagramId')], label)
        elif t == 'table':
            columns, rows = block.get('columns'), block.get('rows')
            if not isinstance(columns, list) or not columns or not isinstance(rows, list) or not rows: fail(label + ': table needs columns and rows'); return
            for i, c in enumerate(columns): cell(c, label + '.column' + str(i))
            for r, row in enumerate(rows):
                if not isinstance(row, list) or len(row) != len(columns): fail(label + ': row ' + str(r) + ' does not match the columns'); continue
                for i, c in enumerate(row): cell(c, label + '.row' + str(r) + '.' + str(i))
        elif t in ('note', 'cards'):
            for card in ([block] if t == 'note' else block.get('cards', [])):
                if card.get('heading') is not None: bi(card['heading'], label + '.heading')
                for key in ('paragraphs', 'items', 'definitions'):
                    for i, v in enumerate(card.get(key, [])): bi(v, label + '.' + key + str(i))
            if t == 'cards' and block.get('layout', 'columns') not in ('columns', 'stages', 'stack'): fail(label + ': unknown cards layout')
        elif t in records:
            ids = reading.block_ids(block)
            if not ids or any(i not in records[t] for i in ids): fail(label + ': unknown ' + t + ' record')
        elif t == 'steps':
            for i, item in enumerate(block.get('items', [])): bi(item.get('heading'), label + '.step' + str(i)); bi(item.get('text'), label + '.step' + str(i))
        elif t == 'mnemonic':
            bi(block.get('text'), label + '.text')
            if not isinstance(block.get('original'), str) or not CJK.search(block['original']): fail(label + ': mnemonic original must be the Chinese text')
        elif t == 'details':
            if nested: fail(label + ': details cannot be nested')
            bi(block.get('summary'), label + '.summary')
            for i, inner in enumerate(block.get('blocks', [])): check_block(inner, label + '.' + str(i), True)
        elif t == 'sources':
            if not block.get('ids') or any(x not in source_ids for x in block['ids']): fail(label + ': unknown source reference')
            for key in ('label', 'note'):
                if block.get(key) is not None: bi(block[key], label + '.' + key)
        elif t != 'nerveNotation': fail(label + ': unknown block type ' + str(t))

    for section in sections:
        label = 'section ' + str(section.get('id'))
        bi(section.get('title'), label + '.title')
        bi(section.get('overview'), label + '.overview')
        if section.get('navTitle') is not None: bi(section['navTitle'], label + '.navTitle')
        placed = [b['diagramId'] for b in reading.iter_blocks(section.get('blocks', [])) if b.get('type') == 'figure']
        diagram_refs(section.get('diagramIds', []), label)
        if section.get('id') in ['anatomy', 'innervation', 'movement', 'clinical']:
            require(bool(section.get('diagramIds') or placed), label + ': anatomical diagram required')
        for i, block in enumerate(section.get('blocks', [])):
            if not isinstance(block, dict): fail(label + ': blocks must be objects'); continue
            check_block(block, label + '.block' + str(i))
    require(bool(content['muscles']), 'Muscle attachment/course records are missing')
    seen_muscles = set()
    for muscle in content['muscles']:
        mid = muscle.get('id')
        if not ID.fullmatch(str(mid)) or mid in seen_muscles: fail('Invalid or duplicate muscle id')
        seen_muscles.add(mid)
        bi(muscle.get('name'), str(mid) + '.name')
        for key in MUSCLE_FIELDS: bi(muscle.get(key), str(mid) + '.' + key)
        course = muscle.get('course', {}).get('en', '')
        if course and not all(re.search(pattern, course, re.I) for pattern in [r'\boriginates?\b|\barises?\b', r'\bfrom\b', r'\binserts?\b|\battaches?\b']):
            require(False, str(mid) + ': course must be a complete English origin-to-insertion description')
        sourced(muscle, str(mid))
        mapped = muscle.get('modelTermId')
        if mapped:
            term = next((t for t in terms if t['id'] == mapped), None)
            if term is None and mapped in app_terms: pass  # defined by the chapter's own 3D vocabulary
            elif not term or term.get('kind') != 'muscle': fail(str(mid) + ': invalid muscle 3D mapping')
            elif normal_model_name(term['name']['en']) != normal_model_name(muscle['name']['en']): fail(str(mid) + ': muscle maps to a different anatomy')
        else:
            bi(muscle.get('modelUnavailableReason'), str(mid) + '.modelUnavailableReason')
        refs = muscle.get('diagramIds', [])
        diagram_refs(refs, str(mid), True)
        for label_kind in ['origin', 'insertion']:
            found = any(label.get('kind') == label_kind and label.get('muscleId') == mid
                        and label_kind in label.get('text', {}).get('en', '').lower()
                        and ('起点' if label_kind == 'origin' else '止点') in label.get('text', {}).get('zh', '')
                        for did in refs if did in diagrams for label in diagrams[did].get('labels', []))
            require(found, str(mid) + ': a diagram must visibly label its ' + label_kind)
    require(bool(content['landmarks']), 'Named bony landmark records and diagrams are missing')
    for landmark in content['landmarks']:
        bi(landmark.get('name'), 'landmark.name'); bi(landmark.get('description'), 'landmark.description')
        sourced(landmark, 'landmark')
        diagram_refs(landmark.get('diagramIds', []), 'landmark', True)
        mapped = landmark.get('modelTermId')
        if mapped:
            term = next((t for t in terms if t['id'] == mapped), None)
            if not term or term.get('kind') != 'bone': fail('Bony landmark needs a bone modelTermId')
        marker_id = landmark.get('viewerLandmarkId')
        if marker_id and marker_id in app_landmarks and not any(l.get('id') == marker_id for l in landmarks):
            if app_landmarks[marker_id] != mapped: fail('Landmark marker belongs to another structure: ' + marker_id)
        elif marker_id:
            marker = next((l for l in landmarks if l['id'] == marker_id), None)
            if not mapped: fail('Landmark marker needs its parent bone modelTermId')
            if not marker or marker.get('reviewStatus') != 'reviewed': fail('Landmark marker is not reviewed')
            elif mapped and term and marker.get('structures') != term.get('structures'): fail('Landmark marker belongs to another structure')
            elif normal_model_name(marker['name']['en']) != normal_model_name(landmark['name']['en']): fail('Landmark marker refers to a different anatomical name')
        else:
            bi(landmark.get('modelUnavailableReason'), 'landmark.modelUnavailableReason')
    require(bool(content['review']), 'Full English/Chinese review questions and answers are missing')
    for review in content['review']:
        for field in ['question', 'answer']: bi(review.get(field), 'review.' + field)
        if review.get('mnemonic') is not None: bi(review['mnemonic'], 'review.mnemonic')
        sourced(review, 'review')
        require(len(review.get('answer', {}).get('en', '').split()) >= 12, 'Review answer must include a complete English explanation, not only a mnemonic')
    for paper in content['papers']:
        require(bool(paper.get('citation', '').strip()), 'Paper citation is missing')
        for field in PAPER_FIELDS: bi(paper.get(field), 'paper.' + field)
        sourced(paper, 'paper')
        require(bool(paper.get('terms')), 'Paper methodology terms are missing')
        for term in paper.get('terms', []):
            bi(term.get('term'), 'paper.term'); bi(term.get('explanation'), 'paper.explanation')
    for link in content['modelLinks']:  # extra names the reading page links to the 3D viewer (AN-40)
        if link.get('term') is not None and link['term'] not in model_ids: fail('modelLinks ' + str(link.get('en')) + ': not a real 3D id')
    seen_points = set()
    for point in content['acupoints']:
        pid = point.get('id'); label = 'acupoint ' + str(pid)
        if not ID.fullmatch(str(pid)) or pid in seen_points: fail(label + ': invalid or duplicate id')
        seen_points.add(pid)
        if not str(point.get('code', '')).strip(): fail(label + ': code is required')
        bi(point.get('name'), label + '.name')
        for key in ('location', 'safety'): bi(point.get(key), label + '.' + key)  # AN-20
        for key in ('layers', 'target', 'howToFind'):
            if point.get(key) is not None: bi(point[key], label + '.' + key)
        sourced(point, label)
        if point.get('modelPointId') is not None and point['modelPointId'] not in app_points: fail(label + ': modelPointId is not a real 3D point')
    review_blocks = next((b for s, b in reading.resolved_sections(content) if s.get('id') == 'review'), [])
    require(any(b.get('type') == 'mnemonic' for b in reading.iter_blocks(review_blocks)) or any(r.get('mnemonic') for r in content['review']),
            'Review needs at least one mnemonic with its full English and Chinese wording (CH-01 05)')
    chapter_text = {section.get('id'): reading.section_text(content, section, blocks).lower()
                    for section, blocks in reading.resolved_sections(content) if section.get('id') in set(section_ids) & (set(five) | {'papers'})}
    check_structures(chapter_text, model_ids, [m.get('id') for m in content['muscles']])
    check_pronunciation(manifest, topic_dir, fail, require)
    qa = content.get('qa', {})
    require(bool(qa.get('reviewedBy', '').strip()), 'Reviewer signoff is missing')
    require(valid_review_date(qa.get('reviewedOn', '')), 'A valid review date is required (YYYY-MM-DD)')
    for key in QA_CHECKS: require(qa.get('checks', {}).get(key) is True, 'QA pending: ' + key)
    if manifest.get('pdf'):
        pdf = manifest['pdf']
        try:
            path = inside(topic_dir, pdf.get('file'))
            if path.suffix != '.pdf' or not path.is_file(): fail('Declared PDF is missing')
            if pdf.get('contentDigest') != content_digest(content, topic_dir): fail('PDF is stale relative to content/diagrams')
            if not pdf.get('reviewedBy', '').strip() or not valid_review_date(pdf.get('reviewedOn', '')): fail('PDF visual review signoff is missing')
        except (ValueError, OSError, KeyError) as exc: fail('PDF: ' + str(exc))
    if not errors and ready:
        try:
            page, _ = reading.render_page(chapter(manifest, content, topic_dir, root))
            body = re.search(r'<main\b.*?</main>', page, re.S)  # the reading text; <html lang="en"> wraps the whole page
            for problem in html_order_problems(body.group() if body else page): require(False, 'QC-05 rendered page: ' + problem)
        except (KeyError, ValueError, OSError) as exc: fail('Reading page cannot be rendered: ' + str(exc))
    if ready: errors.extend(missing)
    return errors, missing


def discover(topics_dir=None, root=ROOT):
    topics_dir = Path(topics_dir or Path(root) / 'library')
    result = []
    for path in sorted(topics_dir.glob('*/topic.json')):
        if path.parent.is_symlink(): raise ValueError('Symlinked topic directories are not allowed')
        manifest = read_json(path)
        if not isinstance(manifest, dict): raise ValueError(str(path) + ': topic.json must contain an object')
        content = read_json(path.parent / 'content.json') if (path.parent / 'content.json').exists() else None
        result.append((manifest, content, path.parent))
    return result


def links(manifest):
    tid = manifest['id']
    output = {'home': './topics/' + tid + '/index.html'}
    if manifest['adapter'] == 'shoulder':
        output.update(reading='./reading.html', claude='./reading-claude.html', pdf='./downloads/shoulder-bilingual.pdf', markdown='./reading.md')
    elif manifest['status'] == 'published':
        output.update(reading='./topics/' + tid + '/reading.html', markdown='./topics/' + tid + '/reading.md')
        if manifest.get('pdf'): output['pdf'] = './topics/' + tid + '/' + manifest['pdf']['file']
    if manifest['viewer']['enabled']:
        output['viewer'] = './?' + urlencode({'topic': tid, 'term': manifest['viewer']['defaultTerm']})
    return output


def esc(value): return html.escape(str(value), quote=True)


def bilingual(value, tag='p', cls=''):
    return f'<{tag} class="bilingual {cls}"><span lang="en">{esc(value["en"])}</span><span lang="zh-CN" class="zh">{esc(value["zh"])}</span></{tag}>'


def md_pair(value): return value['en'] + '\n\n' + value['zh'] + '\n\n'


def shell(manifest, body):
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(manifest["title"]["en"])} · {esc(manifest["title"]["zh"])}</title>'
            '<link rel="stylesheet" href="../../topic.css"></head><body><header><a href="../../study.html">Anatomy study · 解剖学习</a></header><main>'
            + bilingual(manifest['title'], 'h1') + body + '</main></body></html>')


def render(manifest, content, missing, topic_dir=None, root=ROOT):
    tid, status = manifest['id'], manifest['status']
    entry_links = links(manifest)
    local_link = lambda link: '../../' + link.removeprefix('./')
    label_pairs = {'reading': pair('Read the course', '阅读课程'), 'claude': pair('Claude reading edition', 'Claude 阅读版'),
                   'pdf': pair('Download reviewed PDF', '下载已核验 PDF'), 'markdown': pair('Download Markdown', '下载 Markdown'),
                   'viewer': pair('Explore the 3D model', '查看三维模型')}
    if manifest['adapter'] == 'shoulder':  # the reviewed PDF predates the content.json edition; restore the label after re-exporting it
        label_pairs['pdf'] = pair('Download PDF (2026-10-06 edition, not yet updated)', '下载 PDF（2026-10-06 版，尚未随正文更新）')
    nav = '<nav class="cards">' + ''.join('<a class="card" href="' + esc(local_link(url)) + '">' + bilingual(label_pairs[key], 'strong') + '</a>'
                                               for key, url in entry_links.items() if key in label_pairs) + '</nav>'
    if status == 'draft':
        notice = bilingual(pair('Draft — the course is not yet available.', '草稿：课程尚未完成，不能作为已核验的学习材料。'), 'p', 'notice')
        if manifest['viewer']['enabled']:
            notice += bilingual(pair('The preview contains only the mapped model structures. Muscles, attachment labels and the five-part course still need preparation and review.',
                                     '预览仅包含已匹配的模型结构；肌肉、起止点标注和五部分课程仍需编写与核验。'))
        body = notice + nav + bilingual(pair('Preparation checklist', '待完成项目'), 'h2') + '<ul class="checklist">'
        checklist = [pair('Complete all five bilingual sections.', '完成五部分双语正文。'),
                     pair('Add sourced muscle origins, insertions, courses and actions.', '补齐有来源依据的肌肉起止点、走行与动作。'),
                     pair('Label anatomical diagrams, nerves and bony landmarks.', '在解剖图中标出神经、骨性结构与肌肉起止点。'),
                     pair('Match model links and review any landmark coordinates.', '匹配三维模型链接并核验骨性标志坐标。'),
                     pair('Write complete answers and mnemonics.', '编写完整答案与简记。'),
                     pair('Review sources and desktop/mobile layouts before publication.', '发布前核验来源与桌面、窄屏显示效果。')]
        body += ''.join('<li>' + bilingual(item, 'span') + '</li>' for item in checklist) + '</ul>'
        return shell(manifest, body), shell(manifest, body), '# ' + manifest['title']['en'] + ' · ' + manifest['title']['zh'] + '\n\nDraft · 草稿：课程尚未发布。\n\n'
    if manifest['adapter'] == 'shoulder':
        body = bilingual(manifest['summary']) + nav
        body += bilingual(pair('Study muscle attachments, nerve pathways and movement in English, with Chinese translations and linked 3D anatomy.', '结合中文翻译与三维解剖，用英语学习肌肉起止点、神经走行与运动功能。'))
        return shell(manifest, body), shell(manifest, body), '# ' + manifest['title']['en'] + ' · ' + manifest['title']['zh'] + '\n\n[Read the maintained course · 阅读维护中的课程](../../reading.md)\n'

    page, markdown = reading.render_page(chapter(manifest, content, topic_dir, root))
    landing = shell(manifest, bilingual(manifest['summary']) + nav)
    return landing, page, markdown


def chapter(manifest, content, topic_dir, root=ROOT, **paths):
    """Everything the reading renderer needs for one chapter; paths default to topics/<id>/ in the site."""
    pron = Path(topic_dir) / 'pronunciation.json'
    audio = reading.load_audio(Path(root) / 'library/shoulder/3d/public/audio/manifest.json')
    return reading.Chapter(manifest, content, topic_dir, read_json(pron) if pron.is_file() else {}, audio,
                           **{'model_base': '../../', 'audio_base': '../../', **paths})


def build(topics_dir=None, output=None, root=ROOT):
    output = Path(output or Path(root) / 'library/shoulder/3d/public')
    records = discover(topics_dir, root)
    models = catalog_models(root)
    checked = []
    for manifest, content, path in records:
        errors, missing = validate(manifest, content, path, models, root)
        if errors: raise ValueError(str(manifest.get('id', path.name)) + ':\n  ' + '\n  '.join(errors))
        checked.append((manifest, content, path, missing))
    # Validate the entire catalog before mutating generated outputs.
    output.mkdir(parents=True, exist_ok=True)
    generated = output / 'topics'
    if generated.exists(): shutil.rmtree(generated)
    generated.mkdir()
    catalog = []
    for manifest, content, path, missing in checked:
        target = generated / manifest['id']
        target.mkdir()
        landing, page, markdown = render(manifest, content, missing, path, root)
        (target / 'index.html').write_text(landing, encoding='utf-8')
        (target / 'reading.html').write_text(page, encoding='utf-8')
        (target / 'reading.md').write_text(markdown, encoding='utf-8')
        public_manifest = dict(manifest, links=links(manifest), missing=missing)
        addons = topic_addons(manifest, path)
        if addons: public_manifest['viewer'] = dict(manifest['viewer'], addons=addons)
        write_json(target / 'data.json', {'topic': public_manifest, 'content': content if manifest['status'] == 'published' else None})
        if manifest['adapter'] == 'standard' and manifest['status'] == 'published':
            for diagram in content['diagrams']:
                destination = inside(target, diagram['file']); destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(inside(path, diagram['file']), destination)
            if manifest.get('pdf'):
                destination = inside(target, manifest['pdf']['file']); destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(inside(path, manifest['pdf']['file']), destination)
        catalog.append(public_manifest)
    write_json(output / 'topics.json', {'schemaVersion': 1, 'topics': catalog})
    shutil.copy2(Path(root) / 'site/build/platform/topic.css', output / 'topic.css')
    return catalog
