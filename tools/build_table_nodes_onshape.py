#!/usr/bin/env python3
"""Legacy FeatureScript experiment; NOT synchronization of the FreeCAD master."""
from __future__ import annotations
import argparse
import json
from onshape_joinery_client import ROOT, FOLDER, request

STATE = ROOT / "cad/table-node-pair_onshape.json"
NAME = "可打印的榫卯 · 夹头与插肩对照 · v0.1"
PARAMS = {"stock":24, "legLength":96, "apronLength":96, "apronThickness":8,
          "apronHeight":24, "topWidth":40, "topThickness":16, "tenonWidth":16,
          "tenonThickness":2, "tenonHeight":8, "fit":0.3, "slotFit":0.3,
          "endGap":0.4, "spread":4}


def save(state):
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-experiment",action="store_true",help="Explicitly request the old independent FeatureScript experiment; never use as FCStd synchronization")
    parser.add_argument("--public",action="store_true",help="Create a public document only after the owner explicitly authorizes public geometry and source")
    args=parser.parse_args()
    if not args.legacy_experiment:
        raise RuntimeError("FreeCAD is now the master. This legacy creator is disabled by default and is not an Onshape sync pipeline.")
    folder = request("GET", f"/api/v10/folders/{FOLDER}")
    if "WRITE" not in folder["permissionSet"]:
        raise RuntimeError("Target folder is not writable")
    if STATE.exists():
        state = json.loads(STATE.read_text())
        if state["folder_id"] != FOLDER:
            raise RuntimeError("Recorded target folder differs")
    else:
        doc = request("POST", "/api/v10/documents", {
            "name": NAME, "isPublic": args.public, "parentId": FOLDER,
            "description": "Three-part N24 teaching variants. Original geometry; no print or traditional-reconstruction claim."
        })
        state = {"folder_id": FOLDER, "document_id": doc["id"], "workspace_id": doc["defaultWorkspace"]["id"], "is_public":args.public, "nodes":{}}
        save(state)
        print("Created task document:", state["document_id"], flush=True)
    did, wid = state["document_id"], state["workspace_id"]
    elements = request("GET", f"/api/v10/documents/d/{did}/w/{wid}/elements")
    if not state.get("feature_studio_id"):
        existing = next((e for e in elements if e["name"] == "Table node source"), None)
        fs = existing or request("POST", f"/api/v10/featurestudios/d/{did}/w/{wid}", {"name":"Table node source"})
        state["feature_studio_id"] = fs["id"]
        save(state)
    fsid = state["feature_studio_id"]
    contents = (ROOT / "cad/table-node-pair_v0.1.fs").read_text()
    request("POST", f"/api/v10/featurestudios/d/{did}/w/{wid}/e/{fsid}", {"contents":contents})
    specs = request("GET", f"/api/v10/featurestudios/d/{did}/w/{wid}/e/{fsid}/featurespecs")
    (ROOT / "cad/table-node-pair_feature-spec.json").write_text(json.dumps(specs,indent=2)+"\n")
    print("Feature source uploaded; spec keys:", list(specs), flush=True)
    for slug, name, shouldered in [("clamp-tenon","夹头榫 · 三件教学节点",False),("shouldered-tenon","插肩榫 · 双斜肩教学节点",True)]:
        node = state["nodes"].setdefault(slug,{})
        if not node.get("part_studio_id"):
            existing = next((e for e in elements if e["name"] == name), None)
            ps = existing or request("POST", f"/api/v10/partstudios/d/{did}/w/{wid}", {"name":name})
            node["part_studio_id"] = ps["id"]
            save(state)
        eid = node["part_studio_id"]
        features_path = f"/api/v10/partstudios/d/{did}/w/{wid}/e/{eid}/features"
        features = request("GET", features_path)
        ours = next((f for f in features["features"] if f["featureType"] == "tableNode"),None)
        if any(f["featureType"] != "tableNode" for f in features["features"]):
            raise RuntimeError("Unexpected user features in task Part Studio")
        if ours:
            node["feature_id"] = ours["featureId"]
            print(slug, "existing feature", ours["featureId"], flush=True)
        else:
            params = [{"btType":"BTMParameterQuantity-147", "parameterId":key,"expression":f"{value} mm"} for key,value in PARAMS.items()]
            params.append({"btType":"BTMParameterBoolean-144","parameterId":"shouldered","value":shouldered})
            response = request("POST", features_path, {"feature":{
                "btType":"BTMFeature-134", "featureType":"tableNode", "name":name,
                "namespace": f"d{did}::w{wid}::e{fsid}", "parameters":params
            }})
            node["feature_id"] = response["feature"]["featureId"]
            save(state)
            print(slug, "feature state:", response.get("featureState"), flush=True)
            if response.get("featureState",{}).get("featureStatus") != "OK":
                raise RuntimeError("Feature failed; inspect Feature Studio diagnostics")
        parts = request("GET", f"/api/v10/parts/d/{did}/w/{wid}/e/{eid}")
        node["parts"] = [{"name":p["name"],"part_id":p["partId"]} for p in parts]
        save(state)
        print(slug, "parts:", node["parts"], flush=True)
        if sorted(p["name"] for p in parts) != ["Apron","Leg","Top"]:
            raise RuntimeError("Expected exactly the three named solids")
    print("Modelled both nodes", flush=True)


if __name__ == "__main__":
    main()
