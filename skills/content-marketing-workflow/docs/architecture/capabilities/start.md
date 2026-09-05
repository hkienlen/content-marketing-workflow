# Internal capability: start

Date: 2026-09-05
Status: current capability contract

## Purpose

`start` is the onboarding/orchestration capability of the single installable Content / Marketing skill.

It initializes or resumes one user/project without making the user understand repository layout, Git, Work Items, external-media hierarchy or optional integration internals.

The skill owns the schema and onboarding behavior. Concrete user/site/project values are persisted in user data.

## Runtime compatibility authority

Before treating onboarding as operational, read and apply:

```text
docs/architecture/runtime-compatibility-matrix.md
```

`/start` performs compatibility discovery immediately. A new user is not expected to know or pre-install CMW's integration plugins before onboarding.

Hard rule:

```text
no usable GitHub repository access -> BLOCKED -> stop CMW onboarding
```

Cloud-media rule:

```text
no supported operational cloud-media provider -> DEGRADED
```

The implemented cloud-media providers are Google Drive and Dropbox. Exactly one provider is active per project; when both are operational, Google Drive is the recommended/default choice unless the user explicitly selects Dropbox. GitHub, WordPress and local filesystem are not media-storage fallbacks.

When runtime plugin discovery is available, onboarding must search for each implemented cloud-media provider even when not installed, distinguish eligibility/installability/installation/connection state, propose installation when eligible, and guide connection/verification immediately. Never infer provider eligibility solely from a ChatGPT plan name.

Onboarding must also detect whether the active runtime can generate/edit images. When required image generation is unavailable but cloud storage works, configure the manual image handoff defined by `runtime-compatibility-matrix.md`: produce a complete external-generation prompt, receive the user-generated result back, then persist/inspect/finalize it normally.

When WordPress or social publication is enabled, verify the WordPress-hosted SEO Workflow Bridge runtime because the current LinkedIn/Facebook publication architecture depends on it. Without WordPress/Bridge, authoring may continue but current automated social publication is unavailable.

## Capability contract

