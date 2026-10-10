# -*- coding: utf-8 -*-
"""content.json → six chapter sections (HTML + Markdown).

One generic renderer for every learning day. A day's content lives only in data
(content.json) plus its figures.py; nothing day-specific is hard-coded here.
Block types are documented in daily/CONTENT_SCHEMA.md.
"""
import html, json, re
from pathlib import Path
from .paths import DATA, PAPERS, SITE_BASE, LIBRARY

E = lambda s: html.escape(s, quote=False)
EA = lambda s: html.escape(s, quote=True)
ASSET_DIR = "资源"
MEASURE_LABELS = [("Origin · 起点", "o"), ("Insertion · 止点", "i"), ("Nerve · 神经", "n"), ("Action · 动作", "a")]
MEASURE_LABELS_MD = [("Origin 起点", "o"), ("Insertion 止点", "i"), ("Nerve 神经", "n"), ("Action 动作", "a")]


def load_pron(extra=None, chapter=None):
    """Daily pronunciation table, plus the week's library chapter table (weekly plan) and the pack's own extras."""
    p = json.loads((DATA / "pronunciation.json").read_text(encoding="utf-8"))["terms"]
    lib = LIBRARY / str(chapter) / "pronunciation.json"
    if chapter and lib.exists():
        p = {**json.loads(lib.read_text(encoding="utf-8")).get("terms", {}), **p}
    if extra:
        p = {**p, **extra}
    return p


