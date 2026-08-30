#!/usr/bin/env python3
"""Export the frozen dovetail assembly states from Onshape as browser-ready GLB files."""

from __future__ import annotations

import io
import zipfile
import base64
import copy
import json
import os
import struct
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


DOCUMENT_ID = "aa8b70cbf3d6f40dfdcb967a"
VERSION_ID = "cc81e1a378a8fb2804c35364"
STATES = {
    "assembled": "fd7c8ae946a2204d062c1af9",
    "exploded": "f162ab40c560153c427570be",
}
OUTPUT_DIR = Path("assets/models")


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
        with urllib.request.urlopen(req, timeout=90) as response:
            return response.read(), dict(response.headers.items())
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Onshape API returned HTTP {error.code}: {detail}") from error


def json_request(method: str, path: str, body: dict | None = None) -> dict:
    raw, _ = request(method, path, body)
    return json.loads(raw) if raw else {}


def remap(value: int | None, offset: int) -> int | None:
    return value + offset if value is not None else None


def source_is_tail(source: dict) -> bool:
    """The tail is the exported part originally located at positive X."""
    positions = [
        source["accessors"][primitive["attributes"]["POSITION"]]
        for mesh in source.get("meshes", [])
        for primitive in mesh.get("primitives", [])
        if "POSITION" in primitive.get("attributes", {})
    ]
    return bool(positions) and min(item["min"][0] for item in positions) > 0


def add_explode_animation(merged: dict, tail_node: int) -> None:
    """Add a 2.4-second slide from the assembled pose to the verified exploded pose."""
    keyframes = struct.pack("<2f", 0.0, 2.4)
    translations = struct.pack("<6f", -0.070, 0.0, 0.0, -0.070, -0.032, 0.0)
    payload = keyframes + translations
    data_uri = "data:application/octet-stream;base64," + base64.b64encode(payload).decode()
    buffer_index = len(merged["buffers"])
    input_view = len(merged["bufferViews"])
    output_view = input_view + 1
    input_accessor = len(merged["accessors"])
    output_accessor = input_accessor + 1
    merged["buffers"].append({"byteLength": len(payload), "uri": data_uri})
    merged["bufferViews"].extend(
        [
            {"buffer": buffer_index, "byteOffset": 0, "byteLength": len(keyframes)},
            {"buffer": buffer_index, "byteOffset": len(keyframes), "byteLength": len(translations)},
        ]
    )
    merged["accessors"].extend(
        [
            {"bufferView": input_view, "componentType": 5126, "count": 2, "type": "SCALAR", "min": [0], "max": [2.4]},
            {"bufferView": output_view, "componentType": 5126, "count": 2, "type": "VEC3"},
        ]
    )
    merged["animations"] = [
        {
            "name": "Explode",
            "samplers": [{"input": input_accessor, "output": output_accessor, "interpolation": "LINEAR"}],
            "channels": [{"sampler": 0, "target": {"node": tail_node, "path": "translation"}}],
        }
    ]


def merge_part_scenes(paths: list[Path], output: Path, label: str, tail_y_offset: float) -> Path:
    """Join the exported part scenes and restore their verified assembly transforms."""
    merged: dict = {
        "asset": {"version": "2.0", "generator": "Printable Joinery Atlas", "copyright": "Onshape assembly export"},
        "scene": 0,
        "scenes": [{"name": label, "nodes": []}],
        "nodes": [],
        "meshes": [],
        "materials": [],
        "buffers": [],
        "bufferViews": [],
        "accessors": [],
        "extensionsUsed": ["PTC_onshape_metadata"],
    }
    tail_node = None
    for path in paths:
        source = json.loads(path.read_text())
        tail = source_is_tail(source)
        offsets = {
            "buffer": len(merged["buffers"]),
            "bufferView": len(merged["bufferViews"]),
            "accessor": len(merged["accessors"]),
            "material": len(merged["materials"]),
            "mesh": len(merged["meshes"]),
            "node": len(merged["nodes"]),
        }
        merged["buffers"].extend(copy.deepcopy(source.get("buffers", [])))
        for view in source.get("bufferViews", []):
            item = copy.deepcopy(view)
            item["buffer"] = remap(item.get("buffer"), offsets["buffer"])
            merged["bufferViews"].append(item)
        for accessor in source.get("accessors", []):
            item = copy.deepcopy(accessor)
            item["bufferView"] = remap(item.get("bufferView"), offsets["bufferView"])
            sparse = item.get("sparse")
            if sparse:
                sparse["indices"]["bufferView"] = remap(sparse["indices"].get("bufferView"), offsets["bufferView"])
                sparse["values"]["bufferView"] = remap(sparse["values"].get("bufferView"), offsets["bufferView"])
            merged["accessors"].append(item)
        merged["materials"].extend(copy.deepcopy(source.get("materials", [])))
        for mesh in source.get("meshes", []):
            item = copy.deepcopy(mesh)
            for primitive in item.get("primitives", []):
                primitive["attributes"] = {
                    key: remap(index, offsets["accessor"])
                    for key, index in primitive.get("attributes", {}).items()
                }
                primitive["indices"] = remap(primitive.get("indices"), offsets["accessor"])
                primitive["material"] = remap(primitive.get("material"), offsets["material"])
                if "targets" in primitive:
                    primitive["targets"] = [
                        {key: remap(index, offsets["accessor"]) for key, index in target.items()}
                        for target in primitive["targets"]
                    ]
            merged["meshes"].append(item)
        for node in source.get("nodes", []):
            item = copy.deepcopy(node)
            item["mesh"] = remap(item.get("mesh"), offsets["mesh"])
            if "children" in item:
                item["children"] = [remap(index, offsets["node"]) for index in item["children"]]
            if tail:
                if "matrix" in item:
                    raise RuntimeError("Unexpected matrix transform in Onshape part export")
                current = item.get("translation", [0, 0, 0])
                item["translation"] = [current[0] - 0.070, current[1] + tail_y_offset, current[2]]
                tail_node = offsets["node"]
            merged["nodes"].append(item)
        scene = source.get("scenes", [])[source.get("scene", 0)]
        merged["scenes"][0]["nodes"].extend(
            remap(index, offsets["node"]) for index in scene.get("nodes", [])
        )
    if tail_y_offset == 0.0 and tail_node is not None:
        add_explode_animation(merged, tail_node)
    output.write_text(json.dumps(merged, ensure_ascii=False, separators=(",", ":")))
    return output


