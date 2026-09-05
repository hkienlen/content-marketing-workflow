# Generic WordPress workflow boundary

Date: 2026-09-05
Status: architecture decision

## Decision

The WordPress capabilities of the single installable Content / Marketing skill must not encode one user's deployment topology, hostname conventions, page builder, media provider or server administration model.

The generic model is:

```text
user/configuration selects one WordPress connection
        ↓
internal WordPress capability
        ↓
semantic Bridge operation
        ↓
secure transport
        ↓
SEO Workflow Bridge / compatible WordPress companion boundary
        ↓
that selected WordPress site
```

SEO Workflow Bridge is the canonical current companion implementation.

## No hostname inference

Labels such as `test`, `staging`, `preprod`, `prod`, `production` or `www` are opaque unless explicit connection/site strategy says otherwise.

The generic skill must never infer that a site named `test` is temporary, that another WordPress site must exist, or that a draft/content must later be cloned/promoted.

## Separation of responsibilities

### `wordpress-connect`

Connects/verifies exactly the selected WordPress site and bounded Bridge abilities.

### `wordpress-prepare-article`

Creates/updates one Bridge-managed draft from the exact validated GitHub editorial source and exact verified final media identities/hashes.

Normal provider-backed media comes from the selected implemented `cloud_media_storage` provider (`google_drive` or `dropbox`) through a verified temporary delivery path and must match its persisted SHA-256 before Bridge mutation.

Legacy `repository_file` media remains compatibility/migration-only where an owning contract explicitly permits it; it is not a cloud-media fallback.

Preparation does not publish or schedule.

### `wordpress-publish-article`

Publishes only the exact immutable validated candidate after its independent runtime authorization.

It does not rebuild content or media.

## Provider neutrality

The generic capability contracts must not hardcode:

- Divi;
- Elementor;
- Bricks;
- Gutenberg-specific custom layouts;
- Yoast;
- Rank Math;
- WooCommerce;
- ACF;
- one taxonomy/category;
- one author login;
- pilot preset IDs;
- one cloud-media provider as the only possible implementation.

Provider-specific presentation is handled by optional adapters/profiles defined in `docs/architecture/wordpress-adapter-architecture.md`.

Media-provider behavior is defined by `docs/architecture/media-delivery-architecture.md`; implemented `google_drive` and `dropbox` adapters share the same generic media semantics while retaining distinct provider-qualified identities.

## Bridge authority and transport

SEO Workflow Bridge owns bounded WordPress-side operations and local allowlists/permission switches.

Transport only carries authenticated requests to those bounded operations.

Do not conflate:

```text
Bridge = application capability boundary
transport = authenticated delivery mechanism
media provider = source of verified final binary bytes
```

The current GitHub Actions OIDC relay is a transport. It is not the business definition of WordPress preparation/publication.

## Source of truth

GitHub remains the durable editorial/workflow source of truth for:

- validated article source;
- exact provider-qualified final-media identities/hashes/metadata;
- preparation manifests;
- presentation profiles;
- immutable publication candidates;
- durable workflow evidence/configuration.

Provider-backed private final binaries remain in the selected cloud-media workspace.

WordPress is the publication target and contains derived managed media plus a derived managed draft/published representation.

## Stable media identity

For provider-backed media, WordPress managed identity must derive from the stable private final provider + asset identity/reference + SHA-256, not a temporary `tmp-outbox` delivery copy/link.

Changing/recreating the transport copy must not create a new managed attachment when the stable provider-qualified asset identity and SHA-256 are unchanged.

A project switch between Google Drive and Dropbox requires explicit media migration/rebinding; an old provider ID/reference must never be reinterpreted under the new provider namespace.

## Direct-import scripts

Historical direct WP-CLI/Python/shell import/injection scripts may remain in a separate integration repository for traceability, diagnostics or explicitly chosen maintenance; they are not canonical generic product source.

They are not the canonical generic WordPress workflow and must not be selected automatically while SEO Workflow Bridge is available and configured.

Relay/orchestration helpers invoking SEO Workflow Bridge are not classified as legacy importers merely because they are scripts.

## Site-specific operations

A project may retain separate scripts/processes for cloning, maintenance mode, caches, indexability switches or server administration.

These are not prerequisites or completion conditions of the generic `wordpress-connect`, `wordpress-prepare-article` or `wordpress-publish-article` contracts unless a future explicit architecture decision changes that boundary.
