# Runtime capability compatibility handoff

Date: 2026-09-05
Status: approved implementation handoff

## Purpose

Capture the approved product decisions for runtime prerequisite detection, onboarding compatibility checks, degraded-mode behavior and future cloud-media provider extensibility before implementation.

## Approved decisions

### 1. GitHub is a hard prerequisite

GitHub repository access is mandatory for Content Marketing Workflow.

If no usable GitHub integration is available, no accessible project repository exists and one cannot be created/resolved, onboarding is **BLOCKED** and the workflow must not continue in conversational-only mode.

GitHub remains the durable source of truth for non-secret workflow state, articles, social content, metadata, approvals, scheduling/publication state and external-result evidence.

### 2. Cloud media storage is mandatory for the complete media workflow

Onboarding must explicitly state that online cloud media storage is required for the complete workflow and must enumerate every cloud storage provider implemented by the installed CMW version.

Current implementation:

- Google Drive: supported/current provider.
- Dropbox: reserved for a future adapter, not currently supported.

Onboarding must discover whether the supported provider plugin is visible, eligible, installed, connected and operational for the active user/runtime. If installable but not installed, CMW should propose installation during onboarding. If installed but not connected, onboarding should guide connection and verification immediately.

If no supported cloud-media provider is available, CMW enters **DEGRADED** mode rather than silently falling back to GitHub, WordPress or local filesystem storage.

GitHub and WordPress must not be proposed as alternative media-storage providers. Existing repository-backed media support may remain only where needed for explicit legacy compatibility/migration and must never be selected automatically as a fallback.

### 3. No-image publication behavior remains strict

Preserve the current publication invariants:

- without required verified final media, **no WordPress article publication/preparation for publication**;
- without required verified final media, **no social publication**;
- do not introduce text-only social publication as an implicit degraded fallback;
- do not introduce image-less WordPress publication as an implicit degraded fallback.

A missing cloud-media provider may still allow strategy, SEO planning, article drafting/review, social text drafting/review and GitHub persistence where those capabilities do not require final media, but media-dependent publication flows remain blocked.

### 4. WordPress is required for current social publication architecture

The current LinkedIn and Facebook Page publication architecture depends on SEO Workflow Bridge hosted in WordPress.

Therefore:

- WordPress itself remains optional for editorial authoring;
- without a configured/verified WordPress + compatible SEO Workflow Bridge runtime, automatic WordPress publication is unavailable;
- without that WordPress/Bridge runtime, current LinkedIn/Facebook scheduled publication is also unavailable;
- article/social creation and GitHub persistence may continue where their own prerequisites are satisfied.

The compatibility model must distinguish WordPress as a content destination from WordPress/SEO Workflow Bridge as the current publication runtime dependency.

### 5. Image-generation capability must be detected at runtime

CMW must detect whether the active ChatGPT/Codex runtime can actually generate and/or edit images.

When image generation/editing is unavailable but cloud storage is available, CMW enters a degraded/manual handoff path instead of abandoning the visual workflow.

The fallback must:

1. generate a complete ready-to-use prompt for an external/other ChatGPT image-capable conversation or compatible image-generation AI;
2. include content objective, format/dimensions, style, composition, branding, fidelity, required/forbidden elements and source-image constraints;
3. instruct the user to generate/improve the requested image externally;
4. ask the user to upload/provide the resulting image back to the active CMW/Codex workflow;
5. inspect, persist to the configured cloud-media provider, normalize/hash/verify and resume the exact workflow.

If image generation is available but cloud storage is unavailable, generated images may be previewed but cannot become durable `verified_final` media and cannot unlock publication.

### 6. Integration severity and degradation model

CMW must use explicit runtime states:

- `READY`: all prerequisites for the requested/enabled scope are operational;
- `DEGRADED`: core workflow can continue but one or more capabilities are unavailable;
- `BLOCKED`: a hard prerequisite prevents CMW initialization/continuation.

Expected prerequisite classes:

