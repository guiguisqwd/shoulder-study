# -*- coding: utf-8 -*-
"""Publish a built day into the website source (site/public/daily/<date>/) and rebuild the
daily index page + daily/catalog.json. The GitHub Pages workflow ships public/daily/ on push to main."""
import html, json, shutil
from pathlib import Path
from .paths import PUBLIC_DAILY, CATALOG, DAYS, build_dir, out_name, load_content
from . import plan

E = lambda s: html.escape(str(s), quote=True)


def entry(date):
    c = load_content(date)
    B = build_dir(date)
    qa = json.loads((B / "qa" / "qa.json").read_text(encoding="utf-8")) if (B / "qa" / "qa.json").exists() else {}
    return {"date": date, "day": c.get("day"), "week": c.get("week"), "chapter": c.get("chapter"), "kind": c.get("kind"), "out": out_name(c), "title": c["title"],
            "acupoints": [[a["name"], a.get("pinyin", ""), a.get("code", "")] for a in c.get("acupoints", [])],
            "muscles": [[m["en"], m["zh"]] for m in c.get("muscles", [])],
            "tags": c.get("tags", {}), "figures": qa.get("figures"), "path": f"daily/{date}/index.html", "md": f"daily/{date}/{out_name(c)}.md"}


def publish_day(date):
    c = load_content(date)
    B = build_dir(date)
    stem = out_name(c)
    dst = PUBLIC_DAILY / date
    if dst.exists():
        shutil.rmtree(dst)
    (dst / "资源").mkdir(parents=True)
    shutil.copy2(B / f"{stem}.html", dst / "index.html")
    shutil.copy2(B / f"{stem}.md", dst / f"{stem}.md")
    for svg in sorted((B / "资源").glob("*.svg")):
        shutil.copy2(svg, dst / "资源" / svg.name)
    return dst


