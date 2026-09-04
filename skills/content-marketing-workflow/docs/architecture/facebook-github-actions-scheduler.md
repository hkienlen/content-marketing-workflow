# Facebook Page publication scheduler - GitHub Actions

Date: 2026-09-04
Status: normative scheduler contract

## Purpose

GitHub Actions owns future timing for the Facebook Page adapter. Meta is called only when an exact persisted Facebook Page authorization becomes due.

The scheduler never interprets a Page token, connection state or standing user policy as a wildcard publication grant.

## Components

Timing workflow:

```text
.github/workflows/facebook-scheduler.yml
```

Dedicated publication relay:

```text
.github/workflows/facebook-publish-relay.yml
```

State engine:

```text
scripts/facebook-scheduler-v1.py
```

Authorization directory:

```text
social/publication-authorizations/facebook/
```

Historical consumed authorizations may be archived in subdirectories; the scheduler scans only top-level `*.json` records.

## Cadence

The scheduler runs every 10 minutes by default in the current workflow template.

`planned_at` is an earliest-publication threshold, not a promise that GitHub Actions starts on the exact minute.

The Bridge independently rejects early requests and requests more than 24 hours late.

## Due selection

Only authorization records satisfying all of the following are eligible:

- schema valid;
- target type exactly `facebook_page`;
- authorization status exactly `authorized_for_scheduled_publication`;
- candidate/authorization binding exact;
- text/ALT/intent hashes valid;
- execution state `pending` or `retryable_error`;
- `planned_at <= now < planned_at + 24h`.

The scheduler contains no hard-coded post IDs and no Page token.

A post present in the social queue but lacking an exact authorization file is invisible to automatic execution.

## Standing publication policy interaction

A user may explicitly select:

```text
standing_auto_publish_scheduled
```

This policy acts **upstream** of the scheduler: after normal final content + schedule validation, the skill may automatically materialize the exact per-post authorization file.

The scheduler itself is unchanged and remains strict. It does not publish merely because the standing policy exists.

See:

```text
docs/architecture/facebook-page-standing-publication-policy.md
```

The selected policy is user/project data and is never hard-coded into the generic scheduler.

## Dispatch

For every due exact authorization:

```text
facebook-scheduler.yml
-> workflow_dispatch facebook-publish-relay.yml
-> input = exact authorization_path
```

The timing workflow has only repository read + Actions dispatch permissions. It does not hold Meta credentials and does not call WordPress directly.

## Dedicated relay

The publication relay:

1. validates the authorization path is under `social/publication-authorizations/facebook/`;
2. rebuilds the exact request with `scripts/facebook-scheduler-v1.py`;
3. resolves the WordPress Bridge connection profile;
4. requires the Facebook endpoint to be HTTPS on the exact expected WordPress hostname;
5. obtains a short-lived GitHub OIDC token for the configured audience;
6. calls only `/facebook/publish-authorized`;
7. persists the Bridge response into authorization/post durable state;
8. applies post-publication verification state according to the current Facebook verification contract;
9. pushes only the resulting durable publication/verification state back to the configured default branch.

No Page Access Token or Meta App Secret is present in GitHub Actions.

## OIDC trust

Bridge trust remains pinned to the configured private repository identity, owner, audience and workflow identity.

For `workflow_dispatch`, the Bridge explicitly allows only the dedicated configured publication workflow identities required by the enabled adapters. This is not a wildcard social workflow trust rule.

## Success reconciliation

Scheduler success is only due-record detection and relay dispatch. It is not publication evidence.

When Bridge returns definitive creation evidence bound to the current exact authorization, durable publication state may become:

```text
publication_state = published
```

The current Facebook adapter then performs bounded read-only remote verification. Only successful read-back may set:

```text
verification_state = remote_verified
```

The post's Facebook block preserves original `planned_at`, Page target/connection and actual `published_at`/remote evidence.

## Retryable failures

A deterministic pre-publication failure that is safe to re-evaluate may persist:

```text
execution.state = retryable_error
```

The exact authorization must still match when retried.

## Uncertain Meta creation

If Bridge reports an uncertain external creation result, durable state becomes equivalent to:

```text
execution.state = uncertain_external_result
requires_human_reconciliation = true
```

This state is excluded from due selection.

Do not automatically retry because Meta may already have created the Page post.

## Definite creation followed by verification failure

A definite provider creation followed by failed remote read-back is **not** a retryable publication failure.

The post remains known as created/published according to the definitive creation evidence, while verification is marked failed/unavailable for reconciliation.

Never republish merely to make remote verification pass.

## Live-validation evidence boundary

A new adapter/installation requires one controlled first live validation before production readiness.

Installation-specific evidence such as exact post IDs, Page IDs, scheduler/relay run IDs, remote post/media IDs, timestamps and human visual confirmation belongs to user/project checkpoints/state and is excluded from the generic skill package.

The generic scheduler contract retains only the validated behavior and safety rules learned from those tests.

## Separation from other relays

Keep these independent:

```text
wordpress-relay.yml              -> WordPress article/bounded operations
linkedin-publish-relay.yml       -> LinkedIn scheduled publication
facebook-publish-relay.yml       -> Facebook Page scheduled publication
```

Do not merge them into one broad mutation workflow merely for convenience.

## Authorization invariant

The exact JSON record remains mandatory regardless of whether consent was collected one-off or from a durable standing scheduled-publication policy.

Connection setup, Page token possession, Page verification, `status: scheduled` and a due time are never sufficient by themselves.

Provider evidence returned from an older authorization/idempotency record must not be accepted as proof for a new exact authorization unless all bound identities/hashes/timing fields match the current authorization contract.
