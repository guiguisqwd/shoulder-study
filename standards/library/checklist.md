# 第 3 层 · 生理解剖检查清单

ST-5 核验时逐条过。自动项由脚本检查；人工项要留截图或记录作证据，未做的不能勾为通过（G-03）。

## 自动检查

| 编号 | 检查 | 对应规则 | 现在由谁检查 |
| --- | --- | --- | --- |
| QC-01 | 章节五部分齐全、顺序正确，没有论文一节（2026-10-09 之前做的章节在移出前除外）；每日包在生成流程改造前仍按 CH-02 六章检查 | CH-01、CH-02 | `topiclib.py`、`daily/engine/schema.py` |
| QC-02 | 图示占位符都有对应 SVG，SVG 是有效 XML，页面 id 唯一 | AN-10、AN-17 | `build-reading.py`、`daily` 构建 |
| QC-03 | Markdown 图片路径有效 | G-08 | `build-reading.py` |
| QC-04 | 每个 3D term / point 在模型词库中存在；缺项为 `null` | AN-40、AN-41 | `build-reading.py`、`topiclib.py` |
| QC-05 | 英文在前；肌肉 O/I/N/A 和句式齐全；穴位字段齐全 | AN-01 至 AN-03、AN-20 | `daily/engine/schema.py`；主题包的“英文在前”由 `site/build/platform/topiclib.py` 检查：`content.json` 每对 `{en, zh}` 英文格放英文、中文格放中文；生成的阅读页里 `lang="en"` 不夹中文、中文译文前面有英文、没有中文领头夹英文名词的句子（草稿记为待办，`published` 时报错）。主题包的 O/I/N/A 由 `topiclib.py` 的肌肉记录检查覆盖 |
| QC-06 | 读音覆盖所有英文关键术语 | AN-07 | `daily/engine/qa/qa.js`；主题包由 `topiclib.py` 检查：ST-1 结构清单里每个肌肉、神经、骨、骨性标志、关节在 `library/<id>/pronunciation.json` 有 IPA、重音拼读和词典链接，每个穴位有带声调拼音（草稿记为待办，`published` 时报错） |
| QC-07 | SVG 文字出界、重叠；手机宽度显示 | AN-16 | `daily/engine/qa/qa.js` |
| QC-08 | ST-1 结构清单存在；每一项在它所列的章节正文里出现；3D ID 真实存在；正文里每条肌肉记录都在清单里 | ST-1、AN-40、AN-41 | `site/build/platform/topiclib.py`（草稿记为待办，`published` 时报错） |
| QC-09 | 3D 附加模型检查通过（有 `library/<id>/3d/atlas-addon.json` 的章节）：`python3 site/build/atlas/check-addon.py` 无报错退出——与自带模型同一 `atlasVersion` 和 `buildId`、metadata 与 GLB 一致、ID 不与自带模型重复、左右侧位置正确且互为镜像、清单 `checks` 的位置检查全过 | AN-42、AN-44 | `site/build/atlas/check-addon.py`；CI 由 `tests/test_atlas_addon.py` 运行它，并核对导出脚本未改动、provenance 记录的 GLB 摘要与发布的文件一致；附加模型的 ID 只能由它所属的章节使用，由 `topiclib.py` 检查 |

## 人工检查

| 编号 | 检查 | 对应规则 |
| --- | --- | --- |
| QC-20 | 每项解剖事实都能对上来源，简化图与真实结构的差别已说明 | G-02、AN-50 |
| QC-21 | 逐张看截图：标签不压结构、引线不交叉且指向正确、穴位点位置正确、没有被裁掉的内容、图文一致 | AN-16、AN-17、AN-21 |
| QC-22 | 每段英文后面都有对应中文；问答展开后答案完整 | AN-01、AN-06 |
| QC-23 | 论文数值、单位、时间点与核对记录一致；核对层级已写明（2026-10-09 起用于每日的论文 N-5） | AN-31 至 AN-33 |
| QC-24 | 点开代表性 3D 链接，确认选中结构、侧别正确；旋转、缩放、切换、后退无跳跃 | AN-40、AN-42 |
| QC-25 | 宽屏、分屏、窄屏下无遮挡和溢出 | AN-16 |
| QC-26 | 制作记录列出所有未核验项 | G-03 |
| QC-27 | PDF（ST-9）：每一页都渲染出来看过；内容和阅读页逐项对照无遗漏（章节、图、表、问答数与导出清单一致）；文字不出界；链接可点击；生成自当前构建 | G-03、G-08、AN-16 |

新主题从 `draft` 改为 `published` 前，以上各项和 `library/README.md` §4 的 8 项签核都要完成，并记录审核人和日期。
