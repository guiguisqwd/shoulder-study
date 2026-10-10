"""Weekly plan (standards/daily/README.md DL-10 to DL-15): plan lookup, the v2 pack checks and the form blocks."""
import copy, json, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "daily"))
from engine import codes, plan, render, schema, week_pack  # noqa: E402

T = ["This is artificial test prose for renderer verification only.", "这是仅用于渲染核验的测试文字。"]


def chapter(num, cid, content, items, forms, blocks, **extra):
    return {"num": num, "id": cid, "content": content, "items": items, "forms": forms,
            "title": ["Test chapter", "测试章节"], "toc": ["Test", "测试"], "goals": [T],
            "terms": [["Supraspinatus", "冈上肌"]], "blocks": blocks, "bridge": ["next", "Next. 下一章。", "Next"], **extra}


def fixture():
    """Every form once, with artificial text; plan checks are off because it is not a real plan day."""
    blocks = {"F-1": {"t": "p", "en": T[0], "zh": T[1]},
              "F-2": {"t": "flow", "steps": [{"title": ["Test step", "测试步骤"], "text": T}]},
              "F-3": {"t": "case", "title": ["Test case", "测试案例"], "soap": {k: T for k in "SOAP"}},
              "F-4": {"t": "dialogue", "lines": [["PT", T[0], T[1]]]},
              "F-5": {"t": "paper", "id": "hando-2026-dry-needling"},
              "F-6": {"t": "quiz", "items": [[T[0], T[1], T[0], T[1]]]},
              "F-7": {"t": "flashcards", "extra": [[T[0], T[1], T[0], T[1]]]},
              "F-8": {"t": "listen", "words": [["Supraspinatus", "冈上肌"]]},
              "F-9": {"t": "spell", "words": [["Supraspinatus", "冈上肌"]]},
              "F-10": {"t": "due_cards"},
              "F-11": {"t": "notes", "id": "test-notes", "prompt": T, "answer": T},
              "F-12": {"t": "oral", "prompt": T, "answer": T}}
    forms = list(blocks)
    chs = [chapter(k + 1, f"c{k + 1}", "O-1" if k % 2 else "N-2", ["Test item"], [f], [blocks[f]]) for k, f in enumerate(forms)]
    chs[-1].pop("bridge")
    return {"schema": "dpt-daily-pack/2", "date": "2026-10-12", "kind": "supplement", "week": 1, "chapter": "shoulder",
            "chapter_name": "肩袖 Rotator cuff", "slug_zh": "测试", "title": {"zh": "测试", "en": "Test"}, "description": "测试",
            "today_line": "测试", "tags": {"vertical": ["解剖学"], "horizontal": ["测试"]}, "figures": {},
            "sources": [["https://example.invalid/test", "Synthetic test reference"]], "chapters": chs}


class WeeklyPlan(unittest.TestCase):
    def test_days_of_the_first_weeks(self):
        self.assertEqual(plan.day_info("2026-10-08")["kind"], "learning")  # before the weekly plan: the 60-day schedule
        self.assertEqual(plan.day_info("2026-10-11")["kind"], "chapter_day")
        mon = plan.day_info("2026-10-12")
        self.assertEqual((mon["kind"], mon["week"], mon["chapter"]), ("supplement", 1, "shoulder"))
        self.assertEqual([e["type"] for e in mon["entries"]], ["N-1", "O-1"])
        self.assertEqual(plan.day_info("2026-10-19")["kind"], "unplanned")  # hip week: items come after its ST-1 list

    def test_every_planned_code_and_form_is_in_the_standard(self):
        names = codes.table()
        self.assertTrue(set(codes.FORM_BLOCKS) <= set(names))
        for w in plan.weeks()["weeks"]:
            if isinstance(w.get("days"), dict):
                for d, day in w["days"].items():
                    for e in day.get("new", []) + day.get("consolidate", []):
                        self.assertIn(e["type"], names, d)
                        for f in e["forms"]:
                            self.assertIn(f, codes.FORM_BLOCKS, d)

    def test_chapter_day_is_generated_and_valid(self):
        c = week_pack.chapter_day("2026-10-11", plan.day_info("2026-10-11"))
        self.assertEqual(schema.validate(c, check_figures=False), [])
        self.assertIn("Dry Needling Plus Manual Therapy", json.dumps(c))


class WeeklyPack(unittest.TestCase):
    def test_fixture_with_every_form_is_valid_and_renders(self):
        c = fixture()
        self.assertEqual(schema.validate(c, check_plan=False, check_figures=False), [])
        with tempfile.TemporaryDirectory() as tmp:
            render.render_sections(c, {}, tmp, due=[{"title": "冈上肌", "sub": "Supraspinatus", "ask": "起点？", "learned": "2026-10-07",
                                                     "fields": [["起点", "冈上窝"]]}])
            page = "".join(p.read_text(encoding="utf-8") for p in sorted(Path(tmp).glob("*.html")))
        for marker in ["flow-steps", "case-card", "dialogue-line", "paper-card", "checkpoint-q", "deck-data", "listen-item",
                       'data-answer="Supraspinatus"', "spell-check", "typed-notes", "checkpoint oral", "间隔复习"]:
            self.assertIn(marker, page)

    def test_a_form_without_its_block_is_reported(self):
        c = fixture()
        c["chapters"][1]["blocks"] = [{"t": "p", "en": T[0], "zh": T[1]}]  # F-2 flow chart missing
        self.assertTrue(any("form F-2" in e for e in schema.validate(c, check_plan=False, check_figures=False)))

    def test_plan_mismatch_and_missing_meridian_are_reported(self):
        c = fixture()
        errs = " | ".join(schema.validate(c, check_figures=False))
        self.assertIn("!= plan", errs)
        c = fixture()
        c["acupoints"] = [{"name": "肩外俞", "pinyin": "Jiānwàishū", "code": "SI14", "loc": "测", "loc_short": "test", "layers": "皮肤 → 深层",
                           "safety": "测", "muscles": "测", "find": "测"}]
        self.assertIn("missing meridian", " | ".join(schema.validate(c, check_plan=False, check_figures=False)))

    def test_unknown_chapter_and_paper_are_reported(self):
        c = copy.deepcopy(fixture())
        c["chapter"] = "no-such-chapter"
        c["chapters"][4]["blocks"][0]["id"] = "no-such-paper"
        errs = " | ".join(schema.validate(c, check_plan=False, check_figures=False))
        self.assertIn("not a library chapter", errs)
        self.assertIn("no daily/papers/no-such-paper.json", errs)




class LibraryFigureReuse(unittest.TestCase):
    def test_copy_strips_displacement_filter(self):
        import xml.etree.ElementTree as ET
        from engine.figlib import copy_library_figure
        name = "01-右肩的后面观与前面观"
        self.assertIn("feDisplacementMap", (ROOT / "library" / "shoulder" / "figures" / (name + ".svg")).read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as d:
            svg = copy_library_figure("shoulder", name, d, "04-test").read_text(encoding="utf-8")
        self.assertNotIn("feDisplacementMap", svg)
        self.assertNotIn('filter="url(', svg)
        ET.fromstring(svg)


if __name__ == "__main__":
    unittest.main()
