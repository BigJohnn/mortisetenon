# 可打印的榫卯 · Printable Joinery Atlas v0.4

本版把直榫从"规格文字"推到了**第一个走完全链路的资产包**：Onshape 参数化源 → 打印排版 STL → 拆装动画 GLB → 爆炸图渲染，三个导出口共用同一份零件位姿。Clearance Kit 与直榫 C sweep 的首轮实打正在进行中。

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
- `assets/models/straight-tenon_assembled_v0.1.glb`：直榫拆装动画（剪辑 `Explode`，2.4 s）
- `assets/images/straight-tenon/v0.1/exploded-01.webp`：爆炸图（动画最后一帧）
- `tools/build_straight_tenon_assets.py`：由零件 STL 一次生成上述三个导出件
- `research/sources.html`：研究来源与版权边界
- `content/research_pack_v0.3.json`：结构化研究 + CAD 数据
- `ASSET_CONTRACT.md`：CAD / STL / STEP / GLB / 图片 / print log 版本契约
- `assets/downloads/manifest.json`：公开下载资产的哈希与几何检查清单
- `assets/downloads/clearance_test_log_template.csv`：可离线填写的打印记录模板

## 这版最重要的变化
1. 直榫 C sweep v0.1 建模完成（C = 0.20 / 0.30 / 0.40 / 0.50 mm），打印排版 STL 通过壳数与流形检查，已在打印。
2. 直榫页接入真实 GLB：可旋转、缩放，并用滑块手动拖动整个拆装过程，动画与下载件同版本快照。
3. 爆炸图、拆装动画、打印排版由 `tools/build_straight_tenon_assets.py` 一次产出，共用同一份零件位姿，不会互相漂移。
4. manifest 新增 `straight-tenon@v0.1`：构建输入、三个导出件、动画元数据与几何检查全部留档。

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
1. 取回本轮打印件，在 `labs/clearance.html#record` 记录四档装配手感、卡尺尺寸和打印条件，导出 JSON。
2. 比较 Clearance Kit 与直榫 C sweep 的趋势，判断"测试块 → 结构件"是否一致。
3. 把 print log 回填进 manifest，两份资产才能从 `GEOMETRY_VERIFIED` 升到 `PRINT_VERIFIED`。
4. 补齐直榫的 Onshape 文档链接与 STEP 导出（manifest 中 `document_url` 目前为 null）。
5. Gate A 通过后，再建/打燕尾与楔钉榫。
