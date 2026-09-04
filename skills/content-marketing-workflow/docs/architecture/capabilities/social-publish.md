# Internal capability: social-publish

Date: 2026-09-04
Status: LinkedIn and Facebook Page live-validated; post-publication verification model current

## Purpose

`social-publish` is the only internal capability allowed to create an externally visible social-network publication through a supported adapter.

It remains separate from content creation, visual generation, scheduling metadata, connection setup, connection-health monitoring, editorial approval and optional notification delivery.

Current adapters:

```text
LinkedIn -> authenticated member-profile publication
Facebook -> facebook_page publication
```

A Facebook personal/professional profile is not a supported API target.

Concrete remote identities, connection IDs, API/app configuration IDs, credential expiry metadata, publication preferences and notification preferences belong to the active **user profile**. This capability owns the model/behavior only.

## Common architecture

```text
validated post + private final
-> planned_at
-> publication consent resolved by active user/platform policy
-> exact per-platform/per-post authorization record
-> exact temporary tmp-outbox delivery copy
-> platform-specific generic scheduler
-> platform-specific GitHub Actions OIDC relay
-> SEO Workflow Bridge
-> exact prepublication verification
-> remote API immediate creation
-> provider creation evidence
-> post-publication verification when current permissions support it
-> GitHub evidence/status reconciliation
-> optional user notification report
```

GitHub stores no social-platform secret.

## Common prerequisites

For unattended publication all must be true:

- immutable `post_id` exists;
- final text approved;
- exact final image `verified_final`;
- exact ALT present;
- target platform connection from the active user profile exists and exact remote identity is verified;
- compatible Bridge installed/active;
- connection health is not known expired/invalid;
- exact timezone-aware `planned_at`;
- publication consent is satisfied under the active user/platform policy;
- exact revision has `authorized_for_scheduled_publication` for that platform;
- exact delivery copy exists in configured tmp-outbox;
- authorization binds all platform-specific target/content/media/time identity;
- no conflicting definitive-success evidence exists.

`approved`, `final`, `scheduled`, due time, connection or stored token alone are never sufficient runtime mutation grants.

## Publication-consent policy

Conceptual modes:

```text
one_off_exact_confirmation
standing_auto_publish_scheduled
```

The user's selected mode is persisted in their connection profile. In both modes the Bridge receives only an exact per-platform/per-post authorization record.

A standing policy allows the skill to materialize that exact record automatically after normal final content + schedule validation. It is not a Bridge wildcard and does not apply to `publish_now` unless a separate explicit contract says so.

Normative Facebook policy model: `docs/architecture/facebook-page-standing-publication-policy.md`.

## Scheduling semantics

Current adapters publish immediately when called; remote platforms are not used as the future scheduler.

```text
planned_at = earliest due threshold in user/project durable state
GitHub Actions = scheduler
SEO Workflow Bridge = final verifier + platform adapter
remote platform = immediate creation target
```

Publication schedulers run every 10 minutes. Persist actual `published_at` separately.

**Scheduler success alone never means a post was published.** A scheduler only finds due exact authorizations and dispatches a relay. Publication/deployment proof belongs to the relay and persisted remote evidence.

Before creating/saving a schedule, `social-connection-health` checks whether a known credential effective-expiry occurs before `planned_at`. A post beyond known credential validity is surfaced as renewal-required rather than silently assumed safe.

## Connection-health relationship

Normative capability:

```text
docs/architecture/capabilities/social-connection-health.md
```

Daily monitoring:

- obtains provider-active read-only credential/identity evidence from Bridge 0.10.0+;
- evaluates profile-owned token/Data Access expiry metadata;
- updates profile-owned non-secret health state;
- warns before known expiry;
- detects pending authorizations scheduled beyond known validity.

Health monitoring never replaces runtime checks. Every publication endpoint rechecks credential/identity prerequisites just before mutation.

Credential renewal does not invalidate already-approved post content/schedules when the exact remote target identity is unchanged.

## Post-publication verification relationship

Normative capability:

