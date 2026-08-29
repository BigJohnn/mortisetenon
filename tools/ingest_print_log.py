#!/usr/bin/env python3
"""Validate an exported print log, file it, and move the asset to PRINT_VERIFIED.

This is the step where physical evidence enters the repository, so it is the one
step that must not be done by hand. The tool checks the exported JSON against
three independent things — the recording form in the lab page, the release
manifest, and the asset contract's own requirements — before writing anything.

    # check only, touch nothing
    python3 tools/ingest_print_log.py --check ~/Downloads/2026-08-31_straight-tenon_v0.1_run-01.json

    # file it and promote the asset
    python3 tools/ingest_print_log.py ~/Downloads/2026-08-31_straight-tenon_v0.1_run-01.json

    # regenerate the blank CSV templates from the current forms
    python3 tools/ingest_print_log.py --emit-templates
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import re
import sys
from pathlib import Path

from print_log_spec import FIT_CLASSES, REPO_ROOT, FormSpec, load_form_specs

MANIFEST = REPO_ROOT / "assets" / "downloads" / "manifest.json"
LOG_DIR = REPO_ROOT / "content" / "print-logs"
SCHEMA_VERSION = "0.2"

RUN_COLUMNS = [
    "schema_version", "experiment_id", "recorded_at", "asset_id", "asset_version",
    "asset_sha256", "printer_model", "slicer", "slicer_version", "material",
    "material_brand", "nozzle_mm", "layer_height_mm", "walls", "infill_percent",
    "orientation", "scale_percent",
]

REQUIRED_CONDITIONS = [
    "printer_model", "slicer", "material", "nozzle_mm",
    "layer_height_mm", "walls", "infill_percent", "orientation", "scale_percent",
]


class LogError(Exception):
    """A validation failure that must stop the log from being filed."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9-]+", "-", str(value).strip().lower()).strip("-")
    return slug or "run-01"


def validate(log: dict, specs: dict[str, FormSpec], manifest: dict) -> tuple[FormSpec, dict, list[str]]:
    """Return (form spec, manifest entry, warnings) or raise LogError."""
    problems: list[str] = []
    warnings: list[str] = []

    if log.get("schema_version") != SCHEMA_VERSION:
        problems.append(
            f"schema_version is {log.get('schema_version')!r}, expected {SCHEMA_VERSION!r}. "
            "Re-export from the current Clearance Lab page."
        )

    asset = log.get("asset") or {}
    asset_id, version, sha = asset.get("id"), asset.get("version"), asset.get("sha256")
    spec = specs.get(asset_id)
    if spec is None:
        raise LogError(
            f"unknown asset id {asset_id!r}; the lab page declares {sorted(specs)}"
        )
    if version != spec.version:
        problems.append(f"asset.version is {version!r}, the form records {spec.version!r}")
    if sha != spec.sha256:
        problems.append(
            f"asset.sha256 does not match the file the form records.\n"
            f"    log:  {sha}\n    form: {spec.sha256}\n"
            "    A log must be tied to the exact geometry that was printed."
        )

    entry = next(
        (a for a in manifest["assets"] if a["id"] == asset_id and a["version"] == version),
        None,
    )
    if entry is None:
        problems.append(f"{asset_id}@{version} is not in the release manifest")
    else:
        hashes = {d.get("sha256") for d in entry.get("derivatives", [])}
        hashes.update(d.get("sha256") for d in entry.get("build_inputs", []))
        source_sha = (entry.get("source") or {}).get("sha256")
        if source_sha:
            hashes.add(source_sha)
        if sha not in hashes:
            problems.append(
                f"asset.sha256 {sha} matches no file recorded for {asset_id}@{version} "
                "in the manifest"
            )

    experiment = log.get("experiment") or {}
    if not experiment.get("id"):
        problems.append("experiment.id is empty")
    recorded_at = experiment.get("recorded_at")
    try:
        dt.date.fromisoformat(str(recorded_at))
    except (TypeError, ValueError):
        problems.append(f"experiment.recorded_at is not an ISO date: {recorded_at!r}")

    conditions = log.get("print_conditions") or {}
    for key in REQUIRED_CONDITIONS:
        value = conditions.get(key)
        if value in (None, ""):
            problems.append(f"print_conditions.{key} is empty — a result without it cannot be reproduced")
    if conditions.get("orientation") and conditions["orientation"] != spec.orientation:
        warnings.append(
            f"orientation {conditions['orientation']!r} differs from the form default "
            f"{spec.orientation!r}; make sure the run notes explain the change"
        )

    results = log.get("results") or []
    recorded = [r.get("nominal_clearance_total_mm") for r in results]
    if recorded != spec.clearances:
        problems.append(
            f"results cover {recorded}, the form defines {spec.clearances}. "
            "Every rung needs a row, including the ones that failed."
        )

    for result in results:
        rung = result.get("nominal_clearance_total_mm")
        for name in spec.required_result_fields:
            if result.get(name) is None:
                problems.append(f"C={rung}: {name} is empty")
        unknown = set(result) - set(spec.result_fields) - {"nominal_clearance_total_mm"}
        if unknown:
            problems.append(f"C={rung}: unexpected fields {sorted(unknown)}")

        fit = result.get("fit_class")
        if fit is not None and fit not in FIT_CLASSES:
            problems.append(f"C={rung}: fit_class {fit!r} is not one of {list(FIT_CLASSES)}")
        for force_field in ("insertion_force_1_5", "withdrawal_force_1_5"):
            force = result.get(force_field)
            if force is not None and not (isinstance(force, int) and 1 <= force <= 5):
                problems.append(f"C={rung}: {force_field} must be an integer 1–5, got {force!r}")

    if not str(log.get("photo_refs") or "").strip():
        problems.append(
            "photo_refs is empty. The asset contract requires photo references before "
            "PRINT_VERIFIED, including any failure."
        )

    if problems:
        raise LogError("\n  - " + "\n  - ".join(problems))

    if not any(r.get("fit_class") in ("press-fit", "snug", "sliding") for r in results):
        warnings.append(
            "no rung assembled (every fit_class is jammed or loose). This is a valid "
            "recorded result, but it does not clear Gate A on its own."
        )

    return spec, entry, warnings


