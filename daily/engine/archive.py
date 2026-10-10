# -*- coding: utf-8 -*-
"""Mac archive for agents (DPT-每日简报): detailed tagged Markdown + catalog + topic indexes,
and the manifest of files Claude writes to the Mac with device_commit_files.

Marking rules come from DPT-每日简报/README.md: vertical = place in the subject tree (fixed top
levels), horizontal = cross-topic themes (controlled vocabulary), one item-meta block per item."""
import datetime as dt, json, re, shutil
from pathlib import Path
from .paths import DAILY, DAYS, MAC_ROOT, MAC_PACKS, build_dir, out_name, load_content
from . import plan

TOP_LEVELS = ["解剖学", "生理学", "运动学/生物力学", "病理学", "神经科学", "检查评估", "康复干预", "循证方法学", "中医针灸对照"]
SEED = DAILY / "archive" / "seed-catalog.jsonl"
OFFS = [1, 3, 7, 14, 30]


def _review(date):
    d = dt.date.fromisoformat(date)
    return [(d + dt.timedelta(days=k)).isoformat() for k in OFFS]


def items(c):
    """One catalog item per muscle and per acupoint."""
    date = c["date"]; info = plan.day_info(date)
    region = (info.get("regions") or ["肌肉"])[0]
    day_h = c.get("tags", {}).get("horizontal", [])
    stem = out_name(c)
    out = []
    mids = [f"{date}-M{i + 1}" for i in range(len(c.get("muscles", [])))]
    pids = [f"{date}-P{i + 1}" for i in range(len(c.get("acupoints", [])))]
    for i, m in enumerate(c.get("muscles", [])):
        out.append({"item_id": mids[i], "date": date, "kind": "muscle", "title": f"{m['zh']} {m['en']}",
                    "vertical": m.get("vertical") or f"解剖学/肌肉/{region}/{m['zh']}",
                    "horizontal": sorted(set(day_h + m.get("horizontal", []) + ["记忆法"])),
                    "links_to": [pids[j] for j, a in enumerate(c.get("acupoints", [])) if a["name"] in m.get("acu", "")] or pids[:2],
                    "nerve": m["n"][0], "difficulty": 1, "source_url": m.get("source"),
                    "file": f"daily/{date[:4]}/{date[5:7]}/{date}.md#{mids[i].lower()}", "visual": f"每日学习包/{stem}/{stem}.html",
                    "review_schedule": _review(date)})
    for i, a in enumerate(c.get("acupoints", [])):
        out.append({"item_id": pids[i], "date": date, "kind": "acupoint", "title": f"{a['name']} {a.get('pinyin', '')} {a.get('code', '')}".strip(),
                    "vertical": a.get("vertical") or f"中医针灸对照/经络/{a.get('meridian', '')}/{a['name']}",
                    "horizontal": sorted(set(day_h + a.get("horizontal", []) + ["中西医对照/穴位-触发点"])),
                    "links_to": [mids[j] for j, m in enumerate(c.get("muscles", [])) if a["name"] in m.get("acu", "")],
                    "difficulty": 1, "file": f"daily/{date[:4]}/{date[5:7]}/{date}.md#{pids[i].lower()}",
                    "visual": f"每日学习包/{stem}/{stem}.html", "review_schedule": _review(date)})
    for it in out:
        top = it["vertical"].split("/")[0]
        assert top in TOP_LEVELS or it["vertical"].startswith("运动学/生物力学"), f"vertical top level not allowed: {it['vertical']}"
    return out