def strip(x):
    x = re.sub(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', r'[\2](\1)', x)
    return re.sub(r"<[^>]+>", "", x).replace("&amp;", "&").replace("&nbsp;", " ")


def link(url, text):
    return f'<a href="{url}" target="_blank" rel="noreferrer">{text}</a>'


def say_btn(text, lang="en-US"):
    return f'<button type="button" class="say" data-say="{EA(text)}" data-lang="{lang}" aria-label="朗读 {EA(text)}"></button>'


def chapter_url(cid):
    """Public page of a library chapter (shoulder keeps its original address)."""
    return SITE_BASE + ("reading.html" if cid == "shoulder" else f"topics/{cid}/index.html")


def _bi(en, zh, tag="p"):
    return f'<div class="bilingual-pair"><{tag} lang="en">{en}</{tag}><{tag} class="translation" lang="zh-Hans">{zh}</{tag}></div>'


class WeeklyBlocks:
    """Blocks for the weekly plan's forms (standards/daily/README.md F-x); see CONTENT_SCHEMA.md."""

    def b_chapter_link(self, b):
        cid, name = self.c["chapter"], self.c.get("chapter_name", self.c["chapter"])
        url = chapter_url(cid)
        return (f'<p class="model-link-row chapter-link">{link(url, "Open this week&#39;s chapter · 打开本周章节：" + E(name))}</p>',
                f"[Open this week's chapter · 打开本周章节：{name}]({url})\n")

    def b_flow(self, b):
        steps = "".join(f'<li><b lang="en">{st["title"][0]}</b> <b lang="zh-Hans">{st["title"][1]}</b>{_bi(*st["text"])}</li>' for st in b["steps"])
        md = "".join(f"{i}. **{st['title'][0]}｜{st['title'][1]}**：{strip(st['text'][0])}<br>{strip(st['text'][1])}\n" for i, st in enumerate(b["steps"], 1))
        return f'<ol class="memory-steps flow-steps">{steps}</ol>', md

    def b_case(self, b):
        labels = {"S": ("Subjective", "主观"), "O": ("Objective", "客观"), "A": ("Assessment", "评估"), "P": ("Plan", "计划")}
        rows = "".join(f'<dt>{k} · {labels[k][0]} · {labels[k][1]}</dt><dd>{_bi(*b["soap"][k])}</dd>' for k in "SOAP")
        note = b.get("note", ["Teaching case, not a real patient.", "教学案例，不是真实病人。"])
        h = (f'<article class="muscle-card case-card"><div class="muscle-title"><span>✚</span><div><h4 lang="en">{b["title"][0]}</h4><small lang="zh-Hans">{b["title"][1]}</small></div></div>'
             f'<dl class="attachment-facts">{rows}</dl>{_bi(*note)}</article>')
        md = f"#### {b['title'][0]}｜{b['title'][1]}\n\n" + "".join(f"- **{k} {labels[k][0]} {labels[k][1]}**：{strip(b['soap'][k][0])}<br>{strip(b['soap'][k][1])}\n" for k in "SOAP") + f"\n*{note[0]} {note[1]}*\n"
        return h, md

    def b_dialogue(self, b):
        lines = "".join(f'<div class="dialogue-line"><b>{E(sp)}</b>{say_btn(strip(en))}{_bi(en, zh)}</div>' for sp, en, zh in b["lines"])
        md = "".join(f"- **{sp}**：{strip(en)}<br>{strip(zh)}\n" for sp, en, zh in b["lines"])
        return f'<div class="dialogue">{lines}</div>', md

    def b_paper(self, b):
        rec = json.loads((PAPERS / f"{b['id']}.json").read_text(encoding="utf-8"))
        p = rec["paper"]
        parts = [("question", "Research question", "研究问题"), ("design", "Design", "设计"), ("population", "Population", "人群"),
                 ("methods", "Methods", "方法"), ("results", "Results", "结果"), ("limitations", "Limitations", "局限"),
                 ("applicability", "Applicability", "适用范围")]
        h = [f'<article class="paper-card"><h3><span lang="en">{E(p["title"]["en"])}</span><span class="translation" lang="zh-Hans">{E(p["title"]["zh"])}</span></h3>'
             f'<p class="paper-meta">{E(p.get("byline", p["citation"]))} · {link("https://doi.org/" + p["doi"], "DOI " + E(p["doi"]))}</p>']
        md = [f"#### {p['title']['en']}｜{p['title']['zh']}\n\n{p.get('byline', p['citation'])} · [DOI {p['doi']}](https://doi.org/{p['doi']})\n"]
        for key, en, zh in parts:
            if p.get(key):
                h.append(f'<h4><span lang="en">{en}</span> · <span lang="zh-Hans">{zh}</span></h4>' + _bi(p[key]["en"], p[key]["zh"]))
                md.append(f"**{en}｜{zh}**\n\n{strip(p[key]['en'])}\n\n{strip(p[key]['zh'])}\n")
        if p.get("terms"):
            h.append('<dl class="attachment-facts">' + "".join(f'<dt>{E(t["term"]["en"])} · {E(t["term"]["zh"])}</dt><dd>{_bi(t["explanation"]["en"], t["explanation"]["zh"])}</dd>' for t in p["terms"]) + "</dl>")
            md.append("".join(f"- **{t['term']['en']}｜{t['term']['zh']}**：{strip(t['explanation']['en'])}<br>{strip(t['explanation']['zh'])}\n" for t in p["terms"]))
        srcs = " · ".join(link(s["url"], E(s["title"])) for s in rec.get("sources", [])[:4])
        h.append(f'<p class="model-link-row">{srcs}</p></article>')
        return "".join(h), "\n".join(md)

    def b_quiz(self, b):
        H, M = [], []
        self._check(H, M, b["items"])
        return "".join(H), "".join(M)

    def b_listen(self, b):
        items = "".join(f'<details class="quiz listen-item"><summary>{say_btn(en)}<span class="quiz-toggle">Listen, write it, then check · 听音写出，再展开</span></summary>'
                        f'<div class="bilingual-pair"><p lang="en">{E(en)} {self.pron_html(en)}</p><p class="translation" lang="zh-Hans">{E(zh)}</p></div></details>' for en, zh in b["words"])
        md = "".join(f"- 🔊 {en}（{zh}）\n" for en, zh in b["words"])
        return f'<div class="checkpoint listen"><p class="kicker"><span lang="en">Listen and write</span> <span lang="zh-Hans">听音辨词</span></p>{items}</div>', md

    def b_spell(self, b):
        items = "".join(f'<div class="spell-item"><label><span lang="zh-Hans">{E(zh)}</span>{say_btn(en)}<input type="text" autocomplete="off" autocapitalize="off" spellcheck="false" data-answer="{EA(en)}" aria-label="拼写 {EA(zh)}"></label>'
                        f'<button type="button" class="spell-check">Check · 核对</button><span class="spell-result" aria-live="polite"></span></div>' for en, zh in b["words"])
        md = "".join(f"- {zh}：________（{en}）\n" for en, zh in b["words"])
        return f'<div class="checkpoint spell"><p class="kicker"><span lang="en">Spell from memory</span> <span lang="zh-Hans">拼写默写</span></p>{items}</div>', md

    def _prompt_answer(self, b, kind, label_en, label_zh, field):
        pe, pz = b["prompt"]; ae, az = b["answer"]
        key = b.get("id") or re.sub(r"\W+", "-", strip(pe).lower())[:40]
        box = f'<textarea class="typed-notes" data-key="{EA(key)}" rows="6" aria-label="{EA(label_zh)}"></textarea>' if field else ""
        h = (f'<div class="checkpoint {kind}"><p class="kicker"><span lang="en">{label_en}</span> <span lang="zh-Hans">{label_zh}</span></p>{_bi(pe, pz)}{box}'
             f'<details class="quiz"><summary><span class="quiz-toggle">Compare with the reference · 对照原文</span></summary>{_bi(ae, az)}</details></div>')
        md = f"**{label_en}｜{label_zh}**：{strip(pe)}<br>{strip(pz)}\n\n<details><summary>Reference 原文</summary>\n\n{strip(ae)}<br>{strip(az)}\n\n</details>\n"
        return h, md

    def b_notes(self, b):
        return self._prompt_answer(b, "notes", "Type it from memory", "手敲笔记", True)

    def b_oral(self, b):
        return self._prompt_answer(b, "oral", "Say it aloud from memory", "口述", False)

    def b_due_cards(self, b):
        if not self.due:
            return ('<div class="checkpoint due"><p lang="en">No earlier cards are due today.</p><p class="translation" lang="zh-Hans">今天没有到期的旧卡。</p></div>',
                    "No earlier cards are due today. 今天没有到期的旧卡。\n")
        items = "".join(f'<details class="quiz"><summary><span class="question-pair"><span lang="zh-Hans">{E(c["title"])} <small>{E(c.get("sub", ""))}</small></span><span lang="zh-Hans">{E(c["ask"])}</span></span>'
                        f'<span class="quiz-toggle">Show answer · 展开答案</span></summary><dl>' + "".join(f"<dt>{E(k)}</dt><dd>{E(v)}</dd>" for k, v in c["fields"]) + f'</dl><p class="paper-meta">{E(c["learned"])}</p></details>' for c in self.due)
        md = "".join(f"- **{c['title']}**（{c.get('sub', '')}，{c['learned']}）：{c['ask']}\n" for c in self.due)
        return f'<div class="checkpoint due"><p class="kicker"><span lang="en">Spaced review: due today</span> <span lang="zh-Hans">间隔复习：今天到期</span></p>{items}</div>', md


class Renderer(WeeklyBlocks):
    def __init__(self, content, figs, due=None):
        """figs: {"01": "01-xxx.svg", ...} — files present in the day's 资源/ folder.
        due: review-center cards due on this date (F-10), filled in by the builder."""
        self.c = content
        self.due = due or []
        self.figs = figs
        self.pron = load_pron(content.get("pronunciation"), content.get("chapter"))
        self.mus = content.get("muscles", [])
        self.acu = content.get("acupoints", [])

    # ---------------------------------------------------------------- pronunciation
    def stress_html(self, st):
        return re.sub(r"\b([A-Z]{2,})\b", lambda m: f"<b>{m.group(1).lower()}</b>", E(st))

    def pron_html(self, en):
        p = self.pron.get(en)
        if not p:
            return ""
        return f'<span class="pron"><span class="stress" lang="en">{self.stress_html(p[1])}</span> <span class="ipa">{E(p[0])}</span></span>'

    def term_html(self, a, b, lang="en"):
        if lang == "zh":
            return (f'<span class="term has-pron acu-term"><button type="button" class="say" data-say="{E(a)}" data-lang="zh-CN" aria-label="朗读 {E(a)}"></button>'
                    f'<span class="term-txt"><b lang="zh-Hans">{E(a)}</b> <span class="pinyin" lang="zh-Latn">{E(b)}</span></span></span>')
        pr = self.pron_html(a)
        return (f'<span class="term{" has-pron" if pr else ""}"><button type="button" class="say" data-say="{E(a)}" data-lang="en-US" aria-label="Pronounce {E(a)}"></button>'
                f'<span class="term-txt"><b lang="en">{E(a)}</b> <small lang="zh-Hans">{E(b)}</small>{pr}</span></span>')

    def term_md(self, a, b, lang="en"):
        if lang == "zh":
            return f"{a}（{b}）"
        p = self.pron.get(a)
        return f"{a}（{b}）" + (f" `{p[1]}` {p[0]}" if p else "")

    # ---------------------------------------------------------------- chapter
    def chapter(self, ch):
        num, cid = ch["num"], ch["id"]
        en, zh = ch["title"]
        H = [f'<section id="{cid}" class="chapter" aria-labelledby="{cid}-heading"><header class="chapter-head"><span class="chapter-number">{num:02d}</span><div><h2 id="{cid}-heading"><span lang="en">{E(en)}</span><span class="translation" lang="zh-Hans">{E(zh)}</span></h2></div></header>']
        M = [f"## {num:02d} {en}\n\n{zh}\n"]
        self._before(H, M, cid, ch.get("goals", []), ch.get("terms", []))
        for b in ch.get("blocks", []):
            if b.get("end"):
                continue
            h, m = self.block(b)
            H.append(h); M.append(m)
        if ch.get("check"):
            self._check(H, M, ch["check"])
        for b in ch.get("blocks", []):   # blocks flagged "end" come after the self-check (e.g. sources)
            if b.get("end"):
                h, m = self.block(b)
                H.append(h); M.append(m)
        if ch.get("take"):
            te, tz = ch["take"]
            H.append(f'<div class="takeaway take-home"><b>Take-home · 本章要点</b><div><span lang="en">{te}</span><span class="translation" lang="zh-Hans">{tz}</span></div></div>')
            M.append(f"> **Take-home 本章要点：** {te}  \n> {tz}\n")
        H.append(f'<div class="chapter-done"><button type="button" class="mark-done" data-chapter="{cid}"><span lang="en">Mark this chapter as done</span> · <span lang="zh-Hans">标记本章已完成</span></button></div>')
        M.append("")
        if ch.get("bridge"):
            bid, btext, blabel = ch["bridge"]
            H.append(f'<div class="bridge"><span>{btext}</span><a href="#{bid}">{blabel} ↓</a></div>')
            M.append("")
        H.append("</section>")
        return "".join(H), "\n".join(M)

    def _before(self, H, M, cid, goals, terms):
        g = "".join(f'<li><span lang="en">{a}</span><span class="translation" lang="zh-Hans">{b}</span></li>' for a, b in goals)
        t = "".join(self.term_html(*tm) for tm in terms)
        H.append(f'<div class="before-read"><div class="before-goals"><p class="kicker"><span lang="en">After this chapter you can</span> <span lang="zh-Hans">读完本章，你能够</span> · <span class="read-time" data-chapter="{cid}"></span></p><ol>{g}</ol></div>'
                 f'<div class="before-terms"><p class="kicker"><span lang="en">Key terms</span> <span lang="zh-Hans">关键词（点按钮听发音）</span></p><div class="term-list">{t}</div></div></div>')
        M.append("> **After this chapter you can｜读完本章，你能够**\n" + "".join(f"> {i+1}. {a}<br>{b}\n" for i, (a, b) in enumerate(goals)) +
                 ">\n> **Key terms｜关键词：** " + " · ".join(self.term_md(*tm) for tm in terms) + "\n")

    def _check(self, H, M, qas):
        items = "".join(f'<details class="quiz checkpoint-q"><summary><span class="question-pair"><span lang="en">{qe}</span><span lang="zh-Hans">{qz}</span></span><span class="quiz-toggle">Show answer · 展开答案</span></summary><div class="bilingual-pair"><p lang="en">{ae}</p><p class="translation" lang="zh-Hans">{az}</p></div></details>' for qe, qz, ae, az in qas)
        H.append(f'<div class="checkpoint"><p class="kicker"><span lang="en">Check yourself before moving on</span> <span lang="zh-Hans">先自测，再往下读</span></p>{items}</div>')
        M.append("#### Check yourself｜先自测\n\n" + "".join(f"**Q.** {qe}<br>{qz}\n\n<details><summary>Answer 答案</summary>\n\n{ae}<br>{az}\n\n</details>\n\n" for qe, qz, ae, az in qas))

    # ---------------------------------------------------------------- blocks
    def block(self, b):
        t = b["t"]
        fn = getattr(self, "b_" + t, None)
        if not fn:
            raise ValueError(f"unknown block type: {t}")
        return fn(b)

    def b_p(self, b):
        return (f'<div class="bilingual-pair"><p lang="en">{b["en"]}</p><p class="translation" lang="zh-Hans">{b["zh"]}</p></div>',
                f"{strip(b['en'])}\n\n{strip(b['zh'])}\n")

    def b_h3(self, b):
        return (f'<h3><span lang="en">{E(b["en"])}</span><span class="translation" lang="zh-Hans">{E(b["zh"])}</span></h3>', f"### {b['en']}｜{b['zh']}\n")

    def b_fig(self, b):
        n = b["n"]
        return (f'<figure class="diagram"><div class="figure-scroll" tabindex="0" aria-label="{E(b["en"])} · {E(b["zh"])}">{{{{FIGURE:{n}}}}}</div><figcaption>{E(b["en"])}<br><span lang="zh-Hans">{E(b["zh"])}</span></figcaption></figure>',
                f"![{b['zh']}]({ASSET_DIR}/{self.figs[n]})\n\n*{b['en']}*  \n*{b['zh']}*\n")

    def b_html(self, b):
        return b["html"], b.get("md", "")

    def b_levels(self, b):
        items = "".join(f'<div><b lang="en">{lv}</b><span class="translation" lang="zh-Hans">{zh}</span></div>' for lv, zh in b["items"])
        return (f'<div class="note-card nerve-levels"><h3><span lang="en">{b["title"]}</span></h3><div class="level-key">{items}</div></div>',
                f"> **{strip(b['title'])}** — " + "；".join(f"{lv} {zh}" for lv, zh in b["items"]) + "\n")

    def b_pitfall(self, b):
        label = b.get("label", "易混点")
        return (f'<p class="mnemonic-original" lang="zh-Hans"><b>{label}：</b>{b["zh"]}</p>', f"**{label}：** {b['zh']}\n")

    def b_song(self, b):
        label = b.get("label", "经穴歌（传统）")
        return (f'<p class="mnemonic-original" lang="zh-Hans"><b>{label}：</b>{b["zh"]}</p>', f"**{label}：** {b['zh']}\n")

    def b_muscle_cards(self, b):
        cards = ['<div class="muscle-grid attachment-grid">']
        md = []
        for mu in self.mus:
            cards.append(f'<article class="muscle-card attachment-card" id="muscle-{mu["id"]}" style="--muscle:{mu["color"]}"><div class="muscle-title"><span>{mu["letter"]}</span><div><h4 lang="en">{mu["en"]}</h4><small lang="zh-Hans">{mu["zh"]}</small>{self.pron_html(mu["en"])}</div>{say_btn(mu["en"])}</div>'
                         f'<div class="attachment-diagram">{{{{FIGURE:{mu["figure"]}}}}}</div><dl class="attachment-facts">'
                         + "".join(f'<dt>{lab}</dt><dd><span lang="en">{mu[k][0]}</span><span class="translation" lang="zh-Hans">{mu[k][1]}</span></dd>' for lab, k in MEASURE_LABELS)
                         + '</dl>' + f'<div class="bilingual-pair"><p lang="en">{mu["sentence"][0]}</p><p class="translation" lang="zh-Hans">{mu["sentence"][1]}</p></div>'
                         + "".join(f'<div class="bilingual-pair"><p lang="en">{e}</p><p class="translation" lang="zh-Hans">{z}</p></div>' for e, z in mu.get("extra_pairs", []))
                         + f'<div class="bilingual-pair"><p lang="en">Acupoint anchor: {mu["acu_en"]}</p><p class="translation" lang="zh-Hans">穴位锚点：{mu["acu"]}</p></div>'
                         + f'<p class="model-link-row">{link(mu["source"], "Anatomy source · 解剖依据")}</p></article>')
            md.append(f"#### {mu['en']}｜{mu['zh']}\n\n![{mu['zh']}]({ASSET_DIR}/{self.figs[mu['figure']]})\n\n"
                      + "".join(f"- **{lab}**：{mu[k][0]}｜{mu[k][1]}\n" for lab, k in MEASURE_LABELS_MD)
                      + f"\n{mu['sentence'][0]}\n\n{mu['sentence'][1]}\n\n"
                      + "".join(f"{e}\n\n{z}\n\n" for e, z in mu.get("extra_pairs", []))
                      + f"穴位锚点：{mu['acu']}\n")
        mem = self.c.get("memory")
        if mem:
            ten, tzh = mem["title"]
            cards.append(f'<article class="muscle-card memory-card" style="--muscle:#3f6a5c"><div class="muscle-title"><span>✎</span><div><h4 lang="en">{ten}</h4><small lang="zh-Hans">{tzh}</small></div></div><ol class="memory-steps">'
                         + "".join(f'<li><b lang="en">{en}</b> <b lang="zh-Hans">{zh}</b><p lang="en">{te}</p><p class="translation" lang="zh-Hans">{tz}</p></li>' for en, zh, te, tz in mem["steps"])
                         + '</ol>' + (f'<p class="memory-hook"><b lang="en">Number hook</b> <span lang="en">{mem["hook"][0]}</span><span class="translation" lang="zh-Hans">数字钩子：{mem["hook"][1]}</span></p>' if mem.get("hook") else "") + '</article>')
            md.append(f"#### {ten}｜{tzh}\n\n" + "".join(f"{i}. **{en} {zh}**：{te}<br>{tz}\n" for i, (en, zh, te, tz) in enumerate(mem["steps"], 1))
                      + (f"\n**Number hook 数字钩子**：{mem['hook'][0]}（{mem['hook'][1]}）\n" if mem.get("hook") else ""))
        cards.append("</div>")
        return "".join(cards), "\n".join(md)

    def b_acu_cards(self, b):
        cards = ['<div class="acu-grid">']
        md = []
        for a in self.acu:
            special = f'<dt>特定穴</dt><dd>{a["special"]}</dd>' if a.get("special") else ""
            cards.append(f'<article class="acu-card" id="acu-{a["pinyin"]}"><header><h4><span class="acu-name">{a["name"]}</span> <span class="pinyin" lang="zh-Latn">{a["pinyin"]}</span></h4>{say_btn(a["name"], "zh-CN")}</header>'
                         f'<dl><dt>定位</dt><dd>{a["loc"]}</dd>' + (f'<dt lang="en">Location</dt><dd lang="en">{a["loc_en"]}</dd>' if a.get("loc_en") and b.get("show_en_loc") else "")
                         + f'<dt>层次（浅 → 深）</dt><dd>{a["layers"]}</dd><dt>安全提示</dt><dd class="safe">{a["safety"]}</dd><dt>相关肌肉</dt><dd>{a["muscles"]}</dd>{special}<dt>怎么找</dt><dd>{a["find"]}</dd></dl></article>')
            md.append(f"#### {a['name']}（{a['pinyin']}）\n\n- 定位：{a['loc']}\n" + (f"- Location: {a['loc_en']}\n" if a.get("loc_en") and b.get("show_en_loc") else "")
                      + f"- 层次：{a['layers']}\n- 安全：{a['safety']}\n- 相关肌肉：{a['muscles']}\n" + (f"- 特定穴：{a['special']}\n" if a.get("special") else "") + f"- 怎么找：{a['find']}\n")
        cards.append("</div>")
        return "".join(cards), "\n".join(md)

    def _table(self, head, rows, cls=""):
        th = "".join(f'<th>{E(a)}<span class="translation" lang="zh-Hans">{E(b)}</span></th>' for a, b in head)
        body = ""
        for r in rows:
            cells = []
            for k, (a, b) in enumerate(r):
                tag = "th" if k == 0 else "td"
                cells.append(f'<{tag}><span lang="en">{a}</span><span class="translation" lang="zh-Hans">{b}</span></{tag}>')
            body += "<tr>" + "".join(cells) + "</tr>"
        h = f'<div class="table-scroll"><table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'
        m = ("| " + " | ".join(f"{a} {b}" for a, b in head) + " |\n|" + "---|" * len(head) + "\n" +
             "".join("| " + " | ".join(f"{strip(a)}<br>{strip(b)}" for a, b in r) + " |\n" for r in rows))
        return h, m

    def b_summary_tables(self, b):
        h1, m1 = self._table([("Muscle", "肌肉"), ("Origin", "起点"), ("Insertion", "止点"), ("Nerve", "神经"), ("Action", "动作"), ("Acupoint", "穴位锚点")],
                             [[(m["en"], m["zh"]), tuple(m["o_short"]), tuple(m["i_short"]), tuple(m["n_short"]), tuple(m["a_short"]), (m["acu_en"], m["acu"])] for m in self.mus], cls="summary-table")
        h2, m2 = self._table([("Point", "穴位"), ("Location", "定位"), ("Layers", "层次"), ("Safety", "安全")],
                             [[(a["pinyin"], a["name"]), (a["loc_short"], a["loc"]), ("", a["layers"]), ("", a["safety"])] for a in self.acu], cls="summary-table")
        return h1 + h2, m1 + "\n" + m2

    def b_pron_table(self, b):
        rows = b["terms"]
        zh = b["zh_map"]
        h = ('<div class="table-scroll"><table class="pron-table"><thead><tr><th>Term<span class="translation" lang="zh-Hans">术语</span></th><th>Stress<span class="translation" lang="zh-Hans">重音拼读</span></th><th>IPA<span class="translation" lang="zh-Hans">音标</span></th><th>Dictionary<span class="translation" lang="zh-Hans">词典</span></th></tr></thead><tbody>'
             + "".join(f'<tr><th><span class="pron-term">{say_btn(t)}<span><span lang="en">{t}</span><span class="translation" lang="zh-Hans">{zh[t]}</span></span></span></th><td class="stress" lang="en">{self.stress_html(self.pron[t][1])}</td><td class="ipa">{self.pron[t][0]}</td><td>{link(self.pron[t][2], "Open · 打开")}</td></tr>' for t in rows)
             + '</tbody></table></div>')
        m = "| Term 术语 | Stress 重音 | IPA | Dictionary |\n|---|---|---|---|\n" + "".join(f"| {t} {zh[t]} | {self.pron[t][1]} | {self.pron[t][0]} | [link]({self.pron[t][2].replace(' ', '%20')}) |\n" for t in rows)
        return h, m

    def deck(self, extra):
        deck = []
        for a in self.acu:
            deck.append({"f": [a["name"] + " " + a["pinyin"], "定位？层次？"], "say": a["name"], "lang": "zh-CN", "b": [a["loc_short"], f"{a['loc']}。层次：{a['layers']}"]})
        for m in self.mus:
            deck.append({"f": [m["en"], m["zh"]], "say": m["en"], "lang": "en-US", "b": [m["sentence"][0], f"神经：{m['n'][1]}；动作：{m['a'][1]}"]})
        for e, z, x, y in extra:
            deck.append({"f": [e, z], "say": e.replace("____", "blank"), "lang": "en-US", "b": [x, y]})
        return deck

    def b_flashcards(self, b):
        deck = self.deck(b.get("extra", []))
        h = ('<div class="flashcards" id="flashcards"><div class="fc-head"><span class="fc-count"></span><button type="button" class="fc-reset">Reset · 重置</button></div>'
             '<div class="fc-card" tabindex="0"><div class="fc-front"></div><div class="fc-back" hidden></div></div>'
             '<div class="fc-actions"><button type="button" class="fc-say" aria-label="朗读"></button><button type="button" class="fc-flip">Show answer · 翻面</button><button type="button" class="fc-again" hidden>Again · 再来</button><button type="button" class="fc-know" hidden>Got it · 记住了</button></div>'
             '<script type="application/json" id="deck-data">' + json.dumps(deck, ensure_ascii=False).replace("</", "<\\/") + '</script></div>')
        m = "".join(f"- **{d['f'][0]}**（{d['f'][1]}）→ {d['b'][0]}<br>{d['b'][1]}\n" for d in deck)
        return h, m

    def b_sources(self, b):
        items = " · ".join(link(u, t) for u, t in self.c.get("sources", []))
        note = b.get("note", "穴位定位依据 GB/T 12346《腧穴名称与定位》")
        return (f'<div class="end-note"><b>Sources · 来源</b><p>{items} · {note}</p></div>',
                "**Sources 来源：** " + " · ".join(f"[{t}]({u})" for u, t in self.c.get("sources", [])) + f" · {strip(note)}\n")


def render_sections(content, figs, out_dir, due=None):
    """Write NN-id.html / NN-id.md for every chapter. Returns list of (num, id)."""
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    r = Renderer(content, figs, due)
    order = []
    for ch in content["chapters"]:
        h, m = r.chapter(ch)
        (out_dir / f"{ch['num']:02d}-{ch['id']}.html").write_text(h, encoding="utf-8")
        (out_dir / f"{ch['num']:02d}-{ch['id']}.md").write_text(m, encoding="utf-8")
        order.append((ch["num"], ch["id"]))
    return order
