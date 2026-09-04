# Internal capability: social-connection-health

Date: 2026-09-04
Status: current capability contract

## Purpose

`social-connection-health` prevents unattended scheduled publication from discovering an expired or invalid social credential only when a post becomes due.

It is a read-mostly operational capability with one durable side effect: updating **non-secret connection-health metadata in the active user profile**.

It never stores raw credentials and never publishes content.

## Capability contract

```yaml
name: social-connection-health
purpose: Monitor configured social publication connections, warn before known credential/data-access expiry, detect scheduled posts beyond known validity, and guide safe renewal.
availability: optional
feature_gate: social.enabled
mode: read_mostly

mandatory_context:
  - docs/architecture/user-profile-data-contract.md
  - docs/architecture/schemas/user-profile.schema.json
  - active user-profile instance
  - docs/architecture/capabilities/social-publish.md
  - provider-specific onboarding/renewal contract for each configured platform

reads:
  - active project profile
  - non-secret credential expiry/data-access metadata
  - scheduled social-post frontmatter for enabled platforms
  - pending/retryable exact publication authorizations
  - read-only live Bridge provider probes when WordPress Bridge is configured

writes:
  - active user-profile connection.health metadata
  - updated non-secret observed expiry metadata when the credential owner/Bridge returns it
  - optional durable notification/issue state managed by the scheduled workflow

external_side_effects:
  - read-only provider identity/credential probe through SEO Workflow Bridge
  - optional GitHub issue creation/update/closure for renewal warnings
  - no social publication
  - no credential mutation
```

## Default health thresholds

The skill owns these default behavioral thresholds; they are not user-specific values:

```text
> 30 days       -> healthy
<= 30 days      -> renewal_due_30
<= 14 days      -> renewal_due_14
<= 7 days       -> renewal_required_7
expired/invalid -> expired_or_invalid
```

A later user-configurable threshold belongs in the user profile; until then these are generic defaults.

## Effective-expiry rules

### LinkedIn

Use OAuth access-token `token_expires_at` stored as non-secret metadata in the active user profile and refresh it from Bridge health results when available.

The current Bridge does not assume a refresh token exists. Normal renewal is a user-driven OAuth reconnect through WordPress followed by exact member re-verification.

### Facebook Page

A final Page Access Token may report no fixed token expiry. This does not make connection health unbounded.

When Meta exposes **Data Access Expiration**, persist it as:

```text
credential.data_access_expires_at
```

and use it as an effective renewal horizon.

If a future flow exposes both a fixed Page-token expiration and a Data Access expiration, use the earliest relevant known boundary.

## Live-probe rules

A daily/read-only Bridge health call verifies provider reality without publishing.

### LinkedIn

- token is present WordPress-side;
- stored WordPress expiry has not passed;
- authenticated member userinfo succeeds;
- returned member subject still matches the verified identity.

### Facebook Page

- Page token is present WordPress-side;
- exact Page `id,name` read succeeds;
- returned ID exactly matches the configured/verified Page;
- returned name may be evidence, but name drift alone never silently retargets publication.

The Bridge response must never include raw access tokens.

## Scheduled-post horizon check

Check **both** durable schedule metadata and exact executable authorization state.

### Scheduled post metadata

For each materialized social post whose platform block says:

```text
status: scheduled
planned_at: <timezone-aware timestamp>
```

compare `planned_at` with the connection's effective known expiry, even if no exact technical publication authorization exists yet.

This prevents a future schedule from being missed simply because authorization materialization occurs later in the workflow.

### Exact authorization records

For each pending/retryable exact authorization, compare candidate `planned_at` with the same effective expiry.

For either source, when:

```text
planned_at >= effective_expiry_at
```

record the post ID in `scheduled_after_expiry` and surface renewal before that publication.

Deduplicate the same post when it appears in both schedule metadata and an authorization record.

A scheduled post beyond known validity is not automatically cancelled. It is marked as requiring connection renewal before publication can be guaranteed.

## Renewal behavior

### LinkedIn

```text
WordPress -> SEO Workflow Bridge - LinkedIn
-> reconnect LinkedIn through normal OAuth authorization-code flow
-> same intended member identity must be returned
-> replace stored token atomically in WordPress
-> update token_expires_at in user profile
-> run read-only health probe
```

Changing only the credential does not invalidate approved post content or schedules when the verified remote member target remains unchanged.

### Facebook Page

Do not recreate provider application/configuration objects when only credential renewal is required.

Resume the generic credential path from the existing user profile:

```text
existing provider app/configuration
-> fresh bootstrap User Access Token when required
-> read-only exact Page/task check
-> obtain/extend appropriate User credential when required
-> derive exact Page Access Token
-> provider debugger validation
-> paste Page token directly into WordPress
-> Re-verify Facebook Page
-> update non-secret expiry/data-access metadata in user profile
-> run read-only health probe
```

Changing only the Page credential does not invalidate approved content or schedules when the exact Page ID remains unchanged.

## Fail-closed runtime relationship

Connection-health monitoring supplements but never replaces publication endpoint runtime checks.

Even if the latest daily health state is `healthy`, the Bridge still verifies token/identity prerequisites immediately before an external publication mutation.

If a live health probe reports invalidity or runtime publication reports a deterministic credential failure:

```text
health.status = expired_or_invalid
publication blocks
renewal is required
```

Do not blind-retry credential failures.

## Scheduled workflow

Current generic implementation:

```text
.github/workflows/social-connection-health.yml
scripts/social-connection-health.py
```

The workflow:

- runs daily and on manual dispatch;
- obtains short-lived GitHub OIDC;
- invokes Bridge read-only `social_connection_health`;
- evaluates profile expiry metadata, scheduled post frontmatter and pending authorizations;
- updates only non-secret profile health metadata;
- opens/updates one GitHub issue when attention is required;
- closes that issue when configured connections return healthy.

## Narrow machine-write exception

The scheduled workflow may commit an updated active profile directly to the configured default branch only for deterministic operational fields allowed by:

```text
docs/architecture/skill-package-boundary.md
```

It may update observed validity/expiry and derived `health.*` fields. It must not change account identity, preferred publication times, standing publication policy, editorial/business settings, post content, exact authorization records or any raw credential.

The push is non-force and fails on conflict.

## User-profile ownership

All concrete values below belong to user/project data, not this capability contract:

```text
site/repository identity
connection IDs
remote Page/member IDs
provider application/configuration IDs
preferred publication hours
token/data-access expiry timestamps
last health-check timestamps
health state
renewal history
```

The skill owns only the model, generic thresholds and behavior.

## References

- `docs/architecture/user-profile-data-contract.md`
- `docs/architecture/skill-package-boundary.md`
- `docs/architecture/facebook-page-token-provisioning-contract.md`
- `docs/architecture/linkedin-publication-onboarding.md`
- `docs/architecture/capabilities/social-publish.md`
