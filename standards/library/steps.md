# 第 3 层 · 知识库章节制作步骤

每一步写成同样的四格。调整某一步时只改那一行；合格标准只引用规则编号，不重写规则。编号固定不改，表格按实际执行顺序排列：ST-1 → ST-2 → ST-3 → ST-10 → ST-4 → ST-7 → ST-8 → ST-5 → ST-9 → ST-6；需要附加模型时，ST-7 先做它的附加模型子步骤，再做映射。

| 步骤 | 输入 | 输出 | 合格标准 |
| --- | --- | --- | --- |
| ST-1 选题 | 学习计划或用户指定的主题 | `library/<id>/topic.json` 的 `structures` 清单：本章讲到的每块肌肉、神经、骨、骨性标志、关节和穴位各一项，写明英中名称、类型、出现在哪几章、3D ID（模型没有写 `null`）；格式见 [library/README.md](../../library/README.md) | 每个结构都放进 CH-01 的某一章；QC-08 |
| ST-2 查证 | 结构清单 | 起止点、走行、神经、动作、穴位数据；核对记录 | G-02、AN-02、AN-20、AN-50、AN-51；未核验项已列出（G-03） |
| ST-3 写作 | 主题数据 + 章节模板 | 五部分正文（单一源稿） | CH-01、AN-01 至 AN-07、G-04 |
| ST-10 出题（【试用】，在 ST-3 之后） | 五部分正文 `content.json` + 结构清单 | `library/<id>/questions.json` 题库 | AN-60 至 AN-66；QC-10 无待办 |
| ST-4 画图 | 主题数据 + 正文 | 编号 SVG | AN-10 至 AN-17、AN-21、AN-22 |
| ST-7 本章 3D（在 ST-4 之后、ST-5 之前做） | 主题数据（结构清单、3D 映射）+ 正文 | 本章 3D 部分：结构映射、骨性标志、需要时的语音和交互改动，放在 `library/<id>/3d/` | AN-40 至 AN-44；正文里的每个 `?term=` 都能在本章 3D 中打开；模型没有的结构按 AN-41 写明 |
| ST-7 子步骤：附加模型（自带模型缺本章要讲的肌肉、且用户已同意时做；在 ST-7 的结构映射之前做） | `library/<id>/3d/atlas-addon.json`：要导出的 Z-Anatomy 源网格、`renameSourceObjects`、位置检查 `checks`、`mappingNotes`；固定源文件见 `site/build/atlas/source.json` | `library/shoulder/3d/public/models/` 下的 `z-anatomy-1.4.0-<id>-addon.glb`、`<id>-addon.metadata.json`、`<id>-addon.provenance.json`；之后回到 ST-7 给新结构配名称、词条、读音和链接。命令见下方“构建与导出命令” | AN-42、AN-43、AN-44；QC-09 通过；导出后没有手改 GLB 或 metadata，要改就改清单重新导出（G-08） |
| ST-8 构建（在 ST-7 之后、ST-5 之前做） | 源文件：`topic.json`、`content.json`、`pronunciation.json`、`figures/` 的 SVG、`3d/`（肩袖相同） | 生成的页面：`library/shoulder/3d/public/topics.json`、`public/topics/<id>/` 下的 `index.html`、`reading.html`、`reading.md`、`data.json`，以及 `study.html` 首页；肩袖另把同一页写到旧地址：`text/2026-10-06-肩袖-阅读优化版.html` 与 `.md`、`3d/public/reading.html`，并写 `text/build-report.json`。命令见下方“构建与导出命令” | 校验和构建都无报错退出；QC-01 至 QC-06、QC-08 通过（草稿的待办项列进制作记录）；生成页没有手改，要改就回到源文件重建（G-08）；HTML 和 Markdown 来自同一次构建 |
| ST-5 核验 | ST-8 构建出的页面和 SVG | 截图、检查清单结果 | [checklist.md](./checklist.md) 自动项全过，人工项逐条有证据；G-07 |
| ST-9 导出 PDF（在 ST-5 之后、ST-6 之前做；本章提供 PDF 时必做） | 通过 ST-5 的阅读页（ST-8 输出）+ `figures/` 的 SVG | `library/<id>/pdf/` 下的 PDF；导出清单 `export-report.json`（页数、章节、图、表、问答数）；临时图片用完删除 | QC-27；PDF 来自当前这次构建，不是旧版；通过后才在 `topic.json` 的 `pdf` 里登记 `file`、`contentDigest`（当前正文和图的摘要，`topiclib.content_digest` 算出）、`reviewedBy`、`reviewedOn`，正文或图一改摘要就对不上，校验报 PDF 过期 |
| ST-6 定稿 | 通过核验的内容（页面、PDF） | 成品 + 制作记录（方法、来源边界、3D 映射、未核验项、构建与 PDF 导出结果） | 制作记录齐全；之后交给推送流程，本规范到此为止 |

