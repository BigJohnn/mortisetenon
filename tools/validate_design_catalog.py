#!/usr/bin/env python3
"""Validate the design-first book architecture without changing asset evidence."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "content" / "design_catalog_v0.1.json"


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def unique(values: list[str], label: str, errors: list[str]) -> None:
    counts = Counter(values)
    duplicates = sorted(value for value, count in counts.items() if count > 1)
    require(not duplicates, f"duplicate {label}: {', '.join(duplicates)}", errors)


def validate(catalog_path: Path) -> list[str]:
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
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
    print("Design catalog valid: 24 joints / 6 works / first wave 10+3 / 8 families x 3.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
