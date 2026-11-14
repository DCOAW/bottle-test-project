"""Standard-library WSGI tests. No external HTTP or browser downloads."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

STORYFLOW_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STORYFLOW_ROOT))

from app import create_app


class StoryFlowIntakeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.app = create_app(Path(self.temp.name) / "storage")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def request(self, method="GET", path="/", data=b"", content_type="application/json", prefix="", filename=None):
        status = {}
        environ = {
            "REQUEST_METHOD": method,
            "SCRIPT_NAME": prefix,
            "PATH_INFO": path,
            "QUERY_STRING": "",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8000",
            "SERVER_PROTOCOL": "HTTP/1.1",
            "CONTENT_TYPE": content_type,
            "CONTENT_LENGTH": str(len(data)),
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": "http",
            "wsgi.input": io.BytesIO(data),
            "wsgi.errors": io.StringIO(),
            "wsgi.multithread": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
        }
        if filename:
            environ["HTTP_X_FILENAME"] = filename

        def start_response(code, headers, exc_info=None):
            status["code"] = int(code.split()[0])
            status["headers"] = dict(headers)

        response = self.app(environ, start_response)
        try:
            content = b"".join(response)
        finally:
            if hasattr(response, "close"):
                response.close()
        return status["code"], content, status["headers"]

    def post_json(self, obj, filename="sample.json"):
        return self.request(method="POST", path="/api/import", data=json.dumps(obj).encode("utf-8"), filename=filename)

    def example_knowledge(self):
        return {
            "schema_version": "1.0.0",
            "document_type": "platform_knowledge",
            "platform": {"name": "Demo", "primary_goal": "Keep humans in control", "audiences": ["Operators"]},
        }

    def example_dataset(self):
        return {
            "schema_version": "1.0.0",
            "dataset": {"id": "demo-december", "name": "December Campaign"},
            "campaigns": [{"name": "Launch"}],
            "goals": [{"title": "Create 12 pieces"}],
            "content_items": [{"id": "a-1", "title": "First draft", "review": {"status": "approved"}}],
            "daily_plan": [{"date": "2026-12-01"}],
        }

    def test_home_and_health_check(self):
        code, body, headers = self.request()
        self.assertEqual(code, 200)
        self.assertIn(b"StoryFlow AI", body)
        self.assertIn(b"Knowledge intake", body)
        self.assertIn("no-store", headers["Cache-Control"])
        code, body, _ = self.request(path="/healthz")
        self.assertEqual(code, 200)
        self.assertTrue(json.loads(body)["ok"])

    def test_static_and_knowledge_example_are_available(self):
        code, body, _ = self.request(path="/assets/main.js")
        self.assertEqual(code, 200)
        self.assertIn(b"fetch", body)
        code, body, _ = self.request(path="/examples/knowledge.json")
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body)["document_type"], "platform_knowledge")

    def test_mount_prefix_in_asset_links(self):
        code, body, _ = self.request(prefix="/storyflow")
        self.assertEqual(code, 200)
        self.assertIn(b'/storyflow/assets/main.js', body)

    def test_knowledge_upload_and_restart_persistence(self):
        code, body, _ = self.post_json(self.example_knowledge())
        self.assertEqual(code, 200, body)
        self.assertEqual(json.loads(body)["kind"], "knowledge")
        code, body, _ = self.request(path="/api/state")
        self.assertEqual(json.loads(body)["knowledge"]["primary_goal"], "Keep humans in control")
        new_app = create_app(Path(self.temp.name) / "storage")
        self.app = new_app
        code, body, _ = self.request(path="/api/state")
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body)["knowledge"]["name"], "Demo")

    def test_dataset_stages_drafts_without_trusting_approval(self):
        code, body, _ = self.post_json(self.example_dataset())
        self.assertEqual(code, 200, body)
        result = json.loads(body)
        self.assertFalse(result["record"]["imported_approvals_trusted"])
        self.assertFalse(result["record"]["scheduled_publications_enabled"])
        self.assertEqual(result["record"]["preview"][0]["stage"], "needs_human_review")
        code, body, _ = self.request(path="/api/state")
        self.assertEqual(json.loads(body)["datasets"][0]["daily_plan_count"], 1)

    def test_deduplicate_identical_dataset(self):
        self.post_json(self.example_dataset())
        code, body, _ = self.post_json(self.example_dataset())
        self.assertEqual(code, 200)
        self.assertTrue(json.loads(body)["duplicate"])
        _, body, _ = self.request(path="/api/state")
        self.assertEqual(len(json.loads(body)["datasets"]), 1)

    def test_reject_invalid_json(self):
        code, body, _ = self.request("POST", "/api/import", b"{bad json", filename="bad.json")
        self.assertEqual(code, 400)
        self.assertFalse(json.loads(body)["ok"])

    def test_reject_invalid_dataset_structure(self):
        broken = self.example_dataset()
        broken["content_items"].append({"id": "a-1", "title": "Duplicate"})
        code, body, _ = self.post_json(broken)
        self.assertEqual(code, 400)
        self.assertIn("Duplicate", json.loads(body)["error"])

    def test_reject_non_json_filename(self):
        code, body, _ = self.post_json(self.example_knowledge(), filename="text.txt")
        self.assertEqual(code, 400)
        self.assertIn(".json", json.loads(body)["error"])

    def test_reject_oversized_upload(self):
        data = b" " * (2 * 1024 * 1024 + 1)
        code, body, _ = self.request("POST", "/api/import", data, filename="large.json")
        self.assertEqual(code, 413)
        self.assertIn("2 MB", json.loads(body)["error"])

    def test_multipart_browser_upload(self):
        boundary = "storyflowtestboundary"
        payload = json.dumps(self.example_knowledge()).encode()
        body = (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"knowledge.json\"\r\n"
            "Content-Type: application/json\r\n\r\n"
        ).encode() + payload + f"\r\n--{boundary}--\r\n".encode()
        code, response_body, _ = self.request(
            "POST", "/api/import", body, content_type=f"multipart/form-data; boundary={boundary}"
        )
        self.assertEqual(code, 200, response_body)
        self.assertEqual(json.loads(response_body)["kind"], "knowledge")

    def test_fork_sample_datasets_are_stageable(self):
        sample_dir = STORYFLOW_ROOT.parents[1] / "docs" / "sample-data"
        if not sample_dir.is_dir():
            self.skipTest("Bottle fork sample data is not present in this test checkout")
        for name in ("storyflow_ai_demo_template.json", "programlift_ai_30_day_launch_demo.json"):
            with self.subTest(name=name):
                raw = (sample_dir / name).read_bytes()
                code, body, _ = self.request("POST", "/api/import", raw, filename=name)
                self.assertEqual(code, 200, body)
                result = json.loads(body)
                self.assertEqual(result["kind"], "dataset")
                self.assertFalse(result["record"]["imported_approvals_trusted"])


if __name__ == "__main__":
    unittest.main()