def day_markdown(c, run=None):
    date = c["date"]; info = plan.day_info(date); stem = out_name(c)
    its = items(c); byid = {i["item_id"]: i for i in its}
    nxt = [d for d in plan.schedule()["learning_days"] if d["date"] > date][:1]
    fm = ["---", f"doc_id: pack-{date}", "doc_type: daily-study-pack", f"date: {date}", f"weekday: {plan.weekday_zh(date)}",
          "timezone: America/Los_Angeles", "language: zh-CN + en", "schema_version: 2.0",
          f"items: [{', '.join(i['item_id'] for i in its)}]", f"day_theme: {c['title']['zh']} · {c['title']['en']}",
          "vertical_paths:"] + [f"  - {v}" for v in c.get("tags", {}).get("vertical", [])] + ["horizontal_themes:"] + \
         [f"  - {h}" for h in c.get("tags", {}).get("horizontal", [])] + \
         [f"keywords_en: [{', '.join([m['en'] for m in c.get('muscles', [])] + [a.get('pinyin', '') for a in c.get('acupoints', [])])}]",
          f"pack: 每日学习包/{stem}/{stem}.html", f"pack_md: 每日学习包/{stem}/{stem}.md",
          f"site: https://guiguisqwd.github.io/dpt-study/daily/{date}/index.html",
          f"next_up: [{', '.join(a['name'] for a in (nxt[0]['acupoints'] if nxt else []))}{'; ' if nxt else ''}{', '.join(m['zh'] for m in (nxt[0]['muscles'] if nxt else []))}]", "---", ""]
    when = f"第 {c['week']} 周 · {c.get('chapter_name', c['chapter'])}" if c.get("schema") == "dpt-daily-pack/2" else f"第 {c.get('day')} 天"
    L = fm + [f"# 每日学习包存档 · {date}（{plan.weekday_zh(date)}）· {when}", "",
              f"> {c['title']['zh']}｜{c['title']['en']}。推送页是 `{stem}.html`；本文件比推送页多出每一条知识的检索标记（纵向/横向）、复习日期和资料来源，供后续 Agent 检索复用。", ""]
    L += ["## 肌肉 Muscles", ""]
    for m, it in zip(c.get("muscles", []), [i for i in its if i["kind"] == "muscle"]):
        L += [f'<a id="{it["item_id"].lower()}"></a>', "", f"### {m['en']}｜{m['zh']}", "", "<!-- item-meta", *[f"{k}: {json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v}" for k, v in it.items()], "-->", "",
              f"- **Origin 起点**：{m['o'][0]}｜{m['o'][1]}", f"- **Insertion 止点**：{m['i'][0]}｜{m['i'][1]}",
              f"- **Nerve 神经**：{m['n'][0]}｜{m['n'][1]}", f"- **Action 动作**：{m['a'][0]}｜{m['a'][1]}", "",
              m["sentence"][0], "", m["sentence"][1], ""] + [f"{e}\n\n{z}\n" for e, z in m.get("extra_pairs", [])] + \
             [f"- 穴位锚点：{m['acu']}｜{m['acu_en']}", f"- 来源：{m.get('source', '')}", ""]
    L += ["## 穴位 Acupoints", ""]
    for a, it in zip(c.get("acupoints", []), [i for i in its if i["kind"] == "acupoint"]):
        L += [f'<a id="{it["item_id"].lower()}"></a>', "", f"### {a['name']}（{a.get('pinyin', '')}）{a.get('code', '')}", "", "<!-- item-meta", *[f"{k}: {json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v}" for k, v in it.items()], "-->", "",
              f"- 定位（GB/T 12346）：{a['loc']}"] + ([f"- Location (WHO 2008): {a['loc_en']}"] if a.get("loc_en") else []) + \
             [f"- 层次（浅 → 深）：{a['layers']}", f"- 安全提示：{a['safety']}", f"- 相关肌肉：{a['muscles']}"] + \
             ([f"- 特定穴：{a['special']}"] if a.get("special") else []) + [f"- 怎么找：{a['find']}"] + \
             ([f"- 来源：{' · '.join(a['sources'])}"] if a.get("sources") else []) + [""]
    L += ["## 自测题 Check questions", ""]
    for ch in c["chapters"]:
        for qe, qz, ae, az in ch.get("check", []):
            L += [f"- **Q.** {qe}｜{qz}", f"  - **A.** {ae}｜{az}"]
    L += ["", "## 来源 Sources", ""] + [f"- [{t}]({u})" for u, t in c.get("sources", [])]
    if run:
        L += ["", "## 生成记录 Run record", "", "```json", json.dumps(run, ensure_ascii=False, indent=1), "```"]
    return "\n".join(L) + "\n"


