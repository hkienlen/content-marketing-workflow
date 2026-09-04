# LinkedIn scheduled publication - generic GitHub Actions scheduler

Date: 2026-09-03
Status: normative contract
Bridge minimum version: `0.8.0`

## Decision

LinkedIn's organic Posts API is used only for immediate `PUBLISHED` creation. Scheduled delivery is therefore owned by GitHub Actions, not by LinkedIn and not by a server cron.

The mainstream path requires no cron, daemon, systemd service or additional server administration.

## Generic pipeline

```text
exact post approved
-> planned_at persisted
-> exact per-post scheduled-publication authorization persisted
-> exact final media copied temporarily to Google Drive tmp-outbox
-> linkedin-scheduler.yml checks due authorizations every 10 minutes
-> scheduler dispatches linkedin-publish-relay.yml for each due authorization
-> dedicated relay obtains short-lived GitHub OIDC
-> SEO Workflow Bridge verifies OIDC + exact authorization + current state
-> Bridge downloads and hashes the exact tmp-outbox image
-> Bridge uploads that exact image to LinkedIn
-> Bridge creates one LinkedIn post
-> HTTP 201 + x-restli-id persisted as publication evidence
-> relay synchronizes GitHub post/authorization state
```

The scheduler workflow contains no post-specific IDs. New authorized posts are added only by persisted authorization records.

## Authorization semantics

Automatic publication is authorized **per post and per exact revision**.

A record is eligible only when:

```text
authorization.status = authorized_for_scheduled_publication
execution.state = pending | retryable_error
planned_at <= now < planned_at + 24h
```

The exact authorization binds at least:

- immutable `post_id`;
- `planned_at` including timezone;
- verified LinkedIn author URN;
- exact text SHA-256;
- exact ALT-text SHA-256;
- exact final-image SHA-256;
- image MIME and byte size;
- temporary delivery provider/file identity;
- composite publication-intent SHA-256;
- authorization ID and authorization timestamp.

Changing a bound value invalidates the authorization. A post that is merely approved or has `planned_at` but lacks this exact authorization must never be dispatched.

## Media transport

The retained final remains the private provider-backed Google Drive asset. GitHub stores its durable provider identity/hash metadata.

For an authorized scheduled publication, the skill creates an exact temporary delivery copy in the site's public-by-link `tmp-outbox`. The authorization binds the delivery file ID plus the retained final SHA-256, MIME and byte length.

Immediately before any LinkedIn mutation, Bridge `0.8.0+` downloads the delivery copy and verifies:

1. HTTP fetch succeeds;
2. exact byte length matches;
3. exact SHA-256 matches the approved final;
4. detected PNG/JPEG MIME matches.

Only verified bytes are uploaded to LinkedIn. The LinkedIn image URN is generated at runtime and is therefore publication evidence, not an authorization identity.

The temporary outbox copy should be removed after verified publication when practical. The private retained final must never be removed by outbox cleanup.

## Scheduler timing

The default scheduler cadence is every 10 minutes.

`planned_at` remains the earliest intended publication time. GitHub Actions schedules are not guaranteed to start exactly on the cron minute, therefore actual publication may occur after `planned_at`. The workflow must never publish before `planned_at`.

More than 24 hours late is treated as stale and requires review rather than silently publishing old content.

## OIDC trust boundary

The timing workflow `linkedin-scheduler.yml` does not hold LinkedIn credentials and does not call WordPress directly. It may only dispatch the dedicated `linkedin-publish-relay.yml` workflow for exact due authorization paths.

The dedicated publication relay:

- runs only through `workflow_dispatch`;
- has the minimum GitHub permissions needed for OIDC and evidence synchronization;
- obtains a short-lived GitHub Actions OIDC token;
- calls only the configured HTTPS `linkedin_publish_endpoint` on the expected WordPress host;
- never receives the LinkedIn Client Secret or access token.

SEO Workflow Bridge verifies repository identity, owner, visibility, audience and exact workflow reference. The existing issue-driven WordPress relay remains separate and is not expanded to accept arbitrary scheduler operations.

## Idempotency and recovery

WordPress stores successful publication evidence keyed by `post_id` before returning success. If GitHub synchronization fails after LinkedIn accepted the post, the next exact attempt must receive the already stored evidence instead of creating another post.

A fresh scheduler request ID is allowed for recovery, but duplicate remote creation is forbidden when Bridge already holds successful evidence.

GitHub persists at least:

- publication state;
- remote `x-restli-id`;
- `published_at`;
- `planned_at`;
- authorization ID;
- author URN;
- text/image/ALT/intent hashes;
- runtime LinkedIn image URN;
- final Posts API payload SHA-256;
- LinkedIn API version;
- GitHub Actions run ID.

## Current pilot authorizations

The user explicitly authorized scheduled LinkedIn publication for exactly:

- `2026-0003` at `2026-09-08T07:30:00+02:00`;
- `2026-0004` at `2026-09-10T07:30:00+02:00`.

No other post is authorized by that decision.

Canonical records:

```text
social/publication-authorizations/linkedin/2026-0003.json
social/publication-authorizations/linkedin/2026-0004.json
```

## Future skill requirement

The future skill must make this automatic for ordinary users. When an approved post is scheduled and the user authorizes its automatic LinkedIn publication, the skill must create/verify the exact authorization and temporary delivery asset itself. The user must not need to edit YAML, JSON, GitHub Actions, WordPress files or cron configuration.
