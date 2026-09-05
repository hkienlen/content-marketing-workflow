# Dropbox asset workspace contract

Date: 2026-09-05
Status: current provider adapter

## Authority

Dropbox is an implemented `cloud_media_storage` adapter in CMW 0.3.0.

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

This file defines Dropbox-specific workspace behavior only. It must not redefine global readiness or fallback policy.

## Product boundary

Implemented provider:

```text
dropbox
```

Google Drive is the other implemented `cloud_media_storage` provider. Exactly one provider is active for a project at a time.

GitHub, WordPress and local filesystem are not alternate media-storage providers and must never be proposed as automatic fallback choices.

## Purpose

Dropbox stores provider-backed binary media for:

- private user-provided source originals used by content workflows;
- generated/treated review image proposals;
- private retained selected/final binaries;
- temporary public delivery copies through `tmp-outbox`.

GitHub remains the durable editorial/workflow source of truth and stores exact media identity, provenance, SHA-256 and metadata, not the normal media binary store.

Concrete Dropbox folder paths/IDs and site domains belong to active user/project data.

## Onboarding prerequisite discovery

`/start` must enumerate implemented cloud providers and discover Dropbox even when it is not already installed, when the active runtime exposes plugin discovery/management.

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
- when Google Drive and Dropbox are both operational, present both choices and keep Google Drive as the recommended/default selection unless the user chooses Dropbox;
- if unavailable or ineligible and no other implemented provider exists, enter the `cloud_media_storage` DEGRADED state;
- never infer eligibility from Free/Plus/Pro/Enterprise labels alone;
- never offer GitHub, WordPress or local filesystem as a fallback.

## Site-domain workspace

Under the selected Dropbox root, create/reuse:

```text
<dropbox-root>/
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
<dropbox-root>/<site-domain>/articles/<article-slug>/
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
<dropbox-root>/<site-domain>/social/<post-name>/
├── source-user/
├── proposals/
└── final/
```

The immutable post ID remains durable metadata but is not the only human-facing folder identity.

## Source-image placement UX

When the skill asks the user to place source images in Dropbox, it first creates/reuses/verifies the exact private `source-user/` folder and shows:

1. exact canonical human-readable path;
2. resolved direct clickable Dropbox folder link when the active integration exposes one.

Never guess a Dropbox URL from a folder path. A non-secret provider folder reference/link may be persisted for resume.

## `tmp-outbox`

Canonical site path:

```text
<dropbox-root>/<site-domain>/tmp-outbox/
```

Purpose:

```text
temporary public read-only delivery copies only
```

Rules:

- normal article/social/source-user/proposals/final folders remain private;
- only exact verified final files required for an active external operation are copied to outbox;
- outbox bytes must match expected SHA-256 before external mutation;
- stable destination identity uses the private final `asset_id`, never the outbox copy identity;
- use a verified public read-only shared link for the exact staged object/folder as supported by the active Dropbox integration;
- delete temporary copies and temporary links after verified destination success when practical;
- never delete private retained finals or source originals during outbox cleanup.

If `tmp-outbox` cannot be configured/verified for public read-only delivery, media-dependent WordPress/social publication remains unavailable according to the central compatibility matrix.

## What belongs in Dropbox

Dropbox may contain:

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
source_provider: dropbox
source_asset_id: <private source file id/path reference>
source_original_filename: <original filename>
source_sha256: <exact bytes when available>
source_role: use_as_is|enhance|subject_reference|inspiration_reference|composition_input
source_fidelity: strict|high|moderate|flexible
ai_treatment: none|light_correction|natural_enhancement|marketing_enhancement|creative_transformation
```

Final provider-backed media metadata:

```yaml
provider: dropbox
asset_id: <private-final-file-id/path-reference>
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

Dropbox storage alone never means a source was inspected or a proposal selected/final.

## Onboarding behavior

After Dropbox is discovered/eligible/connected and selected, the skill must:

1. resolve/select the Dropbox workspace root;
2. persist the non-secret root reference;
3. resolve site domain;
4. create/reuse site root, `articles/`, `social/`, `tmp-outbox/`;
5. explain that only staged `tmp-outbox` delivery material may receive public read-only links;
6. create or guide creation of the required read-only shared link using the active Dropbox integration's supported surface;
7. persist non-secret outbox/shared-link references only when useful for resume;
8. test anonymous read-only accessibility before publication readiness is claimed;
9. verify hierarchy/privacy boundary;
10. lazily create content-level `source-user/`, `proposals/`, `final/` as workflows require.

Normal setup must not require developer-console OAuth application creation, manually pasted access tokens or Dropbox API credentials when an operational ChatGPT/Codex integration is available.

## Multiple sites

The same Dropbox root may serve several sites, each with its own private article/social workspaces and outbox.

## Secrets and sharing

Dropbox folder/file references and intentionally public read-only delivery URLs are non-secret metadata and may be persisted when required.

Never persist OAuth/access tokens in GitHub. Never broaden sharing of the site root, article/social folders, source-user/proposals/final or future media library merely because temporary outbox delivery material is public by link.
