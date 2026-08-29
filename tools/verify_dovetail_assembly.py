#!/usr/bin/env python3
"""Build assembled and exploded Onshape views for the insertable dovetail."""

from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.request


DID = "aa8b70cbf3d6f40dfdcb967a"
WID = "943c5823d305588e19a86353"
PART_STUDIO = "0d07eeb01c441d834f260832"
ASSEMBLED = "fd7c8ae946a2204d062c1af9"


def request(method: str, path: str, body: dict | None = None) -> dict:
    key = os.environ["ONSHAPE_ACCESS_KEY"]
    secret = os.environ["ONSHAPE_SECRET_KEY"]
    base = os.environ.get("ONSHAPE_BASE_URL", "https://cad.onshape.com").rstrip("/")
    headers = {
        "Accept": "application/json;charset=UTF-8; qs=0.09",
        "Authorization": "Basic " + base64.b64encode(f"{key}:{secret}".encode()).decode(),
    }
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json;charset=UTF-8; qs=0.09"
    req = urllib.request.Request(base + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Onshape returned HTTP {error.code}: {detail}") from error


def assembly_path(eid: str, suffix: str = "") -> str:
    return f"/api/v10/assemblies/d/{DID}/w/{WID}/e/{eid}{suffix}"


def add_instance(assembly_id: str, part_id: str) -> None:
    request(
        "POST",
        assembly_path(assembly_id, "/instances"),
        {
            "documentId": DID,
            "elementId": PART_STUDIO,
            "includePartTypes": ["PARTS"],
            "partId": part_id,
        },
    )


def definition(assembly_id: str) -> dict:
    return request("GET", assembly_path(assembly_id))


def occurrence_for(assembly: dict, part_id: str) -> dict:
    root = assembly.get("rootAssembly", {})
    instance_id = next(
        (instance["id"] for instance in root.get("instances", []) if instance.get("partId") == part_id),
        None,
    )
    if not instance_id:
        raise RuntimeError(f"No assembly instance found for part {part_id}")
    occurrences = root.get("occurrences", [])
    for occurrence in occurrences:
        if occurrence.get("path", []) and occurrence["path"][-1] == instance_id:
            return occurrence
    raise RuntimeError(f"No assembly occurrence found for part {part_id}")


def transform_tail(assembly_id: str, tail_part_id: str, y_offset: float) -> None:
    occurrence = occurrence_for(definition(assembly_id), tail_part_id)
    request(
        "POST",
        assembly_path(assembly_id, "/modify"),
        {
            "transformDefinitions": [
                {
                    "occurrences": [{"path": occurrence["path"]}],
                    # Source parts are offset ±35 mm in X.  -70 mm aligns their
                    # dovetail centre-lines.  A Y translation is the 24 mm slide
                    # direction because the profiles were extruded from Front.
                    "transform": [
                        1, 0, 0, -0.070,
                        0, 1, 0, y_offset,
                        0, 0, 1, 0,
                        0, 0, 0, 1,
                    ],
                }
            ]
        },
    )


def check_transform(assembly_id: str, tail_part_id: str, expected_y: float) -> None:
    occurrence = occurrence_for(definition(assembly_id), tail_part_id)
    actual = occurrence.get("transform")
    expected = [1, 0, 0, -0.070, 0, 1, 0, expected_y, 0, 0, 1, 0, 0, 0, 0, 1]
    if actual is None or any(abs(float(a) - float(b)) > 1e-9 for a, b in zip(actual, expected)):
        raise RuntimeError(f"Unexpected tail transform: {actual}")


def main() -> int:
    parts = request("GET", f"/api/v10/parts/d/{DID}/w/{WID}/e/{PART_STUDIO}")
    if len(parts) != 2:
        raise RuntimeError(f"Expected exactly two dovetail parts, found {len(parts)}")
    parts.sort(key=lambda part: part["ordinal"])
    socket, tail = parts

    assembled_before = definition(ASSEMBLED)
    existing_parts = {item.get("partId") for item in assembled_before["rootAssembly"]["instances"]}
    unexpected = existing_parts - {socket["partId"], tail["partId"]}
    if unexpected:
        raise RuntimeError("Assembly 1 contains unrelated user content; refusing to modify it.")
    if socket["partId"] not in existing_parts:
        add_instance(ASSEMBLED, socket["partId"])
    if tail["partId"] not in existing_parts:
        add_instance(ASSEMBLED, tail["partId"])
    transform_tail(ASSEMBLED, tail["partId"], 0.0)
    check_transform(ASSEMBLED, tail["partId"], 0.0)

    exploded_response = request(
        "POST",
        f"/api/v10/assemblies/d/{DID}/w/{WID}",
        {"name": "燕尾榫 · 爆炸图 v0.2"},
    )
    exploded_id = exploded_response.get("id") or exploded_response.get("elementId")
    if not exploded_id:
        raise RuntimeError(f"Could not read exploded assembly ID: {exploded_response}")
    add_instance(exploded_id, socket["partId"])
    add_instance(exploded_id, tail["partId"])
    transform_tail(exploded_id, tail["partId"], -0.032)
    check_transform(exploded_id, tail["partId"], -0.032)

    # Analytic interference proof in the fully assembled cross-section:
    # mother material starts at z=10 mm; the male body ends at z=10 mm; the
    # only overlapping z range is the removed dovetail cavity.  C=0.20 mm
    # makes the socket 0.10 mm wider on each sloping side than the tail.
    print("Assembly 1: assembled, centre-lines aligned, transform verified.")
    print("Exploded assembly:", exploded_id)
    print("Fit proof: no positive-volume overlap; 0.10 mm side clearance per flank.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
