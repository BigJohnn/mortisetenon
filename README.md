# 可打印的榫卯 · Printable Joinery Atlas v0.7

本版把项目切成两条可以不同步前进的路径：**设计线**先冻结全书要实现的结构，**证据线**继续控制哪些打印与性能主张可以发布。Design Catalog v0.1 已确定 24 个基本榫卯、6 个综合作品和 4 个实验章；首轮选择 10+3，记录教学目的、装配动作、关键参数、作品映射和未来实验问题。实体实验暂缓，Gate A 仍未通过；`DESIGN_BRIEF` 或已有页面不等于 `PRINT_VERIFIED`。

## 本地浏览

不要直接双击 `index.html`。GLB 是由浏览器通过网络请求加载的，`file://` 会阻止这个请求。

```bash
npm run dev
```

无需先执行 `npm install`；该命令只调用系统自带的 Python 本地服务器。终端会显示地址，默认打开 [http://localhost:8000](http://localhost:8000)。从这里进入首页、直榫或燕尾榫页，3D 模型和交互控件都会正常工作。按 `Ctrl+C` 停止服务。

## 入口
- `index.html`：首页
- `design-catalog.html`：24+6 全书设计目录、首批 10+3 简报与实验债务
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
- `ASSET_CONTRACT.md`：CAD / STL / STEP / GLB / 图片 / print log 版本契约
- `assets/downloads/manifest.json`：公开下载资产的哈希与几何检查清单
- `assets/downloads/clearance-test-kit_print-log-template_v0.1.csv`、`assets/downloads/straight-tenon_print-log-template_v0.1.csv`：可离线填写的打印记录模板（由工具生成）
- `tools/print_log_spec.py`：从实验室页面反解表单定义，作为唯一的字段真值
- `tools/ingest_print_log.py`：校验打印记录、归档到 `content/print-logs/`、把资产升到 `PRINT_VERIFIED`
- `tools/validate_design_catalog.py`：校验 24 / 6 / 10+3 数量、8×3 家族分布、交叉引用与页面路径

## 这版最重要的变化
1. 新增 Design Catalog v0.1：最终纸书目标从模糊的“30–50 个案例”收敛为 **24 个基本榫卯 + 6 个综合作品**，另设 4 个横向实验章。
2. 24 个榫卯按本项目的 8 个教学家族组织，每类 3 个；这是一种编辑结构，不冒充传统工艺的唯一分类法。
3. 首批 10 个覆盖全部 8 个家族：现有直榫、燕尾榫、楔钉榫，加上夹头榫、插肩榫、粽角榫、龙凤榫加穿带、走马销、十字榫搭接和破头楔。
4. 首批 3 个作品为框板收纳盒、夹头榫小案和八仙桌。八仙桌的连接列表仍是候选映射，必须由冻结 CAD / BOM 审计，不能从照片或名称倒推。
5. 资产契约新增“设计阶段不等于证据状态”：`CATALOG_SLOT`、`DESIGN_BRIEF`、`IMPLEMENTED` 只描述编辑进度；`DRAFT`、`GEOMETRY_VERIFIED`、`PRINT_VERIFIED`、`USER_REPRODUCED` 继续描述证据。
6. Roadmap v0.7 改为双轨：设计线现在推进 10+3；直榫实测、Clearance Kit、方向/承载/耐久实验进入 Deferred 队列，但所有证据门槛保持不变。

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
1. 逐项审计首批新增七种结构的名称、机制、应用和解释边界；出版社目录只证明名称进入候选池，不替代结构研究。
2. 冻结首批十种结构共用的教学尺度、间隙字段、接触面、装配轴和导出约定。
3. 先做夹头榫 / 插肩榫对照 CAD，再做粽角榫 / 十字榫搭接 / 走马销，最后做龙凤榫加穿带 / 破头楔。
4. 基本节点稳定后，为框板收纳盒和夹头榫小案建立 BOM、闭环尺寸与装配依赖。
5. 恢复实验时从 Deferred 队列继续：直榫四档实测、Clearance Kit 首打，再按方向、承载和耐久成批验证。

目录校验：

```bash
npm run check:catalog
```
