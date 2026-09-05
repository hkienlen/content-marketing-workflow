# Changelog

All notable changes to Content Marketing Workflow are documented here. The project follows Semantic Versioning.

## [Unreleased]

## [0.2.0] - 2026-09-05

- Added a central runtime compatibility/prerequisite matrix with `READY`, `DEGRADED` and `BLOCKED` states.
- Made GitHub repository access a fatal prerequisite; CMW no longer treats conversation memory as a fallback project store.
- Made cloud-media availability an explicit onboarding requirement for the complete media workflow while preserving repository-only strategy/content work in degraded mode.
- Kept Google Drive as the only implemented cloud-media provider for this release and reserved Dropbox as a future adapter.
- Explicitly prohibited GitHub, WordPress and local filesystem as automatic media-storage fallbacks; legacy repository-backed media remains compatibility-only.
- Added plugin/provider discovery expectations during onboarding so new users do not need to pre-install Google Drive before `/start`; eligibility is detected from runtime/plugin state rather than subscription labels.
- Added runtime image-generation/editing detection and a manual image handoff path that produces a complete external-generation prompt and resumes after user upload.
- Preserved strict current no-image publication behavior: no WordPress preparation/publication for publication and no social publication without required verified final media.
- Made the current WordPress-hosted SEO Workflow Bridge dependency explicit for automated LinkedIn/Facebook publication.
- Extended `/status` and `/help` availability annotations to expose prerequisite health, impacted features and degraded/manual fallback behavior.
- Added dedicated runtime compatibility regression tests and synchronized the direct Skill/Codex-plugin behavior model.

## [0.1.3] - 2026-09-05

- Made `/help` exhaustive and deterministic from `user-command-catalog.yaml`, preserving canonical syntax and showing disabled/optional commands instead of silently omitting them.
- Added explicit `/social notifications telegram test` command for one diagnostic Telegram delivery without publishing or retrying social content.
- Extended `/status` to report non-secret Telegram configuration/verification state when Telegram notifications are configured or enabled.
- Added a real Telegram `test` runtime/workflow mode that reuses the persisted destination, preserves the existing enabled preference and updates non-secret verification evidence only.
- Strengthened the Skill entrypoint so `/help` and `/status` load their authoritative contracts/state before answering.

## [0.1.2] - 2026-09-05

- Promoted `skills/content-marketing-workflow/` to the canonical Skill source for direct ChatGPT installation.
- Kept the Codex plugin Skill as a byte-for-byte mirror of the canonical Skill and added CI drift checks.
- Added deterministic `.skill` and Skill ZIP build artifacts for direct ChatGPT upload.
- Added direct ChatGPT runtime/onboarding rules, including connected-tool detection and selective project-repository migration.
- Clarified that repository work can remain in ChatGPT when the required connected tools are available and does not automatically require Codex.
- Added `tools/sync-skill-mirror.py` for maintainers.
- Updated CI and tagged releases to validate and publish both direct Skill and Codex plugin artifacts.
- Updated documentation so direct ChatGPT Skill installation is the primary ChatGPT path while the Codex plugin remains supported.

## [0.1.1] - 2026-09-05

- Added the selected Content Marketing Workflow visual identity to the repository and installable plugin assets.
- Wired `interface.composerIcon` and `interface.logo` to the canonical plugin icon assets.
- Changed the plugin `interface.developerName` to `Hervé Kienlen`.
- Documented ChatGPT Web workspace import from the same private/public GitHub marketplace used by Codex.
- Formalized that no separate Apps SDK/MCP wrapper is required merely to distribute this skill-only plugin on ChatGPT Web.
- Added a repository-maintainer guide for ChatGPT Web marketplace import and synchronization.
- Added the canonical Codex repo/team marketplace manifest at `.agents/plugins/marketplace.json`.
- Moved installable plugin source under `plugins/content-marketing-workflow/` to match the official marketplace layout and avoid repository-root plugin path issues.
- Added repository tests that bind marketplace discovery, plugin source, package manifest and release ZIP to the same canonical plugin.
- Added a Codex CLI marketplace/install smoke test in CI using a pinned CLI version.
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
