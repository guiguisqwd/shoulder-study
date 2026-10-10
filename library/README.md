# Adding a topic · 新增解剖主题

新主题复用 Anatomy study 的主题目录、页面生成、3D 查看器和内容检查。肩袖（`library/shoulder/`）是第一章，也是参照样例；Hip joint（髋关节）目前是结构化草稿。仓库名称为 `dpt-study`（原 `shoulder-study`）；历史目录保持稳定，避免破坏旧链接。

## 1. 同步并创建主题

先读根目录 `CLAUDE.md`，检查工作区及远端，安全同步 GitHub。不要覆盖其他人正在修改的文件，也不要复制整套应用来创建第二个项目。

在仓库根目录运行：

```sh
python3 site/build/new-topic.py --id knee --en 'Knee joint' --zh 膝关节
```

主题 ID 使用稳定的英文 slug，发布后不随展示标题变化。可通过 `--region-en` 和 `--region-zh` 补充解剖区域。脚本创建 `library/knee/`；新主题默认 `draft`，不是可直接学习的完成课程。

| 文件 | 维护内容 |
| --- | --- |
| `topic.json` | 中英文名称、区域、状态、适配方式、模型绑定，以及 ST-1 结构清单 `structures` |
| `content.json` | 按共享结构填写的双语正文、肌肉、问答、文献及核验记录 |
| `figures/` | 该章拥有的图示；优先保留可编辑 SVG 及来源信息 |
| `3d/` | 该章的 3D 部分（ST-7）；新章节起步时只有说明，模型映射写在 `topic.json` |

使用脚本生成的实际字段结构，不自行猜测新字段名称。标准新主题使用 `standard` 适配方式；`shoulder` 适配方式只为肩袖保留旧网址（reading.html、`?term=`），内容检查与其他章相同。

具体记录结构见 `site/build/platform/topic.schema.json`、`site/build/platform/content.schema.json` 和 `site/build/platform/content-records.example.json`；后者提供肌肉、图示、问答、文献等记录样式，空值需要填入真实核验内容。共享要求见 `site/build/platform/QUALITY_RULES.md`。**新主题以 `content.json` 作为唯一正文来源，HTML 和 Markdown 由同一内容生成。**

### 结构清单（ST-1 的输出）

选题时先在 `topic.json` 的 `structures` 里列出本章要讲的全部内容，写正文之前就填好。每一项：

```json
{
  "id": "suprascapular-nerve",
  "kind": "nerve",
  "name": {"en": "Suprascapular nerve", "zh": "肩胛上神经"},
  "chapters": ["innervation", "clinical", "review"],
  "modelTermId": null
}
```

| 字段 | 写什么 |
| --- | --- |
| `id` | 英文小写 slug，章内唯一；肌肉的 `id` 与 `content.json` 里肌肉记录的 `id` 相同 |
| `kind` | `muscle`、`nerve`、`bone`、`landmark`、`joint`、`acupoint` 之一（`paper` 同上，只留给旧章节） |
| `name` | 英文、中文名称；论文写正式标题 |
| `chapters` | 出现在哪几章：`anatomy`、`innervation`、`movement`、`clinical`、`review`（`papers` 只留给 2026-10-09 前做的章节，论文移出后删掉） |
| `modelTermId` | 3D 里真实存在的 ID；模型没有就写 `null`（AN-41） |
| `aliases`（可选） | 正文里的其他写法，如穴位代码 `SI11`、论文 DOI |

校验脚本（QC-08）检查：清单不为空；每一项的英文名或别名出现在它所列的每一章里；`modelTermId` 真实存在；`content.json` 里每条肌肉记录都在清单里。草稿阶段这些记为待办，改成 `published` 时变成错误。肩袖的清单在 `library/shoulder/topic.json`，可作参照。

### 读音表（AN-07 的输出）

每章在 `library/<id>/pronunciation.json` 写读音，格式与每日学习的 `daily/engine/data/pronunciation.json` 相同，方便每日包直接取用：

```json
{
  "terms": {
    "Supraspinatus": ["/ˌsuprəspaɪˈneɪtəs/", "soo-pruh-spy-NAY-tus", "https://www.merriam-webster.com/medical/supraspinatus"]
  },
  "pinyin": {
    "Jianyu": "Jiānyú"
  }
}
```

