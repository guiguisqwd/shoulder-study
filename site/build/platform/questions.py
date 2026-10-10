"""Chapter question bank 【试用】(AN-60 to AN-66, ST-10, QC-10): library/<id>/questions.json.

A bank entry either points at a record that already exists in content.json (a muscle, an acupoint or a
review question) and lets this module build the prompt and answer from it, or carries its own prompt,
answer and scoring points and names the part of the chapter its answer comes from. Every resolved
question has the same shape, so daily packs, the weekly quiz and the review center can all read
`expand()` without knowing how the entry was written.

    python3 site/build/platform/questions.py library/shoulder            # summary
    python3 site/build/platform/questions.py library/shoulder --markdown # every question with its answer
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

SCHEMA = 'dpt-question-bank/1'
BANK_FILE = 'questions.json'
ID = re.compile(r'^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$')
PARTS = ['anatomy', 'innervation', 'movement', 'clinical', 'review']   # CH-01
TYPES = {
    'recall': ('Recall', '回忆'),
    'term': ('Term', '术语'),
    'locate': ('Locate', '定位'),
    'reason': ('Reasoning', '推理'),
    'case': ('Case', '病例'),
}
GRADES = {'know': ('Know', '会'), 'fuzzy': ('Fuzzy', '模糊'), 'miss': ('Miss', '不会')}   # AN-64
MIN_PER_PART = 2          # AN-62
MIN_REASONING = 3         # AN-62: reason + case questions per chapter
POINTS = (2, 5)           # AN-63
FIELDS = {                # record kind -> field -> label; the order here is the order of the answer
    'muscles': {
        'origin': ('Origin', '起点'), 'insertion': ('Insertion', '止点'), 'course': ('Course', '走行'),
        'innervation': ('Innervation', '神经支配'), 'actions': ('Action', '动作'),
    },
    'acupoints': {
        'location': ('Location', '定位'), 'howToFind': ('How to find it', '怎么找'), 'layers': ('Layers (superficial → deep)', '层次（浅 → 深）'),
        'target': ('Target', '对应目标'), 'safety': ('Safety', '安全提示'),
    },
}
REQUIRED_FIELDS = {'muscles': ['origin', 'insertion', 'innervation', 'actions'], 'acupoints': ['location']}   # AN-62


def load(topic_dir):
    """The chapter's bank, or None while it has none (allowed while AN-60 is on trial)."""
    path = Path(topic_dir) / BANK_FILE
    if not path.is_file(): return None
    return json.loads(path.read_text(encoding='utf-8'))


def _records(content):
    return {kind: {r.get('id'): r for r in content.get(kind, []) if isinstance(r, dict)}
            for kind in ['muscles', 'acupoints', 'review']}


def _join(parts, sep):
    return sep.join(p for p in parts if p)


def resolve(entry, content, records=None):
    """One bank entry -> {id, type, part, covers, prompt, answer, points, from, sources}."""
    records = records or _records(content)
    out = {k: entry.get(k) for k in ['id', 'type', 'part', 'covers']}
    ref = entry.get('record')
    if not ref:
        out.update(prompt=entry['prompt'], answer=entry['answer'], points=entry['points'], sources=[])
        out['from'] = 'sections/' + entry['from']
        return out
    kind, rid = ref.split('/', 1)
    rec = records[kind][rid]
    out['from'] = ref
    out['sources'] = list(rec.get('sources', []))
    if kind == 'review':
        out.update(prompt=rec['question'], answer=rec['answer'], points=entry['points'])
        return out
    asked = [f for f in FIELDS[kind] if f in entry['ask']]
    labels = FIELDS[kind]
    name = rec['name']
    head = {'en': name['en'] + (' (' + rec['code'] + ')' if rec.get('code') else ''),
            'zh': name['zh'] + (' ' + rec['code'] if rec.get('code') else '')}
    out['prompt'] = {'en': head['en'] + ': give its ' + _join([labels[f][0].lower() for f in asked[:-1]], ', ') + (' and ' if len(asked) > 1 else '') + labels[asked[-1]][0].lower() + '.',
                     'zh': head['zh'] + '：说出' + '、'.join(labels[f][1] for f in asked) + '。'}
    out['points'] = [{'en': labels[f][0] + ': ' + rec[f]['en'], 'zh': labels[f][1] + '：' + rec[f]['zh']} for f in asked]
    out['answer'] = {'en': _join([p['en'].rstrip('.') for p in out['points']], '; ') + '.', 'zh': _join([p['zh'].rstrip('。') for p in out['points']], '；') + '。'}
    return out


def expand(bank, content):
    records = _records(content)
    out = [resolve(e, content, records) for e in bank.get('questions', [])]
    for q in out: q['key'] = bank['chapter'] + '/' + q['id']   # AN-65: what answer records point to
    return out


