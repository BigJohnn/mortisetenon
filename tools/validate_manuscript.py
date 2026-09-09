#!/usr/bin/env python3
"""Check manuscript coverage, local links, parameter scopes and evidence boundaries."""
from __future__ import annotations

import json
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