def catalog_lines():
    lines = [json.loads(l) for l in SEED.read_text(encoding="utf-8").splitlines() if l.strip()]
    seen = {l["item_id"] for l in lines}
    for f in sorted(DAYS.glob("*/content.json")):
        c = json.loads(f.read_text(encoding="utf-8"))
        if c.get("kind") not in ("learning", "supplement") or not (build_dir(c["date"]) / f"{out_name(c)}.html").exists():
            continue
        for it in items(c):
            if it["item_id"] not in seen:
                lines.append(it); seen.add(it["item_id"])
    return lines


def topic_indexes(lines):
    tree = {}
    for it in lines:
        node = tree
        for part in re.split(r"\s*[/>]\s*", it["vertical"]):
            node = node.setdefault(part, {})
        node.setdefault("__items__", []).append(it["item_id"])
    def walk(node, depth):
        out = []
        for k, v in node.items():
            if k == "__items__":
                continue
            ids = v.get("__items__", [])
            out.append("  " * depth + f"- {k}" + (f" → {', '.join(ids)}" if ids else ""))
            out += walk(v, depth + 1)
        return out
    vert = "# 纵向主题树\n\n" + "\n".join(walk(tree, 0)) + "\n"
    hz = {}
    for it in lines:
        for h in it.get("horizontal", []):
            hz.setdefault(h, []).append(it["item_id"])
    horiz = "# 横向主题\n\n" + "\n".join(f"- **{h}**：{', '.join(ids)}" for h, ids in hz.items()) + "\n"
    return vert, horiz


def stage(date, staging_root, run=None):
    """Copy everything the Mac should receive into staging_root (must be under /mnt/user-data/outputs/
    for device_commit_files) and return the manifest [{stagedPath, devicePath}]."""
    c = load_content(date); B = build_dir(date); stem = out_name(c)
    root = Path(staging_root) / date
    for old in ("pack", "index", "review-center", "runs", "archive.md", "manifest.json"):   # keep deliver/ and others
        q = root / old
        if q.is_dir():
            shutil.rmtree(q)
        elif q.exists():
            q.unlink()
    files = []
    def put(src_path=None, text=None, rel=None, device=None):
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if text is not None:
            dst.write_text(text, encoding="utf-8")
        else:
            shutil.copy2(src_path, dst)
        files.append({"stagedPath": str(dst), "devicePath": device})
    pack = f"{MAC_PACKS}/{stem}"
    put(B / f"{stem}.html", rel=f"pack/{stem}.html", device=f"{pack}/{stem}.html")
    put(B / f"{stem}.md", rel=f"pack/{stem}.md", device=f"{pack}/{stem}.md")
    for svg in sorted((B / "资源").glob("*.svg")):
        put(svg, rel=f"pack/资源/{svg.name}", device=f"{pack}/资源/{svg.name}")
    put(DAYS / date / "content.json", rel="pack/source/content.json", device=f"{pack}/source/content.json")
    if (DAYS / date / "figures.py").exists():
        put(DAYS / date / "figures.py", rel="pack/source/figures.py", device=f"{pack}/source/figures.py")
    for name in ["qa.json", "visual-review.json"]:
        if (B / "qa" / name).exists():
            put(B / "qa" / name, rel=f"pack/qa/{name}", device=f"{pack}/qa/{name}")
    put(text=day_markdown(c, run), rel="archive.md", device=f"{MAC_ROOT}/daily/{date[:4]}/{date[5:7]}/{date}.md")
    lines = catalog_lines()
    put(text="".join(json.dumps(l, ensure_ascii=False) + "\n" for l in lines), rel="index/catalog.jsonl", device=f"{MAC_ROOT}/index/catalog.jsonl")
    vert, horiz = topic_indexes(lines)
    put(text=vert, rel="index/纵向主题树.md", device=f"{MAC_ROOT}/index/纵向主题树.md")
    put(text=horiz, rel="index/横向主题.md", device=f"{MAC_ROOT}/index/横向主题.md")
    rc = DAILY / "review-center" / "index.html"
    if rc.exists():
        put(rc, rel="review-center/index.html", device=f"{MAC_ROOT}/复习中心/index.html")
    rr = DAILY / "runs" / f"{date}.json"
    if rr.exists():
        put(rr, rel=f"runs/{date}.json", device=f"{MAC_ROOT}/系统/运行记录/{date}.json")
    manifest = {"date": date, "files": files}
    (root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    assert len(files) <= 50, "device_commit_files takes at most 50 files per call"
    return manifest