## 文件落点

每一章一个文件夹 `library/<id>/`，四个部分名字固定：

| 部分 | 放什么 | 肩袖 `library/shoulder/` | 新章节（如 `library/hip/`） |
| --- | --- | --- | --- |
| 注册 | 状态、标题、3D 映射 | `topic.json` | `topic.json` |
| 题库（【试用】AN-60） | 本章全部题目 | `questions.json` | `questions.json` |
| `text/` | 正文源稿、数据、成稿、制作记录与核对记录 | 正文在章节根目录的 `content.json`（生成 HTML 和 Markdown，`text/build-reading.py` 写到旧地址）；`text/` 放成稿、`text/data/` 核对记录、`text/制作流程-肩袖双语学习.md` | `content.json`（生成 HTML 和 Markdown），制作记录放章节根目录 |
| `figures/` | 编号 SVG | `figures/` | `figures/` |
| `pdf/` | 离线 PDF 及其导出脚本 | `pdf/` | 有 PDF 时同样放 `pdf/` |
| `3d/` | 本章 3D 网站或 3D 数据（ST-7） | `3d/`：完整的 3D 程序、模型、语音、骨性标志；附加模型清单 `3d/atlas-addon.json`（AN-44） | `3d/`：目前只有 `topic.json` 里的模型映射，借用肩部 3D 程序预览；需要附加模型时同样放 `3d/atlas-addon.json` |

## 构建与导出命令

在仓库根目录运行。详细说明见 [library/README.md](../../library/README.md) §4。

| 步骤 | 命令 | 说明 |
| --- | --- | --- |
| ST-7（附加模型） | `python3 site/build/atlas/build-addon.py <id> --blender-python .venv-bpy/bin/python` | 下载并核对固定的 Z-Anatomy 源文件，按 `library/<id>/3d/atlas-addon.json` 导出，写 GLB、metadata、provenance，最后自动跑检查；需要 Python 3.13 和 `bpy==5.2.0`，准备方法见 [site/build/atlas/README.md](../../site/build/atlas/README.md) |
| ST-7（附加模型） | `python3 site/build/atlas/check-addon.py <id>` | 只检查、不导出（QC-09）；不带章节名查全部章节；纯 Python，CI 由 `tests/test_atlas_addon.py` 运行 |
| ST-10 | `python3 site/build/platform/questions.py library/<id>` | 题库统计（每部分、每种题型几道）；加 `--markdown` 打印每道题和答案，给用户过目。覆盖检查（QC-10）在 `validate-topics.py` 里一起跑 |
| ST-8 | `python3 site/build/validate-topics.py --topic <id>` | 校验本章；不带 `--topic` 查全部，`--require-published` 查是否够发布 |
| ST-8 | `cd library/shoulder/3d && pnpm build` | 先自动跑 `site/build/build-platform.py`（生成各章页面和 `study.html`），再打包 3D 程序；几何或空间标记有改动时另跑 `pnpm test:geometry` |
| ST-8（仅肩袖） | `python3 library/shoulder/text/build-reading.py` | 改了 `library/shoulder/content.json`、读音或 SVG 时跑，把同一页写到肩袖旧地址 |
| ST-9（肩袖） | `node library/shoulder/pdf/render-pdf-diagrams.cjs`，再 `python3 library/shoulder/pdf/export-pdf.py` | 先把 SVG 渲染成图片，再排版 PDF；输入是 `text/2026-10-06-肩袖-阅读优化版.html`（ST-8 输出）；脚本用的是 macOS 系统字体路径。现在线上的 PDF 仍是 2026-10-06 版，主题页标着“尚未随正文更新”，重新导出并过 QC-27 后去掉这个标注（`site/build/platform/topiclib.py`）；细节见 [制作流程-肩袖双语学习.md](../../library/shoulder/text/制作流程-肩袖双语学习.md) §6 |
| ST-9（新章节） | 还没有通用导出脚本 | 新章节不会因为有 `content.json` 就自动有 PDF；要做 PDF 时先在 `library/<id>/pdf/` 放导出脚本，产物同样过 QC-27 |
