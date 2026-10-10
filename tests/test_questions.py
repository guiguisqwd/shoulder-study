"""Chapter question bank (QC-10): format, links back to content.json, and coverage of the chapter."""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'site/build/platform'))
import questions
from topiclib import catalog_models, read_json, validate, write_json


class QuestionBankTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.models = catalog_models()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'shoulder'
        shutil.copytree(ROOT / 'library/shoulder', self.path, ignore=shutil.ignore_patterns('3d', 'pdf', 'text'))
        self.manifest = read_json(self.path / 'topic.json')
        self.content = read_json(self.path / 'content.json')
        self.bank = read_json(self.path / 'questions.json')

    def tearDown(self): self.temp.cleanup()

    def errors(self, bank=None):
        if bank is not None: write_json(self.path / 'questions.json', bank)
        errs, missing = [], []
        bi = lambda value, label: None if isinstance(value, dict) and set(value) == {'en', 'zh'} and all(value.values()) else errs.append(label + ': expected {en, zh}')
        questions.check(self.manifest, self.content, self.path, errs.append, lambda ok, msg: ok or missing.append(msg), bi)
        return errs, missing

    def test_published_chapters_pass(self):
        for tid in ['shoulder', 'hip']:
            path = ROOT / 'library' / tid
            errors, _ = validate(read_json(path / 'topic.json'), read_json(path / 'content.json'), path, self.models)
            self.assertEqual([e for e in errors if 'question' in e or 'QC-10' in e], [], tid)

    def test_shoulder_bank_is_complete_and_every_question_resolves(self):
        self.assertEqual(self.errors(), ([], []))
        qs = questions.expand(self.bank, self.content)
        self.assertEqual(len(qs), len(self.bank['questions']))
        for q in qs:
            for key in ['prompt', 'answer']: self.assertTrue(q[key]['en'] and q[key]['zh'], q['id'])
            self.assertTrue(q['points'], q['id'])
        sup = next(q for q in qs if q['id'] == 'supraspinatus-oina')
        self.assertIn('Supraspinous fossa of the scapula', sup['answer']['en'])   # answers come from content.json, not a copy
        self.assertEqual(sup['from'], 'muscles/supraspinatus')
        self.assertEqual(sup['key'], 'shoulder/supraspinatus-oina')

    def test_chapter_without_bank_is_not_held_back_while_on_trial(self):
        (self.path / 'questions.json').unlink()
        self.assertEqual(self.errors(), ([], []))

    def test_format_errors_fail(self):
        cases = [
            (lambda q: q.__setitem__('type', 'essay'), 'type must be one of'),
            (lambda q: q.__setitem__('part', 'papers'), 'part must be one of'),
            (lambda q: q.__setitem__('covers', ['no-such-structure']), 'covers unknown structure'),
            (lambda q: q.__setitem__('record', 'muscles/no-such-muscle'), 'does not exist in content.json'),
            (lambda q: q.__setitem__('ask', ['colour']), 'ask must list fields'),
            (lambda q: q.__setitem__('prompt', {'en': 'x', 'zh': 'x'}), 'takes its prompt and answer from content.json'),
        ]
        for change, message in cases:
            bank = copy.deepcopy(self.bank); change(bank['questions'][0])
            self.assertTrue(any(message in e for e in self.errors(bank)[0]), message)
        bank = copy.deepcopy(self.bank); bank['questions'].append(copy.deepcopy(bank['questions'][0]))
        self.assertTrue(any('duplicate id' in e for e in self.errors(bank)[0]))
        written = next(q for q in self.bank['questions'] if 'from' in q)
        for change, message in [(lambda q: q.__setitem__('points', q['points'][:1]), 'scoring points'),
                                (lambda q: q.__setitem__('from', 'papers'), 'from must name'),
                                (lambda q: q.__setitem__('answer', 'text'), '.answer')]:
            bank = copy.deepcopy(self.bank); q = next(x for x in bank['questions'] if x['id'] == written['id']); change(q)
            self.assertTrue(any(message in e for e in self.errors(bank)[0]), message)

    def test_coverage_gaps_are_reported(self):
        bank = copy.deepcopy(self.bank)
        bank['questions'] = [q for q in bank['questions'] if q['id'] not in ('supraspinatus-oina', 'review-insertions', 'acu-si11')]
        bank['questions'] = [q for q in bank['questions'] if q['type'] not in ('reason', 'case')]
        errors, missing = self.errors(bank)
        self.assertEqual(errors, [])
        for message in ['QC-10 muscles/supraspinatus is not asked: origin, insertion, innervation, actions',
                        'QC-10 acupoints/si11 is not asked: location, layers',
                        'QC-10 review question q-insertions is not in the bank',
                        'reasoning or case questions (at least']:
            self.assertTrue(any(message in m for m in missing), message)
        self.assertTrue(any(m.startswith('QC-10 part review has') for m in missing))


if __name__ == '__main__': unittest.main()
