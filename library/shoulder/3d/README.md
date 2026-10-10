# 肩部 3D 学习

基于 Vanatome 与 Z-Anatomy 的本地肩部空间解剖学习工具。使用真实肌肉、骨骼模型，帮助对照肩袖、骨性标志和穴位定位文字。

## 启动

直接双击本目录的 `启动肩部学习.command`，然后打开 <http://127.0.0.1:5178/>。已构建的页面和模型都在本地，无需联网下载模型。关闭终端窗口即可停止服务。

需要修改源代码时，可使用下面的开发命令。

依赖已安装时，在本目录运行：

```sh
pnpm dev
```

打开终端显示的本地地址。检查并构建、预览构建结果：

```sh
pnpm build
pnpm preview
```

新环境先运行 `pnpm install --frozen-lockfile`。模型已保存在 `public/models`，页面需通过本地服务打开。

## 当前功能与定位状态

- 加载 Vanatome 1.4.0 肌肉及骨骼模型，以及本章的肩部附加模型（14 块肩部肌肉，见下文“肩部附加模型”），旋转、缩放并查看肩部结构。
- 在模型三维坐标中放置学习标记，通过透视观察标记与深层解剖的关系。
- 将标记位置及说明保存为本地 JSON 数据，保留供后续核对。
- 内置天宗 Tianzong (SI11)、秉风 Bingfeng (SI12)、肩贞 Jianzhen (SI9)、肩髃 Jianyu (LI15)、肩髎 Jianliao (TE14) 的双侧学习参照，共十个点。
- 英语名称为主，中文释义为辅；支持一键隐藏词卡、模型标签和结构索引中的中文，用于回忆与自测。
- 40 个英语解剖词汇（其中 18 个是附加模型的肌肉词条）及 5 个穴位拼音名称，提供读音提示、词典来源，以及正常／0.75 倍慢速发音；还没有录音的词由浏览器自带语音朗读（见“英语背词与读音”）。
- 肌肉按组开关：图层栏的 Rotator cuff · 肩袖、Deltoid · 三角肌 默认打开，More muscles · 更多肌肉 下的四组附加肌肉默认关闭，所以默认视图与加入附加模型之前相同；工具栏的 Hide muscles · 隐藏肌肉 一键隐藏全部肌肉、只留骨骼（见下文“图层与隐藏肌肉”）。
- 点击模型结构、标签或词表会联动背词卡；Anatomy / Bone landmarks / Acupoints 切换结构、骨性标志和穴位参照。词表中的八个骨性标志现在直接聚焦对应骨面指示点；Posterior shoulder 单独标明为肩后区域参照。
- 点击阅读笔记中的穴名，聚焦对应标记；手动调整保存在覆盖层，可恢复内置参照。
- Acupoints 模式中，Depth probe · 深浅探针 沿一条几何学习轴线显示所选穴位参照穿过的模型层次；穴位详情的 Depth & surroundings · 深浅与周围结构 列出层次深度、参照点深度及 3 cm 内的周围结构。

**已建立模型中的深部解剖学习参照，尚未经过临床穴位校准。** 天宗依据近似肩胛冈中点与下角比例线推定区域，其余条目按特定骨肌关系建立区域参照。十个点均经过实际 GLB 网格内部检查，不是皮肤表面的贴图。体表定位参考点与深层解剖参考点应分别注明；肌肉中心、一次模型点击或任意向内偏移不能直接确定标准穴位。标记之间的空间关系不应解读为穿刺路径，也不表示进针方向或深度。

标记保存的是原始 GLB 模型坐标。显示时模型与标记共同应用 7 倍缩放及 `[0, -6.1, 0]` 位移。校准数据应绑定当前模型版本，不能直接套用于另一人体、另一姿势或改过比例的模型。

## 校准前需核对的姿势差异

- 肩贞：核对模型上臂位置是否符合定位描述中的内收姿势，以及腋后纹能否辨认。
- 肩髃、肩髎：标准描述涉及上臂外展，肩髎还涉及屈肘；需核对肩峰、肱骨大结节及相应凹陷在当前模型姿势下的关系。
- 天宗、秉风：先辨认肩胛冈、冈上窝、冈下窝与肩胛下角，并核对肩胛骨当前位置。
- 左右侧分别复核骨性标志与模型形态；不能只凭镜像坐标就视为完成校准。

## 肩部附加模型