`terms` 的键是英文名称，值依次是斜杠包住的 IPA、只大写重音音节的拼读、HTTPS 词典链接。`pinyin` 的键是穴位在结构清单里的英文名，值是带声调拼音。校验脚本（QC-06）检查：结构清单里每个 `muscle`、`nerve`、`bone`、`landmark`、`joint` 在 `terms` 里有一项（不分大小写），每个 `acupoint` 在 `pinyin` 里有一项；每一项格式正确。论文不需要读音。

同一脚本还检查英文在前（QC-05）：`content.json` 里每对 `{en, zh}` 英文格只放英文、中文格放中文。

### 题库（ST-10 的输出，【试用】AN-60）

每章在 `library/<id>/questions.json` 写题库。一道题有三种写法：

```json
{
  "schema": "dpt-question-bank/1",
  "chapter": "shoulder",
  "questions": [
    {"id": "supraspinatus-oina", "type": "recall", "part": "anatomy", "covers": ["supraspinatus", "greater-tubercle"],
     "record": "muscles/supraspinatus", "ask": ["origin", "insertion", "innervation", "actions"]},
    {"id": "review-insertions", "type": "recall", "part": "review", "covers": ["greater-tubercle"],
     "record": "review/q-insertions", "points": [{"en": "...", "zh": "..."}, {"en": "...", "zh": "..."}]},
    {"id": "force-couples", "type": "recall", "part": "movement", "covers": ["deltoid"], "from": "movement",
     "prompt": {"en": "...", "zh": "..."}, "answer": {"en": "...", "zh": "..."}, "points": [{"en": "...", "zh": "..."}, {"en": "...", "zh": "..."}]}
  ]
}
```

- `record` 指向 `content.json` 里已有的记录：`muscles/<id>`、`acupoints/<id>` 用 `ask` 选要问的字段（肌肉：`origin`、`insertion`、`course`、`innervation`、`actions`；穴位：`location`、`howToFind`、`layers`、`target`、`safety`），题面、答案和评分要点由脚本生成；`review/<id>` 取第 5 部分那道问答，另配 `points`。
- 没有现成记录的题自己写 `prompt`、`answer`、2–5 条 `points`，并用 `from` 写明答案出自哪一部分（`anatomy`、`innervation`、`movement`、`clinical`、`review`）。
- `type`：`recall`、`term`、`locate`、`reason`、`case`；`part`：这道题归在哪一部分；`covers`：考到的结构清单 `id`。
- `python3 site/build/platform/questions.py library/<id> --markdown` 打印全部题目和答案。其他程序（每日包、复习中心）用同一文件里的 `expand()` 取统一格式的题：`id`、`type`、`part`、`covers`、`prompt`、`answer`、`points`、`from`、`sources`。

### 正文块（`sections[].blocks`）

每章的 `blocks` 按顺序排版，同一份内容生成网页和 Markdown（`site/build/platform/reading.py`）。双语值都写 `{"en", "zh"}`；文字里可用 `**粗体**` 和 `[来源名](https://…)`。解剖名称不要手写 3D 链接：结构清单里的名称和 `modelLinks` 里的名称在生成时自动链接。

| `type` | 用途 | 主要字段 |
| --- | --- | --- |
| `heading` | 小标题 | `level`（3 或 4）、`text` |
| `paragraph` | 一段英文 + 中文译文 | `text` |
| `figure` | 插图，图注取自图示记录 | `diagramId`、`size`（可选 `medium`） |
| `table` | 表格；每行第一格是行标题 | `columns`、`rows`（格子是 `{en, zh}`，数字、代码这类不分语言的值可写字符串）、`className` |
| `note` | 提示框 | `heading`、`paragraphs`、`items`、`definitions`、`className` |
| `cards` | 并排卡片或分阶段卡片 | `layout`（`columns` / `stages` / `stack`）、`cards[]`（`label`、`heading`、`paragraphs`、`items`） |
| `steps` | 编号步骤，如触诊顺序 | `items[]`（`heading`、`text`） |
| `mnemonic` | 口诀：完整英文中文句 + 中文原口诀 | `text`、`original` |
| `details` | 可折叠段落（不能再套 `details`） | `summary`、`open`、`blocks` |
| `sources` | 段落下的“来源”行 | `ids` |
| `muscles` / `landmarks` / `acupoints` / `quiz` / `paper` | 把对应记录排进这一位置 | `ids`（`paper` 用 `id`）；`muscles` 另有 `layout`（`cards` / `compact`） |
| `nerveNotation` | C / T / L / S 说明（AN-04） | — |

