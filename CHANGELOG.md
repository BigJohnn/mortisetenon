# Changelog

## Unreleased
- Added the first-wave reading edition (`book.html`): seven new joint chapters and two new work chapters join the existing four pages to cover all 10+3 entries. Each new chapter includes original explanatory prose, bounded source citations, parameter relations, candidate assembly, failure interpretation and a reader exercise.
- Froze teaching-interface v0.1: ten-entry size-profile mapping, author-approved work envelopes, total versus normal clearance, stop versus relief surfaces, coordinate frames and versioned derivative rules. This is an editorial interface, not a validated CAD snapshot.
- Documented unresolved geometry explicitly: the storage box's last-edge versus bottom-groove motion, the mini table's orthogonal apron occupancy and assembly closure, the three-way corner's final insertion, and the split wedge's deformation stage.
- Corrected the first-wave workspace's dovetail and keyed-tenon evidence labels to `DRAFT`, consistent with their existing chapters and asset contract; removed an incorrect claim that a keyed-tenon STL release was available.
- Added a deterministic static-page builder and validation for chapter coverage, parameter mappings, generated-page drift, local links and evidence boundaries. No CAD, released assets, manifest entries or physical-evidence states were added or promoted in this writing iteration.
- Resolved the remaining six author decisions with their documented defaults: the clamp-tenon lesson stays three-part; the split-tenon wedge uses a reversible hard stop with a traditional comparison; the box is open and 160 × 110 × 70 mm; the mini table is 220 × 140 × 150 mm across 2–3 plates with a combined v0.1 top.
- Advanced every newly unblocked first-wave joint and proposed work to `READY_FOR_CAD`; all U01–U09 decisions now retain explicit resolutions, with no open author decisions remaining.
- Resolved U02 / U03 / U09: froze the first sliding-blind-pin design as the side-entry wide-mouth/narrow-slot teaching variant, renamed catalog item 09 to `十字半搭接`, and recorded the author-supplied Baxian-table source CAD.
- Audited the Baxian-table Onshape source at immutable microversion `f9e8c517a1e9b12a6a5c4c4b`: 30 solid bodies and six named variables are present, while `Assembly 1` contains zero instances. The source-identity blocker is closed; interface, assembly, and traditional-name mappings remain provisional.
- Added OPEN / RESOLVED decision states to the 10+3 review workspace and validator. The page now shows all nine confirmed decisions without treating design approval as physical validation.
- Added `first-wave.html` and `content/first_wave_v0.1.json`, filling all first-wave 10+3 entries with evidence-bounded source claims, a proposed teaching model, part roles, four assembly or audit steps, parameter interfaces, CAD deliverables, and deferred experiment debt.
- Added a filterable 10+3 review workspace that separates source-supported statements from project design proposals and exposes all nine author decisions with priorities, defaults, impacts, and explicit blocking boundaries.
- Completed the first source pass for clamp tenon, shouldered tenon, zongjiao, tongue-and-groove with battens, sliding blind pin, cross-lap terminology, split-tenon wedge, and the two proposed integrated works; unresolved variants and terminology remain visibly provisional.
- Extended the catalog validator to require complete first-wave coverage, matching IDs, four-step assembly narratives, valid joint/work/source references, unique assistance IDs, and the current nine author decisions.
- Advanced Roadmap v0.8 from catalog selection into author review and CAD implementation while leaving every physical experiment and evidence gate unchanged.
- Added `design-catalog.html` and `content/design_catalog_v0.1.json`, freezing the first book architecture at 24 basic joints across eight teaching families, six integrated works, and four cross-cutting experiment chapters.
- Selected the first design wave of 10 joints + 3 works. All thirteen records define a teaching role and work mapping; the ten joint records also define assembly actions, parameter interfaces, and later experiment questions.
- Split editorial progress (`CATALOG_SLOT`, `DESIGN_BRIEF`, `IMPLEMENTED`) from asset evidence (`DRAFT` through `USER_REPRODUCED`) in `ASSET_CONTRACT.md`; design can now proceed while experiments are deferred without manufacturing proof by vocabulary.
- Reworked Roadmap v0.7 into parallel design and evidence paths. The design path now advances source audit → shared parameter interface → CAD → digital chapters, while physical measurements and experiments remain visible in a deferred evidence queue.
- Added `tools/validate_design_catalog.py` and `npm run check:catalog` to enforce the 24 / 6 / 10+3 counts, the eight-families-by-three structure, unique identities, valid cross-references, and existing linked paths.
- Added `works/baxian-table.html`, the first integrated-work chapter. It turns six supplied records into an evidence-led narrative spanning the complete-object question, four-view physical reading, Onshape-to-multi-plate manufacturing, a provisional assembly sequence, explicit evidence limits, and a Prototype 02 recording brief.
- Added six contract-named WebP assets under `assets/images/baxian-table/v0.1/`: four uncropped physical views, one CAD-workspace overview, and one slicer orientation overview. The supplied JPEGs remain untouched.
- Added the Baxian table to the home page and CAD Spec, and revised Phase 3 of the roadmap from “make a first work later” to “turn the already assembled Prototype 01 into a reproducible work tutorial.” Gate A remains unchanged; a complete object photo does not replace the missing clearance measurements.
- Initially recorded the Baxian table as `DRAFT · PHYSICAL PROTOTYPE 01` from a mutable `/w/` workspace and screenshots only; the later authenticated microversion audit above supersedes that source-identity limitation without changing the physical evidence state.
- Expanded Clearance Lab from a download-and-record utility into a complete experiment chapter: design versus measured clearance, separate X/Y calculations, six-step print and measurement protocol, five fit classes, anomaly diagnosis, and a controlled transfer comparison against the straight-tenon sweep.
- Documented a release-relevant limitation found while writing the protocol: Clearance Test Kit v0.1 has no physical rung labels. The chapter now requires marking the 0.10 end before removal from the bed and reserves embossed labels for a new asset version instead of silently changing v0.1.
- Added chapter navigation and a direct reading path from the experiment to the straight-tenon chapter, without changing either asset's evidence state or inventing missing print data.

