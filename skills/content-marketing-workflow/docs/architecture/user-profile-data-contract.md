# User profile data contract

Date: 2026-09-06
Status: normative architecture contract

## Purpose

The installable Content Marketing Workflow Skill owns models and behavior, not one user's durable values.

All durable values describing a user/project/site, repository, cloud-media workspace, WordPress/Bridge connection, social accounts, visual preferences, **visual identity/brand assets**, publication preferences, credential-expiration metadata, connection-health state, runtime compatibility checkpoints or notification preferences belong to user/project data.

## Primary invariant

```text
skill package
= generic contracts + schemas + capability logic + reusable companion code

user data
= actual user/site/repository/preferences/connections/IDs/health/compatibility/workflow state
```

A new installation starts from empty/default project data and discovers/gathers values. It never inherits pilot-user values.

## Canonical profile model

Generic schema:

```text
docs/architecture/schemas/user-profile.schema.json
```

Typical project instance:

```text
user-data/profile.json
```

The profile is the canonical registry for infrastructure/preference metadata needed across capabilities. Rich strategy documents may remain separate authorities referenced by the profile.

## Runtime compatibility persistence

Global compatibility behavior is normative in:

```text
docs/architecture/runtime-compatibility-matrix.md
```

The schema supports optional project-level runtime compatibility state such as:

```yaml
runtime_compatibility:
  overall_status: READY|DEGRADED|BLOCKED|UNKNOWN
  checked_at: <timestamp>
  cloud_media_storage:
    provider: google_drive|dropbox
    state: operational|...
    operational: true|false|null
    last_checked_at: <timestamp>
  wordpress_bridge_runtime:
    state: operational|...
  github_actions_scheduler:
    state: operational|...
  blockers: []
  degraded_features: []
```

Persist only non-secret, future-relevant observations. This persisted projection is a resume aid, not proof that the current conversation exposes the same tools.

### Ephemeral surface capabilities

Whether the **current ChatGPT/Codex conversation can generate/edit images** is runtime/surface state and must be re-detected when needed. It is intentionally not a permanent `runtime_compatibility.image_generation=true` preference in the schema.

Similarly, plugin eligibility may change with account/workspace/runtime. Persisting the last observation never replaces fresh discovery when the capability is needed.

## Cloud-media storage selection

CMW implements:

```text
google_drive
dropbox
```

Exactly one provider is active per project. The durable project profile/state must preserve the selected provider and provider-specific non-secret workspace references required for exact resume.

Conceptual project storage state:

```yaml
storage:
  cloud_media_storage:
    provider: google_drive|dropbox
    root_ref: <provider root identity/reference>
    site_ref: <site workspace identity/reference>
    brand_ref: <private brand workspace identity/reference when configured>
    articles_ref: <articles workspace identity/reference>
    social_ref: <social workspace identity/reference>
    tmp_outbox_ref: <outbox identity/reference>
    tmp_outbox_link: <public read-only delivery link when configured/needed>
    verified_at: <timestamp>
```

Provider-specific IDs/paths/links may differ. Do not force a Google Drive ID shape onto Dropbox or vice versa.

Google Drive remains the recommended/default choice when both providers are operational, but the selected value is user/project state, not a generic hard-coded default that silently overrides an existing Dropbox project.

Switching provider is an explicit migration/configuration operation. Existing source/final/brand provider identities must be migrated/rebound with exact hash/provenance verification; they are never reinterpreted under the new provider namespace.

## User-data categories

User/project data includes:

- profile/project IDs;
- GitHub repository identity/default branch;

For `/status`, the primary durable authority for the active project repository name is `projects[active_project_id].repository.full_name`. This user/project value must never be replaced by the CMW product repository or marketplace source repository simply because that is where the Skill was installed from.
- site domain/name/URLs;
- selected cloud-media provider and workspace/folder/file references;
- runtime compatibility checkpoints/blockers and last verification timestamps;
- WordPress site/Bridge connection IDs and non-secret relay endpoints/audience;
- audiences/offers/editorial/SEO preferences;
- project visual sourcing/fidelity/treatment preferences and overrides;
- project visual identity, official logo registry and independent article/social logo policy;
- user-owned rich visual directives/strategy;
- source-image provenance attached to durable content;
- content-local visual/logo/directive overrides;
- social enablement/platform accounts/remote IDs;
- observed scopes/application/configuration IDs belonging to user's integration;
- publication timezone/hours and consent preferences;
- non-secret token/data-access expiry and connection health;
- notification preferences/routing/verification timestamps;
- content/article/post/publication/verification evidence.

## Visual preferences

The project may persist:

```yaml
visual_preferences:
  default:
    visual_source: ai_first|user_images_first|strict_user_images|hybrid_best_fit
    missing_user_images_behavior: ask_before_drafting|allow_ai_generation|continue_without_visuals
    source_fidelity: strict|high|moderate|flexible
    ai_treatment: none|light_correction|natural_enhancement|marketing_enhancement|creative_transformation
    ai_treatment_directive: <string-or-null>
  article: <partial override, optional>
  social: <partial override, optional>
```

Content-local source/treatment overrides belong to owning article/post state and must not silently mutate project defaults.

## Visual identity and logo policy

Brand identity is distinct from source/treatment preference.

Canonical structured state:

```yaml
visual_identity:
  guidelines_path: strategy/visual-guidelines.md
  logo_policy:
    article: always|auto|never
    social: always|auto|never
  logo_assets:
    primary: <optional verified provider-backed asset>
    light: <optional verified provider-backed asset>
    dark: <optional verified provider-backed asset>
  configured_at: <timestamp>
  updated_at: <timestamp>
```

### Article and social are independent

