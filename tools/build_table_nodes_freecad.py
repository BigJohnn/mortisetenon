#!/usr/bin/env python3
"""Build two standalone native FreeCAD masters; run inside FreeCAD Python.

Only Spreadsheet, Sketcher, PartDesign Body/Pad/Pocket objects are used. No
FeaturePython proxy, imported STEP base, external link or add-on is required.
Existing masters are never overwritten: use an empty --output directory to
experiment. All exports are made after closing and reopening the saved FCStd.
"""
from pathlib import Path
import argparse
import hashlib
import itertools
import json
import math
import sys
import FreeCAD as App
import Part
import Sketcher
import MeshPart

ROOT=Path(__file__).resolve().parents[1]
INITIAL=json.loads((ROOT/"cad/table-node-pair_parameters_v0.1.json").read_text())["parameters"]
COLORS={"Leg":(0.73,0.42,0.27),"Apron":(0.84,0.65,0.40),"Top":(0.73,0.76,0.71)}
LABELS={"stock":"腿方截面", "legLength":"腿展示长度", "apronLength":"牙条长度", "apronThickness":"牙条厚度", "apronHeight":"牙条高度", "topWidth":"面板宽度", "topThickness":"面板厚度", "tenonWidth":"顶榫宽度", "tenonThickness":"顶榫厚度", "tenonHeight":"顶榫高度", "fit":"顶榫总间隙（试验值）", "slotFit":"夹头槽总间隙（插肩不使用）", "endGap":"非承压端部避让", "spread":"插肩每侧展开量"}
CELLS={key:f"B{i}" for i,key in enumerate(INITIAL,2)}


def parameters(doc):
    sheet=doc.addObject("Spreadsheet::Sheet","Params")
    sheet.Label="00 · 参数表（编辑 B 列，单位 mm）"
    for cell,value in {"A1":"参数", "B1":"值 / mm", "C1":"说明"}.items():sheet.set(cell,value)
    for i,(key,value) in enumerate(INITIAL.items(),2):
        sheet.set(f"A{i}",key);sheet.set(f"B{i}",f"{value} mm");sheet.setAlias(f"B{i}",key);sheet.set(f"C{i}",LABELS[key])
    sheet.set("A18","说明");sheet.set("B18","DRAFT / 未试打")
    sheet.set("A19","肩角");sheet.set("B19","=atan(B15/B6)")
    sheet.set("C19","相对竖直；spread / apronHeight")
    sheet.set("A21","编辑规则");sheet.set("B21","仅 B2:B15 为初始参数；需满足尺寸边界")
    sheet.setColumnWidth("A",150);sheet.setColumnWidth("B",145);sheet.setColumnWidth("C",290)
    doc.recompute()
    return sheet


def scalar(doc,expression):
    return float(doc.Params.evalExpression(expression).Value)


def polygon(doc,body,name,loops,plane="XY",offset="0 mm"):
    sketch=body.newObject("Sketcher::SketchObject",name)
    if plane=="YZ":
        sketch.Placement=App.Placement(App.Vector(0,0,0),App.Rotation(App.Vector(1,1,1),120))
        sketch.setExpression("Placement.Base.x",offset)
    else:sketch.setExpression("Placement.Base.z",offset)
    for points in loops:
        coordinates=[(scalar(doc,x),scalar(doc,y)) for x,y in points]
        start=sketch.GeometryCount
        for i,(x,y) in enumerate(coordinates):
            xx,yy=coordinates[(i+1)%len(points)]
            sketch.addGeometry(Part.LineSegment(App.Vector(x,y,0),App.Vector(xx,yy,0)),False)
        for i,(x,y) in enumerate(points):
            edge=start+i
            sketch.addConstraint(Sketcher.Constraint("Coincident",edge,2,start+(i+1)%len(points),1))
            for axis,expression in [("X",x),("Y",y)]:
                value=scalar(doc,expression)
                if abs(value)<1e-10:
                    # All zero coordinates in these profiles are literal datum
                    # coordinates, never parameters which happen to be zero.
                    assert expression=="0 mm",expression
                    sketch.addConstraint(Sketcher.Constraint("PointOnObject",edge,1,-2 if axis=="X" else -1))
                else:
                    index=sketch.addConstraint(Sketcher.Constraint("Distance"+axis,edge,1,value))
                    sketch.setExpression(f"Constraints[{index}]",expression)
    doc.recompute()
    assert sketch.FullyConstrained,(name,"underconstrained sketch")
    return sketch


def rectangle(x0,y0,x1,y1):return [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]


