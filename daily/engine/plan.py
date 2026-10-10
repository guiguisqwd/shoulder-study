# -*- coding: utf-8 -*-
"""Which day is it in the study plan?

From the first Sunday of plan/weeks.json (DL-10 to DL-15): `chapter_day` (Sunday: study the week's library
chapter), `supplement` (Monday–Saturday: the planned content items and forms) or `unplanned` (the week has
no day entries yet). Before that, plan/schedule.json: learning day / weekly review / final review / nothing.
"""
import datetime as dt
import json
from .paths import PLAN, WEEKS


def schedule():
    return json.loads(PLAN.read_text(encoding="utf-8"))


def weeks():
    return json.loads(WEEKS.read_text(encoding="utf-8"))


def weekly_start() -> str:
    return weeks()["weeks"][0]["sunday"]


def week_of(date: str):
    """The weeks.json entry whose Sunday-to-Saturday span holds this date, or None."""
    d = dt.date.fromisoformat(date)
    for w in weeks()["weeks"]:
        start = dt.date.fromisoformat(w["sunday"])
        if start <= d < start + dt.timedelta(days=7):
            return w
    return None


def weekly_info(date: str) -> dict:
    w = week_of(date)
    if w is None:
        return {"kind": "none", "date": date}
    base = {"date": date, "week": w["week"], "chapter": w.get("chapter"), "chapterName": w.get("chapterName")}
    if not w.get("chapter"):
        return {"kind": "unplanned", **base, "reason": f"week {w['week']} ({w['chapterName']}) has no chapter or day entries yet"}
    if date == w["sunday"]:
        return {"kind": "chapter_day", **base, "chapterStatus": w.get("chapterStatus"), "days": w.get("days")}
    days = w.get("days")
    if not isinstance(days, dict) or date not in days:
        return {"kind": "unplanned", **base, "reason": f"weeks.json week {w['week']} lists no items for {date}; fill them after the chapter's ST-1 list"}
    entries = [{"group": group, **e} for group in ("new", "consolidate") for e in days[date].get(group, [])]
    return {"kind": "supplement", **base, "entries": entries}


def day_info(date: str) -> dict:
    if date >= weekly_start():
        return weekly_info(date)
    S = schedule()
    for d in S["learning_days"]:
        if d["date"] == date:
            return {"kind": "learning", **d}
    if date in S.get("weekly_review_days", []):
        # the learning days of the week that ends on this review day
        end = dt.date.fromisoformat(date)
        week = [d for d in S["learning_days"] if 0 < (end - dt.date.fromisoformat(d["date"])).days <= 7]
        idx = S["weekly_review_days"].index(date) + 1
        return {"kind": "weekly_review", "date": date, "week": idx, "days": week}
    if date in S.get("final_review", []):
        return {"kind": "final_review", "date": date, "days": S["learning_days"]}
    return {"kind": "none", "date": date}


def tomorrow(date: str = None, tz: str = "America/Los_Angeles") -> str:
    if date:
        return (dt.date.fromisoformat(date) + dt.timedelta(days=1)).isoformat()
    return (today(tz) + dt.timedelta(days=1)).isoformat()


def today(tz: str = "America/Los_Angeles") -> dt.date:
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo(tz)).date()
    except Exception:  # pragma: no cover
        return dt.date.today()


def previous_learning_days(date: str, n: int = 3):
    S = schedule()
    return [d for d in S["learning_days"] if d["date"] < date][-n:]


def days_left(date: str, goal: str = "2026-12-23") -> int:
    return (dt.date.fromisoformat(goal) - dt.date.fromisoformat(date)).days


WEEKDAY = "一二三四五六日"


def weekday_zh(date: str) -> str:
    return "周" + WEEKDAY[dt.date.fromisoformat(date).weekday()]