```text
docs/architecture/capabilities/social-publication-verification.md
```

Final verification states currently differ by platform while publication status remains `published`:

```text
Facebook Page -> verification_state = remote_verified
LinkedIn      -> verification_state = provider_acknowledged
```

The distinction is intentional: Facebook can be read back with the current Page permissions, while the current LinkedIn member connection can prove provider creation but does not have the restricted read permission needed for an independent member-post GET.

## LinkedIn adapter

Target:

```text
authenticated member profile
```

Bridge endpoint:

```text
POST /wp-json/seo-workflow-bridge/v1/linkedin/publish-authorized
```

Bridge verifies current member/token, text/ALT/intent, exact delivery bytes, uploads media through LinkedIn Images API and accepts success only with HTTP `201` + `x-restli-id`.

After definitive creation, durable state becomes:

```text
publication_state = published
execution.state = provider_acknowledged
verification.state = provider_acknowledged
verification.readback_available = false
```

This is not labelled `remote_verified`.

LinkedIn secrets remain in WordPress. `token_expires_at` and non-secret health metadata belong to the active user profile.

Current Bridge does not assume a refresh token exists. Renewal is normally OAuth reconnect through WordPress followed by exact same-member verification.

Normative runtime contract:

```text
docs/architecture/linkedin-scheduled-publication-bridge-0.8.0.md
```

## Facebook Page adapter

Target:

```text
facebook_page
```

Bridge publication endpoint:

```text
POST /wp-json/seo-workflow-bridge/v1/facebook/publish-authorized
```

Bridge 0.11.0+ read-back endpoint:

```text
POST /wp-json/seo-workflow-bridge/v1/facebook/verify-publication
```

WordPress owns the raw Page Access Token. The user profile owns non-secret exact Page identity, Meta/app/configuration metadata, observed scopes and credential-lifecycle/health metadata.

Required onboarding permissions:

```text
pages_show_list
pages_read_engagement
pages_manage_posts
```

The granting user/token also needs Page task access sufficient to create content (`CREATE_CONTENT`).

Validated generic credential path:

```text
fresh User Access Token
-> GET /me/accounts?fields=id,name,tasks
-> Meta debugger: Étendre le token d'accès
-> long-lived User Access Token
-> GET /me/accounts?fields=id,name,access_token,tasks
-> exact Page Access Token
-> Meta debugger: Type Page / exact profile Page / Valid
-> paste Page token directly into WordPress
-> read-only Bridge Page verification
```

If Meta reports Page-token `Expiration: Never` but provides a Data Access expiration, persist that separate timestamp in the user profile and use it as a renewal horizon.

Immediately before Facebook mutation Bridge verifies exact authorization, due/stale window, configured/verified Page identity, fresh Meta identity, text/ALT/intent hashes and exact tmp-outbox media bytes/hash/MIME.

After Meta returns definitive creation IDs, Bridge/GitHub perform a bounded **read-only** GET of the created post/media. `remote_verified` requires exact remote IDs and authorized message hash to match. Eventual-consistency retries may repeat the read only; they must never repeat the publication mutation.

If publication is definitive but read-back fails, durable publication remains `published` and verification is marked failed. Automatic publication retry is forbidden.

Normative runtime contract:

```text
docs/architecture/facebook-page-scheduled-publication-bridge-0.11.0.md
```

## Live-validation evidence boundary

A new adapter/installation requires controlled live validation before production readiness. Concrete test post IDs, workflow run IDs, remote post/media IDs and user validation belong to user/project checkpoints/state and are excluded from the generic skill package.

The generic contract retains only the reusable requirement: one exact controlled publication must be verified end to end without duplicate creation.

## Target metadata

A Page-targeted post uses:

```yaml
facebook:
  status: scheduled
  planned_at: <ISO 8601 + timezone>
  target_type: facebook_page
  connection_id: <user-profile facebook connection>
```

After a successful Facebook read-back the platform block keeps publication status and adds verification state:

