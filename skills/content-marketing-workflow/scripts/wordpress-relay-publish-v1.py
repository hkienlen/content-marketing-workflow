#!/usr/bin/env python3
import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.request
from typing import Any, Dict

ALLOWED_OPERATIONS = {
    "publication_preflight": "publication_preflight",
    "publish_article": "article_publish",
    "published_article_read": "published_article_read",
}


def fail(response_path: pathlib.Path, code: str, message: str, status: int = 400) -> int:
    body = {
        "ok": False,
        "schema_version": 1,
        "error": {"code": code, "message": message},
        "relay_http_status": status,
    }
    response_path.write_text(json.dumps(body, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"{code}: {message}", file=sys.stderr)
    return 1


def load_json(path: pathlib.Path) -> Dict[str, Any]:
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def safe_repo_path(value: str) -> bool:
    if not value or value.startswith("/") or "\x00" in value:
        return False
    parts = value.replace("\\", "/").split("/")
    if any(part in ("", ".", "..") for part in parts):
        return False
    return re.fullmatch(r"[A-Za-z0-9._/@+,:=\-/]+", value.replace("\\", "/")) is not None


def allowed_prefix(path: str, prefixes: Any) -> bool:
    if not isinstance(prefixes, list) or not prefixes:
        return False
    normalized = path.rstrip("/")
    for raw in prefixes:
        if not isinstance(raw, str) or not safe_repo_path(raw):
            continue
        prefix = raw.rstrip("/")
        if normalized == prefix or normalized.startswith(prefix + "/"):
            return True
    return False


def git_file(commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{path}"])


def call_wordpress(endpoint: str, oidc_token: str, body: Dict[str, Any]) -> tuple[int, Dict[str, Any]]:
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {oidc_token}",
            "User-Agent": "seo-workflow-wordpress-publish-relay/1",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            http_status = response.status
            response_bytes = response.read()
    except urllib.error.HTTPError as exc:
        http_status = exc.code
        response_bytes = exc.read()
    parsed = json.loads(response_bytes.decode("utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("WordPress returned a non-object JSON response.")
    return http_status, parsed


def capture_candidate(
    request_data: Dict[str, Any],
    profile: Dict[str, Any],
    payload: Dict[str, Any],
    token: str,
    prepare_endpoint: str,
    response_path: pathlib.Path,
) -> int:
    if "authorization" in payload:
        return fail(
            response_path,
            "unexpected_publication_authorization",
            "Read-only publication capture must not carry publication authorization.",
        )

    post_id = payload.get("post_id")
    if not isinstance(post_id, int) or post_id <= 0:
        return fail(response_path, "invalid_capture_post_id", "publication_capture requires a positive post_id.")

    bridge_request = {
        "schema_version": 1,
        "request_id": request_data.get("request_id"),
        "connection_id": request_data.get("connection_id"),
        "operation": "article_read",
        "issued_at": request_data.get("issued_at"),
        "payload": {"id": post_id},
    }

    try:
        http_status, wordpress_response = call_wordpress(prepare_endpoint, token, bridge_request)
    except Exception as exc:
        return fail(
            response_path,
            "publication_capture_endpoint_failed",
            f"Unable to read the WordPress draft for publication capture: {exc}",
            502,
        )

    if not (200 <= http_status < 300) or wordpress_response.get("ok") is not True:
        wordpress_response["relay_capture"] = {"post_id": post_id}
        response_path.write_text(
            json.dumps(wordpress_response, ensure_ascii=False, separators=(",", ":")) + "\n"
        )
        return 1

    result = wordpress_response.get("result")
    if not isinstance(result, dict):
        return fail(response_path, "invalid_capture_readback", "WordPress article_read result is missing.", 502)
    if result.get("status") != "draft":
        return fail(
            response_path,
            "capture_post_not_draft",
            "Only a bridge-managed WordPress draft may be captured as a publication candidate.",
        )
    if result.get("id") != post_id:
        return fail(response_path, "capture_post_id_mismatch", "WordPress returned an unexpected post ID.")

    content = result.get("content")
    if not isinstance(content, str):
        return fail(response_path, "invalid_capture_content", "WordPress article_read did not return string content.")

    post_meta = result.get("post_meta")
    if not isinstance(post_meta, dict):
        return fail(response_path, "invalid_capture_meta", "WordPress article_read did not return post_meta.")

    raw_taxonomies = result.get("taxonomies")
    if not isinstance(raw_taxonomies, dict):
        return fail(response_path, "invalid_capture_taxonomies", "WordPress article_read did not return taxonomies.")

    taxonomies: Dict[str, Any] = {}
    for taxonomy, terms in raw_taxonomies.items():
        if not isinstance(taxonomy, str) or not isinstance(terms, list):
            return fail(response_path, "invalid_capture_taxonomy", "Captured taxonomy data is malformed.")
        slugs = []
        for term in terms:
            if not isinstance(term, dict) or not isinstance(term.get("slug"), str) or not term["slug"]:
                return fail(response_path, "invalid_capture_term", "Captured taxonomy term is missing a slug.")
            slugs.append(term["slug"])
        taxonomies[taxonomy] = sorted(slugs)

    content_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
    connection_id = request_data.get("connection_id")
    candidate = {
        "schema_version": 1,
        "candidate_id": f"{connection_id}:{post_id}:{content_sha256[:12]}",
        "connection_id": connection_id,
        "post_id": post_id,
        "validation": {
            "status": "captured_after_human_validation",
            "authorization_included": False,
        },
        "expected": {
            "post_type": result.get("post_type"),
            "slug": result.get("slug"),
            "title": result.get("title"),
            "excerpt": result.get("excerpt", ""),
            "content_sha256": content_sha256,
            "featured_media_id": result.get("featured_media_id", 0),
            "manifest_path": result.get("manifest_path"),
            "source_commit": result.get("source_commit"),
            "source_article_path": result.get("source_article_path"),
            "source_article_sha256": result.get("source_article_sha256"),
            "post_meta": post_meta,
            "taxonomies": taxonomies,
        },
    }

    out = {
        "ok": True,
        "schema_version": 1,
        "request_id": request_data.get("request_id"),
        "operation": "publication_capture",
        "site_url": wordpress_response.get("site_url"),
        "result": {
            "candidate": candidate,
            "captured_status": "draft",
            "content_sha256": content_sha256,
        },
        "oidc": wordpress_response.get("oidc", {}),
    }
    response_path.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--oidc-token-file", required=True)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--prepare-endpoint", required=True)
    parser.add_argument("--response", required=True)
    args = parser.parse_args()

    request_path = pathlib.Path(args.request)
    profile_path = pathlib.Path(args.profile)
    response_path = pathlib.Path(args.response)

    try:
        request_data = load_json(request_path)
        profile = load_json(profile_path)
    except Exception as exc:
        return fail(response_path, "invalid_relay_input", str(exc))

    if request_data.get("schema_version") != 1:
        return fail(response_path, "unsupported_schema", "Publication relay request schema_version must be 1.")

    operation = request_data.get("operation")
    if operation != "publication_capture" and operation not in ALLOWED_OPERATIONS:
        return fail(response_path, "unsupported_publication_operation", "Unsupported publication parent relay operation.")

    connection_id = request_data.get("connection_id")
    if connection_id != profile.get("connection_id"):
        return fail(response_path, "publication_connection_mismatch", "Request connection_id does not match the connection profile.")

    payload = request_data.get("payload")
    if not isinstance(payload, dict):
        return fail(response_path, "invalid_publication_payload", "Publication relay payload must be an object.")

    token = pathlib.Path(args.oidc_token_file).read_text().strip()
    if not token:
        return fail(response_path, "missing_oidc_token", "OIDC token file is empty.")

    if operation == "publication_capture":
        return capture_candidate(
            request_data,
            profile,
            payload,
            token,
            args.prepare_endpoint,
            response_path,
        )

    candidate_path = payload.get("candidate_path")
    candidate_commit = payload.get("candidate_commit")
    if not isinstance(candidate_path, str) or not safe_repo_path(candidate_path):
        return fail(response_path, "invalid_candidate_path", "A safe repository candidate_path is required.")
    if not isinstance(candidate_commit, str) or re.fullmatch(r"[a-f0-9]{40}", candidate_commit) is None:
        return fail(response_path, "invalid_candidate_commit", "candidate_commit must be a full lowercase Git commit SHA.")

    prefixes = profile.get("relay", {}).get("publish_candidate_prefixes")
    if not allowed_prefix(candidate_path, prefixes):
        return fail(response_path, "candidate_path_not_allowed", "candidate_path is outside the configured publication candidate prefixes.")

    try:
        candidate_bytes = git_file(candidate_commit, candidate_path)
        candidate = json.loads(candidate_bytes.decode("utf-8"))
    except subprocess.CalledProcessError:
        return fail(response_path, "candidate_not_found", "Publication candidate was not found at the requested Git commit.")
    except Exception as exc:
        return fail(response_path, "invalid_candidate_json", f"Publication candidate is not valid UTF-8 JSON: {exc}")

    if not isinstance(candidate, dict) or candidate.get("schema_version") != 1:
        return fail(response_path, "invalid_candidate_schema", "Publication candidate schema_version must be 1.")

    forbidden = {"authorization", "publish_authorized", "authorized", "publish_now"}
    if forbidden.intersection(candidate.keys()):
        return fail(response_path, "candidate_contains_authorization", "Publication candidate must not persist runtime publication authorization.")

    candidate_id = candidate.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id:
        return fail(response_path, "invalid_candidate_id", "Publication candidate must contain a non-empty candidate_id.")
    if candidate.get("connection_id") != connection_id:
        return fail(response_path, "candidate_connection_mismatch", "Publication candidate connection_id does not match the request.")

    post_id = candidate.get("post_id")
    expected = candidate.get("expected")
    if not isinstance(post_id, int) or post_id <= 0 or not isinstance(expected, dict):
        return fail(response_path, "invalid_candidate_snapshot", "Publication candidate requires a positive post_id and expected snapshot.")

    if operation == "publish_article":
        authorization = payload.get("authorization")
        if not isinstance(authorization, dict):
            return fail(response_path, "publication_authorization_required", "Explicit runtime publication authorization is required.")
        if authorization.get("decision") != "publish_now":
            return fail(response_path, "publication_authorization_required", "Runtime authorization decision must be publish_now.")
        if authorization.get("candidate_id") != candidate_id:
            return fail(response_path, "publication_authorization_candidate_mismatch", "Runtime authorization is not bound to this publication candidate.")
    elif "authorization" in payload:
        return fail(response_path, "unexpected_publication_authorization", "Read-only publication operations must not carry publication authorization.")

    bridge_request = {
        "schema_version": 1,
        "request_id": request_data.get("request_id"),
        "connection_id": connection_id,
        "operation": ALLOWED_OPERATIONS[operation],
        "issued_at": request_data.get("issued_at"),
        "payload": {
            "post_id": post_id,
            "expected": expected,
        },
    }

    try:
        http_status, wordpress_response = call_wordpress(args.endpoint, token, bridge_request)
    except Exception as exc:
        return fail(response_path, "publication_endpoint_failed", f"Unable to call WordPress publication endpoint: {exc}", 502)

    wordpress_response["relay_candidate"] = {
        "candidate_id": candidate_id,
        "candidate_path": candidate_path,
        "candidate_commit": candidate_commit,
        "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
    }
    response_path.write_text(json.dumps(wordpress_response, ensure_ascii=False, separators=(",", ":")) + "\n")

    ok = 200 <= http_status < 300 and wordpress_response.get("ok") is True
    if not ok:
        print(f"WordPress publication endpoint returned HTTP {http_status}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
