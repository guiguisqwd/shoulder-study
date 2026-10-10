#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DPT daily study pack pipeline — every step is checked and recorded.

Two phases, each a fixed list of steps. A step is either AUTO (this script does it and checks the
result) or CLAUDE (a tool action only the running Claude session can do: write the content, look at
the screenshots, write files to the Mac, send the file). The script never skips a step: it stops at
the first unfinished step, prints exactly what is needed, and exits with that step's code. Claude
does the action, records evidence with `mark`, and runs the phase again. `verify` exits 0 only when
every step of the phase is done (with evidence) — otherwise it lists what is missing.

  python3 daily/pipeline.py evening [--date D]   # build the pack for D (default: tomorrow, Pacific)
  python3 daily/pipeline.py morning [--date D]   # deliver the pack for D (default: today, Pacific)
  python3 daily/pipeline.py mark STEP --date D --evidence TEXT|@file.json
  python3 daily/pipeline.py status [--date D]
  python3 daily/pipeline.py verify --date D --phase evening|morning
  python3 daily/pipeline.py brief --date D        # write the authoring brief for D

Exit codes: 0 done · 10 author content · 11 visual review · 12 write to Mac · 13 deliver file ·
14 review center · 20 validation failed · 21 figures failed · 22 build failed · 23 QA failed ·
24 git commit/push blocked · 30 pack missing (morning) · 2 usage error.
"""
import argparse, datetime as dt, hashlib, json, os, shutil, subprocess, sys, tempfile, traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine import paths, plan, schema, build as builder, site, archive, cards, codes  # noqa: E402
from engine.paths import DAYS, RUNS, REPO, DAILY  # noqa: E402

STAGING = Path(os.environ.get("DPT_STAGING") or ("/mnt/user-data/outputs/dpt-daily" if Path("/mnt/user-data/outputs").is_dir()
                                                  else str(Path(tempfile.gettempdir()) / "dpt-daily")))
TZ = "America/Los_Angeles"

EVENING = [  # (name, kind, exit code if it needs action / fails)
    ("plan", "auto", 2),
    ("author", "claude", 10),
    ("figures", "auto", 21),
    ("validate", "auto", 20),
    ("build", "auto", 22),
    ("qa", "auto", 23),
    ("visual_review", "claude", 11),
    ("site", "auto", 22),
    ("cards", "auto", 22),
    ("publish", "auto", 24),
]
# The evening phase runs where the repository can be pushed (a Claude Code routine with the repo attached).
# The morning phase runs in the Mac-linked Cowork task: it clones the pushed repo, delivers the pack,
# updates the review-center artifact and writes the archive (including this run record) to the Mac.
MORNING = [
    ("locate", "auto", 30),
    ("deliver", "claude", 13),
    ("review_center", "claude", 14),
    ("archive", "claude", 12),
]
PHASES = {"evening": EVENING, "morning": MORNING}
# Steps whose evidence may be "skipped: <reason>" without failing verify (the reason is recorded).
SKIPPABLE = {"review_center"}


def now():
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


# ------------------------------------------------------------------ run record
def run_path(date):
    return RUNS / f"{date}.json"


def load_run(date):
    p = run_path(date)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"date": date, "phases": {}, "history": []}


def save_run(run):
    RUNS.mkdir(parents=True, exist_ok=True)
    run_path(run["date"]).write_text(json.dumps(run, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def step_rec(run, phase, name):
    ph = run["phases"].setdefault(phase, {"steps": {}})
    return ph["steps"].setdefault(name, {"status": "pending"})


def set_step(run, phase, name, status, evidence=None, error=None, **extra):
    r = step_rec(run, phase, name)
    r.update({"status": status, "at": now()})
    if evidence is not None:
        r["evidence"] = evidence
    if error is not None:
        r["error"] = error
    elif "error" in r and status == "done":
        r.pop("error")
    r.update(extra)
    run["history"].append({"at": r["at"], "phase": phase, "step": name, "status": status})
    save_run(run)
    with open(RUNS / "log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"date": run["date"], "at": r["at"], "phase": phase, "step": name, "status": status,
                            **({"error": str(error)[:300]} if error else {})}, ensure_ascii=False) + "\n")


def fingerprint(date):
    h = hashlib.sha256()
    for p in [DAYS / date / "content.json", DAYS / date / "figures.py"]:
        if p.exists():
            h.update(p.read_bytes())
    # only engine files that change the pack itself (not the archive/site/pipeline plumbing)
    eng = DAILY / "engine"
    for p in sorted([*(eng / "figlib").rglob("*.py"), eng / "render.py", eng / "build.py", *(eng / "templates").glob("reading-*"), *(eng / "data").glob("*.json")]):
        if p.is_file():
            h.update(p.read_bytes())
    return h.hexdigest()[:16]


def page_sha(date):
    B = paths.build_dir(date)
    h = hashlib.sha256()
    for p in sorted(B.glob("*.html")) + sorted((B / "资源").glob("*.svg")):
        h.update(p.read_bytes())
    return h.hexdigest()[:16]


# ------------------------------------------------------------------ helpers
def sh(cmd, cwd=None, check=True, timeout=600):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(map(str, cmd))} failed ({r.returncode}):\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}")
    return r


def say(msg):
    print(msg, flush=True)


def need(code, title, lines):
    say("\n" + "=" * 72 + f"\nACTION NEEDED · {title} (exit {code})\n" + "=" * 72)
    for l in lines:
        say("  " + l)
    say("=" * 72)
    return code


# ------------------------------------------------------------------ authoring brief
def write_weekly_brief(date, info):
    """Brief for a Monday–Saturday pack of the weekly plan (standards/daily/README.md)."""
    d = DAYS / date
    d.mkdir(parents=True, exist_ok=True)
    names = codes.table()
    prev = sorted(p.parent.name for p in DAYS.glob("*/content.json")
                  if p.parent.name < date and json.loads(p.read_text(encoding="utf-8")).get("kind") == "supplement")
    lines = [f"# Authoring brief · {date} {plan.weekday_zh(date)}", "",
             f"Week {info['week']} · chapter `{info['chapter']}` ({info['chapterName']}) · rules: `standards/daily/README.md`", "",
             "## Today's chapters (one per plan entry, same order; content/items/forms copied exactly from plan/weeks.json)", ""]
    for k, e in enumerate(info["entries"], 1):
        forms = "; ".join(f"{f} {names.get(f, '?')} → block `{'/'.join(sorted(codes.FORM_BLOCKS.get(f, {'?'})))}`" for f in e["forms"])
        lines += [f"{k}. **{e['type']} {names.get(e['type'], '')}** ({'新' if e['group'] == 'new' else '旧的夯实'})",
                  f"   - items: {json.dumps(e['items'], ensure_ascii=False)}", f"   - forms: {forms}"]
    lines += ["", "## What to write", "",
              f"1. `daily/days/{date}/content.json` — schema `dpt-daily-pack/2`, kind `supplement`, `week` {info['week']}, `chapter` `{info['chapter']}`, "
              f"`chapter_name` `{info['chapterName']}`. Each chapter carries `content`, `items`, `forms` as above plus the usual title/toc/goals/terms/blocks/bridge. "
              "Field and block definitions: `daily/CONTENT_SCHEMA.md` (v2 section)" + (f"; the last weekly pack is `daily/days/{prev[-1]}/content.json`." if prev else "."),
              f"2. `daily/days/{date}/figures.py` — `build(out_dir)` drawing every figure in `content.figures` with `engine.figlib` (an empty build is fine when no figure is needed). "
              "To reuse a chapter figure (DL-03) call `copy_library_figure(chapter, name, out_dir, out_name)`; it strips the displacement filter the figure check rejects.",
              "3. Consolidation (O-x): take the facts from the chapter `library/" + info["chapter"] + "/content.json` (DL-01), do not rewrite them differently.",
              "   New content: N-1 acupoints in `content.acupoints` with `meridian` (AN-20 to AN-24); N-5 papers come from `daily/papers/<id>.json` (block `paper`);",
              "   N-2/N-3/N-4/N-6/N-7 need sources you actually opened (G-02); N-4 cases are teaching cases.",
              "4. Rules: English first then Chinese; pronunciation for every English key term (content.pronunciation or engine/data/pronunciation.json); "
              "no public-health framing; archive tags (tags.vertical with fixed top levels, tags.horizontal).",
              "5. Then run `python3 daily/pipeline.py evening --date " + date + "` again."]
    (d / "AUTHORING_BRIEF.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return d / "AUTHORING_BRIEF.md"


def write_brief(date):
    info = plan.day_info(date)
    if info["kind"] == "supplement":
        return write_weekly_brief(date, info)
    d = DAYS / date
    d.mkdir(parents=True, exist_ok=True)
    prev = sorted(p.parent.name for p in DAYS.glob("*/content.json") if p.parent.name < date)
    ref = prev[-1] if prev else "2026-10-07"
    lines = [f"# Authoring brief · {date}", "",
             f"Kind: **{info['kind']}**"]
    if info["kind"] == "learning":
        lines += [f"Day {info['day']} · meridians: {', '.join(info['meridians'])} · regions: {', '.join(info['regions'])}", "",
                  "## Today's items (must match exactly, same order)", "",
                  "Acupoints: " + "、".join(f"{a['name']} {a['code']}" for a in info["acupoints"]),
                  "", "Muscles: " + "、".join(f"{m['zh']} {m['en']}" for m in info["muscles"]), ""]
    lines += ["## What to write", "",
              f"1. `daily/days/{date}/content.json` — schema `dpt-daily-pack/1`; copy the structure of `daily/days/{ref}/content.json` "
              "(six chapters muscles → nerve → motion → acupoints → review → english, block types in `daily/CONTENT_SCHEMA.md`).",
              f"2. `daily/days/{date}/figures.py` — `build(out_dir)` that draws every figure declared in `content.figures` with "
              "`engine.figlib` (reuse region base art: chest.py, arm.py, …; add new base art to engine/figlib/ when a new region appears).",
              "3. Facts: verify from sources you actually open (StatPearls/NCBI, TeachMeAnatomy, Kenhub, Radiopaedia; acupoints: GB/T 12346-2021, "
              "WHO 2008, 《针灸学》). Put URLs in muscle.source / acupoint.sources / content.sources. Never invent; mark uncertainty in text.",
              "4. Rules: English first then Chinese; muscle sentence 'The X originates from …, passes …, and inserts onto ….'; nerve with segments "
              "(C = Cervical 颈部, T = Thoracic 胸部); nerve figure starts from the spine; movement explained from line of pull with firing order/force "
              "couples where relevant; every acupoint: GB/T location, layers skin → deep, safety, related muscles, how to find, shown on a figure with the "
              "surrounding muscles; layer figures say 'not needling depth or direction'; pronunciation (IPA + CAPS stress + dictionary URL) for every English key term; "
              "no public-health framing; archive tags (tags.vertical with fixed top levels, tags.horizontal from the controlled vocabulary in DPT-每日简报/README.md).",
              "5. Then run `python3 daily/pipeline.py evening --date " + date + "` again."]
    (d / "AUTHORING_BRIEF.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return d / "AUTHORING_BRIEF.md"


# ------------------------------------------------------------------ evening steps
def s_plan(run, date):
    info = plan.day_info(date)
    run["kind"] = info["kind"]
    if info["kind"] == "learning":
        run["day"] = info["day"]
    if "week" in info:
        run["week"], run["chapter"] = info["week"], info["chapter"]
        if info["kind"] == "unplanned":
            set_step(run, "evening", "plan", "failed", error=info["reason"])
            return need(2, "the weekly plan has nothing for this date", [info["reason"], "Fill daily/plan/weeks.json (DL-12) and run again."])
        set_step(run, "evening", "plan", "done", evidence={"kind": info["kind"], "week": info["week"], "chapter": info["chapter"],
                                                            "entries": [[e["type"], e["items"], e["forms"]] for e in info.get("entries", [])]})
        return 0
    set_step(run, "evening", "plan", "done", evidence={"kind": info["kind"], "day": info.get("day"),
                                                        "acupoints": [a["name"] for a in info.get("acupoints", [])],
                                                        "muscles": [m["zh"] for m in info.get("muscles", [])]})
    return 0


def s_author(run, date):
    info = plan.day_info(date)
    c, f = DAYS / date / "content.json", DAYS / date / "figures.py"
    if info["kind"] in ("weekly_review", "final_review") and not c.exists():
        from engine import review_pack
        review_pack.write(date, info)
    if info["kind"] == "chapter_day" and not c.exists():
        from engine import week_pack
        week_pack.write_chapter_day(date, info)
    if info["kind"] == "none":
        set_step(run, "evening", "author", "done", evidence="no study item planned for this date")
        return 0
    if c.exists() and f.exists():
        set_step(run, "evening", "author", "done", evidence={"content": str(c.relative_to(REPO)), "figures": str(f.relative_to(REPO)),
                                                              "fingerprint": fingerprint(date)})
        return 0
    b = write_brief(date)
    set_step(run, "evening", "author", "waiting", evidence=str(b.relative_to(REPO)))
    return need(10, "write today's content", [f"Read {b.relative_to(REPO)} and write content.json + figures.py for {date}.",
                                              "Then run the evening phase again."])


def s_figures(run, date):
    import xml.etree.ElementTree as ET
    out = paths.build_dir(date) / "资源"
    if out.exists():
        shutil.rmtree(out)
    sh([sys.executable, str(DAYS / date / "figures.py"), str(out)], cwd=DAYS / date)
    first = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob("*.svg")}
    tmp = paths.build_dir(date) / "_figcheck"
    if tmp.exists():
        shutil.rmtree(tmp)
    sh([sys.executable, str(DAYS / date / "figures.py"), str(tmp)], cwd=DAYS / date)
    second = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in tmp.glob("*.svg")}
    shutil.rmtree(tmp)
    if first != second:
        raise RuntimeError("figures.py is not deterministic (two runs gave different SVGs)")
    c = paths.load_content(date)
    declared = set(c.get("figures", {}))
    have = {n[:2] for n in first}
    if declared != have:
        raise RuntimeError(f"declared figures {sorted(declared)} != drawn {sorted(have)}")
    for p in sorted(out.glob("*.svg")):
        ET.fromstring(p.read_text(encoding="utf-8"))
        if "feDisplacementMap" in p.read_text(encoding="utf-8"):
            raise RuntimeError(f"{p.name}: displacement filters are not allowed (seams in Chrome); use the double-stroke Fig.path")
    set_step(run, "evening", "figures", "done", evidence={"svgs": sorted(first)})
    return 0


def s_validate(run, date):
    errs = schema.validate(paths.load_content(date))
    if errs:
        set_step(run, "evening", "validate", "failed", error=errs)
        return need(20, "content.json has problems", errs)
    set_step(run, "evening", "validate", "done", evidence=f"schema {paths.load_content(date)['schema']}: 0 problems")
    return 0


def s_build(run, date):
    rep = builder.build(date)
    set_step(run, "evening", "build", "done", evidence=rep)
    run["out"] = rep["out"]
    return 0


def s_qa(run, date):
    from PIL import Image
    B = paths.build_dir(date)
    c = paths.load_content(date)
    qa_dir = B / "qa"
    keep = (qa_dir / "visual-review.json").read_bytes() if (qa_dir / "visual-review.json").exists() else None
    if qa_dir.exists():
        shutil.rmtree(qa_dir)
    qa_dir.mkdir(parents=True)
    if keep:  # the reviewer's record survives a re-run; it is only accepted again if the page is unchanged or re-reviewed
        (qa_dir / "visual-review.json").write_bytes(keep)
        os.utime(qa_dir / "visual-review.json", (0, 0))
    sh(["node", str(paths.QA_JS), str(B / f"{paths.out_name(c)}.html"), str(qa_dir)], timeout=300)
    q = json.loads((qa_dir / "qa.json").read_text(encoding="utf-8"))
    problems = []
    if q["errors"]: problems.append(f"JS errors: {q['errors'][:5]}")
    if q["overlaps"]: problems.append(f"SVG text overlaps: {q['overlaps'][:8]}")
    if q["outside"]: problems.append(f"SVG text outside its figure: {q['outside'][:8]}")
    want = [ch["id"] for ch in c["chapters"]]
    if q["chapters"] != want: problems.append(f"chapters on page {q['chapters']} != {want}")
    if q["figures"] < len(c.get("figures", {})): problems.append(f"only {q['figures']} figures rendered, {len(c.get('figures', {}))} declared")
    if q["mobile_scroll_width"] and q["mobile_scroll_width"] > 392: problems.append(f"horizontal scroll on a phone: {q['mobile_scroll_width']}px")
    if q["terms_without_pron"]: problems.append(f"key terms without pronunciation: {q['terms_without_pron']}")
    if c.get("kind") == "learning" and q.get("flashcards", 0) < len(c.get("acupoints", [])) + len(c.get("muscles", [])):
        problems.append("flashcard deck incomplete")
    # slices that a human-size eye can read (tall chapter shots → ≤1300 px pieces)
    view = qa_dir / "view"; view.mkdir()
    pieces = []
    for p in q["screenshots"] + q["figure_shots"]:
        im = Image.open(p); w, h = im.size
        if h <= 1400:
            dst = view / Path(p).name; im.save(dst); pieces.append(dst.name)
        else:
            for k, y in enumerate(range(0, h, 1300)):
                dst = view / f"{Path(p).stem}-{k + 1}.png"; im.crop((0, y, w, min(h, y + 1300))).save(dst); pieces.append(dst.name)
    (qa_dir / "view-list.json").write_text(json.dumps(pieces, ensure_ascii=False, indent=1), encoding="utf-8")
    if problems:
        set_step(run, "evening", "qa", "failed", error=problems)
        return need(23, "automatic QA failed — fix content/figures and rerun", problems)
    set_step(run, "evening", "qa", "done", evidence={k: q[k] for k in ["figures", "say_buttons", "mobile_scroll_width", "flashcards"]} | {"views": len(pieces)})
    return 0


def s_visual_review(run, date):
    qa_dir = paths.build_dir(date) / "qa"
    vr = qa_dir / "visual-review.json"
    pieces = json.loads((qa_dir / "view-list.json").read_text(encoding="utf-8"))
    try:
        r = json.loads(vr.read_text(encoding="utf-8")) if vr.exists() else {}
    except json.JSONDecodeError as e:
        r = {}
        say(f"visual-review.json is not valid JSON: {e}")
    if r and r.get("verdict") == "pass" and r.get("page_sha") == page_sha(date):
        set_step(run, "evening", "visual_review", "done", evidence={"viewed": len(r.get("viewed", [])), "notes": r.get("notes", "")[:500],
                                                                   "carried_over": "page and figures identical to the reviewed version"})
        return 0
    if r and vr.stat().st_mtime >= (qa_dir / "qa.json").stat().st_mtime:
        missing = [p for p in pieces if p not in r.get("viewed", [])]
        if r.get("verdict") == "pass" and not missing and r.get("notes"):
            r["page_sha"] = page_sha(date)
            vr.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
            set_step(run, "evening", "visual_review", "done", evidence={"viewed": len(r["viewed"]), "notes": r["notes"][:500],
                                                                       "fixed": r.get("fixed", [])})
            return 0
        problems = ([f"not viewed: {missing[:10]}"] if missing else []) + ([] if r.get("verdict") == "pass" else [f"verdict: {r.get('verdict')}"]) + \
                   ([] if r.get("notes") else ["notes are empty"])
    else:
        problems = ["no visual-review.json newer than qa.json"]
    set_step(run, "evening", "visual_review", "waiting", error=problems)
    return need(11, "look at every screenshot", [
        f"Open each image in daily/days/{date}/build/qa/view/ with the Read tool ({len(pieces)} images).",
        "Check: labels readable and not covering structures; leaders point at the right structure; acupoint dots on the right",
        "anatomy; English first; nothing cut off; figure matches the text. Fix figures.py/content.json and rerun if not.",
        f"Then write daily/days/{date}/build/qa/visual-review.json:",
        '  {"reviewer": "claude", "verdict": "pass", "viewed": [<every file name from qa/view-list.json>],',
        '   "notes": "<what you checked and what you saw>", "fixed": ["<issues fixed before passing>"]}',
        "and run the evening phase again."] + problems)


def s_site(run, date):
    site.publish_day(date)
    rep = site.rebuild_index()
    set_step(run, "evening", "site", "done", evidence=rep | {"page": f"site/public/daily/{date}/index.html"})
    return 0


def s_cards(run, date):
    rep = cards.write_review_center(DAILY / "review-center")
    rep["due_on_" + date] = len(cards.due(date))
    set_step(run, "evening", "cards", "done", evidence=rep)
    return 0


def s_archive(run, date):
    steps = {f"{ph}/{k}": v.get("status") for ph in ("evening", "morning") for k, v in run["phases"].get(ph, {}).get("steps", {}).items()}
    set_step(run, "morning", "archive", "waiting")
    man = archive.stage(date, STAGING, run={"date": date, "fingerprint": fingerprint(date), "steps": steps})
    mpath = STAGING / date / "manifest.json"
    set_step(run, "morning", "archive", "waiting", evidence=str(mpath))
    return need(12, "write the pack to the Mac", [
        f"Call device_commit_files with the {len(man['files'])} entries in {mpath} (stagedPath → devicePath).",
        f"Save the tool's JSON result to {STAGING / date / 'commit-result.json'} and run:",
        f"  python3 daily/pipeline.py mark archive --date {date} --evidence @{STAGING / date / 'commit-result.json'}",
        "If the Mac is offline, record that instead (the step stays unfinished and verify will report it):",
        f"  python3 daily/pipeline.py mark archive --date {date} --failed 'Mac offline: <tool error>'"])


def s_review_center(run, date):
    rec = step_rec(run, "morning", "review_center")
    if rec.get("status") == "done":
        return 0
    set_step(run, "morning", "review_center", "waiting")
    return need(14, "update the review center (复习中心)", [
        "Publish daily/review-center/index.html to the existing review-center artifact with the Artifact tool:",
        "  read https://claude.ai/artifact/3k1RZqb9tf9heXKLHe58ig first, then publish file_path=daily/review-center/index.html with that url.",
        f"Then: python3 daily/pipeline.py mark review_center --date {date} --evidence '<artifact url + version>'",
        f"If the Artifact tool is not available in this session: python3 daily/pipeline.py mark review_center --date {date} --evidence 'skipped: <reason>'"])


def git(*args, check=True):
    return sh(["git", *args], cwd=REPO, check=check)


def s_publish(run, date, phase="evening", step="publish"):
    c_out = run.get("out", date)
    git("add", "daily", "site/public/daily", "site/build/prepare-web-release.py", "site/build/build-platform.py", check=False)
    staged = git("diff", "--cached", "--name-only").stdout.split()
    if staged:
        git("-c", "user.name=Claude", "-c", "user.email=noreply@anthropic.com", "commit", "-m",
            f"Daily pack {date}: {c_out} ({phase})\n\nGenerated and checked by daily/pipeline.py; run record in daily/runs/{date}.json.\n\n"
            "Co-Authored-By: Claude <noreply@anthropic.com>")
    head = git("rev-parse", "HEAD").stdout.strip()
    branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    try:
        git("fetch", "origin", "main")
        git("rebase", "origin/main")
        head = git("rev-parse", "HEAD").stdout.strip()
        git("push", "origin", f"HEAD:main")
        remote = git("ls-remote", "origin", "refs/heads/main").stdout.split()[0]
        if remote != head:
            raise RuntimeError(f"remote main {remote} != local {head}")
    except Exception as e:  # keep the commit locally; report precisely
        git("rebase", "--abort", check=False)          # never leave the clone mid-rebase
        head = git("rev-parse", "HEAD").stdout.strip()
        bundle = STAGING / "backup" / "dpt-study-unpushed.bundle"
        bundle.parent.mkdir(parents=True, exist_ok=True)
        base = "origin/main" if git("rev-parse", "--verify", "-q", "origin/main", check=False).returncode == 0 else None
        b = git("bundle", "create", str(bundle), f"{base}..HEAD" if base else "HEAD", check=False)
        set_step(run, phase, step, "blocked", error=str(e)[-800:], commit=head, branch=branch,
                 bundle=str(bundle) if b.returncode == 0 else None)
        return need(24, "GitHub push blocked", [
            f"Local commit {head[:10]} is kept. Error: {str(e)[-400:]}",
            f"Backup: device_commit_files stagedPath={bundle} → devicePath=~/Documents/DPT-每日简报/系统/待推送/dpt-study-unpushed.bundle "
            "(force=true). A later session restores it with: git fetch <bundle> HEAD && git merge --ff-only FETCH_HEAD.",
            "Report this in the final message; do not force-push. If credentials are missing, run the evening phase in the Claude Code routine that has guiguisqwd/dpt-study attached "
            "(this session cannot push)."])
    set_step(run, phase, step, "done", evidence={"commit": head, "pushed_to": "origin/main",
                                               "site": f"{paths.SITE_BASE}daily/{date}/index.html"})
    return 0


# ------------------------------------------------------------------ morning steps
def s_locate(run, date):
    ev = load_run(date)["phases"].get("evening", {}).get("steps", {})
    out = None
    for p in (paths.build_dir(date)).glob("*.html"):
        out = p
    ok = out and ev.get("qa", {}).get("status") == "done" and ev.get("visual_review", {}).get("status") == "done"
    if not ok:
        set_step(run, "morning", "locate", "failed", error="pack missing or not checked (evening phase incomplete)")
        return need(30, "the pack for today is missing", [
            f"Run the evening phase for {date} now: python3 daily/pipeline.py evening --date {date}",
            "and finish all its steps, then run the morning phase again."])
    # copy to the outputs folder so SendUserFile can deliver it
    dst = STAGING / date / "deliver"
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copy2(out, dst / out.name)
    set_step(run, "morning", "locate", "done", evidence={"file": str(dst / out.name)})
    return 0


def s_deliver(run, date):
    rec = step_rec(run, "morning", "deliver")
    if rec.get("status") == "done":
        return 0
    f = step_rec(run, "morning", "locate").get("evidence", {}).get("file")
    set_step(run, "morning", "deliver", "waiting")
    return need(13, "send today's pack to the user", [
        f"SendUserFile files=[\"{f}\"] status=proactive display=render, caption: today's topics.",
        f"Then: python3 daily/pipeline.py mark deliver --date {date} --evidence '<file_uuid from SendUserFile>'"])


def s_record(run, date):
    return s_publish(run, date, phase="morning", step="record")


FUN = {"plan": s_plan, "author": s_author, "figures": s_figures, "validate": s_validate, "build": s_build, "qa": s_qa,
       "visual_review": s_visual_review, "site": s_site, "cards": s_cards, "archive": s_archive, "review_center": s_review_center,
       "publish": s_publish, "locate": s_locate, "deliver": s_deliver, "record": s_record}


def run_phase(phase, date):
    run = load_run(date)
    ph = run["phases"].setdefault(phase, {"steps": {}})
    ph.setdefault("started", now())
    fp = fingerprint(date)
    if phase == "evening" and ph.get("fingerprint") and ph["fingerprint"] != fp:
        # content / figures / engine changed → everything after authoring must run again
        for name, kind, _ in EVENING[2:]:
            if name in ph["steps"] and ph["steps"][name].get("status") == "done":
                ph["steps"][name]["status"] = "stale"
        say(f"content or engine changed since the last run ({ph['fingerprint']} → {fp}); later steps will run again")
    ph["fingerprint"] = fp
    save_run(run)
    ran = False
    for name, kind, code in PHASES[phase]:
        rec = step_rec(run, phase, name)
        if rec.get("status") == "done":
            continue
        ran = True
        say(f"→ {phase}/{name}")
        try:
            rc = FUN[name](run, date)
        except Exception as e:
            set_step(run, phase, name, "failed", error=f"{type(e).__name__}: {e}")
            traceback.print_exc()
            return need(code, f"step {name} failed", [f"{type(e).__name__}: {str(e)[:1500]}"])
        if rc:
            return rc
        if phase == "evening" and name == "author":
            fp = fingerprint(date); ph["fingerprint"] = fp; save_run(run)
    if not ran and ph.get("finished"):  # everything was already done: leave the committed run record as it is
        return verify(date, phase, save=False)
    ph["finished"] = now()
    save_run(run)
    return verify(date, phase)


def push_run_record(date):
    """s_publish commits the pack before its own step, the phase's finish and the verify result are written to
    the run record. Commit and push that record too, so the pushed record passes `verify` and the clone stays clean."""
    files = [run_path(date).relative_to(REPO).as_posix(), (RUNS / "log.jsonl").relative_to(REPO).as_posix()]
    dirty = bool(git("status", "--porcelain", "--", *files).stdout.strip())
    ahead = git("rev-list", "--count", "origin/main..HEAD", check=False).stdout.strip() not in ("", "0")
    if not dirty and not ahead:
        return 0
    if dirty:
        git("add", "--", *files)
        git("-c", "user.name=Claude", "-c", "user.email=noreply@anthropic.com", "commit", "-m",
            f"Daily pack {date}: record the publish step in the run log\n\nCo-Authored-By: Claude <noreply@anthropic.com>")
    try:  # also retries a run-record commit an earlier run could not push
        git("fetch", "origin", "main")
        git("rebase", "origin/main")
        git("push", "origin", "HEAD:main")
    except Exception as e:  # the pack itself is already pushed; this commit goes out with the next publish
        git("rebase", "--abort", check=False)
        say(f"note: the run-record commit for {date} is kept locally (push failed: {str(e)[-300:]}). "
            "The pack itself is pushed; the next publish pushes this commit too. Mention it in the report.")
    return 0


def verify(date, phase, save=True):
    run = load_run(date)
    steps = run["phases"].get(phase, {}).get("steps", {})
    missing = []
    for name, kind, _ in PHASES[phase]:
        r = steps.get(name, {})
        if r.get("status") == "done":
            ev = r.get("evidence")
            if ev in (None, "", {}, []):
                missing.append(f"{name}: done but no evidence")
            continue
        missing.append(f"{name}: {r.get('status', 'pending')}" + (f" — {r['error']}" if r.get("error") else ""))
    say(f"\nVERIFY {phase} {date}: " + ("ALL STEPS DONE" if not missing else f"{len(missing)} step(s) not done"))
    for m in missing:
        say("  ✗ " + str(m)[:600])
    old = run["phases"].get(phase, {}).get("verified") or {}
    if save and (old.get("ok") != (not missing) or old.get("missing") != missing):  # rewrite only when the result changes
        run["phases"].setdefault(phase, {})["verified"] = {"at": now(), "ok": not missing, "missing": missing}
        save_run(run)
    return 0 if not missing else 1


def mark(date, step, evidence=None, failed=None):
    run = load_run(date)
    phase = next(p for p, steps in PHASES.items() if step in [s[0] for s in steps])
    if failed:
        set_step(run, phase, step, "failed", error=failed)
        return 0
    if evidence is None:
        say("--evidence is required"); return 2
    if isinstance(evidence, str) and evidence.startswith("@"):
        evidence = json.loads(Path(evidence[1:]).read_text(encoding="utf-8"))
    if step == "archive":
        man = json.loads((STAGING / date / "manifest.json").read_text(encoding="utf-8"))
        written = set(evidence.get("written", [])) if isinstance(evidence, dict) else set()
        rejected = evidence.get("rejected", []) if isinstance(evidence, dict) else []
        want = {f["devicePath"] for f in man["files"]}
        if rejected or want - written:
            set_step(run, phase, step, "failed", error={"not_written": sorted(want - written)[:20], "rejected": rejected[:10]})
            say("archive incomplete: " + json.dumps({"not_written": sorted(want - written)[:20], "rejected": rejected[:5]}, ensure_ascii=False))
            return 12
        set_step(run, phase, step, "done", evidence={"written": len(written)}, fingerprint=fingerprint(date))
        return 0
    if step in SKIPPABLE and isinstance(evidence, str) and evidence.startswith("skipped:"):
        set_step(run, phase, step, "done", evidence=evidence)
        return 0
    if step == "deliver" and not (isinstance(evidence, str) and len(evidence) >= 8):
        say("deliver evidence must be the file_uuid returned by SendUserFile"); return 13
    set_step(run, phase, step, "done", evidence=evidence)
    return 0


def status(date):
    run = load_run(date)
    say(f"{date} · kind={run.get('kind')} · out={run.get('out')}")
    for phase, steps in PHASES.items():
        st = run["phases"].get(phase, {}).get("steps", {})
        say(f"  [{phase}]")
        for name, kind, _ in steps:
            r = st.get(name, {})
            say(f"    {r.get('status', 'pending'):8s} {name:14s} {kind:6s} {str(r.get('evidence', r.get('error', '')))[:90]}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["evening", "morning", "mark", "status", "verify", "brief"])
    ap.add_argument("step", nargs="?")
    ap.add_argument("--date")
    ap.add_argument("--phase", choices=["evening", "morning"])
    ap.add_argument("--evidence")
    ap.add_argument("--failed")
    a = ap.parse_args()
    if a.cmd == "evening":
        date = a.date or plan.tomorrow(tz=TZ)
        rc = run_phase("evening", date)
        if rc == 0 and step_rec(load_run(date), "evening", "publish").get("status") == "done":
            push_run_record(date)
        sys.exit(rc)
    if a.cmd == "morning":
        date = a.date or plan.today(TZ).isoformat()
        sys.exit(run_phase("morning", date))
    if not a.date:
        ap.error("--date is required")
    if a.cmd == "mark":
        sys.exit(mark(a.date, a.step, a.evidence, a.failed))
    if a.cmd == "status":
        sys.exit(status(a.date))
    if a.cmd == "verify":
        sys.exit(verify(a.date, a.phase or "evening"))
    if a.cmd == "brief":
        say(str(write_brief(a.date))); sys.exit(0)


if __name__ == "__main__":
    main()