def check(manifest, content, topic_dir, fail, require, bi):
    """QC-10: format errors always fail; coverage gaps are pending items (errors once published)."""
    try: bank = load(topic_dir)
    except (ValueError, OSError) as exc: fail(BANK_FILE + ': ' + str(exc)); return
    if bank is None: return   # AN-60 【试用】: chapters without a bank are not held back yet
    if not isinstance(bank, dict) or bank.get('schema') != SCHEMA or not isinstance(bank.get('questions'), list):
        fail(BANK_FILE + ': expected {"schema": "' + SCHEMA + '", "chapter": ..., "questions": [...]}'); return
    if bank.get('chapter') != manifest.get('id'): fail(BANK_FILE + ': chapter must be the topic id')
    records = _records(content)
    structures = {s.get('id') for s in manifest.get('structures') or [] if isinstance(s, dict)}
    seen, covered, per_part, reasoning, asked_records = set(), set(), {p: 0 for p in PARTS}, 0, {}
    for entry in bank['questions']:
        if not isinstance(entry, dict): fail(BANK_FILE + ': every question must be an object'); continue
        qid = entry.get('id')
        label = 'question ' + str(qid)
        if not isinstance(qid, str) or not ID.fullmatch(qid) or qid in seen: fail(label + ': invalid or duplicate id'); continue
        seen.add(qid)
        if entry.get('type') not in TYPES: fail(label + ': type must be one of ' + ', '.join(TYPES)); continue
        if entry.get('part') not in PARTS: fail(label + ': part must be one of ' + ', '.join(PARTS)); continue
        covers = entry.get('covers')
        if not isinstance(covers, list) or not covers or any(not isinstance(c, str) for c in covers): fail(label + ': covers must list structure ids'); continue
        for sid in covers:
            if sid not in structures: fail(label + ': covers unknown structure ' + sid + ' (topic.json structures)')
        ref = entry.get('record')
        if ref is not None:
            kind, _, rid = str(ref).partition('/')
            if kind not in records or rid not in records[kind]: fail(label + ': record ' + str(ref) + ' does not exist in content.json'); continue
            if any(k in entry for k in ['prompt', 'answer', 'from']): fail(label + ': a record question takes its prompt and answer from content.json'); continue
            if kind == 'review':
                if 'ask' in entry: fail(label + ': ask is only for muscle and acupoint records'); continue
            else:
                ask = entry.get('ask')
                if not isinstance(ask, list) or not ask or any(f not in FIELDS[kind] for f in ask): fail(label + ': ask must list fields of ' + ', '.join(FIELDS[kind])); continue
                for f in ask:
                    if not isinstance(records[kind][rid].get(f), dict): fail(label + ': ' + ref + ' has no ' + f); break
                else:
                    if 'points' in entry: fail(label + ': a ' + kind + ' question scores the asked fields; do not add points')
                    asked_records.setdefault(ref, set()).update(ask)
                    covered.update(covers); per_part[entry['part']] += 1
                    reasoning += entry['type'] in ('reason', 'case')
                continue
            asked_records.setdefault(ref, set())
        else:
            if entry.get('from') not in PARTS: fail(label + ': from must name the CH-01 part the answer comes from'); continue
            bi(entry.get('prompt'), label + '.prompt'); bi(entry.get('answer'), label + '.answer')
        points = entry.get('points')
        if not isinstance(points, list) or not POINTS[0] <= len(points) <= POINTS[1]:
            fail(label + ': needs %d to %d scoring points' % POINTS); continue
        for i, p in enumerate(points): bi(p, label + '.points[%d]' % i)
        covered.update(covers); per_part[entry['part']] += 1
        reasoning += entry['type'] in ('reason', 'case')
    # AN-62 coverage
    for sid in sorted(structures - covered): require(False, 'QC-10 no question covers structure ' + sid + ' (' + BANK_FILE + ')')
    for kind, need in REQUIRED_FIELDS.items():
        for rid, rec in records[kind].items():
            have = asked_records.get(kind + '/' + rid, set())
            want = [f for f in need if isinstance(rec.get(f), dict)]
            if kind == 'acupoints' and isinstance(rec.get('layers'), dict): want.append('layers')
            missing = [f for f in want if f not in have]
            if missing: require(False, 'QC-10 ' + kind + '/' + rid + ' is not asked: ' + ', '.join(missing))
    for rid in records['review']:
        require('review/' + rid in asked_records, 'QC-10 review question ' + rid + ' is not in the bank')
    for part, n in per_part.items():
        require(n >= MIN_PER_PART, 'QC-10 part ' + part + ' has %d questions (at least %d)' % (n, MIN_PER_PART))
    require(reasoning >= MIN_REASONING, 'QC-10 %d reasoning or case questions (at least %d)' % (reasoning, MIN_REASONING))


def markdown(manifest, questions):
    lines = ['# ' + manifest['title']['en'] + ' · ' + manifest['title']['zh'] + ' — question bank 题库', '',
             '%d questions. Answer aloud first, then open the answer and grade yourself: ' % len(questions)
             + ' / '.join(en + ' ' + zh for en, zh in GRADES.values()) + '.', '']
    for part in PARTS:
        qs = [q for q in questions if q['part'] == part]
        if not qs: continue
        lines += ['## ' + part + ' (%d)' % len(qs), '']
        for n, q in enumerate(qs, 1):
            t = TYPES[q['type']]
            lines += ['### %d. %s' % (n, q['prompt']['en']), q['prompt']['zh'], '',
                      '`' + q['id'] + '` · ' + t[0] + ' ' + t[1] + ' · covers: ' + ', '.join(q['covers']) + ' · from: ' + q['from'], '',
                      '**Answer 答案**', '', q['answer']['en'], '', q['answer']['zh'], '', '**Scoring points 评分要点**', '']
            lines += ['- ' + p['en'] + ' / ' + p['zh'] for p in q['points']]
            lines.append('')
    return '\n'.join(lines)


def main(argv):
    topic_dir = Path(argv[1])
    manifest = json.loads((topic_dir / 'topic.json').read_text(encoding='utf-8'))
    content = json.loads((topic_dir / 'content.json').read_text(encoding='utf-8'))
    bank = load(topic_dir)
    if bank is None: print(manifest['id'] + ': no ' + BANK_FILE); return 0
    questions = expand(bank, content)
    if '--markdown' in argv: print(markdown(manifest, questions)); return 0
    by = lambda key: ', '.join('%s %d' % (k, sum(q[key] == k for q in questions)) for k in (PARTS if key == 'part' else TYPES))
    print('%s: %d questions · %s · %s' % (manifest['id'], len(questions), by('part'), by('type')))
    return 0


if __name__ == '__main__': sys.exit(main(sys.argv))
