# Printable Joinery Atlas Asset Contract v0.1

Updated: 2026-08-29

## Purpose

Every public model must answer four questions without relying on memory:

1. Which parameterized source produced it?
2. Which version of the geometry does it represent?
3. Has the digital geometry been checked?
4. Has that exact version been physically printed and reproduced?

The parameterized CAD source is the geometry source of truth. STL, STEP, GLB,
renders, diagrams, and print logs are versioned derivatives, not independent
masters.

## Evidence states

Assets move forward only; changing geometry creates a new version.

| State | Meaning | Required evidence |
| --- | --- | --- |
| `DRAFT` | Geometry is still changing. | Parameter table and editable source. |
| `GEOMETRY_VERIFIED` | The release file is structurally usable. | Hash, units, bounding box, shell count, manifold check. |
| `PRINT_VERIFIED` | This exact version has been printed. | Complete print log, measurements, fit result, failure notes, photo references. |
| `USER_REPRODUCED` | Someone outside the authoring workflow reproduced it. | External print log tied to the same asset version. |

Words such as "best", "recommended", or "works" must not appear as unqualified
claims before `PRINT_VERIFIED`. A print result is always scoped to printer,
material, orientation, slicer settings, and geometry version.

## Identity and versioning

- **Slug:** lowercase ASCII kebab-case, for example `straight-tenon`.
- **Version:** `vMAJOR.MINOR`, for example `v0.1`.
- Increment **minor** for compatible geometry experiments or documentation fixes.
- Increment **major** when interfaces, dimensions, assembly direction, or learning
  intent changes.
- Released files are immutable. Never replace a file while retaining its version.
- One asset pack version uses one parameter snapshot across every derivative.

## Paths and filenames

Existing files remain valid. New files follow these patterns:

| Asset | Pattern | Example |
| --- | --- | --- |
| Parameterized source | `cad/{slug}_{version}.{ext}` | `cad/straight-tenon_v0.1.scad` |
| Printable mesh | `assets/downloads/{slug}_{variant}_{version}.stl` | `assets/downloads/straight-tenon_c020_v0.1.stl` |
| Exchange CAD | `assets/downloads/{slug}_{version}.step` | `assets/downloads/straight-tenon_v0.1.step` |
| Web model | `assets/models/{slug}_{state}_{version}.glb` | `assets/models/straight-tenon_assembled_v0.1.glb` |
| Photography | `assets/images/{slug}/{version}/{shot}.webp` | `assets/images/straight-tenon/v0.1/assembled-01.webp` |
| Print log | `content/print-logs/{date}_{slug}_{version}_{run}.json` | `content/print-logs/2026-08-28_clearance-test-kit_v0.1_run-01.json` |
| Print-log template | `assets/downloads/{slug}_print-log-template_{version}.csv` | `assets/downloads/straight-tenon_print-log-template_v0.1.csv` |

Allowed shot names are `assembled`, `exploded`, `orientation`,
`scale-reference`, `failure`, and `detail`, followed by a two-digit index.

Print-log templates are generated, never hand-edited: `python3
tools/ingest_print_log.py --emit-templates` reads the recording forms in
`labs/clearance.html` and writes one blank CSV per asset with the same columns
the browser export produces. Editing a template by hand would let the offline
sheet drift away from the form and from `tools/ingest_print_log.py`, which
validates against the same parsed definition.

`placeholder`, `final`, `latest`, and `new` are forbidden in published
asset filenames. Placeholder files may exist during drafting but must never be
linked from a public page or included in the release manifest.

## Required asset-pack contents

Each joint promoted to `PRINT_VERIFIED` contains:

- Editable parameterized CAD source and parameter snapshot.
- STEP, STL, and GLB derived from the same source version.
- SHA-256, byte size, units, bounding box, and geometry validation result.
- Assembly direction and print orientation.
- One complete print log, including failures.
- Photography: assembled, exploded, print orientation, scale reference, and any
  meaningful failure.
- Content entry with source citations and a clearly scoped recommendation.

## Release manifest

