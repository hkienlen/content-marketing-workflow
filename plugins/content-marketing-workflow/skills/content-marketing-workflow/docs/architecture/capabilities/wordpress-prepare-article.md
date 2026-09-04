# Internal capability: wordpress-prepare-article

Date: 2026-09-01
Status: current implementation contract

## Purpose

`wordpress-prepare-article` is an optional internal capability of the single installable Content / Marketing skill.

It converts one fully validated GitHub article plus its exact verified final media into one **SEO Workflow Bridge-managed WordPress draft**, then verifies the resulting WordPress state.

It never publishes or schedules the article.

Final media may be provider-backed (`public_media_source`) or intentionally repository-backed (`repository_file`).

## Capability contract

```yaml
name: wordpress-prepare-article
purpose: Create or update one verified SEO Workflow Bridge-managed WordPress draft from an exact validated GitHub editorial source and exact verified final media.
availability: optional
feature_gate: wordpress.enabled
mode: mutating

prerequisites:
  - wordpress.enabled = true
  - wordpress-connect is fully verified for the selected connection
  - whole article is human_validated
  - every required final asset has durable verified identity/hash metadata
  - provider-backed final assets exist in the private final workspace
  - exact source article commit/path/blob are known
  - target connection_id is explicit
  - any required presentation profile is verified for reuse or is entering an explicit verification cycle

mandatory_context:
  - AGENTS.md
  - docs/architecture/persistence-contract.md
  - docs/architecture/testing-policy.md
  - docs/architecture/media-delivery-architecture.md
  - docs/architecture/wordpress-workflow-authority.md
  - docs/architecture/wordpress-generic-boundary.md
  - docs/architecture/wordpress-adapter-architecture.md
  - docs/architecture/wordpress-article-preparation.md
  - exact connection profile
  - exact validated article and final-media metadata
  - existing preparation manifest/state when present
  - selected presentation profile when required

reads:
  - validated article source at immutable Git identity
  - verified final-media durable records
  - provider private final files when public delivery staging is needed
  - connection profile
  - preparation manifest
  - presentation profile/reference data when required
  - existing Bridge-managed WordPress draft/readback

writes:
  - derived preparation manifest in GitHub
  - temporary delivery copies in tmp-outbox when required
  - Bridge-managed WordPress media attachments
  - one Bridge-managed WordPress draft
  - durable preparation state/evidence
  - presentation profile state when an onboarding/verification cycle is performed

persists:
  - exact source article identity
  - exact stable media identities and SHA-256 values
  - transient delivery identity only while needed for resume/debugging
  - manifest identity
  - target connection
  - WordPress post ID/status/slug/content hash
  - media IDs/URLs/reuse state
  - applied allowlisted metadata/taxonomies
  - selected presentation profile and verification state
  - blockers/diagnostic evidence when verification fails

external_side_effects:
  - copy provider-backed final media to tmp-outbox when anonymous delivery is required
  - upload/reuse exact verified final media through SEO Workflow Bridge
  - create or update one Bridge-managed draft through SEO Workflow Bridge
  - assign allowlisted metadata/taxonomies through SEO Workflow Bridge
  - read back and verify the managed draft
  - clean temporary tmp-outbox copies after verified delivery when practical

human_approval:
  - editorial article validation must already be explicit
  - final image selection must already be explicit
  - presentation/editor verification is required when the adapter/profile contract requires it
  - preparation authorization does not authorize publication
  - Divi/editor validation does not imply that the publication capability should start

validation:
  - exact target site/connection
  - source Git identities match immutable article bytes
  - each media record is either repository_file or public_media_source
  - provider-backed stable asset identity is distinct from temporary delivery identity
  - downloaded delivery bytes match the exact persisted SHA-256 before Bridge mutation
  - only verified final media is used
  - unmanaged slug collisions fail closed
  - managed source identity resolves to at most one post
  - managed post remains status=draft
  - final content/readback hashes and identities match declared preparation contract
  - required metadata/taxonomies/media match readback
  - presentation profile machine/human verification is satisfied where required

completion_conditions:
  - immutable/current preparation manifest exists
  - all source/media identities verified
  - all required media are created/reused by the Bridge with expected identity/hash
  - one managed WordPress draft exists or was idempotently updated
  - status is exactly draft
  - technical readback passes
  - required presentation review passes or is explicitly reported as the remaining gate
  - durable preparation state is synchronized
  - temporary delivery cleanup is completed or truthfully recorded as pending
  - no publication occurred
  - after successful Divi/editor validation, this capability may terminate successfully with the article remaining draft when publication was not requested

next_actions:
  - human presentation/editor review when required
  - stop with validated draft when publication is not currently requested
  - wordpress-publish-article only after an explicit publication-stage request
```

## Canonical flow

