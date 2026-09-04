# SEO Workflow Bridge - capabilities and operating model

Date: 2026-09-04
Status: normative companion-plugin contract
Current release target: `0.11.0`

## Role in the future skill

`SEO Workflow Bridge` is the canonical mainstream WordPress companion extension for the single installable Content / Marketing skill. It is not a separate workflow product.

Normal users must not need SSH, server cron, Python/WSGI, systemd, Docker, reverse-proxy configuration or another daemon.

The Bridge is the mainstream integration point for:

- bounded WordPress reads/test operations;
- WordPress article draft preparation;
- separately authorized WordPress article publication;
- LinkedIn OAuth/member verification + exact scheduled publication;
- Facebook Page identity/token ownership + exact scheduled publication;
- read-only social connection-health probes;
- Facebook Page post-publication read-back verification.

Concrete site/repository/account IDs, publishing preferences, notification preferences and credential-lifecycle dates belong to user/project data, not this contract.

## Capability families

### WordPress content

Supported bounded reads/test operations include `site_info`, `content_list`, `reference_read`, `draft_read`, `draft_create` and `draft_delete` under their existing allowlists/gates.

Article preparation creates/updates Bridge-managed drafts and never publishes. Article publication remains a separate exact-candidate capability and must not reconstruct or silently alter the validated article.

### LinkedIn

WordPress-hosted OAuth callback:

```text
/wp-json/seo-workflow-bridge/v1/linkedin/oauth/callback
```

Required current products/scopes:

```text
Share on LinkedIn -> w_member_social
Sign in with LinkedIn using OpenID Connect -> openid + profile
```

Secrets remain WordPress-side.

Scheduled endpoint:

```text
POST /wp-json/seo-workflow-bridge/v1/linkedin/publish-authorized
```

LinkedIn scheduled runtime requires Bridge `0.8.0+`; later Bridge versions preserve that contract unless explicitly versioned otherwise.

With the current member access, definitive creation evidence is HTTP `201` + `x-restli-id`. Independent member-post read-back is not available, so the durable deployment-verification state is `provider_acknowledged`, not `remote_verified`.

### Facebook Page

Bridge `0.9.0+` supports:

```text
target_type: facebook_page
```

and explicitly does not support personal/professional Facebook profiles as API publication targets.

WordPress owns:

- exact numeric Page ID;
- Page Access Token;
- verified Page ID/name evidence;
- Bridge-side definitive publication evidence.

Current Graph API baseline:

```text
v26.0
```

Current onboarding permissions:

```text
pages_show_list
pages_read_engagement
pages_manage_posts
```

The granting Meta user/token must also have Page task access sufficient to create content.

Read-only Page connection verification asks Meta only for exact `id,name` and publishes nothing.

Scheduled publication endpoint:

```text
POST /wp-json/seo-workflow-bridge/v1/facebook/publish-authorized
```

Bridge `0.11.0+` additionally exposes the read-only post-publication verifier:

```text
POST /wp-json/seo-workflow-bridge/v1/facebook/verify-publication
```

The verifier accepts only a request bound to definitive Facebook publication evidence already persisted by this Bridge. It then reads the exact remote post/media from Meta, checks the exact Page/remote IDs and exact authorized message SHA-256, and returns `remote_verified` only after successful read-back. It contains no Meta mutation path.

Normative runtime contracts:

```text
docs/architecture/facebook-page-scheduled-publication-bridge-0.9.0.md
docs/architecture/facebook-page-scheduled-publication-bridge-0.11.0.md
```

Onboarding contracts:

```text
docs/architecture/facebook-page-publication-onboarding.md
docs/architecture/facebook-page-token-provisioning-contract.md
docs/architecture/facebook-login-for-business-configuration.md
docs/architecture/user-help-facebook-page-onboarding.md
```

### Social connection health

Bridge `0.10.0+` adds the read-only relay operation:

```text
social_connection_health
```

It uses provider credentials already stored in WordPress to verify current connection reality without returning those credentials.

LinkedIn health verifies authenticated member identity. Facebook health verifies the configured Page `id,name`. Results may include only non-secret fields such as validity, identity match, provider HTTP status and known WordPress-side expiry metadata.

The skill reconciles those results with credential-expiry/data-access-expiry metadata stored in the active user/project profile.

This operation never publishes and never renews a credential.