`assets/downloads/manifest.json` lists public downloadable releases. A release
entry must include:

- Stable asset ID, version, evidence state, and geometry variant.
- Source and derivative paths plus SHA-256 values.
- Units, dimensions, connected shell count, and mesh validation.
- The print log path once the state becomes `PRINT_VERIFIED`.

## Current baseline

`clearance-test-kit@v0.1` is the first release:

- Source: `cad/clearance_test_kit_v0.1.scad`
- STL: `assets/downloads/clearance_test_kit_v0.1.stl`
- Current state: `GEOMETRY_VERIFIED`
- Next state requires one complete four-clearance print log and photo references.

`straight-tenon@v0.1` is the second release, and the first asset pack whose web
model, print file, and render all derive from one part-pose definition:

- Build inputs: `cad/straight-tenon_v0.1_parts/*.stl` (Onshape export snapshot)
- Build script: `tools/build_straight_tenon_assets.py` (Blender 5.2.1 LTS)
- STL: `assets/downloads/straight-tenon_c-sweep-print-layout_v0.1.stl`
- GLB: `assets/models/straight-tenon_assembled_v0.1.glb`
- Render: `assets/images/straight-tenon/v0.1/exploded-01.webp`
- STEP: `assets/downloads/straight-tenon_v0.1.step` (AP242, five solids)
- Current state: `GEOMETRY_VERIFIED`
- Source of record: Onshape version `straight-tenon v0.1`
  (`652edb49197bc7af84e099bc`, microversion `85b4a056964c33f558516f13`),
  frozen 2026-08-29. The manifest's `document_url` points at the version
  (`/v/`), never the workspace (`/w/`): a workspace URL keeps moving as the
  model is edited, which would make the release non-reproducible. The workspace
  URL is recorded separately as `source.workspace_url` for continued editing.
- Unit note: Onshape writes STEP in SI metres regardless of the requested
  export unit, so this one derivative carries `"units": "m"` while every other
  file in the pack is mm. STEP embeds its own unit metadata, so importing CAD
  reads it correctly; the manifest states it explicitly so nobody compares the
  raw numbers against the mm derivatives by mistake.

`dovetail@v0.2` is not an asset pack yet. It exists as an Onshape model and one
physical print, so it is recorded here only to keep the source traceable:

- Source of record: Onshape version `dovetail v0.2`
  (`cc81e1a378a8fb2804c35364`, microversion `09afd4d32a0f94591eaa927b`),
  frozen 2026-08-29 after all seven features regenerated clean. The joint page
  links that version (`/v/`), matching the rule above.
- Geometry: slide-in dovetail, C = 0.20 mm per flank pair, 0.20 mm roof
  clearance, 0.4 mm internal socket-root relief.
- Photography: `assets/images/dovetail/v0.2/assembled-01.webp`.
- Current state: `DRAFT`. No STEP / STL / GLB is exported and there is no
  manifest entry, because a first print alone is not a release: the print
  conditions, insertion force, and measured clearances are all unrecorded. The
  page states that boundary rather than implying a recommended clearance.

`keyed-tenon@v0.7` is likewise not an asset pack. It is an Onshape model that has
been checked digitally and printed once. The two members below are v0.7 exactly;
the key is not -- it was redrawn by hand in the workspace after v0.7 was frozen,
and no version has been cut since, so the key numbers here are read back from the
live workspace (2026-08-30) rather than from a frozen version:

- Source of record: Onshape version `keyed-tenon v0.7`
  (`3aa8f29bde2c332836964647`, microversion `4e657dd2fda60180ce765e6e`),
  frozen 2026-08-29 after all eighteen features regenerated clean. v0.1 - v0.6
  are kept as history; v0.5 holds an alternative key, lofted and then given
  clearance by a 0.2 mm offset boolean, preserved because it was superseded
  rather than abandoned.
- Geometry as built: 24 x 18 mm stock, two 70 mm members, a 30 mm half-lap split
  9 + 9 mm, and an 8 x 5 x 3 mm stub tongue at each lap end running into a blind
  mortise in the mating member. Assembled length 100 mm.
