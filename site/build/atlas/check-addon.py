#!/usr/bin/env python3
"""Check a chapter's 3D add-on: metadata matches the GLB, ids don't clash with the
base model, sides and mirror twins agree, and the AN-42 position checks in
library/<chapter>/3d/atlas-addon.json pass. Pure Python; runs in CI.

    python3 site/build/atlas/check-addon.py shoulder
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atlaslib  # noqa: E402

chapters = sys.argv[1:] or [p.parent.parent.name for p in sorted((atlaslib.ROOT / 'library').glob('*/3d/atlas-addon.json'))]
failed = False
for chapter in chapters:
    problems = atlaslib.check_addon(chapter)
    for problem in problems:
        print(f'{chapter}: FAIL {problem}')
    print(f'{chapter}: {"ok" if not problems else f"{len(problems)} problem(s)"}')
    failed |= bool(problems)
sys.exit(1 if failed else 0)
