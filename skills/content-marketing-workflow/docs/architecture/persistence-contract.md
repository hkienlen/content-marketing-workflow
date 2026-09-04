# Durable persistence contract

Date: 2026-09-04
Status: architecture contract

## Purpose

This document defines persistence rules for the single installable Content / Marketing skill.

The skill may expose several internal capabilities, but durable information must behave consistently across them and must respect the boundary:

```text
skill = generic models/contracts/behavior
user/project data = concrete values/state/content/connections/preferences
```

See `docs/architecture/user-profile-data-contract.md`.

GitHub is the durable source of truth for non-secret project/user rules, validated editorial content, workflow state, media source/final identities/metadata/hashes/provenance and external-result evidence. Provider workspaces such as Google Drive retain source originals, generated/reviewed assets and validated final binaries. External systems such as WordPress and social networks may hold operational/published copies, but non-secret metadata that affects future behavior is synchronized to user/project data.

Conversation memory is not durable storage.

## Core invariant

> If information is required for correct behavior in a future independent execution, it must be recoverable from user/project data in GitHub or from an explicitly referenced durable external system.

The user expresses intent. The skill is responsible for persistence, consistency, traceability and verification.

## User-profile registry

Generic schema:

```text
docs/architecture/schemas/user-profile.schema.json
```

Concrete instance convention:

```text
user-data/profile.json
```

The active profile is the canonical registry for user/project identity and infrastructure/preferences such as:

- repository identity;
- site domain/URL;
- WordPress connection identity/non-secret endpoints;
- media provider/workspace references;
- structured `visual_preferences` including global default plus article/social overrides;
- social accounts/remote IDs;
- preferred publication timezone/hours;
- standing publication-consent preferences;
- credential type and **non-secret** expiry/data-access-expiry metadata;
- connection-health/renewal state;
- authority pointers to richer business/SEO/editorial/social documents.

The profile does not replace rich content/strategy authorities. It locates and coordinates them.

A generic skill contract/schema must never be edited merely to save one user's concrete value.

## Durable information

Examples include:

- user/project/site identity;
- configured GitHub repository references;
- media provider/workspace and non-secret folder references;
- business/activity description;
- offers and target audiences;
- editorial tone/vocabulary rules;
- SEO/internal-linking/image/social rules;
- structured project visual-source/fidelity/treatment preferences;
- content-local visual policy overrides that must survive a later run;
- optional capability activation;
- WordPress/social connection state;
- social account IDs/names and publication preferences;
- token/data-access expiration timestamps and last observed credential validity, **without token values**;
- content identifiers/lifecycle states;
- article/post relationships;
- verified user-provided source-image provenance/role/identity/hash when available;
- image proposal/final selection state;
- stable final-media identity/hash/MIME/dimensions;
- scheduling and publication authorization metadata;
- external publication IDs/URLs/timestamps/evidence;
- validated changes to reusable workflow behavior.

A mutating capability is not complete until the durable information it owns has been persisted and verified.

## Transient information

Examples include rejected brainstorm variants, temporary debug output, one-off instructions limited to one content item when they are no longer needed for resume, intermediate generation files and temporary `tmp-outbox` delivery copies.

A one-off visual override that still governs an unfinished article/post is durable **content-item state** until the workflow no longer needs it. It must not be promoted to a project preference unless the user says so.

Drive presence alone does not make a source verified/inspected or a proposal final. A `tmp-outbox` copy is transport state only and never replaces the stable retained-final identity.

## Scope classification

Whenever information may affect future behavior, classify it as:

1. generic skill/model behavior;
2. user-global durable fact/preference;
3. project/site durable fact/preference;
4. content-item durable state;
5. derived/index/compatibility state;
6. transient task context;
7. secret/credential material.

If one-off versus durable scope materially changes future behavior and cannot be inferred, ask one concise clarification.

For visual behavior:

```text
"Always prefer my photos" -> project/user preference
"For social, use my photos first" -> project social override
"For this post only, generate with AI" -> content-item local override
"Use this uploaded photo as the exact product reference" -> content-item source provenance/role
```

## Authoritative locations

- reusable cross-user invariants/models -> `AGENTS.md`, `docs/architecture/**`, reusable code;
- user/project identity/infrastructure/preferences/connection-health -> `user-data/profile.json`;
- structured project visual preference -> `projects.<active_project>.visual_preferences` in the active profile;
- business/SEO/editorial/image/social prose rules -> corresponding **user-owned** `strategy/**` authorities referenced by the profile;
- articles/posts, local overrides and source provenance -> user/project content/state files;
- user-provided source originals -> configured provider private `source-user/` workspace when provider-backed retention is used;
- final media binary -> configured provider private final workspace when provider-backed mode is used;
- final media durable identity/hash/provenance -> owning user/project content/state/manifest;
- temporary delivery -> configured `tmp-outbox`;
- WordPress operational connection/presentation/manifests -> user/project `wordpress/config/**`, `wordpress/presentation/**`, etc. when compatibility/runtime requires them;
- external publication metadata -> corresponding user/project content/state record;
- credentials/secrets -> external credential/token systems only, never Git.

