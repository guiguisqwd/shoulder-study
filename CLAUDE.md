# Anatomy study · 解剖学习 — Claude collaboration rules

本文件记录用户对本项目的长期协作要求。Claude 在开始工作前应读取本文件；用户在当前对话中的明确指示优先于本文件。

用户要求将本仓库作为独立的“解剖学习工作台”项目维护，范围覆盖整个多主题学习工作台。项目职责、入口和接手说明见 [README.md](./README.md)；项目注册不由这些文档自动完成。

## 0. 两大块：知识库与每日学习

用户 2026-10-08 定的结构（“我们要细分，才能划清结构”）：

- **① 解剖知识库 `library/`**：生成好的大内容，按部位分章。肩袖是“肩部”这一章（`library/shoulder/`），髋关节是另一章（`library/hip/`）。每一章自带 `text/` 正文、`figures/` 图、`pdf/` 和 `3d/`。生成、修改 3D 网站是每一章都要有的部分（`standards/library/steps.md` 的 ST-7）。现在的 3D 网站还没完成，归肩部这一章（`library/shoulder/3d/`）；髋关节暂时借用它预览骨骼。
- **② 每日学习 `daily/`**：按规程（`standards/daily/README.md`）从知识库取材，生成当天该学的东西。
- **网站总装 `site/`**：`site/build/` 把各章和每日学习拼成网站并发布；`site/public/daily/` 是每日页面输出。它不放内容。
- 线上地址在重新分目录后保持不变（reading.html、reading-claude.html、`?term=`、topics/<id>/、daily/）。新内容放进上面对应的块，不在仓库根目录另放文件。

## 0.1 多主题产品

用户要求这个软件覆盖多个解剖主题；后续加入 Hip joint（髋关节）等内容时，应沿用已经确认的内容、图示、英语表达、模型联动与质量检查规范，避免重复修正同一类问题。

- GitHub 仓库于 2026-10-08 按用户要求由 `shoulder-study` 改名为 **`dpt-study`**（站点 `https://guiguisqwd.github.io/dpt-study/`）。GitHub 会把旧仓库地址重定向到新仓库，但 Pages 旧站点路径不会自动跳转（`guiguisqwd.github.io` 仓库里的 `shoulder-study/` 跳转页负责这件事）。
- 新主题放在 `library/<id>/`，由 `topic.json` 注册；用共享脚本发现、校验并构建。先读 [library/README.md](./library/README.md)，不要复制整个应用另建一套。
- 保持“共享界面与渲染逻辑”和“主题内容与模型映射”分离。一般新增关节应修改主题数据、图示和资料；如果确需扩展共享能力，扩展一次并检查已有主题。
- 肩袖和其他章节一样以 `library/shoulder/content.json` 为唯一正文来源；`shoulder` 适配方式只负责保留旧地址（reading.html、`?term=`）、3D 行为、语音和 Claude 独立版。不要为统一目录破坏已经完成的内容。
- `draft` 表示内容未完成，`published` 表示主题已完成相应核验。Hip joint 的起始目录是结构化草稿，不等于已完成的髋关节课程。不得把占位数据、未核对图示或未知模型当作已就绪学习材料。
- 自动检查可以发现结构和链接问题，不能证明解剖事实正确；发布前仍须核验资料和实际图文显示。

## 1. GitHub 是共同维护的项目来源

用户的原话：

> 直接存在 github 上，然后每次更新和修改都存在 github 上；写个 md 给 Claude，让他记录这个规则。

执行规则：**每次完成用户授权的内容或代码修改，都要在适当检查通过后提交到 Git，并推送到同一个 GitHub 仓库。只修改本地文件不算完成同步。** 不必为已经授权的正常提交和推送重复征求确认。