- Clearance is applied to fits and only to fits: tongue/mortise C = 0.20 mm and
  key-to-hole C = 0.20 mm across the key's parallel faces. The lap face and both
  24 x 9 mm shoulders stay coincident, because they are the bearing surfaces.
  Clearing them instead would buy a permanent 0.2 mm of play in Z and X that
  nothing takes up: the key locks X and Y by shear, not Z.
- Corner relief is not sized from anything. The lap corners carry a 45 degree
  notch of leg 0.20 mm and the mortise mouths a 0.50 mm lead-in, and those two
  numbers are assumptions the first print has to settle. An earlier version of
  this record derived the 0.20 mm from "a fillet of radius r intrudes 0.414 r
  along the diagonal, so c >= 0.586 r"; that argument measured the fillet where
  it intrudes least. Keeping the same nozzle-radius model but asking where the
  relief's own concave vertex ends up gives c >= (1 + sqrt 2) r, about 0.48 mm
  for a 0.4 mm nozzle -- which would make 0.20 mm a notch narrower than the
  nozzle that has to cut it. v0.7 ships as built; the print decides.
- The lap relief stops short of both side faces. That corner lies on the outside
  of the assembled joint, so a relief taken across the full width breaks out and
  leaves a notch in the seam -- four of them on the finished piece. It is
  therefore cut as its own feature over the middle 23 mm of the 24 mm width,
  leaving 0.5 mm of sharp corner at each edge so the seam reads as one
  continuous line. Those slivers keep about 0.08 mm of interference on the most
  compliant part of the section -- 0.08 mm being the fillet's diagonal reach,
  not its worst case, which is r itself against a sharp mating corner. That is
  the price of an unbroken seam. The
  mortise mouth needs no such treatment: it sits inside the shoulder face and is
  hidden once assembled, so its lead-in stays in the pocket profile.
- Print orientation was designed as side-face-down: build direction Y, layers in
  X-Z planes, every concave corner that matters lying in that plane -- which is
  why both reliefs can be shaped from Front sketches -- and the tongue supported
  rather than hanging. The first print did not use it. It went down flat on the
  70 x 24 footprint, 18 mm tall, lap face up, which is steadier and gives better
  flatness but makes each tongue an overhang: the tongue is not on the lap face,
  it floats in the middle of the remaining 9 mm section (member A: z = 3.05 to
  5.95), so its 7.90 x 5.00 mm underside hangs 3.05 mm above the plate.
- Support therefore has to be painted, not left to the slicer. The first print
  used Bambu Studio tree support in manual mode, which generates support only
  under painted regions, with enforcers on exactly those two tongue undersides
  and "overhangs only" checked. Nothing else on the part needs support: the key
  hole opens upward with walls 2.5 degrees off vertical, and the mortise is an
  8.10 mm bridge. Leaving it automatic would pack support into the mortise, which
  is both a fit surface and unreachable. The cost of this orientation is that the
  support scar lands on a tongue face that has only 0.10 mm of clearance.
- Key and hole: the hole tapers in X from 6.40 mm at the far face to 8.00 mm at
  the entry face over 18 mm, and is 7.20 mm wide in Y. The key tapers in X only,
  so its parallel Y faces let it print lying flat with its layers along the shear
  path. Both tapers are essentially equal -- and that, not the word "wedge", is
  what governs the key. Two matched tapers have no included angle for the key to
  drive itself into; they grip over the full face the way a Morse taper does, and
  the depth at which the grip starts is set entirely by size.
