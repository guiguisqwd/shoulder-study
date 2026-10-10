# -*- coding: utf-8 -*-
"""Assemble a day's pack: sections + figures + shell → <OUT>.html and <OUT>.md (in days/<date>/build/)."""
import html, json, re, xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from .paths import TEMPLATES, DATA, APP_SRC, LOCAL_3D, build_dir, out_name
from .render import render_sections, chapter_url
from . import plan

BASE = LOCAL_3D


def _terms():
    models = json.loads((DATA / "model-links.json").read_text(encoding="utf-8"))
    landmarks = models.pop("_landmarks")
    terms = {v["english"].lower(): v["term"] for v in models.values()}
    terms.update(landmarks)
    return terms


def _valid_3d_terms():
    """IDs that really exist in the 3D app (vocabulary + bone landmarks)."""
    valid = set()
    voc = APP_SRC / "vocabulary.ts"
    if voc.exists():
        valid.update(re.findall(r"id: '([a-z-]+)'", voc.read_text(encoding="utf-8")))
    for fn in ["humerus-landmarks.json", "scapula-landmarks.json"]:
        p = APP_SRC / fn
        if p.exists():
            valid.update(item["id"] for item in json.loads(p.read_text(encoding="utf-8")))
    return valid


class _Linker(HTMLParser):
    def __init__(self, sub):
        super().__init__(convert_charrefs=False); self.parts = []; self.skip = 0; self.sub = sub
    def handle_starttag(self, tag, attrs):
        self.parts.append(self.get_starttag_text())
        if tag in ("a", "svg", "script", "style", "button"): self.skip += 1
    def handle_startendtag(self, tag, attrs): self.parts.append(self.get_starttag_text())
    def handle_endtag(self, tag):
        self.parts.append(f"</{tag}>")
        if tag in ("a", "svg", "script", "style", "button"): self.skip -= 1
    def handle_data(self, data): self.parts.append(data if self.skip else self.sub(data))
    def handle_entityref(self, name): self.parts.append("&" + name + ";")
    def handle_charref(self, name): self.parts.append("&#" + name + ";")
    def handle_comment(self, data): self.parts.append("<!--" + data + "-->")


def weekly(c):
    return c.get("schema") == "dpt-daily-pack/2"


def header_html(c):
    date, day = c["date"], c.get("day")
    left = f"DPT 基础 · {date} {plan.weekday_zh(date)}"
    right = (f"第 {day} 天 / 60 · " if c.get("kind") == "learning" else "") + f"距 12 月 23 日还有 {plan.days_left(date)} 天"
    if weekly(c):  # DL-04: every pack names and links the week's library chapter
        right = (f'第 {c["week"]} 周 · 本周章节 <a href="{chapter_url(c["chapter"])}" target="_blank" rel="noreferrer">{html.escape(c.get("chapter_name", c["chapter"]))}</a>'
                 f' · 距 12 月 23 日还有 {plan.days_left(date)} 天')
    default_plan = ([[ch["toc"][1], ch["title"][1]] for ch in c["chapters"]] if weekly(c) else None)
    sp = c.get("study_plan") or default_plan or [["先看图（10 分钟）", "01 肌肉、04 穴位的图，对着自己身体找"], ["再读文字（20 分钟）", "01–04 章，每章末尾先自测"],
                                 ["复习（15 分钟）", "05 章记忆卡 + 复习中心里的旧卡"], ["英文（5 分钟）", "06 章读两遍，用新词造一句"]]
    plan_html = "".join(f"<div><b>{b}</b><span>{s}</span></div>" for b, s in sp)
    return (f'<header class="page-header"><div class="eyebrow"><span>{left}</span><span>{right}</span></div>'
            f'<h1>{c["title"]["zh"]}<span>{c["title"]["en"]}</span></h1><p>{c["today_line"]}</p><div class="study-plan">{plan_html}</div></header>')


def toc_html(c):
    items = "".join(f'<a href="#{ch["id"]}"><span>{ch["num"]:02d}</span><b class="toc-title">{ch["toc"][0]}<small>{ch["toc"][1]}</small></b></a>' for ch in c["chapters"])
    return f'<nav class="toc" aria-label="章节目录">{items}</nav>'


