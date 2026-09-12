#!/usr/bin/env python3
"""Check manuscript coverage, local links, parameter scopes and evidence boundaries."""
from __future__ import annotations

import json
import hashlib
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from build_manuscript import generate

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, text: str):
        super().__init__()
        self.ids: list[str] = []
        self.links: list[str] = []
        self.h1_count = 0
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if value := attrs.get("id"):
            self.ids.append(value)
        for attr in ("href", "src"):
            if value := attrs.get(attr):
                self.links.append(value)
        self.h1_count += tag == "h1"


def main() -> int:
    errors: list[str] = []

    def require(ok: bool, message: str):
        if not ok:
            errors.append(message)

    wave = json.loads((ROOT / "content/first_wave_v0.1.json").read_text())
    spec = json.loads((ROOT / "content/teaching_spec_v0.1.json").read_text())
    manuscript = json.loads((ROOT / "content/manuscript_v0.1.json").read_text())
    catalog = json.loads((ROOT / "content/design_catalog_v0.1.json").read_text())
    first = wave["joints"] + wave["works"]
    by_id = {e["id"]: e for e in first}
    existing = {"straight-tenon", "dovetail", "keyed-tenon", "baxian-table"}
    authored = {c["id"] for c in manuscript["chapters"]}
    require(authored == set(by_id) - existing, "Authored chapters must cover exactly the seven new joints and two works")
    coverage = Counter(slug for profile in spec["profiles"] for slug in profile["applies_to"])
    require(coverage == Counter(e["id"] for e in wave["joints"]), "Teaching profiles must cover each first-wave joint exactly once")
    require({w["id"] for w in spec["work_envelopes"]} == {w["id"] for w in wave["works"]}, "Missing work envelope")
    require(len({f["id"] for f in spec["fields"]}) == len(spec["fields"]), "Duplicate parameter field")
    require(all(f["default"] is None for f in spec["fields"] if f["id"].startswith("fit_")), "Unverified fit fields must have null defaults")
    require(spec["status"] == "EDITORIAL_INTERFACE_FROZEN", "The spec must not claim geometry verification")
    for e in first:
        path = e.get("chapter_path") or e.get("case_path")
        require(bool(path) and (ROOT / path).is_file(), f"Missing first-wave reading page: {e['id']}")
        if e["id"] in authored:
            if e.get("local_cad_review"):
                require(e["evidence_state"].startswith("DRAFT") and "FreeCAD" in e["evidence_state"], f"Local CAD must retain its evidence boundary: {e['id']}")
                require((ROOT/e["local_cad_review"]).is_file(), f"Missing CAD review: {e['id']}")
                review_path=ROOT/e['local_cad_review']
                if review_path.is_file():
                    for href in Page(review_path.read_text()).links:
                        url=urlsplit(href)
                        if url.scheme or url.netloc or not url.path:continue
                        target=(review_path.parent/unquote(url.path)).resolve()
                        require(target.is_relative_to(ROOT) and target.is_file(), f"Broken CAD review link: {href}")
                        require('/cad/private/' not in str(target) and '/table-node-pair_freecad_' not in str(target), f"Private CAD linked from public review: {href}")
                        require(target.suffix.lower() not in {'.fcstd','.step','.stp','.stl','.glb','.gltf','.3mf'}, f"Geometry linked from static-only review: {href}")
                summary_path=ROOT/e.get("cad_status_path", "content/cad_status_v0.1.json")
                require(summary_path.is_file(), f"Missing non-geometric CAD status summary: {e['id']}")
                if summary_path.is_file():
                    summary=json.loads(summary_path.read_text())
                    require(summary.get("state")=="DRAFT" and summary.get("print_verified") is False, f"Invalid CAD summary evidence boundary: {e['id']}")
                    require(summary.get("id")==e['id'] or e['id'] in summary.get("nodes",{}), f"CAD summary belongs to another chapter: {e['id']}")
                    for name,digest in summary.get('static_images',{}).items():
                        target=ROOT/'assets/images'/e['id']/'v0.1'/name
                        require(target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest()==digest, f"Static CAD image differs from checked summary: {name}")
                for extra in e.get('cad_supplements',[]):
                    review=ROOT/extra['review'];status=ROOT/extra['summary']
                    require(review.is_file() and status.is_file(), f"Missing supplemental CAD review: {e['id']}")
                    if not review.is_file() or not status.is_file():continue
                    parsed=Page(review.read_text());data=json.loads(status.read_text())
                    require(parsed.h1_count==1 and len(parsed.ids)==len(set(parsed.ids)), f"Invalid supplemental review structure: {review.name}")
                    require(data.get('id')==e['id'] and data.get('state')=='DRAFT' and data.get('print_verified') is False, f"Invalid supplemental evidence boundary: {e['id']}")
                    for href in parsed.links:
                        url=urlsplit(href)
                        if url.scheme or url.netloc or not url.path:continue
                        target=(review.parent/unquote(url.path)).resolve()
                        require(target.is_relative_to(ROOT) and target.is_file(), f"Broken supplemental link: {href}")
                        require('/cad/private/' not in str(target) and '/table-node-pair_freecad_' not in str(target) and target.suffix.lower() not in {'.fcstd','.step','.stp','.stl','.glb','.gltf','.3mf'}, f"Protected geometry linked from static supplement: {href}")
                    for name,digest in data.get('static_images',{}).items():
                        target=ROOT/'assets/images'/e['id']/'v0.1'/name
                        require(target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest()==digest, f"Supplemental image identity mismatch: {name}")
                    for grid in data.get('grids',{}).values():
                        require(grid['clear']+grid['colliding']==grid['case_count'], 'Invalid finite-grid counts')
                        require(grid.get('clear_but_lap_gap',0)<=grid['clear'], 'Invalid gap subset')
            else:
                require("尚无本项目 CAD" in e["evidence_state"], f"New chapter has unexpected evidence: {e['id']}")
        if e["id"] in {"dovetail", "keyed-tenon"}:
            require(e["evidence_state"].startswith("DRAFT"), f"Legacy evidence contradicts asset contract: {e['id']}")
    catalog_entries = {e["id"]: e for e in catalog["joints"] + catalog["works"]}
    for slug in by_id:
        require(catalog_entries[slug]["design_stage"] == "IMPLEMENTED", f"Reading page missing from catalog: {slug}")
    for c in manuscript["chapters"]:
        require(set(c["next_ids"]) <= set(by_id), f"Unknown related chapter in {c['id']}")
        require(set(c["source_ids"]) <= set(wave["sources"]), f"Unknown source in {c['id']}")
        require(len(c["sections"]) >= 3, f"Incomplete prose in {c['id']}")
        require(all(len(row) == 3 for row in c["relations"] + c["failure_reading"]), f"Malformed table in {c['id']}")

    pages = generate()
    for relative, expected in pages.items():
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"Missing generated page: {relative}")
            continue
        actual = path.read_text(encoding="utf-8")
        require(actual == expected, f"Generated page is stale: {relative}")
        parsed = Page(actual)
        require(parsed.h1_count == 1, f"Expected one h1: {relative}")
        require(len(parsed.ids) == len(set(parsed.ids)), f"Duplicate anchors: {relative}")
        for href in parsed.links:
            url = urlsplit(href)
            if url.scheme or url.netloc:
                continue
            target = (path.parent / unquote(url.path)).resolve() if url.path else path
            require(target.is_relative_to(ROOT), f"Link escapes repository: {relative}: {href}")
            require(target.is_file(), f"Broken local link: {relative}: {href}")
            if target.is_file() and url.fragment and target.suffix == ".html":
                require(unquote(url.fragment) in Page(target.read_text()).ids, f"Missing fragment: {relative}: {href}")
        require("placeholder.stl" not in actual, f"Placeholder exposed: {relative}")
    for error in errors:
        print("ERROR: " + error)
    if not errors:
        print("Manuscript valid: 13 reading entries / 9 new chapters / 10 parameter mappings / 11 static pages / local links and evidence boundaries checked.")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
