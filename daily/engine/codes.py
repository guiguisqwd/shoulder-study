# -*- coding: utf-8 -*-
"""Content types (N-x new, O-x consolidation) and forms (F-x), read from the tables in
standards/daily/README.md so the names live in one place. Plan entries may also use the two
Saturday types `quiz` (weekly mixed test, DL-14) and `review` (cross-week spaced review, DL-15)."""
import re
from .paths import STANDARDS_DAILY

EXTRA = {"quiz": "本周小测", "review": "跨周间隔复习"}
# Each form needs at least one of these blocks in its chapter (F-6 may also be the chapter's own check list).
FORM_BLOCKS = {"F-1": {"p"}, "F-2": {"flow"}, "F-3": {"case"}, "F-4": {"dialogue"}, "F-5": {"paper"},
               "F-6": {"quiz"}, "F-7": {"flashcards"}, "F-8": {"listen"}, "F-9": {"spell"}, "F-10": {"due_cards"},
               "F-11": {"notes"}, "F-12": {"oral"}}


def table():
    """{code: name} for every N-, O- and F- row in the daily standard."""
    rows = re.findall(r"^\| ([NOF]-\d+) \| ([^|]+?) \|", STANDARDS_DAILY.read_text(encoding="utf-8"), re.M)
    return {code: name.strip() for code, name in rows} | EXTRA


def name(code):
    return table().get(code, code)
