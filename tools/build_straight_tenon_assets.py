#!/usr/bin/env python3
"""Derive the straight-tenon print layout, animated GLB, and poster from STL parts.

Run with Blender:
  blender --background --python tools/build_straight_tenon_assets.py -- \
    --input-dir /path/to/part-stls \
    --layout-stl assets/downloads/straight-tenon_c-sweep-print-layout_v0.1.stl \
    --glb assets/models/straight-tenon_assembled_v0.1.glb \
    --poster assets/images/straight-tenon/v0.1/exploded-01.webp
"""

from __future__ import annotations

import argparse
import math
import os
import sys

import bpy
from mathutils import Vector


PARTS = {
    "rail": {
        "filename": "rail.stl",
        "name": "Mortise_Rail_C020_C050",
        "color": (0.76, 0.56, 0.34, 1.0),
    },
    "c20": {
        "filename": "c20.stl",
        "name": "Tenon_C020",
        "color": (0.86, 0.35, 0.12, 1.0),
        "explode": (-0.010, -0.034, 0.000),
    },
    "c30": {
        "filename": "c30.stl",
        "name": "Tenon_C030",
        "color": (0.90, 0.46, 0.16, 1.0),
        "explode": (-0.003, -0.030, 0.000),
    },
    "c40": {
        "filename": "c40.stl",
        "name": "Tenon_C040",
        "color": (0.91, 0.58, 0.23, 1.0),
        "explode": (0.003, -0.030, 0.000),
    },
    "c50": {
        "filename": "c50.stl",
        "name": "Tenon_C050",
        "color": (0.88, 0.69, 0.34, 1.0),
        "explode": (0.010, -0.034, 0.000),
    },
}

ANIMATION_NAME = "Explode"

PRINT_LAYOUT = {
    "rail": {"location_mm": (0.0, 0.0, 0.0), "rotation_x_deg": 90.0},
    "c20": {"location_mm": (-9.0, -31.0, 10.0), "rotation_x_deg": 0.0},
    "c30": {"location_mm": (-3.0, -31.0, 10.0), "rotation_x_deg": 0.0},
    "c40": {"location_mm": (3.0, -31.0, 10.0), "rotation_x_deg": 0.0},
    "c50": {"location_mm": (9.0, -31.0, 10.0), "rotation_x_deg": 0.0},
}


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--layout-stl", required=True)
    parser.add_argument("--glb", required=True)
    parser.add_argument("--poster", required=True)
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return parser.parse_args(argv)


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (
        bpy.data.meshes,
        bpy.data.materials,
        bpy.data.cameras,
        bpy.data.lights,
        bpy.data.actions,
    ):
        for item in list(block):
            block.remove(item)


def import_parts(input_dir: str) -> dict[str, bpy.types.Object]:
    result = {}
    for key, spec in PARTS.items():
        path = os.path.join(input_dir, spec["filename"])
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        before = set(bpy.data.objects)
        bpy.ops.wm.stl_import(filepath=path)
        imported = list(set(bpy.data.objects) - before)
        if len(imported) != 1:
            raise RuntimeError(f"Expected one object from {path}, found {len(imported)}")
        obj = imported[0]
        obj.name = spec["name"]
        obj.data.name = f"{spec['name']}_Mesh"
        result[key] = obj
    return result


def select_only(objects) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = list(objects)[0]


def build_print_layout(input_dir: str, output_path: str) -> None:
    clear_scene()
    objects = import_parts(input_dir)
    for key, obj in objects.items():
        layout = PRINT_LAYOUT[key]
        obj.location = layout["location_mm"]
        obj.rotation_euler[0] = math.radians(layout["rotation_x_deg"])
    select_only(objects.values())
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    bpy.ops.wm.stl_export(
        filepath=output_path,
        ascii_format=False,
        export_selected_objects=True,
        global_scale=1.0,
        use_scene_unit=False,
        forward_axis="Y",
        up_axis="Z",
        apply_modifiers=True,
    )


def material(name: str, color) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    principled = mat.node_tree.nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value = color
    principled.inputs["Roughness"].default_value = 0.68
    principled.inputs["Metallic"].default_value = 0.0
    return mat


