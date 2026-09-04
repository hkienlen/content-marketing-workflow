# Google Drive asset workspace contract

Date: 2026-09-04
Status: current architecture decision

## Authority

This document defines the current Google Drive workspace contract for the installable skill.

The current media-delivery authority is:

```text
docs/architecture/media-delivery-architecture.md
```

User-provided source media is governed by:

```text
docs/architecture/user-provided-images.md
```

## Purpose

Google Drive is the mandatory current provider-backed workspace for:

- private user-provided source originals used by content workflows;
- generated/treated review image proposals;
- private retained selected/final binaries;
- temporary public delivery copies through `tmp-outbox`.

GitHub remains the durable editorial/workflow source of truth and stores the exact media source/final provider identity, provenance, SHA-256 and metadata required to recover/verify durable assets.

Concrete Drive folder names/IDs and site domains belong to the active user/project profile, not this skill contract.

## Prerequisite

In addition to GitHub access, the current skill design requires Google Drive access.

During onboarding, the skill asks the user for the Drive folder to use as workspace root and resolves/verifies that exact folder.

Generic example:

```text
<drive-root>
```

## Site-domain folder

Under the selected root, create/reuse a folder named after the configured site domain:

```text
<drive-root>/
└── <site-domain>/
```

Never mix assets from several sites in one site-domain namespace.

## Required site folders

Inside the site-domain folder, create/reuse:

```text
<drive-root>/<site-domain>/articles/
<drive-root>/<site-domain>/social/
<drive-root>/<site-domain>/tmp-outbox/
```

`articles/` and `social/` remain private workspaces.

`tmp-outbox/` is a shared temporary transport folder configured as public-link reader only.

## Article assets

Each article uses:

```text
<drive-root>/<site-domain>/articles/<article-slug>/
├── source-user/
├── proposals/
└── final/
```

- `source-user/` contains original user-provided source files when that content uses them;
- `proposals/` contains generated/treated candidates and review variants;
- `final/` contains retained human-selected/final binaries;
- all three remain private;
- the folder name comes from the article's canonical name/slug, not its Work Item number.

`source-user/` is created/reused lazily when the effective visual policy or local override requires user-source intake. The original source must never be overwritten by treatment, normalization or finalization.

## Social assets

Each social post/concept uses:

```text
<drive-root>/<site-domain>/social/<post-name>/
├── source-user/
├── proposals/
└── final/
```

The immutable post ID remains durable metadata but must not be the only human-facing folder identity.

`source-user/` is private and preserves original user files. Generated/treated proposals and finals use distinct provider objects/files.

## Mandatory source-image placement UX

When the skill asks the user to place source images in Google Drive, it must first create/reuse and verify the exact private `source-user/` folder, then show both:

1. the exact human-readable canonical path/name;
2. the resolved direct clickable Google Drive folder link.

Example:

```text
<drive-root>/<site-domain>/articles/<article-slug>/source-user/
Ouvrir le dossier : <resolved direct Drive folder link>
```

Do not say only `place the images in Drive`. Do not guess a URL from a folder name. The link must come from the resolved provider folder identity, and the non-secret folder ID/link may be persisted in content/project state when needed for resume.

## Reusable project media-library extension point

The architecture remains compatible with a future private reusable project library such as:

```text
<drive-root>/<site-domain>/media-library/
```

A full media-library indexing/search implementation is not required for the first user-image workflow. Any future library source must still be resolved, verified, inspected and traced before use.

## `tmp-outbox`

Canonical site path:

```text
<drive-root>/<site-domain>/tmp-outbox/
```

Purpose:

```text
temporary public read-only delivery copies only
```

It may serve WordPress and supported social destination adapters.

The outbox does **not** contain the retained source-of-record binary and never contains user-source originals merely for intake/review.

Rules:

- normal article/social/source-user/proposal/final folders remain private;
- only exact final files needed for an active external operation are copied into the outbox;
- the delivery copy must resolve to the expected SHA-256 before external mutation;
- stable destination identity uses the private retained final asset identity (`asset_id`), not the outbox copy ID;
- after verified destination success, the outbox copy should be deleted when practical;
- never delete the private retained final file or any source-user original during outbox cleanup.

## Naming rule

Use stable, descriptive, URL/filesystem-friendly names.

Requirements:

- human-recognizable;
- no content numbering as the primary identity;
- stable once actively used when practical;
- collision-safe within the namespace;
- article and social folders are separate namespaces.

Source originals keep their original filename when practical; a collision-safe provider copy may add a suffix while durable provenance retains `source_original_filename`.

## What belongs in Drive

Drive may contain:

- user-provided source originals;
- generated proposals;
- retained A/B/C candidates when the effective workflow uses alternatives;
- regenerated candidates;
- temporary normalization source files;
- selected normalized private final binaries;
- temporary `tmp-outbox` delivery copies.

Rejected/superseded proposals may be retained during active review/debugging and cleaned later according to retention policy. User originals are not treated as disposable rejected proposals.

## What belongs in GitHub

For provider-backed source media used durably, GitHub stores provenance such as:

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

For provider-backed final media, GitHub stores durable identity/state, not necessarily the binary:

```yaml
provider: google_drive
asset_id: <private-final-file-id>
filename: <canonical filename>
sha256: <exact bytes>
mime_type: <image mime>
width: <pixels>
height: <pixels>
```

plus source provenance reference when applicable, ALT/title/caption/placement, selection/validation state and downstream destination evidence.

Repository-backed binaries remain supported only when `repository_file` is intentionally selected.

## Lifecycle

Source intake and finalization are distinct:

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

Drive storage alone never means a source was verified/inspected or a proposal was selected/final.

A public outbox copy never becomes the durable source or final identity.

## Onboarding behavior

The skill must:

1. verify GitHub access;
2. verify Google Drive access;
3. ask/select the Drive workspace root;
4. persist the non-secret root folder reference in user/project data;
5. determine the configured site domain from the active profile;
6. create/reuse `<drive-root>/<site-domain>/`;
7. create/reuse `articles/`, `social/`, and `tmp-outbox/`;
8. explain that only `tmp-outbox` should be shared publicly;
9. ask the user to set `tmp-outbox` to `Anyone with the link -> Viewer` when the connector cannot perform that folder-sharing mutation itself;
10. retrieve/persist the non-secret outbox folder ID/link in user/project data;
11. run an anonymous read-only accessibility test;
12. verify the resulting hierarchy and privacy boundary;
13. create content-level `source-user/`, `proposals/` and `final/` lazily as workflows need them.

The setup must remain suitable for non-technical users and must not require Google Cloud Console, a service account, OAuth client creation or manual API credentials.

## Multiple sites

The same Drive root may serve several sites:

```text
<drive-root>/
├── <site-a-domain>/
│   ├── articles/
│   ├── social/
│   └── tmp-outbox/
└── <site-b-domain>/
    ├── articles/
    ├── social/
    └── tmp-outbox/
```

Each site has its own outbox and private workspaces.

## Secrets and sharing

Drive folder/file IDs and public read-only delivery URLs are non-secret metadata and may be persisted in user/project data when required.

Do not persist OAuth tokens, access tokens or other reusable credentials in GitHub.

Do not broaden sharing of the site root, article folders, social folders, `source-user/`, proposal folders, private final folders or a future media library merely because `tmp-outbox` is public by link.