自带的 `z-anatomy-1.4.0-muscular.glb` 是 Vanatome 的演示子集，肩带和上臂的肌肉只有肩袖和三角肌。用户 2026-10-09 选定“整个肩部”后，按 AN-44（[standards/library/rules.md](../../../standards/library/rules.md)）从同一份 Z-Anatomy 源文件另导出一个附加模型，补上 14 块肩部肌肉；自带模型、骨性标志和穴位参照位置都没有改，深浅数据随附加模型重新计算（见“深浅与周围结构”）。

| 文件 | 内容 |
| --- | --- |
| [`atlas-addon.json`](./atlas-addon.json) | 清单（唯一可编辑的源）：每块肌肉的 Z-Anatomy 源网格、`renameSourceObjects`、位置检查 `checks`、`mappingNotes` |
| `public/models/z-anatomy-1.4.0-shoulder-addon.glb` | 42 个网格，左右各 21 个，约 2.3 MB |
| `public/models/shoulder-addon.metadata.json` | 结构清单：每个网格一个 ID（以 `-right` / `-left` 结尾）；另有 13 个不含网格的组 ID（如 `trapezius-muscles`；大、小菱形肌同在 `rhomboid-muscles`），`objectCount` 为 0，它们的上级 `muscular-system` 在自带模型里 |
| `public/models/shoulder-addon.provenance.json` | 来源记录：Z-Anatomy 仓库 commit、zip 与 `.blend` 的 SHA-256、导出脚本、Blender 版本、GLB 的 SHA-256，以及每个网格的源名称（改过名的另记 Z-Anatomy 原名）和上下范围 |

14 块肌肉（按图层栏分组）：

- Back · 背部：Trapezius 斜方肌（descending part 降部 = upper 上部、transverse part 横部 = middle 中部、ascending part 升部 = lower 下部）、Latissimus dorsi 背阔肌、Levator scapulae 肩胛提肌、Rhomboid major 大菱形肌、Rhomboid minor 小菱形肌
- Chest · 胸部：Pectoralis major 胸大肌（clavicular head 锁骨头、sternocostal head 胸肋头、abdominal part 腹部）、Pectoralis minor 胸小肌、Subclavius 锁骨下肌、Serratus anterior 前锯肌
- Teres major · 大圆肌
- Upper arm · 上臂：Biceps brachii 肱二头肌（long head 长头、short head 短头）、Triceps brachii 肱三头肌（long head 长头、lateral head 外侧头、medial head 内侧头）、Coracobrachialis 喙肱肌、Brachialis 肱肌

**怎么生成。** 在仓库根目录运行 `python3 site/build/atlas/build-addon.py shoulder --blender-python <能 import bpy 的 Python>`：它下载并核对固定的 Z-Anatomy 源文件，用 Vanatome 原样保留的导出脚本导出，写上面三个文件，最后跑检查。只检查用 `python3 site/build/atlas/check-addon.py shoulder`（QC-09；CI 由 `tests/test_atlas_addon.py` 运行）。环境准备、清单字段和检查规则见 [site/build/atlas/README.md](../../../site/build/atlas/README.md)。不要手改 GLB 或 metadata，改清单后重新导出。附加模型与自带模型同为 `atlasVersion` 1.4.0、`buildId` `994e6cc8ffbb212e`、同一坐标系，所以 `src/vendor/composition.ts` 把它当作第三个模型接受；肩部页面在 `src/model.ts` 用 `loadAtlases(['shoulder'])` 载入它。

**斜方肌改名。** Z-Anatomy 把斜方肌两部分的名字弄反了：2026-10-09 实测（记录在 `atlas-addon.json` 的 `renameSourceObjects._why`），它叫 “Ascending part” 的网格从 C7 上方（项韧带、枕骨）走到锁骨外侧，按国际解剖学名词（Terminologia Anatomica）是降部（上斜方肌）；叫 “Descending part” 的网格从约 T12 走到肩胛冈内侧，是升部（下斜方肌）。清单用 `renameSourceObjects` 在导出前改正，所以 ID 按 TA：`trapezius-muscles-descending-part-of-trapezius-muscle-*` 是上斜方肌，`…-ascending-part-…` 是下斜方肌，`…-transverse-part-…` 是中斜方肌。provenance 的 `zAnatomyName` 保留原名；清单的位置检查（降部高过 C7 并接触锁骨，升部低于 C7、下端低于 T7 并接触肩胛骨）防止以后再弄反。