```yaml
facebook:
  status: published
  published_at: <actual creation time>
  remote_post_id: <provider id>
  remote_media_id: <provider id>
  verification_state: remote_verified
  remote_verified_at: <read-back time>
```

LinkedIn definitive provider acknowledgement is represented as:

```yaml
linkedin:
  status: published
  published_at: <actual creation time>
  remote_post_id: <x-restli-id>
  verification_state: provider_acknowledged
```

Target metadata is not itself runtime authorization.

## Media delivery

Canonical final media remains private/provider-backed.

```text
private final
-> exact verified tmp-outbox copy
-> Bridge downloads exact bytes
-> size/hash/MIME verification
-> platform-specific upload/create
```

No Google OAuth/service-account secret is required in GitHub Actions.

## Success evidence

Persist in user/project state:

- platform/post ID;
- exact remote target identity;
- remote post/media identifier(s);
- actual `published_at` + planned time;
- content/media/ALT/intent hashes;
- delivery identity;
- authorization ID;
- API version/HTTP result;
- GitHub Actions run ID;
- post-publication verification state/evidence where supported.

## Optional publication reports

After durable publication/verification state is reconciled, an enabled notification adapter may report the result.

Current generic Telegram adapter:

```text
docs/architecture/capabilities/telegram-publication-notifications.md
```

Telegram enablement, chat destination and report preferences belong to user/project data. The bot token remains in GitHub Actions Repository Secrets when GitHub Actions sends the report.

A notification failure never changes social publication state and never authorizes a retry.

## Idempotency and recovery

Blind retry after uncertain external creation is forbidden.

For definitive success, Bridge persists evidence before GitHub synchronization. A later exact retry reconciles existing evidence rather than blindly creating another post.

Facebook transport/server ambiguity after the Meta creation request begins becomes `uncertain_external_result`, excluded from automatic retry until reconciliation.

Verification failure after definitive creation is a separate state and does not make the publication candidate retryable.

## WordPress UI

Normal users configure useful connection state only:

```text
Settings -> SEO Workflow Bridge - LinkedIn
Settings -> SEO Workflow Bridge - Facebook Page
```

Raw credentials remain WordPress-side and are not rendered back.

## Guided setup

- LinkedIn: `docs/architecture/linkedin-publication-onboarding.md`
- Facebook: `docs/architecture/facebook-page-publication-onboarding.md`
- Facebook credential supplement: `docs/architecture/facebook-page-token-provisioning-contract.md`
- Facebook user help: `docs/architecture/user-help-facebook-page-onboarding.md`
- Telegram reports: `docs/architecture/user-help-telegram-notifications.md`

New reusable provider/UI behavior updates generic contracts/help. Concrete account IDs/names/expiry/timestamps/chat destinations update only user/project data.

## Platform-adapter invariant

Adding another network must not redesign immutable `post_id`, validated master text, combined review, final media identity/hash, `planned_at` semantics, exact authorization record, common evidence/idempotency model, user-profile credential-health model or notification-preference ownership.

Platform-specific remote identities, permissions, renewal mechanics, API payloads and ambiguous-result recovery stay isolated behind adapters.

Disabled/unconfigured adapters fail closed without blocking independently enabled platforms unless an atomic multi-platform action is explicitly required.

## References

- `docs/architecture/user-profile-data-contract.md`
- `docs/architecture/capabilities/social-connection-health.md`
- `docs/architecture/capabilities/social-publication-verification.md`
- `docs/architecture/capabilities/telegram-publication-notifications.md`
- `docs/architecture/capabilities/social-schedule.md`
- `docs/architecture/facebook-page-standing-publication-policy.md`
- `docs/architecture/linkedin-scheduled-publication-bridge-0.8.0.md`
- `docs/architecture/facebook-page-scheduled-publication-bridge-0.11.0.md`
- `docs/architecture/facebook-page-publication-onboarding.md`
- `docs/architecture/facebook-page-token-provisioning-contract.md`
- `docs/architecture/facebook-github-actions-scheduler.md`
- `docs/architecture/seo-workflow-bridge-capabilities.md`