### Post-publication verification

Publication acknowledgement and remote verification are separate concepts:

```text
scheduler success != publication proof

Facebook:
published -> remote_verified

LinkedIn:
published -> provider_acknowledged
```

For Facebook 0.11.0, the dedicated relay performs a bounded read-only verification after definitive creation. Eventual-consistency retries may repeat only the GET/read-back request. A failed verification must never cause the publication mutation to run again.

For LinkedIn, current access can prove provider creation but not independently GET the member post. The relay therefore records `provider_acknowledged` explicitly.

Normative model:

```text
docs/architecture/capabilities/social-publication-verification.md
```

## Production validation

A social adapter is considered production-ready for one user/project only after:

```text
compatible Bridge installed
+ connection identity verified read-only
+ scheduler/relay/OIDC path verified
+ media-delivery path verified
+ controlled end-to-end live publication validated
+ platform-appropriate post-publication evidence model validated
```

Concrete validation posts, account/Page IDs, GitHub run IDs and remote publication identifiers are user/project evidence and are excluded from the generic skill package.

## Ordinary UI and secrets

Normal administrator screens expose useful configuration/connection state only.

```text
Settings -> SEO Workflow Bridge - LinkedIn
Settings -> SEO Workflow Bridge - Facebook Page
```

Stored Client Secret/access tokens/Page Access Token must never be rendered back in clear text.

Connection state is never the runtime authorization for a specific post.

Historical pilot-specific LinkedIn dry-run/live-gate payloads are excluded from the distributable plugin. A generic non-publishing media identity probe may remain packaged for controlled diagnostics but is not registered into the ordinary UI.

Telegram notification credentials do not belong in the Bridge: when GitHub Actions is the sender, `TELEGRAM_BOT_TOKEN` is stored only as a GitHub Actions Repository Secret. Telegram enablement/chat destination/report preferences belong to user/project data.

## Exact scheduled-publication authorization

Both social adapters require persisted per-platform/per-post state:

```text
authorized_for_scheduled_publication
```

A post being approved/final/scheduled/due is insufficient as a Bridge mutation request.

Common authorization binding includes exact post/time/content/media/delivery identity. Platform-specific target identity is also bound:

```text
LinkedIn -> author_urn
Facebook -> target_type + Page ID
```

Changing a bound value invalidates the authorization for that platform.

## Publication-consent policy vs exact runtime authorization

The skill may collect publication consent using a user/project policy such as:

```text
one_off_exact_confirmation
standing_auto_publish_scheduled
```

This does not change the Bridge endpoint contract. The Bridge still receives only an exact per-platform/per-post authorization.

Standing policy values belong to the active user profile and do not live in this generic contract.

Immediate `publish_now` remains separate unless explicitly governed by a future policy.

## Media behavior

The private provider-backed final remains the retained source of record.

For scheduled delivery the skill creates an exact temporary delivery copy in the configured `tmp-outbox`. Bridge downloads it and verifies exact byte length, SHA-256 and supported MIME immediately before remote mutation.

The temporary file is transport only and never replaces the retained final identity.

### LinkedIn runtime

Bridge uploads exact verified bytes through LinkedIn Images API, obtains the runtime image URN, constructs the final Posts API payload and accepts success only with the contractually required success evidence.

### Facebook Page runtime

Bridge freshly verifies the configured Page identity with Meta, then sends the exact verified image bytes as multipart `source` to:

```text
/v26.0/{page_id}/photos
```

with exact `caption`, exact `alt_text_custom`, `published=true` and the Page Access Token only in the Authorization header.

A definitive success requires HTTP 2xx plus non-empty remote media/post identifiers. Bridge persists that evidence before returning success. Bridge 0.11.0 can then read the exact created post/media back without mutating them.

## GitHub Actions scheduler model

LinkedIn:

```text
linkedin-scheduler.yml
-> linkedin-publish-relay.yml
-> short-lived GitHub OIDC
-> Bridge LinkedIn endpoint
-> provider_acknowledged evidence
-> optional Telegram report
```

Facebook Page:

```text
facebook-scheduler.yml
-> facebook-publish-relay.yml
-> short-lived GitHub OIDC
-> Bridge Facebook publication endpoint
-> definitive publication evidence
-> Bridge Facebook read-only verification endpoint
-> remote_verified or verification_failed
-> optional Telegram report
```