**名称、词条与链接。** 21 个部分的中英文名称在 `src/data.ts` 的 `anatomyNames` / `anatomyEnglish`；18 个肌肉词条在 `src/vocabulary.ts`（Trapezius 与上、中、下斜方肌，Triceps brachii 与 Long head of triceps 等），可用 `?term=<词条 id>` 打开，例如 `?term=trapezius`、`?term=upper-trapezius`、`?term=teres-major`。选中的部分没有自己的词条时（如胸大肌锁骨头、肱二头肌长头），词卡显示它所属整块肌肉的词条。已有的 `?term=`、`?point=` 链接使用的 ID 没有改。

### 图层与隐藏肌肉

- 图层栏：Bones · 骨骼、Rotator cuff · 肩袖、Deltoid · 三角肌 默认打开；More muscles · 更多肌肉 下的 Back · 背部、Chest · 胸部、Teres major · 大圆肌、Upper arm · 上臂 默认关闭。勾选后显示当前一侧的这组肌肉；点选词表、EXPLORE 条或穴位关联的肌肉时，它所在的组自动打开。
- 工具栏的 Hide muscles · 隐藏肌肉 一次隐藏全部肌肉、只留骨骼；按钮随即变成 Show muscles · 显示肌肉，再按恢复各组原来的勾选。隐藏时图层栏各组变灰。它和骨标模式用同一个开关：进入 Bone landmarks 时肌肉自动隐藏，按钮显示 Show muscles；勾选任一组、从词表或 EXPLORE 条选词、选穴位或切回 Anatomy / Acupoints 时肌肉重新显示。
- Acupoints 模式下 Depth probe · 深浅探针 打开时，探针经过的肌肉即使所在组关闭也保持显示（Hide muscles 仍隐藏全部肌肉）。
- 附加肌肉打开后标签较多：斜方肌、胸大肌、肱二头肌、肱三头肌各只标一个整块肌肉的名称，选中其中一部分时只标这一部分；放不下时按优先级显示，并在图层栏上方提示 “N of M labels fit the view”。

## 来源与许可