```yaml
name: start
purpose: Initialize or resume durable user/project/site onboarding and leave the profile, repository and workspaces in a verified state for enabled capabilities.
availability: core
feature_gate: null
mode: mutating

prerequisites:
  - GitHub repository access is available; absence is a fatal BLOCKED state
  - repository-wide instructions can be read
  - runtime compatibility is evaluated from docs/architecture/runtime-compatibility-matrix.md
  - configured external-media provider access can be verified before asset-producing workflows are considered ready

mandatory_context:
  - AGENTS.md
  - docs/architecture/single-skill-scope.md
  - docs/architecture/runtime-compatibility-matrix.md
  - docs/architecture/business-model-extensibility.md
  - docs/architecture/persistence-contract.md
  - docs/architecture/user-profile-data-contract.md
  - docs/architecture/user-provided-images.md
  - docs/architecture/schemas/user-profile.schema.json
  - docs/architecture/capability-contract-template.md
  - docs/architecture/testing-policy.md
  - docs/architecture/google-drive-workspace.md
  - docs/architecture/dropbox-workspace.md
  - docs/architecture/media-delivery-architecture.md
  - user-data/profile.json when present
  - user-owned strategy/storage/connection authorities referenced by the active profile when present

optional_context:
  - existing website and representative public content
  - existing SEO/editorial/social strategy
  - existing WordPress configuration/state
  - existing social configuration/state
  - existing notification configuration/state
  - representative existing articles/posts useful for editorial learning
  - existing project images/brand assets useful only as evidence/proposals until intentionally adopted

reads:
  - current generic architecture/models
  - active user/project profile and authority pointers
  - existing durable business/site facts
  - existing strategy and content indexes/state when available
  - configured external-media workspace state
  - runtime/plugin eligibility/availability state when inspectable
  - existing visual_preferences when present
  - optional WordPress/social/notification capability state

writes:
  - user-data/profile.json for concrete user/project identity, preferences and infrastructure metadata
  - richer user-owned business/strategy documents referenced by the profile
  - external-media workspace references/configuration in user data
  - structured visual_preferences when the user confirms them
  - tmp-outbox non-secret configuration and verified accessibility state
  - optional capability flags and notification preferences selected by the user
  - verified onboarding/progress state and durable blockers in user/project data

persists:
  - selected repository/site identity
  - site domain/URL
  - durable business/activity facts
  - composable offers and audiences as the site's authoritative model supports them
  - editorial/SEO initialization decisions
  - visual_preferences default + optional article/social overrides
  - external-media workspace root/site/article/social/tmp-outbox references
  - selected media provider
  - optional WordPress/social enablement choices
  - user publication preferences such as timezone/platform hours when explicitly chosen
  - non-secret social connection identity and credential-expiry metadata when discovered
  - optional notification preferences and non-secret routing/configuration metadata
  - verified onboarding checkpoints and blockers

external_side_effects:
  - inspect the existing public website when useful
  - discover supported provider plugins when runtime tooling exposes plugin management
  - propose installation/connection of an implemented provider during onboarding when eligible
  - create/reuse required external-media workspace folders
  - test anonymous read access to tmp-outbox after the user configures its share setting
  - delegate to wordpress-connect only when WordPress is enabled/relevant and the user proceeds with that integration
  - guide/verify optional Telegram notification setup when explicitly enabled
  - no public content publication

human_approval:
  - ask only for durable business/editorial/visual values that cannot be safely inferred or verified
  - do not overwrite contradictory previously confirmed durable data without explicit resolution
  - summarize the proposed durable visual preference in plain language before first persistence/material replacement
  - enabling optional external integrations/notifications is a durable user choice
  - when the connected provider cannot set folder public-link sharing itself, instruct the user through the one simple share-setting action instead of requiring cloud-console credentials
  - any temporary WordPress write test keeps the separate wordpress-connect approval gate
  - Telegram setup may send one explicit test message after the user opts in; it never authorizes social publication
  - no merge or publication authorization is implied

validation:
  - active profile validates against docs/architecture/schemas/user-profile.schema.json
  - existing onboarding state is reused instead of duplicated
  - GitHub hard prerequisite is verified before CMW proceeds
  - cloud-media and runtime capability states are reported truthfully and never inferred from subscription label alone
  - every durable answer is persisted immediately in the correct user/project authority
  - visual_preferences, when present, use only the structured schema enums and do not contain pilot-specific defaults
  - content-local visual instructions are not promoted to project preference without explicit user intent
  - no concrete pilot/user value is saved by modifying a generic skill contract
  - no secret or credential is committed
  - external-media workspace hierarchy is verified before media workflows are marked ready
  - tmp-outbox is the only public-link workspace and anonymous read access is verified
  - article/social/source-user/proposal/final workspaces remain private
  - optional capability/notification state matches actual configuration
  - no profession-specific assumption is introduced into generic onboarding

completion_conditions:
  - required core user/project/site/business facts are durably recoverable
  - active profile is valid and points to richer authorities when applicable
  - visual preference is explicitly configured, or its missing state is explicitly recorded/resumable rather than silently inferred from one-off content
  - GitHub is verified or onboarding is truthfully BLOCKED
  - cloud-media readiness is verified or explicit DEGRADED blockers/affected features are reported
  - media provider and delivery-folder configuration are recoverable and verified when media readiness is claimed
  - image-generation/editing runtime availability is known for the current surface when visual generation is in scope, with manual handoff available when needed
  - WordPress/Bridge dependency is verified when WordPress or automated social publication is enabled
  - relevant strategy exists or is explicitly marked incomplete
  - optional capability choices are persisted
  - optional notification preference is explicit when offered
  - enabled notification configuration is verified or left as an explicit resumable blocker
  - blockers are explicit and resumable
  - repository/user state is re-read and verified

next_actions:
  - seo-plan-article
  - strategy-update when durable strategy/preferences change
  - wordpress-connect when WordPress is enabled and not verified
  - social capabilities when social is enabled and source content is ready
  - telegram-publication-notifications when Telegram publication reports are requested
```

