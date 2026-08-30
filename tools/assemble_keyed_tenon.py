#!/usr/bin/env python3
"""Compose the assembled and exploded Onshape views of the keyed tenon.

Members A and B already sit in their mated position in the Part Studio, so they
go into the assembly untransformed.  Only the key has to be placed: it is
modelled parked beside the joint, and this script rotates it 180 deg about X and
drops it into the hole at the depth where its taper first meets the 7.20 mm
socket.

Unlike its dovetail counterpart, this script is safe to re-run: it looks the
exploded assembly up by name instead of creating a new one every time, and it
only inserts instances that are missing.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.request


DID = "73de9c93248e073d85379a97"
WID = "1bd7eba357dd91d2503bfa3c"
PART_STUDIO = "bd84c453f68419d4085d9688"
ASSEMBLED = "8fc834ed7d4b7b8f20ba8ff1"
# No version in the element name: the version is carried by the document
# version, and a name that says v0.1 goes stale the moment geometry changes.
EXPLODED_NAME = "楔钉榫 · 爆炸图"

# The key and the hole share one taper, so the key drops straight down its own
# axis into place: no rotation, just a translation back from where it is parked.
KEY_PARK_X = 80.0
STOCK_HEIGHT = 18.0
EXPLODE = 45.0


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
        with urllib.request.urlopen(req, timeout=90) as response:
            raw = response.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Onshape returned HTTP {error.code}: {detail}") from error


def matrix(rows: list[list[float]]) -> list[float]:
    return [value for row in rows for value in row]


def key_transform(extra_lift_mm: float = 0.0) -> list[float]:
    """Slide the parked key back onto the joint axis, optionally lifted clear."""
    return matrix([
        [1.0, 0.0, 0.0, -KEY_PARK_X / 1000.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, extra_lift_mm / 1000.0],
        [0.0, 0.0, 0.0, 1.0],
    ])


def member_a_transform(offset_mm: float) -> list[float]:
    return matrix([
        [1.0, 0.0, 0.0, offset_mm / 1000.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ])


def classify_parts() -> dict[str, str]:
    """Name the three parts by where they sit, not by their ordinal.

    Extents come from the tessellated edges because the /boundingboxes endpoint
    has been seen returning all zeros for a body carrying fillets.
    """
    found: dict[str, str] = {}
    for part in request("GET", f"/api/v10/parts/d/{DID}/w/{WID}/e/{PART_STUDIO}"):
        edges = request(
            "GET",
            f"/api/v10/parts/d/{DID}/w/{WID}/e/{PART_STUDIO}/partid/{part['partId']}/tessellatededges",
        )
        points = [(v["x"] * 1000, v["y"] * 1000)
                  for body in edges["bodies"] for edge in body["edges"]
                  for v in edge["vertices"]]
        low_x = min(x for x, _ in points)
        if low_x > 50.0:
            found["key"] = part["partId"]
        elif low_x < -30.0:
            found["A"] = part["partId"]
        else:
            found["B"] = part["partId"]
    if sorted(found) != ["A", "B", "key"]:
        raise RuntimeError(f"Part Studio does not hold the expected three parts: {found}")
    return found


def assembly_path(eid: str, suffix: str = "") -> str:
    return f"/api/v10/assemblies/d/{DID}/w/{WID}/e/{eid}{suffix}"


def ensure_instances(eid: str, parts: dict[str, str]) -> dict:
    """Make the assembly hold exactly the current three parts.

    A Part Studio rebuild issues fresh part IDs, so an assembly that was built
    against the previous rebuild still points at bodies that no longer exist.
    Those stale instances are dropped, but anything that did not come from this
    Part Studio is treated as somebody's work and stops the script instead.
    """
    definition = request("GET", assembly_path(eid))
    wanted = set(parts.values())
    for instance in definition["rootAssembly"]["instances"]:
        if instance.get("elementId") != PART_STUDIO or instance.get("documentId") != DID:
            raise RuntimeError(f"Assembly {eid} holds unrelated content; refusing to modify it.")
        if instance.get("partId") not in wanted:
            request("DELETE", assembly_path(eid, f"/instance/nodeid/{instance['id']}"))
            print(f"  dropped stale instance {instance.get('partId')}")
    definition = request("GET", assembly_path(eid))
    present = {i.get("partId") for i in definition["rootAssembly"]["instances"]}
    for part_id in wanted:
        if part_id not in present:
            request("POST", assembly_path(eid, "/instances"), {
                "documentId": DID,
                "elementId": PART_STUDIO,
                "includePartTypes": ["PARTS"],
                "partId": part_id,
            })
    return request("GET", assembly_path(eid))


def occurrence_path(definition: dict, part_id: str) -> list[str]:
    root = definition["rootAssembly"]
    instance_id = next(
        (i["id"] for i in root["instances"] if i.get("partId") == part_id), None)
    if not instance_id:
        raise RuntimeError(f"No assembly instance found for part {part_id}")
    for occurrence in root["occurrences"]:
        if occurrence.get("path") and occurrence["path"][-1] == instance_id:
            return occurrence["path"]
    raise RuntimeError(f"No assembly occurrence found for part {part_id}")


def place(eid: str, definition: dict, part_id: str, transform: list[float]) -> None:
    request("POST", assembly_path(eid, "/modify"), {
        "transformDefinitions": [
            {"occurrences": [{"path": occurrence_path(definition, part_id)}],
             "transform": transform}
        ]
    })


def check(eid: str, part_id: str, expected: list[float], label: str) -> None:
    definition = request("GET", assembly_path(eid))
    actual = None
    for occurrence in definition["rootAssembly"]["occurrences"]:
        if occurrence.get("path") == occurrence_path(definition, part_id):
            actual = occurrence.get("transform")
    if actual is None or any(abs(float(a) - float(b)) > 1e-9 for a, b in zip(actual, expected)):
        raise RuntimeError(f"{label}: unexpected transform {actual}")
    print(f"  {label}: transform verified")


def find_or_create_exploded() -> str:
    for element in request("GET", f"/api/v10/documents/d/{DID}/w/{WID}/elements"):
        if element["elementType"] == "ASSEMBLY" and element["name"] == EXPLODED_NAME:
            print(f"reusing exploded assembly: {element['id']}")
            return element["id"]
    created = request("POST", f"/api/v10/assemblies/d/{DID}/w/{WID}", {"name": EXPLODED_NAME})
    eid = created.get("id") or created.get("elementId")
    if not eid:
        raise RuntimeError(f"Could not read the new assembly's ID: {created}")
    print(f"created exploded assembly: {eid}")
    return eid


def main() -> int:
    parts = classify_parts()
    print("parts:", {k: v for k, v in sorted(parts.items())})

    print("\nAssembly 1 (mated):")
    definition = ensure_instances(ASSEMBLED, parts)
    place(ASSEMBLED, definition, parts["A"], member_a_transform(0.0))
    place(ASSEMBLED, definition, parts["key"], key_transform())
    check(ASSEMBLED, parts["A"], member_a_transform(0.0), "member A")
    check(ASSEMBLED, parts["key"], key_transform(), "key")

    exploded_id = find_or_create_exploded()
    print(f"\n{EXPLODED_NAME}:")
    definition = ensure_instances(exploded_id, parts)
    # Member B is the fixed reference; A withdraws along the joint axis and the
    # key lifts straight out, each the reverse of how it went together.
    place(exploded_id, definition, parts["A"], member_a_transform(-EXPLODE))
    place(exploded_id, definition, parts["key"], key_transform(EXPLODE))
    check(exploded_id, parts["A"], member_a_transform(-EXPLODE), "member A")
    check(exploded_id, parts["key"], key_transform(EXPLODE), "key")

    print("\nKey placed fully home: head flush with the entry face, tip 4.5 mm above "
          "the far face.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
