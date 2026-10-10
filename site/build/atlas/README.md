# 章节 3D 附加模型（共用导出脚本）

自带的 `z-anatomy-1.4.0-muscular/skeletal.glb` 是 Vanatome 的演示子集，很多肌肉没有。这里的脚本从同一份 Z-Anatomy 源文件导出某一章需要的肌肉，生成一个**附加模型**，和现有模型放在同一个坐标系里；现有模型、穴位和骨性标志数据都不动。

每一章只需要一份清单：`library/<章>/3d/atlas-addon.json`。别的章节照抄肩部的清单改肌肉名即可，脚本不用改。

## 文件

| 文件 | 作用 |
| --- | --- |
| `source.json` | 固定输入：Z-Anatomy 仓库 commit、zip 和 `Startup.blend` 的 SHA-256、导出脚本的 SHA-256、Blender 版本、坐标换算 |
| `export_batch.py` | Vanatome 的导出脚本，原样保留（MIT），不要改；测试会核对 SHA-256 |
| `run_export.py` | 在能 `import bpy` 的 Python 里打开 .blend（禁用其中的脚本），按清单改名，再运行导出脚本 |
| `build-addon.py` | 一条命令完成：下载并核对源文件 → 导出 → 写 GLB、metadata、provenance → 跑检查 |
| `check-addon.py` / `atlaslib.py` | 纯 Python 检查（CI 也跑，`tests/test_atlas_addon.py`） |

## 一章的清单 `atlas-addon.json`

- `output`：GLB、metadata、provenance 写到 3D 程序 `public/` 下的路径（相对 `library/shoulder/3d/`）。
- `batch.groups`：每组一块肌肉，`sourceObjects` 写 Z-Anatomy 里的网格名（左右各一个，`.l` / `.r`）。组 id 和网格名决定结构 ID，例如 `teres-major-muscles-teres-major-muscle-right`。
- `renameSourceObjects`：Z-Anatomy 网格名和解剖不符时，导出前改名，让 ID 按国际解剖学名词。肩部的斜方肌上、下两部在源文件里名字是反的，就是用这一项改正的。provenance 里保留原名。
- `checks`：按实测位置核对每块肌肉，`{side}` 会分别换成左右。规则有 `topAbove`、`topBelow`、`bottomBelow`、`bottomAbove`（比较上下端和某块骨的上下端）和 `overlaps`（包围盒相接，`tolerance` 为允许的间隙，单位米）。骨名用骨骼模型里的源网格名，如 `Humerus.l`、`Vertebra C7`。
- `mappingNotes`：名字和位置不一致、或需要说明的地方写在这里。

不要按名字猜位置：先导出，看 provenance 里每块网格的上下范围，再写检查。检查不过就不能用。

## 运行

需要 Python 3.13 和 `bpy==5.2.0`（Linux 和 macOS arm64 都有 wheel，不需要另装 Blender）：

```sh
python3.13 -m venv .venv-bpy
.venv-bpy/bin/pip install bpy==5.2.0
python3 site/build/atlas/build-addon.py <章> --blender-python .venv-bpy/bin/python
python3 site/build/atlas/check-addon.py <章>
```

第一次运行会下载 Z-Anatomy.zip（约 87 MB）并解出 `Startup.blend`（约 307 MB）到 `~/.cache/dpt-study/z-anatomy/`，校验值不符就停止。导出约 1–2 分钟。

## 导出之后

附加模型只是文件。要在 3D 页面里出现，还要：在 3D 程序里载入它（肩部见 `src/model.ts` 的 `loadAtlases`），给新结构配名称、词条和读音，并在正文里把 3D 链接接上（AN-40、AN-41）。新增肌肉或模型文件要先问用户（AN-43）。附加模型本身的规则是 AN-44，发布前的检查是 QC-09（`check-addon.py` 无报错退出），见 `standards/library/rules.md` 和 `standards/library/checklist.md`。

## 许可

Z-Anatomy 模型为 CC BY-SA 4.0（源自 BodyParts3D），导出的附加模型同样按 CC BY-SA 4.0 发布并署名；`export_batch.py` 为 MIT（Copyright (c) 2026 Vanatome contributors），许可全文和来源地址见同目录的 [`LICENSE-export_batch.txt`](./LICENSE-export_batch.txt)（与 `library/shoulder/3d/public/licenses/LICENSE` 相同）。
