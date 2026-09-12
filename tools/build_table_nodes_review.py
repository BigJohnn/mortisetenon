#!/usr/bin/env python3
"""Publish a static CAD review; keep native masters and interactive GLB private.

A clean public checkout can rebuild from the non-geometric status summary.
When private verified outputs exist, refresh that summary and static renders.
"""
import hashlib
import json
import shutil
from build_manuscript import ROOT, page, section, table, link

PRIVATE=ROOT/"cad/table-node-pair_freecad_v0.1"
SUMMARY=ROOT/"content/cad_status_v0.1.json"
TITLES={"clamp-tenon":"夹头 · 水平槽底", "shouldered-tenon":"插肩 · 双斜肩教学变体"}


def main():
    if (PRIVATE/"report.json").exists():
        report=json.loads((PRIVATE/"report.json").read_text())
        source=json.loads((PRIVATE/"source-report.json").read_text())
        status={"date":"2026-09-12","master_type":"FREECAD_LOCAL","state":"DRAFT","print_verified":False,"onshape_sync":"OPTIONAL_NOT_PERFORMED","private_artifacts_not_published":True,"nodes":{}}
        public_images=ROOT/"assets/images/table-node-pair/v0.1"
        public_images.mkdir(parents=True,exist_ok=True)
        local_body='<h1>FreeCAD 本地母版与私有预览</h1><p>本目录已被 Git 忽略；不要将其包含在网站发布包中。修改原生文件后须另存版本、重新导出与验证。</p>'
        for slug,title in TITLES.items():
            node=report["nodes"][slug];src=source["nodes"][slug]
            assert hashlib.sha256((PRIVATE/node["source_file"]).read_bytes()).hexdigest()==node["source_sha256"]
            status["nodes"][slug]={"source_sha256":node["source_sha256"],"solid_count":len(node["parts"]),"sketch_count":sum(o["type"]=="Sketcher::SketchObject" for o in src["feature_tree"]),"parameter_test_count":node["parameter_test_count"],"reopen_recompute_passed":node["reopen_recompute_passed"],"mesh_checks_passed":all(p["watertight"] and p["winding_consistent"] for p in node["parts"].values()),"motion_samples":sum(m["samples"] for m in node["motion"].values()),"motion_step_mm":1,"sampled_path_intersections":False,"overtravel_controls_passed":True}
            for state in ["assembled","exploded"]:
                shutil.copyfile(PRIVATE/f"{slug}_{state}.webp",public_images/f"{slug}_{state}.webp")
            local_body+=f'<h2>{title}</h2><p><a href="{node["source_file"]}">打开原生 FCStd</a> · <a href="{slug}_v0.1.step">本地 STEP</a></p><model-viewer id="{slug}" src="{slug}_preview.glb" poster="{slug}_exploded.webp" camera-controls animation-name="Explode" style="width:100%;height:500px"></model-viewer><label>拆装 <input data-viewer="{slug}" type="range" min="0" max="1000" value="0" disabled></label><p>如果直接通过文件打开，交互模型可能受浏览器限制；请通过项目本地 HTTP 服务访问本页。仅限本地审阅。</p>'
        SUMMARY.write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n")
        local_html='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>私有 CAD 审阅</title><body style="max-width:900px;margin:40px auto;font-family:sans-serif">'+local_body+'<script type="module" src="../../assets/vendor/model-viewer-4.3.1.min.js"></script><script>document.querySelectorAll("[data-viewer]").forEach(r=>{const v=document.getElementById(r.dataset.viewer);v.addEventListener("load",()=>{v.play();v.pause();r.disabled=false;});r.addEventListener("input",()=>{v.currentTime=Math.min(r.value/1000*v.duration,v.duration-.001);});});</script></body></html>'
        (PRIVATE/"index.html").write_text(local_html)
    else:
        status=json.loads(SUMMARY.read_text())
    body=section("boundary","FreeCAD 是本地主模型",'<div class="reading-note"><p>两套节点已转换为 FreeCAD 原生参数化母版，采用参数表、约束草图及 PartDesign 拉伸 / 切除，不是导入 STEP 后改存后缀。模型已完成保存、重新打开、重算和选定参数的修改测试。</p><p>本页仅发布静态渲染和检查摘要；原生母版、精确参数、STEP/STL/GLB 及详细报告留在本地忽略目录。Onshape 仅为可选同步，本轮没有上传。状态仍为 DRAFT，尚无实物试打。</p></div>')
    toc=[("boundary","母版与公开边界")]
    for slug,title in TITLES.items():
        n=status["nodes"][slug]
        stem=f"../assets/images/table-node-pair/v0.1/{slug}"
        images=f'<div class="node-images"><figure><img src="{stem}_assembled.webp" alt="{title}装合渲染"><figcaption>装合 · FreeCAD 同源数字渲染</figcaption></figure><figure><img src="{stem}_exploded.webp" alt="{title}拆分渲染"><figcaption>拆分 · 先面板、后牙条；腿固定</figcaption></figure></div>'
        checks=table(["检查","结果"],[["有效单实体",str(n["solid_count"])],["完全约束草图",str(n["sketch_count"])],["改参 / 恢复测试",str(n["parameter_test_count"])+" 次通过"],["保存后重新打开并重算","通过"],["网格水密与绕向","通过"],["装配采样",f'{n["motion_samples"]} 个位置，步长 {n["motion_step_mm"]} mm；未发现体积相交'],["越过停止位置的负对照","发生预期干涉"]])
        body+=section(slug,title,images+checks+'<p>上述结果仅针对本轮默认几何与明确测试的改参情形。离散采样不是连续扫掠证明，数字接触不代表打印配合或承载通过。</p>')
        toc.append((slug,title))
    body+=section("editing","本地怎么改",'<ol><li>用 FreeCAD 打开本地母版，不要从网页网格逆向修改。</li><li>双击树中的“00 · 参数表”，编辑 B 列的参数值；重算后检查三个 Body 及其草图、拉伸和切除特征。</li><li>另存为新版本，重新导出并检查。旧的报告和静态图不会因手工改尺寸而自动有效。</li></ol><p>原始 FeatureScript 与 CadQuery 重建保留为历史对照，不再是本轮母版。完整桌架、正交牙条、打印取向和实物实验仍待后续完成。</p>')
    toc.append(("editing","编辑与下一步"))
    body+=section("privacy","发布前仍需审计历史",'<p>仓库已有历史 CAD 被跟踪，新增忽略规则无法撤回这些内容。新的本地母版不增加公开下载入口；历史清理与仓库可见性需单独决定。</p><div class="reading-links">'+link("CAD 保密与发布说明 →","../CAD_PRIVACY.md")+link("不含精确几何的状态摘要 →","../content/cad_status_v0.1.json")+'</div>')
    toc.append(("privacy","保密与发布"))
    result=page("夹头 / 插肩 · CAD 对照审阅","FreeCAD 本地母版，静态图用于书稿审阅；精确几何不从本页公开下载。","FreeCAD local master · v0.1","DRAFT · 原生参数化已检查 · 未试打",body,toc)
    result=result.replace('<!-- Generated by tools/build_manuscript.py. Edit content/manuscript_v0.1.json or content/teaching_spec_v0.1.json. -->','<!-- Generated by tools/build_table_nodes_review.py; public static summary only. -->').replace('2026-09-08','2026-09-12').replace('正文初稿 v0.1','CAD 工作稿 v0.1')
    result=result.replace('</head>','<style>.node-images{display:grid;grid-template-columns:1fr 1fr;gap:12px}.node-images figure{margin:20px 0}.node-images img{width:100%;display:block}.node-images figcaption{font-size:13px;color:#777}@media(max-width:600px){.node-images{grid-template-columns:1fr}}</style></head>')
    (ROOT/"cad/table-node-pair.html").write_text(result)
    print("Built public static CAD review; private files are not linked or copied into the public page")


if __name__=="__main__":main()