```text
validated GitHub article
+ verified final-media records
+ verified WordPress connection
        ↓
for provider-backed media:
private final -> tmp-outbox delivery copy
        ↓
derive/persist preparation manifest
        ↓
GitHub Actions downloads delivery bytes anonymously
        ↓
validate image/MIME/size/SHA-256
        ↓
SEO Workflow Bridge media_upsert using stable asset identity
        ↓
render/adapter transform
        ↓
SEO Workflow Bridge article_prepare
        ↓
SEO Workflow Bridge article_read
        ↓
exact technical verification
        ↓
tmp-outbox cleanup when practical
        ↓
human presentation/editor verification when required
        ↓
prepared + validated draft
        ↓
STOP unless publication was explicitly requested
```

Historical direct-import/injection scripts are not part of this canonical flow.

## Source-of-truth boundary

GitHub remains the editorial/workflow source of truth.

For provider-backed media, GitHub holds exact durable identity/hash/metadata while the retained private final binary remains in the configured provider workspace.

The WordPress draft and media library are derived publication representations.

When final WordPress presentation intentionally changes serialized `post_content`, publication eligibility is captured from the exact post-validation WordPress draft **only when the publication capability is subsequently invoked**.

## Preparation manifest

Canonical path:

```text
wordpress/prepare/manifests/<connection_id>/<article-slug>.json
```

Current provider-aware schema:

```text
wordpress/prepare/manifest-schema-v3.json
```

Manifest v3 supports per-media source types:

```text
repository_file
public_media_source
```

The article source remains pinned through immutable Git identity.

For provider-backed media, the manifest pins:

- stable provider `asset_id` from the private final asset;
- temporary public delivery file/URL;
- exact SHA-256;
- canonical filename/MIME;
- human-validated ALT/title/caption/placement.

Keep `manifest_commit` separate from `source.article_commit`; do not create a self-referential Git contract.

Manifest v2 remains readable for existing repository-backed preparation state.

## Provider-backed media rules

Only assets that reached:

```text
selected -> normalized -> verified_final
```

may be staged for WordPress.

For each `public_media_source`:

1. stable `asset_id` must identify the retained private final asset;
2. `delivery.file_id` / `delivery_url` identify only the temporary public delivery object;
3. GitHub Actions downloads the delivery object without provider credentials;
4. downloaded bytes must match declared SHA-256 and supported image signature/MIME;
5. Bridge managed identity is derived from stable `asset_id`, not delivery copy ID;
6. same stable identity + same SHA -> reuse;
7. same stable identity + different SHA -> fail closed unless an explicit replacement contract has authorized new durable identity/state.

Rejected proposals never enter WordPress.

## Repository-backed compatibility

Existing `repository_file` media remains valid.

Repository-backed behavior stays conservative:

- exact repository path/blob is verified;
- exact bytes are hashed before Bridge mutation;
- same managed path + same content hash -> reuse;
- same managed path + different bytes -> fail closed unless explicitly replaced.

Do not silently convert a provider-backed failure into repository-backed media.

## Managed draft identity and collision safety

Stable preparation identity is the durable repository source article path.

Required behavior:

- rerun updates the same Bridge-managed draft;
- slug changes do not silently create a second draft for the same source path;
- multiple managed posts for one source path block execution;
- unmanaged content owning the target slug blocks execution;
- a Bridge-managed post that is no longer `draft` is immutable through preparation.

Preparation always writes `post_status = draft`.

## Presentation adapters/profiles

Provider-specific presentation belongs to `docs/architecture/wordpress-adapter-architecture.md`.

The generic capability does not hardcode Divi, Gutenberg, Elementor, Bricks, Yoast or another provider.

For the pilot, the current profile is persisted under:

```text
wordpress/presentation/profiles/<connection_id>/<profile-id>.json
```

A profile claiming page-builder fidelity is reusable only after required real editor/preview verification reaches durable human-verified state.

## Bridge permissions

Keep WordPress permissions separated:

```text
Read content
Connection-test writes
Article draft preparation
Article publication
```

Preparation never uses publication permission as a shortcut.

## Verification

Machine verification must check at least:

- exact target site;
- one expected managed post ID;
- `status = draft`;
- expected title/slug;
- exact source path/commit/hash identity;
- exact expected media IDs/URLs/hashes where returned;
- final content hash according to active renderer/adapter contract;
- featured media;
- required allowlisted metadata/taxonomies;
- direct managed WordPress media URLs;
- no unresolved renderer/template tokens or literal Markdown artifacts.

If machine verification fails after a draft write, preserve the known draft ID and blocker. Correct and rerun idempotently; do not automatically delete or publish the draft.

## Publication separation

The following statements are never equivalent:

```text
article validé
brouillon WordPress préparé
Divi/editor OK
publication demandée
publication autorisée maintenant
```

`wordpress-prepare-article` stops at a verified/validated draft. Publication belongs exclusively to `wordpress-publish-article`, which is invoked only after explicit publication intent and then requires its independent candidate/preflight/runtime gate.
