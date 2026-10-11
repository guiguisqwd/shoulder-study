"""Render one library chapter's content.json into its reading page (HTML) and Markdown.

One source (content.json + figures/ + pronunciation.json) produces both outputs, so they cannot drift
(G-08). Block and record formats are documented in library/README.md and content.schema.json.
"""
from __future__ import annotations
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode

PLATFORM = Path(__file__).resolve().parent
INLINE = re.compile(r'\*\*(.+?)\*\*|\[([^\]]+)\]\((https://[^)\s]+)\)')
PRON_HEADING = {'en': 'Pronunciation', 'zh': '读音'}


def esc(value):
    return html.escape(str(value), quote=True)


def inline(text):
    """Bilingual strings may carry **bold** and [label](https://source) markup."""
    out, last = [], 0
    for m in INLINE.finditer(text):
        out.append(esc(text[last:m.start()]))
        if m.group(1) is not None: out.append('<b>' + esc(m.group(1)) + '</b>')
        else: out.append('<a href="' + esc(m.group(3)) + '" target="_blank" rel="noreferrer">' + esc(m.group(2)) + '</a>')
        last = m.end()
    return ''.join(out) + esc(text[last:])


def plain(text):
    return INLINE.sub(lambda m: m.group(1) if m.group(1) is not None else m.group(2), text)


def pair_spans(value, tag='span'):
    """English, then its Chinese translation, inside one parent (AN-01)."""
    en = f'<{tag} lang="en">{inline(value["en"])}</{tag}>' if value.get('en') else ''
    zh = f'<{tag} class="translation" lang="zh-Hans">{inline(value["zh"])}</{tag}>' if value.get('zh') else ''
    return en + zh


def pair_div(value):
    return '<div class="bilingual-pair">' + pair_spans(value, 'p') + '</div>'


def md_pair(value, sep='\n\n'):
    return sep.join(v for v in [value.get('en', ''), value.get('zh', '')] if v)


def md_inline_pair(value):
    return ' · '.join(v for v in [value.get('en', ''), value.get('zh', '')] if v)


def cell_html(cell):
    return esc(cell) if isinstance(cell, str) else pair_spans(cell)


def cell_md(cell):
    text = cell if isinstance(cell, str) else '<br>'.join(v for v in [cell.get('en', ''), cell.get('zh', '')] if v)
    return text.replace('|', '\\|').replace('\n', ' ')


class Chapter:
    """Everything a renderer needs about one chapter, resolved once."""

    def __init__(self, manifest, content, topic_dir, pronunciation=None, audio=None,
                 model_base='../../', audio_base='../../', figure_prefix=''):
        self.manifest, self.content, self.dir = manifest, content, Path(topic_dir)
        self.pron = pronunciation or {}
        self.audio = audio or {}
        self.model_base, self.audio_base, self.figure_prefix = model_base, audio_base, figure_prefix
        self.sources = {s['id']: s for s in content.get('sources', [])}
        self.diagrams = {d['id']: d for d in content.get('diagrams', [])}
        self.muscles = {m['id']: m for m in content.get('muscles', [])}
        self.landmarks = {m['id']: m for m in content.get('landmarks', [])}
        self.acupoints = {m['id']: m for m in content.get('acupoints', [])}
        self.review = {m['id']: m for m in content.get('review', [])}
        self.papers = {m['id']: m for m in content.get('papers', [])}
        self.figures_used = []
        self.terms = self._link_terms()
        # Acupoint codes in running text (e.g. "Bingfeng (SI12)") open that point in the 3D viewer.
        self.point_codes = {p['code'].lower(): p['modelPointId'] for p in content.get('acupoints', []) if p.get('modelPointId')}
        names = sorted(set(self.terms) | set(self.point_codes), key=len, reverse=True)
        self.term_pattern = re.compile(r'(?<![A-Za-z0-9])(?:' + '|'.join(re.escape(n) for n in names) + r')(?![A-Za-z0-9])', re.I) if names else None

    def _term_url(self, label):
        key = label.lower()
        if key in self.point_codes and label.isupper(): return self.model_url(point=self.point_codes[key])
        term = self.terms.get(key)
        return self.model_url(term) if term else None

    # ------------------------------------------------------------------ 3D links (AN-40, AN-41)
    def _link_terms(self):
        """Every name in the ST-1 list and modelLinks; names without a model id stay plain text but
        still stop a shorter name inside them from linking (e.g. deltoid tuberosity vs deltoid)."""
        terms = {}
        for item in self.manifest.get('structures') or []:
            if item.get('kind') in ('paper', 'acupoint'): continue
            for name in [item['name']['en']] + list(item.get('aliases', [])):
                terms.setdefault(name.lower(), item.get('modelTermId'))
        for link in self.content.get('modelLinks', []):
            terms[link['en'].lower()] = link.get('term')
        return terms

    def model_url(self, term=None, point=None, landmark=None):
        query = {}
        if self.manifest.get('adapter') != 'shoulder': query['topic'] = self.manifest['id']
        if term: query['term'] = term
        if landmark: query['landmark'] = landmark
        if point: query['point'] = point
        return self.model_base + '?' + urlencode(query)

    def landmark_url(self, lm):
        marker = lm.get('viewerLandmarkId')
        if marker and any(l.get('id') == marker for l in self.manifest.get('viewer', {}).get('landmarks', [])):
            return self.model_url(lm.get('modelTermId'), landmark=marker)
        if marker: return self.model_url(marker)  # a marker of the chapter's own 3D part is addressed as a term
        return self.model_url(lm['modelTermId']) if lm.get('modelTermId') else None

    def link_text(self, markup):
        """Link anatomical names in rendered text to the 3D viewer, outside links, figures and scripts."""
        if not self.term_pattern: return markup
        def sub(match):
            label = match.group(); url = self._term_url(label)
            if not url: return label
            return (f'<a class="anatomy-link" href="{esc(url)}" target="_blank" rel="noreferrer" '
                    f'title="Explore {esc(label)} in 3D · 在三维模型中查看">{label}</a>')
        parser = _Linker(lambda data: self.term_pattern.sub(sub, data))
        parser.feed(markup); parser.close()
        return ''.join(parser.parts)

    def link_md(self, text):
        if not self.term_pattern: return text
        def sub(match):
            label = match.group(); url = self._term_url(label)
            return f'[{label}]({url})' if url else label
        parts = re.split(r'(!?\[[^\]]*\]\([^)]*\)|<[^>]+>|`[^`]*`)', text)
        return ''.join(p if i % 2 else self.term_pattern.sub(sub, p) for i, p in enumerate(parts))

    # ------------------------------------------------------------------ figures (AN-10, AN-16)
    def svg(self, diagram_id):
        diagram = self.diagrams[diagram_id]
        markup = (self.dir / diagram['file']).read_text(encoding='utf-8')
        markup = re.sub(r'<\?xml[^>]*\?>\s*', '', markup)
        number = re.match(r'figures/(\d+)', diagram['file'])
        self.figures_used.append(diagram_id)
        def label(match):
            raw = match.group(0)
            text = html.unescape(re.sub(r'<[^>]+>', '', raw)).strip().lower()
            for name, term in sorted(self.terms.items(), key=lambda kv: len(kv[0]), reverse=True):
                if text.startswith(name) and (len(text) == len(name) or not text[len(name)].isascii() or not text[len(name)].isalpha()):
                    if term: return f'<a href="{esc(self.model_url(term))}" target="_blank" aria-label="Explore {esc(name)} in 3D">{raw}</a>'
                    break
            return raw
        markup = re.sub(r'<text\b[^>]*>.*?</text>', label, markup, flags=re.S)
        attr = f' data-figure="{number.group(1)}"' if number else f' data-figure="{esc(diagram_id)}"'
        return re.sub(r'<svg\b', '<svg' + attr, markup, count=1)

    def figure_html(self, diagram_id, size=''):
        d = self.diagrams[diagram_id]
        aria = esc(d['alt']['en'] + ' · ' + d['alt']['zh'])
        caption = inline(d['caption']['en']) + ('<br><span lang="zh-Hans">' + inline(d['caption']['zh']) + '</span>' if d['caption'].get('zh') else '')
        return (f'<figure class="diagram{" " + esc(size) if size else ""}"><div class="figure-scroll" tabindex="0" aria-label="{aria}">'
                + self.svg(diagram_id) + f'</div><figcaption>{caption}</figcaption></figure>')

    def figure_md(self, diagram_id):
        d = self.diagrams[diagram_id]
        return f'![{d["alt"]["en"]}｜{d["alt"]["zh"]}]({self.figure_prefix}{d["file"]})\n\n' + md_pair(d['caption'], '  \n')

    def source_links(self, ids):
        return ' · '.join(f'<a href="{esc(self.sources[s]["url"])}" target="_blank" rel="noreferrer">{esc(self.sources[s]["title"])}</a>' for s in ids)

    def source_md(self, ids):
        return ' · '.join(f'[{self.sources[s]["title"]}]({self.sources[s]["url"]})' for s in ids)

    def stress(self, en):
        entry = self.pron.get('terms', {}).get(en)
        return entry[1] if entry else ''


