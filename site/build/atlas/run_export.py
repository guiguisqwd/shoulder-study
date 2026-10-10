"""Open the pinned Z-Anatomy .blend with scripts disabled, apply the chapter's object renames,
then run the vendored exporter.

Called by build-addon.py in a Python that can `import bpy` (pip install bpy==5.2.0):
    python run_export.py -- <Startup.blend> <export_batch.py> <renames.json> --config C --batch B --output DIR

renames.json maps a Z-Anatomy object name to the name the exporter should see (atlas-addon.json
"renameSourceObjects"), for source meshes whose names do not match the anatomy. Renames are applied
through temporary names, so two meshes can swap names.
"""
import json
import runpy
import sys

import bpy

argv = sys.argv[sys.argv.index('--') + 1:]
blend, exporter, renames_path, rest = argv[0], argv[1], argv[2], argv[3:]
bpy.ops.wm.open_mainfile(filepath=blend, load_ui=False, use_scripts=False)
renames = json.loads(open(renames_path, encoding='utf-8').read())
objects = {}
for old in renames:
    obj = bpy.data.objects.get(old)
    if obj is None:
        sys.exit(f'renameSourceObjects: "{old}" is not in the source file')
    objects[old] = obj
for i, obj in enumerate(objects.values()):
    obj.name = f'__dpt_rename_{i}'
for old, obj in objects.items():
    obj.name = renames[old]
    if obj.name != renames[old]:
        sys.exit(f'renameSourceObjects: "{renames[old]}" is already taken in the source file')
sys.argv = ['blender', '--'] + rest
runpy.run_path(exporter, run_name='__main__')
