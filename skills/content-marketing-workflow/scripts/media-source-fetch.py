#!/usr/bin/env python3
"""Fetch and verify one public media source without provider credentials.

The initial implemented provider is Google Drive public-link delivery. The
provider dispatch is intentionally explicit so Dropbox can be added later
without changing the WordPress preparation contract.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

DEFAULT_MAX_BYTES = 8 * 1024 * 1024
KNOWN_PROVIDERS = {"google_drive", "dropbox"}
IMPLEMENTED_PROVIDERS = {"google_drive"}
_ALLOWED_GOOGLE_HOSTS = {"drive.google.com", "drive.usercontent.google.com"}
_FILE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{10,200}$")
_RESOURCE_KEY_RE = re.compile(r"^[A-Za-z0-9_-]{1,300}$")
_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


class MediaSourceError(RuntimeError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sniff_image_mime(data: bytes) -> str:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    raise MediaSourceError("Downloaded bytes are not a supported PNG/JPEG/WebP/GIF image")


def _validate_file_id(value: str) -> str:
    value = value.strip()
    if not _FILE_ID_RE.fullmatch(value):
        raise MediaSourceError("Invalid Google Drive file_id")
    return value


def _validate_resource_key(value: str) -> str:
    value = value.strip()
    if not _RESOURCE_KEY_RE.fullmatch(value):
        raise MediaSourceError("Invalid Google Drive resource_key")
    return value


def google_drive_identity(source: dict[str, Any]) -> tuple[str, str]:
    file_id = str(source.get("file_id", "")).strip()
    resource_key = str(source.get("resource_key", "")).strip()
    delivery_url = str(source.get("delivery_url", "")).strip()

    if delivery_url:
        parsed = urllib.parse.urlparse(delivery_url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or host not in _ALLOWED_GOOGLE_HOSTS:
            raise MediaSourceError("Google Drive delivery_url must use HTTPS on an allowed Google Drive host")
        query = urllib.parse.parse_qs(parsed.query)
        url_file_id = ""
        match = re.search(r"/file/d/([A-Za-z0-9_-]+)", parsed.path)
        if match:
            url_file_id = match.group(1)
        elif query.get("id"):
            url_file_id = query["id"][0]
        if url_file_id:
            url_file_id = _validate_file_id(url_file_id)
            if file_id and file_id != url_file_id:
                raise MediaSourceError("Google Drive file_id does not match delivery_url")
            file_id = url_file_id
        url_resource_key = (query.get("resourcekey") or query.get("resource_key") or [""])[0]
        if url_resource_key:
            url_resource_key = _validate_resource_key(url_resource_key)
            if resource_key and resource_key != url_resource_key:
                raise MediaSourceError("Google Drive resource_key does not match delivery_url")
            resource_key = url_resource_key

    file_id = _validate_file_id(file_id)
    if resource_key:
        resource_key = _validate_resource_key(resource_key)
    return file_id, resource_key


def google_drive_download_urls(source: dict[str, Any]) -> list[str]:
    file_id, resource_key = google_drive_identity(source)
    common = {"id": file_id, "export": "download", "confirm": "t"}
    if resource_key:
        common["resourcekey"] = resource_key
    return [
        "https://drive.usercontent.google.com/download?" + urllib.parse.urlencode(common),
        "https://drive.google.com/uc?" + urllib.parse.urlencode(common),
    ]


def _default_open(url: str, timeout: int):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "seo-workflow-media-source/0.1",
            "Accept": "image/avif,image/webp,image/png,image/jpeg,image/gif,*/*;q=0.1",
        },
    )
    return urllib.request.urlopen(request, timeout=timeout)


def _read_response(response: Any, max_bytes: int) -> tuple[bytes, str]:
    content_type = str(response.headers.get("Content-Type", "")).split(";", 1)[0].strip().lower()
    raw_length = str(response.headers.get("Content-Length", "")).strip()
    if raw_length.isdigit() and int(raw_length) > max_bytes:
        raise MediaSourceError("Remote media exceeds configured maximum size")
    chunks: list[bytes] = []
    size = 0
    while True:
        chunk = response.read(min(64 * 1024, max_bytes + 1 - size))
        if not chunk:
            break
        chunks.append(chunk)
        size += len(chunk)
        if size > max_bytes:
            raise MediaSourceError("Remote media exceeds configured maximum size")
    data = b"".join(chunks)
    if not data:
        raise MediaSourceError("Remote media response is empty")
    prefix = data[:512].lstrip().lower()
    if content_type in {"text/html", "application/xhtml+xml"} or prefix.startswith(b"<!doctype html") or prefix.startswith(b"<html"):
        raise MediaSourceError("Remote media resolved to HTML instead of image bytes")
    return data, content_type


def fetch_google_drive(
    source: dict[str, Any],
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
    timeout: int = 30,
    opener: Callable[[str, int], Any] = _default_open,
) -> tuple[bytes, str]:
    errors: list[str] = []
    for url in google_drive_download_urls(source):
        try:
            with opener(url, timeout) as response:
                data, _declared = _read_response(response, max_bytes)
            return data, url
        except (MediaSourceError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            errors.append(str(exc))
    raise MediaSourceError("Google Drive public download failed: " + " | ".join(errors))


def fetch_and_verify(
    source: dict[str, Any],
    *,
    opener: Callable[[str, int], Any] = _default_open,
) -> dict[str, Any]:
    if not isinstance(source, dict):
        raise MediaSourceError("Media source descriptor must be an object")
    provider = str(source.get("provider", "")).strip()
    if provider not in KNOWN_PROVIDERS:
        raise MediaSourceError(f"Unsupported media provider: {provider or '<empty>'}")
    if provider not in IMPLEMENTED_PROVIDERS:
        raise MediaSourceError(f"Media provider adapter is not implemented yet: {provider}")

    expected_sha = str(source.get("sha256", "")).strip().lower()
    if not _SHA256_RE.fullmatch(expected_sha):
        raise MediaSourceError("Media source sha256 must be a lowercase 64-character digest")
    expected_mime = str(source.get("mime_type", "")).strip().lower()
    filename = str(source.get("filename", "")).strip()
    if not filename or pathlib.PurePosixPath(filename).name != filename:
        raise MediaSourceError("Media source filename must be a basename")

    max_bytes = int(source.get("max_bytes", DEFAULT_MAX_BYTES))
    if max_bytes <= 0 or max_bytes > DEFAULT_MAX_BYTES:
        raise MediaSourceError(f"Media source max_bytes must be between 1 and {DEFAULT_MAX_BYTES}")

    if provider == "google_drive":
        data, fetched_url = fetch_google_drive(source, max_bytes=max_bytes, opener=opener)
    else:  # pragma: no cover - guarded above
        raise MediaSourceError(f"Unhandled media provider: {provider}")

    actual_mime = sniff_image_mime(data)
    if expected_mime and expected_mime != actual_mime:
        raise MediaSourceError(f"Media MIME mismatch: expected {expected_mime}, got {actual_mime}")
    actual_sha = sha256_bytes(data)
    if actual_sha != expected_sha:
        raise MediaSourceError(f"Media SHA-256 mismatch: expected {expected_sha}, got {actual_sha}")

    file_id = ""
    resource_key = ""
    if provider == "google_drive":
        file_id, resource_key = google_drive_identity(source)

    return {
        "bytes": data,
        "provider": provider,
        "file_id": file_id,
        "resource_key": resource_key,
        "filename": filename,
        "mime_type": actual_mime,
        "sha256": actual_sha,
        "size_bytes": len(data),
        "fetched_url": fetched_url,
    }


def load_descriptor(path: str) -> dict[str, Any]:
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise MediaSourceError("Descriptor JSON must be an object")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--descriptor", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--summary")
    args = parser.parse_args()
    try:
        result = fetch_and_verify(load_descriptor(args.descriptor))
        output = pathlib.Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        temp = output.with_name(output.name + ".tmp")
        temp.write_bytes(result["bytes"])
        temp.replace(output)
        summary = {key: value for key, value in result.items() if key not in {"bytes", "fetched_url"}}
        if args.summary:
            pathlib.Path(args.summary).write_text(json.dumps(summary, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(summary, sort_keys=True))
        return 0
    except Exception as exc:
        print(str(exc), file=__import__("sys").stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