class _Linker(HTMLParser):
    SKIP = ('a', 'svg', 'script', 'style', 'button', 'code')

    def __init__(self, transform):
        super().__init__(convert_charrefs=False)
        self.transform, self.parts, self.skip = transform, [], 0

    def handle_starttag(self, tag, attrs):
        self.parts.append(self.get_starttag_text())
        if tag in self.SKIP: self.skip += 1

    def handle_startendtag(self, tag, attrs): self.parts.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        self.parts.append(f'</{tag}>')
        if tag in self.SKIP: self.skip -= 1

    def handle_data(self, data): self.parts.append(data if self.skip else self.transform(data))
    def handle_entityref(self, name): self.parts.append('&' + name + ';')
    def handle_charref(self, name): self.parts.append('&#' + name + ';')
    def handle_comment(self, data): self.parts.append('<!--' + data + '-->')
    def handle_decl(self, decl): self.parts.append('<!' + decl + '>')
    def handle_pi(self, data): self.parts.append('<?' + data + '>')


# ---------------------------------------------------------------------- placement
RECORD_BLOCKS = {'muscles': ('muscles', 'anatomy'), 'landmarks': ('landmarks', 'anatomy'), 'acupoints': ('acupoints', 'clinical'),
                 'review': ('quiz', 'review'), 'papers': ('paper', 'papers')}


def iter_blocks(blocks):
    for b in blocks:
        yield b
        if b.get('type') == 'details': yield from iter_blocks(b.get('blocks', []))


def block_ids(b):
    return b['ids'] if 'ids' in b else ([b['id']] if 'id' in b else [])


def resolved_sections(content):
    """Each section with the blocks it renders. Records go where a block places them; any record no block
    places is appended to its default section, so a chapter written only with records still shows them all.
    Figures listed in a section's diagramIds but never placed are appended, and the innervation section
    gets the C/T/L/S notation (AN-04) unless it already explains it in a nerve-levels note."""
    sections = content.get('sections', [])
    placed = {kind: set() for kind in RECORD_BLOCKS}
    figures, notation = set(), False
    for section in sections:
        for b in iter_blocks(section.get('blocks', [])):
            t = b.get('type')
            for kind, (block_type, _) in RECORD_BLOCKS.items():
                if t == block_type: placed[kind].update(block_ids(b))
            if t == 'figure': figures.add(b['diagramId'])
            if t == 'nerveNotation' or (t == 'note' and b.get('className') == 'nerve-levels'): notation = True
    out = []
    for section in sections:
        blocks = list(section.get('blocks', []))
        if section.get('id') == 'innervation' and not notation: blocks.insert(0, {'type': 'nerveNotation'})
        for kind, (block_type, home) in RECORD_BLOCKS.items():
            missing = [r['id'] for r in content.get(kind, []) if r.get('id') not in placed[kind]]
            if home != section.get('id') or not missing: continue
            blocks += [{'type': block_type, 'id': i} for i in missing] if block_type == 'paper' else [{'type': block_type, 'ids': missing}]
        blocks += [{'type': 'figure', 'diagramId': d} for d in section.get('diagramIds', []) if d not in figures]
        out.append((section, blocks))
    return out


