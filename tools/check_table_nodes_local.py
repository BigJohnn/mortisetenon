#!/usr/bin/env python3
"""Independent OpenCascade construction/check of the FeatureScript geometry.

Local STEP/STL are check intermediates, not Onshape exports. Published derivatives
must be re-exported from the frozen Onshape source and compared with this report.
Run with CadQuery + trimesh installed (temporary uv environment is sufficient).
"""
from __future__ import annotations
import hashlib
import itertools
import json
import math
import re
from pathlib import Path
import cadquery as cq
import trimesh
ROOT=Path(__file__).resolve().parents[1]
PARAMS=json.loads((ROOT/"cad/table-node-pair_parameters_v0.1.json").read_text())["parameters"]


def box(low, high):
    return cq.Solid.makeBox(*(high[i]-low[i] for i in range(3)), cq.Vector(*low))


def prism(points, width):
    return cq.Workplane("YZ", origin=(-width/2,0,0)).polyline(points).close().extrude(width).val()


def build(shouldered, p=PARAMS):
    w, h, t, l = (p[k] for k in ["stock","apronHeight","apronThickness","apronLength"])
    a, b = t/2, t/2+p["spread"]
    leg = box((-w/2,-w/2,-p["legLength"]),(w/2,w/2,0))
    for side in [-1,1]:
        cy=side*(w/2-2)
        leg=leg.fuse(box((-p["tenonWidth"]/2,cy-p["tenonThickness"]/2,-1),(p["tenonWidth"]/2,cy+p["tenonThickness"]/2,p["tenonHeight"])))
    if shouldered:
        slot=prism([(-a,-h-p["endGap"]),(a,-h-p["endGap"]),(a,-h),(b,0),(b,p["tenonHeight"]+1),(-b,p["tenonHeight"]+1),(-b,0),(-a,-h)],w+2)
    else:
        slot=box((-w/2-1,-a-p["slotFit"]/2,-h),(w/2+1,a+p["slotFit"]/2,p["tenonHeight"]+1))
    leg=leg.cut(slot).clean()
    apron=box((-l/2,-a,-h),(l/2,a,0))
    if shouldered:
        apron=apron.fuse(prism([(-a,-h),(a,-h),(b,0),(-b,0)],w)).clean()
    top=box((-l/2,-p["topWidth"]/2,0),(l/2,p["topWidth"]/2,p["topThickness"]))
    for side in [-1,1]:
        cy=side*(w/2-2)
        hw,ht=(p["tenonWidth"]+p["fit"])/2,(p["tenonThickness"]+p["fit"])/2
        top=top.cut(box((-hw,cy-ht,-1),(hw,cy+ht,p["tenonHeight"]+p["endGap"])))
    return {"Leg":leg,"Apron":apron,"Top":top.clean()}


def collision(a,b):
    return a.intersect(b).Volume()


def expected_volumes(shouldered, p=PARAMS):
    """Closed-form cross-section calculations, independent of BREP booleans."""
    w,h,t,l=(p[k] for k in ["stock","apronHeight","apronThickness","apronLength"])
    opening=(t*h+p["spread"]*h+t*p["endGap"]) if shouldered else (t+p["slotFit"])*h
    return {"Leg":w*w*p["legLength"]+2*p["tenonWidth"]*p["tenonThickness"]*p["tenonHeight"]-w*opening,
            "Apron":l*t*h+(w*p["spread"]*h if shouldered else 0),
            "Top":l*p["topWidth"]*p["topThickness"]-2*(p["tenonWidth"]+p["fit"])*(p["tenonThickness"]+p["fit"])*(p["tenonHeight"]+p["endGap"])}