def build(date):
    from .paths import load_content
    c = load_content(date)
    B = build_dir(date)
    assets_dir = B / "资源"
    figs = {p.name[:2]: p.name for p in sorted(assets_dir.glob("*.svg"))}
    due = None
    if any(b.get("t") == "due_cards" for ch in c["chapters"] for b in ch.get("blocks", [])):
        from . import cards
        due = cards.due(date)
    secs = render_sections(c, figs, B / "sections", due)
    terms = _terms()
    pattern = re.compile(r"(?<![A-Za-z])(?:" + "|".join(re.escape(k) for k in sorted(terms, key=len, reverse=True)) + r")(?![A-Za-z])", re.I)

    def term_link(m, markdown=False):
        label = m.group(); term = terms[label.lower()]
        if term is None: return label
        url = BASE + "?term=" + term
        if markdown: return f"[{label}]({url})"
        return f'<a class="anatomy-link" href="{url}" target="_blank" rel="noreferrer" title="Explore {label} in 3D · 在三维模型中查看">{label}</a>'

    def linked_html(s):
        p = _Linker(lambda d: pattern.sub(term_link, d)); p.feed(s); p.close(); assert p.skip == 0; return "".join(p.parts)

    def linked_md(s):
        parts = re.split(r"(!?\[[^\]]*\]\([^)]*\)|<[^>]+>|`[^`]*`)", s)
        return "".join(p if i % 2 else pattern.sub(lambda m: term_link(m, True), p) for i, p in enumerate(parts))

    figure_ids = []

    def link_svg_label(m):
        raw = m.group(0); plain = html.unescape(re.sub(r"<[^>]+>", "", raw)).strip()
        for name, term in sorted(terms.items(), key=lambda it: len(it[0]), reverse=True):
            if plain.lower().startswith(name) and (len(plain) == len(name) or not plain[len(name)].isascii() or not plain[len(name)].isalpha()):
                if term: return f'<a href="{BASE}?term={term}" target="_blank" aria-label="Explore {name} in 3D">{raw}</a>'
                break
        return raw

    def embed(m):
        n = m.group(1); s = (assets_dir / figs[n]).read_text(encoding="utf-8"); ET.fromstring(s)
        figure_ids.append(n)
        s = re.sub(r"<text\b[^>]*>.*?</text>", link_svg_label, s, flags=re.S)
        s = re.sub(r"<\?xml[^>]*\?>", "", s)
        return re.sub(r"<svg\b", f'<svg data-figure="{n}"', s, count=1)

    chapters, md_chapters = [], []
    for num, cid in secs:
        raw = (B / "sections" / f"{num:02d}-{cid}.html").read_text(encoding="utf-8").replace('href="./?point=', f'href="{BASE}?point=')
        chapters.append(re.sub(r"\{\{FIGURE:(\d\d)\}\}", embed, linked_html(raw)))
        md_chapters.append(linked_md((B / "sections" / f"{num:02d}-{cid}.md").read_text(encoding="utf-8")))
    shell = (TEMPLATES / "reading-shell.html").read_text(encoding="utf-8")
    css = (TEMPLATES / "reading.css").read_text(encoding="utf-8")
    first = c["chapters"][0]
    brand = c.get("brand") or (f"第 {c['week']} 周 · {plan.weekday_zh(date)}" if weekly(c) else f"第 {c.get('day')} 天")
    rep = {"{{PAGE_TITLE}}": c.get("page_title") or (f"第 {c['day']} 天｜{c['title']['zh']}" if c.get("kind") == "learning"
                                                     else f"第 {c['week']} 周 {plan.weekday_zh(date)}｜{c['title']['zh']}" if weekly(c) else c["title"]["zh"]),
           "{{DESCRIPTION}}": html.escape(c.get("description", ""), quote=True),
           "{{SKIP}}": f'<a class="skip" href="#{first["id"]}">跳到{first.get("skip_label", first["toc"][1])}</a>',
           "{{BRAND}}": f'<div class="brand">{brand}<small>{c.get("brand_sub") or c["title"]["zh"]}</small></div>',
           "{{TOC}}": toc_html(c), "{{NCH}}": str(len(c["chapters"])), "{{HEADER}}": header_html(c),
           "{{FOOTER}}": c.get("footer") or f"DPT 基础 · {c['date']} · 定位依据 GB/T 12346；层次为学习用的简化描述，不代表进针方向或深度。",
           "{{KEY}}": f"dpt-day-{c['date']}:",
           "{{SIDEBAR_NOTE}}": "学法：周日学一章，周一到周六补全这一章（新内容 + 旧的夯实）。" if weekly(c) else "进度目标：12 月 23 日前背完十四经穴 362 个和常用肌肉 157 块。"}
    page = shell
    for k, v in rep.items():
        page = page.replace(k, v)
    page = page.replace("{{CHAPTERS}}", "\n".join(chapters)).replace("</style>", css + "\n</style>", 1)
    assert "{{" not in page, re.findall(r"\{\{[A-Z_:0-9]+\}\}", page)
    ids = re.findall(r'\bid="([^"]+)"', page)
    dup = sorted({x for x in ids if ids.count(x) > 1}); assert not dup, dup
    for _, cid in secs: assert f'id="{cid}"' in page, cid
    valid = _valid_3d_terms()
    bad = sorted(t for t in set(re.findall(r"\?term=([a-z-]+)", page)) if valid and t not in valid)
    assert not bad, f"3D links to unknown terms: {bad}"
    stem = out_name(c)
    (B / f"{stem}.html").write_text(page, encoding="utf-8")
    prefix = c.get("md_prefix") or f"# {rep['{{PAGE_TITLE}}']}\n\nDPT 基础 · {c['date']} · {c['title']['en']}\n"
    md = prefix + "\n\n" + "\n\n".join(md_chapters) + "\n\n---\n\n" + rep["{{FOOTER}}"] + "\n"
    for path in re.findall(r"!\[[^]]*\]\(([^)]+)\)", md):
        assert (B / path).exists(), path
    (B / f"{stem}.md").write_text(md, encoding="utf-8")
    report = {"date": date, "out": stem, "chapters": len(secs), "figure_occurrences": len(figure_ids), "figures": figure_ids,
              "model_links": sorted(set(re.findall(r"\?term=([a-z-]+)", page))), "html_bytes": len(page.encode())}
    (B / "build-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report