def strings(value):
    if isinstance(value, str): yield value
    elif isinstance(value, dict):
        for v in value.values(): yield from strings(v)
    elif isinstance(value, list):
        for v in value: yield from strings(v)


def section_text(content, section, blocks):
    """All text a section shows, including the records its blocks render (for the QC-08 coverage check)."""
    records = {'muscles': 'muscles', 'landmarks': 'landmarks', 'acupoints': 'acupoints', 'quiz': 'review', 'paper': 'papers'}
    parts = list(strings([section.get('title'), section.get('overview')]))
    for b in iter_blocks(blocks):
        parts += [x for k, v in b.items() if k not in ('type', 'ids', 'id', 'diagramId', 'className', 'layout', 'size') for x in strings(v)]
        if b.get('type') in records:
            index = {r.get('id'): r for r in content.get(records[b['type']], [])}
            parts += [x for i in block_ids(b) if i in index for x in strings(index[i])]
    return ' '.join(parts)


# ---------------------------------------------------------------------- blocks
def block_html(ch, b):
    t = b.get('type', 'text')
    if t == 'text':  # original standard block: heading + body + optional 3D terms
        out = f'<h3>{pair_spans(b["heading"])}</h3>' + pair_div(b['body'])
        for term in b.get('termIds', []):
            out += f'<p class="model-link-row"><a href="{esc(ch.model_url(term))}" target="_blank" rel="noreferrer">Explore in 3D · 三维查看 ↗</a></p>'
        return out
    if t == 'heading':
        anchor = f' id="{esc(b["id"])}"' if b.get('id') else ''
        return f'<h{b["level"]}{anchor}>{pair_spans(b["text"])}</h{b["level"]}>'
    if t == 'paragraph': return pair_div(b['text'])
    if t == 'figure': return ch.figure_html(b['diagramId'], b.get('size', ''))
    if t == 'table':
        head = ''.join(f'<th scope="col">{cell_html(c)}</th>' for c in b['columns'])
        rows = ''.join('<tr>' + ''.join((f'<th scope="row">{cell_html(c)}</th>' if i == 0 else f'<td>{cell_html(c)}</td>') for i, c in enumerate(r)) + '</tr>' for r in b['rows'])
        cls = f' class="{esc(b["className"])}"' if b.get('className') else ''
        caption = f'<caption>{pair_spans(b["caption"])}</caption>' if b.get('caption') else ''
        return f'<div class="table-scroll" tabindex="0"><table{cls}>{caption}<thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'
    if t == 'note':
        return f'<article class="note-card{" " + esc(b["className"]) if b.get("className") else ""}">' + card_body(b, 'h3') + '</article>'
    if t == 'cards':
        layout = {'columns': 'two-col', 'stages': 'stage-grid bilingual-stages', 'stack': 'attachment-narratives'}[b.get('layout', 'columns')]
        inner = ''.join((('<article>' if b.get('layout') == 'stages' else '<article class="note-card">') + card_body(c, 'h4') + '</article>') for c in b['cards'])
        return f'<div class="{layout}">{inner}</div>'
    if t == 'muscles':
        if b.get('layout') == 'compact':
            return '<div class="attachment-narratives">' + ''.join(muscle_compact(ch, ch.muscles[i]) for i in b['ids']) + '</div>'
        return '<div class="muscle-grid attachment-grid">' + ''.join(muscle_card(ch, ch.muscles[i]) for i in b['ids']) + '</div>'
    if t == 'landmarks':
        rows = ''
        for i in b['ids']:
            lm = ch.landmarks[i]
            url = ch.landmark_url(lm)
            link = f'<a href="{esc(url)}" target="_blank" rel="noreferrer">3D ↗</a>' if url else '—'
            rows += f'<tr><th scope="row">{pair_spans(lm["name"])}</th><td>{pair_spans(lm["description"])}</td><td>{link}</td></tr>'
        return ('<div class="table-scroll" tabindex="0"><table class="landmark-table"><thead><tr><th scope="col">' + pair_spans({'en': 'Landmark', 'zh': '骨性标志'})
                + '</th><th scope="col">' + pair_spans({'en': 'Where it is and why it matters here', 'zh': '位置与本章关联'}) + '</th><th scope="col">' + pair_spans({'en': '3D', 'zh': '三维'})
                + f'</th></tr></thead><tbody>{rows}</tbody></table></div>' + record_sources(ch, [ch.landmarks[i] for i in b['ids']]))
    if t == 'acupoints': return acupoint_table(ch, b['ids']) + record_sources(ch, [ch.acupoints[i] for i in b['ids']])
    if t == 'steps':
        items = ''.join(f'<li><b>{pair_spans(i["heading"])}</b>{pair_div(i["text"])}</li>' for i in b['items'])
        return f'<ol class="palpation">{items}</ol>'
    if t == 'mnemonic':
        return pair_div(b['text']) + f'<p class="mnemonic-original"><b><span lang="en">Chinese mnemonic</span> · <span lang="zh-Hans">中文口诀：</span></b><span lang="zh-Hans">{esc(b["original"])}</span></p>'
    if t == 'quiz': return ''.join(quiz_html(ch.review[i]) for i in b['ids'])
    if t == 'paper': return paper_html(ch, ch.papers[b['id']], b.get('open', True))
    if t == 'details':
        inner = ''.join(block_html(ch, x) for x in b['blocks'])
        return f'<details class="reference"{" open" if b.get("open") else ""}><summary>{pair_spans(b["summary"])}</summary>{inner}</details>'
    if t == 'sources':
        label = f'<span lang="en">{inline(b["label"]["en"])}</span> · <span lang="zh-Hans">{inline(b["label"]["zh"])}</span>：' if b.get('label') else ''
        note = f' <span lang="en">{inline(b["note"]["en"])}</span> <span lang="zh-Hans">{inline(b["note"]["zh"])}</span>' if b.get('note') else ''
        return '<p class="source">' + label + ch.source_links(b['ids']) + note + '</p>'
    if t == 'nerveNotation': return block_html(ch, notation_note(ch))
    raise ValueError('Unknown block type: ' + t)