## v0.6 — 2026-08-31
- Logged the first straight-tenon C sweep print: Bambu Lab H2C, 0.4 mm nozzle, PLA Basic, 0.2 mm layers, tenons upright and rail flat. All four clearances assemble; C = 0.20 mm presses in against damping the whole way, and 0.30 / 0.40 / 0.50 mm get progressively looser.
- Added `assets/images/straight-tenon/v0.1/printed-01.webp` (all four tenons seated in one rail) and converted the unreferenced `p2s.png` slicer screenshot to `orientation-01.webp`, which is a contract shot name.
- Added a `04 · First physical print` section to the straight-tenon page carrying the photo, the print conditions, the observation, and the list of what is still unmeasured; renumbered the sections below it.
- Left `straight-tenon@v0.1` at `GEOMETRY_VERIFIED`. A fit result with no measured dimension cannot separate clearance from elephant foot or layer lines, so no print log is filed and no recommended clearance appears anywhere on the site. `tools/ingest_print_log.py` would reject the run regardless: it requires a fit class per rung and only 0.20 mm has one.
- Extended the contract's allowed shot names with `printed`, and wrote down the rule the keyed-tenon print had already been following: a slicer screenshot is named for what it documents (`orientation-NN`, `slicer-support-NN`), and any `assembled` / `exploded` shot must say whether it is a photograph or a render.
- Roadmap v0.4: the blocking item moved off "print the two plates" and onto the two things that now stand between here and Gate A — measuring the four straight-tenon rungs, and printing the Clearance Kit. Gate A's evidence list is now marked per line instead of showing four green ticks, and the pipeline section carries the print photo next to the render it was derived from.
- Home page: hero, joint card, Lab 01 and the roadmap teaser all state the result and the same boundary.
- Stopped `.print-photo img` from re-framing photographs. It forced `aspect-ratio: 4/3` with `object-fit: cover`, so wherever that ratio did not take effect the HTML `height` attribute set the box instead and the photo was cover-cropped to a fraction of itself — the C sweep print showed one and a half of its four blocks, and the keyed-tenon slicer screenshot was cut from 16:9 down to 4:3. Photos now render at the frame they were shot at (`width:100%; height:auto`). A print photograph is evidence, and cropping evidence to fit a layout is the layout deciding what the reader gets to check.

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
- Froze the dovetail workspace as Onshape version `dovetail v0.2` (`cc81e1a378a8fb2804c35364`) after checking that all seven features regenerate, and repointed the joint page's assembly and exploded links from the workspace (`/w/`) to that version.
- Converted the first dovetail print photo to `assets/images/dovetail/v0.2/assembled-01.webp`, matching the contract's photography path, shot name, and format; the JPEG under `v0.1/` is gone and its EXIF block did not survive the conversion.
- Corrected the dovetail status chip from the invented `PRINTED` to the contract state `DRAFT`: one print with no measurements is not a print-verified asset.
- Recorded `dovetail@v0.2` in the asset contract as a traceable source with no asset pack, stating why a first print alone is not a release.

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
