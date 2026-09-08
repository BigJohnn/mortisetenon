#!/usr/bin/env python3
"""Validate the design-first book architecture without changing asset evidence."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "content" / "design_catalog_v0.1.json"
FIRST_WAVE_CONTENT = ROOT / "content" / "first_wave_v0.1.json"


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def unique(values: list[str], label: str, errors: list[str]) -> None:
    counts = Counter(values)
    duplicates = sorted(value for value, count in counts.items() if count > 1)
    require(not duplicates, f"duplicate {label}: {', '.join(duplicates)}", errors)


def validate(catalog_path: Path) -> list[str]:
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    first_wave = json.loads(FIRST_WAVE_CONTENT.read_text(encoding="utf-8"))
    errors: list[str] = []
    targets = data["editorial_targets"]
    joints = data["joints"]
    works = data["works"]
    families = data["families"]
    labs = data["experiment_chapters"]
    sources = data["sources"]

    require(len(joints) == targets["basic_joint_entries"], "basic-joint target does not match catalog", errors)
    require(len(works) == targets["integrated_work_cases"], "work target does not match catalog", errors)
    require(len(labs) == targets["experiment_chapters"], "experiment target does not match catalog", errors)
    require(len(families) == 8, "the 24-entry architecture must contain eight teaching families", errors)

    first_target = targets["first_design_wave"]
    require(sum(joint["wave"] == "FIRST_10" for joint in joints) == first_target["basic_joint_entries"], "FIRST_10 count does not match target", errors)
    require(sum(work["wave"] == "FIRST_3" for work in works) == first_target["integrated_work_cases"], "FIRST_3 count does not match target", errors)

    unique([joint["id"] for joint in joints], "joint id", errors)
    unique([joint["index"] for joint in joints], "joint index", errors)
    unique([work["id"] for work in works], "work id", errors)
    unique([work["index"] for work in works], "work index", errors)
    unique([family["id"] for family in families], "family id", errors)

    family_ids = {family["id"] for family in families}
    work_ids = {work["index"] for work in works}
    joint_ids = {joint["id"] for joint in joints}
    source_ids = set(sources)
    family_counts = Counter(joint["family_id"] for joint in joints)
    for family_id in family_ids:
        require(family_counts[family_id] == 3, f"{family_id} must contain exactly three joints", errors)

    allowed_stages = {"IMPLEMENTED", "DESIGN_BRIEF", "CATALOG_SLOT"}
    detailed_fields = ("teaching_goal", "assembly_action", "key_parameters", "future_experiment", "work_ids")
    for joint in joints:
        prefix = f"joint {joint['index']} {joint['name_cn']}"
        require(joint["family_id"] in family_ids, f"{prefix} references unknown family", errors)
        require(joint["design_stage"] in allowed_stages, f"{prefix} has unknown design stage", errors)
        require(set(joint.get("source_ids", [])) <= source_ids, f"{prefix} references unknown source", errors)
        require(set(joint.get("work_ids", [])) <= work_ids, f"{prefix} references unknown work", errors)
        if joint["wave"] == "FIRST_10":
            for field in detailed_fields:
                require(bool(joint.get(field)), f"{prefix} is missing detailed field {field}", errors)
        if chapter_path := joint.get("chapter_path"):
            require((ROOT / chapter_path).is_file(), f"{prefix} chapter path does not exist: {chapter_path}", errors)

    for work in works:
        prefix = f"work {work['index']} {work['name_cn']}"
        require(work["design_stage"] in allowed_stages, f"{prefix} has unknown design stage", errors)
        require(set(work["joint_ids"]) <= joint_ids, f"{prefix} references unknown joint", errors)
        if work["wave"] == "FIRST_3":
            require(bool(work.get("design_questions")), f"{prefix} needs design questions in FIRST_3", errors)
        if case_path := work.get("case_path"):
            require((ROOT / case_path).is_file(), f"{prefix} case path does not exist: {case_path}", errors)

    for lab in labs:
        if path := lab.get("path"):
            require((ROOT / path).is_file(), f"lab path does not exist: {path}", errors)

    for source_id, source in sources.items():
        if path := source.get("path"):
            require((ROOT / path).is_file(), f"source {source_id} path does not exist: {path}", errors)

    first_joint_ids = {joint["id"] for joint in joints if joint["wave"] == "FIRST_10"}
    first_work_ids = {work["id"] for work in works if work["wave"] == "FIRST_3"}
    catalog_joints_by_id = {joint["id"]: joint for joint in joints}
    catalog_works_by_id = {work["id"]: work for work in works}
    content_joints = first_wave["joints"]
    content_works = first_wave["works"]
    content_sources = first_wave["sources"]

    require(len(content_joints) == 10, "first-wave content must contain 10 joints", errors)
    require(len(content_works) == 3, "first-wave content must contain 3 works", errors)
    require({joint["id"] for joint in content_joints} == first_joint_ids, "first-wave joint ids do not match design catalog", errors)
    require({work["id"] for work in content_works} == first_work_ids, "first-wave work ids do not match design catalog", errors)
    unique([joint["index"] for joint in content_joints], "first-wave joint index", errors)
    unique([work["index"] for work in content_works], "first-wave work index", errors)

    assistance_items: list[dict] = []
    allowed_review_states = {"EXISTING_CHAPTER", "READY_FOR_CAD", "NEEDS_USER", "PROVISIONAL_MAPPING"}
    joint_fields = (
        "one_sentence",
        "teaching_question",
        "confirmed",
        "design_proposal",
        "assembly_steps",
        "parameters",
        "cad_deliverables",
        "experiment_debt",
    )
    for joint in content_joints:
        prefix = f"first-wave joint {joint['index']} {joint['name_cn']}"
        require(joint["name_cn"] == catalog_joints_by_id[joint["id"]]["name_cn"], f"{prefix} name does not match design catalog", errors)
        require(joint["review_state"] in allowed_review_states, f"{prefix} has unknown review state", errors)
        for field in joint_fields:
            require(bool(joint.get(field)), f"{prefix} is missing {field}", errors)
        require(len(joint.get("assembly_steps", [])) == 4, f"{prefix} must have four assembly steps", errors)
        require(bool(joint.get("design_proposal", {}).get("parts")), f"{prefix} needs part roles", errors)
        require(set(joint.get("source_ids", [])) <= set(content_sources), f"{prefix} references unknown content source", errors)
        if chapter_path := joint.get("chapter_path"):
            require((ROOT / chapter_path).is_file(), f"{prefix} chapter path does not exist: {chapter_path}", errors)
        assistance_items.extend(joint.get("user_assistance", []))

    work_fields = (
        "one_sentence",
        "teaching_question",
        "confirmed",
        "functional_brief",
        "parts",
        "joint_map",
        "assembly_steps",
        "cad_deliverables",
        "experiment_debt",
    )
    for work in content_works:
        prefix = f"first-wave work {work['index']} {work['name_cn']}"
        require(work["name_cn"] == catalog_works_by_id[work["id"]]["name_cn"], f"{prefix} name does not match design catalog", errors)
        require(work["review_state"] in allowed_review_states, f"{prefix} has unknown review state", errors)
        for field in work_fields:
            require(bool(work.get(field)), f"{prefix} is missing {field}", errors)
        require(len(work.get("assembly_steps", [])) == 4, f"{prefix} must have four assembly/audit steps", errors)
        require({item["joint_id"] for item in work.get("joint_map", [])} <= joint_ids, f"{prefix} maps an unknown joint", errors)
        require({item["joint_id"] for item in work.get("joint_map", [])} == set(catalog_works_by_id[work["id"]]["joint_ids"]), f"{prefix} joint map does not match design catalog", errors)
        require(set(work.get("source_ids", [])) <= set(content_sources), f"{prefix} references unknown content source", errors)
        if case_path := work.get("case_path"):
            require((ROOT / case_path).is_file(), f"{prefix} case path does not exist: {case_path}", errors)
        assistance_items.extend(work.get("user_assistance", []))

    assistance_ids = [item["id"] for item in assistance_items]
    unique(assistance_ids, "user-assistance id", errors)
    require(len(assistance_ids) == 9, "first-wave content must preserve all nine author decisions", errors)
    allowed_decision_states = {"OPEN", "RESOLVED"}
    for item in assistance_items:
        require(item.get("status") in allowed_decision_states, f"author decision {item['id']} has unknown status", errors)
        if item.get("status") == "RESOLVED":
            require(bool(item.get("resolution")), f"resolved author decision {item['id']} needs a resolution", errors)
    open_ids = {item["id"] for item in assistance_items if item.get("status") == "OPEN"}
    resolved_ids = {item["id"] for item in assistance_items if item.get("status") == "RESOLVED"}
    require(not open_ids, "first-wave content must have no open author decisions", errors)
    require(resolved_ids == {f"U{index:02d}" for index in range(1, 10)}, "all nine author decisions must be resolved", errors)
    require(not any(entry["review_state"] == "NEEDS_USER" for entry in [*content_joints, *content_works]), "no first-wave entry may remain NEEDS_USER after all decisions resolve", errors)
    for source_id, source in content_sources.items():
        require(bool(source.get("url") or source.get("path")), f"content source {source_id} needs a URL or local path", errors)
        if path := source.get("path"):
            require((ROOT / path).is_file(), f"content source {source_id} path does not exist: {path}", errors)
    baxian_source = content_sources.get("onshape_baxian_source", {})
    require(baxian_source.get("source_microversion") == "f9e8c517a1e9b12a6a5c4c4b", "Baxian source microversion is not the confirmed baseline", errors)
    require(baxian_source.get("assembly_instance_count") == 0, "Baxian source must record the empty audited assembly", errors)
    require(sum(baxian_source.get("part_inventory", {}).values()) == 30, "Baxian source inventory must total 30 solids", errors)
    require(len(baxian_source.get("variables", {})) == 6, "Baxian source must preserve the six audited variables", errors)

    require((ROOT / "first-wave.html").is_file(), "first-wave content page does not exist", errors)
    require((ROOT / "assets" / "first-wave.js").is_file(), "first-wave renderer does not exist", errors)
    require((ROOT / "assets" / "first-wave.css").is_file(), "first-wave stylesheet does not exist", errors)

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog", nargs="?", type=Path, default=DEFAULT_CATALOG)
    args = parser.parse_args()
    errors = validate(args.catalog.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Design catalog valid: 24 joints / 6 works / first wave 10+3 / 8 families x 3 / 9 author decisions (9 resolved, 0 open).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
