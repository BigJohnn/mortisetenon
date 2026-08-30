#!/usr/bin/env python3
"""Export the frozen keyed-tenon assembly from Onshape as one browser-ready glTF.

Onshape's assembly glTF export writes every part in Part Studio coordinates and
drops the assembly transforms, so this script reads the transforms back from the
two assembly definitions -- the same ones ``tools/assemble_keyed_tenon.py``
verified -- and applies them here.  The ``Explode`` clip is the measured
difference between the mated and separated states: nothing about the motion is
typed into this file, so if the exploded assembly moves, the clip moves with it.

The export is also Z-up, which model-viewer is not, so the parts hang under one
root node that rotates the scene a quarter turn about X.
"""

from __future__ import annotations

import base64
import copy
import io
import json
import math
import os
import struct
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path


DOCUMENT_ID = "73de9c93248e073d85379a97"
VERSION_ID = "3aa8f29bde2c332836964647"          # keyed-tenon v0.7
ASSEMBLED = "8fc834ed7d4b7b8f20ba8ff1"
EXPLODED = "ae62a5499ac33f0ba5abc9f6"
SLUG = "keyed-tenon"
VERSION = "v0.7"
CLIP_SECONDS = 2.4
OUTPUT_DIR = Path("assets/models")

# Onshape models the joint standing on the world origin; recentring it here keeps
# model-viewer's default framing on the joint instead of on empty space.
RECENTRE = (0.0, 0.0, -0.009)
# Z-up (Onshape) to Y-up (glTF): a quarter turn about X, as a quaternion.
Y_UP = [-math.sin(math.pi / 4), 0.0, 0.0, math.cos(math.pi / 4)]


