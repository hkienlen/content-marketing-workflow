#!/usr/bin/env python3
"""Prepare v2 wrapper adding provider-neutral presentation profiles.

The generic preparation core renders validated editorial Markdown and resolves
managed WordPress media. When a manifest content object supplies a pinned
`presentation_profile_path`, this wrapper delegates final post_content
serialization to the adapter named by that profile.

V1 adapter registry contains only `divi_shortcode_v1`. The generic contract does
not assume Divi; sites without a presentation profile continue through the core
renderers unchanged.
"""

from __future__ import annotations

import html
import importlib.util
import json
import pathlib
import re
from typing import Any

CORE_PATH = pathlib.Path(__file__).with_name("wordpress-relay-prepare-v2.py")
spec = importlib.util.spec_from_file_location("wordpress_relay_prepare_v2", CORE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load wordpress-relay-prepare-v2.py")
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

_original_resolve_repository_content = core.resolve_repository_content

_FIGURE_RE = re.compile(
    r'<figure\s+class="wp-block-image">\s*<img\s+(?P<attrs>[^>]+)>\s*(?:<figcaption>.*?</figcaption>)?\s*</figure>',
    re.IGNORECASE | re.DOTALL,
)
_ATTR_RE = re.compile(r'([A-Za-z_:][-A-Za-z0-9_:.]*)="([^"]*)"')


def _profile(content_cfg: dict[str, Any], source_commit: str, prefixes: list[str]) -> dict[str, Any] | None:
    path_raw = str(content_cfg.get("presentation_profile_path", "")).strip()
    sha_raw = str(content_cfg.get("presentation_profile_git_blob_sha", "")).strip().lower()
    if not path_raw and not sha_raw:
        return None
    if not path_raw or not sha_raw:
        raise core.PrepareError(
            "presentation_profile_path and presentation_profile_git_blob_sha must be provided together"
        )
    path = core.safe_repo_path(path_raw)
    if not core.allowed_prefix(path, prefixes):
        raise core.PrepareError(f"Presentation profile path is outside allowed content prefixes: {path}")
    core.verify_git_blob(source_commit, path, sha_raw)
    try:
        data = json.loads(core.git_bytes(source_commit, path).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise core.PrepareError(f"Presentation profile is not valid UTF-8 JSON: {path}") from exc
    if not isinstance(data, dict):
        raise core.PrepareError("Presentation profile must be a JSON object")
    if int(data.get("schema_version", 0)) != 1:
        raise core.PrepareError("Unsupported presentation profile schema_version")
    return data


def _shortcode_attrs(attrs: dict[str, Any]) -> str:
    out: list[str] = []
    for key, raw in attrs.items():
        if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", key):
            raise core.PrepareError(f"Unsafe shortcode attribute key in presentation profile: {key!r}")
        value = html.escape(str(raw), quote=True)
        out.append(f'{key}="{value}"')
    return (" " + " ".join(out)) if out else ""


def _open(tag: str, attrs: dict[str, Any]) -> str:
    if not re.fullmatch(r"et_pb_[a-z0-9_]+", tag):
        raise core.PrepareError(f"Unsafe Divi shortcode tag in presentation profile: {tag}")
    return f"[{tag}{_shortcode_attrs(attrs)}]"


def _close(tag: str) -> str:
    return f"[/{tag}]"


def _module(profile: dict[str, Any], name: str) -> tuple[str, dict[str, Any]]:
    adapter_config = profile.get("adapter_config")
    if not isinstance(adapter_config, dict):
        raise core.PrepareError("Presentation profile adapter_config must be an object")
    modules = adapter_config.get("modules")
    if not isinstance(modules, dict) or not isinstance(modules.get(name), dict):
        raise core.PrepareError(f"Presentation profile is missing module definition: {name}")
    entry = modules[name]
    tag = str(entry.get("tag", ""))
    attrs = entry.get("attributes", {})
    if not isinstance(attrs, dict):
        raise core.PrepareError(f"Presentation module attributes must be an object: {name}")
    return tag, dict(attrs)


def _extract_img_attrs(raw: str) -> dict[str, str]:
    attrs = {key.lower(): html.unescape(value) for key, value in _ATTR_RE.findall(raw)}
    if not attrs.get("src"):
        raise core.PrepareError("Managed inline figure is missing img src")
    return attrs


def _divi_shortcode_v1(profile: dict[str, Any], article_body_html: str) -> str:
    section_tag, section_attrs = _module(profile, "section")
    row_tag, row_attrs = _module(profile, "row")
    column_tag, column_attrs = _module(profile, "column")
    text_tag, text_attrs_base = _module(profile, "text")
    image_tag, image_attrs_base = _module(profile, "image")

    pieces: list[str] = []
    cursor = 0
    text_index = 0
    image_index = 0

    def append_text(fragment: str) -> None:
        nonlocal text_index
        if not fragment.strip():
            return
        text_index += 1
        attrs = dict(text_attrs_base)
        attrs["admin_label"] = f"Article text {text_index}"
        pieces.extend([_open(text_tag, attrs), fragment.strip(), _close(text_tag)])

    for match in _FIGURE_RE.finditer(article_body_html):
        append_text(article_body_html[cursor:match.start()])
        image_index += 1
        img = _extract_img_attrs(match.group("attrs"))
        attrs = dict(image_attrs_base)
        attrs["admin_label"] = f"Article image {image_index}"
        attrs["src"] = img["src"]
        if img.get("alt"):
            attrs["alt"] = img["alt"]
        if img.get("title"):
            attrs["title_text"] = img["title"]
        pieces.extend([_open(image_tag, attrs), _close(image_tag)])
        cursor = match.end()

    append_text(article_body_html[cursor:])
    if not pieces:
        raise core.PrepareError("Presentation adapter produced no article modules")

    return "\n".join([
        _open(section_tag, section_attrs),
        _open(row_tag, row_attrs),
        _open(column_tag, column_attrs),
        *pieces,
        _close(column_tag),
        _close(row_tag),
        _close(section_tag),
    ])


def resolve_repository_content(
    content_cfg: dict[str, Any],
    source_commit: str,
    prefixes: list[str],
    article_body_html: str,
    media_results: dict[str, dict[str, Any]],
) -> str:
    profile = _profile(content_cfg, source_commit, prefixes)
    if profile is None:
        return _original_resolve_repository_content(
            content_cfg, source_commit, prefixes, article_body_html, media_results
        )

    adapter = str(profile.get("adapter", "")).strip()
    if adapter == "divi_shortcode_v1":
        rendered = _divi_shortcode_v1(profile, article_body_html)
        if "<!-- wp:divi/placeholder" in rendered:
            raise core.PrepareError("Divi shortcode presentation adapter must not emit a Divi block placeholder")
        if "[et_pb_section" not in rendered or "[et_pb_text" not in rendered:
            raise core.PrepareError("Divi shortcode presentation adapter produced an incomplete layout")
        return rendered
    raise core.PrepareError(f"Unsupported presentation profile adapter: {adapter}")


core.resolve_repository_content = resolve_repository_content

if __name__ == "__main__":
    raise SystemExit(core.main())
