# Internal capability: social-schedule

Date: 2026-09-05
Status: current implementation contract

## Purpose

`social-schedule` persists intended publication times for approved social posts, preserves global editorial balance and prepares exact per-platform/per-post authorization for unattended publication according to active user policy.

Global prerequisite/degradation behavior is owned by:

```text
docs/architecture/runtime-compatibility-matrix.md
```

Scheduling metadata and technical publication authorization remain distinct states.

## Capability contract

```yaml
name: social-schedule
purpose: Persist per-platform planned publication times and, when prerequisites/policy allow, materialize exact scheduled-publication authorization without publishing immediately.
availability: optional
feature_gate: social.enabled
mode: mutating
```

## Common prerequisites

Before persisting a schedule:

- active user/project profile resolved;
- `social.enabled = true`;
- immutable registered `post_id`;
- approved text;
- required final visual `verified_final`;
- `visual_alt_text` for the required visual;
- target platforms/connections known;
- global editorial-balance check complete.

Before marking unattended publication operational or creating exact authorization, additionally require:

- `github_repository` operational;
- `cloud_media_storage` operational;
- required exact final image remains `verified_final`;
- `wordpress_bridge_runtime` operational because current LinkedIn/Facebook relays use SEO Workflow Bridge hosted in WordPress;
- `github_actions_scheduler` operational;
- compatible platform adapter enabled/connected;
- exact verified remote identity;
- connection health not known expired/invalid;
- exact timezone-aware `planned_at`;
- exact text/ALT/image hashes and image MIME/size;
- verified temporary delivery copy in configured `tmp-outbox`;
- publication consent satisfied under active user/platform policy.

If any publication prerequisite is absent, CMW may retain planning metadata if useful, but must not describe unattended scheduling as operational and must not create/reuse an authorization as though publication were executable.

Strict media invariant:

```text
no required verified final media
=> no social publication
```

There is no text-only degraded publication fallback.

## Durable timing preferences

Read user-specific defaults from:

```text
user-data/profile.json
-> projects[active_project_id].publishing_preferences.timezone
-> projects[active_project_id].publishing_preferences.social.<platform>.default_time
```

Resolution priority:

```text
1. exact date/time explicitly selected for the post/platform
2. durable user profile platform time
3. generic recommended default
```

Changing a reusable preference does not silently move existing scheduled posts.

## Credential-validity horizon gate

Before finalizing executable schedule/authorization, read platform connection health.

If known `effective_expiry_at` exists and `planned_at >= effective_expiry_at`:

- persist chosen planning time if appropriate;
- record renewal blocker;
- surface that credentials do not cover the slot;
- do not claim publication readiness.

Renewal preserving exact remote identity may clear this operational blocker without reapproval of unchanged content/schedule.

## Global editorial balance

Before fixing a slot, inspect neighbouring scheduled/published content across series/free posts.

Default behavior:

- avoid consecutive strong conversion/CTA posts when reasonable alternative exists;
- prefer identification/expertise/positioning between strong commercial posts;
- never silently move a user-selected date;
- persist rationale for deliberate exception.

## Current scheduling model

Current LinkedIn/Facebook adapters do not store future calendar remotely. GitHub Actions owns timing and WordPress-hosted SEO Workflow Bridge performs final verification/adapter execution.

```text
approved post + verified_final
-> planned_at persisted
-> compatibility + credential horizon checks
-> exact per-platform authorization
-> exact tmp-outbox copy
-> GitHub Actions scheduler
-> OIDC relay
-> WordPress / SEO Workflow Bridge
-> immediate remote publication when due
-> actual published_at / provider evidence persisted
```

`planned_at` is earliest allowed time. Scheduler latency may make actual publication later, never earlier.

## Missing-runtime behavior

### WordPress/Bridge unavailable

Content planning/review may continue, but current automated LinkedIn/Facebook publication is unavailable. Do not substitute direct provider publication silently.

### GitHub Actions unavailable

Planning metadata may remain, but unattended publication is not operational. Do not claim scheduled publication is active.

### Cloud media unavailable

No durable final/delivery copy can satisfy current publication contract. Do not fall back to GitHub/WordPress/local filesystem or text-only publication.

## Platform independence

LinkedIn and Facebook Page adapters are gated independently. Missing one adapter does not block the other if all shared prerequisites are operational.

Facebook personal/professional profile is not a fallback target.

## Exact authorization semantics

`status: scheduled` alone is never runtime mutation authority.

Required unattended state:

```text
authorized_for_scheduled_publication
```

Authorization is platform-specific, post-specific, content/media/time/target-bound and invalidated by relevant drift.

## Media delivery

Private retained final remains canonical:

```text
private final
-> exact temporary public-read tmp-outbox copy
-> persisted delivery ID + expected SHA/MIME/size
-> Bridge downloads/re-verifies immediately before upload
```

Outbox is transport only and should be cleaned after verified publication when practical.

## Completion conditions

Planning is complete when exact `planned_at`, timezone, target/connection and editorial-balance result are persisted.

Unattended execution readiness additionally requires the full prerequisite graph, exact authorization and verified delivery state. Missing prerequisites/known expiry remain explicit blockers.

## References

- `docs/architecture/runtime-compatibility-matrix.md`
- `docs/architecture/user-profile-data-contract.md`
- `docs/architecture/capabilities/social-connection-health.md`
- `docs/architecture/capabilities/social-publish.md`
- `docs/architecture/facebook-page-standing-publication-policy.md`
- `docs/architecture/linkedin-scheduled-publication-bridge-0.8.0.md`
- `docs/architecture/facebook-page-scheduled-publication-bridge-0.11.0.md`
- `docs/architecture/facebook-github-actions-scheduler.md`
