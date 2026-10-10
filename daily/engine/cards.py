# -*- coding: utf-8 -*-
"""Spaced-repetition cards for the review center (复习中心), built from every day's content.json
plus the legacy shoulder preview (plan/legacy/*.json). Intervals 1, 3, 7, 14, 30 days."""
import datetime as dt, json
from .paths import DAYS, DAILY, TEMPLATES
from . import plan

OFFSETS = [1, 3, 7, 14, 30]


def _acu_card(a, date, region):
    return {"id": "acu-" + a["name"], "type": "acu", "learned": date, "title": a["name"], "sub": a.get("meridian", ""), "meridian": a.get("meridian", ""), "region": region,
            "fields": [["定位", a["loc"]], ["层次（浅 → 深）", a["layers"]], ["安全提示", a.get("safety", "—")], ["相关肌肉", a.get("muscles", "")]]
                      + ([["怎么找", a["find"]]] if a.get("find") else []) + ([["记忆提示", a["hint"]]] if a.get("hint") else []),
            "ask": "定位在哪里？从浅到深经过哪些肌肉？"}


def _mus_card(m, date, region):
    return {"id": "mus-" + m["en"], "type": "mus", "learned": date, "title": m["zh"], "sub": m["en"], "meridian": "", "region": region,
            "fields": [["英文名", m["en"]], ["起点 Origin", m["o"][0] + "｜" + m["o"][1]], ["止点 Insertion", m["i"][0] + "｜" + m["i"][1]],
                       ["神经 Nerve", m["n"][0] + "｜" + m["n"][1]], ["动作 Action", m["a"][0] + "｜" + m["a"][1]], ["穴位锚点", m.get("acu", "")]],
            "ask": "英文名？起点、止点、神经、动作？"}


def all_cards(upto=None):
    cards = {}
    def add(c):
        old = cards.get(c["id"])
        if old:
            c["learned"] = min(old["learned"], c["learned"])
        cards[c["id"]] = c
    for f in sorted((DAILY / "plan" / "legacy").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for a in d.get("acupoints", []):
            add(_acu_card(a, d["date"], a.get("region", "")))
        for m in d.get("muscles", []):
            add(_mus_card(m, d["date"], m.get("region", "")))
    for f in sorted(DAYS.glob("*/content.json")):
        c = json.loads(f.read_text(encoding="utf-8"))
        if c.get("kind") not in ("learning", "supplement") or (upto and c["date"] > upto):
            continue
        info = plan.day_info(c["date"])
        region = "、".join(info.get("regions", [])) or c.get("chapter_name", "")
        for a in c.get("acupoints", []):
            add(_acu_card(a, c["date"], region))
        for m in c.get("muscles", []):
            add(_mus_card(m, c["date"], region))
    return list(cards.values())


def due(date, cards=None):
    cards = cards if cards is not None else all_cards(upto=date)
    d0 = dt.date.fromisoformat(date)
    return [c for c in cards if c["learned"] < date and (d0 - dt.date.fromisoformat(c["learned"])).days in OFFSETS]


def write_review_center(out_dir):
    """review-center/index.html (Artifact page body, no doctype) + cards.json."""
    out_dir.mkdir(parents=True, exist_ok=True)
    cards = all_cards()
    data = json.dumps(cards, ensure_ascii=False).replace("</", "<\\/")
    tpl = (TEMPLATES / "review_template.html").read_text(encoding="utf-8")
    (out_dir / "index.html").write_text(tpl.replace("__CARDS__", data), encoding="utf-8")
    (out_dir / "cards.json").write_text(json.dumps(cards, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"cards": len(cards), "acupoints": sum(c["type"] == "acu" for c in cards), "muscles": sum(c["type"] == "mus" for c in cards)}
