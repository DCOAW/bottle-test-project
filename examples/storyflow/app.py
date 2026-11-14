"""StoryFlow AI — local-only JSON knowledge and campaign intake.

Run from the Bottle fork root: python3 examples/storyflow/app.py
WSGI: from examples.storyflow.app import application

SPDX-License-Identifier: Unlicense
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = PROJECT_ROOT.parents[1]
# Reuse the existing framework from this Bottle fork without installing packages.
# This also works when app.py is launched with an absolute path from elsewhere.
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from bottle import Bottle, request, response, run, static_file, template


MAX_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_DATASETS = 200


class InvalidImport(ValueError):
    """An uploaded JSON document does not match an accepted data type."""


def _reject_json_constant(token: str) -> None:
    raise InvalidImport(f"Invalid JSON numeric value: {token}")


def _safe_filename(value: str | None) -> str:
    # Only used for display; never used to construct storage paths.
    name = re.split(r"[/\\]", value or "upload.json")[-1]
    name = "".join(char for char in name if char.isprintable()).strip()
    return name[:120] or "upload.json"


def _required_text(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidImport(f"{location} must be a non-empty string")
    return value.strip()


def _decode_json(raw: bytes) -> dict[str, Any]:
    try:
        document = json.loads(raw.decode("utf-8-sig"), parse_constant=_reject_json_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidImport(f"Invalid UTF-8 JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise InvalidImport("The JSON file must contain one top-level object")
    return document


def summarize_document(document: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Validate supported documents and return metadata, not approval decisions."""
    version = _required_text(document.get("schema_version"), "schema_version")
    if not version.startswith("1."):
        raise InvalidImport("Only schema_version 1.x is supported")

    if document.get("document_type") == "platform_knowledge":
        platform = document.get("platform")
        if not isinstance(platform, dict):
            raise InvalidImport("platform must be a JSON object")
        name = _required_text(platform.get("name"), "platform.name")
        goal = _required_text(platform.get("primary_goal"), "platform.primary_goal")
        audience = platform.get("audiences", [])
        if not isinstance(audience, list) or any(not isinstance(x, str) for x in audience):
            raise InvalidImport("platform.audiences must be a list of strings")
        return "knowledge", {
            "name": name,
            "primary_goal": goal,
            "audiences": audience[:30],
            "principles": [x for x in platform.get("principles", []) if isinstance(x, str)][:30]
            if isinstance(platform.get("principles", []), list)
            else [],
            "schema_version": version,
        }

    dataset = document.get("dataset")
    if not isinstance(dataset, dict):
        raise InvalidImport("Expected document_type 'platform_knowledge' or a StoryFlow 'dataset' object")
    dataset_id = _required_text(dataset.get("id"), "dataset.id")
    for field in ("campaigns", "goals", "content_items"):
        if not isinstance(document.get(field), list):
            raise InvalidImport(f"{field} must be an array")
    items = document["content_items"]
    if len(items) > 1000:
        raise InvalidImport("content_items cannot contain more than 1000 entries")
    ids = set()
    for position, item in enumerate(items):
        if not isinstance(item, dict):
            raise InvalidImport(f"content_items[{position}] must be an object")
        item_id = _required_text(item.get("id"), f"content_items[{position}].id")
        _required_text(item.get("title"), f"content_items[{position}].title")
        if item_id in ids:
            raise InvalidImport(f"Duplicate content item ID: {item_id}")
        ids.add(item_id)

    daily_plan = document.get("daily_plan", [])
    if not isinstance(daily_plan, list):
        raise InvalidImport("daily_plan must be an array when provided")
    campaign_names = [c.get("name", "Untitled campaign") for c in document["campaigns"] if isinstance(c, dict)]
    goal_names = [g.get("title", "Untitled goal") for g in document["goals"] if isinstance(g, dict)]
    return "dataset", {
        "name": _required_text(dataset.get("name", dataset_id), "dataset.name"),
        "dataset_id": dataset_id,
        "campaigns": campaign_names[:30],
        "goals": goal_names[:30],
        "content_count": len(items),
        "daily_plan_count": len(daily_plan),
        "preview": [
            {"id": item["id"], "title": item["title"], "stage": "needs_human_review"}
            for item in items[:8]
        ],
        "schema_version": version,
        "imported_approvals_trusted": False,
        "scheduled_publications_enabled": False,
    }


def _write_atomically(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".storyflow-", delete=False) as temp:
            pending = Path(temp.name)
            os.chmod(pending, 0o600)
            temp.write(content)
            temp.flush()
            os.fsync(temp.fileno())
        os.replace(pending, path)
    finally:
        if pending is not None:
            pending.unlink(missing_ok=True)