def rebuild_index():
    entries = []
    for f in sorted(DAYS.glob("*/content.json")):
        date = f.parent.name
        if (PUBLIC_DAILY / date / "index.html").exists():
            entries.append(entry(date))
    entries.sort(key=lambda e: e["date"], reverse=True)
    CATALOG.write_text(json.dumps({"schema": "dpt-daily-catalog/1", "entries": entries}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    S = plan.schedule()
    total_acu, total_mus = S["counts"]["acupoints"], S["counts"]["muscles_new"] + S["counts"]["muscles_learned"]
    learned_acu = sum(len(e["acupoints"]) for e in entries if e["kind"] in ("learning", "supplement"))
    learned_mus = sum(len(e["muscles"]) for e in entries if e["kind"] in ("learning", "supplement")) + S["counts"]["muscles_learned"]
    cards = []
    for e in entries:
        chips_a = "".join(f'<span class="chip acu">{E(n)}<small>{E(p)}</small></span>' for n, p, _ in e["acupoints"])
        chips_m = "".join(f'<span class="chip mus">{E(en)}<small>{E(zh)}</small></span>' for en, zh in e["muscles"])
        label = {"learning": f"Day {e['day']} · 第 {e['day']} 天", "supplement": f"Week {e.get('week')} · 第 {e.get('week')} 周",
                 "chapter_day": f"Week {e.get('week')} chapter · 第 {e.get('week')} 周章节日"}.get(e["kind"], "Review · 复习")
        cards.append(f'''<article class="day" data-search="{E((e['title']['zh'] + ' ' + e['title']['en'] + ' ' + ' '.join(a[0] for a in e['acupoints']) + ' ' + ' '.join(m[0] + ' ' + m[1] for m in e['muscles'])).lower())}">
<div class="meta"><span>{E(e['date'])} {plan.weekday_zh(e['date'])}</span><span>{label}</span></div>
<h2><a href="./{E(e['date'])}/index.html">{E(e['title']['zh'])}<small>{E(e['title']['en'])}</small></a></h2>
<div class="chips">{chips_a}{chips_m}</div>
<p class="tags">{' · '.join(E(t) for t in e['tags'].get('horizontal', []))}</p>
<p class="links"><a href="./{E(e['date'])}/index.html">Open pack · 打开学习包 ↗</a> <a href="./{E(e['date'])}/{E(e['out'])}.md">Markdown</a></p></article>''')
    page = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Daily study packs · 每日学习包</title>
<style>:root{{--paper:#faf7ef;--ground:#ede9df;--ink:#292b2a;--muted:#6c706b;--rule:#dad7cc;--accent:#42695e;--red:#ae4b3e}}*{{box-sizing:border-box}}body{{margin:0;background:var(--ground);color:var(--ink);font:16px/1.7 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}}
main{{max-width:980px;margin:auto;padding:40px 20px 70px}}.eyebrow{{font-size:12px;letter-spacing:2px;color:var(--muted)}}h1{{font:700 38px/1.25 "Kaiti SC","STKaiti","Songti SC",serif;margin:10px 0 6px}}h1 span{{display:block;font:400 17px/1.6 -apple-system,sans-serif;color:var(--muted)}}
.progress{{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0 8px}}.progress span{{background:var(--paper);border:1px solid var(--rule);border-radius:999px;padding:5px 14px;font-size:14px}}.bar{{height:8px;background:#ddd8cc;border-radius:9px;overflow:hidden;margin:6px 0 24px}}.bar i{{display:block;height:100%;background:var(--accent)}}
input{{width:100%;padding:11px 14px;border:1px solid var(--rule);border-radius:9px;background:var(--paper);font-size:15px;margin:6px 0 18px}}
.day{{background:var(--paper);border:1px solid var(--rule);border-radius:12px;padding:18px 20px;margin:0 0 14px}}.meta{{display:flex;justify-content:space-between;gap:12px;font-size:12.5px;color:var(--muted)}}
.day h2{{margin:6px 0 10px;font:700 25px/1.35 "Kaiti SC","STKaiti","Songti SC",serif}}.day h2 a{{color:var(--ink);text-decoration:none}}.day h2 small{{display:block;font:400 14px/1.5 -apple-system,sans-serif;color:var(--muted)}}
.chips{{display:flex;flex-wrap:wrap;gap:6px}}.chip{{border:1px solid var(--rule);border-radius:999px;padding:2px 10px;font-size:13.5px;background:#fffdf7}}.chip small{{color:var(--muted);margin-left:5px}}.chip.acu{{border-color:#e2b9ae;color:var(--red)}}
.tags{{font-size:12.5px;color:var(--muted);margin:10px 0 4px}}.links a{{color:var(--accent);font-weight:600;margin-right:14px;font-size:14px}}footer{{font-size:12px;color:var(--muted);margin-top:30px}}footer a{{color:var(--accent)}}</style></head>
<body><main><div class="eyebrow">DPT FOUNDATIONS · DAILY</div><h1>每日学习包<span>Daily study packs · acupoints, muscles, nerves and movement, English first</span></h1>
<div class="progress"><span>{learned_acu} / {total_acu} acupoints · 穴位</span><span>{learned_mus} / {total_mus} muscles · 肌肉</span><span>Goal · 目标 2026-12-23</span></div>
<div class="bar"><i style="width:{round(100 * (learned_acu + learned_mus) / (total_acu + total_mus), 1)}%"></i></div>
<input id="q" type="search" placeholder="Search a point or muscle · 搜索穴位或肌肉" autocomplete="off">
{''.join(cards) or '<p>No packs yet · 还没有学习包</p>'}
<footer>Every pack is generated and checked by the daily pipeline (daily/pipeline.py); run records are in the repository under daily/runs/. · 每份学习包都由每日流程生成并检查，运行记录见仓库 daily/runs/。 <a href="../study.html">Topic library · 主题库</a></footer></main>
<script>const q=document.getElementById('q'),days=[...document.querySelectorAll('.day')];q.addEventListener('input',()=>{{const v=q.value.trim().toLowerCase();days.forEach(d=>d.hidden=!d.dataset.search.includes(v));}});</script></body></html>'''
    PUBLIC_DAILY.mkdir(parents=True, exist_ok=True)
    (PUBLIC_DAILY / "index.html").write_text(page, encoding="utf-8")
    return {"entries": len(entries), "learned_acupoints": learned_acu, "learned_muscles": learned_mus}