上游：[vixotic/Vanatome](https://github.com/vixotic/Vanatome)，固定于提交 [`8185b3fa46a1dbefdd907390918c57954fd9b816`](https://github.com/vixotic/Vanatome/tree/8185b3fa46a1dbefdd907390918c57954fd9b816)。引入文件清单见 [UPSTREAM.json](./UPSTREAM.json)。本项目在上游查看器基础上增加学习标注与中文界面。

查看器代码采用 MIT 许可；解剖资产由 Z-Anatomy 等上游材料衍生，遵循 CC BY-SA 4.0 及原始署名要求。肩部附加模型同样衍生自 Z-Anatomy（CC BY-SA 4.0，其模型又源自 BodyParts3D），用 Vanatome 的导出脚本（MIT）生成，按 CC BY-SA 4.0 发布；改动项写在资产许可和署名文件里，来源记录在 [UPSTREAM.json](./UPSTREAM.json) 的 `addons`。完整说明保留在 [代码许可](./public/licenses/LICENSE)、[资产许可](./public/licenses/ASSET-LICENSE.md) 与 [署名文件](./public/licenses/ATTRIBUTION.txt)。

## 几何核对

### 骨性结构辨认

点击 Humerus 自动展开近端六个骨标：肱骨头、大结节、小结节、结节间沟、解剖颈、外科颈。点击 Scapula 展开肩胛冈、下角、肩峰、冈上窝、冈下窝、肩峰前外侧和后外侧七个骨标。英文在前，中文释义跟随隐藏开关。

骨标使用原模型上的代表性表面点，共 26 个双侧位置；它们没有分割完整结构边界，简化肱骨网格中的沟和颈尤其只能提供区域提示。新增肱骨骨标列在独立骨标面板，现有 27 条词表及语音文件保持不变。

进入骨标模式会隐藏肌肉并单独显示该骨，可关闭 Isolate bone 查看周围骨骼；Whole bone / Close-up 在整骨和局部之间切换。选中骨头保留正常表面阴影。骨标切换复用同一场景，相机平滑移动；同骨切换保留手动观察角度和缩放，跨骨或显式视角按钮使用绕目标的旋转动画。

坐标与证据：`src/humerus-landmarks.json`、`src/scapula-landmarks.json`；骨面投射和检查记录在 `public/*-landmark-evidence.json`，可用 `scripts/calibrate-humerus-landmarks.mjs`、`scripts/calibrate-scapula-landmarks.mjs` 重现。

### 连续切换

肌肉、骨标、穴位、左右侧与全身视图共用同一个三维场景。只有明确的导航操作发送镜头请求；图层、显示模式、语言和标签开关保持观察位置。新请求从当前镜头位置继续，拖动可立即接管动画。前后和侧面按钮围绕当前焦点旋转，保留缩放；同一骨头内切换骨标及同模式切换穴位保留当前观察角度和距离。

骨标工具栏预留固定空间，词卡名称与读音区预留稳定高度，切换条目不会推动画布和词表按钮。来源说明的展开状态在切词时保留。

### 穴位学习参照

运行 `pnpm test:geometry` 可重现十个标记的验证：七方向射线奇偶与三角网格绕数必须一致，点须位于其关联肌肉内部、肩胛骨与肱骨外。此测试只证明模型几何归属。

- 内置位置与可见说明：`src/model-references.json`
- 骨标、局部截面和来源：`public/calibration-evidence.json`
- 本次几何验证结果：`public/geometry-validation.json`

### 深浅与周围结构

`public/acupoint-depth.json` 由 `scripts/compute-acupoint-depth.mjs` 从肌肉、骨骼和肩部附加模型三个 GLB 计算（三者的 SHA-256 记在 `modelFiles`）；改变参照点或模型后运行 `pnpm depth:compute` 重新生成，`pnpm test:depth` 检查文件是否为最新并核对层次顺序、参照点所在结构、左右对称及轴线经过参照点。该脚本不依赖 `node_modules`，并先重现 `geometry-validation.json` 中由 three.js 得到的全部射线计数与表面距离，以证明读取结果一致。

- 坐标约定经模型标志核对：+y 向上（胸骨柄高于胸骨体，C7 高于骶骨），+z 向前（胸骨体在 T4 前方），右侧 x < 0（`.r` 结构均在 x < 0，且与 +y 向上、+z 向前的右手坐标一致）。
- 探针轴线：先按记录的方向（SI11、SI12、SI9 自后方；LI15、TE14 自外侧）穿过参照点，再取该线首先遇到的模型外表面 2.5 cm 范围内的面积加权外法线，使轴线垂直于模型外表面并准确经过参照点。1.5–3 cm 取样半径的结果另记在 `axis.sensitivity`。
- 深度以厘米表示（原始模型米 × 100），从轴线上第一个建模表面起算。模型不含皮肤、皮下脂肪、筋膜、神经、血管、滑囊；肌肉来自自带模型和肩部附加模型，肋间肌等仍未建模；从皮肤量起的实际深度会更大。
- 周围结构为参照点到其他结构最近表面的距离（3 cm 内），方向按上下、内外、前后及沿探针深浅命名。原始网格在 LI15 等处互相穿插，重叠按模型显示。
- 这是模型学习参照，不是进针路径、进针方向或进针深度。

**加入肩部附加模型之后（2026-10-09）。** 深浅探针同时读取肩部附加模型（`z-anatomy-1.4.0-shoulder-addon.glb`），轴线穿过斜方肌、前锯肌和肱三头肌长头时会列为层次，附加肌肉也会出现在周围结构中。

- 秉风（SI12）的第一个建模表面现在是斜方肌，不再是冈上肌。原始模型中斜方肌各部的分界正好经过此处（离探针入点约 0.2–0.3 cm），所以只有 SI12 用 `patchScope: "muscle"`：轴线垂直于同侧整片斜方肌（三个网格），比原轴线转了约 5°。轴线依次经过斜方肌 → 冈上肌 → 肩胛骨 → 肩胛下肌 → 前锯肌 → 第 3 肋，参照点深 1.78 cm（原为 0.93 cm，因为深度 0 现在是斜方肌表面）。探针进入的是下斜方肌网格，但离中斜方肌网格只有 0.3 cm，而模型各部的分界只是近似（下部网格在中线向上到约 T2，资料写 T4 或 T5，见 `atlas-addon.json` 的 `mappingNotes`），所以第一层按整块斜方肌显示为 Trapezius · 斜方肌，层次说明写明进入的是哪个网格。
- 天宗（SI11）多了前锯肌一层（肩胛下肌之后、第 5 肋之前），肩贞（SI9）多了肱三头肌长头一层（小圆肌之后），停止原因改为 `unmodeled-gap`。这两个穴位的轴线和其余层次深度不变；肩髃（LI15）、肩髎（TE14）的层次不变。
- 天宗、秉风、肩贞另有 `sourceComparison`，把探针与资料中的层次描述对照（来源列在各穴，查阅于 2026-10-09），差异照实保留：秉风顺序一致；天宗处模型的斜方肌边缘离探针约 0.35 cm，恰好没有盖到探针；肩贞处探针从大圆肌（约 2.3 cm）和背阔肌（约 2.2 cm）上方经过，资料描述的路径更低。
- `pnpm test:geometry`（加 `--write` 时更新 `public/geometry-validation.json`）同时用 three.js 测量各参照点 3 cm 内的同侧附加模型网格，`pnpm test:depth` 用自带的 GLB 读取器重现这些测量（共 50 项，其中 20 项在附加模型网格上）。重新导出附加模型后先运行 `node scripts/validate-reference-geometry.mjs --write`，再运行 `pnpm depth:compute`，否则 `pnpm test:depth` 会因哈希和测量值改变而失败。

穴名采用 WHO 文献使用的罗马字名称及国际编号；它们是汉语拼音名称，发音使用普通话。SI11 和 SI12 的 WHO 印刷页码均为 93。

## 英语背词与读音

背词卡位于右侧顶部。`Listen` 播放、`Slow` 慢速播放，`Hide Chinese` 隐藏中文释义；`Word list` 选择词汇，或使用 Previous / Next 顺序练习。

英语采用美式读音参考，IPA 与重音拆读的来源保留在 `src/vocabulary.ts` 和词卡的读音依据中。大写音节表示重音辅助提示，不能代替 IPA；词组标音可能由单词读音组合，Merriam-Webster 条目按其标音转写。Supraspinatus 使用有来源的重音提示，没有补写未核实的完整 IPA。

发音文件保存在 `public/audio`，播放时不依赖在线语音服务（下面说的附加模型肌肉词除外）。目前 22 个英语词中，10 个已换成 OpenAI 的 Marin：Supraspinatus、Infraspinatus、Teres minor、Subscapularis、Deltoid、Acromial part、Clavicular part、Spinal part、Scapula、Clavicle。其余 12 个英语词暂用原来的 Samantha；5 个穴名保留普通话 Tingting。词卡按当前词的清单显示实际声音。所有音频均为合成发音，词典链接提供读音核对依据。

Marin 文件由 OpenAI.fm 页面生成并下载；本次在第 10 次下载后遇到页面每周下载上限。逐条来源、模型、实际生成参数及音频测量见 `public/audio/manifest.json`，未在页面显示的参数保留为 `null`。新文件名含内容哈希，避免继续使用旧的缓存音频。

补齐剩余 12 词的脚本只使用本机环境变量 `OPENAI_API_KEY`，默认只检查已有文件并列出缺项；加入 `--generate` 才调用官方语音 API。它保留已有 10 个下载文件及其来源，每生成一词即保存进度，全部完成后再导入并构建：

```sh
python3 scripts/generate-openai-pronunciation-audio.py --reuse .voice-staging/marin-downloads.json
python3 scripts/generate-openai-pronunciation-audio.py --reuse .voice-staging/marin-downloads.json --generate
python3 scripts/import-openai-pronunciation-audio.py .voice-staging/marin-complete.json --apply
pnpm build
```

仅在明确接受部分替换时，导入器才使用 `--allow-partial`；默认要求 22 个英语词齐全。旧的 `generate-pronunciation-audio.py` 不会覆盖已经包含 OpenAI 音频的清单。

附加模型的 18 个肌肉词还没有录音，不在 `public/audio/manifest.json` 里，上面的生成和导入脚本也只处理原有的 22 个词。这些词按 `Listen` / `Slow` 时由浏览器自带语音（Web Speech API 的 `speechSynthesis`，`en-US`，慢速 0.75 倍）朗读，词卡写 `Browser voice · 浏览器朗读`，音色和发音因设备而异；浏览器不支持时，词卡提示改用“读音依据”里的词典链接。它们的 IPA、重音拼读和词典链接与其他词一样写在 `src/vocabulary.ts`，词组的读音说明写在各词的 `pronunciationNote`。
