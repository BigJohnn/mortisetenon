# 可打印的榫卯 · Printable Joinery Atlas v0.9.0

本版把项目切成两条可以不同步前进的路径：**设计线**先冻结全书要实现的结构，**证据线**继续控制哪些打印与性能主张可以发布。Design Catalog v0.1 已确定 24 个基本榫卯、6 个综合作品和 4 个实验章；First Wave Content v0.1 已为首轮 10+3 补齐来源边界、设计提案、装配步骤、参数接口、CAD 交付物和实验债务。9 项作者决策已全部确认，首轮 10+3 不再等待设计取舍。实体实验暂缓，Gate A 仍未通过；`DESIGN_BRIEF` 或已有页面不等于 `PRINT_VERIFIED`。

本轮已补齐首批正文阅读入口：[book.html](book.html) 汇集全部 10+3，新增七篇榫卯与两篇作品正文。公共教学尺度、配合字段、坐标、接触面与输出规则见 [cad/teaching-spec.html](cad/teaching-spec.html)。新增九章为设计正文初稿，尚未新增 CAD 或物理验证；整条路线图并未完成。

## 本地浏览

不要直接双击 `index.html`。GLB 是由浏览器通过网络请求加载的，`file://` 会阻止这个请求。

```bash
npm run dev
```

无需先执行 `npm install`；该命令只调用系统自带的 Python 本地服务器。终端会显示地址，默认打开 [http://localhost:8000](http://localhost:8000)。从这里进入首页、直榫或燕尾榫页，3D 模型和交互控件都会正常工作。按 `Ctrl+C` 停止服务。

## 入口
- `book.html`：首批 10+3 正文阅读目录，新增九章可独立阅读与打印
- `cad/teaching-spec.html`：统一教学参数与输出约定 v0.1
- `content/manuscript_v0.1.json`：新增七篇榫卯、两篇作品的正文事实源
- `content/teaching_spec_v0.1.json`：十项教学尺度分组、配合字段和派生规则
- `tools/build_manuscript.py`：从内容源生成九章、阅读目录与公共规范，`--check` 检测漂移
- `tools/validate_manuscript.py`：校验首批覆盖、参数映射、本地链接与证据边界
- `index.html`：首页
- `design-catalog.html`：24+6 全书设计目录与实验债务
- `first-wave.html`：首轮 10+3 内容工作台，可筛选作者决策、基本榫卯和作品
- `joints/straight-tenon.html`：直榫
- `joints/dovetail.html`：燕尾榫
- `joints/keyed-tenon.html`：楔钉榫
- `works/baxian-table.html`：八仙桌综合案例（完整作品命题、四向实物阅读、CAD → 分盘 → 装配、证据边界与原型 02 清单）
- `labs/clearance.html`：Clearance Lab 实验章（定义、测量协议、fit map 判读、直榫迁移与记录表）
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
- `content/design_catalog_v0.1.json`：24 个基本榫卯、6 个综合作品、4 个实验章的机器可读设计真值
- `content/first_wave_v0.1.json`：首轮 10+3 的来源、结构提案、装配、参数、CAD 交付物、实验债务与 9 项已确认的作者决策
- `ASSET_CONTRACT.md`：CAD / STL / STEP / GLB / 图片 / print log 版本契约
- `assets/downloads/manifest.json`：公开下载资产的哈希与几何检查清单
- `assets/downloads/clearance-test-kit_print-log-template_v0.1.csv`、`assets/downloads/straight-tenon_print-log-template_v0.1.csv`：可离线填写的打印记录模板（由工具生成）
- `tools/print_log_spec.py`：从实验室页面反解表单定义，作为唯一的字段真值
- `tools/ingest_print_log.py`：校验打印记录、归档到 `content/print-logs/`、把资产升到 `PRINT_VERIFIED`
- `tools/validate_design_catalog.py`：校验 24 / 6 / 10+3 数量、8×3 家族分布、首轮内容完整性、作者决策状态、交叉引用与页面路径

## 这版最重要的变化
1. 新增 Design Catalog v0.1：最终纸书目标从模糊的“30–50 个案例”收敛为 **24 个基本榫卯 + 6 个综合作品**，另设 4 个横向实验章。
2. 24 个榫卯按本项目的 8 个教学家族组织，每类 3 个；这是一种编辑结构，不冒充传统工艺的唯一分类法。
3. 首批 10 个覆盖全部 8 个家族：现有直榫、燕尾榫、楔钉榫，加上夹头榫、插肩榫、粽角榫、龙凤榫加穿带、走马销、十字半搭接和破头楔。
4. 首批 3 个作品为框板收纳盒、夹头榫小案和八仙桌。八仙桌已定位到作者确认的 Onshape source microversion，读到 30 个实体和 6 个参数；连接列表仍须由接口几何审计，不能从照片或零件名倒推。
5. 资产契约新增“设计阶段不等于证据状态”：`CATALOG_SLOT`、`DESIGN_BRIEF`、`IMPLEMENTED` 只描述编辑进度；`DRAFT`、`GEOMETRY_VERIFIED`、`PRINT_VERIFIED`、`USER_REPRODUCED` 继续描述证据。
6. First Wave Content v0.1 把 10+3 从目录层推进到可审阅内容，并区分“来源已确认”“本轮设计提案”和“实验债务”。
7. 9 项作者决策均已确认并保留默认方案、确认结果和推进边界；夹头榫、破头楔、收纳盒与小案均可进入 CAD。
8. Roadmap v0.9 记录公共参数与首批正文已就位，夹头 / 插肩 CAD 为下一项；直榫实测、Clearance Kit、方向/承载/耐久实验仍在 Deferred 队列，所有证据门槛保持不变。

## 重建资产
```bash
blender --background --python tools/build_straight_tenon_assets.py -- \
  --input-dir cad/straight-tenon_v0.1_parts \
  --layout-stl assets/downloads/straight-tenon_c-sweep-print-layout_v0.1.stl \
  --glb assets/models/straight-tenon_assembled_v0.1.glb \
  --poster assets/images/straight-tenon/v0.1/exploded-01.webp
```
排版 STL 的输出是确定性的：重跑得到的文件与已发布版本 SHA-256 一致。网页需通过 HTTP 打开；开发时使用 `npm run dev`。

## 建议下一步
1. 公共教学接口 v0.1 与新增 7+2 正文初稿已完成；新增 CAD 按规范实现，局部榫区与推荐间隙不由编辑规范替代验证。
2. 先做夹头榫 / 插肩榫对照 CAD；走马销 / 十字半搭接可并行进入 CAD，再做粽角榫、龙凤榫加穿带和破头楔。
3. 为八仙桌 30 个源实体补接口 ID 和非空总装，逐项通过或驳回候选 joint_ids；随后建立命名发布版本。
4. 基本节点稳定后，为开放式 160 × 110 × 70 mm 框板收纳盒和 220 × 140 × 150 mm 夹头榫小案建立作品 CAD。
5. 恢复实验时从 Deferred 队列继续：直榫四档实测、Clearance Kit 首打，再按方向、承载和耐久成批验证。

目录校验：

```bash
npm run check:catalog
```

正文由结构化原稿生成静态 HTML，不依赖浏览器脚本读取内容。修改正文或参数规范后运行：

```bash
npm run build:book
npm run check:book
```

新增九篇正文直接使用稿件中的来源说明；概念示意图明确标注为非 CAD。燕尾、楔钉在首轮工作台中的错误 `GEOMETRY_VERIFIED` 标签已按既有章节与资产契约校正为 `DRAFT`。本轮没有读取 `.env`、新增 Onshape 文档或改动已发布几何。