def unique_sources(records):
    return list(dict.fromkeys(sid for r in records for sid in r.get('sources', [])))


def record_sources(ch, records):
    """One "Sources" line under a table of records (landmarks, acupoints), so every row's evidence is visible."""
    ids = unique_sources(records)
    return f'<p class="source"><span lang="en">Sources</span> · <span lang="zh-Hans">来源</span>：{ch.source_links(ids)}</p>' if ids else ''


def notation_note(ch):
    return {'type': 'note', 'className': 'nerve-levels', 'heading': {'en': 'Spinal levels: C, T, L and S', 'zh': '脊髓节段：C、T、L、S'},
            'paragraphs': list(ch.content.get('nerveNotation', {}).values())}


def card_body(c, heading_tag):
    out = f'<strong>{esc(c["label"])}</strong>' if c.get('label') else ''
    if c.get('heading'): out += f'<{heading_tag}>{pair_spans(c["heading"])}</{heading_tag}>'
    out += ''.join(pair_div(p) for p in c.get('paragraphs', []))
    if c.get('items'): out += '<ul>' + ''.join('<li>' + pair_spans(i) + '</li>' for i in c['items']) + '</ul>'
    if c.get('definitions'):
        out += '<div class="level-key">' + ''.join(f'<div><b>{inline(d["en"])}</b><span class="translation">{inline(d["zh"])}</span></div>' for d in c['definitions']) + '</div>'
    return out


def model_row(ch, record, source_label):
    parts = []
    if record.get('modelTermId'):
        parts.append(f'<a href="{esc(ch.model_url(record["modelTermId"]))}" target="_blank" rel="noreferrer">Explore in 3D · 三维查看 ↗</a>')
    elif record.get('modelUnavailableReason'):
        parts.append(pair_spans(record['modelUnavailableReason']))
    ids = record.get('sources', [])
    if len(ids) == 1:
        parts.append(f'<a href="{esc(ch.sources[ids[0]]["url"])}" target="_blank" rel="noreferrer" title="{esc(ch.sources[ids[0]]["title"])}">{source_label}</a>')
    elif ids:  # several sources: one label, numbered links with the full titles on hover
        parts.append(source_label + ' ' + ' '.join(f'<a href="{esc(ch.sources[sid]["url"])}" target="_blank" rel="noreferrer" title="{esc(ch.sources[sid]["title"])}">[{n}]</a>'
                                                  for n, sid in enumerate(ids, 1)))
    return '<p class="model-link-row">' + ' · '.join(parts) + '</p>'


def muscle_facts(m, fields):
    labels = {'origin': 'Origin · 起点', 'insertion': 'Insertion · 止点', 'innervation': 'Innervation · 神经支配'}
    return '<dl class="attachment-facts">' + ''.join(f'<dt>{labels[k]}</dt><dd>{pair_spans(m[k])}</dd>' for k in fields) + '</dl>'


def muscle_card(ch, m):
    color = f' style="--muscle:{esc(m["color"])}"' if m.get('color') else ''
    letter = m.get('letter') or m['name']['en'][:1]
    stress = ch.stress(m['name']['en'])
    out = (f'<article class="muscle-card attachment-card" id="muscle-{esc(m["id"])}"{color}><div class="muscle-title"><span>{esc(letter)}</span><div>'
           f'<h4 lang="en">{esc(m["name"]["en"])}</h4><small lang="zh-Hans">{esc(m["name"]["zh"])}</small>'
           + (f' <small class="stress" lang="en">{esc(stress)}</small>' if stress else '') + '</div></div>')
    out += ''.join(f'<div class="attachment-diagram">{ch.svg(d)}</div>' for d in m['diagramIds'][:1])
    out += muscle_facts(m, ['origin', 'insertion', 'innervation']) + pair_div(m['course']) + pair_div(m['actions'])
    return out + model_row(ch, m, 'Anatomy source · 解剖依据') + '</article>'


def muscle_compact(ch, m):
    out = f'<article class="note-card" id="muscle-{esc(m["id"])}"><h4>{pair_spans(m["name"])}</h4>'
    out += muscle_facts(m, ['origin', 'insertion', 'innervation']) + pair_div(m['course']) + pair_div(m['actions'])
    return out + model_row(ch, m, 'Anatomy source · 解剖依据') + '</article>'


ACU_COLUMNS = [('location', {'en': 'Location', 'zh': '定位'}), ('howToFind', {'en': 'How to find', 'zh': '怎么找'}), ('layers', {'en': 'Layers: superficial → deep', 'zh': '层次：浅 → 深'}),
               ('target', {'en': 'Related muscle or trigger point', 'zh': '相关肌肉或触发点'}), ('safety', {'en': 'Safety', 'zh': '安全提示'})]