class LocalImportStore:
    def __init__(self, root: Path):
        self.root = root
        self.uploads = root / "uploads"
        self.index_file = root / "index.json"
        self.lock = threading.RLock()
        self.uploads.mkdir(parents=True, exist_ok=True)

    def _load_index(self) -> dict[str, Any]:
        if not self.index_file.exists():
            return {"knowledge": None, "datasets": []}
        with self.index_file.open("r", encoding="utf-8") as source:
            index = json.load(source)
        if not isinstance(index, dict) or not isinstance(index.get("datasets"), list):
            raise RuntimeError("Stored import index is invalid")
        return index

    def state(self) -> dict[str, Any]:
        with self.lock:
            index = self._load_index()
        return {
            "knowledge": index.get("knowledge"),
            "datasets": list(reversed(index.get("datasets", []))),
            "mode": "local_internal_demo",
            "workflow": ["import", "analyze (next)", "human review (next)", "plan (next)", "schedule (next)"],
            "automatic_publishing": False,
        }

    def import_file(self, filename: str, raw: bytes) -> dict[str, Any]:
        kind, summary = summarize_document(_decode_json(raw))
        digest = hashlib.sha256(raw).hexdigest()
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        record = {
            "id": digest[:16],
            "kind": kind,
            "filename": _safe_filename(filename),
            "imported_at": timestamp,
            "sha256": digest,
            "stage": "staged_only",
            **summary,
        }

        with self.lock:
            index = self._load_index()
            if kind == "dataset" and not any(x["sha256"] == digest for x in index["datasets"]):
                if len(index["datasets"]) >= MAX_DATASETS:
                    raise InvalidImport(f"At most {MAX_DATASETS} staged datasets are supported")
            stored = self.uploads / f"{digest}.json"
            if not stored.exists():
                _write_atomically(stored, raw)
            duplicate = False
            if kind == "knowledge":
                duplicate = bool(index.get("knowledge", {}).get("sha256") == digest) if index.get("knowledge") else False
                index["knowledge"] = record
            else:
                duplicate = any(x["sha256"] == digest for x in index["datasets"])
                if not duplicate:
                    index["datasets"].append(record)
            _write_atomically(self.index_file, (json.dumps(index, indent=2) + "\n").encode("utf-8"))
        return {"ok": True, "kind": kind, "duplicate": duplicate, "record": record}


def create_app(storage_dir: str | Path | None = None) -> Bottle:
    root = Path(storage_dir or os.environ.get("STORYFLOW_DATA_DIR") or PROJECT_ROOT / "data").expanduser()
    store = LocalImportStore(root)
    app = Bottle()

    @app.hook("after_request")
    def set_security_headers() -> None:
        response.set_header("Cache-Control", "no-store")
        response.set_header("X-Content-Type-Options", "nosniff")
        response.set_header("X-Frame-Options", "DENY")
        response.set_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; "
            "connect-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
        )

    @app.get("/")
    def dashboard() -> str:
        base_path = request.environ.get("SCRIPT_NAME", "").rstrip("/")
        return template("index.tpl", template_lookup=[str(PROJECT_ROOT / "views")], base_path=base_path)

    @app.get("/assets/<filename:path>")
    def assets(filename: str):
        return static_file(filename, root=str(PROJECT_ROOT / "static"))

    @app.get("/examples/knowledge.json")
    def example_knowledge():
        return static_file("knowledge.example.json", root=str(PROJECT_ROOT / "examples"), download="knowledge.example.json")

    @app.get("/healthz")
    def health() -> dict[str, Any]:
        return {"ok": True, "service": "storyflow-intake"}

    @app.get("/api/state")
    def state() -> dict[str, Any]:
        return {"ok": True, **store.state()}

    @app.post("/api/import")
    def import_json() -> dict[str, Any]:
        declared_length = request.content_length
        if declared_length is not None and declared_length > MAX_UPLOAD_BYTES + 16384:
            response.status = 413
            return {"ok": False, "error": "Maximum upload size is 2 MB"}
        try:
            if request.content_type.startswith("application/json"):
                filename = request.headers.get("X-Filename", "uploaded.json")
                raw = request.body.read(MAX_UPLOAD_BYTES + 1)
            else:
                uploaded = request.files.get("file")
                if uploaded is None:
                    raise InvalidImport("Choose a .json file to upload")
                filename = uploaded.raw_filename or uploaded.filename or "uploaded.json"
                try:
                    raw = uploaded.file.read(MAX_UPLOAD_BYTES + 1)
                finally:
                    uploaded.file.close()
            if not filename.lower().endswith(".json"):
                raise InvalidImport("Only .json files are accepted")
            if not raw:
                raise InvalidImport("The uploaded JSON file is empty")
            if len(raw) > MAX_UPLOAD_BYTES:
                response.status = 413
                return {"ok": False, "error": "Maximum upload size is 2 MB"}
            return store.import_file(filename, raw)
        except InvalidImport as exc:
            response.status = 400
            return {"ok": False, "error": str(exc)}

    return app


application = create_app()


if __name__ == "__main__":
    host = os.environ.get("STORYFLOW_HOST", "127.0.0.1")
    port = int(os.environ.get("STORYFLOW_PORT", "8000"))
    print(f"StoryFlow AI: http://{host}:{port} (internal, no authentication)")
    run(app=application, host=host, port=port, quiet=False, debug=False, reloader=False)
