#!/usr/bin/env python3
"""Small Onshape REST client that reads credentials only from the environment."""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("method", choices=("GET", "POST", "DELETE"))
    parser.add_argument("path", help="API path beginning with /api/")
    parser.add_argument("--data", help="JSON request body file")
    parser.add_argument("--output", help="Response output file; defaults to stdout")
    args = parser.parse_args()

    access_key = os.environ.get("ONSHAPE_ACCESS_KEY")
    secret_key = os.environ.get("ONSHAPE_SECRET_KEY")
    base_url = os.environ.get("ONSHAPE_BASE_URL", "https://cad.onshape.com").rstrip("/")
    if not access_key or not secret_key:
        parser.error("ONSHAPE_ACCESS_KEY and ONSHAPE_SECRET_KEY are required")
    if not args.path.startswith("/api/"):
        parser.error("path must begin with /api/")

    headers = {
        "Accept": "application/json;charset=UTF-8; qs=0.09",
        "Authorization": "Basic "
        + base64.b64encode(f"{access_key}:{secret_key}".encode()).decode(),
    }
    body = None
    if args.data:
        with open(args.data, "rb") as payload:
            body = payload.read()
        headers["Content-Type"] = "application/json;charset=UTF-8; qs=0.09"

    request = urllib.request.Request(
        base_url + args.path, data=body, headers=headers, method=args.method
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = response.read()
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        print(f"Onshape API returned HTTP {error.code}: {detail}", file=sys.stderr)
        return 1

    if args.output:
        with open(args.output, "wb") as output:
            output.write(result)
    else:
        sys.stdout.buffer.write(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
