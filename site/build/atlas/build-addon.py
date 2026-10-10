#!/usr/bin/env python3
"""Build a chapter's 3D add-on model from the pinned Z-Anatomy source (ST-7, AN-44).

    python3 site/build/atlas/build-addon.py shoulder [--blender-python PATH] [--cache DIR]

Reads library/<chapter>/3d/atlas-addon.json, downloads and hash-checks the source
once (site/build/atlas/source.json), exports the listed meshes with the vendored
Vanatome exporter, writes the GLB, its metadata and a provenance record into the
3D app's public/models/, then runs the position checks. Needs a Python where
`import bpy` works: python3.13 -m venv .venv && .venv/bin/pip install bpy==5.2.0
"""
import argparse
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atlaslib  # noqa: E402

SRC = atlaslib.SOURCE['zAnatomy']


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def source_blend(cache):
    cache.mkdir(parents=True, exist_ok=True)
    blend = cache / 'Startup.blend'
    if blend.exists() and sha256(blend) == SRC['blendSha256']:
        return blend
    archive = cache / 'Z-Anatomy.zip'
    if not archive.exists() or sha256(archive) != SRC['zipSha256']:
        print('Downloading', SRC['zipUrl'])
        with urllib.request.urlopen(SRC['zipUrl']) as response, open(archive, 'wb') as out:
            shutil.copyfileobj(response, out)
    if sha256(archive) != SRC['zipSha256']:
        sys.exit(f'{archive}: SHA-256 does not match source.json; refusing to use it')
    with zipfile.ZipFile(archive) as z, z.open(SRC['blendMember']) as member, open(blend, 'wb') as out:
        shutil.copyfileobj(member, out)
    if sha256(blend) != SRC['blendSha256']:
        sys.exit(f'{blend}: SHA-256 does not match source.json; refusing to use it')
    return blend


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('chapter')
    parser.add_argument('--blender-python', default=sys.executable, help='Python that can import bpy 5.2.0')
    parser.add_argument('--cache', type=Path, default=Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache')) / 'dpt-study/z-anatomy')
    parser.add_argument('--date', default=datetime.date.today().isoformat(), help='date written into the provenance record')
    args = parser.parse_args()

    config_path, config = atlaslib.chapter_config(args.chapter)
    paths = atlaslib.output_paths(args.chapter, config)
    exporter = atlaslib.ROOT / atlaslib.SOURCE['exporter']['file']
    if sha256(exporter) != atlaslib.SOURCE['exporter']['sha256']:
        sys.exit(f'{exporter} differs from the vendored Vanatome exporter; keep it unchanged')
    blend = source_blend(args.cache)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / 'config.json').write_text(json.dumps({'batches': {args.chapter: config['batch']}}), encoding='utf-8')
        renames = {old: new for old, new in config.get('renameSourceObjects', {}).items() if not old.startswith('_')}
        (tmp / 'renames.json').write_text(json.dumps(renames), encoding='utf-8')
        command = [args.blender_python, '-I', str(Path(__file__).with_name('run_export.py')), '--', str(blend), str(exporter), str(tmp / 'renames.json'),
                   '--config', str(tmp / 'config.json'), '--batch', args.chapter, '--output', str(tmp / 'out')]
        run = subprocess.run(command, capture_output=True, text=True)
        if run.returncode != 0 or 'VANATOME_EXPORT_COMPLETE' not in run.stdout:
            sys.stdout.write(run.stdout[-4000:]); sys.stderr.write(run.stderr[-4000:])
            sys.exit('Blender export failed')
        report = json.loads((tmp / 'out/export-report.json').read_text(encoding='utf-8'))
        metadata = atlaslib.metadata_from_report(report, args.chapter)
        paths['glb'].parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(tmp / 'out/atlas.glb', paths['glb'])
        paths['metadata'].write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    meshes = atlaslib.mesh_nodes(paths['glb'])
    original = {new: old for old, new in renames.items()}
    provenance = {
        'chapter': args.chapter,
        'built': args.date,
        'config': str(config_path.relative_to(atlaslib.ROOT)),
        'source': {k: SRC[k] for k in ('repository', 'commit', 'zipSha256', 'blendSha256', 'license')},
        'exporter': {k: atlaslib.SOURCE['exporter'][k] for k in ('upstream', 'sha256', 'license')},
        'blenderVersion': report['blenderVersion'],
        'glbSha256': sha256(paths['glb']),
        'glbBytes': paths['glb'].stat().st_size,
        'objectCount': report['objectCount'],
        'meshes': {m['anatomyId']: {'source': source, **({'zAnatomyName': original[source]} if source in original else {}),
                                    'minMetres': [round(v, 4) for v in m['min']],
                                    'maxMetres': [round(v, 4) for v in m['max']]}
                   for source, m in sorted(meshes.items(), key=lambda item: item[1]['anatomyId'])},
        'mappingNotes': config.get('mappingNotes', []),
    }
    paths['provenance'].write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    problems = atlaslib.check_addon(args.chapter)
    for problem in problems:
        print('FAIL', problem)
    print(json.dumps({'glb': str(paths['glb'].relative_to(atlaslib.ROOT)), 'bytes': provenance['glbBytes'],
                      'meshes': report['objectCount'], 'problems': len(problems)}))
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
