"""Regression tests for new-topic isolation and honest publication, not medical facts."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'site/build/platform'))
from topiclib import QA_CHECKS, build, catalog_models, html_order_problems, pair, skeleton, validate, write_json


class TopicTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.models = catalog_models()

    def tearDown(self): self.temp.cleanup()

    def draft(self, tid='test-topic'):
        manifest, content = skeleton(tid, 'Test topic', '测试主题')
        path = self.base / 'topics' / tid
        path.mkdir(parents=True)
        return manifest, content, path

    def completed_fixture(self):
        """Artificial prose kept inside a temporary directory; never a real medical lesson."""
        m, c, path = self.draft()
        m['status'] = 'published'
        m['viewer'] = {'enabled': True, 'defaultTerm': 'humerus', 'terms': [
            {'id': 'humerus', 'name': pair('Humerus', '肱骨'), 'kind': 'bone', 'structures': {
                'right': 'appendicular-skeleton-humerus-right', 'left': 'appendicular-skeleton-humerus-left'}},
            {'id': 'supraspinatus', 'name': pair('Supraspinatus', '冈上肌'), 'kind': 'muscle', 'structures': {
                'right': 'rotator-cuff-muscles-supraspinatus-muscle-right', 'left': 'rotator-cuff-muscles-supraspinatus-muscle-left'}}]}
        artificial = pair('This is artificial test prose for renderer verification only.', '这是仅用于渲染核验的测试文字。')
        for section in c['sections']:
            section['overview'] = artificial
            section['diagramIds'] = ['test-diagram']
            section['blocks'] = [{'heading': pair('Test heading', '测试标题'), 'body': artificial, 'termIds': ['humerus']}]
        c['sources'] = [{'id': 'test-source', 'title': 'Synthetic test reference', 'url': 'https://example.invalid/test'}]
        c['muscles'] = [{'id': 'supraspinatus', 'name': pair('Supraspinatus', '冈上肌'),
                         **{k: artificial for k in ['origin', 'insertion', 'actions', 'innervation']},
                         'course': pair('The test muscle originates from the artificial test origin and inserts onto the artificial test insertion.', '测试肌肉从虚构测试起点起始，止于虚构测试止点。'),
                         'modelTermId': 'supraspinatus', 'modelUnavailableReason': None,
                         'diagramIds': ['test-diagram'], 'sources': ['test-source']}]
        c['landmarks'] = [{'id': 'test-landmark', 'name': pair('Test landmark', '测试标志'), 'description': artificial,
                           'modelTermId': 'humerus', 'viewerLandmarkId': None,
                           'modelUnavailableReason': pair('Exact landmark position is not mapped in this test.', '本测试未标注该标志的准确位置。'),
                           'diagramIds': ['test-diagram'], 'sources': ['test-source']}]
        c['diagrams'] = [{'id': 'test-diagram', 'file': 'figures/test.svg', 'alt': artificial, 'caption': artificial,
                          'labels': [{'kind': 'origin', 'muscleId': 'supraspinatus', 'text': pair('Origin: test site', '起点：测试部位')},
                                     {'kind': 'insertion', 'muscleId': 'supraspinatus', 'text': pair('Insertion: test site', '止点：测试部位')}],
                          'sources': ['test-source']}]
        (path / 'figures').mkdir()
        (path / 'figures/test.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"><text>Origin: test site 起点：测试部位</text><text>Insertion: test site 止点：测试部位</text></svg>')
        c['review'] = [{'id': 'test-question', 'question': pair('What is the test question?', '测试问题是什么？'),
                        'answer': pair('This complete English answer contains enough words to verify that a full explanation survives rendering before its Chinese translation.', '这是一段完整测试答案，用于检查中文位于英文之后。'),
                        'mnemonic': pair('Test mnemonic', '测试简记'), 'sources': ['test-source']}]
        m['structures'] = [{'id': 'supraspinatus', 'kind': 'muscle', 'name': pair('Supraspinatus', '冈上肌'),
                            'chapters': ['anatomy'], 'modelTermId': 'supraspinatus'}]
        write_json(path / 'pronunciation.json', {'terms': {'Supraspinatus': [
            '/ˌsuprəspaɪˈneɪtəs/', 'soo-pruh-spy-NAY-tus', 'https://www.merriam-webster.com/medical/supraspinatus']}})
        c['qa'] = {'reviewedBy': 'Test fixture only', 'reviewedOn': '2026-10-06', 'checks': {key: True for key in QA_CHECKS}}
        return m, c, path

    def write_topic(self, m, c, path):
        write_json(path / 'topic.json', m); write_json(path / 'content.json', c)

    def test_two_independent_topics_scaffold_without_core_changes(self):
        topics = self.base / 'topics'
        core_before = (ROOT / 'site/build/platform/topiclib.py').read_bytes()
        for tid in ['knee-test', 'elbow-test']:
            result = subprocess.run([sys.executable, str(ROOT / 'site/build/new-topic.py'), '--id', tid, '--en', tid,
                                     '--zh', '测试主题', '--topics-dir', str(topics)], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr.decode())
        catalog = build(topics, self.base / 'public')
        self.assertEqual({t['id'] for t in catalog}, {'knee-test', 'elbow-test'})
        self.assertTrue(all(t['status'] == 'draft' for t in catalog))
        self.assertEqual((ROOT / 'site/build/platform/topiclib.py').read_bytes(), core_before)
        for topic in catalog:
            self.assertTrue((self.base / 'public/topics' / topic['id'] / 'index.html').exists())

    def test_new_topic_refuses_overwrite_and_path_traversal(self):
        topics = self.base / 'topics'
        command = [sys.executable, str(ROOT / 'site/build/new-topic.py'), '--en', 'Test', '--zh', '测试', '--topics-dir', str(topics)]
        self.assertEqual(subprocess.run(command + ['--id', 'knee'], capture_output=True).returncode, 0)
        existing = (topics / 'knee/topic.json').read_bytes()
        self.assertNotEqual(subprocess.run(command + ['--id', 'knee'], capture_output=True).returncode, 0)
        self.assertEqual((topics / 'knee/topic.json').read_bytes(), existing)
        for invalid in ['../escape', '/tmp/escape', 'Hip', 'hip/other', 'hip--other']:
            self.assertNotEqual(subprocess.run(command + ['--id', invalid], capture_output=True).returncode, 0)
        self.assertFalse((self.base / 'escape').exists())

    def test_draft_has_no_fake_course_or_reading_link(self):
        m, c, path = self.draft(); self.write_topic(m, c, path)
        catalog = build(path.parent, self.base / 'public')
        self.assertNotIn('reading', catalog[0]['links'])
        data = json.loads((self.base / 'public/topics/test-topic/data.json').read_text())
        self.assertIsNone(data['content'])
        text = (self.base / 'public/topics/test-topic/reading.html').read_text()
        self.assertIn('Draft', text); self.assertIn('草稿', text)
        self.assertNotIn('class="muscle"', text)
        self.assertLess(text.index('Test topic'), text.index('测试主题'))

    def test_published_empty_topic_rejected_and_existing_output_preserved(self):
        m, c, path = self.draft(); m['status'] = 'published'; self.write_topic(m, c, path)
        output = self.base / 'public'; (output / 'topics').mkdir(parents=True)
        sentinel = output / 'topics/keep'; sentinel.write_text('existing build')
        with self.assertRaises(ValueError): build(path.parent, output)
        self.assertEqual(sentinel.read_text(), 'existing build')

    def test_invalid_root_and_nested_shapes_report_errors_without_tracebacks(self):
        m, c, path = self.draft()
        self.assertTrue(validate([], c, path, self.models)[0])
        malformed = copy.deepcopy(c); malformed['sections'][0]['blocks'] = [None]
        self.assertTrue(validate(m, malformed, path, self.models)[0])
        write_json(path / 'topic.json', [])
        result = subprocess.run([sys.executable, str(ROOT / 'site/build/validate-topics.py'), '--topics-dir', str(path.parent)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('must contain an object', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_complete_topic_generates_bilingual_answers_and_exact_links(self):
        m, c, path = self.completed_fixture()
        errors, missing = validate(m, c, path, self.models)
        self.assertEqual(errors, []); self.assertEqual(missing, [])
        self.write_topic(m, c, path); build(path.parent, self.base / 'public')
        destination = self.base / 'public/topics/test-topic'
        text = (destination / 'reading.html').read_text()
        english, chinese = c['review'][0]['answer']['en'], c['review'][0]['answer']['zh']
        self.assertLess(text.index(english), text.index(chinese))
        self.assertIn('topic=test-topic&amp;term=supraspinatus', text)
        self.assertTrue((destination / 'figures/test.svg').exists())
        markdown = (destination / 'reading.md').read_text()
        self.assertIn(english, markdown); self.assertIn('Test mnemonic', markdown)
        self.assertIn('lumbar', text)

    def test_typed_blocks_render_in_page_and_markdown_and_records_are_placed_once(self):
        m, c, path = self.completed_fixture()
        artificial = c['sections'][0]['overview']
        c['acupoints'] = [{'id': 'test-point', 'code': 'TP1', 'name': pair('Testpoint', '测试穴'), 'location': artificial, 'layers': None,
                           'target': artificial, 'howToFind': None, 'safety': artificial, 'modelPointId': None, 'sources': ['test-source']}]
        c['sections'][0]['blocks'] = [
            {'type': 'heading', 'level': 3, 'text': pair('Typed heading', '类型标题')},
            {'type': 'table', 'columns': [pair('Name', '名称'), pair('Level', '节段')], 'rows': [[pair('Test row', '测试行'), 'C5–C6']]},
            {'type': 'note', 'heading': pair('Test note', '测试提示'), 'items': [artificial]},
            {'type': 'steps', 'items': [{'heading': pair('First step', '第一步'), 'text': artificial}]},
            {'type': 'details', 'summary': pair('More detail', '更多细节'), 'blocks': [{'type': 'muscles', 'ids': ['supraspinatus'], 'layout': 'compact'}]},
            {'type': 'sources', 'ids': ['test-source']}]
        c['sections'][3]['blocks'].append({'type': 'mnemonic', 'text': artificial, 'original': '测试口诀'})
        errors, missing = validate(m, c, path, self.models)
        self.assertEqual(errors, []); self.assertEqual(missing, [])
        self.write_topic(m, c, path); build(path.parent, self.base / 'public')
        text = (self.base / 'public/topics/test-topic/reading.html').read_text()
        markdown = (self.base / 'public/topics/test-topic/reading.md').read_text()
        for needle in ['Typed heading', 'C5–C6', 'Test note', 'First step', 'More detail', 'Testpoint', 'TP1', '测试口诀']:
            self.assertIn(needle, text); self.assertIn(needle, markdown)
        self.assertEqual(text.count('id="muscle-supraspinatus"'), 1)  # placed by the block, not appended again
        self.assertLess(text.index('id="clinical"'), text.index('Testpoint'))  # unplaced acupoints go to chapter 04
        bad = copy.deepcopy(c); bad['sections'][0]['blocks'].append({'type': 'acupoints', 'ids': ['missing-point']})
        self.assertTrue(any('unknown acupoints record' in e for e in validate(m, bad, path, self.models)[0]))
        bad = copy.deepcopy(c); bad['sections'][0]['blocks'][1]['rows'] = [[pair('Test row', '测试行'), '中文格']]
        self.assertTrue(any(e.startswith('QC-05') for e in validate(m, bad, path, self.models)[0]))

    def test_structure_list_must_exist_be_complete_and_match_the_text(self):
        m, c, path = self.completed_fixture()
        bad = copy.deepcopy(m); bad['structures'] = []
        errors, _ = validate(bad, c, path, self.models)
        self.assertIn('ST-1 structure list is missing (topic.json structures)', errors)
        self.assertIn('supraspinatus: muscle record is not in the ST-1 structure list', errors)
        bad = copy.deepcopy(m); bad['structures'][0]['chapters'] = ['clinical']
        self.assertIn('structure supraspinatus: not mentioned in chapter clinical', validate(bad, c, path, self.models)[0])
        bad = copy.deepcopy(m); bad['structures'][0]['chapters'] = ['papers']  # CH-01: no paper section any more
        self.assertIn('structure supraspinatus: chapters must list at least one of anatomy, innervation, movement, clinical, review',
                      validate(bad, c, path, self.models)[0])
        bad = copy.deepcopy(m); bad['structures'][0]['modelTermId'] = 'guessed-id'
        self.assertIn('structure supraspinatus: modelTermId is not a real 3D id', validate(bad, c, path, self.models)[0])
        bad = copy.deepcopy(m); bad['structures'][0]['kind'] = 'organ'
        self.assertTrue(validate(bad, c, path, self.models)[0])
        draft = copy.deepcopy(m); draft['status'] = 'draft'; draft['structures'] = []
        errors, missing = validate(draft, c, path, self.models)
        self.assertEqual(errors, []); self.assertIn('ST-1 structure list is missing (topic.json structures)', missing)

    def test_chapter_has_five_sections_and_no_paper_section(self):
        m, c, path = self.completed_fixture()
        self.assertNotIn('Five sections must appear in the CH-01 order: anatomy, innervation, movement, clinical, review',
                         validate(m, c, path, self.models)[0])
        bad = copy.deepcopy(c)
        bad['sections'].append({'id': 'papers', 'title': pair('Critical reading', '论文阅读'), 'overview': pair(), 'blocks': [], 'diagramIds': []})
        self.assertIn('Five sections must appear in the CH-01 order: anatomy, innervation, movement, clinical, review',
                      validate(m, bad, path, self.models)[0])

    def test_english_must_come_first(self):
        m, c, path = self.completed_fixture()
        bad = copy.deepcopy(c); bad['sections'][0]['overview'] = pair('这是中文。', 'This is English.')
        errors, _ = validate(m, bad, path, self.models)
        self.assertTrue(any(e.startswith('QC-05 section anatomy.overview') for e in errors))
        draft = copy.deepcopy(m); draft['status'] = 'draft'
        errors, missing = validate(draft, bad, path, self.models)
        self.assertEqual(errors, []); self.assertTrue(any(e.startswith('QC-05') for e in missing))
        good = '<div><p lang="en">Origin</p><p class="translation" lang="zh-Hans">起点</p></div><dt>Origin · 起点</dt><div><b>C5 vertebra</b><span class="translation">第 5 颈椎</span></div>'
        self.assertEqual(html_order_problems(good), [])
        self.assertEqual(len(html_order_problems('<div><p class="translation" lang="zh-Hans">起点</p><p lang="en">Origin</p></div>')), 1)
        self.assertEqual(len(html_order_problems('<p lang="en">Origin 起点</p>')), 1)
        self.assertEqual(len(html_order_problems('<td>深面有 Suprascapular nerve（肩胛上神经）</td>')), 1)
        self.assertEqual(len(html_order_problems('<figcaption>红点为穴位</figcaption>')), 1)

    def test_every_key_term_needs_pronunciation(self):
        m, c, path = self.completed_fixture()
        bad = copy.deepcopy(m)
        bad['structures'].append({'id': 'jianyu', 'kind': 'acupoint', 'name': pair('Jianyu', '肩髃'), 'chapters': ['anatomy'], 'modelTermId': None})
        c['sections'][0]['blocks'][0]['body'] = pair('Jianyu lies on the test shoulder.', '肩髃位于测试肩部。')
        errors, _ = validate(bad, c, path, self.models)
        self.assertIn('QC-06 tone-marked pinyin missing for acupoint Jianyu (pronunciation.json)', errors)
        (path / 'pronunciation.json').unlink()
        errors, _ = validate(m, c, path, self.models)
        self.assertIn('QC-06 pronunciation missing for key term Supraspinatus (pronunciation.json)', errors)
        for entry in [['ˌsuprəspaɪˈneɪtəs', 'soo-pruh-spy-NAY-tus', 'https://example.invalid/x'],
                      ['/ˌsuprəspaɪˈneɪtəs/', 'soo-pruh-spy-nay-tus', 'https://example.invalid/x'],
                      ['/ˌsuprəspaɪˈneɪtəs/', 'SOO-PRUH-SPY-NAY-TUS', 'https://example.invalid/x'],
                      ['/ˌsuprəspaɪˈneɪtəs/', 'soo-pruh-spy-NAY-tus', 'not a link'], 'Supraspinatus']:
            write_json(path / 'pronunciation.json', {'terms': {'Supraspinatus': entry}})
            self.assertTrue(any(e.startswith('pronunciation Supraspinatus') for e in validate(m, c, path, self.models)[0]), entry)
        write_json(path / 'pronunciation.json', {'terms': {'Supraspinatus': ['/ˌsuprəspaɪˈneɪtəs/', 'soo-pruh-spy-NAY-tus', 'https://example.invalid/x'],
                                                           'Nerve root': ['/nɝv rut/', 'NURV ROOT', 'https://example.invalid/root']}})
        self.assertFalse([e for e in validate(m, c, path, self.models)[0] if e.startswith('pronunciation')])  # one-syllable words may be all capitals
        write_json(path / 'pronunciation.json', {'terms': {}, 'pinyin': {'Jianyu': 'Jianyu'}})
        self.assertIn('pinyin Jianyu: tone marks are required', validate(m, c, path, self.models)[0])

    def test_nonexistent_incorrect_tissue_and_wrong_anatomy_mappings_fail(self):
        m, c, path = self.completed_fixture()
        for wrong in ['not-a-model', 'skeleton-hip-bone-right', 'rotator-cuff-muscles-supraspinatus-muscle-right']:
            edited = copy.deepcopy(m); edited['viewer']['terms'][0]['structures']['right'] = wrong
            errors, _ = validate(edited, c, path, self.models)
            self.assertTrue(errors, wrong)
        edited = copy.deepcopy(m); edited['viewer']['terms'][0]['structures']['right'] = 'appendicular-skeleton-humerus-left'
        errors, _ = validate(edited, c, path, self.models)
        self.assertTrue(any('swapped' in e for e in errors))

    def test_origin_insertion_must_exist_in_actual_svg(self):
        m, c, path = self.completed_fixture()
        (path / 'figures/test.svg').write_text('<svg><text>Origin: test site 起点：测试部位</text></svg>')
        errors, _ = validate(m, c, path, self.models)
        self.assertTrue(any('absent from SVG' in error for error in errors))
        c['diagrams'][0]['labels'] = c['diagrams'][0]['labels'][:1]
        errors, _ = validate(m, c, path, self.models)
        self.assertTrue(any('label its insertion' in error for error in errors))

    def test_bony_landmark_requirement_and_false_point_links_rejected(self):
        m, c, path = self.completed_fixture(); c['landmarks'] = []
        errors, _ = validate(m, c, path, self.models)
        self.assertTrue(any('bony landmark' in error for error in errors))
        m, c, path = self.completed_fixture_at_new_path('second')
        c['landmarks'][0]['viewerLandmarkId'] = 'imaginary-point'
        errors, _ = validate(m, c, path, self.models)
        self.assertTrue(any('not reviewed' in error for error in errors))

    def completed_fixture_at_new_path(self, suffix):
        # Keep the public topic id consistent while reusing the temporary test helper.
        old_base = self.base; self.base = self.base / suffix
        result = self.completed_fixture(); self.base = old_base
        return result

    def test_reviewed_coordinates_need_finite_values_sources_and_signoff(self):
        m, c, path = self.completed_fixture()
        m['viewer']['landmarks'] = [{'id': 'test-point', 'name': pair('Point', '点'), 'structures': m['viewer']['terms'][0]['structures'],
                                    'reviewStatus': 'reviewed', 'positions': {'right': [float('nan'), 0, 0], 'left': [0, 0, 0]}}]
        errors, _ = validate(m, c, path, self.models)
        self.assertTrue(any('positions' in e for e in errors))
        m['viewer']['landmarks'][0]['positions']['right'] = [0, 0, 0]
        self.assertTrue(any('signoff' in e for e in validate(m, c, path, self.models)[0]))
        m['viewer']['landmarks'][0]['reviewStatus'] = 'pending'
        del m['viewer']['landmarks'][0]['positions']
        self.assertEqual(validate(m, c, path, self.models)[0], [])

    def test_asset_path_traversal_and_active_svg_rejected(self):
        m, c, path = self.completed_fixture()
        c['diagrams'][0]['file'] = '../outside.svg'
        self.assertTrue(validate(m, c, path, self.models)[0])
        c['diagrams'][0]['file'] = 'figures/test.svg'
        (path / 'figures/test.svg').write_text('<svg><script>alert(1)</script></svg>')
        self.assertTrue(any('Active SVG' in e for e in validate(m, c, path, self.models)[0]))

    def test_source_and_qa_omissions_cannot_publish(self):
        m, c, path = self.completed_fixture()
        c['muscles'][0]['sources'] = ['unknown']; c['qa']['checks']['layoutMobile'] = False
        errors, _ = validate(m, c, path, self.models)
        self.assertTrue(any('unknown source' in e for e in errors))
        self.assertIn('QA pending: layoutMobile', errors)

    def test_invalid_source_url_and_impossible_review_date_fail(self):
        m, c, path = self.completed_fixture()
        c['sources'][0]['url'] = 'https://['
        c['qa']['reviewedOn'] = '2026-99-99'
        errors, _ = validate(m, c, path, self.models)
        self.assertTrue(any('valid HTTPS' in e for e in errors))
        self.assertTrue(any('valid review date' in e for e in errors))

    def test_new_topic_cannot_bypass_quality_with_legacy_adapter(self):
        m, c, path = self.draft(); m['adapter'] = 'shoulder'; m['status'] = 'published'
        self.assertTrue(any('reserved' in e for e in validate(m, c, path, self.models)[0]))

    def test_missing_or_stale_pdf_is_not_advertised(self):
        m, c, path = self.completed_fixture()
        m['pdf'] = {'file': 'figures/missing.pdf', 'contentDigest': 'old', 'reviewedBy': 'Tester', 'reviewedOn': '2026-10-06'}
        errors, _ = validate(m, c, path, self.models)
        self.assertTrue(any('PDF is missing' in e for e in errors)); self.assertTrue(any('stale' in e for e in errors))

    # Chapter 3D add-ons (library/<id>/3d/atlas-addon.json): only the owning chapter's viewer loads one.
    def test_catalog_includes_chapter_addons_with_their_chapter(self):
        self.assertEqual(self.models['teres-major-muscles-teres-major-muscle-right'].get('addon'), 'shoulder')
        self.assertEqual(self.models['trapezius-muscles'].get('addon'), 'shoulder')
        self.assertIsNone(self.models['appendicular-skeleton-humerus-right'].get('addon'))
        self.assertIsNone(self.models['rotator-cuff-muscles-supraspinatus-muscle-right'].get('addon'))

    def addon_root(self, name, output=None, write_metadata=True, structures=None):
        """A temporary repository root: the real base metadata plus one fake chapter add-on ('knee')."""
        root = self.base / name
        models = root / 'library/shoulder/3d/public/models'
        models.mkdir(parents=True)
        for system in ['skeletal', 'muscular']:
            name = system + '.metadata.json'
            (models / name).write_bytes((ROOT / 'library/shoulder/3d/public/models' / name).read_bytes())
        output = output or {'glb': 'public/models/z-anatomy-1.4.0-knee-addon.glb', 'metadata': 'public/models/knee-addon.metadata.json',
                            'provenance': 'public/models/knee-addon.provenance.json'}
        write_json(root / 'library/knee/3d/atlas-addon.json', {'output': output})
        if write_metadata:
            write_json(models / 'knee-addon.metadata.json', {'structures': structures or [
                {'id': 'popliteus-muscles', 'name': 'Popliteus', 'system': 'muscular', 'layer': 'muscular', 'parentId': 'muscular-system', 'objectCount': 0},
                {'id': 'popliteus-muscles-popliteus-muscle-right', 'name': 'Popliteus muscle.r', 'system': 'muscular', 'layer': 'muscular', 'parentId': 'popliteus-muscles', 'objectCount': 1},
                {'id': 'popliteus-muscles-popliteus-muscle-left', 'name': 'Popliteus muscle.l', 'system': 'muscular', 'layer': 'muscular', 'parentId': 'popliteus-muscles', 'objectCount': 1}]})
        return root

    def test_addon_catalog_reads_any_chapter_and_rejects_bad_declarations(self):
        models = catalog_models(self.addon_root('valid'))
        self.assertEqual(models['popliteus-muscles-popliteus-muscle-right']['addon'], 'knee')
        self.assertIn('appendicular-skeleton-humerus-right', models)
        with self.assertRaisesRegex(ValueError, 'metadata is missing'): catalog_models(self.addon_root('unbuilt', write_metadata=False))
        with self.assertRaisesRegex(ValueError, 'output.metadata must be'):
            catalog_models(self.addon_root('renamed', output={'glb': 'public/models/z-anatomy-1.4.0-knee-addon.glb', 'metadata': '../../outside.json'}))
        with self.assertRaisesRegex(ValueError, 'duplicates an existing model id'):
            catalog_models(self.addon_root('duplicate', structures=[{'id': 'appendicular-skeleton-humerus-right', 'name': 'Humerus.r', 'system': 'skeletal', 'objectCount': 1}]))

    def test_viewer_terms_may_use_only_their_own_chapter_addon(self):
        m, c, path = self.completed_fixture()
        models = dict(self.models)
        for side in ['right', 'left']:
            models['popliteus-muscles-popliteus-muscle-' + side] = {'id': 'popliteus-muscles-popliteus-muscle-' + side, 'name': 'Popliteus muscle.' + side[0],
                                                                    'system': 'muscular', 'objectCount': 1, 'addon': 'test-topic'}
        own = copy.deepcopy(m)
        own['viewer']['terms'].append({'id': 'popliteus', 'name': pair('Popliteus', '腘肌'), 'kind': 'muscle', 'structures': {
            'right': 'popliteus-muscles-popliteus-muscle-right', 'left': 'popliteus-muscles-popliteus-muscle-left'}})
        self.assertFalse([e for e in validate(own, c, path, models)[0] if 'add-on' in e])
        borrowed = copy.deepcopy(m)
        borrowed['viewer']['terms'].append({'id': 'teres-major', 'name': pair('Teres major', '大圆肌'), 'kind': 'muscle', 'structures': {
            'right': 'teres-major-muscles-teres-major-muscle-right', 'left': 'teres-major-muscles-teres-major-muscle-left'}})
        errors, _ = validate(borrowed, c, path, self.models)
        self.assertIn('viewer term teres-major: teres-major-muscles-teres-major-muscle-right is in the shoulder chapter 3D add-on, which this topic does not load', errors)

    def test_topic_with_its_own_addon_lists_it_for_the_viewer(self):
        m, c, path = self.draft(); self.write_topic(m, c, path)
        other, other_content, other_path = self.draft('second-topic'); self.write_topic(other, other_content, other_path)
        write_json(path / '3d/atlas-addon.json', {'output': {}})
        catalog = {t['id']: t for t in build(path.parent, self.base / 'public')}
        self.assertEqual(catalog['test-topic']['viewer']['addons'], ['test-topic'])
        self.assertNotIn('addons', catalog['second-topic']['viewer'])
        self.assertNotIn('addons', json.loads((path / 'topic.json').read_text())['viewer'])  # derived, never written back

    def test_real_catalog_gives_each_chapter_its_own_addon(self):
        with tempfile.TemporaryDirectory() as output:
            catalog = {t['id']: t for t in build(output=Path(output))}
        self.assertEqual(catalog['shoulder']['viewer']['addons'], ['shoulder'])
        self.assertEqual(catalog['hip']['viewer']['addons'], ['hip'])


if __name__ == '__main__': unittest.main()
