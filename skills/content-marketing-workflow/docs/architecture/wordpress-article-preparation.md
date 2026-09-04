# WordPress article preparation architecture

Date: 2026-09-01
Status: living architecture document

## Authority

This document defines the generic preparation stage used by `docs/architecture/capabilities/wordpress-prepare-article.md`.

The current companion path is defined by `docs/architecture/wordpress-workflow-authority.md` and media delivery by `docs/architecture/media-delivery-architecture.md`.

SEO Workflow Bridge is the current WordPress-side application boundary. Historical direct-import scripts are not part of normal preparation.

## Purpose

Prepare one exact human-validated repository article plus exact verified final media as a **Bridge-managed WordPress draft** on one selected connection.

Preparation does not publish, schedule, clone, promote or delete the real article.

```text
validated GitHub editorial source
+ verified final-media identities/hashes
        ↓
derived immutable preparation manifest
        ↓
media delivery resolution
        ↓
GitHub Actions / selected transport
        ↓
SEO Workflow Bridge
        ↓
managed media + managed draft
        ↓
exact readback
        ↓
required presentation review
        ↓
prepared draft
        ↓
STOP
```

## Generic boundary

Do not assume test/staging/prod semantics, clone/promotion lifecycle, a specific builder/SEO plugin, author/category, pilot preset IDs or one media provider.

Presentation providers belong to `docs/architecture/wordpress-adapter-architecture.md`.

Media providers belong to `docs/architecture/media-delivery-architecture.md`.

## Prerequisite state

Normal preparation requires:

- `wordpress.enabled = true`;
- fully verified WordPress connection;
- article state `human_validated`;
- every required image at `verified_final` with stable identity/hash metadata;
- exact Git source commit/path/blob identity;
- selected connection ID;
- required presentation profile in usable state.

A provider-backed final does not need its binary committed in GitHub.

## Preparation manifests

Canonical path:

```text
wordpress/prepare/manifests/<connection_id>/<article-slug>.json
```

Current provider-aware schema:

```text
wordpress/prepare/manifest-schema-v3.json
```

Existing repository-backed manifests remain supported through:

```text
wordpress/prepare/manifest-schema-v2.json
```

### Immutable identities

Keep distinct:

```text
manifest_commit
= immutable Git commit containing derived manifest

source.article_commit
= immutable Git commit containing validated article source
```

A manifest never contains the SHA of the same commit that contains itself.

The article remains pinned by Git blob identity.

Provider-backed media is pinned by stable provider asset identity and exact SHA-256 rather than Git blob identity.

## Manifest v3 media model

Each v3 media entry contains:

```text
key
source
title
alt
caption (optional)
placement (optional)
```

`source` is exactly one of:

```text
repository_file
public_media_source
```

### `repository_file`

Pins:

```text
path
git_blob_sha
```

The orchestrator reads exact bytes from the pinned article source commit and computes SHA-256 before Bridge mutation.

### `public_media_source`

Pins stable final identity separately from delivery identity.

Conceptual shape:

```yaml
source:
  type: public_media_source
  provider: google_drive
  asset_id: <private-final-file-id>
  filename: image.webp
  sha256: <exact-final-bytes>
  mime_type: image/webp
  width: 1600
  height: 900
  size_bytes: 123456
  delivery:
    file_id: <temporary-tmp-outbox-copy-id>
    delivery_url: https://...
```

`asset_id` is durable final identity.

`delivery.file_id` and `delivery_url` are transport identity and may change when the outbox copy is recreated.

The WordPress managed-media identity must stay stable while `provider + asset_id + filename` stays stable.

## Provider-aware orchestration

The stable workflow entrypoint remains:

```text
scripts/wordpress-relay-prepare-v3.py
```

Normal preparation delegates to:

```text
scripts/wordpress-relay-prepare-v6.py
```

Behavior:

- manifest v2 -> delegates unchanged to v5;
- manifest v3 repository media -> verified as repository-backed;
- manifest v3 public media -> downloaded/verified through `scripts/media-source-fetch.py` before Bridge mutation.

The provider-aware layer exposes verified public media to the existing preparation core through an in-memory deterministic synthetic path:

```text
assets/external-media/<provider>/<hash-of-stable-asset-id>/<filename>
```

This synthetic managed path derives from stable `asset_id`, not the temporary delivery copy ID.

Therefore recreating `tmp-outbox` delivery objects does not by itself create duplicate WordPress attachments.

No external provider bytes are committed into Git merely to satisfy the compatibility core.

## Public-media verification

Before `media_upsert`, the downloader must:

