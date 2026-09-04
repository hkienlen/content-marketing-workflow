#!/usr/bin/env python3
"""Execute one repository-backed WordPress article preparation request (manifest v2).

The parent relay request identifies a manifest path and the immutable commit that
contains that manifest. The manifest separately pins the immutable source commit
for the editorial article and media. This avoids impossible Git self-reference:
a manifest never needs to contain the SHA of the commit that contains itself.

Manifest v2 uses Git blob SHAs as repository-native identity checks. The trusted
runner computes SHA-256 from the exact bytes it reads before sending media/article
identity to WordPress.

Rendering rule: render the public Markdown first, then inject bridge-controlled
media HTML into the rendered HTML. This prevents GitHub Markdown from rewriting
WordPress image URLs through its camo proxy or breaking headings adjacent to raw
HTML blocks.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import html
import json
import mimetypes
import os
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.request
from typing import Any


class PrepareError(RuntimeError):
    pass


def load_json(path: str) -> dict[str, Any]:
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise PrepareError(f"JSON object required: {path}")
    return data


def safe_repo_path(value: str) -> str:
    value = value.strip().replace("\\", "/")
    if not value or value.startswith("/") or "\x00" in value:
        raise PrepareError("Invalid repository path")
    parts = value.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise PrepareError(f"Unsafe repository path: {value}")
    if not re.fullmatch(r"[A-Za-z0-9._/@+,:=\-]+(?:/[A-Za-z0-9._/@+,:=\-]+)*", value):
        raise PrepareError(f"Unsupported repository path characters: {value}")
    return value


def allowed_prefix(path: str, prefixes: list[str]) -> bool:
    for prefix in prefixes:
        clean = safe_repo_path(prefix).rstrip("/")
        if path == clean or path.startswith(clean + "/"):
            return True
    return False


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], text=True, capture_output=True, check=check)


def default_branch_ref() -> str:
    default_ref = os.environ.get("GITHUB_REF_NAME", "main")
    remote_ref = f"origin/{default_ref}"
    if git("show-ref", "--verify", f"refs/remotes/{remote_ref}", check=False).returncode == 0:
        return remote_ref
    if git("show-ref", "--verify", "refs/remotes/origin/main", check=False).returncode == 0:
        return "origin/main"
    return "HEAD"


def ensure_commit(commit: str, label: str) -> None:
    if not re.fullmatch(r"[a-f0-9]{40}", commit):
        raise PrepareError(f"{label} must be a full lowercase 40-character commit SHA")
    if git("cat-file", "-e", f"{commit}^{{commit}}", check=False).returncode != 0:
        raise PrepareError(f"{label} does not exist in the checked-out repository")
    if git("merge-base", "--is-ancestor", commit, default_branch_ref(), check=False).returncode != 0:
        raise PrepareError(f"{label} is not an ancestor of the checked-out default branch")


def git_bytes(commit: str, path: str) -> bytes:
    proc = subprocess.run(["git", "show", f"{commit}:{path}"], capture_output=True, check=False)
    if proc.returncode != 0:
        raise PrepareError(f"Repository file not found at commit {commit[:12]}: {path}")
    return proc.stdout


def git_blob_sha(commit: str, path: str) -> str:
    proc = git("rev-parse", f"{commit}:{path}", check=False)
    value = proc.stdout.strip().lower() if proc.returncode == 0 else ""
    if not re.fullmatch(r"[a-f0-9]{40}", value):
        raise PrepareError(f"Unable to resolve Git blob SHA for {path} at {commit[:12]}")
    return value


def verify_git_blob(commit: str, path: str, expected: str) -> None:
    expected = expected.lower()
    if not re.fullmatch(r"[a-f0-9]{40}", expected):
        raise PrepareError(f"Invalid expected Git blob SHA for {path}")
    actual = git_blob_sha(commit, path)
    if not hmac.compare_digest(actual, expected):
        raise PrepareError(f"Git blob SHA mismatch for {path}: expected {expected}, got {actual}")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def strip_front_matter(markdown: str) -> str:
    if not markdown.startswith("---"):
        return markdown
    lines = markdown.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return markdown
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return "".join(lines[idx + 1 :]).lstrip("\r\n")
    raise PrepareError("Article starts with YAML front matter but has no closing delimiter")


def strip_first_h1(markdown: str) -> str:
    lines = markdown.splitlines(keepends=True)
    for idx, line in enumerate(lines):
        if line.strip() == "":
            continue
        if re.match(r"^#\s+\S", line):
            del lines[idx]
            if idx < len(lines) and lines[idx].strip() == "":
                del lines[idx]
        break
    return "".join(lines)


def stop_before_marker(markdown: str, marker: str) -> str:
    if not marker:
        return markdown
    pos = markdown.find(marker)
    if pos < 0:
        raise PrepareError("Configured public-content stop marker was not found in the source article")
    comment_start = markdown.rfind("<!--", 0, pos + 1)
    if comment_start >= 0 and markdown.find("-->", comment_start, pos + len(marker) + 4) >= 0:
        pos = comment_start
    return markdown[:pos].rstrip() + "\n"


def figure_html(media: dict[str, Any]) -> str:
    url = html.escape(str(media["url"]), quote=True)
    alt = html.escape(str(media.get("alt", "")), quote=True)
    caption = html.escape(str(media.get("caption", "")))
    title = html.escape(str(media.get("title", "")), quote=True)
    title_attr = f' title="{title}"' if title else ""
    out = f'<figure class="wp-block-image"><img src="{url}" alt="{alt}"{title_attr}>'
    if caption:
        out += f"<figcaption>{caption}</figcaption>"
    out += "</figure>"
    return out


_RENDERED_HEADING_RE = re.compile(r"<h([2-6])\b[^>]*>(.*?)</h\1>", re.IGNORECASE | re.DOTALL)


def rendered_heading_matches(rendered_html: str) -> list[tuple[re.Match[str], int, str]]:
    matches: list[tuple[re.Match[str], int, str]] = []
    for match in _RENDERED_HEADING_RE.finditer(rendered_html):
        plain = re.sub(r"<[^>]+>", "", match.group(2))
        plain = html.unescape(plain).strip()
        matches.append((match, int(match.group(1)), plain))
    return matches


def inject_one_media_html(rendered_html: str, media: dict[str, Any], result: dict[str, Any]) -> str:
    placement = media.get("placement")
    if not placement:
        return rendered_html
    if not isinstance(placement, dict):
        raise PrepareError(f"Invalid media placement for key: {media.get('key', '')}")

    rendered = {**media, **result}
    block = "\n" + figure_html(rendered) + "\n"

    if placement.get("at_end") is True:
        return rendered_html.rstrip() + block + "\n"

    headings = rendered_heading_matches(rendered_html)

    if "before_heading" in placement:
        target = str(placement["before_heading"]).strip()
        for match, _level, text in headings:
            if text == target:
                return rendered_html[: match.start()] + block + rendered_html[match.start() :]
        raise PrepareError(f"Media before_heading anchor was not found after Markdown rendering: {target}")

    if "after_heading" in placement:
        target = str(placement["after_heading"]).strip()
        for match, _level, text in headings:
            if text == target:
                return rendered_html[: match.end()] + block + rendered_html[match.end() :]
        raise PrepareError(f"Media after_heading anchor was not found after Markdown rendering: {target}")

    if "after_section" in placement:
        target = str(placement["after_section"]).strip()
        for idx, (match, level, text) in enumerate(headings):
            if text != target:
                continue
            insert_at = len(rendered_html)
            for next_match, next_level, _next_text in headings[idx + 1 :]:
                if next_level <= level:
                    insert_at = next_match.start()
                    break
            return rendered_html[:insert_at] + block + rendered_html[insert_at:]
        raise PrepareError(f"Media after_section anchor was not found after Markdown rendering: {target}")

    raise PrepareError(f"Unsupported media placement for key: {media.get('key', '')}")


def inject_inline_media_html(
    rendered_html: str,
    manifest_media: list[dict[str, Any]],
    media_results: dict[str, dict[str, Any]],
) -> str:
    out = rendered_html
    for media in manifest_media:
        key = str(media.get("key", ""))
        if not media.get("placement"):
            continue
        if key not in media_results:
            raise PrepareError(f"Missing uploaded media result for placement key: {key}")
        out = inject_one_media_html(out, media, media_results[key])
    if "camo.githubusercontent.com" in out:
        raise PrepareError("Rendered WordPress content unexpectedly contains a GitHub camo media URL")
    return out


def github_markdown(markdown: str, github_token: str) -> str:
    body = json.dumps(
        {"text": markdown, "mode": "gfm", "context": os.environ.get("GITHUB_REPOSITORY", "")},
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.github.com/markdown",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {github_token}",
            "Accept": "text/html",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "seo-workflow-bridge-relay",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise PrepareError(f"GitHub Markdown rendering failed: HTTP {exc.code}: {detail[:500]}") from exc


def wp_call(endpoint: str, token: str, envelope_data: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(envelope_data, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode("utf-8")
            status = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        status = exc.code
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PrepareError(f"WordPress returned non-JSON HTTP {status}") from exc
    if status < 200 or status >= 300 or not isinstance(parsed, dict) or parsed.get("ok") is not True:
        raise PrepareError(
            f"WordPress relay call failed HTTP {status}: {json.dumps(parsed, ensure_ascii=False)[:1000]}"
        )
    return parsed


def envelope(parent: dict[str, Any], operation: str, suffix: str, payload: dict[str, Any]) -> dict[str, Any]:
    parent_id = str(parent["request_id"])
    child_hash = hashlib.sha256(f"{parent_id}:{operation}:{suffix}".encode("utf-8")).hexdigest()[:16]
    readable_suffix = re.sub(r"[^A-Za-z0-9._:-]+", "-", suffix)[:24]
    max_parent = 128 - len(child_hash) - len(readable_suffix) - 2
    child_id = f"{parent_id[:max_parent]}.{readable_suffix}.{child_hash}"
    return {
        "schema_version": 1,
        "request_id": child_id,
        "connection_id": parent["connection_id"],
        "operation": operation,
        "issued_at": parent["issued_at"],
        "payload": payload,
    }


def resolve_repository_content(
    content_cfg: dict[str, Any],
    source_commit: str,
    prefixes: list[str],
    article_body_html: str,
    media_results: dict[str, dict[str, Any]],
) -> str:
    path = safe_repo_path(str(content_cfg.get("path", "")))
    if not allowed_prefix(path, prefixes):
        raise PrepareError(f"Repository content path is outside allowed prefixes: {path}")
    expected_blob = str(content_cfg.get("git_blob_sha", "")).lower()
    verify_git_blob(source_commit, path, expected_blob)
    text = git_bytes(source_commit, path).decode("utf-8")
    text = text.replace("{{ARTICLE_BODY_HTML}}", article_body_html)
    for key, result in media_results.items():
        text = text.replace(f"{{{{MEDIA_URL:{key}}}}}", str(result["url"]))
        text = text.replace(f"{{{{MEDIA_ID:{key}}}}}", str(result["id"]))
    unresolved = re.findall(r"\{\{(?:ARTICLE_BODY_HTML|MEDIA_(?:URL|ID):[^}]+)\}\}", text)
    if unresolved:
        raise PrepareError(f"Unresolved repository content tokens remain: {', '.join(sorted(set(unresolved)))}")
    return text


def split_post_meta(post_meta: Any) -> tuple[dict[str, Any], dict[str, dict[str, str]]]:
    if post_meta is None:
        return {}, {}
    if not isinstance(post_meta, dict):
        raise PrepareError("wordpress.post_meta must be an object")
    scalar: dict[str, Any] = {}
    dynamic: dict[str, dict[str, str]] = {}
    for key, value in post_meta.items():
        if not isinstance(key, str) or not key:
            raise PrepareError("wordpress.post_meta keys must be non-empty strings")
        if isinstance(value, dict):
            if set(value) != {"term_id_from_taxonomy"} or not isinstance(value["term_id_from_taxonomy"], dict):
                raise PrepareError(f"Unsupported dynamic post_meta resolver for key: {key}")
            selector = value["term_id_from_taxonomy"]
            if set(selector) != {"taxonomy", "slug"}:
                raise PrepareError(f"term_id_from_taxonomy requires exactly taxonomy and slug for key: {key}")
            taxonomy = str(selector["taxonomy"])
            slug = str(selector["slug"])
            if not taxonomy or not slug:
                raise PrepareError(f"term_id_from_taxonomy taxonomy/slug cannot be empty for key: {key}")
            dynamic[key] = {"taxonomy": taxonomy, "slug": slug}
        elif value is None or isinstance(value, (str, int, float, bool)):
            scalar[key] = value
        else:
            raise PrepareError(f"Unsupported post_meta value for key: {key}")
    return scalar, dynamic


def resolve_dynamic_post_meta(
    scalar: dict[str, Any],
    dynamic: dict[str, dict[str, str]],
    read_result: dict[str, Any],
) -> dict[str, Any]:
    resolved = dict(scalar)
    taxonomies = read_result.get("taxonomies")
    if dynamic and not isinstance(taxonomies, dict):
        raise PrepareError("article_read did not return taxonomies required by dynamic post_meta")
    for key, selector in dynamic.items():
        terms = taxonomies.get(selector["taxonomy"]) if isinstance(taxonomies, dict) else None
        if not isinstance(terms, list):
            raise PrepareError(f"Taxonomy missing from article_read: {selector['taxonomy']}")
        matches = [
            term for term in terms
            if isinstance(term, dict) and str(term.get("slug", "")) == selector["slug"]
        ]
        if len(matches) != 1 or not matches[0].get("id"):
            raise PrepareError(
                f"Unable to resolve unique term ID for {key}: {selector['taxonomy']}/{selector['slug']}"
            )
        resolved[key] = int(matches[0]["id"])
    return resolved


def verify_readback(expected: dict[str, Any], read: dict[str, Any], expected_content: str) -> dict[str, bool]:
    result = read.get("result")
    if not isinstance(result, dict):
        raise PrepareError("article_read result is missing")
    actual_content = str(result.get("content", ""))
    checks: dict[str, bool] = {
        "status_draft": result.get("status") == "draft",
        "slug": result.get("slug") == expected["slug"],
        "title": result.get("title") == expected["title"],
        "source_commit": result.get("source_commit") == expected["source_commit"],
        "source_article_path": result.get("source_article_path") == expected["source_article_path"],
        "source_article_sha256": result.get("source_article_sha256") == expected["source_article_sha256"],
        "content_sha256": hashlib.sha256(actual_content.encode("utf-8")).hexdigest()
        == hashlib.sha256(expected_content.encode("utf-8")).hexdigest(),
        "content_no_github_camo": "camo.githubusercontent.com" not in actual_content,
        "content_no_literal_h2_markdown": "\n## " not in actual_content,
    }
    if expected.get("featured_media_id", 0):
        checks["featured_media_id"] = int(result.get("featured_media_id", 0)) == int(expected["featured_media_id"])

    actual_meta = result.get("post_meta") if isinstance(result.get("post_meta"), dict) else {}
    expected_meta = expected.get("post_meta")
    if isinstance(expected_meta, dict):
        for key, value in expected_meta.items():
            checks[f"post_meta:{key}"] = str(actual_meta.get(key, "")) == ("" if value is None else str(value))

    actual_taxonomies = result.get("taxonomies") if isinstance(result.get("taxonomies"), dict) else {}
    expected_taxonomies = expected.get("taxonomies")
    if isinstance(expected_taxonomies, list):
        for group in expected_taxonomies:
            if not isinstance(group, dict):
                continue
            taxonomy = str(group.get("taxonomy", ""))
            terms = group.get("terms")
            expected_slugs = sorted(
                str(term.get("slug", "")) for term in terms if isinstance(term, dict)
            ) if isinstance(terms, list) else []
            actual_terms = actual_taxonomies.get(taxonomy)
            actual_slugs = sorted(
                str(term.get("slug", "")) for term in actual_terms if isinstance(term, dict)
            ) if isinstance(actual_terms, list) else []
            checks[f"taxonomy:{taxonomy}"] = actual_slugs == expected_slugs

    if not all(checks.values()):
        raise PrepareError(f"Prepared draft readback verification failed: {json.dumps(checks, sort_keys=True)}")
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--oidc-token-file", required=True)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--response", required=True)
    parser.add_argument("--github-token", required=True)
    args = parser.parse_args()

    response_path = pathlib.Path(args.response)
    parent = load_json(args.request)
    profile = load_json(args.profile)
    token = pathlib.Path(args.oidc_token_file).read_text().strip()

    try:
        if parent.get("operation") != "prepare_article":
            raise PrepareError("This helper accepts only prepare_article parent operations")
        payload = parent.get("payload")
        if not isinstance(payload, dict):
            raise PrepareError("prepare_article payload must be an object")

        manifest_path = safe_repo_path(str(payload.get("manifest_path", "")))
        manifest_commit = str(payload.get("manifest_commit", "")).lower()
        ensure_commit(manifest_commit, "manifest_commit")

        relay = profile.get("relay") if isinstance(profile.get("relay"), dict) else {}
        manifest_prefixes = relay.get("prepare_manifest_prefixes", ["wordpress/prepare/manifests"])
        asset_prefixes = relay.get("prepare_asset_prefixes", ["assets"])
        content_prefixes = relay.get("prepare_content_prefixes", ["articles", "wordpress"])
        groups = [manifest_prefixes, asset_prefixes, content_prefixes]
        if not all(isinstance(v, list) and all(isinstance(x, str) for x in v) for v in groups):
            raise PrepareError("Relay preparation prefixes in connection profile are invalid")
        if not allowed_prefix(manifest_path, manifest_prefixes):
            raise PrepareError("Preparation manifest path is outside allowed prefixes")

        manifest_raw = git_bytes(manifest_commit, manifest_path)
        manifest = json.loads(manifest_raw.decode("utf-8"))
        if not isinstance(manifest, dict) or int(manifest.get("schema_version", 0)) != 2:
            raise PrepareError("Unsupported preparation manifest schema; manifest v2 is required")
        if manifest.get("connection_id") != parent.get("connection_id"):
            raise PrepareError("Preparation manifest connection_id does not match relay request")

        source = manifest.get("source")
        wordpress = manifest.get("wordpress")
        if not isinstance(source, dict) or not isinstance(wordpress, dict):
            raise PrepareError("Preparation manifest requires source and wordpress objects")

        source_commit = str(source.get("article_commit", "")).lower()
        ensure_commit(source_commit, "source.article_commit")
        article_path = safe_repo_path(str(source.get("article_path", "")))
        if not allowed_prefix(article_path, content_prefixes):
            raise PrepareError("Source article path is outside allowed content prefixes")
        verify_git_blob(source_commit, article_path, str(source.get("article_git_blob_sha", "")))
        article_raw = git_bytes(source_commit, article_path)
        article_sha = sha256(article_raw)

        media_cfg = wordpress.get("media", [])
        if not isinstance(media_cfg, list):
            raise PrepareError("wordpress.media must be an array")
        media_results: dict[str, dict[str, Any]] = {}
        media_summary: list[dict[str, Any]] = []
        for index, media in enumerate(media_cfg):
            if not isinstance(media, dict):
                raise PrepareError("Each media entry must be an object")
            key = str(media.get("key", ""))
            if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,63}", key):
                raise PrepareError(f"Invalid media key: {key}")
            if key in media_results:
                raise PrepareError(f"Duplicate media key: {key}")
            path = safe_repo_path(str(media.get("path", "")))
            if not allowed_prefix(path, asset_prefixes):
                raise PrepareError(f"Media path is outside allowed prefixes: {path}")
            verify_git_blob(source_commit, path, str(media.get("git_blob_sha", "")))
            raw = git_bytes(source_commit, path)
            digest = sha256(raw)
            mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
            media_payload = {
                "manifest_path": manifest_path,
                "repository_path": path,
                "asset_key": key,
                "sha256": digest,
                "filename": pathlib.PurePosixPath(path).name,
                "mime_type": mime,
                "content_base64": base64.b64encode(raw).decode("ascii"),
                "title": str(media.get("title", "")),
                "alt": str(media.get("alt", "")),
                "caption": str(media.get("caption", "")),
            }
            media_response = wp_call(
                args.endpoint,
                token,
                envelope(parent, "media_upsert", f"media.{index + 1}", media_payload),
            )
            result = media_response.get("result")
            if not isinstance(result, dict) or not result.get("id") or not result.get("url"):
                raise PrepareError(f"media_upsert returned an invalid result for key: {key}")
            merged = {
                "id": int(result["id"]),
                "url": str(result["url"]),
                "reused": bool(result.get("reused")),
                "sha256": digest,
                "git_blob_sha": str(media.get("git_blob_sha", "")).lower(),
                "alt": str(media.get("alt", "")),
                "title": str(media.get("title", "")),
                "caption": str(media.get("caption", "")),
            }
            media_results[key] = merged
            media_summary.append({"key": key, "path": path, **merged})

        content_cfg = wordpress.get("content")
        if not isinstance(content_cfg, dict):
            raise PrepareError("wordpress.content must be an object")
        markdown = article_raw.decode("utf-8")
        if content_cfg.get("strip_front_matter", True):
            markdown = strip_front_matter(markdown)
        if content_cfg.get("strip_first_h1", True):
            markdown = strip_first_h1(markdown)
        marker = str(content_cfg.get("stop_before_marker", ""))
        if marker:
            markdown = stop_before_marker(markdown, marker)

        # Render clean editorial Markdown first. Only after GitHub has finished
        # rendering/sanitizing it do we add trusted media HTML with WordPress URLs.
        article_body_html = github_markdown(markdown, args.github_token)
        article_body_html = inject_inline_media_html(article_body_html, media_cfg, media_results)

        mode = str(content_cfg.get("mode", "github_markdown"))
        if mode == "github_markdown":
            post_content = article_body_html
        elif mode == "repository_file":
            post_content = resolve_repository_content(
                content_cfg, source_commit, content_prefixes, article_body_html, media_results
            )
        else:
            raise PrepareError(f"Unsupported content mode: {mode}")

        featured_key = str(wordpress.get("featured_media_key", ""))
        featured_media_id = 0
        if featured_key:
            if featured_key not in media_results:
                raise PrepareError("featured_media_key is not present in wordpress.media")
            featured_media_id = int(media_results[featured_key]["id"])

        scalar_meta, dynamic_meta = split_post_meta(wordpress.get("post_meta", {}))
        base_payload = {
            "manifest_path": manifest_path,
            "source_commit": source_commit,
            "source_article_path": article_path,
            "source_article_sha256": article_sha,
            "post_type": str(wordpress.get("post_type", "post")),
            "title": str(wordpress.get("title", "")),
            "slug": str(wordpress.get("slug", "")),
            "content": post_content,
            "excerpt": str(wordpress.get("excerpt", "")),
            "author_login": str(wordpress.get("author_login", "")),
            "taxonomies": wordpress.get("taxonomies", []),
            "post_meta": scalar_meta,
            "featured_media_id": featured_media_id,
        }

        prepared = wp_call(args.endpoint, token, envelope(parent, "article_prepare", "article.initial", base_payload))
        prepared_result = prepared.get("result")
        if not isinstance(prepared_result, dict) or not prepared_result.get("id"):
            raise PrepareError("article_prepare returned an invalid result")
        post_id = int(prepared_result["id"])
        read = wp_call(args.endpoint, token, envelope(parent, "article_read", "verify.initial", {"id": post_id}))

        final_payload = dict(base_payload)
        final_prepared = prepared
        final_read = read
        if dynamic_meta:
            read_result = read.get("result")
            if not isinstance(read_result, dict):
                raise PrepareError("Initial article_read result is missing")
            final_payload["post_meta"] = resolve_dynamic_post_meta(scalar_meta, dynamic_meta, read_result)
            final_prepared = wp_call(
                args.endpoint,
                token,
                envelope(parent, "article_prepare", "article.resolved-meta", final_payload),
            )
            resolved_result = final_prepared.get("result")
            if not isinstance(resolved_result, dict) or int(resolved_result.get("id", 0)) != post_id:
                raise PrepareError("Resolved-meta preparation did not update the same managed draft")
            final_read = wp_call(
                args.endpoint,
                token,
                envelope(parent, "article_read", "verify.final", {"id": post_id}),
            )

        checks = verify_readback(final_payload, final_read, post_content)
        final_result = final_prepared.get("result")
        if not isinstance(final_result, dict):
            raise PrepareError("Final article_prepare result is missing")

        aggregate = {
            "ok": True,
            "schema_version": 1,
            "request_id": parent["request_id"],
            "operation": "prepare_article",
            "site_url": final_prepared.get("site_url", ""),
            "result": {
                "manifest_path": manifest_path,
                "manifest_commit": manifest_commit,
                "manifest_sha256": sha256(manifest_raw),
                "source_commit": source_commit,
                "source_article_path": article_path,
                "source_article_git_blob_sha": str(source.get("article_git_blob_sha", "")).lower(),
                "source_article_sha256": article_sha,
                "article": final_result,
                "media": media_summary,
                "verification": checks,
                "content_sha256": hashlib.sha256(post_content.encode("utf-8")).hexdigest(),
            },
        }
        response_path.write_text(
            json.dumps(aggregate, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
        )
        return 0
    except Exception as exc:
        error = {
            "ok": False,
            "schema_version": 1,
            "request_id": str(parent.get("request_id", "")),
            "error": {"code": "prepare_article_failed", "message": str(exc)},
        }
        response_path.write_text(
            json.dumps(error, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
        )
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