def main():
    source=(ROOT/"cad/table-node-pair_v0.1.fs").read_text()
    for key,value in PARAMS.items():
        match=re.search(r'"'+re.escape(key)+r'"\s*:\s*([\d.]+)\s*\*\s*millimeter',source)
        assert match and float(match.group(1))==value,(key,"FeatureScript default differs from check snapshot")
    output=ROOT/"cad/table-node-pair_local-check"
    output.mkdir(exist_ok=True)
    report={"source":"Independent CadQuery reconstruction of table-node-pair_v0.1.fs", "cadquery_version":cq.__version__, "trimesh_version":trimesh.__version__,
            "feature_script_sha256":hashlib.sha256((ROOT/"cad/table-node-pair_v0.1.fs").read_bytes()).hexdigest(),
            "limitations":["FeatureScript has not been compiled in Onshape", "Local files are independent check intermediates, not cloud exports", "Motion is sampled at 1 mm, not a continuous swept-volume proof", "Nominal digital contact is not a printed fit or strength test"],
            "units":"mm", "status":"DIGITAL_CHECK_ONLY", "print_verified":False, "parameters":PARAMS,
            "shoulder_angle_from_vertical_deg":math.degrees(math.atan(PARAMS["spread"]/PARAMS["apronHeight"])),"nodes":{}}
    for shouldered,slug in [(False,"clamp-tenon"),(True,"shouldered-tenon")]:
        parts=build(shouldered)
        info={"parts":{},"assembled_intersections_mm3":{},"motion":{}}
        for name,shape in parts.items():
            assert shape.isValid() and len(shape.Solids())==1, (slug,name,"invalid")
            analytic=expected_volumes(shouldered)[name]
            assert abs(shape.Volume()-analytic)<1e-6,(slug,name,"analytic volume mismatch")
            target=output/f"{slug}_{name}.stl"
            cq.exporters.export(shape,str(target),tolerance=0.01,angularTolerance=0.1)
            mesh=trimesh.load(str(target),force="mesh",process=True)
            assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split())==1,(slug,name,"mesh invalid")
            bounds=shape.BoundingBox()
            info["parts"][name]={"volume_mm3":shape.Volume(),"analytic_volume_mm3":analytic,"bbox_mm":[[bounds.xmin,bounds.ymin,bounds.zmin],[bounds.xmax,bounds.ymax,bounds.zmax]],
                "solid_count":1,"watertight":True,"winding_consistent":True,"triangle_count":len(mesh.faces),"sha256":hashlib.sha256(target.read_bytes()).hexdigest()}
        for first,second in itertools.combinations(parts,2):
            v=collision(parts[first],parts[second]);assert v<1e-7,(slug,first,second,v)
            info["assembled_intersections_mm3"][first+"/"+second]=v
        # Evaluate actual BREP planes, independently of the mesh representation.
        planes=[]
        for face in parts["Leg"].Faces():
            n,c=face.normalAt(),face.Center()
            if shouldered and abs(n.x)<1e-8 and 0.1<n.z<0.2:
                planes.append({"interface":"IF-APRON","normal":n.toTuple(),"area_mm2":face.Area(),"centroid_mm":c.toTuple()})
            elif not shouldered and n.z>0.999999 and abs(c.z+PARAMS["apronHeight"])<1e-8:
                planes.append({"interface":"IF-APRON","normal":n.toTuple(),"area_mm2":face.Area(),"centroid_mm":c.toTuple()})
        assert len(planes)==(2 if shouldered else 1),(slug,"missing bearing planes")
        target_area=PARAMS["stock"]*(math.hypot(PARAMS["apronHeight"],PARAMS["spread"]) if shouldered else PARAMS["apronThickness"]+PARAMS["slotFit"])
        assert all(abs(f["area_mm2"]-target_area)<1e-6 for f in planes),(slug,"bearing plane area")
        info["leg_bearing_planes"]=planes
        # Sequence: top parked at +96, apron +48 -> 0, then top +96 -> 0.
        for moving,distance,fixed in [("Apron",48,[parts["Leg"],parts["Top"].translate((0,0,96))]),("Top",96,[parts["Leg"],parts["Apron"]])]:
            maximum=0
            minimum_distance=float("inf")
            for z in range(distance+1):
                shape=parts[moving].translate((0,0,z))
                for other in fixed:
                    maximum=max(maximum,collision(shape,other))
                    minimum_distance=min(minimum_distance,shape.distance(other))
            assert maximum<1e-7,(slug,moving,"sweep",maximum)
            overtravel=collision(parts[moving].translate((0,0,-0.5)),parts["Leg"])
            assert overtravel>0.1,(slug,moving,"missing stop")
            info["motion"][moving]={"axis":[0,0,-1],"travel_mm":distance,"sample_step_mm":1,"samples":distance+1,
                "max_intersection_mm3":maximum,"minimum_separation_mm":minimum_distance,"negative_control_overtravel_mm":0.5,"negative_control_intersection_mm3":overtravel}
        comp=cq.Compound.makeCompound(list(parts.values()))
        cq.exporters.export(comp,str(output/f"{slug}_local-check.step"))
        report["nodes"][slug]=info
        print(slug,"valid solids / watertight meshes / zero sampled path intersections / overtravel controls passed",flush=True)
    (output/"report.json").write_text(json.dumps(report,indent=2)+"\n")


if __name__=="__main__":main()
