#!/usr/bin/env python3
"""Stable preparation entrypoint with bounded legacy probe routing.

Normal preparation delegates to provider-aware v6. Manifest v2 remains
backward-compatible through v6 -> v5. The historical media-source probe stays
available only when explicitly requested by `experimental_mode`.
"""

from pathlib import Path
import json
import runpy
import sys

HERE = Path(__file__).resolve().parent


def _experimental_media_probe_requested(argv: list[str]) -> bool:
    try:
        request_index = argv.index("--request") + 1
        request_path = Path(argv[request_index])
        body = json.loads(request_path.read_text(encoding="utf-8"))
        payload = body.get("payload") if isinstance(body, dict) else None
        return (
            body.get("operation") == "prepare_article"
            and isinstance(payload, dict)
            and payload.get("experimental_mode") == "media_source_probe"
        )
    except (ValueError, IndexError, OSError, json.JSONDecodeError):
        return False


if _experimental_media_probe_requested(sys.argv):
    runpy.run_path(str(HERE / "wordpress-relay-media-source-probe.py"), run_name="__main__")
else:
    runpy.run_path(str(HERE / "wordpress-relay-prepare-v6.py"), run_name="__main__")