def acupoint_table(ch, ids):
    points = [ch.acupoints[i] for i in ids]
    columns = [(k, label) for k, label in ACU_COLUMNS if any(p.get(k) for p in points)]
    head = f'<th scope="col">{pair_spans({"en": "Acupoint", "zh": "穴位"})}</th>' + ''.join(f'<th scope="col">{pair_spans(label)}</th>' for _, label in columns)
    rows = ''
    for p in points:
        pinyin = ch.pron.get('pinyin', {}).get(p['name']['en'], '')
        name = f'{esc(p["name"]["en"])} <span lang="zh-Hans">{esc(p["name"]["zh"])}</span> <span class="acu-code">{esc(p["code"])}</span>'
        if p.get('modelPointId'):
            name = f'<a href="{esc(ch.model_url(point=p["modelPointId"]))}" target="_blank" rel="noreferrer" title="Explore {esc(p["name"]["en"])} in 3D · 在三维模型中查看">{name}</a>'
        name += f'<small class="pinyin" lang="zh-Latn">{esc(pinyin)}</small>' if pinyin else ''
        rows += f'<tr><th scope="row">{name}</th>' + ''.join(f'<td>{pair_spans(p[k]) if p.get(k) else "—"}</td>' for k, _ in columns) + '</tr>'
    return f'<div class="table-scroll" tabindex="0"><table class="acu-table"><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'


def quiz_html(q):
    out = (f'<details class="quiz"><summary><span class="question-pair">{pair_spans(q["question"])}</span>'
           '<span class="quiz-toggle">Answer · 答案</span></summary>' + pair_div(q['answer']))
    if q.get('mnemonic'): out += '<p class="mnemonic">' + pair_spans(q['mnemonic']) + '</p>'
    return out + '</details>'


PAPER_LABELS = [('question', {'en': 'Research question', 'zh': '研究问题'}), ('design', {'en': 'Study design', 'zh': '研究设计'}),
                ('population', {'en': 'Population', 'zh': '研究人群'}), ('methods', {'en': 'Methods', 'zh': '方法'}),
                ('results', {'en': 'Results', 'zh': '结果'}), ('limitations', {'en': 'Limitations', 'zh': '局限'}),
                ('applicability', {'en': 'Applicability', 'zh': '适用范围'})]


def paper_html(ch, p, open_summary=True):
    title = p.get('title') or {'en': p['citation'], 'zh': ''}
    doi = f'<br>DOI: {esc(p["doi"])}' if p.get('doi') else ''
    link = f'https://doi.org/{p["doi"]}' if p.get('doi') else None
    head = f'<a href="{esc(link)}" target="_blank" rel="noreferrer">{esc(title["en"])}</a>' if link else esc(title['en'])
    out = (f'<div class="paper-meta"><span>Research article · 研究论文</span><div><p><b>{head}</b></p>'
           + (f'<p lang="zh-Hans" class="translation">{esc(title["zh"])}</p>' if title.get('zh') else '')
           + f'<p>{esc(p.get("byline", p["citation"]))}{doi}</p></div></div>')
    rows = ''.join(f'<tr><th scope="row">{pair_spans(label)}</th><td>{pair_spans(p[k])}</td></tr>' for k, label in PAPER_LABELS if p.get(k))
    out += (f'<details class="reference paper-summary"{" open" if open_summary else ""}><summary>' + pair_spans({'en': 'Appraisal at a glance', 'zh': '评价一览'}) + '</summary>'
            f'<div class="table-scroll" tabindex="0"><table><tbody>{rows}</tbody></table></div>')
    if p.get('terms'):
        out += '<dl class="method-terms">' + ''.join(f'<dt>{pair_spans(t["term"])}</dt><dd>{pair_spans(t["explanation"])}</dd>' for t in p['terms']) + '</dl>'
    return out + '</details>'


