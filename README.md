# 可打印的榫卯 · Printable Joinery Atlas v0.3.1

本版完成 Decision 001：第三个 MVP 案例选择 **A · 楔钉榫**，并从内容研究进入首轮 CAD / 打印验证。

## 入口
- `index.html`：首页
- `joints/straight-tenon.html`：直榫
- `joints/dovetail.html`：燕尾榫
- `joints/keyed-tenon.html`：楔钉榫
- `labs/clearance.html`：Clearance Lab
- `cad/index.html`：三个 MVP 榫卯 + Clearance Kit 的参数化 CAD 规格
- `cad/clearance_test_kit_v0.1.scad`：可编辑 OpenSCAD 源码
- `assets/downloads/clearance_test_kit_v0.1.stl`：首个真实可打印模型
- `research/sources.html`：研究来源与版权边界
- `content/research_pack_v0.3.json`：结构化研究 + CAD 数据
- `ASSET_CONTRACT.md`：CAD / STL / STEP / GLB / 图片 / print log 版本契约
- `assets/downloads/manifest.json`：公开下载资产的哈希与几何检查清单
- `assets/downloads/clearance_test_log_template.csv`：可离线填写的打印记录模板

## 这版最重要的变化
1. Roadmap 改为 evidence-first：真实打印与直榫迁移验证是当前 Gate。
2. 建立资产契约与发布 manifest；Clearance STL v0.1 已通过哈希、尺寸、壳数和流形检查。
3. Clearance Lab 可在浏览器本地保存草稿，并导出字段一致的 JSON / CSV。
4. 下一步不扩内容数量：先完成 Clearance 首轮实打，再生成直榫 C sweep。

## 建议下一步
1. 打印 `clearance_test_kit_v0.1.stl`。
2. 在 `labs/clearance.html#record` 记录四档装配手感、卡尺尺寸和打印条件，导出 JSON。
3. 用结果确定直榫的 C sweep，并验证测试块结果能否迁移到真实榫卯几何。
4. Gate A 通过后，再建/打燕尾与楔钉榫。
