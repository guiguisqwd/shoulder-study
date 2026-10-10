# Hip 3D · 髋关节三维部分

按 `standards/library/steps.md` 的 ST-7，每一章都有自己的 3D 部分。

现状（2026-10-10）：

- 网页借用肩部章节的 3D 程序（`library/shoulder/3d/`，`?topic=hip&term=femur`）。结构映射写在 `../topic.json` 的 `viewer` 里：髋骨、股骨、骶骨和自带模型里已有的 10 块臀部肌肉。
- 自带模型缺的 12 块肌肉（腰大肌、髂肌、缝匠肌、股直肌、耻骨肌、长收肌、短收肌、大收肌、股薄肌、股二头肌长头和短头、半腱肌、半膜肌）由共用导出脚本生成附加模型。gui 2026-10-09 同意补（AN-43）。清单是本目录的 `atlas-addon.json`，产物在 `library/shoulder/3d/public/models/` 的 `z-anatomy-1.4.0-hip-addon.glb`、`hip-addon.metadata.json`、`hip-addon.provenance.json`。
- 重新导出：见 `site/build/atlas/README.md`，命令是 `python3 site/build/atlas/build-addon.py hip --blender-python <能 import bpy 的 Python>`，检查是 `python3 site/build/atlas/check-addon.py hip`。
- 3D 程序按 `topics.json` 的 `viewer.addons` 载入附加模型（构建时只要本目录有 `atlas-addon.json` 就自动加上）。12 块肌肉已经接进 `topic.json` 的 `viewer.terms`。股二头肌在模型里是长头、短头两块，所以分成两个词条（`biceps-femoris-long-head`、`biceps-femoris-short-head`），正文里“long head / short head”的链接打开对应的头。