def block_md(ch, b):
    t = b.get('type', 'text')
    if t == 'text':
        out = f'### {b["heading"]["en"]}｜{b["heading"]["zh"]}\n\n' + md_pair(b['body'])
        return out + ''.join(f'\n\n[Explore in 3D · 三维查看]({ch.model_url(term)})' for term in b.get('termIds', []))
    if t == 'heading': return '#' * b['level'] + ' ' + b['text']['en'] + ('｜' + b['text']['zh'] if b['text'].get('zh') else '')
    if t == 'paragraph': return md_pair(b['text'])
    if t == 'figure': return ch.figure_md(b['diagramId'])
    if t == 'table':
        cols = b['columns']
        out = '| ' + ' | '.join(cell_md(c) for c in cols) + ' |\n|' + ' --- |' * len(cols) + '\n'
        return out + ''.join('| ' + ' | '.join(cell_md(c) for c in r) + ' |\n' for r in b['rows']).rstrip('\n')
    if t == 'note': return card_md(b, '###')
    if t == 'cards': return '\n\n'.join(card_md(c, '####') for c in b['cards'])
    if t == 'muscles': return '\n\n'.join(muscle_md(ch, ch.muscles[i]) for i in b['ids'])
    if t == 'landmarks':
        out = '| Landmark｜骨性标志 | Where it is and why it matters here｜位置与本章关联 |\n| --- | --- |\n'
        out += ''.join(f'| {cell_md(ch.landmarks[i]["name"])} | {cell_md(ch.landmarks[i]["description"])} |\n' for i in b['ids'])
        ids = unique_sources([ch.landmarks[i] for i in b['ids']])
        return out + ('\nSources · 来源: ' + ch.source_md(ids) if ids else '').rstrip('\n')
    if t == 'acupoints':
        points = [ch.acupoints[i] for i in b['ids']]
        columns = [(k, label) for k, label in ACU_COLUMNS if any(p.get(k) for p in points)]
        out = '| Acupoint｜穴位 | ' + ' | '.join(f'{label["en"]}｜{label["zh"]}' for _, label in columns) + ' |\n|' + ' --- |' * (len(columns) + 1) + '\n'
        for p in points:
            pinyin = ch.pron.get('pinyin', {}).get(p['name']['en'], '')
            out += f'| {p["name"]["en"]} {p["name"]["zh"]} {p["code"]}' + (f' ({pinyin})' if pinyin else '') + ' | ' + ' | '.join(cell_md(p[k]) if p.get(k) else '—' for k, _ in columns) + ' |\n'
        ids = unique_sources(points)
        return (out + ('\nSources · 来源: ' + ch.source_md(ids) if ids else '')).rstrip('\n')
    if t == 'steps':
        return '\n'.join(f'{n}. **{i["heading"]["en"]}｜{i["heading"]["zh"]}**  \n   {i["text"]["en"]}  \n   {i["text"]["zh"]}' for n, i in enumerate(b['items'], 1))
    if t == 'mnemonic': return md_pair(b['text']) + '\n\n**Chinese mnemonic · 中文口诀：** ' + b['original']
    if t == 'quiz':
        return '\n\n'.join(f'**Q. {q["question"]["en"]}**  \n{q["question"]["zh"]}\n\n<details><summary>Answer · 答案</summary>\n\n{md_pair(q["answer"])}'
                           + (f'\n\n{md_inline_pair(q["mnemonic"])}' if q.get('mnemonic') else '') + '\n\n</details>'
                           for q in (ch.review[i] for i in b['ids']))
    if t == 'paper':
        p = ch.papers[b['id']]
        title = p.get('title') or {'en': p['citation'], 'zh': ''}
        out = f'> **Research article · 研究论文**  \n> **{title["en"]}**' + (f'  \n> {title["zh"]}' if title.get('zh') else '') + f'  \n> {p.get("byline", p["citation"])}' + (f'  \n> DOI: {p["doi"]}' if p.get('doi') else '')
        out += '\n\n#### Appraisal at a glance｜评价一览\n\n| | |\n| --- | --- |\n' + ''.join(f'| {label["en"]}｜{label["zh"]} | {cell_md(p[k])} |\n' for k, label in PAPER_LABELS if p.get(k))
        if p.get('terms'): out += '\n' + '\n'.join(f'- **{t["term"]["en"]}｜{t["term"]["zh"]}:** {t["explanation"]["en"]}  \n  {t["explanation"]["zh"]}' for t in p['terms'])
        return out.rstrip('\n')
    if t == 'details': return f'#### {b["summary"]["en"]}｜{b["summary"]["zh"]}\n\n' + '\n\n'.join(block_md(ch, x) for x in b['blocks'])
    if t == 'sources':
        label = f'{b["label"]["en"]} · {b["label"]["zh"]}: ' if b.get('label') else 'Source · 来源: '
        return label + ch.source_md(b['ids']) + (f' {b["note"]["en"]} {b["note"]["zh"]}' if b.get('note') else '')
    if t == 'nerveNotation': return block_md(ch, notation_note(ch))
    raise ValueError('Unknown block type: ' + t)


def card_md(c, hashes):
    out = []
    if c.get('heading'): out.append(f'{hashes} ' + (c['label'] + ' ' if c.get('label') else '') + c['heading']['en'] + '｜' + c['heading']['zh'])
    out += [md_pair(p) for p in c.get('paragraphs', [])]
    if c.get('items'): out.append('\n'.join(f'- {i["en"]}  \n  {i["zh"]}' for i in c['items']))
    if c.get('definitions'): out.append('\n'.join(f'- **{d["en"]}**｜{d["zh"]}' for d in c['definitions']))
    return '\n\n'.join(out)


def muscle_md(ch, m):
    stress = ch.stress(m['name']['en'])
    out = [f'### {m["name"]["en"]}｜{m["name"]["zh"]}' + (f' `{stress}`' if stress else '')]
    out += [ch.figure_md(d).split('\n\n')[0] for d in m['diagramIds'][:1]]
    for key, label in [('origin', 'Origin（起点）'), ('insertion', 'Insertion（止点）'), ('innervation', 'Innervation（神经支配）')]:
        out.append(f'**{label}:** {m[key]["en"]}  \n{m[key]["zh"]}')
    out += [md_pair(m['course']), md_pair(m['actions'])]
    links = [f'[Explore in 3D · 三维查看]({ch.model_url(m["modelTermId"])})'] if m.get('modelTermId') else ([md_inline_pair(m['modelUnavailableReason'])] if m.get('modelUnavailableReason') else [])
    links += ['Anatomy source · 解剖依据: ' + ch.source_md(m['sources'])] if m.get('sources') else []
    out.append(' · '.join(links))
    return '\n\n'.join(out)


# ---------------------------------------------------------------------- pronunciation appendix (AN-07)
def pronunciation_rows(ch):
    names = {}
    for item in ch.manifest.get('structures') or []: names[item['name']['en']] = item['name']['zh']
    names.update(ch.pron.get('names', {}))
    terms = sorted(ch.pron.get('terms', {}).items(), key=lambda kv: kv[0].lower())
    return names, terms


def audio_for(ch, text):
    clip = ch.audio.get(text.lower())
    return ch.audio_base + clip if clip else None


def say_button(ch, text, lang):
    src = audio_for(ch, text)
    data = f' data-audio="{esc(src)}"' if src else ''
    return f'<button type="button" class="say" data-say="{esc(text)}" data-lang="{lang}"{data} aria-label="Pronounce {esc(text)} · 朗读">▶</button>'


PINYIN_UNVERIFIED = {'en': 'Not confirmed in an acupoint standard', 'zh': '未在穴位标准中核实'}


