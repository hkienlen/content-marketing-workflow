# Facebook Page publication onboarding

Date: 2026-09-04
Status: normative current onboarding contract - production path live-validated

## Purpose

Defines mandatory setup when Facebook Page publication is enabled, during initial social onboarding or later activation.

Supported target:

```text
target_type: facebook_page
```

Personal/professional Facebook profiles are not API publication targets.

The connection procedure never performs a publication. Publication consent/policy is configured only after the Page adapter is technically ready.

Concrete user/site values are read from and persisted to the active user profile. This contract contains behavior/placeholders only.

## Implementation baseline

```text
SEO Workflow Bridge: 0.10.0+
Meta Graph API: adapter-defined current version
```

Runtime publication remains compatible with `docs/architecture/facebook-page-scheduled-publication-bridge-0.9.0.md`.

Required companion contracts:

- `docs/architecture/user-profile-data-contract.md`
- `docs/architecture/facebook-page-token-provisioning-contract.md`
- `docs/architecture/user-help-facebook-page-onboarding.md`
- `docs/architecture/facebook-login-for-business-configuration.md`
- `docs/architecture/facebook-page-standing-publication-policy.md`
- `docs/architecture/capabilities/social-connection-health.md`

## Core invariants

Before Facebook publication can become ready:

- a target Facebook Page exists;
- the granting personal account has sufficient Page task access;
- compatible Bridge is installed;
- exact Graph API Page identity is verified read-only;
- final Page credential is valid, exact-Page-bound, unexposed and stored only in WordPress;
- non-secret credential lifecycle metadata is persisted in user data;
- scheduler/relay/Bridge readiness is verified;
- one controlled live publication validates a newly implemented/installed production path before declaring it live-validated.

None of the Meta/WordPress connection steps alone publishes a post.

## Active user-profile values

Resolve under the active project's Facebook social connection:

```text
connection_id
target_type
remote_id / remote_name
graph_api_version
meta_app_id
login_configuration_id / login_configuration_name
scopes
publication_policy
credential.token_expires_at
credential.data_access_expires_at
health.*
```

Actual values are not stored in this contract.

## Onboarding stages

### 1. Meta developer/app readiness

If required, register the correct Page administrator with Meta for Developers, create/select the user's Meta app and configure the content/Page-management use case.

If Meta allows a no-Business-Portfolio path and no relevant portfolio exists, do not create one solely to advance a simple own-Page flow.

Persist non-secret app identity to user data.

### 2. Minimum permissions

Require only:

```text
pages_show_list
pages_read_engagement
pages_manage_posts
```

Do not broaden permission scope unless an implemented feature requires it.

### 3. Facebook Login for Business configuration

If Graph API Explorer has no User-token configuration, create/reuse a Facebook Login for Business configuration using:

```text
Login variant: General
Token type: User Access Token
Asset scope: current Pages only
```

Persist its non-secret name/ID in user data. Do not recreate it for routine token renewal.

### 4. Bootstrap User Access Token

Use Graph API Explorer with the profile-selected app/configuration. During consent select only the intended Page for a single-Page connection.

Raw token never enters chat/GitHub.

### 5. Exact Page/task verification

Run read-only:

```text
GET /me/accounts?fields=id,name,tasks
```

Require exact intended Page and `CREATE_CONTENT`. Persist canonical verified Page ID/name to user data.

### 6. Token lifetime inspection and extension

Use Meta token debugger. Persist only non-secret metadata. A short-lived User token is bootstrap only.

Validated UI path:

```text
Outils -> Débogueur de token d'accès -> Déboguer -> Étendre le token d'accès
```

### 7. Exact Page Access Token

From the unexposed long-lived User token run:

```text
GET /me/accounts?fields=id,name,access_token,tasks
```

Select the object matching the profile Page ID. Validate its token in Meta debugger:

```text
Type: Page
Page ID: <profile remote_id>
Valid: true
expected Page scopes
```

