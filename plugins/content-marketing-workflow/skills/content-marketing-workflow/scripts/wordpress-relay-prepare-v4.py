#!/usr/bin/env python3
"""Prepare v2 wrapper using Divi's official server-side D4 -> D5 converter.

This wrapper intentionally does not reverse-engineer Divi 5 block storage. A
repository template may request `server_transform: divi_d4_to_d5`; in that case
legacy Divi 4 shortcode content is sent to the authenticated WordPress bridge's
transform-only endpoint, and only Divi's own converted output is persisted by
the normal draft preparation controller.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import re
import sys
from typing import Any

CORE_PATH = pathlib.Path(__file__).with_name("wordpress-relay-prepare-v2.py")
spec = importlib.util.spec_from_file_location("wordpress_relay_prepare_v2", CORE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load wordpress-relay-prepare-v2.py")
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

_original_resolve_repository_content = core.resolve_repository_content
_original_wp_call = core.wp_call
_original_verify_readback = core.verify_readback
_transform_mode: str | None = None
_converted_content: str | None = None
_conversion_summary: dict[str, Any] | None = None


def resolve_repository_content(
    content_cfg: dict[str, Any],
    source_commit: str,
    prefixes: list[str],
    article_body_html: str,
    media_results: dict[str, dict[str, Any]],
) -> str:
    global _transform_mode
    transform = str(content_cfg.get("server_transform", "")).strip()
    if transform not in ("", "divi_d4_to_d5"):
        raise core.PrepareError(f"Unsupported server_transform: {transform}")
    _transform_mode = transform or None
    text = _original_resolve_repository_content(
        content_cfg, source_commit, prefixes, article_body_html, media_results
    )
    if transform == "divi_d4_to_d5":
        text = re.sub(r"^\s*<!--\s*wp:divi/placeholder\s*-->\s*", "", text)
        text = re.sub(r"\s*<!--\s*/wp:divi/placeholder\s*-->\s*$", "", text)
        if not re.search(r"\[et_pb_(?:section|row|column|text)\b", text):
            raise core.PrepareError("divi_d4_to_d5 input does not contain core Divi 4 shortcodes")
    return text


def _conversion_endpoint(prepare_endpoint: str) -> str:
    suffix = "/seo-workflow-bridge/v1/prepare"
    if not prepare_endpoint.endswith(suffix):
        raise core.PrepareError("Unable to derive Divi conversion endpoint from preparation endpoint")
    return prepare_endpoint[: -len(suffix)] + "/seo-workflow-bridge/v1/divi-convert"


def _conversion_envelope(article_envelope: dict[str, Any], content: str) -> dict[str, Any]:
    base_id = str(article_envelope.get("request_id", ""))
    digest = hashlib.sha256((base_id + ":divi_d4_to_d5").encode("utf-8")).hexdigest()[:16]
    max_base = 128 - len(digest) - len(".divi.")
    return {
        "schema_version": 1,
        "request_id": f"{base_id[:max_base]}.divi.{digest}",
        "connection_id": article_envelope["connection_id"],
        "operation": "divi_d4_to_d5",
        "issued_at": article_envelope["issued_at"],
        "payload": {"content": content},
    }


def wp_call(endpoint: str, token: str, envelope_data: dict[str, Any]) -> dict[str, Any]:
    global _converted_content, _conversion_summary
    if _transform_mode == "divi_d4_to_d5" and envelope_data.get("operation") == "article_prepare":
        payload = envelope_data.get("payload")
        if not isinstance(payload, dict):
            raise core.PrepareError("article_prepare payload is missing during Divi conversion")
        legacy = str(payload.get("content", ""))
        conversion = _original_wp_call(
            _conversion_endpoint(endpoint),
            token,
            _conversion_envelope(envelope_data, legacy),
        )
        result = conversion.get("result")
        if not isinstance(result, dict) or not isinstance(result.get("content"), str):
            raise core.PrepareError("Divi conversion endpoint returned an invalid result")
        converted = str(result["content"])
        if not converted or converted == legacy:
            raise core.PrepareError("Divi did not produce changed native content")
        if re.search(r"\[et_pb_(?:section|row|column|text)\b", converted):
            raise core.PrepareError("Core Divi 4 shortcodes remain after official conversion")
        if "<!-- wp:divi/" not in converted:
            raise core.PrepareError("Official Divi conversion did not return native Divi block storage")
        _converted_content = converted
        _conversion_summary = {
            "type": "divi_d4_to_d5",
            "converter": str(result.get("converter", "")),
            "input_sha256": str(result.get("input_sha256", "")),
            "output_sha256": str(result.get("output_sha256", "")),
            "conversion_changed": bool(result.get("conversion_changed")),
        }
        forwarded = dict(envelope_data)
        forwarded_payload = dict(payload)
        forwarded_payload["content"] = converted
        forwarded["payload"] = forwarded_payload
        return _original_wp_call(endpoint, token, forwarded)
    return _original_wp_call(endpoint, token, envelope_data)


def verify_readback(
    expected: dict[str, Any],
    read: dict[str, Any],
    expected_content: str,
) -> dict[str, bool]:
    content = _converted_content if _transform_mode == "divi_d4_to_d5" else expected_content
    if _transform_mode == "divi_d4_to_d5" and not content:
        raise core.PrepareError("Converted Divi content is unavailable for verification")
    checks = _original_verify_readback(expected, read, str(content))
    if _transform_mode == "divi_d4_to_d5":
        result = read.get("result")
        actual = str(result.get("content", "")) if isinstance(result, dict) else ""
        divi_checks = {
            "divi_official_conversion_used": bool(_conversion_summary and _conversion_summary.get("conversion_changed")),
            "divi_native_storage_present": "<!-- wp:divi/" in actual,
            "divi_core_legacy_shortcodes_absent": re.search(r"\[et_pb_(?:section|row|column|text)\b", actual) is None,
        }
        checks.update(divi_checks)
        if not all(divi_checks.values()):
            raise core.PrepareError(
                f"Official Divi conversion readback verification failed: {json.dumps(divi_checks, sort_keys=True)}"
            )
    return checks


def _response_path_from_argv() -> pathlib.Path | None:
    try:
        idx = sys.argv.index("--response")
        return pathlib.Path(sys.argv[idx + 1])
    except (ValueError, IndexError):
        return None


core.resolve_repository_content = resolve_repository_content
core.wp_call = wp_call
core.verify_readback = verify_readback

if __name__ == "__main__":
    rc = core.main()
    response_path = _response_path_from_argv()
    if rc == 0 and response_path and response_path.exists() and _transform_mode == "divi_d4_to_d5":
        data = json.loads(response_path.read_text(encoding="utf-8"))
        result = data.get("result") if isinstance(data, dict) else None
        if isinstance(result, dict) and _converted_content is not None:
            result["content_sha256"] = hashlib.sha256(_converted_content.encode("utf-8")).hexdigest()
            result["content_transform"] = _conversion_summary or {"type": "divi_d4_to_d5"}
            response_path.write_text(
                json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
            )
    raise SystemExit(rc)
