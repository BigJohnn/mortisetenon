#!/usr/bin/env python3
"""Read-only check of the keyed-tenon Part Studio against its analytic geometry.

Nothing here writes to Onshape.  The model is built from axis-aligned boxes plus
one chamfer and one tapered key, so every quantity it reports has a closed form;
comparing the two catches a wrong extrude direction, a boolean that hit the
wrong body, or a mistyped dimension.

The congruence test is the load-bearing one: member A mapped through a 180 deg
rotation about Y must reproduce member B everywhere except the key hole.  That
guarantees the two 30 mm shoulder spacings carry identical error, so both
shoulders seat together instead of one of them fighting the other.

The hole is the one deliberate exception.  It tapers along Z, and a 180 degree
rotation about Y reverses Z, so a tapered hole cannot map onto itself; the two
members therefore differ by their half of the hole and are exported as two
separate meshes.  The test masks out the hole footprint and checks that nothing
else differs, which is what keeps that exception honest instead of open-ended.

Two notes on method:

* Congruence is checked on tessellated edge vertices, not on centroids.  No
  material is assigned to these parts, so Onshape reports zero mass and a
  meaningless (0, 0, 0) centre of mass.  Every face here is planar, so an exact
  match of the two vertex sets is a proof of congruence, not a sample of it.
* Bounding boxes also come from those vertices rather than from the
  /boundingboxes endpoint, which has been observed returning all zeros for a
  body carrying fillets while the tessellation reported the correct extents.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.request

# The expected numbers are derived from the build script's own constants rather
# than copied, so a dimension can never be changed in one file and checked
# against a stale literal in the other.
import create_keyed_tenon_onshape as model


DID = "73de9c93248e073d85379a97"
WID = "1bd7eba357dd91d2503bfa3c"
EID = "bd84c453f68419d4085d9688"

TOL = 1e-3          # mm; tessellated edges come back as float32
VERTEX_TOL = 1e-3   # mm


def get(path: str) -> dict:
    key = os.environ["ONSHAPE_ACCESS_KEY"]
    secret = os.environ["ONSHAPE_SECRET_KEY"]
    base_url = os.environ.get("ONSHAPE_BASE_URL", "https://cad.onshape.com").rstrip("/")
    request = urllib.request.Request(base_url + path, headers={
        "Accept": "application/json;charset=UTF-8; qs=0.09",
        "Authorization": "Basic " + base64.b64encode(f"{key}:{secret}".encode()).decode(),
    })
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Onshape returned HTTP {error.code}: {detail}") from error


def relief_in_use() -> tuple[float, float]:
    """Read the built feature names to see which relief the model actually has.

    The build script can produce the model with or without relief, so the
    expected volumes depend on which one is in the document.  Asking the document
    beats passing a flag that can be forgotten.
    """
    names = [f.get("name", "") for f in
             get(f"/api/v10/partstudios/d/{DID}/w/{WID}/e/{EID}/features")["features"]]
    corner = model.CORNER_RELIEF if any("Lap corner relief" in n for n in names) else 0.0
    mouth = model.MOUTH_CHAMFER if any("mouth chamfer" in n for n in names) else 0.0
    return corner, mouth


def hole_width(z: float) -> float:
    return model.HOLE_X_BOTTOM + model.HOLE_TAPER * z


def expected(corner_relief: float, mouth_chamfer: float) -> dict[str, dict]:
    m = model
    mortise_w, mortise_h = 2 * m.MORTISE_HW, m.MORTISE_HI - m.MORTISE_LO
    tongue_w, tongue_h = 2 * m.TONGUE_HW, m.TONGUE_HI - m.TONGUE_LO

    profile = m.FREE_LENGTH * m.HEIGHT + m.OVERLAP * m.HALF_LAP   # the L-shape
    # The lap corner relief is cut separately and stops short of both side faces,
    # so it removes a triangular prism over part of the width, not all of it.
    corner = (corner_relief ** 2 / 2) * (m.WIDTH - 2 * m.CORNER_EDGE_KEEP)
    mortise = (m.MORTISE_BOTTOM - m.HALF) * mortise_h * mortise_w
    # The mouth chamfer takes two triangular prisms off the pocket's Z walls.
    mouth = mouth_chamfer ** 2 * mortise_w
    tongue = m.TONGUE_L * tongue_h * tongue_w
    body = profile * m.WIDTH - corner - mortise - mouth + tongue

    # The hole is a trapezoid in X-Z of constant Y width, so each member loses
    # the trapezoid over its own half of the depth -- different amounts, which is
    # exactly why the two members are no longer interchangeable.
    def hole_slice(z_low: float, z_high: float) -> float:
        return (hole_width(z_low) + hole_width(z_high)) / 2 * (z_high - z_low) * m.HOLE_Y

    key = ((m.KEY_X_TIP + m.KEY_X_HEAD) / 2) * m.KEY_LENGTH * m.KEY_Y
    half_w, half_head = m.WIDTH / 2, m.KEY_X_HEAD / 2
    return {
        "A": {"volume": body - hole_slice(0.0, m.HALF_LAP),
              "box": ((-m.MAIN_END, -half_w, 0.0), (m.TONGUE_TIP, half_w, m.HEIGHT))},
        "B": {"volume": body - hole_slice(m.HALF_LAP, m.HEIGHT),
              "box": ((-m.TONGUE_TIP, -half_w, 0.0), (m.MAIN_END, half_w, m.HEIGHT))},
        "key": {"volume": key,
                "box": ((m.KEY_PARK_X - half_head, -m.KEY_Y / 2, m.KEY_SEAT_Z),
                        (m.KEY_PARK_X + half_head, m.KEY_Y / 2, m.HEIGHT))},
    }


def vertices(part_id: str) -> set[tuple[float, float, float]]:
    """Every tessellated edge endpoint of one part, in millimetres."""
    response = get(f"/api/v10/parts/d/{DID}/w/{WID}/e/{EID}/partid/{part_id}/tessellatededges")
    points = set()
    for body in response["bodies"]:
        for edge in body["edges"]:
            for vertex in edge["vertices"]:
                points.add(tuple(round(vertex[axis] * 1000, 3) for axis in "xyz"))
    return points


def measure() -> list[dict]:
    out = []
    for part in get(f"/api/v10/parts/d/{DID}/w/{WID}/e/{EID}"):
        pid = part["partId"]
        points = vertices(pid)
        mass = get(f"/api/v10/parts/d/{DID}/w/{WID}/e/{EID}/partid/{pid}/massproperties")
        columns = list(zip(*points))
        out.append({
            "partId": pid,
            "name": part["name"],
            "points": points,
            "low": tuple(min(c) for c in columns),
            "high": tuple(max(c) for c in columns),
            "volume": mass["bodies"][pid]["volume"][0] * 1e9,
        })
    return out


def close(a: float, b: float) -> bool:
    return abs(a - b) < TOL


def main() -> int:
    parts = measure()
    if len(parts) != 3:
        print(f"FAIL: expected 3 parts (member A, member B, key), found {len(parts)}",
              file=sys.stderr)
        return 1

    # Member A starts furthest -X, B next, and the key is parked past B's far end.
    parts.sort(key=lambda item: item["low"][0])
    labels = ["A", "B", "key"]
    corner_relief, mouth_chamfer = relief_in_use()
    print(f"model as built: lap-corner relief {corner_relief:.2f} mm, "
          f"mortise-mouth chamfer {mouth_chamfer:.2f} mm\n")
    want = expected(corner_relief, mouth_chamfer)
    failures = []

    for label, part in zip(labels, parts):
        spec = want[label]
        size = tuple(h - l for l, h in zip(part["low"], part["high"]))
        print(f"{label:<4} {part['name']:<22} "
              f"min={tuple(round(v, 4) for v in part['low'])} "
              f"size={tuple(round(v, 4) for v in size)} "
              f"vol={part['volume']:.4f} mm³  ({len(part['points'])} vertices)")
        for axis, got, exp in zip("xyz", part["low"], spec["box"][0]):
            if not close(got, exp):
                failures.append(f"{label}: low{axis.upper()} {got:.4f} != {exp:.4f}")
        for axis, got, exp in zip("xyz", part["high"], spec["box"][1]):
            if not close(got, exp):
                failures.append(f"{label}: high{axis.upper()} {got:.4f} != {exp:.4f}")
        if not close(part["volume"], spec["volume"]):
            failures.append(f"{label}: volume {part['volume']:.4f} != {spec['volume']:.4f} mm³")

    print(f"\nexpected A {want['A']['volume']:.4f} mm³, B {want['B']['volume']:.4f} mm³, "
          f"key {want['key']['volume']:.4f} mm³")

    member_a, member_b = parts[0], parts[1]

    def outside_hole(point: tuple[float, float, float]) -> bool:
        x, y, _ = point
        return abs(x) > model.KEY_X_HEAD / 2 + 0.5 or abs(y) > model.HOLE_Y / 2 + 0.5

    body_a = {p for p in member_a["points"] if outside_hole(p)}
    body_b = {p for p in member_b["points"] if outside_hole(p)}
    mapped = {(round(-x, 3), y, round(model.HEIGHT - z, 3)) for x, y, z in body_a}
    print(f"\ncongruence outside the key hole (A rotated 180° about Y vs B): "
          f"{len(body_a)} vertices in A, {len(body_b)} in B")
    unmatched = [p for p in mapped
                 if not any(all(abs(a - b) < VERTEX_TOL for a, b in zip(p, q))
                            for q in body_b)]
    if len(body_a) != len(body_b):
        failures.append(f"congruence: A has {len(body_a)} non-hole vertices, "
                        f"B has {len(body_b)}")
    if unmatched:
        failures.append(f"congruence: {len(unmatched)} mapped A vertices have no match in B, "
                        f"e.g. {unmatched[:3]}")
    else:
        print("  every mapped vertex of A outside the hole coincides with one of B")

    if failures:
        print("\nFAILURES:", file=sys.stderr)
        for item in failures:
            print("  " + item, file=sys.stderr)
        return 1
    print("\nOK: 3 parts; every bounding box and volume matches the analytic model, and")
    print("    member A rotated 180° about Y reproduces member B outside the key hole.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
