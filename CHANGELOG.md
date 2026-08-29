# Changelog

## v0.5 — 2026-08-29
- Froze the straight-tenon geometry source as Onshape version `straight-tenon v0.1` and registered it in the manifest, pointing `document_url` at the version (`/v/`) rather than the workspace (`/w/`) so the release stays reproducible; the workspace URL is kept separately as `source.workspace_url`.
- Exported `assets/downloads/straight-tenon_v0.1.step` (AP242, five solids) and validated it against the expected per-part bounding boxes, completing the STEP / STL / GLB set.
- Recorded that Onshape writes STEP in SI metres regardless of the requested unit, so that derivative carries `"units": "m"` while the rest of the pack stays mm.
- Added STEP and Onshape-source links to the straight-tenon page.
- Raised the print log to schema v0.2: the Clearance Lab now carries one form per asset (test kit and straight tenon) behind a tab switch, the straight tenon additionally records withdrawal force and shoulder seating, and the measurement fields were renamed `peg_/socket_` → `male_/female_` so both assets share one column vocabulary.
- Reworked `assets/app.js` into a per-form `initPrintLog(form)`; the CSV header is now derived from the rows present rather than hard-coded, and export filenames follow the print-log path in the asset contract.
- Added `tools/print_log_spec.py`, which parses the recording forms straight out of `labs/clearance.html` so the validator cannot drift from the form that produces the data.
- Added `tools/ingest_print_log.py`: validates an exported log against the form spec, the release manifest, and the asset contract, files it under `content/print-logs/`, promotes the asset to `PRINT_VERIFIED`, and regenerates the blank CSV templates.
- Replaced the hand-written `clearance_test_log_template.csv` with generated per-asset templates; the contract now states that templates are generated, never hand-edited.
- Added `tools/create_dovetail_onshape.py` and `tools/verify_dovetail_assembly.py` for the slide-in dovetail v0.2 (C = 0.20 mm, 0.20 mm roof clearance, 0.4 mm internal socket-root relief) with assembled and exploded assemblies. The model exists in Onshape only; no dovetail asset pack is published yet.
- Added `.gitignore` so the Onshape API keys in `.env` and Python bytecode stay out of the repository.

## v0.4 — 2026-08-28
- Built the straight-tenon C sweep v0.1 (C = 0.20 / 0.30 / 0.40 / 0.50 mm) from the Onshape source: print-layout STL, animated GLB, and exploded WebP render, all from one part-pose definition.
- Fixed `tools/build_straight_tenon_assets.py` for Blender 4.4+ slotted actions; the four tenons now share one action so the GLB carries a single clip named `Explode`.
- Rendered the poster through the Standard view transform so it matches the site palette, and switched its output to WebP.
- Added a real `<model-viewer>` to the straight-tenon page: orbit, zoom, and a scrub slider driving the clip's `currentTime`, plus assemble / separate / loop controls.
- Added a "爆炸图怎么变成动画" section documenting the six-step method and this clip's parameters.
- Stored the build-input part STLs in `cad/straight-tenon_v0.1_parts/` so the release is reproducible outside `/tmp`.
- Added `straight-tenon@v0.1` to the release manifest with build inputs, derivatives, animation metadata, and Blender mesh validation (5 shells, 0 boundary / non-manifold edges).
- Roadmap v0.3: printing marked in progress, new Asset pipeline section, rewritten backlog.
- Recorded the open traceability gap: the Onshape document URL is not yet registered and STEP is not exported.

## v0.3.1 — 2026-08-28
- Rebuilt the roadmap around an evidence-first critical path and explicit gates.
- Added `ASSET_CONTRACT.md` with immutable versioning and evidence states.
- Added a release manifest with SHA-256 and Blender mesh validation for Clearance Kit v0.1.
- Added browser-local print-log drafts plus validated JSON / CSV export to Clearance Lab.
- Added a blank CSV print-log template for offline use.
- Verified desktop/mobile layout, local draft restore, both exports, and zero severe browser console errors.


## v0.3 — 2026-08-27
- Decision 001 closed: MVP Joint 03 = 楔钉榫.
- Added `joints/keyed-tenon.html` with research-backed mechanism and traditional context.
- Added `cad/index.html` with first-print parametric specifications for all three MVP joints.
- Added `cad/clearance_test_kit_v0.1.scad`.
- Exported the first real printable asset: `assets/downloads/clearance_test_kit_v0.1.stl`.
- Updated homepage, Clearance Lab, research source list, and roadmap status.
- All proposed CAD dimensions are explicitly marked as teaching/engineering starting values pending real print validation.