Connection health:

```text
social-connection-health.yml
-> short-lived GitHub OIDC
-> Bridge read-only social_connection_health
-> non-secret user-profile health reconciliation
```

Publication schedulers contain no hard-coded user/post identity and scan only exact authorization state.

OIDC trust remains pinned to repository/audience/owner/workflow identity. The scheduled `schedule` event is accepted only for the exact read-only health workflow; publication relay workflow refs are not implicitly trusted for scheduled events.

GitHub-provided installation/runtime tokens must be treated as opaque variable-length credentials. No workflow or skill code may assume a fixed `ghs_` token length or parse its internal format. See `docs/architecture/github-app-installation-token-compatibility.md`.

## Evidence and recovery

Definitive successful remote evidence is persisted WordPress-side before GitHub synchronization so later exact retry can reconcile rather than duplicate.

For Facebook, a Meta transport/server ambiguity after external creation begins becomes:

```text
facebook_page_publish_uncertain
-> uncertain_external_result
-> automatic retry forbidden
-> human reconciliation required
```

A Facebook verification failure after definitive creation is different:

```text
publication_state = published
verification.state = verification_failed
-> publication retry forbidden
-> read-back/reconciliation may be retried separately
```

Notification failure is also independent and never changes social publication state.

## Capability separation

Conceptually:

```yaml
seo_workflow_bridge:
  wordpress_article_prepare: false
  wordpress_article_publish: false
  linkedin_connection: false
  linkedin_scheduled_publication: false
  facebook_page_connection: false
  facebook_page_scheduled_publication: false
  facebook_page_post_publication_verification: read_only
  social_connection_health: read_only
```

Installation/configuration of one capability does not activate another.

## Packaging/versioning

Every materially different distributed ZIP receives a new visible version and must be directly installable with no nested ZIP.

Capability minimums:

```text
LinkedIn scheduled publication -> Bridge 0.8.0+
Facebook Page scheduled publication -> Bridge 0.9.0+
read-only social connection health -> Bridge 0.10.0+
Facebook Page post-publication read-back -> Bridge 0.11.0+
```

## Future-skill obligations

The skill must:

1. detect install/activation/version;
2. know capability-specific Bridge minimums;
3. provide a directly installable compatible ZIP when upgrade is required;
4. guide platform onboarding without exposing secrets;
5. persist non-secret user/project connection identity and lifecycle metadata in the active profile;
6. prepare exact temporary delivery assets;
7. resolve publication consent according to the active user policy;
8. always materialize an exact per-platform/per-post authorization before unattended execution;
9. invalidate authorization when a bound value changes;
10. dispatch only due authorized records;
11. persist/verify definitive provider-creation evidence;
12. distinguish scheduler success from relay/publication success;
13. run platform-appropriate post-publication verification and persist its separate state;
14. never blind-retry uncertain external creation or a definitive publication merely because verification failed;
15. send optional user notifications only after durable publication/verification reconciliation;
16. keep notification credentials out of user profile/repository content;
17. monitor connection health read-only and warn before known credential validity ends;
18. resume credential/notification reconfiguration from the last valid user/project milestone instead of rebuilding integrations unnecessarily.

## References

- `docs/architecture/seo-workflow-bridge-onboarding.md`
- `docs/architecture/user-profile-data-contract.md`
- `docs/architecture/capabilities/social-connection-health.md`
- `docs/architecture/capabilities/social-publication-verification.md`
- `docs/architecture/capabilities/telegram-publication-notifications.md`
- `docs/architecture/linkedin-publication-onboarding.md`
- `docs/architecture/linkedin-scheduled-publication-bridge-0.8.0.md`
- `docs/architecture/facebook-page-publication-onboarding.md`
- `docs/architecture/facebook-page-token-provisioning-contract.md`
- `docs/architecture/facebook-login-for-business-configuration.md`
- `docs/architecture/facebook-page-standing-publication-policy.md`
- `docs/architecture/facebook-page-scheduled-publication-bridge-0.9.0.md`
- `docs/architecture/facebook-page-scheduled-publication-bridge-0.11.0.md`
- `docs/architecture/facebook-github-actions-scheduler.md`
- `docs/architecture/user-help-telegram-notifications.md`
- `docs/architecture/github-app-installation-token-compatibility.md`