1. accept a declared supported provider;
2. validate provider URL/ID consistency;
3. fetch without provider credentials where the selected delivery mode requires public access;
4. reject empty/HTML/non-image responses;
5. enforce size limits;
6. verify actual image signature/MIME;
7. calculate SHA-256;
8. compare exact expected SHA-256;
9. fail closed on mismatch.

For unchanged media:

```text
same stable asset identity + same SHA-256 -> Bridge reuse
```

For drift:

```text
same stable asset identity + different SHA-256 -> fail closed
```

unless a separate explicit replacement contract has durably authorized the new final asset state.

## `tmp-outbox` staging

For Google Drive, a downstream preparation workflow may copy required private finals into:

```text
<drive-root>/<site-domain>/tmp-outbox/
```

The outbox is configured `Anyone with the link -> Viewer` and used only for temporary delivery.

After verified WordPress media/draft success, the orchestrating skill should delete the temporary delivery copies when practical. The private retained finals remain untouched.

## Public-content boundary

The article source may include internal production instructions after the public body.

Manifest preprocessing may deterministically:

- strip YAML front matter;
- strip source H1 when theme owns it;
- stop before an exact production-only marker.

A configured marker that cannot be found is a hard failure.

## Rendering modes

Current content modes remain:

```text
github_markdown
repository_file
```

### `github_markdown`

```text
preprocess clean public Markdown
-> render Markdown to HTML
-> inject Bridge-managed WordPress media HTML
-> optional bounded adapter transform
-> article_prepare
```

Do not inject WordPress image HTML into Markdown before rendering.

### `repository_file`

Used when a deterministic repository-backed presentation renderer/profile supplies final `post_content` representation.

Current pilot may use it with a pinned presentation profile and `divi_shortcode_v1` adapter.

## Presentation profiles

Profiles live under:

```text
wordpress/presentation/profiles/<connection_id>/<profile-id>.json
```

The manifest pins profile path and Git blob SHA when required.

Builder fidelity requires the machine/human checks declared by the adapter/profile contract.

## Draft identity/idempotency

Stable managed-draft identity remains:

```text
source.article_path
```

Required behavior:

- rerun updates same managed draft;
- slug change does not create second draft for same source path;
- duplicate managed posts block;
- unmanaged target-slug collision blocks;
- managed post no longer `draft` cannot be modified by preparation;
- preparation forces `post_status = draft`.

## Bridge permissions

SEO Workflow Bridge separates read, connection-test writes, article draft preparation and article publication.

Production preparation uses draft-preparation permission and readback only. It does not imply publication permission.

## Post-meta/taxonomy safety

Post-meta and taxonomies are deny-by-default via Bridge allowlists.

Bridge-owned identity metadata and WordPress attachment/edit internals remain protected.

## Current relay orchestration

Current pilot transport remains `github_actions_oidc_relay`.

Parent operation:

```text
prepare_article
```

The request carries bounded routing/provenance only:

```text
connection_id
manifest_path
manifest_commit
```

The trusted orchestrator loads the pinned manifest, resolves/verifies media, invokes `media_upsert`, renders, invokes `article_prepare`, reads back and verifies.

## Bridge operations

Bounded preparation operations remain:

```text
media_upsert
article_prepare
article_read
```

No generic arbitrary PHP/shell/filesystem/database execution endpoint is permitted.

## Verification contract

Preparation succeeds only when readback verifies applicable contract elements:

- exact selected site;
- one managed post ID;
- `status = draft`;
- title/slug;
- source commit/path/SHA identity;
- expected stable media identities and exact hashes;
- final `post_content` hash;
- featured media;
- allowlisted post meta/taxonomies;
- direct managed media URLs;
- no GitHub camo URL;
- no unresolved token/literal Markdown artifact.

If WordPress wrote a draft but later verification fails, retain draft ID/blocker and repair/rerun idempotently. Do not publish/delete automatically.

## Durable preparation state

Persist enough non-secret state for independent resume, including:

```text
connection/site
manifest path + immutable commit/hash
source path + commit + blob/hash
WordPress post ID/status/slug/content hash
stable media provider asset IDs/hashes
WordPress media IDs/URLs/reuse state
applied meta/taxonomy verification
presentation profile + verification state
latest request evidence/blocker
publication_authorized = false by definition
```

## Completion

Preparation is complete only when:

1. connection is verified;
2. article/media satisfy prerequisites;
3. manifest/source identities are immutable and verified;
4. provider delivery bytes pass exact integrity verification;
5. media are safely created/reused;
6. exactly one managed draft is created/updated;
7. status remains `draft`;
8. technical readback passes;
9. required presentation/editor verification passes or is explicitly remaining;
10. durable state is synchronized/re-read;
11. temporary outbox cleanup is done or truthfully recorded pending;
12. no publication occurred.

Publication remains a separate capability and human gate.