- GitHub repository access: fatal/hard prerequisite;
- cloud media storage: required for complete media workflow, degraded when unavailable;
- image generation/editing: degraded with manual image-generation handoff when unavailable;
- WordPress + SEO Workflow Bridge: optional for authoring but required for WordPress publication and current automated social publication;
- GitHub Actions/scheduler: required for unattended scheduled publication, not for content creation;
- LinkedIn adapter: optional, independently gated;
- Facebook Page adapter: optional, independently gated;
- Telegram: optional notification capability only; absence must never change publication state.

### 7. Onboarding must run compatibility discovery immediately

`/start` must not defer dependency discovery until first use.

During onboarding it must:

1. detect the runtime/surface and available capabilities;
2. verify GitHub first and block if unusable;
3. enumerate supported cloud-media providers for this CMW version;
4. discover provider plugin eligibility/installation/connection state and guide installation/configuration immediately when possible;
5. detect image-generation/editing capability;
6. detect configured WordPress/Bridge availability when the user enables WordPress or social publication;
7. inspect GitHub Actions/scheduler availability for scheduled publication;
8. inspect enabled social adapters independently;
9. inspect Telegram only as an optional notification capability;
10. compute and persist/report the resulting compatibility state and exact unavailable feature list.

### 8. `/status` and `/help` must expose compatibility truthfully

`/status` must show prerequisite health, active provider/runtime choices, global readiness and feature-specific blockers/degradations.

`/help` and command-specific help must not advertise a capability as currently usable when its prerequisite graph is unsatisfied. Commands remain canonical, but availability annotations must come from the compatibility model.

### 9. Central compatibility authority

Do not duplicate degradation logic independently across capability contracts.

Introduce a central architecture authority that defines:

- prerequisite identifiers;
- severity;
- supported providers/adapters;
- detection expectations;
- capabilities depending on each prerequisite;
- missing-prerequisite behavior;
- fallback strategy where one exists.

Individual capability contracts should reference that authority and retain only capability-specific hard gates.

## Initial compatibility matrix

| Prerequisite | Severity | Missing behavior |
|---|---|---|
| GitHub repository access | BLOCKED | CMW does not initialize or continue |
| Cloud media storage | DEGRADED | no durable media workflow, no media-dependent WordPress/social publication |
| Image generation/editing | DEGRADED | external-generation prompt + user upload handoff |
| WordPress + SEO Workflow Bridge runtime | DEGRADED for publication scope | no WordPress publication and no current automated social publication |
| GitHub Actions scheduler | DEGRADED for scheduled-publication scope | no unattended scheduled publication |
| LinkedIn connection/adapter | Optional feature unavailable | LinkedIn publication unavailable only |
| Facebook Page connection/adapter | Optional feature unavailable | Facebook publication unavailable only |
| Telegram | Optional feature unavailable | no notifications; publication state unaffected |

## Implementation work

Implement the approved model across the canonical Skill source and keep the Codex plugin mirror byte-for-byte synchronized.

Expected work:

1. add a central runtime/integration compatibility contract;
2. update `start` onboarding behavior and direct-ChatGPT runtime contract;
3. generalize cloud-media wording around a provider capability while retaining Google Drive as the only current implementation;
4. encode Google Drive discovery/installability/connection verification expectations;
5. add image-generation runtime detection and manual handoff behavior;
6. update media, article, WordPress and social contracts to reference compatibility state while preserving strict no-image publication gates;
7. make WordPress/SEO Workflow Bridge an explicit prerequisite of current automated social publication;
8. expose compatibility/degradation state through `/status` and availability annotations in `/help`;
9. update user-profile schema/persistence model as needed for non-secret compatibility/provider state;
10. update tests for fatal GitHub absence, cloud-storage degraded mode, image-generation handoff, WordPress/social dependency and Telegram independence;
11. update README/direct-install documentation and changelog/versioning as appropriate;
12. synchronize canonical Skill to Codex plugin mirror and run repository tests/CI.

## Non-goals

This change does not implement Dropbox yet.

This change does not make GitHub, WordPress or local filesystem alternative cloud-media providers.

This change does not introduce text-only social publication or image-less WordPress publication.
