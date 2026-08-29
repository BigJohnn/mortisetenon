# 可打印的榫卯 · Printable Joinery Atlas v0.5

本版把直榫资产包**接回它的几何源**，并为即将到手的实打数据修好入口：Onshape 版本已冻结并登记，STEP 补齐了 STEP / STL / GLB 三格式；打印记录升到 schema v0.2，测试块与直榫各有一套表单，导出的 JSON 由 `tools/ingest_print_log.py` 校验后才允许进仓库。Clearance Kit 与直榫 C sweep 的首轮实打正在进行中。

## 入口
- `index.html`：首页
- `joints/straight-tenon.html`：直榫
- `joints/dovetail.html`：燕尾榫
- `joints/keyed-tenon.html`：楔钉榫
- `labs/clearance.html`：Clearance Lab
- `cad/index.html`：三个 MVP 榫卯 + Clearance Kit 的参数化 CAD 规格
- `cad/clearance_test_kit_v0.1.scad`：可编辑 OpenSCAD 源码
- `cad/straight-tenon_v0.1_parts/`：直榫 C sweep 的零件 STL 快照（构建输入）
- `assets/downloads/clearance_test_kit_v0.1.stl`：首个真实可打印模型
- `assets/downloads/straight-tenon_c-sweep-print-layout_v0.1.stl`：直榫 C sweep 打印排版
- `assets/downloads/straight-tenon_v0.1.step`：直榫 STEP AP242 交换件（5 个实体，单位为米）
- `assets/models/straight-tenon_assembled_v0.1.glb`：直榫拆装动画（剪辑 `Explode`，2.4 s）
- `assets/images/straight-tenon/v0.1/exploded-01.webp`：爆炸图（动画最后一帧）
- `tools/build_straight_tenon_assets.py`：由零件 STL 一次生成上述三个导出件
- `research/sources.html`：研究来源与版权边界
- `content/research_pack_v0.3.json`：结构化研究 + CAD 数据
- `ASSET_CONTRACT.md`：CAD / STL / STEP / GLB / 图片 / print log 版本契约
- `assets/downloads/manifest.json`：公开下载资产的哈希与几何检查清单
- `assets/downloads/clearance-test-kit_print-log-template_v0.1.csv`、`assets/downloads/straight-tenon_print-log-template_v0.1.csv`：可离线填写的打印记录模板（由工具生成）
- `tools/print_log_spec.py`：从实验室页面反解表单定义，作为唯一的字段真值
- `tools/ingest_print_log.py`：校验打印记录、归档到 `content/print-logs/`、把资产升到 `PRINT_VERIFIED`

## 这版最重要的变化
1. 直榫几何源冻结为 Onshape 版本 `straight-tenon v0.1` 并登记进 manifest。链接指向版本（`/v/`）而不是工作区（`/w/`）：工作区会随编辑漂移，那样发布件就不可复现；工作区链接另存为 `source.workspace_url` 供继续建模。
2. 补齐 STEP AP242 导出（5 个实体，逐件包围盒核对），直榫现在 STEP / STL / GLB 三格式齐全。Onshape 的 STEP 固定写 SI 米，manifest 显式标注 `"units": "m"`，避免与包内其它 mm 派生件混用。
3. 打印记录升到 schema v0.2：Clearance Lab 拆成两套表单（测试块 / 直榫），直榫多记拔出力与榫肩贴合；字段从 `peg_/socket_` 改名为 `male_/female_`，两类资产共用同一组列名。
4. 新增 `tools/print_log_spec.py` + `tools/ingest_print_log.py`：表单定义从页面反解，校验、归档和 `PRINT_VERIFIED` 升级都走同一份真值，CSV 模板也由工具生成，纸面记录不会和网页表单对不上。

## 重建资产
```bash
blender --background --python tools/build_straight_tenon_assets.py -- \
  --input-dir cad/straight-tenon_v0.1_parts \
  --layout-stl assets/downloads/straight-tenon_c-sweep-print-layout_v0.1.stl \
  --glb assets/models/straight-tenon_assembled_v0.1.glb \
  --poster assets/images/straight-tenon/v0.1/exploded-01.webp
```
排版 STL 的输出是确定性的：重跑得到的文件与已发布版本 SHA-256 一致。网页需通过 HTTP 打开（例如 `python3 -m http.server`），`file://` 下浏览器会拦截 GLB 加载。

## 建议下一步
1. 取回本轮打印件，在 `labs/clearance.html#record` 分别记录测试块与直榫的四档结果，导出 JSON。
2. `python3 tools/ingest_print_log.py --check <导出的 json>` 先校验，通过后去掉 `--check` 归档并升级 evidence state。
3. 比较 Clearance Kit 与直榫 C sweep 的趋势，判断"测试块 → 结构件"是否一致。
4. Gate A 通过后，把燕尾榫 v0.2 从 Onshape 导出成正式资产包，替换 `assets/downloads/` 里的 placeholder。