记录（`muscles`、`landmarks`、`acupoints`、`review`、`papers`）没被任何块排进去时，自动接在默认章节末尾：肌肉和骨性标志在 01，穴位在 04，问答在 05（旧章节的论文在 06）；神经支配一章没有自己的 `nerve-levels` 提示框时自动加上 `nerveNotation`。穴位记录（AN-20）写 `code`、`name`、`location`、`layers`、`target`、`howToFind`、`safety`、`modelPointId` 和 `sources`。`page`（可选）放页眉、副标题、页脚和目录下方说明。肩袖 `library/shoulder/content.json` 用到了全部块，可作参照。

## 2. 一次性按完整标准填写

专业名词、完整句子、标题、图示标签和答案均为 **English first, Chinese second（英文在前，中文在后）**。句子分别给出完整英文和中文译文；不要用中文句子夹几个英文单词替代专业英文表达。

| 阶段 | 必须包含的内容 |
| --- | --- |
| 01 Anatomy · 解剖 | 关节和骨性标志；每块肌肉的 Origin（起点）、Insertion（止点）、Course（走行）与 Action（动作）；起止点图示与正文可对应 |
| 02 Innervation · 神经支配 | 神经起源、节段、解剖走行和支配对象；实际位置图，流程图仅作补充；明确 C / T / L / S 指颈、胸、腰、骶部，并区分椎骨与神经节段 |
| 03 Movement · 动作 | 动作方向、参与肌肉、起止点与牵拉关系；相关结构链接到同一主题中的实际模型 |
| 04 Clinical anatomy · 临床解剖 | 与本主题相关的结构关系、检查或损伤表现及资料依据；说明教学模型的简化和证据范围 |
| 05 Review · 复习 | 简记或口诀，以及完整专业英文描述和中文译文；问题与完整答案，不只给关键词 |

肌肉英文表达可使用下面的句式，但各主题的内容必须根据资料填写：

> The [muscle] originates from [origin], passes [direction or anatomical relation], and inserts onto [insertion]. It is innervated by [nerve and spinal segments] and contributes to [action].
>
> ［肌肉］起于［起点］，沿［方向或解剖关系］走行，止于［止点］。其由［神经及节段］支配，并参与［动作］。

图中同时标注 Origin / 起点、Insertion / 止点及相应解剖名称。必要时使用上下两行标签、引线或分图；不能缩小到无法阅读，也不能让文字遮盖所指结构。

资料与图示来源一并记录；第三方图片和模型须确认使用许可。不将 AI 提示词、“把前面的知识用起来”等制作性话语写进课程正文。制作和核验过程放维护文档。

## 3. 核对 3D 模型绑定

从现有模型清单和查看器实际支持的结构选择绑定 ID，不能根据英文名称猜 ID。主题配置保存绑定，共享引擎负责加载、定位和展示。

- 新主题入口使用 `?topic=<id>`，结构入口使用对应的真实 `term`；已有肩袖 `?term=humerus` 等链接继续兼容。
- 骨骼、骨性标志和肌肉要分别核对；选择大骨骼不代表其中每个标志已经提供独立定位。
- 模型中没有的结构记录为缺项，明确说明；不能让链接悄悄跳到别的肌肉。
- 标记坐标、观察视角和来源需验证。穴位深部参照、附着点示意等不能自动当作标准临床定位。
- 每个实际模型链接都在浏览器打开核对；检查前后切换、旋转、缩放和返回阅读的行为。

一般加入一个关节不需要复制 React 页面或重写渲染器。若现有模型或共享能力确实不够，补充一次通用支持并检查肩袖兼容性；内容骨架不会自动生成可信的解剖图或模型。