## Resume-first behavior

On every invocation:

1. read `user-data/profile.json` first when it exists;
2. resolve `active_project_id` and referenced user-owned authorities;
3. determine which onboarding facts/checkpoints are already complete;
4. re-evaluate runtime compatibility needed for the active surface/scope rather than assuming a previous conversation exposed the same tools;
5. ask only for missing or contradictory information;
6. persist each durable answer immediately;
7. verify the write before continuing to a dependent step;
8. finish with the next unresolved checkpoint or next useful capability.

Do not restart onboarding from zero just because the conversation is new.

## User-profile architecture

Generic schema:

```text
docs/architecture/schemas/user-profile.schema.json
```

Concrete active instance:

```text
user-data/profile.json
```

The profile is the canonical registry for concrete user/project identity, infrastructure, platform connections, publication preferences, **visual_preferences**, optional notification preferences/routing metadata and non-secret credential-lifecycle metadata. Rich strategy/content documents remain separate user-owned authorities referenced by or compatible with the profile.

Do not copy concrete profile values into generic capability/help/skill files.

Existing older project files such as `strategy/storage-workspace.md`, `wordpress/config/connections/**`, `wordpress/presentation/profiles/**`, `social/**` and `articles/**` remain user/project data and are excluded from the distributable skill package.

## Information gathering

Gather progressively, not as one giant questionnaire, but perform prerequisite discovery at the beginning rather than deferring integration requirements until first use.

Useful durable categories include:

- repository identity;
- site name/domain/URL;
- business/activity;
- offers;
- target audiences;
- geography/local-vs-remote constraints when relevant;
- conversion goals/CTAs;
- representative existing content;
- editorial tone and vocabulary;
- initial SEO priorities;
- asset/brand requirements;
- visual sourcing/fidelity/treatment preference;
- media-provider/workspace configuration;
- optional WordPress capability choice;
- optional social capability choice and account identities;
- publication timezone/hours when the user wants defaults;
- non-secret connection expiration metadata when providers expose it;
- optional publication-report channel/preferences when the user wants notifications.

Inspect existing sources first when doing so can answer a question safely. Ask the user when the value is subjective, private, strategic or cannot be verified reliably.

## Guided visual preference onboarding

When article/social visual generation is in scope and `visual_preferences` is missing or the user asks to change it, guide them in plain language rather than exposing enums first.

Resolve these durable decisions:

1. **Source preference** - should the skill normally generate with AI, prefer the user's real photos, require real photos for applicable subjects, or choose case by case?
2. **Strict-real subjects** - are products/work/portfolio/places/people required to stay faithful rather than be synthetically replaced?
3. **Treatment** - none, light correction, natural enhancement, marketing enhancement or creative transformation?
4. **Fidelity** - strict, high, moderate or flexible?
5. **Article vs social** - should either channel override the project default?
6. **Missing source** - ask before drafting, permit AI fallback, or continue without visuals?
7. **Local override** - explicitly explain that any article/post can override the project preference without changing it permanently.

Translate the answers into:

```yaml
visual_preferences:
  default:
    visual_source: ...
    missing_user_images_behavior: ...
    source_fidelity: ...
    ai_treatment: ...
    ai_treatment_directive: ...
  article: ... # optional partial override
  social: ...  # optional partial override
```

Before persisting a newly gathered preference, summarize it in ordinary language so the user understands the future behavior. Then persist/re-read it.

### Existing profiles created before the feature

If `visual_preferences` is absent in an otherwise valid older profile:

- do not rewrite the profile merely to claim migration success;
- report the visual preference as not yet explicitly configured;
- offer/resume this guided checkpoint at `/start` or when a creation workflow first needs the choice;
- a deterministic compatibility resolver may preserve the historical AI-first path where needed, but `configured=false` remains truthful until the user explicitly chooses a policy.

## Business model rule

Never force onboarding into one permanent binary such as `service OR product`. Offers are composable and the image model remains suitable for real product/portfolio/service assets across unrelated professions.

