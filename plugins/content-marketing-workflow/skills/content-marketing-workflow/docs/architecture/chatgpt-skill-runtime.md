# Direct ChatGPT Skill runtime contract

## Purpose

This document defines how Content Marketing Workflow behaves when the canonical Skill is uploaded or installed directly in ChatGPT. It also defines the boundary between direct ChatGPT execution and the optional Codex plugin distribution.

Runtime prerequisite discovery and degraded-mode semantics are authoritative in:

```text
docs/architecture/runtime-compatibility-matrix.md
```

## Distribution modes

The same workflow may be used in two modes:

1. **Direct ChatGPT Skill**: the user uploads or installs the packaged Skill in ChatGPT and works conversationally.
2. **Codex plugin**: the same Skill is mirrored inside the plugin package so Codex can discover it through the repository marketplace.

The direct Skill is the preferred distribution for users who can install Skills in ChatGPT but cannot import or administer plugin marketplaces. The Codex plugin remains supported for repository-heavy Codex execution and marketplace-based installation.

## Tool/plugin availability is runtime state

The Skill is instructions plus packaged resources. It never grants a provider connection by itself.

Before any external read or write, determine whether the active ChatGPT conversation actually exposes the required connected tool. Examples include GitHub repository access, WordPress access, cloud storage and social-provider actions.

A new user is not expected to know which integration plugins CMW needs before running `/start`.

When the active ChatGPT surface exposes plugin discovery/management, onboarding must search for implemented provider plugins even when they are not installed and distinguish at least:

```text
not visible / not eligible
visible and installable but not installed
installed but not connected
connected but unverified
operational
```

If an implemented provider is installable, propose installation during onboarding. If installed but not connected, guide connection immediately. Never infer eligibility merely from a plan label such as Free or Plus; use actual runtime/plugin state when inspectable and report `eligibility unknown` when it is not.

- If the tool is available, use it according to the relevant capability contract.
- If the tool is unavailable, do not claim that the external action occurred.
- Do not force Codex merely because the Skill was installed in ChatGPT. Use Codex only when the user chooses it or when the required operation is genuinely unavailable in the active ChatGPT surface.
- Do not ask the user to repeat repository information that an available connected repository tool can resolve safely.

## Hard GitHub prerequisite

GitHub repository access is structurally required by CMW.

If no usable GitHub integration/repository can be accessed, resolved or created through the available runtime, report:

```text
Compatibility: BLOCKED
```

and stop CMW initialization. Do not continue by treating conversation memory or temporary files as durable project state.

## Cloud-media prerequisite

The complete media workflow requires an implemented online cloud-media provider.

Implemented providers:

```text
Google Drive (`google_drive`)
Dropbox (`dropbox`)
```

Exactly one provider is active per project. When both are operational, Google Drive is recommended/default unless the user explicitly chooses Dropbox. Provider selection is durable project state; changing it later is an explicit migration/configuration action rather than an automatic fallback.

GitHub, WordPress and local filesystem are not fallback media-storage providers.

If no supported provider is operational, report `DEGRADED`. Repository-only strategy/content work may continue where its own prerequisites are satisfied, but required media cannot become durable `verified_final` assets and media-dependent WordPress/social publication remains unavailable.

## Image-generation runtime capability

Image generation/editing is an ephemeral runtime capability and must be detected when visual generation/treatment is needed.

If the current ChatGPT/Codex surface cannot generate/edit the required image but cloud-media storage is operational, use the manual handoff defined in `runtime-compatibility-matrix.md`:

1. preserve the exact owning article/post revision and visual policy;
2. produce a complete ready-to-copy image-generation/improvement prompt;
3. tell the user to run it in an image-capable ChatGPT conversation or another compatible image AI;
4. ask the user to return/upload the resulting image;
5. inspect and retain it in the configured cloud provider;
6. resume normal review/normalization/hash/verification.

Do not mark the visual workflow complete merely because the prompt was produced.

If image generation works but cloud storage does not, the generated output may be shown for review but cannot become publication-eligible durable media.

## `/start` in direct ChatGPT

When `/start` is invoked, or the user naturally asks to initialize/resume a project:

1. load the `start` capability contract and `runtime-compatibility-matrix.md`;
2. detect whether durable project configuration already exists in the target project repository or other authoritative project state;
3. verify GitHub first; if unusable, stop as `BLOCKED`;
4. if a target repository is identified and GitHub/repository tools are available, inspect it before asking onboarding questions;
5. enumerate Google Drive and Dropbox and discover each provider's plugin eligibility/installation/connection state when the runtime supports discovery;
6. when both are operational, present both explicitly and default to Google Drive unless the user chooses Dropbox; persist exactly one active provider;
7. install/connect/verify the selected eligible provider during onboarding when possible; otherwise record/report a resumable `DEGRADED` media blocker with exact impacted features;
8. detect image-generation/editing availability for the current surface;
9. when WordPress or social publication is enabled, verify the WordPress-hosted SEO Workflow Bridge runtime required by the current publication architecture;
10. verify scheduling/social/notification prerequisites for the enabled scope;
11. resume from verified existing configuration rather than restarting onboarding blindly;
12. ask only for unresolved values required by the active capability contract;
13. persist project-specific configuration only in the project repository/state location defined by the persistence contracts, never in this generic Skill package;
14. keep credentials and raw provider secrets outside Git;
15. finish with truthful `READY|DEGRADED|BLOCKED` compatibility and feature-level blockers.

## Initializing a new project repository

When the user wants a fresh project repository for editorial work:

1. confirm or resolve the target repository;
2. inspect the repository before writing when repository tools are available;
3. initialize only the project-specific content/state structure required by the current contracts;
4. do not copy this product repository, its CI/release machinery, generic plugin source, package manifests or product tests into the project repository;
5. record environment/site/channel choices as project data, not generic Skill defaults;
6. run `/status` semantics after initialization and report what is ready, degraded, optional and blocked by unavailable connections.

## Migrating from an existing project repository

Migration is selective, not a repository clone.

When the user names an old repository and specifies content classes to reuse:

1. inspect both source and target repositories when tools permit;
2. inventory candidate files by semantic role, not merely by directory name;
3. copy only the classes explicitly requested by the user, such as article content, social-post content, related approved media metadata or research context that remains authoritative;
4. exclude unrelated product development, generic skill/plugin source, CI/release tooling, credentials, tokens, obsolete integration state and historical implementation experiments unless the user explicitly requests them for reference;
5. preserve provenance where the persistence contracts require it;
6. do not treat historical approval/publication evidence as authorization for a new target environment;
7. do not automatically re-adopt legacy repository-backed media as the new storage strategy; current cloud-media readiness requires one implemented provider;
8. when switching between Google Drive and Dropbox, explicitly migrate/rebind provider-backed asset identities and preserve exact hashes/provenance rather than reinterpreting existing IDs;
9. present the migration plan or bounded changes for review when a human review gate applies.

## ChatGPT conversational workflow

Direct ChatGPT use is intended to support the full conversational loop when the necessary tools are present:

- onboarding and compatibility diagnosis;
- content inventory and status;
- article planning, drafting and revision;
- social-series planning, post creation and review;
- visual-source handling according to policy;
- manual image-generation handoff when the active runtime lacks image generation but a supported cloud provider is available;
- repository writes and GitHub workflow operations when connected GitHub tools expose them;
- WordPress/social preparation or publication only through the explicit provider gates.

A repository-heavy task does not automatically require Codex. Prefer the active surface that can complete the task safely with the available tools and the user's requested interaction style.

## Publication degradation boundary

Preserve the current strict publication behavior:

```text
missing required verified_final image
-> no WordPress publication/preparation-for-publication
-> no social publication
```

Do not introduce text-only social publication or image-less WordPress publication as an automatic degraded fallback.

The current LinkedIn and Facebook Page publication adapters rely on SEO Workflow Bridge hosted in WordPress. Without a verified WordPress/Bridge runtime, social authoring may continue, but current automated social publication is unavailable.

## Installation artifact behavior

The canonical direct-install source is `skills/content-marketing-workflow/` in the product repository. Release automation packages that folder as a Skill bundle. The bundle contains `SKILL.md` plus all supporting resources required by the workflow.

Uploading only `SKILL.md` can install the core playbook, but supporting contracts/scripts are then unavailable. For this workflow, use the complete packaged Skill whenever possible.

## Consistency requirement

The direct Skill source and the copy embedded in the Codex plugin must remain byte-for-byte equivalent. Repository tests enforce this invariant so fixes made for ChatGPT and fixes made for Codex cannot silently diverge.