共同仓库：[guiguisqwd/dpt-study](https://github.com/guiguisqwd/dpt-study)；远端地址：`https://github.com/guiguisqwd/dpt-study.git`。该仓库为公开仓库，只放本项目可公开的学习内容、代码及必要资源。

- 本仓库包含知识库、每日学习、网站总装和规则（见 §0）；用户 Mac 上的本地目录仍沿用“肩袖”这一历史名称。不要把上级“知识工作台”中的其他项目一起加入版本控制。
- 用 `git remote get-url origin` 确认实际 GitHub 地址；用当前分支及其 upstream 确认推送目标。不要猜测仓库名称、分支或部署地址。
- 多台电脑、Codex 和 Claude 使用同一仓库；开始新工作前先同步远端，完成后推送。不要长期保留互不关联的“最终版”副本。
- 生成文件用于阅读和发布；可维护的源文件也必须进入仓库，不能只上传 `dist/`。

## 2. 每次修改的 Git 流程

1. 读取本文件、根目录 `README.md` 和相关子项目说明；运行 `git status --short --branch`、`git remote -v`，确认仓库、分支和未提交修改。
2. 运行 `git fetch origin`，检查本地与 upstream 的差异。工作区干净且能快进时，运行 `git pull --ff-only`。若存在用户或另一代理的未提交修改，先辨认归属、保留原文件，避免直接拉取造成覆盖。存在分叉时检查双方改动并整合，不要强行重置。
3. 修改源文件，再生成相应输出。先完成必要检查，检查 diff，只暂存此次任务需要的文件。不要把不相关修改、账户资料、API key、访问令牌、`.env`、语音暂存目录或依赖目录一并提交。
4. 使用描述实际变化的提交说明。正常完成任务时执行 `git commit` 和 `git push`，推送到已确认的当前工作分支及其 upstream。若用户要求 PR，按该流程提交 PR，不能把尚未合并的分支称为已上线。
5. 推送后核对远端目标分支的 commit 与本地 `HEAD`，报告提交号和推送结果。若存在发布工作流，再核对运行结果和线上入口；“已推送”与“已部署成功”分别报告。

不得自动 `push --force`、`reset --hard`、删除他人分支或覆盖他人工作。遇到权限、网络、合并冲突或发布失败，应保留已完成的文件和提交，说明准确阻碍；不能声称“已同步 GitHub”或“已上线”。推送被拒绝时，先获取远端新提交并检查差异，保护双方工作。

## 3. 文件与构建边界

| 需要修改的内容 | 应编辑的位置 |
| --- | --- |
| 主题目录、状态、标题与入口 | `library/<id>/topic.json` |
| 新主题内容、资料及模型映射 | 对应 `library/<id>/`；创建方式与校验见 `library/README.md` |
| 主题生成与校验规则 | `site/build/` 中共享脚本 |
| 共享主题内容规范、页面渲染和主题库样式 | `site/build/platform/` |
| 肩袖五章阅读正文（HTML 与 Markdown 由它生成） | `library/shoulder/content.json`；读音在 `library/shoulder/pronunciation.json` |
| 阅读页版式与目录（各章共用） | `site/build/platform/reading.py`、`site/build/platform/reading.css` |
| 肩袖可编辑解剖配图 | `library/shoulder/figures/` 中的 SVG |
| 肩袖结构清单与 3D 跳转 | `library/shoulder/topic.json` 的 `structures`；正文另需的 3D 名称写在 `content.json` 的 `modelLinks` |
| 3D 页面、状态与交互（肩部章节，髋关节暂借用） | `library/shoulder/3d/src/` |
| 章节 3D 附加模型（自带模型缺的肌肉） | `library/<id>/3d/atlas-addon.json`；共用脚本 `site/build/atlas/`（见其 README） |
| 模型、音频、许可等公开资源 | `library/shoulder/3d/public/` |
| Claude 独立阅读版 | `library/shoulder/3d/public/reading-claude.html` |
| 每日学习包（内容、配图、流水线、运行记录） | `daily/`：每天的 `days/<date>/content.json` 与 `figures.py`；共用引擎在 `daily/engine/`；说明见 `daily/README.md`。`site/public/daily/` 是生成输出 |

`reading-claude.html` 是独立维护的版本，必须保留。标准阅读构建不得覆盖它；修改该版时以 `public/reading-claude.html` 为源，不要只改 `dist/` 中的副本。

新主题正文只维护一份 `content.json`，共同生成 HTML 和 Markdown。主题校验与生成在仓库根目录运行：

```sh
python3 site/build/validate-topics.py
python3 site/build/build-platform.py
```

`library/shoulder/3d/public/topics.json` 和 `public/topics/` 是主题构建输出，不能只在其中修改正文。新主题先保持 `draft`，按 `library/README.md` 完成内容与验证后再改为 `published`。

`python3 site/build/build-platform.py` 生成主题页和自动发现主题的 `study.html` 学习首页；应用的 `prebuild` / `predev` 会调用它，因此正常的 `pnpm build` / `pnpm dev` 会同步主题库。

修改 `library/shoulder/content.json` 后运行 `python3 library/shoulder/text/build-reading.py`，把同一份内容写到肩袖原有的 HTML / Markdown 输出位置（含 `3d/public/reading.html`），再构建应用。

3D 应用构建：

```sh
cd library/shoulder/3d
pnpm install --frozen-lockfile
pnpm build
```

依赖已安装且锁文件未变时，无须重复安装。`pnpm build` 包含 TypeScript 检查；改变穴位参照或几何逻辑时另运行 `pnpm test:geometry`。对阅读版式、图示、模型链接及交互的修改，要在浏览器中检查实际效果，不能仅以编译通过替代视觉检查。

发布材料由 `site/build/prepare-web-release.py` 生成到 `website-release/`。正式发布传入 `--site-url` 和实际 HTTPS 根地址（包括 GitHub Pages 项目子路径），使 HTML、Markdown 和 PDF 中的 3D 链接指向线上站点。

GitHub Pages 的 Source 已设为 GitHub Actions。`.github/workflows/pages.yml` 在推送 `main` 时执行检查、构建和发布；PR 仅检查与构建。它使用 Node.js 24、pnpm 11.19.0、Python 3.13，以及 `site/build/requirements-publish.txt` 固定的 `pypdf==6.10.0`。本地保存不会自动上线；每次修改完成后提交并推送到 `main`，且工作流发布成功，才会更新网站。必须核对 Actions 和站点结果。

线上入口如下；首次部署已于 2026-10-06 通过 GitHub Actions，并验证阅读、3D 和下载入口返回 HTTP 200。以后每次部署仍需检查运行结果：

- 学习首页：`https://guiguisqwd.github.io/dpt-study/study.html`
- 标准阅读：`https://guiguisqwd.github.io/dpt-study/reading.html`
- Claude 阅读版：`https://guiguisqwd.github.io/dpt-study/reading-claude.html`
- 3D：`https://guiguisqwd.github.io/dpt-study/?term=humerus`

PDF 及其导出脚本位于 `library/shoulder/pdf/`；Markdown 配图包在发布时生成。目前发布使用已核验的 38 页 PDF，仅用 `pypdf` 更新其中的线上链接，不重新排版。PDF 重新导出目前依赖 Mac 字体和本地渲染环境；正文或配图变化后，按 `library/shoulder/text/制作流程-肩袖双语学习.md` 重新导出并检查，再提交更新。不要把旧 PDF 标为已同步，也不要假设 Ubuntu 发布工作流会自动重建 PDF。

## 4. 内容制作规范

内容怎么写、怎么画、怎么核验，统一见 [standards/README.md](./standards/README.md)（2026-10-08 起的唯一来源）。制作知识库章节前依次读 `standards/00-general.md`、`standards/library/chapters.md`、`standards/library/rules.md`、`standards/library/steps.md`，交付前跑 `standards/library/checklist.md`；生成每日学习前再读 `standards/daily/README.md`。规则改动只改 `standards/` 里的那一条，并记进 `standards/CHANGELOG.md`；不要在本文件或其他文档里另抄一份。

最常被指出的几条：英文在前、中文在后（G-01）；肌肉写全起止点和完整走行句（AN-03）；神经画在实体解剖上并分清 C/T/L/S（AN-04、AN-12）；英文术语都配读音（AN-07）；3D ID 必须真实存在，缺项写明（AN-40、AN-41）；保留现有语音与独立阅读版（G-09）。创建新主题时一开始就按这些要求做，不等用户再次指出。

## 5. Claude 的权限与协作方式

公开网站或公开 GitHub 地址允许读取资料，**不会自动赋予 Claude 写入权限**。Claude 必须通过用户已经授权的本地仓库、Claude Code 或支持写入的 GitHub 集成，才能提交和推送。不要在聊天、网页或仓库中索取或保存令牌。

本文件是可版本化的项目规则，不代表已经修改了 Claude 账户的永久记忆或已授予账户权限。支持自动读取 `CLAUDE.md` 的工具应在仓库根目录工作；其他 Claude 界面应先读取或附加本文件，再开始修改。

最终交付说明应包含：改了什么、完成了哪些检查、commit、实际推送分支，以及部署状态（若此次涉及部署）。