def feature(doc,body,kind,name,sketch,length,reverse=False):
    previous=body.Tip
    obj=body.newObject("PartDesign::"+kind,name)
    obj.Profile=sketch
    obj.setExpression("Length",length)
    obj.Reversed=reverse
    obj.Refine=True
    doc.recompute()
    if obj.Shape.isNull() or not obj.Shape.isValid() or len(obj.Shape.Solids)!=1:
        raise RuntimeError(f"{name}: invalid {kind}: {obj.State}")
    sketch.Visibility=False
    if previous:previous.Visibility=False
    obj.Visibility=True
    return obj


def build(slug,shouldered):
    doc=App.newDocument(slug.replace("-","_"))
    doc.Label=("插肩榫 · 双斜肩教学变体" if shouldered else "夹头榫 · 三件教学节点")+" v0.1"
    parameters(doc)
    p=lambda key:"Params."+key
    w,h,t,l=map(p,["stock","apronHeight","apronThickness","apronLength"])
    a=f"{t}/2";b=f"{a}+{p('spread')}"
    bodies={}
    for name in COLORS:
        body=doc.addObject("PartDesign::Body",name)
        body.Label={"Leg":"01 · 腿足 Leg", "Apron":"02 · 牙条 Apron", "Top":"03 · 面板 Top"}[name]
        bodies[name]=body
    leg=bodies["Leg"]
    sk=polygon(doc,leg,"LegSection",[rectangle(f"-{w}/2",f"-{w}/2",f"{w}/2",f"{w}/2")],offset=f"-{p('legLength')}")
    feature(doc,leg,"Pad","LegStock",sk,p("legLength"))
    twins=[]
    for side in [-1,1]:
        cy=f"({side}*({w}/2-2 mm))"
        twins.append(rectangle(f"-{p('tenonWidth')}/2",f"{cy}-{p('tenonThickness')}/2",f"{p('tenonWidth')}/2",f"{cy}+{p('tenonThickness')}/2"))
    sk=polygon(doc,leg,"TwinTenonProfile",twins)
    feature(doc,leg,"Pad","TwinTopTenons",sk,p("tenonHeight"))
    if shouldered:
        points=[(f"-({a})",f"-{h}-{p('endGap')}"),(a,f"-{h}-{p('endGap')}"),(a,f"-{h}"),(b,"0 mm"),(b,f"{p('tenonHeight')}+1 mm"),(f"-({b})",f"{p('tenonHeight')}+1 mm"),(f"-({b})","0 mm"),(f"-({a})",f"-{h}")]
    else:points=rectangle(f"-({a})-{p('slotFit')}/2",f"-{h}",f"{a}+{p('slotFit')}/2",f"{p('tenonHeight')}+1 mm")
    sk=polygon(doc,leg,"ApronSlotProfile",[points],"YZ",f"-{w}/2-1 mm")
    feature(doc,leg,"Pocket","ApronSlot",sk,f"{w}+2 mm",True)
    apron=bodies["Apron"]
    sk=polygon(doc,apron,"ApronSection",[rectangle(f"-{l}/2",f"-({a})",f"{l}/2",a)],offset=f"-{h}")
    feature(doc,apron,"Pad","ApronStock",sk,h)
    if shouldered:
        sk=polygon(doc,apron,"InclinedHeadProfile",[[(f"-({a})",f"-{h}"),(a,f"-{h}"),(b,"0 mm"),(f"-({b})","0 mm")]],"YZ",f"-{w}/2")
        feature(doc,apron,"Pad","IntegratedShoulderHead",sk,w)
    top=bodies["Top"]
    sk=polygon(doc,top,"PanelSection",[rectangle(f"-{l}/2",f"-{p('topWidth')}/2",f"{l}/2",f"{p('topWidth')}/2")])
    feature(doc,top,"Pad","PanelStock",sk,p("topThickness"))
    holes=[]
    for side in [-1,1]:
        cy=f"({side}*({w}/2-2 mm))"
        hw=f"({p('tenonWidth')}+{p('fit')})/2";ht=f"({p('tenonThickness')}+{p('fit')})/2"
        holes.append(rectangle(f"-({hw})",f"{cy}-({ht})",hw,f"{cy}+({ht})"))
    sk=polygon(doc,top,"BlindMortiseProfile",holes)
    feature(doc,top,"Pocket","TwinBlindMortises",sk,f"{p('tenonHeight')}+{p('endGap')}",True)
    for name,body in bodies.items():
        body.addProperty("App::PropertyString","Evidence","Joinery").Evidence="DRAFT / DIGITAL CHECK ONLY / NOT PRINT VERIFIED"
        body.addProperty("App::PropertyString","InterfaceNotes","Joinery")
        body.InterfaceNotes={"Leg":"IF-TOP: Z=0 stop; IF-APRON: inclined faces" if shouldered else "IF-TOP: Z=0 stop; IF-APRON: horizontal floor", "Apron":"Install first: translation -Z 48 mm", "Top":"Install second: translation -Z 96 mm; blind mortise end gap"}[name]
        if App.GuiUp:
            body.ViewObject.ShapeColor=COLORS[name];body.Tip.ViewObject.ShapeColor=COLORS[name]
    doc.recompute()
    return doc