自带模型缺本章要讲的肌肉时，不另找模型：经用户同意（AN-43）后，在 `library/<id>/3d/atlas-addon.json` 列出要导出的 Z-Anatomy 网格和位置检查，用共用脚本导出本章的附加模型（AN-44、QC-09；做法见 [site/build/atlas/README.md](../site/build/atlas/README.md)）。主题构建发现这个文件后，本章的 3D 页面会一起载入附加模型；附加模型里的 ID 只能由本章使用。

## 4. 校验、构建与人工核验

在仓库根目录运行：

```sh
python3 site/build/validate-topics.py --topic knee
cd library/shoulder/3d
pnpm build
```

几何或空间标记发生变化时，另外运行 `pnpm test:geometry`。`validate-topics.py` 不带 `--topic` 时检查全部主题；`--require-published` 可用于检查指定主题是否已达到发布状态。

生成结果在 `library/shoulder/3d/public/topics.json` 及 `public/topics/<id>/`。标准主题包含 `index.html`、`reading.html`、`reading.md` 和 `data.json`；改动应回到主题源文件，不直接修生成页。构建输出同步进入应用打包与网站发布流程。

`python3 site/build/build-platform.py` 还会生成自动发现所有主题的 `study.html` 首页；`pnpm build` 与 `pnpm dev` 通过各自的前置命令调用它。共享规范、校验和渲染逻辑位于 `site/build/platform/`，CLI 入口位于 `site/build/`。

肩袖还要把同一页写到旧地址：改动 `library/shoulder/content.json` 后运行 `python3 library/shoulder/text/build-reading.py`。新主题不需要这一步。

发布前完成以下核验，并在主题提供的审核字段中记录真实结果、审核人和日期：

1. **解剖与来源：** 每项起点、止点、走行、神经支配和动作都有对应资料；区分简化图与真实结构，不把自动通过当作事实正确。
2. **双语与完整性：** 五部分齐全；英文在前，中文在后；完整描述与完整问答均存在；方法学专业名词有对应英文。
3. **图示：** 肌肉起止点清楚；神经有解剖位置图；神经节段与椎骨编号明确；图例、指向线与正文一致。
4. **模型：** 所有提供的结构绑定和链接都实测；缺失结构明确列出；不出现错误结构、错误侧别或错误主题。
5. **版式：** 在宽屏、分屏和窄屏检查标签重叠、溢出、图文遮挡、表格及答案展开，实际阅读尺寸下保持可读。
6. **交互：** 连续切换结构、主题和视角；旋转、缩放、后退和链接跳转不出现不必要的跳跃；现有肩袖行为及语音保持正常。
7. **导出：** HTML 与 Markdown 来自相同内容；所有下载确实存在且与当前内容一致，图片路径和线上链接有效。
8. **发布记录：** 检查 diff、校验和构建结果，记录仍待解决的问题；未执行的人工步骤不得勾为通过。

校验器对 `published` 标准主题要求更完整的内容、资料、图示、审核字段与质量标记。真实完成这些要求后才能把 `status` 改为 `published`；为了消除报错而随意填写审核人、日期或通过标记不算完成。草稿可以进入版本控制并展示草稿状态，不能作为已完成课程推荐。

## 5. 提交并更新网站

按 `CLAUDE.md` 的 Git 流程检查 diff，提交本次相关文件并推送。推送 `main` 后由 GitHub Actions 发布；其他分支或 PR 不应称为已上线。核对远端 commit、Actions 状态、主题目录、阅读页、3D 入口及实际下载，再报告结果。

每个新主题都应自动出现在主题目录，不需要手动复制一份首页。若新增字段需要共享渲染能力，先更新通用脚本和验证规则，再修改主题数据。

PDF 为可选导出，必须真实生成、检查并与当前内容建立对应后才登记。现有肩袖 PDF 的重新导出流程见 [制作流程-肩袖双语学习.md](./shoulder/text/制作流程-肩袖双语学习.md)；新主题不会因为创建了 `content.json` 就自动拥有 PDF。

正常交付说明应包括主题状态、已完成内容、未完成缺项、检查证据、commit、实际推送分支和部署结果。保留清晰的边界比把草稿叫成“完成”更有助于下次继续。