A separate Data Access expiration, if shown, is stored as user credential-lifecycle metadata even if Page-token `Expiration` says `Never`.

### 8. WordPress handoff/read-only verification

```text
Settings -> SEO Workflow Bridge - Facebook Page
Enable connection support
Page ID: <profile remote_id>
Page Access Token: paste directly from Meta
Save
Verify Facebook Page
```

After save the token must never be rendered back. Verification must return exact profile Page identity and publishes nothing.

### 9. Scheduler/relay readiness

Verify exact OIDC trust, scheduler/relay on trusted branch, media transport and fail-closed uncertainty behavior. Do not invoke the real publication endpoint as a connection preflight.

### 10. Controlled first live validation

For a new adapter/installation, use one exact fully approved test post with explicit one-off authorization. Verify one correct visible post, media/text correctness, durable evidence and no duplicate.

Installation-specific post/run/remote IDs belong to user/project evidence/checkpoints, excluded from the generic skill package.

### 11. Future scheduled-publication consent

After production readiness, ask whether this user's future scheduled Facebook posts require per-post confirmation or use a standing scheduled auto-publication policy after normal final content/schedule validation.

Persist the selected policy in user data. The Bridge still requires an exact technical authorization for every post/revision/time. Immediate `publish_now` stays separate.

## Credential lifecycle / renewal

Bridge 0.10.0 + `social-connection-health` monitor the connection daily with a read-only Page identity call and the user's non-secret expiry/Data Access metadata.

Default warning states:

```text
J-30 renewal_due_30
J-14 renewal_due_14
J-7 renewal_required_7
expired/invalid expired_or_invalid
```

On renewal, **do not restart developer/app/configuration onboarding**. Reuse profile Meta objects and repeat only:

```text
fresh User token
-> exact /me/accounts + CREATE_CONTENT
-> Étendre le token d'accès
-> exact Page token
-> debugger validation
-> replace directly in WordPress
-> Re-verify Page
-> update profile expiry/health metadata
```

If the exact Page ID remains unchanged, credential-only renewal does not invalidate already approved content/schedules.

## Exposed-token recovery

If any raw credential appears in chat/GitHub/logs/screenshot, reject it and revoke/rotate via the user's professional-integration/app flow. This is recovery only. Preserve valid Meta app/configuration objects and resume from the last safe non-secret checkpoint.

## Resume semantics

Initial onboarding:

```text
ask configure now/later
-> persist choice
-> run only missing stages
```

Later activation/renewal:

```text
read active user profile
-> read connection health/checkpoints
-> resume at last unresolved stage
```

A production-ready Page connection must not restart from Meta developer registration unless a verified failure says those objects are missing.

## Durable state ownership

Store in user/project data, not in the skill:

```text
Meta App/config IDs
canonical Page ID/name
Graph API version actually used
observed scopes/tasks
verification timestamps
credential type/expiration/Data Access metadata
connection health/renewal state
live-validation evidence
standing publication policy
```

Store no raw token/App Secret.

## Scheduling/authorization invariant

User-specific publication times belong to `publishing_preferences`/post schedules in user data.

Always keep distinct:

```text
planned_at
!=
connection readiness
!=
publication-consent policy
!=
exact authorized_for_scheduled_publication record
!=
published
```

## References

- `docs/architecture/user-profile-data-contract.md`
- `docs/architecture/schemas/user-profile.schema.json`
- `docs/architecture/facebook-login-for-business-configuration.md`
- `docs/architecture/facebook-page-token-provisioning-contract.md`
- `docs/architecture/user-help-facebook-page-onboarding.md`
- `docs/architecture/facebook-page-standing-publication-policy.md`
- `docs/architecture/capabilities/social-connection-health.md`
- `docs/architecture/capabilities/social-publish.md`
- `docs/architecture/capabilities/social-schedule.md`
- `docs/architecture/facebook-github-actions-scheduler.md`