def snapshot(doc):
    return {key:float(getattr(doc.Params,key).Value) for key in INITIAL}


def expected(p,shouldered):
    w,h,t,l=(p[k] for k in ["stock","apronHeight","apronThickness","apronLength"])
    opening=t*h+p["spread"]*h+t*p["endGap"] if shouldered else (t+p["slotFit"])*h
    return {"Leg":w*w*p["legLength"]+2*p["tenonWidth"]*p["tenonThickness"]*p["tenonHeight"]-w*opening,
        "Apron":l*t*h+(w*p["spread"]*h if shouldered else 0),
        "Top":l*p["topWidth"]*p["topThickness"]-2*(p["tenonWidth"]+p["fit"])*(p["tenonThickness"]+p["fit"])*(p["tenonHeight"]+p["endGap"])}


def check(doc,shouldered):
    doc.recompute()
    p=snapshot(doc)
    volumes=expected(p,shouldered)
    for obj in doc.Objects:
        assert not any(s in {"Invalid","Error"} for s in obj.State),(obj.Name,obj.State)
        if obj.TypeId=="Sketcher::SketchObject":assert obj.FullyConstrained,(obj.Name,"unconstrained")
    for name,v in volumes.items():
        shape=doc.getObject(name).Shape
        assert shape.isValid() and len(shape.Solids)==1,name
        assert abs(shape.Volume-v)<1e-5,(name,shape.Volume,v)
    return volumes


def parameter_tests(doc,shouldered):
    results=[]
    cases=[("legLength",104),("apronThickness",9),("fit",0.5),("endGap",0.6),("spread",3)]
    if not shouldered:cases.append(("slotFit",0.5))
    for key,value in cases:
        original=INITIAL[key]
        doc.Params.set(CELLS[key],f"{value} mm")
        volumes=check(doc,shouldered)
        results.append({"parameter":key,"value_mm":value,"volumes_mm3":volumes,"all_sketches_fully_constrained":True})
        doc.Params.set(CELLS[key],f"{original} mm")
        check(doc,shouldered)
    return results


def main(output=None):
    output=Path(output) if output else ROOT/"cad/table-node-pair_freecad_v0.1"
    output.mkdir(parents=True,exist_ok=True)
    for slug in ["clamp-tenon","shouldered-tenon"]:
        if (output/f"{slug}_v0.1.FCStd").exists():raise RuntimeError("Refusing to overwrite existing master. Choose another output directory.")
    report={"master_type":"FreeCAD native parametric PartDesign","freecad_version":App.Version(),"state":"DRAFT","onshape_sync":"OPTIONAL_NOT_PERFORMED","print_verified":False,"nodes":{}}
    for slug,shouldered in [("clamp-tenon",False),("shouldered-tenon",True)]:
        doc=build(slug,shouldered)
        check(doc,shouldered)
        tests=parameter_tests(doc,shouldered)
        target=output/f"{slug}_v0.1.FCStd"
        doc.recompute();doc.saveAs(str(target));App.closeDocument(doc.Name)
        doc=App.openDocument(str(target))
        volumes=check(doc,shouldered)
        info={"source_file":target.name,"source_sha256":hashlib.sha256(target.read_bytes()).hexdigest(),"parameters":snapshot(doc),"reopen_recompute_passed":True,"parameter_tests":tests,"parts":{},"feature_tree":[{"name":o.Name,"type":o.TypeId} for o in doc.Objects if o.TypeId in {"Spreadsheet::Sheet","Sketcher::SketchObject","PartDesign::Body","PartDesign::Pad","PartDesign::Pocket"}]}
        bodies=[doc.getObject(name) for name in COLORS]
        Part.export(bodies,str(output/f"{slug}_v0.1.step"))
        for body in bodies:
            name=body.Name
            mesh=MeshPart.meshFromShape(Shape=body.Shape,LinearDeflection=.01,AngularDeflection=.1,Relative=False)
            mesh.write(str(output/f"{slug}_{name}.stl"))
            b=body.Shape.BoundBox
            info["parts"][name]={"volume_mm3":volumes[name],"bbox_mm":[[b.XMin,b.YMin,b.ZMin],[b.XMax,b.YMax,b.ZMax]],"solid_count":1}
        report["nodes"][slug]=info
        App.closeDocument(doc.Name)
        print(slug,"saved, reopened, parametrically recomputed and exported",flush=True)
    (output/"source-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output")
    args,_=parser.parse_known_args()
    main(args.output)