def to_csv(log: dict, spec: FormSpec) -> str:
    columns = [*RUN_COLUMNS, "nominal_clearance_total_mm", *spec.result_fields, "notes", "photo_refs"]
    conditions = log["print_conditions"]
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(columns)
    for result in log["results"]:
        row = {
            "schema_version": log["schema_version"],
            "experiment_id": log["experiment"]["id"],
            "recorded_at": log["experiment"]["recorded_at"],
            "asset_id": log["asset"]["id"],
            "asset_version": log["asset"]["version"],
            "asset_sha256": log["asset"]["sha256"],
            "notes": log.get("run_notes"),
            "photo_refs": log.get("photo_refs"),
            **{k: conditions.get(k) for k in RUN_COLUMNS if k in conditions},
            **result,
        }
        writer.writerow(["" if row.get(c) is None else row.get(c, "") for c in columns])
    return buffer.getvalue()


def emit_templates(specs: dict[str, FormSpec]) -> list[Path]:
    """Blank CSVs for filling in at the printer, one per asset, same columns as the export."""
    written = []
    for spec in specs.values():
        columns = [*RUN_COLUMNS, "nominal_clearance_total_mm", *spec.result_fields, "notes", "photo_refs"]
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(columns)
        for clearance in spec.clearances:
            prefilled = {
                "schema_version": SCHEMA_VERSION,
                "experiment_id": f"{spec.asset_id}-run-01",
                "asset_id": spec.asset_id,
                "asset_version": spec.version,
                "asset_sha256": spec.sha256,
                "material": "PLA",
                "nozzle_mm": 0.4,
                "layer_height_mm": 0.2,
                "walls": 3,
                "infill_percent": 15,
                "orientation": spec.orientation,
                "scale_percent": 100,
                "nominal_clearance_total_mm": f"{clearance:.2f}",
            }
            writer.writerow([prefilled.get(c, "") for c in columns])

        path = REPO_ROOT / "assets" / "downloads" / f"{spec.asset_id}_print-log-template_{spec.version}.csv"
        path.write_text(buffer.getvalue(), encoding="utf-8")
        written.append(path)
    return written


