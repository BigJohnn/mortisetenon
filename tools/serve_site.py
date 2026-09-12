#!/usr/bin/env python3
"""Serve the Atlas over HTTP so browsers may fetch GLB assets.

Usage:
    python3 tools/serve_site.py
Then open http://localhost:8000/joints/straight-tenon.html.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import mimetypes
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AtlasHandler(http.server.SimpleHTTPRequestHandler):
    """Local preview only; never expose secrets, dot directories or symlink escapes."""
    def __init__(self, *args, private_cad=False, **kwargs):
        self.private_cad = private_cad
        super().__init__(*args, **kwargs)

    def send_head(self):
        translated = Path(self.translate_path(self.path))
        root = Path(self.directory).resolve()
        try:
            # Check both the requested name and its symlink-resolved target.
            candidates = [translated]
            if translated.is_dir():
                for name in ('index.html', 'index.htm'):
                    candidate = translated/name
                    if candidate.is_file():
                        candidates.append(candidate)
                        break
            paths = [path for candidate in candidates for path in
                     (candidate.relative_to(Path(self.directory).absolute()), candidate.resolve().relative_to(root))]
        except ValueError:
            self.send_error(404); return None
        for path in paths:
            if any(part.startswith('.') for part in path.parts):
                self.send_error(404); return None
            private = (path.parts[:2] == ('cad', 'private') or
                       len(path.parts) >= 2 and path.parts[0] == 'cad' and
                       path.parts[1].startswith('table-node-pair_freecad_v'))
            if private and not self.private_cad:
                self.send_error(404); return None
        return super().send_head()

    def list_directory(self, path):
        self.send_error(404)
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve Printable Joinery Atlas locally")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--private-cad", action="store_true", help="Explicitly serve local private CAD for review; still bound to 127.0.0.1. Do not tunnel or deploy this server.")
    args = parser.parse_args()

    mimetypes.add_type("model/gltf-binary", ".glb")
    mimetypes.add_type("model/gltf+json", ".gltf")
    handler = functools.partial(AtlasHandler, directory=ROOT, private_cad=args.private_cad)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"Serving {ROOT} at http://localhost:{args.port}/")
    print("Open http://localhost:%d/joints/straight-tenon.html" % args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