def request(method: str, path: str, body: dict | None = None) -> tuple[bytes, dict]:
    key = os.environ["ONSHAPE_ACCESS_KEY"]
    secret = os.environ["ONSHAPE_SECRET_KEY"]
    base_url = os.environ.get("ONSHAPE_BASE_URL", "https://cad.onshape.com").rstrip("/")
    headers = {
        "Accept": "application/json;charset=UTF-8; qs=0.09",
        "Authorization": "Basic " + base64.b64encode(f"{key}:{secret}".encode()).decode(),
    }
    payload = None
    if body is not None:
        payload = json.dumps(body).encode()
        headers["Content-Type"] = "application/json;charset=UTF-8; qs=0.09"
    req = urllib.request.Request(base_url + path, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            return response.read(), dict(response.headers.items())
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Onshape returned HTTP {error.code}: {detail}") from error


def json_request(method: str, path: str, body: dict | None = None) -> dict:
    raw, _ = request(method, path, body)
    return json.loads(raw) if raw else {}


def instance_name(raw: str) -> str:
    """Drop the ``<1>`` occurrence counter Onshape appends to instance names."""
    return raw.rsplit(" <", 1)[0].strip()


def placements(element_id: str) -> dict[str, tuple[float, float, float]]:
    """Where each part sits in one assembly state, in metres.

    Only translations are supported on purpose: the whole joint is built in its
    mated pose, so any rotation appearing here would mean the assembly no longer
    matches the Part Studio and the geometry should be re-checked, not silently
    baked into a web model.
    """
    definition = json_request(
        "GET", f"/api/v10/assemblies/d/{DOCUMENT_ID}/v/{VERSION_ID}/e/{element_id}")
    root = definition["rootAssembly"]
    by_id = {item["id"]: item for item in root["instances"]}
    found: dict[str, tuple[float, float, float]] = {}
    for occurrence in root["occurrences"]:
        name = instance_name(by_id[occurrence["path"][-1]]["name"])
        transform = occurrence["transform"]
        rotation = [transform[0:3], transform[4:7], transform[8:11]]
        identity = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        if any(abs(a - b) > 1e-9 for row, want in zip(rotation, identity)
               for a, b in zip(row, want)):
            raise RuntimeError(f"{name} is rotated in the assembly; refusing to guess "
                               "how that should be baked into the web model")
        found[name] = (transform[3], transform[7], transform[11])
    return found


def export_parts() -> dict[str, dict]:
    """Run the glTF translation for the mated assembly, one scene file per part."""
    job = json_request(
        "POST",
        f"/api/v11/assemblies/d/{DOCUMENT_ID}/v/{VERSION_ID}/e/{ASSEMBLED}/export/gltf",
        {
            "meshParams": {
                "angularTolerance": 0.05,
                "distanceTolerance": 0.0002,
                "maximumChordLength": 0.01,
                "resolution": "MEDIUM",
                "unit": "METER",
            },
            "storeInDocument": False,
        },
    )
    translation_id = job.get("id") or job.get("translationId")
    if not translation_id:
        raise RuntimeError(f"No translation ID in the export response: {job}")

    for _ in range(90):
        status = json_request("GET", f"/api/v11/translations/{translation_id}")
        state = str(status.get("requestState", "")).upper()
        if state in {"FAILED", "CANCELLED"}:
            raise RuntimeError(f"Onshape glTF export failed: {status}")
        if state != "DONE":
            time.sleep(2)
            continue
        external_ids = status.get("resultExternalDataIds") or []
        if len(external_ids) != 1:
            raise RuntimeError(f"Expected one exported package, received: {status}")
        raw, headers = request(
            "GET", f"/api/v6/documents/d/{DOCUMENT_ID}/externaldata/{external_ids[0]}")
        if raw[:4] != bytes.fromhex("504b0304"):
            raise RuntimeError(
                "Onshape returned something other than a ZIP package "
                f"(content type {headers.get('Content-Type', 'unknown')}; magic {raw[:12].hex()})")
        package_dir = OUTPUT_DIR / f"{SLUG}_parts_{VERSION}"
        package_dir.mkdir(parents=True, exist_ok=True)
        scenes: dict[str, dict] = {}
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            for item in archive.infolist():
                if item.is_dir() or not item.filename.lower().endswith(".gltf"):
                    continue
                relative = Path(item.filename)
                if relative.is_absolute() or ".." in relative.parts:
                    raise RuntimeError(f"Unsafe path in Onshape export: {item.filename}")
                target = package_dir / relative.name
                target.write_bytes(archive.read(item))
                scene = json.loads(target.read_text())
                name = next((node["name"] for node in scene.get("nodes", [])
                             if node.get("name")), relative.stem)
                scenes[name] = scene
        if not scenes:
            raise RuntimeError("No .gltf scene in the Onshape export")
        return scenes
    raise RuntimeError("Timed out waiting for the glTF export")


def remap(value: int | None, offset: int) -> int | None:
    return value + offset if value is not None else None


def merge(scenes: dict[str, dict], where: dict[str, tuple[float, float, float]],
          label: str) -> tuple[dict, dict[str, int]]:
    """Join the per-part scenes into one Y-up document, returning name -> node index."""
    merged: dict = {
        "asset": {"version": "2.0", "generator": "Printable Joinery Atlas",
                  "copyright": "Onshape assembly export"},
        "scene": 0,
        "scenes": [{"name": label, "nodes": [0]}],
        "nodes": [{"name": label, "rotation": Y_UP, "children": []}],
        "meshes": [], "materials": [],
        "buffers": [], "bufferViews": [], "accessors": [],
        "extensionsUsed": ["PTC_onshape_metadata"],
    }
    node_of: dict[str, int] = {}
    for name, source in sorted(scenes.items()):
        if len(source.get("nodes", [])) != 1:
            raise RuntimeError(f"Expected one node in the {name} export, "
                               f"found {len(source.get('nodes', []))}")
        offsets = {key: len(merged[plural]) for key, plural in (
            ("buffer", "buffers"), ("bufferView", "bufferViews"),
            ("accessor", "accessors"), ("material", "materials"),
            ("mesh", "meshes"))}
        merged["buffers"].extend(copy.deepcopy(source.get("buffers", [])))
        for view in source.get("bufferViews", []):
            item = copy.deepcopy(view)
            item["buffer"] = remap(item.get("buffer"), offsets["buffer"])
            merged["bufferViews"].append(item)
        for accessor in source.get("accessors", []):
            item = copy.deepcopy(accessor)
            item["bufferView"] = remap(item.get("bufferView"), offsets["bufferView"])
            merged["accessors"].append(item)
        merged["materials"].extend(copy.deepcopy(source.get("materials", [])))
        for mesh in source.get("meshes", []):
            item = copy.deepcopy(mesh)
            for primitive in item.get("primitives", []):
                primitive["attributes"] = {
                    key: remap(index, offsets["accessor"])
                    for key, index in primitive.get("attributes", {}).items()}
                primitive["indices"] = remap(primitive.get("indices"), offsets["accessor"])
                primitive["material"] = remap(primitive.get("material"), offsets["material"])
            merged["meshes"].append(item)
        node = copy.deepcopy(source["nodes"][0])
        if "matrix" in node:
            raise RuntimeError(f"Unexpected matrix transform in the {name} export")
        node["mesh"] = remap(node.get("mesh"), offsets["mesh"])
        node["name"] = name
        node["translation"] = [where[name][axis] + RECENTRE[axis] for axis in range(3)]
        node_of[name] = len(merged["nodes"])
        merged["nodes"][0]["children"].append(len(merged["nodes"]))
        merged["nodes"].append(node)
    return merged, node_of


def add_explode_clip(merged: dict, moves: dict[int, tuple[float, float, float]]) -> None:
    """One clip: frame 0 is the assembly drawing, the last frame the exploded one."""
    payload = bytearray(struct.pack("<2f", 0.0, CLIP_SECONDS))
    buffer_index = len(merged["buffers"])
    merged["bufferViews"].append(
        {"buffer": buffer_index, "byteOffset": 0, "byteLength": len(payload)})
    input_accessor = len(merged["accessors"])
    merged["accessors"].append({"bufferView": len(merged["bufferViews"]) - 1,
                                "componentType": 5126, "count": 2, "type": "SCALAR",
                                "min": [0.0], "max": [CLIP_SECONDS]})
    samplers, channels = [], []
    for node_index, delta in sorted(moves.items()):
        start = merged["nodes"][node_index]["translation"]
        end = [start[axis] + delta[axis] for axis in range(3)]
        merged["bufferViews"].append({"buffer": buffer_index, "byteOffset": len(payload),
                                      "byteLength": 24})
        payload += struct.pack("<6f", *start, *end)
        merged["accessors"].append({"bufferView": len(merged["bufferViews"]) - 1,
                                    "componentType": 5126, "count": 2, "type": "VEC3"})
        channels.append({"sampler": len(samplers),
                         "target": {"node": node_index, "path": "translation"}})
        samplers.append({"input": input_accessor, "output": len(merged["accessors"]) - 1,
                         "interpolation": "LINEAR"})
    merged["buffers"].append({
        "byteLength": len(payload),
        "uri": "data:application/octet-stream;base64," + base64.b64encode(bytes(payload)).decode(),
    })
    merged["animations"] = [{"name": "Explode", "samplers": samplers, "channels": channels}]


def main() -> int:
    if not os.environ.get("ONSHAPE_ACCESS_KEY") or not os.environ.get("ONSHAPE_SECRET_KEY"):
        print("ONSHAPE_ACCESS_KEY and ONSHAPE_SECRET_KEY are required", file=sys.stderr)
        return 2
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    mated = placements(ASSEMBLED)
    apart = placements(EXPLODED)
    if set(mated) != set(apart):
        raise RuntimeError(f"The two assembly states hold different parts: "
                           f"{sorted(mated)} vs {sorted(apart)}")
    scenes = export_parts()
    if set(scenes) != set(mated):
        raise RuntimeError(f"Exported parts {sorted(scenes)} do not match the assembly "
                           f"instances {sorted(mated)}")

    merged, node_of = merge(scenes, mated, f"楔钉榫 keyed tenon {VERSION}")
    moves = {}
    for name, node_index in node_of.items():
        delta = tuple(apart[name][axis] - mated[name][axis] for axis in range(3))
        if max(abs(value) for value in delta) > 1e-6:
            moves[node_index] = delta
            print(f"  {name}: separates by "
                  f"({delta[0] * 1000:+.1f}, {delta[1] * 1000:+.1f}, {delta[2] * 1000:+.1f}) mm")
        else:
            print(f"  {name}: stays still (reference part)")
    if not moves:
        raise RuntimeError("The two states are identical; there is nothing to animate")
    add_explode_clip(merged, moves)

    output = OUTPUT_DIR / f"{SLUG}_assembled_{VERSION}.gltf"
    output.write_text(json.dumps(merged, ensure_ascii=False, separators=(",", ":")))
    print(f"\nwrote {output} ({output.stat().st_size:,} bytes), "
          f"clip 'Explode' {CLIP_SECONDS} s over {len(moves)} of {len(node_of)} parts")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, RuntimeError, urllib.error.URLError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
