#!/usr/bin/env python3
"""Create the v0.1 slide-in dovetail teaching model in an empty Part Studio.

Credentials are deliberately read from the environment so that ``.env`` is not
embedded in the model definition or emitted by this script.
"""

from __future__ import annotations

import base64
import argparse
import json
import os
import sys
import urllib.error
import urllib.request


DID = "aa8b70cbf3d6f40dfdcb967a"
WID = "943c5823d305588e19a86353"
EID = "0d07eeb01c441d834f260832"
FEATURES_PATH = f"/api/v10/partstudios/d/{DID}/w/{WID}/e/{EID}/features"


def request(method: str, path: str, payload: dict | None = None) -> dict:
    key = os.environ["ONSHAPE_ACCESS_KEY"]
    secret = os.environ["ONSHAPE_SECRET_KEY"]
    base_url = os.environ.get("ONSHAPE_BASE_URL", "https://cad.onshape.com").rstrip("/")
    headers = {
        "Accept": "application/json;charset=UTF-8; qs=0.09",
        "Authorization": "Basic " + base64.b64encode(f"{key}:{secret}".encode()).decode(),
    }
    body = None
    if payload is not None:
        body = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json;charset=UTF-8; qs=0.09"
    req = urllib.request.Request(base_url + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Onshape returned HTTP {error.code}: {detail}") from error


def plane_parameter() -> dict:
    return {
        "btType": "BTMParameterQueryList-148",
        "parameterId": "sketchPlane",
        "queries": [
            {
                "btType": "BTMIndividualQuery-138",
                "queryString": 'query=qCreatedBy(makeId("Front"), EntityType.FACE);',
            }
        ],
    }


def line(entity_id: str, start: tuple[float, float], end: tuple[float, float]) -> dict:
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = (dx * dx + dy * dy) ** 0.5
    return {
        "btType": "BTMSketchCurveSegment-155",
        "entityId": entity_id,
        "startPointId": f"{entity_id}.start",
        "endPointId": f"{entity_id}.end",
        "isConstruction": False,
        "startParam": 0.0,
        "endParam": length,
        "geometry": {
            "btType": "BTCurveGeometryLine-117",
            "pntX": start[0],
            "pntY": start[1],
            "dirX": dx / length,
            "dirY": dy / length,
        },
    }


def profile_sketch(name: str, points: list[tuple[float, float]]) -> dict:
    entities = [
        line(f"edge_{index + 1}", point, points[(index + 1) % len(points)])
        for index, point in enumerate(points)
    ]
    return {
        "btType": "BTFeatureDefinitionCall-1406",
        "feature": {
            "btType": "BTMSketch-151",
            "featureType": "newSketch",
            "name": name,
            "parameters": [plane_parameter()],
            "entities": entities,
            "constraints": [],
            "suppressed": False,
            "returnAfterSubfeatures": False,
        },
    }


def extrude(name: str, sketch_id: str, operation: str) -> dict:
    return {
        "btType": "BTFeatureDefinitionCall-1406",
        "feature": {
            "btType": "BTMFeature-134",
            "featureType": "extrude",
            "name": name,
            "parameters": [
                {
                    "btType": "BTMParameterEnum-145",
                    "value": "SOLID",
                    "enumName": "ExtendedToolBodyType",
                    "parameterId": "bodyType",
                },
                {
                    "btType": "BTMParameterEnum-145",
                    "value": operation,
                    "enumName": "NewBodyOperationType",
                    "parameterId": "operationType",
                },
                {
                    "btType": "BTMParameterQueryList-148",
                    "parameterId": "entities",
                    "queries": [
                        {
                            "btType": "BTMIndividualSketchRegionQuery-140",
                            "featureId": sketch_id,
                        }
                    ],
                },
                {
                    "btType": "BTMParameterEnum-145",
                    "value": "BLIND",
                    "enumName": "BoundingType",
                    "parameterId": "endBound",
                },
                {
                    "btType": "BTMParameterQuantity-147",
                    "expression": "24 mm",
                    "parameterId": "depth",
                },
            ],
            "suppressed": False,
            "returnAfterSubfeatures": False,
        },
    }


def add(payload: dict) -> str:
    response = request("POST", FEATURES_PATH, payload)
    status = response["featureState"]["featureStatus"]
    if status != "OK":
        raise RuntimeError(f"Feature did not regenerate successfully: {json.dumps(response)}")
    feature = response["feature"]
    print(f"{feature['name']}: {feature['featureId']}")
    return feature["featureId"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repair-socket",
        action="store_true",
        help="correct the socket profile in an already-created v0.1 model",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="replace this script's Part Studio features with the insertable v0.2 geometry",
    )
    parser.add_argument(
        "--chamfer-roots",
        action="store_true",
        help="add 0.5 mm root-relief chamfers to the existing dovetail tail",
    )
    parser.add_argument(
        "--chamfer-socket-roots",
        action="store_true",
        help="add 0.4 mm internal root relief and 0.2 mm roof clearance to the socket",
    )
    parser.add_argument(
        "--restore-tail",
        action="store_true",
        help="restore the sharp-root tail profile from before the public root relief",
    )
    args = parser.parse_args()
    initial = request("GET", FEATURES_PATH)
    if args.rebuild:
        expected_prefixes = tuple(f"0{index} ·" for index in range(1, 7))
        if len(initial["features"]) != 6 or any(
            not feature.get("name", "").startswith(expected_prefixes)
            for feature in initial["features"]
        ):
            raise RuntimeError(
                "Target Part Studio does not contain exactly this script's six features; "
                "refusing to delete possible user work."
            )
        for feature in reversed(initial["features"]):
            request("DELETE", FEATURES_PATH + f"/featureid/{feature['featureId']}")
        initial = request("GET", FEATURES_PATH)
    if initial["features"] and not args.repair_socket and not args.chamfer_roots and not args.chamfer_socket_roots and not args.restore_tail:
        raise RuntimeError("Target Part Studio is no longer empty; refusing to append features.")

    # Coordinates use metres because sketch geometry is serialized in SI units.
    # Each profile is on Front, with the 24 mm slide direction as its extrusion.
    # The mother board sits above the tail board.  Their only common boundary is
    # y = 10 mm; the groove has been removed from that board.  The resulting
    # volumes therefore do not overlap when their centres are aligned.
    socket_body = [(-0.050, 0.010), (-0.020, 0.010), (-0.020, 0.028), (-0.050, 0.028)]
    # C is the total mother-minus-male difference, as defined in CAD Spec v0.4.
    # The socket is centred at -35 mm: 16.2 mm at its opening, 10.2 mm at its neck.
    # The cavity has 0.20 mm additional depth above the 8 mm tail.  Its two
    # upper internal roots receive 0.4 mm relief setbacks, so neither a real
    # FDM internal radius nor an elephant-foot lip becomes the first contact.
    socket_slot_relief = [
        (-0.0435, 0.0182), (-0.0431, 0.0178), (-0.0401, 0.0100),
        (-0.0299, 0.0100), (-0.0269, 0.0178), (-0.0265, 0.0182),
    ]
    socket_slot = [(-0.0431, 0.018), (-0.0401, 0.010), (-0.0299, 0.010), (-0.0269, 0.018)]
    tail_profile = [
        (0.020, 0.000), (0.050, 0.000), (0.050, 0.010),
        (0.040, 0.010), (0.043, 0.018), (0.027, 0.018),
        (0.030, 0.010), (0.020, 0.010),
    ]

    # 0.5 mm equal-distance relief on both tail-root shoulders.  These are
    # profile chamfers rather than cosmetic edge treatments: the small material
    # removal avoids a printed male tail bearing on the female slot's imperfect
    # internal root corner or on an elephant-foot lip.
    root_relief = 0.0005
    diagonal = (0.003**2 + 0.008**2) ** 0.5
    tail_profile_chamfered = [
        (0.020, 0.000), (0.050, 0.000), (0.050, 0.010),
        (0.040 + root_relief, 0.010),
        (0.040 + 0.003 * root_relief / diagonal, 0.010 + 0.008 * root_relief / diagonal),
        (0.043, 0.018), (0.027, 0.018),
        (0.030 - 0.003 * root_relief / diagonal, 0.010 + 0.008 * root_relief / diagonal),
        (0.030 - root_relief, 0.010), (0.020, 0.010),
    ]

    if args.restore_tail:
        tail_id = "FU8DvObKul6zMcg_1"
        if not any(feature["featureId"] == tail_id for feature in initial["features"]):
            raise RuntimeError("Expected v0.2 tail sketch is absent; refusing to update a different model.")
        tail_payload = profile_sketch("05 · Dovetail tail — 16 / 10 / 8 mm", tail_profile)
        tail_payload["feature"]["featureId"] = tail_id
        restored = request("POST", FEATURES_PATH + f"/featureid/{tail_id}", tail_payload)
        if restored["featureState"]["featureStatus"] != "OK":
            raise RuntimeError(f"Tail restore failed: {json.dumps(restored)}")
        print("Restored the tail profile from before the root chamfer.")
    elif args.chamfer_socket_roots:
        slot_id = "FrFMqEFRLzm6AHn_1"
        if not any(feature["featureId"] == slot_id for feature in initial["features"]):
            raise RuntimeError("Expected v0.2 socket sketch is absent; refusing to update a different model.")
        slot_payload = profile_sketch(
            "03 · Dovetail socket — C 0.20 mm · roof +0.20 · root chamfer 0.4 mm",
            socket_slot_relief,
        )
        slot_payload["feature"]["featureId"] = slot_id
        repaired = request("POST", FEATURES_PATH + f"/featureid/{slot_id}", slot_payload)
        if repaired["featureState"]["featureStatus"] != "OK":
            raise RuntimeError(f"Socket root-relief update failed: {json.dumps(repaired)}")
        cut_id = "FLKhtbgnOQDzVrU_1"
        cut_payload = extrude("04 · Cut socket — C = 0.20 mm · root relief", slot_id, "REMOVE")
        cut_payload["feature"]["featureId"] = cut_id
        repaired = request("POST", FEATURES_PATH + f"/featureid/{cut_id}", cut_payload)
        if repaired["featureState"]["featureStatus"] != "OK":
            raise RuntimeError(f"Socket cut relabel failed: {json.dumps(repaired)}")
        print("Added 0.4 mm internal socket-root relief and 0.20 mm roof clearance.")
    elif args.chamfer_roots:
        tail_id = "FU8DvObKul6zMcg_1"
        if not any(feature["featureId"] == tail_id for feature in initial["features"]):
            raise RuntimeError("Expected v0.2 tail sketch is absent; refusing to update a different model.")
        tail_payload = profile_sketch(
            "05 · Dovetail tail — 16 / 10 / 8 mm · root chamfer 0.5 mm",
            tail_profile_chamfered,
        )
        tail_payload["feature"]["featureId"] = tail_id
        repaired = request("POST", FEATURES_PATH + f"/featureid/{tail_id}", tail_payload)
        if repaired["featureState"]["featureStatus"] != "OK":
            raise RuntimeError(f"Root chamfer update failed: {json.dumps(repaired)}")
        print("Added 0.5 mm equal-distance root chamfers to both tail shoulders.")
    elif args.repair_socket:
        slot_id = "FrFMqEFRLzm6AHn_1"
        slot_payload = profile_sketch("03 · Dovetail socket — 16.2 / 10.2 / 8 mm", socket_slot)
        slot_payload["feature"]["featureId"] = slot_id
        repaired = request("POST", FEATURES_PATH + f"/featureid/{slot_id}", slot_payload)
        if repaired["featureState"]["featureStatus"] != "OK":
            raise RuntimeError(f"Socket repair failed: {json.dumps(repaired)}")
        cut_id = "FLKhtbgnOQDzVrU_1"
        cut_payload = extrude("04 · Cut socket — C = 0.20 mm", slot_id, "REMOVE")
        cut_payload["feature"]["featureId"] = cut_id
        repaired = request("POST", FEATURES_PATH + f"/featureid/{cut_id}", cut_payload)
        if repaired["featureState"]["featureStatus"] != "OK":
            raise RuntimeError(f"Socket cut relabel failed: {json.dumps(repaired)}")
        print("Corrected socket to 16.2 mm outer / 10.2 mm neck (C = 0.20 mm).")
    else:
        socket_sketch = add(profile_sketch("01 · Mother board — 30 × 18 mm", socket_body))
        add(extrude("02 · Socket body — 24 mm slide length", socket_sketch, "NEW"))
        slot_sketch = add(profile_sketch("03 · Dovetail socket — C 0.20 mm · roof +0.20 · root chamfer 0.4 mm", socket_slot_relief))
        add(extrude("04 · Cut socket — C = 0.20 mm · root relief", slot_sketch, "REMOVE"))
        tail_sketch = add(profile_sketch("05 · Dovetail tail — 16 / 10 / 8 mm", tail_profile))
        add(extrude("06 · Tail body — 30 × 18 × 24 mm", tail_sketch, "NEW"))

    final = request("GET", FEATURES_PATH)
    failing = [
        name for name, state in final["featureStates"].items()
        if state["featureStatus"] != "OK"
    ]
    if failing:
        raise RuntimeError(f"Unexpected failing feature states: {failing}")
    print(f"Verified {len(final['features'])} native features; all regenerated successfully.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
