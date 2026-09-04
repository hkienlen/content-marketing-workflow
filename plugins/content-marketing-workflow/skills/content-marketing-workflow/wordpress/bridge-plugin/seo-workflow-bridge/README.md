# SEO Workflow Bridge

Canonical WordPress companion plugin for the repository-backed Content / Marketing workflow.

Current release: `0.11.0`.

## Purpose

The Bridge provides bounded WordPress-side integration for article workflows plus LinkedIn member-profile and Facebook Page publication. It also exposes read-only social-connection health probing and Facebook post-publication read-back verification without returning provider secrets.

Capabilities remain separated and fail closed.

## WordPress article capabilities

The Bridge supports bounded content reads, connection-test drafts, Bridge-managed article draft preparation, provider-backed media preparation and a separate exact-candidate `draft -> publish` article-publication capability.

Article preparation never grants article-publication authorization. Article publication remains bound to its own exact validated candidate and runtime gate.

## LinkedIn

Admin screen:

```text
Settings -> SEO Workflow Bridge - LinkedIn
```

OAuth callback:

```text
/wp-json/seo-workflow-bridge/v1/linkedin/oauth/callback
```

Required current scopes:

```text
openid
profile
w_member_social
```

Client Secret and access token remain on the WordPress side. OAuth connection never becomes a publication request.

Authorized scheduled publication endpoint:

```text
POST /wp-json/seo-workflow-bridge/v1/linkedin/publish-authorized
```

The Bridge revalidates the connected member, exact content, ALT text, delivery bytes, schedule and exact authorization before creating a post.

Definitive creation requires the expected LinkedIn success evidence, including HTTP `201` + `x-restli-id`. With the current member access there is no independent post read-back, so the surrounding skill records `provider_acknowledged`, not `remote_verified`.

## Facebook Page

Supported target:

```text
target_type: facebook_page
```

Personal or professional Facebook profiles are deliberately not supported API publication targets.

Admin screen:

```text
Settings -> SEO Workflow Bridge - Facebook Page
```

WordPress stores the exact Page ID and Page Access Token. The token is never displayed again after saving and never belongs in GitHub or chat.

Current Meta Graph API baseline:

```text
v26.0
```

Current minimum Page permissions:

```text
pages_show_list
pages_read_engagement
pages_manage_posts
```

Connection verification performs only a read-only exact Page identity request (`id,name`) and creates no post.

Authorized scheduled publication endpoint:

```text
POST /wp-json/seo-workflow-bridge/v1/facebook/publish-authorized
```

The Bridge requires an exact persisted authorization whose target is `facebook_page`. Immediately before mutation it re-verifies Page identity, text/ALT hashes, publication intent and exact temporary delivery bytes. Uncertain external creation blocks blind retry.

### Facebook post-publication read-back - 0.11.0+

Read-only endpoint:

```text
POST /wp-json/seo-workflow-bridge/v1/facebook/verify-publication
```

This endpoint performs no social mutation. It accepts only verification requests bound to definitive Facebook publication evidence already persisted by this Bridge, then reads the exact remote post and media from Meta.

`remote_verified` requires:

- exact configured/verified Page remains unchanged;
- exact persisted authorization/publication evidence matches the requested post/media IDs;
- remote post read returns the exact expected ID;
- remote message SHA-256 matches the exact authorized text;
- remote media read returns the exact expected media ID.

A read-back failure after definitive creation does not turn the post into a retryable publication. Publication remains `published`; verification is a separate state.

## Social connection health

Bridge `0.10.0+` exposes the read-only relay operation:

```text
social_connection_health
```

The operation performs bounded provider checks using credentials already stored in WordPress:

- LinkedIn: calls the configured authenticated member identity endpoint and compares it with the stored member identity;
- Facebook: requests the configured Page `id,name` and compares it with the stored verified Page identity.

The response may expose only non-secret operational metadata such as validity, identity match, provider HTTP status and known expiry metadata. It never returns an access token, refresh token, App Secret, client secret or Page token.

The surrounding skill combines this live result with non-secret expiry/data-access-expiry metadata stored in the active user profile. Generic warning thresholds are J-30, J-14 and J-7.

## Scheduling and proof semantics

LinkedIn and Facebook use separate generic schedulers and relays, both with exact per-post authorization:

```text
linkedin-scheduler.yml
-> linkedin-publish-relay.yml
-> Bridge LinkedIn endpoint
-> provider creation evidence
-> provider_acknowledged

facebook-scheduler.yml
-> facebook-publish-relay.yml
-> Bridge Facebook Page publication endpoint
-> provider creation evidence
-> Bridge Facebook read-only verification endpoint
-> remote_verified or verification_failed
```

