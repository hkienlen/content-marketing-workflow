# Changelog

All notable changes to Content Marketing Workflow are documented here. The project follows Semantic Versioning.

## [Unreleased]

## [0.4.2] - 2026-09-06

- Added a review-ready branding gate so generated/materially transformed social A/B/C under `logo_application=always` cannot become selectable until the exact verified official logo is deterministically composed on clean base visuals.
- Added `scripts/visual-review-gate.py` to validate the frozen `contract_revision`, clean-base inspection evidence, official-logo SHA-256, composition manifest and branded review-output SHA-256 before durable human selection.
- Explicitly prohibited generated/project-logo approximations from surviving as selectable review candidates; raw generator outputs are now internal/base drafts until pre-review integrity gates pass.
- Tightened the combined-review state model so `selected` / `fully_approved` cannot be reached from a visually appealing but technically non-compliant branded binary.
- Added a targeted recovery path for already-selected visuals containing generated/unverified logos: preserve approved text and creative preference, repair only the affected visual, and request targeted re-confirmation when pixels/hash change.
- Added regression tests for missing composition evidence, contaminated bases, wrong logo SHA, raw-output misuse and incorrect A/B/C cardinality.
- Bumped the Skill/Codex plugin version to 0.4.2 and synchronized the canonical Skill with the plugin mirror.

## [0.4.1] - 2026-09-06

- Added `scripts/logo-compose.py`, a deterministic SHA-bound official-logo compositor that preserves logo proportions, never overwrites source assets and emits exact composition/output evidence.
- Made effective visual `contract_revision` mandatory for every durable proposal/review round and every `verified_final`, with `scripts/visual-contract-freeze.py` providing canonical SHA-256 freeze/verify behavior.
- Hardened `visual-policy-resolve.py` so a logo from an inactive Google Drive/Dropbox namespace no longer satisfies `always`; provider switching now exposes an explicit rebinding requirement.
- Extended visual/brand regression coverage for provider mismatch/rebinding, deterministic contract revision drift detection and the exact-logo composition helper contract.
- Clarified finalization contracts so historical finals remain bound to exact visual-contract revisions and exact official logo/provider identities.
- Bumped the Skill/Codex plugin version to 0.4.1 and synchronized the canonical Skill with the plugin mirror.

## [0.4.0] - 2026-09-06

- Added a generic visual-generation contract that separates immutable workflow/integrity guarantees from user/project creative directives and generic CMW creative defaults.
- Added durable `visual_identity` project configuration with provider-backed official logo assets, a user-owned visual-guidelines authority and independent `logo_policy.article` / `logo_policy.social` preferences.
- Added `always`, `auto` and `never` logo application modes for articles and social posts independently, including the supported case `article: never` with `social: always`.
- Added `/visual status`, `/visual configure`, `/visual logo`, `/visual guidelines` and `/logo` for guided visual identity, logo and permanent guideline management, with equivalent natural-language routing.
- Extended `/start` and strategy updates so users can provide one official logo or light/dark variants, choose separate article/social logo behavior and persist arbitrary global/article/social visual directives.
- Added a private provider-backed `brand/logos/` workspace for Google Drive and Dropbox plus verified logo identity/hash metadata in the user profile.
- Required exact official logo bytes for deterministic branding/finalization; CMW must not ask image generation to recreate or approximate a missing official logo.
- Extended article and social workflows, checklists, visual-source resolution and asset ingestion so branding and user visual directives are resolved before final-media verification.
- Preserved one-off content-local visual/logo overrides without silently changing durable project preferences, and kept existing verified finals frozen unless explicitly reopened.
- Added regression tests for independent article/social logo policy, legacy-profile compatibility, content-local overrides, command exposure, provider brand workspaces and brand-integrity rules.
- Bumped the Skill/Codex plugin version to 0.4.0 and synchronized the canonical Skill with the plugin mirror.

## [0.3.0] - 2026-09-05

- Added Dropbox as a first-class `cloud_media_storage` provider alongside Google Drive.
- Defined explicit provider selection: exactly one cloud-media provider is active per project; Google Drive remains recommended/default when both providers are operational.
- Added a Dropbox workspace contract covering private source/proposal/final storage, site isolation, `tmp-outbox`, public read-only delivery links, provenance and onboarding.
- Updated `/start`, direct ChatGPT runtime and installation documentation so Google Drive and Dropbox are both discovered, install/connect guidance is provider-aware, and the selected provider is persisted.
- Generalized media delivery, image ingestion, user-provided-image intake, `visual-source-resolve`, `asset-ingest`, article creation/checklists and social creation/checklists around provider-qualified identities.
- Added explicit provider migration/rebinding semantics: Google Drive and Dropbox asset IDs/references are separate namespaces and switching provider never silently reinterprets old identities.
- Extended the user-profile schema and persistence contracts with `cloud_media_storage.provider: google_drive|dropbox` plus provider-specific non-secret workspace references.
- Generalized the social final package: Google Drive stores the exact approved publishable text in a native Google Doc, while Dropbox stores it as a UTF-8 plain-text `.txt` file beside the verified final visual.
- Preserved provider-neutral publication gates: no verified final media means no media-dependent WordPress or social publication.
- Kept GitHub, WordPress and local filesystem excluded as automatic media-storage fallbacks.
- Added dedicated Dropbox regression tests, stale-contract detection and CI execution for the new provider model.
- Bumped the Skill/Codex plugin version to 0.3.0 and synchronized the canonical Skill with the plugin mirror.

## [0.2.1] - 2026-09-05

- Completed the 0.2.0 runtime-compatibility handoff across media, article, WordPress and social capability contracts.
- Generalized media workspace/delivery contracts around the `cloud_media_storage` capability while keeping Google Drive as the only implemented provider and Dropbox future-only.
- Made legacy `repository_file` media explicitly compatibility/migration-only and prohibited it as an automatic fallback.
- Aligned `seo-create-article` and `social-create-visual` with runtime image-generation detection plus the external-generation prompt/user-upload handoff.
- Aligned WordPress preparation/publication with strict required-media behavior and the central prerequisite graph; no image-less WordPress fallback.
- Aligned social scheduling/publication with required cloud media, WordPress-hosted SEO Workflow Bridge and GitHub Actions scheduler; no text-only publication fallback.
- Added durable non-secret `runtime_compatibility` state to the user-profile schema for cloud media, WordPress Bridge and scheduler health while keeping image-generation availability runtime-ephemeral.
- Expanded direct ChatGPT installation/onboarding documentation so new users are guided through dependency discovery instead of needing to know which plugins to install beforehand.
- Strengthened regression tests to assert the central compatibility model across media/article/WordPress/social contracts.
- Bumped the Skill/Codex plugin version to 0.2.1 and synchronized the direct Skill/Codex-plugin behavior model.

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
- Added repository-maintainer guide for ChatGPT Web marketplace import and synchronization.
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
- Bundled SEO Workflow Bridge companion resource.