`logo_policy.article` and `logo_policy.social` are two separate durable preferences.

A user may choose, for example:

```yaml
logo_policy:
  article: never
  social: always
```

Changing one field must preserve the other exactly unless the user explicitly requests both to change.

Do not infer that a user who wants a logo on social posts also wants it on article images, or vice versa.

### Logo assets

Official logos are user-owned brand assets. Prefer verified provider-backed originals in the private project `brand/` workspace and persist provider-qualified identity/hash/metadata in the profile.

A user may provide one logo or multiple variants (`primary`, `light`, `dark`). Light/dark variants are recommended when available but are not mandatory.

Raw image bytes do not belong in JSON. The profile stores references/metadata only.

Logo integrity/application is governed by:

```text
docs/architecture/brand-assets-contract.md
```

### Rich visual directives

Structured enums do not attempt to encode every creative preference.

The profile may point to the user-owned authority:

```text
strategy/visual-guidelines.md
```

That file may contain global/article/social style rules, palette guidance, people/representation preferences, preferred/forbidden visual families, text-in-image rules, brand placement guidance and arbitrary permanent user directives.

The generic Skill must not package the user's concrete `strategy/visual-guidelines.md`.

Conflict/precedence behavior is defined in `docs/architecture/visual-generation-contract.md`: user creative directives override conflicting generic CMW creative defaults, while workflow/integrity invariants remain authoritative.

### Existing profiles

Older profiles may have `visual_preferences` but no `visual_identity`.

Do not silently convert absence into a confirmed logo preference. Runtime compatibility may preserve historical no-logo behavior while reporting `visual_identity.configured=false`/equivalent, then `/start` or `/visual configure` gathers the article and social choices separately.

## Source provenance

When user-provided image becomes durable input, persist provenance in content state, for example:

```yaml
source_type: user_provided
source_provider: google_drive|dropbox|chat_upload
source_asset_id: <provider identity when available>
source_original_filename: <original filename>
source_sha256: <exact bytes when available>
source_role: use_as_is|enhance|subject_reference|inspiration_reference|composition_input
source_fidelity: strict|high|moderate|flexible
ai_treatment: none|light_correction|natural_enhancement|marketing_enhancement|creative_transformation
```

Provider folder/file IDs/paths/links used for resume are non-secret user/project state.

Final media records must also persist the provider name because provider identity is part of the stable asset namespace:

```yaml
provider: google_drive|dropbox
asset_id: <provider-qualified final identity/reference>
sha256: <exact final bytes>
```

When a logo is present in a final, owning content state should retain enough effective-contract evidence to identify the applied logo asset/version/policy source without duplicating raw logo data.

## Storage/provider boundary

The profile may select/configure `cloud_media_storage` as `google_drive` or `dropbox`.

GitHub, WordPress and local filesystem are not alternate media-storage provider choices. Legacy repository-backed media compatibility belongs to explicit migration/content state and must not be represented as cloud-media readiness.

## Secrets

Raw credentials never belong in profile or committed GitHub content, including access/refresh tokens, app secrets, passwords, authorization codes, cookies/private keys, Telegram bot tokens and mail/API secrets.

The profile may retain non-secret credential owner/name/reference and lifecycle metadata.

Provider OAuth/access tokens for Google Drive or Dropbox are owned by the active integration/runtime and are never persisted in GitHub user/project data.

## Compatibility projections

Existing project files such as `strategy/**`, `wordpress/config/**`, `social/**`, `articles/**` remain user/project data. When profile mirrors a value needed by runtime code, declare one canonical authority and keep projections consistent.

Do not create silent divergent copies.

For visual configuration specifically:

- `visual_preferences` owns structured source/fidelity/treatment/missing-source fields;
- `visual_identity` owns structured logo assets, independent article/social logo policy and the rich-guidelines pointer;
- `strategy/visual-guidelines.md` owns rich user creative prose;
- content item state owns local overrides and source/final/effective-contract provenance.

## Packaging boundary

A distributable Skill must not package user/project data, including:

```text
user-data/**
strategy/**
articles/**
social/**
wordpress/config/**
wordpress/presentation/profiles/**
wordpress/prepare/manifests/**
wordpress/publish/**
work-context/**
project-specific checkpoints/handoffs/live evidence
user logo/media assets
```

Reusable WordPress Bridge source remains skill companion code.

## Persistence behavior

When a capability discovers/receives durable user value:

1. classify it as user/project data;
2. write it to profile or referenced richer authority;
3. update compatibility projection atomically where applicable;
4. verify provider-qualified identities and schema/consistency;
5. never modify generic skill contracts just to save one user's value.

When a durable visual directive is free-form, preserve it in the user's rich authority with the correct scope instead of forcing it into unrelated structured fields.

Runtime-only facts must be re-detected rather than promoted into permanent preferences.

## Multi-project rule

Site-specific repository/storage/visual/brand/social/notification/compatibility state belongs under its project. Do not promote it globally unless user explicitly requests global scope.

## References

- `docs/architecture/runtime-compatibility-matrix.md`
- `docs/architecture/persistence-contract.md`
- `docs/architecture/capabilities/start.md`
- `docs/architecture/capabilities/visual-configure.md`
- `docs/architecture/visual-generation-contract.md`
- `docs/architecture/brand-assets-contract.md`
- `docs/architecture/google-drive-workspace.md`
- `docs/architecture/dropbox-workspace.md`
- `docs/architecture/schemas/user-profile.schema.json`
- `docs/architecture/user-provided-images.md`
- `docs/architecture/capabilities/social-connection-health.md`
- `docs/architecture/capabilities/telegram-publication-notifications.md`
- `docs/architecture/skill-package-boundary.md`