The health monitor is separate and read-only:

```text
social-connection-health.yml
-> GitHub OIDC
-> Bridge execute / social_connection_health
-> update non-secret user-profile health metadata
```

`planned_at` is the earliest permitted execution time. A connection, schedule, editorial approval or standing policy alone is never the Bridge mutation grant.

A green scheduler run means due detection/relay dispatch succeeded. It is not itself proof that a post was created remotely.

## Optional Telegram reports

Telegram publication reports are implemented by GitHub Actions, not by the Bridge.

Credential boundary:

```text
TELEGRAM_BOT_TOKEN -> GitHub Actions Repository Secret
```

Non-secret enablement/chat/report preferences belong to the active user profile. Reports run only after durable publication/verification reconciliation, are idempotent for the same exact state, and never change/retry social publication when notification delivery fails.

Guided setup/reconfiguration is documented in:

```text
docs/architecture/user-help-telegram-notifications.md
```

## OIDC trust

Bridge validates GitHub OIDC issuer, audience, repository identity, owner identity when configured, repository visibility, event type and exact workflow reference.

Scheduled OIDC trust is intentionally narrow:

- publication relays are invoked through their dedicated dispatch workflows;
- the `schedule` event is accepted only for the exact read-only `social-connection-health.yml` workflow;
- no wildcard workflow trust is used.

The Facebook publication relay may call both the exact publication endpoint and the exact read-only verification endpoint. The verifier additionally requires matching Bridge-persisted creation evidence.

## GitHub token format compatibility

GitHub-provided installation/runtime tokens are opaque and variable-length. Workflows must not parse the `ghs_...` representation or assume a fixed legacy length.

Those credentials are distinct from GitHub Actions OIDC JWTs. See:

```text
docs/architecture/github-app-installation-token-compatibility.md
```

## User-data boundary

The Bridge source is generic companion code. User-specific values are configuration/data and must not be compiled into the plugin.

Examples of user/project values:

- WordPress site and connection identity;
- social member/Page IDs and names;
- preferred publication times;
- social application/configuration IDs;
- credential expiration/data-access-expiration metadata;
- standing publication policies;
- optional notification preferences/routing metadata.

Raw social credentials remain WordPress-side only. Telegram bot token remains in GitHub Actions Secrets when GitHub Actions is the sender. Non-secret durable user/project metadata belongs to the active user profile defined by the skill's user-profile schema.

## Media delivery

The retained selected final remains private in the configured provider workspace. Scheduled social publication uses an exact temporary public-by-link read-only `tmp-outbox` copy only as transport.

Bridge re-verifies exact bytes immediately before remote publication. The temporary delivery file never replaces the retained private final identity.

## Packaging

Every materially different distributed ZIP receives a distinct version. The package must be directly installable by WordPress with:

```text
seo-workflow-bridge/seo-workflow-bridge.php
```

at the expected path and no nested ZIP.

Capability minimums:

```text
LinkedIn scheduled publication -> 0.8.0+
Facebook Page scheduled publication -> 0.9.0+
Social connection health -> 0.10.0+
Facebook Page remote read-back verification -> 0.11.0+
```

## Security properties

- no raw social token in GitHub or health/read-back responses;
- exact GitHub OIDC trust checks;
- replay protection where mutation requires it;
- connection state is separate from runtime publication authorization;
- exact content/media/time/target drift fails closed;
- Facebook uncertain external creation blocks blind retry;
- Facebook read-back is bound to Bridge-persisted definitive creation evidence and contains no mutation path;
- verification failure never authorizes republication;
- notification failure never authorizes republication;
- personal Facebook profiles are never API publication targets;
- no remote shell/filesystem/database administration primitive.

## Architecture references

- `docs/architecture/seo-workflow-bridge-capabilities.md`
- `docs/architecture/seo-workflow-bridge-onboarding.md`
- `docs/architecture/linkedin-publication-onboarding.md`
- `docs/architecture/facebook-page-publication-onboarding.md`
- `docs/architecture/facebook-page-token-provisioning-contract.md`
- `docs/architecture/facebook-page-scheduled-publication-bridge-0.11.0.md`
- `docs/architecture/capabilities/social-connection-health.md`
- `docs/architecture/capabilities/social-publication-verification.md`
- `docs/architecture/capabilities/telegram-publication-notifications.md`
- `docs/architecture/user-help-telegram-notifications.md`
- `docs/architecture/github-app-installation-token-compatibility.md`
- `docs/architecture/user-profile-data-contract.md`
