# Internal capability: social-publish

Date: 2026-09-05
Status: LinkedIn and Facebook Page live-validated; runtime prerequisite model current

## Purpose

`social-publish` is the only internal capability allowed to create externally visible social-network publications through supported adapters.

Global prerequisite/degradation behavior is owned by:

```text
docs/architecture/runtime-compatibility-matrix.md
```

Current adapters:

```text
LinkedIn -> authenticated member-profile publication
Facebook -> facebook_page publication
```

A Facebook personal/professional profile is not a supported API target or fallback.

## Current architecture

```text
validated post + required verified_final media
-> planned_at
-> publication consent
-> exact per-platform/per-post authorization
-> exact tmp-outbox delivery copy
-> GitHub Actions scheduler/relay
-> WordPress-hosted SEO Workflow Bridge
-> exact prepublication verification
-> remote API creation
-> provider evidence
-> post-publication verification when supported
-> GitHub reconciliation
-> optional notification report
```

GitHub stores no social-platform secret.

## Shared runtime prerequisites

For current automated/unattended LinkedIn or Facebook publication all must be true:

- `github_repository` operational;
- `cloud_media_storage` operational;
- immutable `post_id` exists;
- final text approved;
- exact required final image is `verified_final`;
- exact ALT present;
- `wordpress_bridge_runtime` operational;
- `github_actions_scheduler` operational for scheduled/unattended publication;
- target platform adapter/connection exists and remote identity is verified;
- connection health is not known expired/invalid;
- exact timezone-aware `planned_at` when scheduled;
- publication consent is satisfied;
- exact revision has appropriate publication authorization;
- exact delivery copy exists in configured `tmp-outbox` and matches expected hash/MIME/size;
- no conflicting definitive-success evidence exists.

Strict invariant:

```text
no required verified final image
=> no social publication
```

CMW must not introduce text-only social publication as a degraded fallback.

## Missing prerequisite behavior

### Cloud media unavailable

Authoring/review of social text may continue where allowed, but publication is unavailable. Do not fall back to GitHub binaries, WordPress media library or local filesystem storage.

### WordPress / SEO Workflow Bridge unavailable

Current automated LinkedIn/Facebook publication is unavailable even when social credentials otherwise exist. Do not silently switch to direct provider APIs outside the governed architecture.

### GitHub Actions unavailable

Scheduled/unattended publication is unavailable. Do not claim scheduler readiness from persisted `planned_at` alone.

### Platform adapter unavailable

Only that platform is unavailable; independently enabled platforms remain usable if shared prerequisites pass.

### Telegram unavailable

Publication remains authoritative and unaffected. Notifications are optional/downstream.

## Publication-consent policy

Conceptual modes:

```text
one_off_exact_confirmation
standing_auto_publish_scheduled
```

The user's selected mode belongs to connection/profile state. In all modes the Bridge receives only an exact per-platform/per-post authorization record. A standing policy is not a Bridge wildcard.

## Scheduling semantics

Remote social platforms are immediate creation targets, not current future schedulers.

```text
planned_at = earliest due threshold
GitHub Actions = scheduler
WordPress-hosted SEO Workflow Bridge = final verifier + platform adapter
remote platform = immediate creation target
```

Scheduler success alone never means publication success. Persist actual `published_at` and provider evidence separately.

Before saving executable schedule/authorization, connection-health checks known credential expiry against `planned_at`.

## LinkedIn adapter

Target:

```text
authenticated member profile
```

Bridge endpoint:

```text
POST /wp-json/seo-workflow-bridge/v1/linkedin/publish-authorized
```

Bridge re-verifies exact member/token, content/ALT/intent and delivery bytes, uploads media and accepts definitive creation only with provider evidence such as HTTP `201` + `x-restli-id`.

Current post-publication state:

```text
publication_state = published
verification.state = provider_acknowledged
verification.readback_available = false
```

LinkedIn secrets remain WordPress-side. Non-secret expiry/health metadata belongs to user profile.

## Facebook Page adapter

Target:

```text
facebook_page
```

Bridge publication endpoint:

```text
POST /wp-json/seo-workflow-bridge/v1/facebook/publish-authorized
```

Read-back endpoint:

```text
POST /wp-json/seo-workflow-bridge/v1/facebook/verify-publication
```

Current permissions include:

```text
pages_show_list
pages_read_engagement
pages_manage_posts
```

plus Page task access sufficient for `CREATE_CONTENT`.

Immediately before mutation Bridge verifies exact authorization, due/stale window, Page identity, credential validity, text/ALT/intent hashes and exact tmp-outbox media bytes/hash/MIME.

Definitive creation followed by failed read-back remains `published` with verification failure; automatic publication retry is forbidden.

## Media delivery

Canonical final media remains private/provider-backed:

```text
private final
-> exact verified tmp-outbox copy
-> Bridge downloads exact bytes
-> size/hash/MIME verification
-> platform-specific upload/create
```

WordPress media library is not CMW media storage. GitHub repository binaries are not a fallback.

## Success evidence

Persist non-secret publication evidence including platform/post ID, remote target identity, remote post/media IDs, actual `published_at`, content/media/ALT/intent hashes, delivery identity, authorization ID, API result, workflow run ID and verification state.

## Idempotency and recovery

Blind retry after uncertain external creation is forbidden. Definitive success evidence is reconciled, not recreated. Facebook transport ambiguity becomes `uncertain_external_result` until reconciled. Verification failure after definitive creation is not retryable publication.

## Optional publication reports

Telegram may report reconciled state when enabled. Telegram failure never changes successful publication state or authorizes retry.

## Platform-adapter invariant

Adding another network must not redesign immutable post identity, validated text, required final media identity/hash, `planned_at`, exact authorization, evidence/idempotency model or user-profile health model.

## References

- `docs/architecture/runtime-compatibility-matrix.md`
- `docs/architecture/user-profile-data-contract.md`
- `docs/architecture/capabilities/social-schedule.md`
- `docs/architecture/capabilities/social-connection-health.md`
- `docs/architecture/capabilities/social-publication-verification.md`
- `docs/architecture/capabilities/telegram-publication-notifications.md`
- `docs/architecture/linkedin-scheduled-publication-bridge-0.8.0.md`
- `docs/architecture/facebook-page-scheduled-publication-bridge-0.11.0.md`
- `docs/architecture/facebook-page-publication-onboarding.md`
- `docs/architecture/facebook-github-actions-scheduler.md`
- `docs/architecture/seo-workflow-bridge-capabilities.md`
