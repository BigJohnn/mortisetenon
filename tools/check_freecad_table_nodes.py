#!/usr/bin/env python3
"""Check exports from reopened native FCStd masters using independent OCP.

Requires CadQuery and trimesh. Does not build or modify the FreeCAD masters.
"""
from pathlib import Path
import hashlib
import itertools
import json
import math
import zipfile
import cadquery as cq
import trimesh
from check_table_nodes_local import build, expected_volumes, collision, ROOT

OUTPUT=ROOT/"cad/table-node-pair_freecad_v0.1"


def main():
    source=json.loads((OUTPUT/"source-report.json").read_text())
    report={"source":"STEP/STL exported after reopening native FreeCAD FCStd masters", "master_type":"FreeCAD native parametric PartDesign", "cadquery_version":cq.__version__, "trimesh_version":trimesh.__version__, "units":"mm", "state":"DRAFT", "print_verified":False,"onshape_sync":"OPTIONAL_NOT_PERFORMED", "nodes":{},"limitations":["Motion sampled at 1 mm, not continuous swept-volume proof", "Parameter changes cover selected test cases, not every possible input", "No physical fit, strength or printer orientation verification"]}
    for slug,shouldered in [("clamp-tenon",False),("shouldered-tenon",True)]:
        src=source["nodes"][slug]
        master=OUTPUT/src["source_file"]
        assert hashlib.sha256(master.read_bytes()).hexdigest()==src["source_sha256"]
        with zipfile.ZipFile(master) as archive:
            xml=archive.read("Document.xml").decode()
            assert 'Spreadsheet::Sheet' in xml and 'Sketcher::SketchObject' in xml
            assert xml.count('type="PartDesign::Body"')==3
            assert 'PartDesign::Pad' in xml and 'PartDesign::Pocket' in xml
            assert 'PartDesign::FeaturePython' not in xml
        p=src["parameters"]
        solids=cq.importers.importStep(str(OUTPUT/f"{slug}_v0.1.step")).val().Solids()
        assert len(solids)==3
        volumes=expected_volumes(shouldered,p)
        parts=dict(zip(sorted(volumes,key=volumes.get),sorted(solids,key=lambda s:s.Volume())))
        reference=build(shouldered,p)
        info={"source_file":src["source_file"],"source_sha256":src["source_sha256"],"parameters":p,"parts":{},"assembled_intersections_mm3":{},"motion":{},"leg_bearing_planes":[],"reopen_recompute_passed":src["reopen_recompute_passed"],"parameter_test_count":len(src["parameter_tests"])}
        for name,shape in parts.items():
            assert shape.isValid() and len(shape.Solids())==1
            assert abs(shape.Volume()-volumes[name])<1e-5
            # Symmetric-difference volume proves more than equal volume alone.
            difference=shape.cut(reference[name]).Volume()+reference[name].cut(shape).Volume()
            assert difference<1e-6,(slug,name,"reference geometry mismatch",difference)
            target=OUTPUT/f"{slug}_{name}.stl"
            mesh=trimesh.load(str(target),force="mesh",process=True)
            assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split())==1
            assert abs(mesh.volume-shape.Volume())<.02
            b=shape.BoundingBox()
            info["parts"][name]={"volume_mm3":shape.Volume(),"analytic_volume_mm3":volumes[name],"symmetric_difference_mm3":difference,"solid_count":1,"watertight":True,"winding_consistent":True,"triangle_count":len(mesh.faces),"bbox_mm":[[b.xmin,b.ymin,b.zmin],[b.xmax,b.ymax,b.zmax]],"sha256":hashlib.sha256(target.read_bytes()).hexdigest()}
        for a,b in itertools.combinations(parts,2):
            v=collision(parts[a],parts[b]);assert v<1e-7
            info["assembled_intersections_mm3"][a+"/"+b]=v
        for face in parts["Leg"].Faces():
            n,c=face.normalAt(),face.Center()
            if (shouldered and abs(n.x)<1e-8 and .1<n.z<.2) or (not shouldered and n.z>.999999 and abs(c.z+p["apronHeight"])<1e-8):
                info["leg_bearing_planes"].append({"interface":"IF-APRON","normal":n.toTuple(),"area_mm2":face.Area(),"centroid_mm":c.toTuple()})
        assert len(info["leg_bearing_planes"])==(2 if shouldered else 1)
        for moving,distance,fixed in [("Apron",48,[parts["Leg"],parts["Top"].translate((0,0,96))]),("Top",96,[parts["Leg"],parts["Apron"]])]:
            maximum=0;minimum=float("inf")
            for z in range(distance+1):
                shape=parts[moving].translate((0,0,z))
                for other in fixed:
                    maximum=max(maximum,collision(shape,other));minimum=min(minimum,shape.distance(other))
            assert maximum<1e-7
            overtravel=collision(parts[moving].translate((0,0,-.5)),parts["Leg"])
            assert overtravel>.1
            info["motion"][moving]={"axis":[0,0,-1],"travel_mm":distance,"sample_step_mm":1,"samples":distance+1,"max_intersection_mm3":maximum,"minimum_separation_mm":minimum,"negative_control_overtravel_mm":.5,"negative_control_intersection_mm3":overtravel}
        report["nodes"][slug]=info
        print(slug,"native source identity / 3 solids / exact geometry comparison / meshes / motion passed",flush=True)
    report["shoulder_angle_from_vertical_deg"]=math.degrees(math.atan(p["spread"]/p["apronHeight"]))
    (OUTPUT/"report.json").write_text(json.dumps(report,indent=2)+"\n")


if __name__=="__main__":main()
