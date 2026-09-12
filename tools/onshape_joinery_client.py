"""Scoped Onshape client. Loads only Onshape keys; never prints credentials."""
from __future__ import annotations
import base64
import json
from pathlib import Path
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
FOLDER = "a1428c7385ef3324eee7cfe4"


def credentials():
    values = {}
    for line in (ROOT / ".env").read_text().splitlines():
        key, sep, value = line.removeprefix("export ").partition("=")
        if sep and key.strip() in {"ONSHAPE_ACCESS_KEY", "ONSHAPE_SECRET_KEY", "ONSHAPE_BASE_URL"}:
            values[key.strip()] = value.strip().strip("\"'")
    # The user explicitly designated this repository's .env as the credential source.
    # An inherited shell may contain a different, stale key pair.
    if values.get("ONSHAPE_BASE_URL", "https://cad.onshape.com").rstrip("/") != "https://cad.onshape.com":
        raise RuntimeError("Configured Onshape origin differs from the authorized cad.onshape.com origin")
    return values


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request(method, path, payload=None, *, binary=False):
    if not path.startswith("/api/"):
        raise ValueError("Only Onshape API paths are accepted")
    values = credentials()
    token = base64.b64encode((values["ONSHAPE_ACCESS_KEY"] + ":" + values["ONSHAPE_SECRET_KEY"]).encode()).decode()
    headers = {"Authorization": "Basic " + token, "Accept": "application/json"}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode()
    req = urllib.request.Request("https://cad.onshape.com" + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=50) as response:
            raw = response.read()
            return raw if binary else json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        # Error bodies can contain identifiers; never echo request headers.
        raise RuntimeError(f"Onshape HTTP {exc.code} at {path}: " + exc.read().decode(errors="replace")[:1500]) from None


if __name__ == "__main__":
    folder = request("GET", f"/api/v10/folders/{FOLDER}")
    print(json.dumps(folder, ensure_ascii=False, indent=2))
