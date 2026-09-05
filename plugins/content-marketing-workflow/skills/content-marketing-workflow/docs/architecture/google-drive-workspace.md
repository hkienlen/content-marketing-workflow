# Google Drive asset workspace contract

Date: 2026-09-05
Status: current provider adapter

## Authority

Google Drive is the only implemented `cloud_media_storage` adapter in CMW 0.2.1.

Global prerequisite/degradation behavior is owned by:

```text
docs/architecture/runtime-compatibility-matrix.md
```

Media identity/delivery behavior is owned by:

```text
docs/architecture/media-delivery-architecture.md
```

User-provided source media is governed by:

```text
docs/architecture/user-provided-images.md
```

This file defines Google Drive-specific workspace behavior only. It must not redefine global readiness or fallback policy.

## Product boundary

Current implemented provider:

```text
google_drive
```

Future reserved adapter:

```text
dropbox
```

GitHub, WordPress and local filesystem are not alternate media-storage providers and must never be proposed as automatic fallback choices.

Legacy `repository_file` media may remain readable only where an owning compatibility/migration contract explicitly permits it. It is not selectable as a new storage provider and must never make cloud-media readiness pass.

## Purpose

Google Drive stores provider-backed binary media for:

- private user-provided source originals used by content workflows;
- generated/treated review image proposals;
- private retained selected/final binaries;
- temporary public delivery copies through `tmp-outbox`.

GitHub remains the durable editorial/workflow source of truth and stores exact media identity, provenance, SHA-256 and metadata, not the normal media binary store.

Concrete Drive folder names/IDs and site domains belong to active user/project data.

## Onboarding prerequisite discovery

`/start` must enumerate implemented cloud providers and discover Google Drive even when it is not already installed, when the active runtime exposes plugin discovery/management.

Distinguish:

```text
not_visible_or_ineligible
visible_installable_not_installed
installed_not_connected
installed_connected_unverified
operational
eligibility_unknown
```

Rules:

- if visible/installable but absent, propose installation during onboarding;
- if installed but disconnected, guide connection immediately;
- if operational, configure/verify the workspace;
- if unavailable or ineligible and no other implemented provider exists, enter the `cloud_media_storage` DEGRADED state;
- never infer eligibility from Free/Plus/Pro/Enterprise labels alone;
- never offer GitHub, WordPress or local filesystem as a fallback.

## Site-domain workspace

Under the selected root, create/reuse:

```text
<drive-root>/
└── <site-domain>/
    ├── articles/
    ├── social/
    └── tmp-outbox/
```

Never mix assets from several sites in one site-domain namespace.

`articles/` and `social/` remain private. `tmp-outbox/` is a temporary public-link reader transport folder only.

## Article assets

Each article uses:

```text
<drive-root>/<site-domain>/articles/<article-slug>/
├── source-user/
├── proposals/
└── final/
```

- `source-user/` contains original user-provided source files;
- `proposals/` contains generated/treated review candidates;
- `final/` contains retained human-selected/final binaries;
- all remain private;
- source originals are never overwritten.

## Social assets

Each social post/concept uses:

```text
<drive-root>/<site-domain>/social/<post-name>/
├── source-user/
├── proposals/
└── final/
```

The immutable post ID remains durable metadata but is not the only human-facing folder identity.

## Source-image placement UX

When the skill asks the user to place source images in Google Drive, it first creates/reuses/verifies the exact private `source-user/` folder and shows:

1. exact canonical human-readable path;
2. resolved direct clickable Drive folder link.

Never guess a Drive URL from a folder name. The non-secret folder ID/link may be persisted for resume.

## `tmp-outbox`

Canonical site path:

```text
<drive-root>/<site-domain>/tmp-outbox/
```

Purpose:

```text
temporary public read-only delivery copies only
```

Rules:

- normal article/social/source-user/proposals/final folders remain private;
- only exact verified final files required for an active external operation are copied to outbox;
- outbox bytes must match expected SHA-256 before external mutation;
- stable destination identity uses the private final `asset_id`, never the outbox copy ID;
- delete temporary copies after verified destination success when practical;
- never delete private retained finals or source originals during outbox cleanup.

If `tmp-outbox` cannot be configured/verified, media-dependent WordPress/social publication remains unavailable according to the central compatibility matrix.

## What belongs in Drive

Drive may contain:

- user-provided source originals;
- generated/treated proposals;
- retained review candidates;
- temporary normalization source files;
- selected normalized private finals;
- temporary `tmp-outbox` copies.

## What belongs in GitHub

GitHub persists identity and provenance, for example:

```yaml
source_type: user_provided
source_provider: google_drive
source_asset_id: <private source file id>
source_original_filename: <original filename>
source_sha256: <exact bytes when available>
source_role: use_as_is|enhance|subject_reference|inspiration_reference|composition_input
source_fidelity: strict|high|moderate|flexible
ai_treatment: none|light_correction|natural_enhancement|marketing_enhancement|creative_transformation
```

Final provider-backed media metadata:

```yaml
provider: google_drive
asset_id: <private-final-file-id>
filename: <canonical filename>
sha256: <exact bytes>
mime_type: <image mime>
width: <pixels>
height: <pixels>
```

plus ALT/title/caption/placement, validation and source relationship.

## Lifecycle

```text
source_discovered
-> source_verified
-> source_inspected
-> proposal/treatment workflow when applicable
-> selected
-> normalized
-> verified_final
-> delivery_staged when needed
-> destination_verified when delivered
```

Drive storage alone never means a source was inspected or a proposal selected/final.

## Onboarding behavior

After Google Drive is discovered/eligible/connected, the skill must:

1. resolve/select the Drive workspace root;
2. persist the non-secret root reference;
3. resolve site domain;
4. create/reuse site root, `articles/`, `social/`, `tmp-outbox/`;
5. explain that only `tmp-outbox` is public-link reader;
6. when connector cannot mutate sharing, instruct `Anyone with the link -> Viewer` for `tmp-outbox` only;
7. retrieve/persist non-secret outbox ID/link;
8. test anonymous read-only accessibility;
9. verify hierarchy/privacy boundary;
10. lazily create content-level `source-user/`, `proposals/`, `final/` as workflows require.

Normal setup must not require Google Cloud Console, service account, OAuth client creation or manually pasted Google credentials.

## Multiple sites

The same Drive root may serve several sites, each with its own private article/social workspaces and outbox.

## Secrets and sharing

Drive folder/file IDs and public read-only delivery URLs are non-secret metadata and may be persisted when required.

Never persist OAuth/access tokens in GitHub. Never broaden sharing of the site root, article/social folders, source-user/proposals/final or future media library merely because `tmp-outbox` is public by link.