def export_state(name: str, element_id: str) -> Path:
    job = json_request(
        "POST",
        f"/api/v11/assemblies/d/{DOCUMENT_ID}/v/{VERSION_ID}/e/{element_id}/export/gltf",
        {
            "meshParams": {
                "angularTolerance": 0.001,
                "distanceTolerance": 0.001,
                "maximumChordLength": 0.01,
                "resolution": "FINE",
                "unit": "METER",
            },
            "storeInDocument": False,
        },
    )
    translation_id = job.get("id") or job.get("translationId")
    if not translation_id:
        raise RuntimeError(f"Could not find translation ID in export response: {job}")

    for _ in range(60):
        status = json_request("GET", f"/api/v11/translations/{translation_id}")
        state = str(status.get("requestState", "")).upper()
        if state == "DONE":
            external_ids = status.get("resultExternalDataIds") or []
            if len(external_ids) != 1:
                raise RuntimeError(f"Expected one exported GLB, received: {status}")
            raw, headers = request(
                "GET", f"/api/v6/documents/d/{DOCUMENT_ID}/externaldata/{external_ids[0]}"
            )
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            output = OUTPUT_DIR / f"dovetail_{name}_v0.2.glb"
            if raw[:4] == b"glTF":
                output.write_bytes(raw)
                return output

            content_type = headers.get("Content-Type", "")
            if raw[:4] != bytes.fromhex("504b0304") or "zip" not in content_type:
                raise RuntimeError(
                    "Onshape export is neither a GLB nor a ZIP package "
                    f"(content type {content_type or 'unknown'}; magic {raw[:12].hex()})"
                )
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                members = [item for item in archive.infolist() if not item.is_dir()]
                names = [item.filename for item in members]
                glb_names = [item for item in names if item.lower().endswith(".glb")]
                if len(glb_names) == 1:
                    output.write_bytes(archive.read(glb_names[0]))
                    return output
                gltf_names = [item for item in names if item.lower().endswith(".gltf")]
                if not gltf_names:
                    raise RuntimeError(f"Could not identify a scene file in Onshape export: {names}")
                package_dir = OUTPUT_DIR / f"dovetail_{name}_v0.2"
                package_dir.mkdir(parents=True, exist_ok=True)
                for item in members:
                    relative = Path(item.filename)
                    if relative.is_absolute() or ".." in relative.parts:
                        raise RuntimeError(f"Unsafe path in Onshape export: {item.filename}")
                    target = package_dir / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.read(item))
                if len(gltf_names) == 1:
                    return package_dir / gltf_names[0]
                return merge_part_scenes(
                    [package_dir / gltf_name for gltf_name in gltf_names],
                    OUTPUT_DIR / f"dovetail_{name}_v0.2.gltf",
                    f"Dovetail {name} v0.2",
                    -0.032 if name == "exploded" else 0.0,
                )
        if state in {"FAILED", "CANCELLED"}:
            raise RuntimeError(f"Onshape GLB export {name} failed: {status}")
        time.sleep(2)
    raise RuntimeError(f"Timed out waiting for the {name} GLB export")


def main() -> int:
    if not os.environ.get("ONSHAPE_ACCESS_KEY") or not os.environ.get("ONSHAPE_SECRET_KEY"):
        print("ONSHAPE_ACCESS_KEY and ONSHAPE_SECRET_KEY are required", file=sys.stderr)
        return 2
    for name, element_id in STATES.items():
        output = export_state(name, element_id)
        print(f"Exported {name}: {output} ({output.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, RuntimeError, urllib.error.URLError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
