# Internal capability: wordpress-prepare-article

Date: 2026-09-05
Status: current implementation contract

## Purpose

`wordpress-prepare-article` converts one fully validated GitHub article plus its exact required verified final media into one SEO Workflow Bridge-managed WordPress draft, then verifies the resulting WordPress state.

Global prerequisite/degradation behavior is owned by:

```text
docs/architecture/runtime-compatibility-matrix.md
```

Strict invariant for the current product:

```text
required verified final media missing
=> do not prepare the article for WordPress publication
```

There is no image-less WordPress fallback.

## Capability contract

```yaml
name: wordpress-prepare-article
purpose: Create/update one verified SEO Workflow Bridge-managed WordPress draft from exact validated GitHub source plus required exact verified final media.
availability: optional
feature_gate: wordpress.enabled
mode: mutating

prerequisites:
  - wordpress.enabled = true
  - github_repository is operational
  - cloud_media_storage is operational for current provider-backed media workflow
  - wordpress_bridge_runtime is verified for selected connection
  - whole article is human_validated
  - every required final asset has durable verified identity/hash metadata
  - provider-backed final assets exist in private final workspace
  - exact source article commit/path/blob are known
  - target connection_id is explicit
  - required presentation profile is verified or entering explicit verification cycle

mandatory_context:
  - AGENTS.md
  - docs/architecture/runtime-compatibility-matrix.md
  - docs/architecture/persistence-contract.md
  - docs/architecture/media-delivery-architecture.md
  - docs/architecture/wordpress-workflow-authority.md
  - docs/architecture/wordpress-adapter-architecture.md
  - exact connection profile
  - exact validated article and final-media metadata
  - existing preparation manifest/state when present

reads:
  - immutable validated article source
  - verified provider-backed final-media records/files
  - WordPress/Bridge connection profile
  - preparation/presentation state
  - existing Bridge-managed draft/readback

writes:
  - derived preparation manifest in GitHub
  - temporary delivery copies in configured tmp-outbox
  - Bridge-managed WordPress media attachments
  - one Bridge-managed WordPress draft
  - durable preparation/readback evidence

external_side_effects:
  - stage exact provider-backed finals through tmp-outbox
  - upload/reuse exact media through SEO Workflow Bridge
  - create/update one Bridge-managed draft
  - read back and verify
  - clean tmp-outbox copies when practical

validation:
  - runtime prerequisites satisfy central compatibility matrix
  - exact target site/connection
  - source Git identities match immutable bytes
  - each newly prepared media record uses provider-backed public delivery from exact verified final
  - provider stable identity differs from temporary delivery identity
  - downloaded bytes match persisted SHA-256 before Bridge mutation
  - only verified final media is used
  - managed post remains draft
  - required metadata/taxonomies/media/readback match
  - no image-less fallback occurs

completion_conditions:
  - preparation manifest exists
  - all required media identities verified
  - all required media created/reused by Bridge with expected identity/hash
  - one managed WordPress draft exists and status is draft
  - technical readback passes
  - required presentation review passes or remains explicit gate
  - no publication occurred
```

## Canonical flow

```text
validated GitHub article
+ required verified provider-backed final media
+ verified WordPress/SEO Workflow Bridge runtime
        ↓
private final -> exact tmp-outbox copy
        ↓
manifest + hash verification
        ↓
SEO Workflow Bridge media_upsert
        ↓
SEO Workflow Bridge article_prepare
        ↓
article_read verification
        ↓
cleanup temporary delivery
        ↓
human presentation/editor verification
        ↓
prepared validated draft
        ↓
STOP unless publication explicitly requested
```

## Media source policy

For new/current provider-backed preparation, canonical media source is `public_media_source` derived from the configured cloud-media provider.

Legacy manifests containing `repository_file` remain readable only for explicit backward compatibility/migration. Rules:

- never select `repository_file` for new media because cloud storage failed;
- never convert provider failure into GitHub binary storage;
- never treat legacy repository media as evidence that `cloud_media_storage` is operational;
- any explicit migration preserves exact hashes/provenance.

## Source-of-truth boundary

GitHub remains editorial/workflow truth. Provider workspace retains private final binary. WordPress draft/media library are derived publication representations and are not CMW storage fallback.

## Provider-backed media rules

Only assets that reached:

```text
selected -> normalized -> verified_final
```

may be staged.

Stable provider `asset_id` identifies private final; delivery file/URL identifies only temporary outbox copy. Same stable identity + changed bytes fails closed unless explicit replacement contract authorizes new state.

## Managed draft safety

Reruns update the same Bridge-managed draft. Slug/source collisions fail closed. Preparation writes `post_status=draft` only and never publishes.

## Publication separation

These are distinct:

```text
article validated
WordPress draft prepared
WordPress/editor OK
publication requested
publication authorized now
```

Actual publication belongs exclusively to `wordpress-publish-article` and requires its independent gates.