def pronunciation_html(ch):
    names, terms = pronunciation_rows(ch)
    if not terms and not ch.pron.get('pinyin'): return ''
    rows = ''
    for term, (ipa, stress, url) in terms:
        stress_html = re.sub(r'\b([A-Z]{2,})\b', lambda m: f'<b>{m.group(1)}</b>', esc(stress))
        rows += (f'<tr><th scope="row">{say_button(ch, term, "en-US")} <span lang="en">{esc(term)}</span>'
                 + (f'<span class="translation" lang="zh-Hans">{esc(names[term])}</span>' if names.get(term) else '')
                 + f'</th><td class="stress" lang="en">{stress_html}</td><td class="ipa">{esc(ipa)}</td>'
                 f'<td><a href="{esc(url)}" target="_blank" rel="noreferrer">Dictionary · 词典</a>'
                 + ('<br><small><span lang="en">Not confirmed in a dictionary</span> · <span lang="zh-Hans">未在词典中核实</span></small>' if term in ch.pron.get('unverified', []) else '')
                 + '</td></tr>')
    acu = {p['name']['en']: p for p in ch.content.get('acupoints', [])}
    pinyin_rows = ''
    for name, value in ch.pron.get('pinyin', {}).items():
        zh = acu[name]['name']['zh'] if name in acu else ch.pron.get('names', {}).get(name, '')
        code = f' <span class="acu-code">{esc(acu[name]["code"])}</span>' if name in acu else ''
        pinyin_rows += (f'<tr><th scope="row">{say_button(ch, zh or name, "zh-CN")} <span lang="en">{esc(name)}</span>{code}'
                        + (f'<span class="translation" lang="zh-Hans">{esc(zh)}</span>' if zh else '') + f'</th><td class="pinyin" lang="zh-Latn">{esc(value)}'
                        + (f'<br><small>{pair_spans(PINYIN_UNVERIFIED)}</small>' if name in ch.pron.get('unverified', []) else '') + '</td></tr>')
    out = (f'<section id="pronunciation" class="chapter pronunciation" aria-labelledby="pronunciation-heading"><header class="chapter-head"><span class="chapter-number">Aa</span><div>'
           f'<h2 id="pronunciation-heading">{pair_spans(PRON_HEADING)}</h2></div></header>'
           + pair_div({'en': 'Capital letters mark the stressed syllable. Press ▶ to hear the term; recorded clips play where the 3D site has one, otherwise the browser reads the term aloud.',
                       'zh': '大写字母是重读音节。点 ▶ 听发音：3D 网站已有录音的词播放录音，其余由浏览器朗读。'}))
    if rows:
        out += ('<div class="table-scroll" tabindex="0"><table class="pron-table"><thead><tr>'
                + ''.join(f'<th scope="col">{pair_spans(h)}</th>' for h in [{'en': 'Term', 'zh': '术语'}, {'en': 'Stress', 'zh': '重音'}, {'en': 'IPA', 'zh': '国际音标'}, {'en': 'Source', 'zh': '来源'}])
                + f'</tr></thead><tbody>{rows}</tbody></table></div>')
    if pinyin_rows:
        out += (f'<h3>{pair_spans({"en": "Acupoint names (Mandarin, tone-marked pinyin)", "zh": "穴位名称（普通话，带声调拼音）"})}</h3>'
                '<div class="table-scroll" tabindex="0"><table class="pron-table"><thead><tr>'
                + ''.join(f'<th scope="col">{pair_spans(h)}</th>' for h in [{'en': 'Acupoint', 'zh': '穴位'}, {'en': 'Pinyin', 'zh': '拼音'}])
                + f'</tr></thead><tbody>{pinyin_rows}</tbody></table></div>')
    return out + '</section>'


def pronunciation_md(ch):
    names, terms = pronunciation_rows(ch)
    if not terms and not ch.pron.get('pinyin'): return ''
    out = f'## {PRON_HEADING["en"]}｜{PRON_HEADING["zh"]}\n\nCapital letters mark the stressed syllable.\n\n大写字母是重读音节。\n\n| Term｜术语 | Stress｜重音 | IPA｜国际音标 | Source｜来源 |\n| --- | --- | --- | --- |\n'
    out += ''.join(f'| {term}' + (f'<br>{names[term]}' if names.get(term) else '') + f' | `{stress}` | {ipa} | [Dictionary · 词典]({url})'
                   + (' (not confirmed in a dictionary · 未在词典中核实)' if term in ch.pron.get('unverified', []) else '') + ' |\n' for term, (ipa, stress, url) in terms)
    if ch.pron.get('pinyin'):
        acu = {p['name']['en']: p for p in ch.content.get('acupoints', [])}
        out += '\n### Acupoint names (Mandarin, tone-marked pinyin)｜穴位名称（普通话，带声调拼音）\n\n| Acupoint｜穴位 | Pinyin｜拼音 |\n| --- | --- |\n'
        out += ''.join(f'| {name}' + (f' {acu[name]["code"]}<br>{acu[name]["name"]["zh"]}' if name in acu else '') + f' | {value}' + (f' ({PINYIN_UNVERIFIED["en"].lower()} · {PINYIN_UNVERIFIED["zh"]})' if name in ch.pron.get('unverified', []) else '') + ' |\n' for name, value in ch.pron['pinyin'].items())
    return out


# ---------------------------------------------------------------------- page
SCRIPT = ('<script>const chapters=[...document.querySelectorAll(".chapter")];const links=[...document.querySelectorAll(".toc a")];let queued=false;'
          'function update(){const offset=innerWidth<=820?110:130;let current=chapters[0];for(const chapter of chapters){if(chapter.getBoundingClientRect().top<=offset)current=chapter;}'
          'for(const link of links){if(link.hash==="#"+current.id)link.setAttribute("aria-current","location");else link.removeAttribute("aria-current");}queued=false;}'
          'addEventListener("scroll",()=>{if(!queued){queued=true;requestAnimationFrame(update);}},{passive:true});addEventListener("resize",update);update();'
          'const closed=[];addEventListener("beforeprint",()=>{for(const el of document.querySelectorAll("details:not([open])")){closed.push(el);el.open=true;}});'
          'addEventListener("afterprint",()=>{for(const el of closed)el.open=false;closed.length=0;});'
          'document.addEventListener("click",e=>{const b=e.target.closest(".say");if(!b)return;if(b.dataset.audio){new Audio(b.dataset.audio).play();return;}'
          'if(!("speechSynthesis" in window))return;const u=new SpeechSynthesisUtterance(b.dataset.say);u.lang=b.dataset.lang||"en-US";u.rate=.85;speechSynthesis.cancel();speechSynthesis.speak(u);});</script>')


