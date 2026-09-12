#!/usr/bin/env python3
"""Report CAD exposure; --staged fails on protected files being added/modified.

This does not remove tracked files, change history, install hooks, or push.
Run --tracked for an inventory that includes already-published legacy assets.
"""
import argparse
from pathlib import PurePosixPath
import re
import subprocess

SOURCE_SCRIPTS={"build_table_nodes_freecad.py","build_table_nodes_onshape.py","check_table_nodes_local.py","check_freecad_table_nodes.py","create_dovetail_onshape.py","create_keyed_tenon_onshape.py","render_table_nodes_local.py"}
GEOMETRY={".step",".stp",".stl",".3mf",".glb",".gltf",".iges",".igs",".brep",".dxf",".dwg",".fcmacro",".fcbak"}


def reason(path):
    p=PurePosixPath(path);s=p.suffix.lower()
    if any(part=='.env' or part.startswith('.env.') for part in p.parts):return "environment configuration / possible secrets"
    if path.startswith("cad/private/") or re.match(r"cad/table-node-pair_freecad_v[^/]+/",path):return "private CAD workspace"
    if re.fullmatch(r"\.fcstd\d*",s) or s in GEOMETRY:return "native / exact geometry / backup"
    if path.startswith("cad/") and s in {".fs",".scad"}:return "reconstructable parametric source"
    if path.startswith("cad/") and ("parameters" in p.name or p.name in {"report.json","source-report.json"}):return "exact parameters / detailed geometry report"
    if path.startswith("tools/") and p.name in SOURCE_SCRIPTS:return "geometry-generating source or reference implementation"
    return None


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--staged",action="store_true")
    group.add_argument("--tracked",action="store_true")
    args=parser.parse_args()
    command=["git","diff","--cached","--name-only","--diff-filter=ACMR","-z"] if args.staged else ["git","ls-files","-z"]
    paths=subprocess.check_output(command).decode().split("\0")
    flagged=[(p,reason(p)) for p in paths if p and reason(p)]
    for path,why in flagged:print(f"PROTECTED {path} — {why}")
    print(f"{'Staged' if args.staged else 'Tracked'} CAD risk files: {len(flagged)}")
    if args.tracked and flagged:print("Ignore rules do not remove these from Git or its history. Review before further publication.")
    return 1 if flagged else 0


if __name__=="__main__":raise SystemExit(main())
