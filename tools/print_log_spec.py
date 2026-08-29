#!/usr/bin/env python3
"""Read the print-log form definitions straight out of the Clearance Lab page.

The recording form in `labs/clearance.html` is the only place the clearance
rungs and per-asset result fields are declared. Parsing them back out here means
the validator cannot drift away from the form that produces the data: if a rung
or a column is added to the page, this module reports it on the next run.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LAB_PAGE = REPO_ROOT / "labs" / "clearance.html"

FIT_CLASSES = ("jammed", "press-fit", "snug", "sliding", "loose")


@dataclass
class FormSpec:
    """One asset's recording form, as declared in the lab page."""

    asset_id: str
    version: str
    sha256: str
    label: str
    orientation: str
    clearances: list[float]
    required_result_fields: list[str] = field(default_factory=list)
    optional_result_fields: list[str] = field(default_factory=list)
    meta_fields: list[str] = field(default_factory=list)

    @property
    def result_fields(self) -> list[str]:
        return [*self.required_result_fields, *self.optional_result_fields]


def _attr(tag: str, name: str) -> str | None:
    match = re.search(rf'{name}="([^"]*)"', tag)
    return match.group(1) if match else None


def _split_forms(html: str) -> list[tuple[str, str]]:
    """Return (opening tag, inner html) for every print-log form on the page."""
    forms = []
    for match in re.finditer(r"<form\b[^>]*data-print-log[^>]*>", html):
        open_tag = match.group(0)
        end = html.find("</form>", match.end())
        if end == -1:
            raise ValueError("unterminated <form data-print-log> in the lab page")
        forms.append((open_tag, html[match.end() : end]))
    return forms


def load_form_specs(page: Path = LAB_PAGE) -> dict[str, FormSpec]:
    html = page.read_text(encoding="utf-8")
    specs: dict[str, FormSpec] = {}

    for open_tag, inner in _split_forms(html):
        asset_id = _attr(open_tag, "data-asset-id")
        version = _attr(open_tag, "data-asset-version")
        sha256 = _attr(open_tag, "data-asset-sha256")
        label = _attr(open_tag, "data-asset-label") or asset_id
        if not (asset_id and version and sha256):
            raise ValueError(f"print-log form is missing asset attributes: {open_tag}")

        orientation_tag = re.search(r'<input[^>]*name="orientation"[^>]*>', inner)
        orientation = _attr(orientation_tag.group(0), "value") if orientation_tag else ""

        rows = re.findall(r'<tr\b[^>]*data-clearance="([^"]*)"[^>]*>(.*?)</tr>', inner, re.S)
        if not rows:
            raise ValueError(f"{asset_id}: form declares no clearance rows")

        clearances = [float(value) for value, _ in rows]

        # Every row carries the same columns; the first one defines the contract.
        required: list[str] = []
        optional: list[str] = []
        for control in re.findall(r"<(?:input|select|textarea)\b[^>]*data-field=[^>]*>", rows[0][1]):
            name = _attr(control, "data-field")
            (optional if "data-optional" in control else required).append(name)

        for value, body in rows[1:]:
            names = {_attr(c, "data-field") for c in
                     re.findall(r"<(?:input|select|textarea)\b[^>]*data-field=[^>]*>", body)}
            if names != set(required) | set(optional):
                raise ValueError(f"{asset_id}: row {value} has different columns from the first row")

        meta = [
            _attr(tag, "name")
            for tag in re.findall(r"<(?:input|select|textarea)\b[^>]*\bname=\"[^\"]+\"[^>]*>", inner)
        ]

        specs[asset_id] = FormSpec(
            asset_id=asset_id,
            version=version,
            sha256=sha256,
            label=label,
            orientation=orientation,
            clearances=clearances,
            required_result_fields=required,
            optional_result_fields=optional,
            meta_fields=[name for name in meta if name],
        )

    if not specs:
        raise ValueError(f"no print-log forms found in {page}")
    return specs


if __name__ == "__main__":
    for spec in load_form_specs().values():
        print(f"{spec.asset_id}@{spec.version}  {spec.label}")
        print(f"  sha256      {spec.sha256}")
        print(f"  orientation {spec.orientation}")
        print(f"  clearances  {spec.clearances}")
        print(f"  required    {spec.required_result_fields}")
        print(f"  optional    {spec.optional_result_fields}")
