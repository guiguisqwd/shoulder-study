# Daily study packs · 每日学习包流水线

Every learning day of the plan (`plan/schedule.json`, 60 days to 2026-12-23: all 362 points of the
14 meridians + the PT muscle list) gets one bilingual pack at the quality of Day 1:
six chapters (Muscles → Innervation → Movement → Acupoints → Review → English), hand-drawn
editable SVGs, pronunciation (IPA + stressed syllable + speech button) for every English key term,
acupoints read aloud in Chinese, self-checks, flashcards, and spaced-repetition cards.

`pipeline.py` runs the work as fixed, checked steps and records every run in `runs/`.

**Weekly plan (2026-10-09).** From 2026-10-11 the plan is `plan/weeks.json`: on Sunday gui studies one
library chapter, Monday–Saturday packs supplement it with new content and consolidation (content types N-x / O-x,
forms F-x in `standards/daily/README.md`). Paper records live in `papers/`. `pipeline.py` reads `weeks.json` from
its first Sunday on: Sunday packs (`chapter_day`) are generated, Monday–Saturday packs (`supplement`, schema
`dpt-daily-pack/2`, see `CONTENT_SCHEMA.md`) are authored from the brief; a date whose week has no day entries yet
stops at the plan step (exit 2) until `weeks.json` is filled. Earlier dates keep `schedule.json` and the v1 form.

This is block ② of the repository: daily learning is generated **from** the anatomy library in
`library/` (block ①). The rules for how a pack draws on the library, and the short chapter form
(CH-02), are in `standards/daily/README.md`. Published pages go to `site/public/daily/`.

## The two phases

| When (Pacific) | Phase | Steps (AUTO = the script does and checks it; CLAUDE = the session does it, then records evidence) |
| --- | --- | --- |
| 18:07 the evening before | `evening` | plan · **author** (CLAUDE: content.json + figures.py) · figures · validate · build · qa · **visual_review** (CLAUDE: look at every screenshot) · site · cards · publish (git commit + push) |
| 04:18 | `morning` | locate · **deliver** (CLAUDE: SendUserFile) · **review_center** (CLAUDE: update the artifact) · **archive** (CLAUDE: write pack, indexes and this run record to the Mac) |

The script stops at the first unfinished step, prints exactly what to do, and exits with that
step's code (10 author, 11 visual review, 12 Mac archive, 13 deliver, 14 review center, 20–23 a
check failed, 24 GitHub push blocked, 30 pack missing). After acting, record evidence with
`pipeline.py mark …` and run the phase again. `pipeline.py verify --date D --phase P` exits 0 only
when every step has status `done` with evidence. Changing `content.json`, `figures.py` or the
pack-shaping engine files marks the later steps `stale`, so they run again; the visual review is
carried over only when the page and every SVG are byte-identical to what was reviewed.

```sh
python3 daily/pipeline.py evening                 # tomorrow (Pacific)
python3 daily/pipeline.py evening --date 2026-10-08
python3 daily/pipeline.py morning                 # today (Pacific)
python3 daily/pipeline.py status --date 2026-10-08
python3 daily/pipeline.py verify --date 2026-10-08 --phase evening
python3 daily/pipeline.py mark archive --date 2026-10-08 --evidence @commit-result.json
```

Review days (Sundays, 12/16–12/23) are generated automatically from the week's packs
(`engine/review_pack.py`): no authoring step.

## Where each phase runs

| Phase | Runs in | Why |
| --- | --- | --- |
| `evening` (18:07 Pacific, for tomorrow) | Claude Code routine `DPT 每日学习包 · 前一晚生成` with `guiguisqwd/dpt-study` attached | can push to `main`, so GitHub Pages updates |
| `morning` (04:18 Pacific, for today) | Cowork scheduled task `DPT 每日学习包 · 4:30 推送`, linked to gui's Mac | can send the file to gui, update the review-center artifact and write the Mac archive |

