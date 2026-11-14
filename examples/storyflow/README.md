# StoryFlow AI — Bottle fork demo

StoryFlow is an internal JSON knowledge and campaign intake demo integrated into
the existing Bottle fork. Its first release provides a browser UI for uploading
platform goals or campaign data, validates JSON, and stages the original files
for later human review. It does **not** approve, schedule, publish, or send content.

No sign-up, external API, Docker, npm, browser download, or dependency install
is required. This demo imports the Bottle framework from the repository root.

## Start in one command

From the **repository root**, with Python 3.10+:

```bash
python3 examples/storyflow/app.py
```

Then open <http://127.0.0.1:8000>.

You can also use an absolute path from any working directory:

```bash
python3 /path/to/bottle-test-project/examples/storyflow/app.py
```

To run isolated WSGI tests:

```bash
python3 -m unittest discover -s examples/storyflow/tests -v
```

## Files, including existing fork data

```text
bottle-test-project/
  bottle.py                                # Existing Bottle source; unchanged
  docs/sample-data/
    storyflow_ai_demo_template.json        # Existing template; unchanged
    programlift_ai_30_day_launch_demo.json # Existing 30-day sample; unchanged
  examples/storyflow/
    app.py                                 # WSGI app and local import API
    views/index.tpl                        # Browser interface
    static/main.js                         # Plain JavaScript
    static/styles.css                      # Responsive styles
    examples/knowledge.example.json       # Downloadable example knowledge document
    tests/test_app.py                      # Standard-library WSGI tests
    data/                                  # Created at runtime; ignored by Git
```

The two JSON files in `docs/sample-data/` are already part of this fork. They
remain in place and can be selected in the StoryFlow upload interface directly.
The app copies uploaded data into its local staging directory without modifying
the original JSON files in the repository.

## Supported JSON documents

1. **Platform knowledge:** `schema_version` starting with `1.`,
   `document_type: "platform_knowledge"`, and `platform` object containing
   `name`, `primary_goal`, and optionally `audiences` and `principles`.
2. **StoryFlow dataset:** `schema_version` starting with `1.`, a `dataset`
   object with `id`, and arrays called `campaigns`, `goals`, and `content_items`.
   Each content item requires a unique `id` and nonempty `title`. Optional
   `daily_plan` entries are counted for preview.

Both sample datasets in `docs/sample-data/` use the second format.
Uploaded files are limited to 2 MB; large or invalid files receive clear errors.

## Data storage and mounting

| Variable | Default | Purpose |
|---|---|---|
| `STORYFLOW_HOST` | `127.0.0.1` | Host for the local server |
| `STORYFLOW_PORT` | `8000` | HTTP port |
| `STORYFLOW_DATA_DIR` | `examples/storyflow/data/` | Writable storage for staged JSON and index |

For a persistent mount, set `STORYFLOW_DATA_DIR` to the desired absolute
directory. The original upload is stored by SHA-256 hash; repeated identical
campaigns are deduplicated. New knowledge imports become the active knowledge
record, and JSON approval claims are never treated as human approval.

The Bottle app exposes `application` as a WSGI callable for an existing server.
The UI respects the proxy-supplied `SCRIPT_NAME` mount prefix.

## API

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Knowledge intake UI |
| GET | `/examples/knowledge.json` | Download example platform knowledge |
| GET | `/api/state` | Current local staged metadata |
| POST | `/api/import` | Validate and stage a JSON upload |
| GET | `/healthz` | Health check |

Local command-line import example:

```bash
curl -H 'Content-Type: application/json' \
  -H 'X-Filename: programlift_ai_30_day_launch_demo.json' \
  --data-binary @docs/sample-data/programlift_ai_30_day_launch_demo.json \
  http://127.0.0.1:8000/api/import
```

## Boundaries and next steps

This is a **local-only, unauthenticated** developer demo. Use the default
loopback bind; do not expose it to the public internet or import sensitive
participant information. Runtime uploads are excluded from Git.

Later PRs can add document analysis, editable drafts, human verification records,
goal/milestone dashboards, and approval-gated scheduling. Nothing in this initial
PR publishes messages or performs external follow-up.

All new files in this demo are dedicated to the public domain under
[`LICENSE`](LICENSE). Existing Bottle framework files and their MIT license
are unchanged.
