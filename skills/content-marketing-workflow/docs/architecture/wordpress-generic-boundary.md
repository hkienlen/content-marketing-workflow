# Generic WordPress workflow boundary

Date: 2026-09-01
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

For the current pilot, **SEO Workflow Bridge is the canonical companion implementation**.

## No hostname inference

Labels such as `test`, `staging`, `preprod`, `prod`, `production` or `www` are opaque unless explicit connection/site strategy says otherwise.

The generic skill must never infer that a site named `test` is temporary, that another WordPress site must exist, or that a draft/content must later be cloned/promoted.

## Separation of responsibilities

### `wordpress-connect`

Connects/verifies exactly the selected WordPress site and bounded Bridge abilities.

### `wordpress-prepare-article`

Creates/updates one Bridge-managed draft from the exact validated GitHub editorial source and exact verified final media identities/hashes.

Final media may be:

```text
public_media_source
repository_file
```

Provider-backed media is downloaded through a verified temporary delivery path and must match its persisted SHA-256 before Bridge mutation.

It does not publish or schedule.

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
- Google Drive as the only possible external media provider.

Provider-specific presentation is handled by optional adapters/profiles defined in `docs/architecture/wordpress-adapter-architecture.md`.

Media-provider behavior is defined by `docs/architecture/media-delivery-architecture.md`; current `google_drive` and future `dropbox` share the same generic media semantics.

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
- exact final-media provider identities/hashes/metadata;
- preparation manifests;
- presentation profiles;
- immutable publication candidates;
- durable workflow evidence/configuration.

Provider-backed private final binaries remain in the configured media provider workspace.

WordPress is the publication target and contains derived managed media plus a derived managed draft/published representation.

## Stable media identity

For provider-backed media, WordPress managed identity must derive from the stable private final asset identity, not a temporary `tmp-outbox` delivery copy.

Changing/recreating the transport copy must not create a new managed attachment when the stable asset identity and SHA-256 are unchanged.

## Direct-import scripts

Historical direct WP-CLI/Python/shell import/injection scripts may remain in a separate pilot/integration repository for traceability, diagnostics or explicitly chosen maintenance; they are not canonical generic product source.

They are not the canonical generic WordPress workflow and must not be selected automatically while SEO Workflow Bridge is available and configured.

Relay/orchestration helpers invoking SEO Workflow Bridge are not classified as legacy importers merely because they are scripts.

## Site-specific operations

The pilot may retain separate scripts/processes for cloning, maintenance mode, caches, indexability switches or server administration.

These are not prerequisites or completion conditions of the generic `wordpress-connect`, `wordpress-prepare-article` or `wordpress-publish-article` contracts unless a future explicit architecture decision changes that boundary.