The morning task clones the pushed repository (public, read-only), so it needs no push access.
If an evening push is ever blocked (exit 24), the pipeline writes `origin/main..HEAD` to
`dpt-study-unpushed.bundle` in the staging folder; restore it with
`git fetch <bundle> HEAD && git merge --ff-only FETCH_HEAD` in a session that can push.

## Layout

```
daily/
  pipeline.py            orchestrator (steps, evidence, verify)
  CONTENT_SCHEMA.md      content.json fields and block types
  plan/weeks.json        the weekly plan from 2026-10-11 (one chapter a week + six supplement days)
  plan/schedule.json     the old 60-day plan (dates before 2026-10-11); plan/legacy/ = 10-06 shoulder preview cards
  papers/<id>.json       paper records for N-5 (paper reading moved out of the chapters)
  engine/
    figlib/              Fig kit (fig.py) + region base art: chest.py, arm.py, … (reuse; add new regions here)
    render.py build.py   content.json → sections → <pack>.html/.md (3D ?term= links validated against library/shoulder/3d/src)
    schema.py            strict content checks (English first, O/I/N/A sentence, acupoint fields, pronunciation, tags, plan match)
    qa/qa.js             Playwright: JS errors, chapters, SVG text overlap/outside, phone width, pronunciation coverage, screenshots
    site.py              public/daily/<date>/ + public/daily/index.html + catalog.json (shipped by GitHub Pages)
    archive.py           Mac archive: pack, tagged Markdown (item-meta, vertical/horizontal), catalog.jsonl, topic indexes
    week_pack.py         Sunday chapter-day pack generated from weeks.json
    codes.py             N-/O-/F- names read from standards/daily/README.md; form → block map
    cards.py             review-center cards (intervals 1/3/7/14/30 days)
    data/                pronunciation.json (IPA, stress, dictionary URL), model-links.json (3D term IDs)
    templates/           reading shell + CSS (Day 1 design), review-center template
  days/<date>/           content.json, figures.py, build/ (pack, 资源/, sections/, qa/qa.json, qa/visual-review.json)
  runs/<date>.json       every step of every run: status, time, evidence, errors; runs/log.jsonl = append-only log
  review-center/         generated review-center page; each answer is written to the artifact's shared db
                         (answers/<page load>, progress/c<hex card id>); push-hub syncs answers into feedback/
  archive/seed-catalog.jsonl  catalog items that predate the pipeline (kept verbatim)
```

## Rules the checks enforce (from the user)

- English first, then Chinese; muscles: Origin / Insertion / Nerve (with spinal segments) / Action and
  the sentence "The X originates from …, passes …, and inserts onto …."; figures for every muscle.
- Nerve figures start from the spine (C = Cervical 颈部, T = Thoracic 胸部 …); movement is explained
  from the line of pull, with firing order and force couples where they matter.
- Every acupoint: GB/T 12346 location, layers skin → deep, safety, related muscles, how to find it,
  shown on a figure with the surrounding muscles. Layer figures are "not needling depth or direction".
- Every English key term has IPA + stressed syllable + dictionary link; acupoints have tone-marked pinyin
  and are read aloud in Chinese.
- No public-health framing. Facts come from sources that were actually opened; uncertainty is stated.
- Archive tags: `tags.vertical` uses the fixed top levels (解剖学 · 生理学 · 运动学/生物力学 · 病理学 ·
  神经科学 · 检查评估 · 康复干预 · 循证方法学 · 中医针灸对照); `tags.horizontal` uses the controlled
  vocabulary in `DPT-每日简报/README.md`.

## Where the results go

- Phone: the 04:18 scheduled task sends the HTML with a Claude notification.
- Website: `https://guiguisqwd.github.io/dpt-study/daily/` (after push + Pages deploy).
- Mac: `~/Documents/DPT-每日简报/每日学习包/<pack>/`, `daily/YYYY/MM/<date>.md`, `index/`.
- Record: `daily/runs/<date>.json` in this repository (evening steps) and `~/Documents/DPT-每日简报/系统/运行记录/<date>.json` on the Mac (all steps).
