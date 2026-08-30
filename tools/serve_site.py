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


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve Printable Joinery Atlas locally")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    mimetypes.add_type("model/gltf-binary", ".glb")
    mimetypes.add_type("model/gltf+json", ".gltf")
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
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
