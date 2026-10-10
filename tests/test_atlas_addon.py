"""ST-7 / AN-42: shipped 3D add-on models match their metadata, the base frame and their position checks."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'site/build/atlas'))
import atlaslib  # noqa: E402

CHAPTERS = sorted(p.parent.parent.name for p in (ROOT / 'library').glob('*/3d/atlas-addon.json'))


class AtlasAddonTests(unittest.TestCase):
    def test_vendored_exporter_is_unchanged(self):
        exporter = atlaslib.SOURCE['exporter']
        digest = hashlib.sha256((atlaslib.ROOT / exporter['file']).read_bytes()).hexdigest()
        self.assertEqual(digest, exporter['sha256'])

    def test_every_chapter_addon_passes_its_checks(self):
        self.assertIn('shoulder', CHAPTERS)
        for chapter in CHAPTERS:
            with self.subTest(chapter=chapter):
                self.assertEqual(atlaslib.check_addon(chapter), [])

    def test_provenance_matches_the_shipped_glb(self):
        for chapter in CHAPTERS:
            _, config = atlaslib.chapter_config(chapter)
            paths = atlaslib.output_paths(chapter, config)
            provenance = json.loads(paths['provenance'].read_text(encoding='utf-8'))
            data = paths['glb'].read_bytes()
            with self.subTest(chapter=chapter):
                self.assertEqual(provenance['glbSha256'], hashlib.sha256(data).hexdigest())
                self.assertEqual(provenance['glbBytes'], len(data))


if __name__ == '__main__':
    unittest.main()