## Optional capabilities

### WordPress

Persist:

```yaml
wordpress:
  enabled: false
  publish_enabled: false
```

`publish_enabled` never authorizes a particular publication.

When WordPress or social publication is enabled, verify that the selected WordPress connection hosts a compatible operational SEO Workflow Bridge. In the current architecture that Bridge runtime is a prerequisite of automated LinkedIn/Facebook publication.

### Social

Persist availability/connection data under `social`. Platform publication-consent preferences belong to user/project data. External social publication still requires the gates declared by `social-publish` and the prerequisite graph from `runtime-compatibility-matrix.md`.

### Telegram publication reports

Telegram notifications remain optional. Inspect `notifications.telegram` before setup and reuse verified state where possible.

Secret boundary:

```text
TELEGRAM_BOT_TOKEN
-> GitHub Actions Repository Secret only
-> never chat
-> never user profile
-> never generic skill files
```

## Media provider selection

The generic media architecture is provider-neutral and supports:

```text
Google Drive (`google_drive`) - recommended/default when available
Dropbox (`dropbox`) - supported alternative
```

Onboarding must discover both providers when runtime tooling permits. If exactly one is operational, it may be selected after the user proceeds with that integration. If both are operational, present both choices and default to Google Drive unless the user chooses Dropbox. Persist exactly one active provider.

If a provider is discoverable and installable but not installed, propose installation during onboarding. If installed but not connected, guide connection immediately. If neither implemented provider is usable, report the exact state (or `eligibility_unknown` when it cannot be inspected) and enter the cloud-media DEGRADED state; do not propose GitHub, WordPress or local filesystem as alternatives.

Provider-specific behavior is defined by:

```text
docs/architecture/google-drive-workspace.md
docs/architecture/dropbox-workspace.md
```

Both adapters preserve the same logical site/content hierarchy:

```text
<provider-root>/<site-domain>/articles/
<provider-root>/<site-domain>/social/
<provider-root>/<site-domain>/tmp-outbox/
```

Content workflows create/reuse private `source-user/`, `proposals/` and `final/` children as needed. `source-user/` is never made public and originals are never overwritten.

For Google Drive, when the connector cannot set public sharing itself, instruct the user to configure `tmp-outbox` as `Anyone with the link -> Viewer`, then verify anonymous read-only access.

For Dropbox, use or guide creation of the active integration's supported public read-only shared-link mechanism only for staged `tmp-outbox` delivery material, then verify anonymous read-only access. Do not broaden sharing of source/proposal/final workspaces.

Normal onboarding must not require the user to create provider developer-console OAuth applications or paste provider access tokens when an operational ChatGPT/Codex integration exists.

## Image-generation runtime fallback

Image generation/editing capability is runtime state, not a permanent user preference.

When the active environment cannot generate/edit an image required by the owning visual workflow but cloud-media storage is operational:

1. preserve the exact article/post revision and visual policy;
2. generate a complete copy/paste prompt for an image-capable ChatGPT conversation or another compatible image AI;
3. include dimensions/format, approved brief, source/fidelity/treatment requirements, branding and prohibited elements;
4. ask the user to return/upload the generated result;
5. inspect the returned asset and continue through provider retention, proposal review where applicable, `asset-ingest` and `verified_final` creation.

Never claim the visual workflow complete from the prompt alone.

If cloud storage is also unavailable, the image may not become a durable final and publication remains blocked.

## Existing website/editorial learning

Observed content/image patterns are proposals until intentionally adopted as durable user/project rules. Do not silently convert every legacy inconsistency into a new strategy or visual preference.

## Completion semantics

Onboarding is complete for the enabled scope only when required user/project facts/configuration are persisted and required infrastructure checkpoints are verified.

A missing GitHub hard prerequisite makes onboarding BLOCKED. An inaccessible supported media workspace, unavailable image-generation runtime requiring manual handoff, failed anonymous tmp-outbox delivery, unverified WordPress/Bridge connection, unhealthy social credential or enabled-but-unverified notification channel remains explicit and resumable rather than silently complete.
