#!/usr/bin/env python3
"""Probe one registered WordPress presentation adapter without creating content.

The parent relay operation is provider-neutral (`presentation_probe`). Adapter-
specific execution is explicit and bounded. V1 registers only the Divi adapter.
Supported actions:

- `detect`: inspect public WordPress REST registration for relevant Divi routes,
  including declared methods and argument names;
- `d4_to_d5`: execute the bridge's bounded Divi conversion adapter against a
  repository-pinned Divi 4 reference/template.

Neither action creates or modifies posts, media, metadata or taxonomies.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request
from typing import Any

CORE_PATH = pathlib.Path(__file__).with_name("wordpress-relay-prepare-v2.py")
spec = importlib.util.spec_from_file_location("wordpress_relay_prepare_v2", CORE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load wordpress-relay-prepare-v2.py")
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


def load_json(path: str) -> dict[str, Any]:
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise core.PrepareError(f"JSON object required: {path}")
    return data


def derive_divi_endpoint(profile: dict[str, Any]) -> str:
    relay = profile.get("relay") if isinstance(profile.get("relay"), dict) else {}
    explicit = str(relay.get("divi_convert_endpoint", "")).strip()
    if explicit:
        return explicit
    prepare = str(relay.get("prepare_endpoint", "")).strip()
    suffix = "/seo-workflow-bridge/v1/prepare"
    if not prepare.endswith(suffix):
        raise core.PrepareError("Unable to derive Divi adapter endpoint from preparation endpoint")
    return prepare[: -len(suffix)] + "/seo-workflow-bridge/v1/divi-convert"


def public_rest_index(profile: dict[str, Any]) -> dict[str, Any]:
    site = str(profile.get("expected_site_url", "")).rstrip("/")
    if not site.startswith("https://"):
        raise core.PrepareError("expected_site_url must be HTTPS")
    request = urllib.request.Request(
        site + "/wp-json/",
        method="GET",
        headers={"Accept": "application/json", "User-Agent": "seo-workflow-bridge-relay"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        raise core.PrepareError(f"Unable to inspect WordPress REST index: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("routes"), dict):
        raise core.PrepareError("WordPress REST index does not expose a routes object")
    return data


def route_contract(route: str, descriptor: Any) -> dict[str, Any]:
    endpoints = descriptor.get("endpoints") if isinstance(descriptor, dict) else None
    normalized: list[dict[str, Any]] = []
    if isinstance(endpoints, list):
        for endpoint in endpoints:
            if not isinstance(endpoint, dict):
                continue
            methods_raw = endpoint.get("methods")
            if isinstance(methods_raw, list):
                methods = sorted(str(v) for v in methods_raw)
            elif isinstance(methods_raw, dict):
                methods = sorted(str(k) for k, v in methods_raw.items() if v)
            elif methods_raw is None:
                methods = []
            else:
                methods = [str(methods_raw)]
            args = endpoint.get("args")
            arg_summary: dict[str, Any] = {}
            if isinstance(args, dict):
                for name, spec in sorted(args.items()):
                    if not isinstance(spec, dict):
                        arg_summary[str(name)] = {}
                        continue
                    arg_summary[str(name)] = {
                        "required": bool(spec.get("required", False)),
                        "type": spec.get("type"),
                        "default": spec.get("default") if "default" in spec else None,
                    }
            normalized.append({"methods": methods, "args": arg_summary})
    return {"route": route, "endpoints": normalized}


def detect_divi(profile: dict[str, Any], request_id: str) -> dict[str, Any]:
    data = public_rest_index(profile)
    routes = data["routes"]
    selected: list[dict[str, Any]] = []
    for route, descriptor in routes.items():
        name = str(route)
        lower = name.lower()
        if "divi" in lower and any(word in lower for word in ("conversion", "migration", "content", "layout")):
            selected.append(route_contract(name, descriptor))
    selected.sort(key=lambda item: item["route"])
    return {
        "ok": True,
        "schema_version": 1,
        "request_id": request_id,
        "operation": "presentation_probe",
        "site_url": profile.get("expected_site_url", ""),
        "result": {
            "adapter": "divi",
            "action": "detect",
            "registered_divi_content_routes": selected,
            "route_count": len(selected),
        },
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--oidc-token-file", required=True)
    parser.add_argument("--response", required=True)
    args = parser.parse_args()

    response_path = pathlib.Path(args.response)
    parent = load_json(args.request)
    profile = load_json(args.profile)
    token = pathlib.Path(args.oidc_token_file).read_text().strip()

    try:
        if parent.get("operation") != "presentation_probe":
            raise core.PrepareError("This helper accepts only presentation_probe")
        payload = parent.get("payload")
        if not isinstance(payload, dict):
            raise core.PrepareError("presentation_probe payload must be an object")

        adapter = str(payload.get("adapter", "")).strip()
        action = str(payload.get("action", "")).strip()
        if adapter != "divi" or action not in ("detect", "d4_to_d5"):
            raise core.PrepareError("Unsupported presentation adapter/action")

        request_id = str(parent.get("request_id", ""))
        if action == "detect":
            response_path.write_text(
                json.dumps(detect_divi(profile, request_id), ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
            )
            return 0

        content_commit = str(payload.get("content_commit", "")).lower()
        core.ensure_commit(content_commit, "content_commit")
        content_path = core.safe_repo_path(str(payload.get("content_path", "")))
        relay = profile.get("relay") if isinstance(profile.get("relay"), dict) else {}
        prefixes = relay.get("prepare_content_prefixes", ["articles", "wordpress"])
        if not isinstance(prefixes, list) or not all(isinstance(x, str) for x in prefixes):
            raise core.PrepareError("prepare_content_prefixes are invalid")
        if not core.allowed_prefix(content_path, prefixes):
            raise core.PrepareError("Probe content path is outside allowed content prefixes")

        expected_blob = str(payload.get("content_git_blob_sha", "")).lower()
        core.verify_git_blob(content_commit, content_path, expected_blob)
        raw = core.git_bytes(content_commit, content_path)
        content = raw.decode("utf-8")
        if not re.search(r"\[et_pb_(?:section|row|column|text)\b", content):
            raise core.PrepareError("Divi probe input does not contain core Divi 4 layout shortcodes")

        digest = hashlib.sha256((request_id + ":presentation_probe:divi").encode("utf-8")).hexdigest()[:16]
        child_id = f"{request_id[:100]}.probe.{digest}"
        envelope = {
            "schema_version": 1,
            "request_id": child_id[:128],
            "connection_id": parent["connection_id"],
            "operation": "divi_d4_to_d5",
            "issued_at": parent["issued_at"],
            "payload": {"content": content},
        }
        converted = core.wp_call(derive_divi_endpoint(profile), token, envelope)
        result = converted.get("result")
        if not isinstance(result, dict) or not isinstance(result.get("content"), str):
            raise core.PrepareError("Divi adapter returned an invalid conversion result")
        output = str(result["content"])
        checks = {
            "changed": bool(output and output != content),
            "native_divi_storage": "<!-- wp:divi/" in output,
            "core_legacy_shortcodes_absent": re.search(r"\[et_pb_(?:section|row|column|text)\b", output) is None,
        }
        if not all(checks.values()):
            raise core.PrepareError(f"Divi adapter probe failed: {json.dumps(checks, sort_keys=True)}")

        response = {
            "ok": True,
            "schema_version": 1,
            "request_id": request_id,
            "operation": "presentation_probe",
            "site_url": converted.get("site_url", ""),
            "result": {
                "adapter": adapter,
                "action": action,
                "content_path": content_path,
                "content_commit": content_commit,
                "content_git_blob_sha": expected_blob,
                "input_sha256": hashlib.sha256(raw).hexdigest(),
                "output_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
                "converter": str(result.get("converter", "")),
                "checks": checks,
            },
        }
        response_path.write_text(json.dumps(response, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        return 0
    except Exception as exc:
        response = {
            "ok": False,
            "schema_version": 1,
            "request_id": str(parent.get("request_id", "")),
            "operation": "presentation_probe",
            "error": {"code": "presentation_probe_failed", "message": str(exc)},
        }
        response_path.write_text(json.dumps(response, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
