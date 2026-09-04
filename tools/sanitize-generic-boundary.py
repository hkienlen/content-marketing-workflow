#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "content-marketing-workflow"


def replace(path: Path, old: str, new: str, *, required: bool = True) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        if required:
            raise SystemExit(f"missing expected text in {path}: {old[:100]!r}")
        return
    path.write_text(text.replace(old, new), encoding="utf-8")


def sub(path: Path, pattern: str, replacement: str, *, count: int = 0, flags: int = 0, required: bool = True) -> None:
    text = path.read_text(encoding="utf-8")
    updated, n = re.subn(pattern, replacement, text, count=count, flags=flags)
    if required and n == 0:
        raise SystemExit(f"pattern did not match in {path}: {pattern[:100]!r}")
    path.write_text(updated, encoding="utf-8")


# Plugin publisher metadata must describe the product, not a private pilot user.
plugin_path = ROOT / ".codex-plugin" / "plugin.json"
plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
plugin["author"] = {"name": "Content Marketing Workflow"}
plugin.setdefault("interface", {})["developerName"] = "Content Marketing Workflow"
plugin_path.write_text(json.dumps(plugin, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# Release provenance is bound to the exact source SHA; the installable package does not need an owner/account URL.
manifest_path = ROOT / "plugin-package-manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest.pop("canonical_repository", None)
manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

build_path = ROOT / "tools" / "build-release.py"
replace(
    build_path,
    "source={'plugin_name':cfg['plugin_name'],'version':version,'canonical_repository':cfg['canonical_repository'],'source_commit_sha':sha}",
    "source={'plugin_name':cfg['plugin_name'],'version':version,'source_commit_sha':sha}",
)

# Repository-only history/guidance must not name the former private pilot source.
agents = ROOT / "AGENTS.md"
sub(
    agents,
    r"All generic product corrections, evolutions, packaging changes and versioning must be developed here\..*?before release\.\n",
    "All generic product corrections, evolutions, packaging changes and versioning must be developed here. Separate integration environments may validate real user/project state, but product changes discovered there must be ported back here through a normal branch/PR before release.\n",
    count=1,
    flags=re.DOTALL,
)

(ROOT / "MIGRATION.md").write_text(
    """# Migration to the canonical repository

Date: 2026-09-04

This repository became the canonical generic product source starting from **Content Marketing Workflow 0.1.0**.

The initial package was validated in a separate private integration environment before the canonical split. That environment and its user/project state are intentionally not identified or reproduced here.

Future generic release source SHAs belong only to this repository. Separate integration environments may continue to validate real workflows, but corrections, evolutions and versioning must be committed here before release.
""",
    encoding="utf-8",
)

(ROOT / "CHANGELOG.md").write_text(
    """# Changelog

All notable changes to Content Marketing Workflow are documented here. The project follows Semantic Versioning.

## [Unreleased]

- Canonical development moved into a dedicated generic product repository.
- Added self-contained release build and repository CI.
- Removed integration-specific presentation/profile examples from generic documentation.
- Removed private integration provenance from installable metadata.
- Removed remaining user/project-specific examples and publisher identity from the canonical source and release payload.
- Added repository-wide privacy/boundary regression checks.

## [0.1.0] - 2026-09-04

- Initial plugin productization.
- One primary `content-marketing-workflow` skill with governed SEO, visual, WordPress and social capabilities.
- Explicit user/project data and credential boundaries.
- Bundled SEO Workflow Bridge companion.
""",
    encoding="utf-8",
)

# Human-review wording must be generic.
prompt = SKILL / "docs" / "architecture" / "prompt-as-contract.md"
replace(prompt, "Il porte les règles communes d'exécution des articles du site pilote", "Il porte les règles communes d'exécution des articles du site actif")
sub(
    prompt,
    r"13\. présenter le résultat à .+? dans ChatGPT pour revue humaine ;",
    "13. présenter le résultat à l'utilisateur dans ChatGPT pour revue humaine ;",
    count=1,
)

# Replace profession/project-derived business examples with neutral examples.
business = SKILL / "docs" / "architecture" / "business-model-extensibility.md"
replace(
    business,
    "The single installable Content / Marketing skill is first validated on the current service-business pilot, but its generic model",
    "The single installable Content / Marketing skill was initially validated in a service-business context, but its generic model",
)
sub(
    business,
    r"A service may represent, for example:\n\n(?:- .*\n)+",
    """A service may represent, for example:

- professional coaching;
- website creation or hosting;
- consulting;
- personal assistance;
- repair;
- plumbing or masonry;
- training;
- maintenance/support;
- local or remote professional services;
- SaaS-related implementation/support services.
""",
    count=1,
)
sub(
    business,
    r"A .*? business may combine hosted SaaS, self-hosted installation, a professional licence and support without becoming a different product architecture\.",
    "A software business may combine hosted SaaS, self-hosted installation, a professional licence and support without becoming a different product architecture.",
    count=1,
)
replace(business, "1. service-business pilot;", "1. service-business workflows;")
sub(
    business,
    r"They must not hardcode pilot-specific values such as:\n\n(?:- .*\n)+",
    """They must not hardcode user/project-specific values such as:

- one user's identity as a universal author;
- one profession's terminology;
- one CTA URL;
- one business offer;
- one WordPress topology;
- one social account;
- one builder/theme;
- user/project-specific brand assets.
""",
    count=1,
)
replace(
    business,
    "For the pilot, existing authoritative strategy remains valid and must be reused rather than duplicated into a speculative new schema.",
    "For an existing project, authoritative strategy remains valid and must be reused rather than duplicated into a speculative new schema.",
)

# Replace real article examples with placeholders.
article_inspect = SKILL / "docs" / "architecture" / "capabilities" / "article-inspect.md"
sub(
    article_inspect,
    r"Accepted identity forms include:\n\n```text\n.*?```",
    """Accepted identity forms include:

```text
/article details <article-slug>
/article details <article-slug>.md
/article details articles/<audience>/<article-slug>.md
```""",
    count=1,
    flags=re.DOTALL,
)

inspection = SKILL / "docs" / "architecture" / "content-inspection-state-model.md"
sub(
    inspection,
    r"1\. exact repository path, e\.g\. `articles/.*?`;\n2\. exact filename, e\.g\. `.*?`;\n3\. exact front-matter slug;\n4\. exact filename stem as a convenience identifier\.",
    """1. exact repository path, e.g. `articles/<audience>/<article-slug>.md`;
2. exact filename, e.g. `<article-slug>.md`;
3. exact front-matter slug;
4. exact filename stem as a convenience identifier.""",
    count=1,
)

# Concrete scheduled authorizations are user/project state and never belong in a generic contract.
linkedin = SKILL / "docs" / "architecture" / "linkedin-github-actions-scheduler.md"
sub(
    linkedin,
    r"## Current pilot authorizations\n.*?## Future skill requirement",
    """## User/project authorization boundary

Concrete post IDs, scheduled timestamps and authorization records are user/project state and must not be embedded in this generic contract or release payload.

Canonical generic record shape:

```text
social/publication-authorizations/linkedin/<post-id>.json
```

## Future skill requirement""",
    count=1,
    flags=re.DOTALL,
)

# Generic placeholders for any social ID examples still present in distributable text.
for path in SKILL.rglob("*"):
    if not path.is_file() or path.suffix.lower() not in {".md", ".json", ".yaml", ".yml", ".py", ".php", ".txt", ".sh", ".bash"}:
        continue
    text = path.read_text(encoding="utf-8", errors="ignore")
    updated = re.sub(r"\b20\d{2}-\d{4}\b", "<post-id>", text)
    if updated != text:
        path.write_text(updated, encoding="utf-8")

# Other examples derived from a real content project become structural placeholders.
runtime = SKILL / "docs" / "architecture" / "user-command-runtime-contract.md"
sub(runtime, r"articles/[^/\s`]+/Mon-Article\.md", "articles/<audience>/<article-slug>.md", count=1)

social_extract = SKILL / "docs" / "architecture" / "capabilities" / "social-extract-posts.md"
sub(social_extract, r"not merely the [A-Za-z-]+ topic", "not merely the subject area", count=1)

user_images = SKILL / "docs" / "architecture" / "user-provided-images.md"
sub(user_images, r"source-user/[a-z0-9-]+\.jpg", "source-user/source-image.jpg", count=1)
sub(user_images, r"final/[a-z0-9-]+-social\.jpg", "final/final-social-image.jpg", count=1)

# Preserve the validated WordPress retry lesson without carrying a real article/date/adapter history.
wp_publish = SKILL / "docs" / "architecture" / "capabilities" / "wordpress-publish-article.md"
sub(
    wp_publish,
    r"## Historical live pilot evidence.*?## Environment boundary",
    """## Validated retry safety behavior

The retry contract is intentionally fail-closed and preserves the following generic sequence once publication is actually requested:

1. prepare provider-backed media and a Bridge-managed draft;
2. complete human presentation validation;
3. receive explicit publication-stage continuation;
4. run `publication_capture` after any editor normalization;
5. persist an immutable candidate;
6. run preflight;
7. if the Bridge reports `article_publish_disabled`, treat the attempt as blocked with no mutation;
8. treat the runtime authorization used by that request as consumed;
9. after the blocking permission is corrected, run a fresh preflight;
10. require a new explicit publication authorization;
11. allow `article_publish` to transition exactly `draft -> publish`;
12. verify the same candidate through `published_article_read` and all pinned checks;
13. return publication permission to least privilege after publication.

This is the canonical safety behavior for future retries once publication is actually requested.

## Environment boundary""",
    count=1,
    flags=re.DOTALL,
)

wp_gate = SKILL / "docs" / "architecture" / "wordpress-review-gate.md"
sub(
    wp_gate,
    r"Older pilot execution records may retain an adapter-specific wording such as `[^`]+`\. Such wording is historical evidence only\. New/current workflow contracts and user-facing prompts must use `WordPress OK`\.",
    "Legacy integration records may retain adapter-specific wording. Such wording is external project history only. Current workflow contracts and user-facing prompts must use `WordPress OK`.",
    count=1,
)

freeze = SKILL / "docs" / "architecture" / "skill-productization-freeze.md"
sub(freeze, r"^[^\n]*content-marketing-workflow main$", "canonical repository main", count=1, flags=re.MULTILINE)
sub(
    freeze,
    r"- future generic releases are sourced only from `[^`]+`;",
    "- future generic releases are sourced only from this canonical repository;",
    count=1,
)

# Remove any concrete user-owned country-domain hostname from current source text.
# Vendor URLs used by the product are .com/.org/invalid endpoints; a .fr hostname in this generic source is treated as a privacy regression.
text_suffixes = {".md", ".json", ".yaml", ".yml", ".py", ".php", ".txt", ".sh", ".bash"}
fr_host = re.compile(r"\b(?:[a-z0-9-]+\.)+[a-z0-9-]*\.fr\b", re.IGNORECASE)
email = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
concrete_post = re.compile(r"\b20\d{2}-\d{4}\b")
for path in ROOT.rglob("*"):
    if not path.is_file() or ".git" in path.parts or "build" in path.parts or path.suffix.lower() not in text_suffixes:
        continue
    text = path.read_text(encoding="utf-8", errors="ignore")
    if fr_host.search(text):
        raise SystemExit(f"country-domain hostname remains in {path.relative_to(ROOT)}")
    if email.search(text):
        raise SystemExit(f"email literal remains in {path.relative_to(ROOT)}")
    if concrete_post.search(text):
        raise SystemExit(f"concrete social post ID remains in {path.relative_to(ROOT)}")

print("generic boundary sanitation complete")