- A wedge therefore cannot be flush, tight and clearanced at once; clearance
  always buys depth. v0.7's key spent none: 6.80 -> 8.00 mm over 13.5 mm, 7.00 mm
  thick, the hole's own profile over its top 13.5 mm at zero offset, seating with
  its head flush and its tip 4.50 mm above the far face. It printed too tight to
  press in by hand. The workspace key is the same idea with clearance: 6.05 ->
  7.65 mm over 17.83125 mm, 6.80 mm thick -- 0.35 mm under the hole in X at every
  level and 0.40 mm under it in Y. It presses in easily and it no longer lands
  flush anywhere: the head catches where the hole has narrowed to 7.65 mm, which
  is 0.35 / 0.0889 = 3.94 mm below the entry face, leaving the tip 3.77 mm out
  the far side. Nor can it be stopped by the far opening any more -- its 6.05 mm
  tip passes through the 6.40 mm hole; friction on the taper is all that holds
  it. Seat depth still moves 11.25 mm per mm of size error.
- The two members are congruent under a 180 degree rotation about Y everywhere
  except the key hole. The hole tapers along Z and that rotation reverses Z, so
  no non-trivial taper can map onto itself; the members differ by their half of
  the hole and ship as two meshes rather than one printed twice. Everything else
  stays congruent, which is what keeps both members' shoulder positions carrying
  identical error so both shoulders seat together.
- Digital assembly check: `tools/verify_keyed_tenon.py` reproduces every bounding
  box and volume from the closed-form model (A 21135.8310 mm3, B 21083.9910 mm3,
  key 830.5796 mm3), and matches the two members vertex for vertex under that
  rotation once the hole footprint is masked out. It reads the feature list to
  see which relief the model carries and derives its expected volumes from the
  build script's own constants, so the two files cannot drift apart. A temporary
  boolean union of the two members measured an interpenetration of 0 mm3, so
  they meet only on the lap plane and the two shoulders.
- Web model: `assets/models/keyed-tenon_assembled_v0.7.gltf`, built by
  `tools/export_keyed_tenon_gltf.py` from the frozen version. Onshape's assembly
  glTF export writes every part in Part Studio coordinates and drops the assembly
  transforms, so the script reads those transforms back from both assembly
  definitions and applies them, then derives the `Explode` clip from the measured
  difference between the mated and separated states. No offset is typed into the
  exporter, so the clip cannot drift away from the assembly it describes. The
  export is also Z-up, which model-viewer is not, so the parts hang under one
  root node carrying a quarter turn about X.
- Renders: `assets/images/keyed-tenon/v0.7/{assembled,exploded}-01.webp`, both
  frames of the two frozen assembly states. They are renders, not photographs,
  and the page says so where they appear. They also show the flush v0.7 key, so
  they predate the key revision; the page says that too.
- Photography: `assets/images/keyed-tenon/v0.7/printed-01.webp`, the first print
  assembled, key not inserted, and `slicer-support-01.webp`, the slicer screen
  that records the orientation and the two painted enforcers.
- First print, 2026-08-30, Bambu Lab P2S, 0.4 mm nozzle, PLA Matte, flat
  orientation, manual tree support on the two tongue undersides. The members go
  together to the shoulders but need real force; the key presses in relatively
  easily. Which key was on the plate is not recorded.
- Current state: `DRAFT`. A print that assembles is not a measurement: both
  0.20 mm clearances, both relief sizes, the seated depth, and whether the hole
  walls survive being driven are all still assumptions, and the one new fact --
  that the members are tight -- has no dimension attached to it. The leading
  explanation is that the tongue's 0.10 mm of clearance is eaten from both sides
  at once, by support scar under the tongue and by sag in the mortise's 8.10 mm
  bridge above it; measuring the two heights settles it. No STEP or STL is
  exported and there is no manifest entry: publishing a printable file now would
  put this project's name on a clearance that has just been shown to be tight.

## Animated assemblies

A joint whose GLB carries an assembly animation follows three rules, so the clip
stays a description of the geometry rather than a separate illustration:

- One clip per asset pack, named `Explode`, running from the assembled pose to
  the separated pose. Frame 0 is the assembly drawing; the last frame is the
  exploded drawing.
- Parts separate along the reverse of their real assembly direction. Lateral fan
  offsets are allowed only to prevent occlusion and carry no meaning.
- At least one part stays still as a reference, and published renders are frames
  of that same clip — never a separately posed scene.

The two legacy `dovetail-placeholder.*` files are not releases and are excluded
from the manifest.