def explode_curves(obj: bpy.types.Object, action: bpy.types.Action):
    """Return the location f-curves for obj, on slotted (4.4+) and legacy actions."""
    if hasattr(action, "fcurves"):
        return list(action.fcurves)
    slot = obj.animation_data.action_slot
    for layer in action.layers:
        for strip in layer.strips:
            channelbag = strip.channelbag(slot)
            if channelbag is not None:
                return list(channelbag.fcurves)
    return []


def add_explode_animation(obj: bpy.types.Object, action: bpy.types.Action, offset) -> None:
    """Keyframe one part pulling out of the rail, inside the shared Explode action.

    All animated parts share a single action so the glTF exporter emits exactly one
    animation clip named "Explode" instead of one clip per part. On Blender 4.4+ each
    object gets its own slot in that action; on older builds the action is shared
    directly.
    """
    animation = obj.animation_data_create()
    animation.action = action
    if hasattr(action, "slots"):
        slot = action.slots.new(id_type="OBJECT", name=obj.name)
        animation.action_slot = slot

    for frame in (1, 12):
        obj.location = (0.0, 0.0, 0.0)
        obj.keyframe_insert(data_path="location", frame=frame)
    for frame in (58, 72):
        obj.location = offset
        obj.keyframe_insert(data_path="location", frame=frame)

    for curve in explode_curves(obj, action):
        for key in curve.keyframe_points:
            key.interpolation = "BEZIER"
            key.handle_left_type = "AUTO_CLAMPED"
            key.handle_right_type = "AUTO_CLAMPED"


def look_at(obj: bpy.types.Object, target) -> None:
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def build_web_model(input_dir: str, glb_path: str, poster_path: str) -> None:
    clear_scene()
    objects = import_parts(input_dir)
    explode_action = bpy.data.actions.new(ANIMATION_NAME)
    for key, obj in objects.items():
        obj.scale = (0.001, 0.001, 0.001)
        select_only((obj,))
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        obj.data.materials.append(material(f"PLA_{key.upper()}", PARTS[key]["color"]))
        obj["asset_version"] = "v0.1"
        obj["source"] = "Onshape Straight Tenon C-Sweep v0.1"
        if key != "rail":
            obj["total_clearance_mm"] = float(key[1:]) / 100.0
            add_explode_animation(obj, explode_action, PARTS[key]["explode"])

    scene = bpy.context.scene
    scene.name = ANIMATION_NAME
    scene.frame_start = 1
    scene.frame_end = 72
    scene.render.fps = 30
    scene.frame_set(1)
    select_only(objects.values())
    os.makedirs(os.path.dirname(glb_path), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format="GLB",
        use_selection=True,
        export_animations=True,
        export_animation_mode="ACTIONS",
        export_merge_animation="ACTION",
        export_optimize_animation_size=True,
        export_optimize_animation_keep_anim_object=True,
        export_extras=True,
        export_cameras=False,
        export_lights=False,
        export_yup=True,
        export_apply=False,
        export_copyright="Printable Joinery Atlas · CAD-derived asset v0.1",
    )

    scene.frame_set(72)
    camera_data = bpy.data.cameras.new("Poster_Camera")
    camera = bpy.data.objects.new("Poster_Camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (0.105, -0.145, 0.080)
    look_at(camera, (0.0, -0.014, -0.002))
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 0.115
    scene.camera = camera

    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "WORLD"
    scene.display.shading.curvature_ridge_factor = 1.8
    scene.display.shading.curvature_valley_factor = 1.2
    scene.display.shading.background_type = "VIEWPORT"
    scene.display.shading.background_color = (0.94, 0.925, 0.89)
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    image_format = "WEBP" if poster_path.lower().endswith(".webp") else "PNG"
    scene.render.image_settings.file_format = image_format
    if image_format == "WEBP":
        scene.render.image_settings.quality = 92
    # Workbench renders through the scene view transform; AgX would desaturate the
    # PLA colors and the paper background away from the palette used on the site.
    scene.view_settings.view_transform = "Standard"
    scene.render.filepath = poster_path
    os.makedirs(os.path.dirname(poster_path), exist_ok=True)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    args = arguments()
    build_print_layout(args.input_dir, os.path.abspath(args.layout_stl))
    build_web_model(args.input_dir, os.path.abspath(args.glb), os.path.abspath(args.poster))
    print(f"layout_stl={os.path.abspath(args.layout_stl)}")
    print(f"glb={os.path.abspath(args.glb)}")
    print(f"poster={os.path.abspath(args.poster)}")


if __name__ == "__main__":
    main()