def ingest(source: Path, *, check_only: bool, force: bool, keep_state: bool) -> int:
    specs = load_form_specs()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    try:
        log = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        print(f"FAIL  {source}: not valid JSON ({error})", file=sys.stderr)
        return 1

    try:
        spec, entry, warnings = validate(log, specs, manifest)
    except LogError as error:
        print(f"FAIL  {source} is not a complete print log:{error}", file=sys.stderr)
        return 1

    for warning in warnings:
        print(f"WARN  {warning}")

    run_id = _slugify(log["experiment"]["id"])
    recorded_at = log["experiment"]["recorded_at"]
    target = LOG_DIR / f"{recorded_at}_{spec.asset_id}_{spec.version}_{run_id}.json"

    if check_only:
        print(f"OK    {source} is a complete print log for {spec.asset_id}@{spec.version}")
        print(f"      would file as {target.relative_to(REPO_ROOT)}")
        return 0

    if target.exists() and not force:
        print(
            f"FAIL  {target.relative_to(REPO_ROOT)} already exists. Filed logs are evidence and "
            "are not overwritten — use a new experiment id, or pass --force if you are "
            "correcting a mistake.",
            file=sys.stderr,
        )
        return 1

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log["evidence_state"] = "PRINT_LOG_FILED"
    target.write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    csv_target = target.with_suffix(".csv")
    csv_target.write_text(to_csv(log, spec), encoding="utf-8")

    record = {
        "path": str(target.relative_to(REPO_ROOT)),
        "csv_path": str(csv_target.relative_to(REPO_ROOT)),
        "sha256": _sha256(target),
        "experiment_id": log["experiment"]["id"],
        "recorded_at": recorded_at,
        "printer_model": log["print_conditions"]["printer_model"],
        "material": log["print_conditions"]["material"],
        "orientation": log["print_conditions"]["orientation"],
        "fit_by_clearance_mm": {
            f"{r['nominal_clearance_total_mm']:.2f}": r["fit_class"] for r in log["results"]
        },
    }

    existing = entry.get("print_log")
    runs = existing if isinstance(existing, list) else ([existing] if existing else [])
    runs = [run for run in runs if run.get("path") != record["path"]]
    runs.append(record)
    entry["print_log"] = runs

    if not keep_state and entry.get("evidence_state") == "GEOMETRY_VERIFIED":
        entry["evidence_state"] = "PRINT_VERIFIED"

    manifest["updated_at"] = dt.date.today().isoformat()
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"OK    filed {target.relative_to(REPO_ROOT)}")
    print(f"OK    filed {csv_target.relative_to(REPO_ROOT)}")
    print(f"OK    {spec.asset_id}@{spec.version} is now {entry['evidence_state']} ({len(runs)} run(s))")
    print("      Remaining for a complete asset pack: photos referenced by photo_refs "
          "must exist under assets/images/, and the joint page must state the result "
          "with its printer / material / orientation scope.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("log", nargs="?", type=Path, help="exported print-log JSON")
    parser.add_argument("--check", action="store_true", help="validate without writing anything")
    parser.add_argument("--force", action="store_true", help="overwrite an already-filed log of the same name")
    parser.add_argument("--keep-state", action="store_true", help="file the log but leave evidence_state alone")
    parser.add_argument("--emit-templates", action="store_true", help="regenerate the blank CSV templates")
    args = parser.parse_args()

    if args.emit_templates:
        for path in emit_templates(load_form_specs()):
            print(f"OK    wrote {path.relative_to(REPO_ROOT)}")
        return 0

    if args.log is None:
        parser.error("a print-log JSON path is required (or use --emit-templates)")
    if not args.log.is_file():
        parser.error(f"no such file: {args.log}")

    return ingest(args.log, check_only=args.check, force=args.force, keep_state=args.keep_state)


if __name__ == "__main__":
    raise SystemExit(main())