Derived compatibility projections may mirror authoritative profile values only when a runtime workflow requires them. Direction of authority must be documented; divergence is an error.

## Skill packaging boundary

The distributable skill contains reusable schemas/contracts/behavior, not one user's dataset.

User/project directories and pilot evidence must be excluded from skill packaging, including at least:

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
project-specific checkpoints/handoffs/live-validation evidence
```

Reusable companion source such as `wordpress/bridge-plugin/**` remains skill code.

## Credential lifecycle metadata

Secrets never go into the profile, but operational metadata does. Generic example:

```yaml
credential:
  kind: oauth_access_token
  secret_location: wordpress_seo_workflow_bridge
  token_expires_at: <provider-returned-expiry-or-null>
  data_access_expires_at: <provider-returned-data-access-expiry-or-null>
  last_observed_valid: true
  last_observed_at: <observation-timestamp>
```

This allows the generic `social-connection-health` capability to warn/guide renewal without seeing the raw credential.

## Media persistence boundary

The authoritative media architecture is `docs/architecture/media-delivery-architecture.md` and user-source intake is additionally governed by `docs/architecture/user-provided-images.md`.

Provider-backed source lifecycle:

```text
source_discovered -> source_verified -> source_inspected
```

Provider-backed final lifecycle:

```text
proposed/treated -> selected -> normalized -> verified_final -> delivery_staged -> destination_verified
```

A content item using user-provided media must retain enough provenance to distinguish the source original from generated/treated derivatives. Never overwrite the original as part of normalization/finalization.

For `verified_final`, user/project state must retain provider, asset ID, filename, SHA-256, MIME, dimensions and owning ALT/title/caption/placement/validation state plus source provenance/reference when applicable. Git binary compatibility mode remains explicit rather than automatic.

## Completion sequence for mutating capabilities

Before reporting completion:

1. classify every new/changed durable value;
2. choose user profile, richer user authority or generic skill contract as appropriate;
3. write/update authoritative state;
4. synchronize required compatibility projections;
5. validate consistency/schema;
6. record Git traceability;
7. re-read/verify the result;
8. report the meaningful outcome.

Producing a correct answer in chat is insufficient when durable mutation is required.

## Cross-capability persistence

Persistence is not delegated to a separate maintenance command. Onboarding, visual-source resolution, SEO/article/social workflows, WordPress connection/publication and social connection-health all persist the durable state they create or discover.

A production lesson that changes the reusable **model/behavior** updates the skill contract/schema. A concrete user's value updates user/project data only.

## Git traceability

All durable GitHub mutations are traceable. Branch/commit/PR mechanics are transparent after onboarding under `docs/architecture/github-transparency.md`; they do not create extra user gates. Machine-generated operational health metadata may use the explicitly designed low-friction daily workflow.

Never rewrite immutable content IDs merely because scheduling/credential dates change.

## External side effects

For externally durable actions:

1. enforce feature/prerequisite/approval gates;
2. verify actual external result;
3. persist non-secret identifiers/status/URLs/timestamps needed later;
4. verify repository synchronization.

A read-only credential health probe is not publication and does not renew a credential automatically.

Image intake, treatment and final selection are not publication authorization.

## Secrets

Never store in Git:

- passwords;
- API/client/app secrets;
- access/refresh tokens;
- WordPress Application Passwords;
- OAuth authorization codes;
- private keys;
- cookies/authorization headers;
- other reusable credentials.

Opaque IDs, folder IDs, public delivery URLs, scopes and expiry metadata are non-secret operational metadata when required.

## Failure behavior

If required persistence fails, do not claim completion and do not use conversation memory as substitute. Preserve valid prior state, record the highest truthful incomplete state where possible and keep recovery resumable/idempotent.

A provider/download failure must not silently substitute a different binary. A missing required user source must not silently become a synthetic replacement when the effective policy forbids it.

## User-facing reporting

The user receives concise operational results, not repository bookkeeping instructions. They must not normally edit files, maintain indexes, run Git commands or manually verify routine persistence.

When source images are requested in Drive, the user-facing exception is purposeful business input: show the exact canonical `source-user/` path and the verified direct Drive folder link as defined by `docs/architecture/user-provided-images.md`.
