#!/usr/bin/env python3
"""Provider-aware WordPress preparation compatibility layer.

Manifest v2 keeps the existing repository-backed v5 behavior unchanged.
Manifest v3 may contain `public_media_source` entries. Those entries are
fetched and SHA-256 verified before any WordPress mutation, then exposed to the
existing v2 preparation core through deterministic in-memory synthetic Git
paths derived from the stable provider asset identity.

The temporary delivery object is never used as the managed WordPress identity.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import re
import runpy
import sys
from typing import Any

HERE = pathlib.Path(__file__).resolve().parent
V5_PATH = HERE / "wordpress-relay-prepare-v5.py"
MEDIA_FETCH_PATH = HERE / "media-source-fetch.py"


def _load_module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


v5 = _load_module("wordpress_relay_prepare_v5_provider_media", V5_PATH)
core = v5.core
media_fetch = _load_module("media_source_fetch_provider_media", MEDIA_FETCH_PATH)

_ORIGINAL_GIT_BYTES = core.git_bytes
_ORIGINAL_GIT_BLOB_SHA = core.git_blob_sha
_SAFE_FILENAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,254}$")
_SAFE_PROVIDER_RE = re.compile(r"^[a-z0-9_]+$")


class ProviderMediaError(RuntimeError):
    pass


def _arg_value(argv: list[str], name: str) -> str:
    try:
        return argv[argv.index(name) + 1]
    except (ValueError, IndexError) as exc:
        raise ProviderMediaError(f"Missing required argument: {name}") from exc


def _load_request(argv: list[str]) -> dict[str, Any]:
    path = pathlib.Path(_arg_value(argv, "--request"))
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ProviderMediaError("Relay request must be a JSON object")
    return data


def _load_manifest(argv: list[str]) -> tuple[dict[str, Any], str, str, bytes]:
    parent = _load_request(argv)
    if parent.get("operation") != "prepare_article":
        raise ProviderMediaError("Provider-aware preparation accepts only prepare_article")
    payload = parent.get("payload")
    if not isinstance(payload, dict):
        raise ProviderMediaError("prepare_article payload must be an object")
    manifest_path = core.safe_repo_path(str(payload.get("manifest_path", "")))
    manifest_commit = str(payload.get("manifest_commit", "")).strip().lower()
    core.ensure_commit(manifest_commit, "manifest_commit")
    raw = _ORIGINAL_GIT_BYTES(manifest_commit, manifest_path)
    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderMediaError("Preparation manifest is not valid UTF-8 JSON") from exc
    if not isinstance(manifest, dict):
        raise ProviderMediaError("Preparation manifest must be an object")
    return manifest, manifest_path, manifest_commit, raw


def _git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _stable_external_path(provider: str, asset_id: str, filename: str) -> str:
    if not _SAFE_PROVIDER_RE.fullmatch(provider):
        raise ProviderMediaError(f"Unsafe media provider: {provider}")
    if not asset_id or len(asset_id) > 300:
        raise ProviderMediaError("public_media_source asset_id is missing or too long")
    if not _SAFE_FILENAME_RE.fullmatch(filename):
        raise ProviderMediaError("public_media_source filename must be a safe canonical basename")
    identity = hashlib.sha256(f"{provider}\0{asset_id}".encode("utf-8")).hexdigest()[:32]
    return f"assets/external-media/{provider}/{identity}/{filename}"


def _provider_descriptor(source: dict[str, Any]) -> tuple[dict[str, Any], str, str, str]:
    provider = str(source.get("provider", "")).strip()
    asset_id = str(source.get("asset_id", "")).strip()
    filename = str(source.get("filename", "")).strip()
    expected_sha = str(source.get("sha256", "")).strip().lower()
    mime_type = str(source.get("mime_type", "")).strip().lower()
    delivery = source.get("delivery")
    if not isinstance(delivery, dict):
        raise ProviderMediaError("public_media_source.delivery must be an object")
    delivery_file_id = str(delivery.get("file_id", "")).strip()
    delivery_url = str(delivery.get("delivery_url", "")).strip()
    if not provider or not asset_id or not filename or not expected_sha or not mime_type:
        raise ProviderMediaError("public_media_source is missing required identity fields")
    if not delivery_file_id or not delivery_url:
        raise ProviderMediaError("public_media_source delivery file_id/delivery_url are required")

    descriptor: dict[str, Any] = {
        "provider": provider,
        "file_id": delivery_file_id,
        "delivery_url": delivery_url,
        "sha256": expected_sha,
        "filename": filename,
        "mime_type": mime_type,
        "max_bytes": 8 * 1024 * 1024,
    }
    resource_key = str(delivery.get("resource_key", "")).strip()
    if resource_key:
        descriptor["resource_key"] = resource_key
    return descriptor, provider, asset_id, delivery_file_id


def _transform_manifest_v3(
    manifest: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, bytes], dict[str, str], dict[str, dict[str, Any]]]:
    if int(manifest.get("schema_version", 0)) != 3:
        raise ProviderMediaError("Manifest v3 is required for provider-media transformation")
    transformed = json.loads(json.dumps(manifest))
    wordpress = transformed.get("wordpress")
    if not isinstance(wordpress, dict):
        raise ProviderMediaError("Manifest v3 requires wordpress object")
    media_entries = wordpress.get("media", [])
    if not isinstance(media_entries, list):
        raise ProviderMediaError("wordpress.media must be an array")

    synthetic_bytes: dict[str, bytes] = {}
    synthetic_blobs: dict[str, str] = {}
    provider_summary: dict[str, dict[str, Any]] = {}
    v2_media: list[dict[str, Any]] = []

    for media in media_entries:
        if not isinstance(media, dict):
            raise ProviderMediaError("Each manifest v3 media entry must be an object")
        key = str(media.get("key", "")).strip()
        source = media.get("source")
        if not isinstance(source, dict):
            raise ProviderMediaError(f"Media source object is required for key: {key}")
        source_type = str(source.get("type", "")).strip()
        common = {
            "key": key,
            "title": str(media.get("title", "")),
            "alt": str(media.get("alt", "")),
            "caption": str(media.get("caption", "")),
        }
        if "placement" in media:
            common["placement"] = media["placement"]

        if source_type == "repository_file":
            path = str(source.get("path", "")).strip()
            blob = str(source.get("git_blob_sha", "")).strip().lower()
            v2_media.append({**common, "path": path, "git_blob_sha": blob})
            provider_summary[key] = {
                "source_type": "repository_file",
                "path": path,
                "git_blob_sha": blob,
            }
            continue

        if source_type != "public_media_source":
            raise ProviderMediaError(f"Unsupported media source type for {key}: {source_type}")

        descriptor, provider, asset_id, delivery_file_id = _provider_descriptor(source)
        fetched = media_fetch.fetch_and_verify(descriptor)
        raw = fetched["bytes"]
        if not isinstance(raw, (bytes, bytearray)):
            raise ProviderMediaError(f"Provider adapter returned invalid bytes for key: {key}")
        raw = bytes(raw)
        declared_size = source.get("size_bytes")
        if declared_size is not None and int(declared_size) != len(raw):
            raise ProviderMediaError(
                f"Provider media size mismatch for {key}: expected {declared_size}, got {len(raw)}"
            )
        synthetic_path = _stable_external_path(provider, asset_id, str(fetched["filename"]))
        synthetic_blob = _git_blob_sha(raw)
        if synthetic_path in synthetic_bytes and synthetic_bytes[synthetic_path] != raw:
            raise ProviderMediaError(f"Conflicting provider media identity: {synthetic_path}")
        synthetic_bytes[synthetic_path] = raw
        synthetic_blobs[synthetic_path] = synthetic_blob
        v2_media.append({**common, "path": synthetic_path, "git_blob_sha": synthetic_blob})
        provider_summary[key] = {
            "source_type": "public_media_source",
            "provider": provider,
            "asset_id": asset_id,
            "delivery_file_id": delivery_file_id,
            "delivery_url": str(source["delivery"].get("delivery_url", "")),
            "filename": str(fetched["filename"]),
            "mime_type": str(fetched["mime_type"]),
            "sha256": str(fetched["sha256"]),
            "size_bytes": int(fetched["size_bytes"]),
            "stable_managed_path": synthetic_path,
        }

    transformed["schema_version"] = 2
    wordpress["media"] = v2_media
    return transformed, synthetic_bytes, synthetic_blobs, provider_summary


def _run_v3(argv: list[str], manifest: dict[str, Any], manifest_path: str, manifest_commit: str, original_raw: bytes) -> int:
    transformed, synthetic_bytes, synthetic_blobs, provider_summary = _transform_manifest_v3(manifest)
    transformed_raw = json.dumps(transformed, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    def patched_git_bytes(commit: str, path: str) -> bytes:
        if commit == manifest_commit and path == manifest_path:
            return transformed_raw
        if path in synthetic_bytes:
            return synthetic_bytes[path]
        return _ORIGINAL_GIT_BYTES(commit, path)

    def patched_git_blob_sha(commit: str, path: str) -> str:
        if path in synthetic_blobs:
            return synthetic_blobs[path]
        return _ORIGINAL_GIT_BLOB_SHA(commit, path)

    core.git_bytes = patched_git_bytes
    core.git_blob_sha = patched_git_blob_sha
    rc = core.main()

    response_path = pathlib.Path(_arg_value(argv, "--response"))
    if response_path.exists():
        try:
            response = json.loads(response_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            response = None
        if isinstance(response, dict) and response.get("ok") is True:
            result = response.get("result")
            if isinstance(result, dict):
                result["manifest_sha256"] = hashlib.sha256(original_raw).hexdigest()
                result["manifest_schema_version"] = 3
                media_summary = result.get("media")
                if isinstance(media_summary, list):
                    for item in media_summary:
                        if not isinstance(item, dict):
                            continue
                        key = str(item.get("key", ""))
                        summary = provider_summary.get(key)
                        if not summary:
                            continue
                        if summary.get("source_type") == "public_media_source":
                            item.pop("git_blob_sha", None)
                            item.update(summary)
                        else:
                            item["source_type"] = "repository_file"
                response_path.write_text(
                    json.dumps(response, ensure_ascii=False, separators=(",", ":")),
                    encoding="utf-8",
                )
    return rc


def main() -> int:
    manifest, manifest_path, manifest_commit, raw = _load_manifest(sys.argv)
    version = int(manifest.get("schema_version", 0))
    if version == 2:
        runpy.run_path(str(V5_PATH), run_name="__main__")
        return 0
    if version != 3:
        raise ProviderMediaError(f"Unsupported preparation manifest schema: {version}")
    return _run_v3(sys.argv, manifest, manifest_path, manifest_commit, raw)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:
        response_path: pathlib.Path | None = None
        try:
            response_path = pathlib.Path(_arg_value(sys.argv, "--response"))
        except Exception:
            pass
        if response_path is not None:
            request_id = ""
            try:
                request_id = str(_load_request(sys.argv).get("request_id", ""))
            except Exception:
                pass
            response_path.write_text(
                json.dumps(
                    {
                        "ok": False,
                        "schema_version": 1,
                        "request_id": request_id,
                        "error": {"code": "prepare_article_failed", "message": str(exc)},
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                encoding="utf-8",
            )
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
