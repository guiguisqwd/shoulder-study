# Atlas asset licensing

The MIT License in `LICENSE` applies to Vanatome viewer software and repository
documentation authored for Vanatome. It does not relicense third-party or
adapted anatomy assets.

The `.glb` atlas files and associated manifest under `public/models/` are
browser-oriented adaptations of material from:

- **Z-Anatomy — The libre 3D atlas of anatomy**
- Primary creators credited by the project: Gauthier Kervyn (design, 3D,
  anatomy) and Marcin Zielinski (Python script)
- Additional contributors and upstream sources are documented by Z-Anatomy
- Source: <https://github.com/Z-Anatomy/Models-of-human-anatomy>
- License: [Creative Commons Attribution-ShareAlike 4.0 International][cc]

Z-Anatomy also documents material derived from BodyParts3D, which has its own
attribution and source history. See
<https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html> and the
Z-Anatomy repository for those notices.

Vanatome’s adaptations include web export, structure selection identifiers,
material adjustments, curve-to-mesh conversion, and geometry optimization.
When redistributing the adapted atlas material, preserve the relevant
attribution, identify modifications, include a link to the license, and follow
the applicable ShareAlike terms. This summary is provided to make provenance
visible; the linked license and upstream notices are authoritative.

## Shoulder add-on model

Added by this project on 2026-10-09:
`public/models/z-anatomy-1.4.0-shoulder-addon.glb`,
`public/models/shoulder-addon.metadata.json` and
`public/models/shoulder-addon.provenance.json`.

- **Adapted from:** Z-Anatomy — The libre 3D atlas of anatomy,
  [Creative Commons Attribution-ShareAlike 4.0 International][cc], whose models
  are derived from BodyParts3D — The Database Center for Life Science (CC BY-SA
  2.1 Japan).
- **Source file:** `Startup.blend` inside `Z-Anatomy.zip` at commit
  `bb293be456f6d2245191f37752d14ec76894740d` of
  <https://github.com/Z-Anatomy/Models-of-human-anatomy> (zip SHA-256
  `e029688545627bd0214b269e1063143abb580aad72b2c2445d6d8a9a0d9da736`, blend
  SHA-256 `9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd`).
- **Exported with:** the Vanatome exporter
  `tools/anatomy/blender/export_batch.py` (MIT, Vanatome contributors; commit
  `8185b3fa46a1dbefdd907390918c57954fd9b816`), run unchanged by
  `site/build/atlas/` in the dpt-study repository.
- **Changes made:**
  - selection: 42 muscle meshes, the 14 shoulder-region muscles of both sides;
    no other Z-Anatomy model is included;
  - web export to GLB with structure identifiers, in the same coordinate frame
    as the bundled models;
  - materials: the source materials are replaced by one plain material per
    muscle group (base colour and roughness set in
    `library/shoulder/3d/atlas-addon.json`); UV maps removed;
  - decimation: meshes with more than 2,500 polygons are decimated to a ratio
    of 0.7;
  - renamed parts: the Z-Anatomy names “Ascending part of trapezius muscle”
    and “Descending part of trapezius muscle” are swapped before export so that
    the names follow Terminologia Anatomica; the provenance file keeps the
    original names.
- **License of the add-on:** CC BY-SA 4.0, the same license as its source.
  Keep this attribution and the list of changes when redistributing it.

[cc]: https://creativecommons.org/licenses/by-sa/4.0/
