# DPT study · 解剖学习

> **一眼看懂**
> - **这是什么**：gui 的 DPT 双语学习站，含解剖知识库（肩袖、髋关节）、3D 模型和每天的学习包。
> - **在线打开**：[学习首页](https://guiguisqwd.github.io/dpt-study/study.html) · [每日学习包](https://guiguisqwd.github.io/dpt-study/daily/)（GitHub Pages，推送 `main` 后自动更新）
> - **状态**：公开，每天都有更新。
> - **相关仓库**：[push-hub](https://github.com/guiguisqwd/push-hub)（把每日学习包推送给你并存档） · [guiguisqwd.github.io](https://github.com/guiguisqwd/guiguisqwd.github.io)（个人主页，含全部仓库目录）


gui 的 DPT 学习仓库。内容分两大块，网站只负责把它们拼起来给人看：

| 块 | 位置 | 是什么 |
| --- | --- | --- |
| ① 解剖知识库 | [`library/`](./library/README.md) | 生成好的大内容，按部位分章。每一章自己带齐 `text/` 正文、`figures/` 图、`pdf/` 和 `3d/` 三维部分。现有：肩部 · 肩袖（`library/shoulder/`，已发布）、髋关节（`library/hip/`，草稿） |
| ② 每日学习 | [`daily/`](./daily/README.md) | 按规程从知识库取材，生成当天该学的东西（60 天十四经穴 + 肌肉计划）。规程见 [`standards/daily/`](./standards/daily/README.md) |
| 网站总装 | `site/` | `site/build/`：主题页、学习首页、发布脚本和校验；`site/public/daily/`：已发布的每日页面 |

规则只有一个来源：[`standards/`](./standards/README.md)（`library/` 知识库章节规则，`daily/` 每日学习规程）。协作、提交和推送规则见 [CLAUDE.md](./CLAUDE.md)。

**GitHub 是共同维护的项目来源：每次授权修改，检查后提交并推送。** 仓库 [guiguisqwd/dpt-study](https://github.com/guiguisqwd/dpt-study)（2026-10-08 由 shoulder-study 改名；同日按“知识库 / 每日学习”重新分目录，线上地址不变）。

- [学习首页](https://guiguisqwd.github.io/dpt-study/study.html) · [每日学习包](https://guiguisqwd.github.io/dpt-study/daily/) · [给 agent 的内容清单](https://guiguisqwd.github.io/dpt-study/llms.txt)
- [肩袖阅读](https://guiguisqwd.github.io/dpt-study/reading.html) · [Claude 阅读版](https://guiguisqwd.github.io/dpt-study/reading-claude.html) · [肩袖 3D](https://guiguisqwd.github.io/dpt-study/?term=humerus)
- [髋关节草稿](https://guiguisqwd.github.io/dpt-study/topics/hip/index.html) · [骨骼模型预览](https://guiguisqwd.github.io/dpt-study/?topic=hip&term=femur)

## 文件结构

```
library/                     ① 解剖知识库
  README.md                  如何新增一章
  shoulder/                  肩部 · 肩袖
    topic.json、ADAPTER.md   注册与兼容说明
    content.json             五章正文的唯一来源（HTML 与 Markdown 由它生成）；pronunciation.json 读音表
    text/                    build-reading.py、生成的成稿、制作记录
    figures/                 17 张可编辑 SVG
    pdf/                     已核验 PDF 与导出脚本
    3d/                      肩部 3D 网站（React / Three.js / Vite，未完成）：模型、语音、骨性标志、Claude 阅读版
  hip/                       髋关节（草稿）：topic.json、content.json、figures/、3d/
daily/                       ② 每日学习：plan/、days/<date>/、engine/、runs/、review-center/、pipeline.py
site/
  build/                     platform/（主题规范、校验、渲染）、build-*.py、validate-topics.py、new-topic.py、prepare-web-release.py
  public/daily/              每日页面（生成输出，由每日流程写入）
standards/                   规则唯一来源
tests/、.github/workflows/   自动检查与 GitHub Pages 发布
```

生成输出不在这里编辑：`library/shoulder/3d/public/topics.json`、`public/topics/`、`public/study.html`（由 `site/build/build-platform.py` 生成），`website-release/`（发布包）。

## 新增一章

```sh
python3 site/build/new-topic.py --id knee --en 'Knee joint' --zh 膝关节
python3 site/build/validate-topics.py
python3 site/build/build-platform.py
```

章节由 `library/<id>/topic.json` 自动发现，双语内容在同目录的 `content.json`，图示放 `figures/`，同一份 `content.json` 生成 HTML 和 Markdown。新章节默认 `draft`；按 [standards/library/steps.md](./standards/library/steps.md)（含 ST-7 本章 3D）做完并核验后才能标为 `published`。详细步骤见 [library/README.md](./library/README.md)。

## 本地构建

使用 Node.js 24、pnpm 11.19.0、Python 3.13，与发布工作流保持一致：

```sh
git clone https://github.com/guiguisqwd/dpt-study.git
cd dpt-study
python3 site/build/validate-topics.py
cd library/shoulder/3d
pnpm install --frozen-lockfile
pnpm build
```

依赖和锁文件未变时可省略安装。`pnpm build` 包含 TypeScript 检查；改变几何参照时另运行 `pnpm test:geometry` 和 `pnpm test:depth`。修改内容、图示或交互后，还需在浏览器中检查实际效果。

`pnpm build` 和 `pnpm dev` 都会先调用 `site/build/build-platform.py`，自动生成主题页与 `study.html` 主题库。单独运行 `build-topics.py` 只生成主题内容，不生成学习首页。

在应用目录运行：

```sh
python3 -m http.server 5178 --bind 127.0.0.1 --directory dist
```

打开 [肩袖 3D](http://127.0.0.1:5178/?term=humerus)、[肩袖阅读](http://127.0.0.1:5178/reading.html) 或 `/topics/<id>/index.html`。Mac 也可双击 `library/shoulder/3d/启动肩部学习.command`；开发时运行 `pnpm dev`。`127.0.0.1` 仅指当前电脑，本地服务停止后不可访问；分享使用线上地址。

## 更新与发布

先同步 GitHub，再修改源文件，校验并构建，检查效果，提交并推送。保留其他协作者的修改；不强推、不覆盖。具体协作规则见 [CLAUDE.md](./CLAUDE.md)。每一章（包括肩袖）的正文只写在自己的 `content.json`，页面与 Markdown 由它生成；Claude 阅读版单独维护。

修改肩袖 `content.json` 后，于仓库根目录运行 `python3 library/shoulder/text/build-reading.py`（写到肩袖原有的阅读页地址），再构建应用。

[GitHub Actions 工作流](./.github/workflows/pages.yml) 在推送 `main` 后检查、构建并发布，PR 只检查和构建。**本地保存、推送成功、部署成功是不同状态，分别核实后再报告。**

根目录运行以下命令生成静态发布包：

```sh
python3 -m pip install -r site/build/requirements-publish.txt
python3 site/build/prepare-web-release.py --site-url https://guiguisqwd.github.io/dpt-study/
```

网站入口为 `website-release/dist/study.html`；3D 入口仍是 `index.html`。发布保留主题内容、肩袖两种阅读版、模型、现有音频、配图、下载及许可，并转换线上链接。

肩袖 PDF 目前使用已核验的 38 页输入文件，发布仅更新其中的链接，不重新排版。正文或图示改动后，按肩袖制作流程重新导出并检查，不能把旧 PDF 称为已同步。新主题只有在实际生成、核验并登记后才提供 PDF 下载；自动生成的 Markdown 不代表 PDF 也已完成。

学习进度及本地标注保存在浏览器 `localStorage`，不随 GitHub 提交跨设备同步。公开站点允许阅读；Claude 修改和推送仍须用户授予 GitHub 写入权限，`CLAUDE.md` 本身不会授予账户权限。

## 交给 Claude

> 请先读本仓库的 CLAUDE.md 和 README.md。这是多主题 Anatomy study 项目，肩袖是第一个主题。新增主题请按 library/README.md 创建并填写主题数据，复用既有引擎和全部内容规范。开始前同步 GitHub 并保留已有修改；检查后提交并推送，报告实际 commit、分支和部署结果。保留现有语音和 Claude 独立阅读版。

## 来源与许可

3D 查看器基于 [Vanatome](https://github.com/vixotic/Vanatome)，版本记录在 [UPSTREAM.json](./library/shoulder/3d/UPSTREAM.json)。上游查看器代码采用 MIT；Z-Anatomy 等资产遵循 CC BY-SA 4.0 及署名要求。肩部附加模型（14 块肩部肌肉）由同一份 Z-Anatomy 源文件导出，同样按 CC BY-SA 4.0 发布，来源记录在 UPSTREAM.json 的 `addons`。分发时保留 [代码许可](./library/shoulder/3d/public/licenses/LICENSE)、[资产许可](./library/shoulder/3d/public/licenses/ASSET-LICENSE.md) 和 [署名](./library/shoulder/3d/public/licenses/ATTRIBUTION.txt)。这些说明不替未授权第三方材料授予新许可。

解剖与研究内容须保留各自来源、证据范围及未解决缺项。校验器检查结构、完整性和链接，不能代替专业内容核验。肩袖穴位为模型学习参照，其状态见 [3D 应用说明](./library/shoulder/3d/README.md)。