def section_anchor(section):
    return section.get('anchor') or section['id']


def render_page(ch):
    """Return (html, markdown) for the whole chapter."""
    manifest, content = ch.manifest, ch.content
    page = content.get('page', {})
    resolved = resolved_sections(content)
    sections = [s for s, _ in resolved]
    title = manifest['title']
    chapters_html, chapters_md = [], []
    for index, (section, blocks) in enumerate(resolved, 1):
        anchor = section_anchor(section)
        body = ''.join(block_html(ch, b) for b in blocks)
        intro = pair_div(section['overview']) if section.get('overview', {}).get('en') else ''
        nxt = sections[index] if index < len(sections) else None
        if nxt:
            label = nxt.get('navTitle') or nxt['title']
            end = f'<div class="bridge"><a href="#{esc(section_anchor(nxt))}"><span lang="en">{esc(label["en"])}</span> · <span lang="zh-Hans">{esc(label["zh"])}</span> →</a></div>'
        else:
            first = sections[0].get('navTitle') or sections[0]['title']
            end = f'<div class="end-note"><a href="#{esc(section_anchor(sections[0]))}"><span lang="en">{esc(first["en"])}</span> · <span lang="zh-Hans">{esc(first["zh"])}</span> ↑</a></div>'
        chapters_html.append(f'<section id="{esc(anchor)}" class="chapter" aria-labelledby="{esc(anchor)}-heading"><header class="chapter-head"><span class="chapter-number">{index:02d}</span><div>'
                             f'<h2 id="{esc(anchor)}-heading">{pair_spans(section["title"])}</h2></div></header>{intro}{body}{end}</section>')
        md = [f'## {index:02d} {section["title"]["en"]}｜{section["title"]["zh"]}']
        if intro: md.append(md_pair(section['overview']))
        md += [block_md(ch, b) for b in blocks]
        chapters_md.append('\n\n'.join(x for x in md if x))
    pron_html, pron_md = pronunciation_html(ch), pronunciation_md(ch)
    nav = [(section_anchor(s), s.get('navTitle') or s['title'], f'{i:02d}') for i, s in enumerate(sections, 1)]
    if pron_html: nav.append(('pronunciation', PRON_HEADING, 'Aa'))
    toc = ''.join(f'<a href="#{esc(a)}"><span>{n}</span><b class="toc-title">{esc(t["en"])}<small>{esc(t["zh"])}</small></b></a>' for a, t, n in nav)
    css = (PLATFORM / 'reading.css').read_text(encoding='utf-8')
    subtitle = page.get('subtitle', {})
    eyebrow = page.get('eyebrow', {})
    header = ('<header class="page-header">'
              + (f'<div class="eyebrow"><span>{esc(eyebrow.get("en", ""))}</span><span>{esc(eyebrow.get("zh", ""))}</span></div>' if eyebrow else '')
              + f'<h1>{esc(title["en"])}<span lang="zh-Hans">{esc(title["zh"])}</span></h1>'
              + (f'<p class="subtitle">{pair_spans(subtitle)}</p>' if subtitle else '')
              + (f'<p class="orientation-line">{pair_spans(page["lead"])}</p>' if page.get('lead') else '') + '</header>')
    footer = f'<footer class="page-footer">{pair_spans(page["footer"])}</footer>' if page.get('footer') else ''
    sidebar_note = f'<p class="sidebar-note">{pair_spans(page["sidebarNote"])}</p>' if page.get('sidebarNote') else ''
    description = esc(plain(page.get('description', manifest['summary'])['en']) + ' ' + plain(page.get('description', manifest['summary'])['zh']))
    first = section_anchor(sections[0])
    body = ''.join(chapters_html) + pron_html
    document = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                f'<title>{esc(title["en"])} · {esc(title["zh"])}</title><meta name="description" content="{description}"><style>\n{css}\n</style></head><body>'
                f'<a class="skip" href="#{esc(first)}">Skip to the chapters · 跳到正文</a><div class="layout"><aside class="sidebar"><a class="home-link" href="{esc(ch.model_base)}study.html">← Study home · 学习首页</a><div class="brand">{esc(title["en"])}<small>{esc(title["zh"])}</small></div>'
                f'<div class="nav-label">Reading order · 阅读顺序</div><nav class="toc" aria-label="Chapters · 章节目录">{toc}</nav>{sidebar_note}</aside>'
                f'<main class="main">{header}{ch.link_text(body)}{footer}</main></div>{SCRIPT}</body></html>\n')
    md_head = f'# {title["en"]}｜{title["zh"]}'
    if subtitle: md_head += f'\n\n{md_inline_pair(subtitle)}'
    if page.get('lead'): md_head += f'\n\n{md_inline_pair(page["lead"])}'
    md_body = '\n\n'.join(chapters_md + ([pron_md.rstrip()] if pron_md else []))
    md_footer = f'\n\n---\n\n{md_inline_pair(page["footer"])}' if page.get('footer') else ''
    markdown = md_head + '\n\n' + ch.link_md(md_body) + md_footer + '\n'
    ids = re.findall(r'\bid="([^"]+)"', document)
    duplicates = sorted({x for x in ids if ids.count(x) > 1})
    if duplicates: raise ValueError('Duplicate HTML ids (SVG filters/markers must be prefixed per figure, AN-10): ' + ', '.join(duplicates[:8]))
    return document, markdown


def load_audio(manifest_path):
    """Map a clip's spoken text (lower case) to its file, from the 3D site's audio manifest."""
    path = Path(manifest_path)
    if not path.is_file(): return {}
    clips = json.loads(path.read_text(encoding='utf-8')).get('clips', {})
    return {c['text'].lower(): c['file'] for c in clips.values() if c.get('text') and c.get('file')}
