# Changelog

All notable changes to Content Marketing Workflow are documented here. The project follows Semantic Versioning.

## [Unreleased]

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
