# -*- coding: utf-8 -*-
"""All locations used by the daily pipeline, in one place."""
from pathlib import Path
import json

ENGINE = Path(__file__).resolve().parent
DAILY = ENGINE.parent                     # <repo>/daily
REPO = DAILY.parent                       # <repo>
DAYS = DAILY / "days"
RUNS = DAILY / "runs"
PLAN = DAILY / "plan" / "schedule.json"   # the 60-day plan (days before the weekly plan starts)
WEEKS = DAILY / "plan" / "weeks.json"     # the weekly plan (DL-12): one library chapter a week + six supplement days
PAPERS = DAILY / "papers"                 # paper records for N-5 (DL-07)
LIBRARY = REPO / "library"
STANDARDS_DAILY = REPO / "standards" / "daily" / "README.md"
TEMPLATES = ENGINE / "templates"
DATA = ENGINE / "data"
QA_JS = ENGINE / "qa" / "qa.js"
APP = REPO / "library" / "shoulder" / "3d"         # the 3D app the ?term= links are checked against
APP_SRC = APP / "src"
PUBLIC_DAILY = REPO / "site" / "public" / "daily"  # website copy of every published pack
CATALOG = DAILY / "catalog.json"

# Mac archive (written by Claude through the device bridge; "~" = the user's home on the Mac)
MAC_ROOT = "~/Documents/DPT-每日简报"
MAC_PACKS = MAC_ROOT + "/每日学习包"
MAC_ARCHIVE_MD = MAC_ROOT + "/daily"           # daily/<yyyy>/<mm>/<date>.md (tagged archive for agents)
MAC_INDEX = MAC_ROOT + "/index"                # catalog.jsonl, 纵向主题树.md, 横向主题.md
MAC_RUNS = MAC_ROOT + "/系统/运行记录"

SITE_BASE = "https://guiguisqwd.github.io/dpt-study/"
LOCAL_3D = "http://127.0.0.1:5178/"


def day_dir(date: str) -> Path:
    return DAYS / date


def content_path(date: str) -> Path:
    return day_dir(date) / "content.json"


def load_content(date: str) -> dict:
    return json.loads(content_path(date).read_text(encoding="utf-8"))


def out_name(content: dict) -> str:
    """Folder / file stem, e.g. 2026-10-07-第1天-肺经与胸前肌, weekly plan: 2026-10-12-第1周-肩袖穴位与肩袖肌."""
    if content.get("kind") == "learning":
        return f"{content['date']}-第{content['day']}天-{content['slug_zh']}"
    if content.get("schema") == "dpt-daily-pack/2":
        return f"{content['date']}-第{content['week']}周-{content['slug_zh']}"
    return f"{content['date']}-{content['slug_zh']}"


def build_dir(date: str) -> Path:
    """Everything generated for a day lives under days/<date>/build/ (committed: it is the record)."""
    return day_dir(date) / "build"
