# Printable Joinery Atlas Asset Contract v0.1

Updated: 2026-08-28

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

Allowed shot names are `assembled`, `exploded`, `orientation`,
`scale-reference`, `failure`, and `detail`, followed by a two-digit index.

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
- Current state: `GEOMETRY_VERIFIED`
- Known gap: the Onshape document URL is not registered and STEP is not
  exported, so `source.document_url` in the manifest is `null`. Until it is
  filled in, the hashed part snapshot is the only verifiable record of this
  geometry.

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
