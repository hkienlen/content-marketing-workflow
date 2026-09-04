#!/usr/bin/env python3
"""Temporary bounded media-source probe for the existing WordPress relay.

It reuses the existing `prepare_article` parent operation only when the payload
contains `experimental_mode=media_source_probe`. It can run download-only or
call the already-existing Bridge `media_upsert` child operation. It never
creates, updates, or publishes an article.
"""
from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import pathlib
import re
from typing import Any

HERE = pathlib.Path(__file__).resolve().parent


def _load_module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


media_source = _load_module("media_source_fetch", HERE / "media-source-fetch.py")
prepare_core = _load_module("wordpress_relay_prepare_v2_probe", HERE / "wordpress-relay-prepare-v2.py")


class ProbeError(RuntimeError):
    pass


def load_json(path: str) -> dict[str, Any]:
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ProbeError(f"JSON object required: {path}")
    return data


def safe_probe_path(value: str) -> str:
    path = prepare_core.safe_repo_path(value)
    if not path.startswith("wordpress/media-source/probes/"):
        raise ProbeError("Probe descriptor path must be under wordpress/media-source/probes/")
    return path


def load_pinned_descriptor(payload: dict[str, Any]) -> tuple[dict[str, Any], str, str, bytes]:
    path = safe_probe_path(str(payload.get("descriptor_path", "")))
    commit = str(payload.get("descriptor_commit", "")).strip().lower()
    prepare_core.ensure_commit(commit, "payload.descriptor_commit")
    raw = prepare_core.git_bytes(commit, path)
    try:
        descriptor = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProbeError("Probe descriptor is not valid UTF-8 JSON") from exc
    if not isinstance(descriptor, dict) or int(descriptor.get("schema_version", 0)) != 1:
        raise ProbeError("Unsupported probe descriptor schema_version")
    source = descriptor.get("media_source")
    if not isinstance(source, dict):
        raise ProbeError("Probe descriptor requires media_source object")
    return descriptor, path, commit, raw


def synthetic_media_identity(result: dict[str, Any]) -> str:
    provider = str(result["provider"])
    file_id = str(result.get("file_id", ""))
    filename = str(result["filename"])
    if not re.fullmatch(r"[a-z0-9_]+", provider):
        raise ProbeError("Unsafe provider for synthetic media identity")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,200}", file_id):
        raise ProbeError("Unsafe provider file identity")
    if pathlib.PurePosixPath(filename).name != filename:
        raise ProbeError("Unsafe filename for synthetic media identity")
    return f"external-media/{provider}/{file_id}/{filename}"


def run_probe(
    parent: dict[str, Any],
    descriptor: dict[str, Any],
    descriptor_path: str,
    token: str,
    endpoint: str,
) -> dict[str, Any]:
    source = descriptor["media_source"]
    fetched = media_source.fetch_and_verify(source)
    summary = {key: value for key, value in fetched.items() if key not in {"bytes", "fetched_url"}}
    payload = parent.get("payload") if isinstance(parent.get("payload"), dict) else {}
    result: dict[str, Any] = {
        "descriptor_path": descriptor_path,
        "article_slug": str(descriptor.get("article_slug", "")),
        "mode": str(payload.get("probe_action", "download_only")),
        "download": summary,
    }

    mode = result["mode"]
    if mode == "download_only":
        return result
    if mode != "media_upsert":
        raise ProbeError("probe_action must be download_only or media_upsert")

    media = descriptor.get("wordpress_media")
    if not isinstance(media, dict):
        raise ProbeError("media_upsert probe requires wordpress_media object")
    key = str(media.get("key", "")).strip()
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,63}", key):
        raise ProbeError("Invalid wordpress_media.key")

    media_payload = {
        "manifest_path": descriptor_path,
        "repository_path": synthetic_media_identity(fetched),
        "asset_key": key,
        "sha256": fetched["sha256"],
        "filename": fetched["filename"],
        "mime_type": fetched["mime_type"],
        "content_base64": base64.b64encode(fetched["bytes"]).decode("ascii"),
        "title": str(media.get("title", "")),
        "alt": str(media.get("alt", "")),
        "caption": str(media.get("caption", "")),
    }
    response = prepare_core.wp_call(
        endpoint,
        token,
        prepare_core.envelope(parent, "media_upsert", "experimental-media-source", media_payload),
    )
    wp_result = response.get("result")
    if not isinstance(wp_result, dict) or not wp_result.get("id") or not wp_result.get("url"):
        raise ProbeError("media_upsert returned an invalid result")
    if str(wp_result.get("sha256", "")) != fetched["sha256"]:
        raise ProbeError("WordPress media_upsert SHA-256 does not match verified source bytes")
    result["wordpress_media"] = {
        "id": int(wp_result["id"]),
        "url": str(wp_result["url"]),
        "reused": bool(wp_result.get("reused")),
        "sha256": str(wp_result.get("sha256", "")),
        "repository_path": str(wp_result.get("repository_path", "")),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--oidc-token-file", required=True)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--response", required=True)
    parser.add_argument("--github-token")
    args = parser.parse_args()

    response_path = pathlib.Path(args.response)
    parent = load_json(args.request)
    try:
        if parent.get("operation") != "prepare_article":
            raise ProbeError("Media-source probe must use prepare_article parent operation")
        payload = parent.get("payload")
        if not isinstance(payload, dict) or payload.get("experimental_mode") != "media_source_probe":
            raise ProbeError("Missing experimental_mode=media_source_probe")
        descriptor, descriptor_path, descriptor_commit, descriptor_raw = load_pinned_descriptor(payload)
        token = pathlib.Path(args.oidc_token_file).read_text(encoding="utf-8").strip()
        probe = run_probe(parent, descriptor, descriptor_path, token, args.endpoint)
        aggregate = {
            "ok": True,
            "schema_version": 1,
            "request_id": parent["request_id"],
            "operation": "media_source_probe",
            "result": {
                "descriptor_commit": descriptor_commit,
                "descriptor_sha256": prepare_core.sha256(descriptor_raw),
                **probe,
            },
        }
        response_path.write_text(json.dumps(aggregate, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        return 0
    except Exception as exc:
        response_path.write_text(
            json.dumps({
                "ok": False,
                "schema_version": 1,
                "request_id": str(parent.get("request_id", "")),
                "error": {"code": "media_source_probe_failed", "message": str(exc)},
            }, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        print(str(exc), file=__import__("sys").stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
