# Internal capability: social-schedule

Date: 2026-09-04
Status: current implementation contract

## Purpose

`social-schedule` persists the intended publication calendar for approved social posts, preserves global editorial balance and prepares exact per-platform/per-post authorization for unattended publication according to the active user policy.

Scheduling metadata and technical publication authorization remain distinct states.

Concrete timezone/platform publication preferences and connection-health/expiry values belong to the active **user profile**, not this skill contract.

## Capability contract

```yaml
name: social-schedule
purpose: Persist per-platform planned publication times and, when allowed by active user publication policy, materialize exact scheduled-publication authorization without publishing immediately.
availability: optional
feature_gate: social.enabled
mode: mutating
```

## Common prerequisites

Before scheduling:

- active user/project profile resolved;
- `social.enabled = true`;
- immutable registered `post_id`;
- approved text;
- required final visual `verified_final`;
- `visual_alt_text` when a visual exists;
- target platforms/connections known;
- global editorial-balance check complete.

Before creating unattended-publication authorization, additionally require:

- compatible adapter/Bridge installed and connected;
- exact verified remote identity;
- connection health is not known `expired_or_invalid`;
- exact timezone-aware `planned_at`;
- exact text + SHA-256;
- exact ALT + SHA-256;
- exact final image SHA-256/MIME/size;
- verified temporary delivery copy in configured `tmp-outbox`;
- publication consent satisfied under the active user/platform policy.

## Durable timing preferences

Read user-specific defaults from:

```text
user-data/profile.json
-> projects[active_project_id].publishing_preferences.timezone
-> projects[active_project_id].publishing_preferences.social.<platform>.default_time
```

Generic model example only:

```yaml
publishing_preferences:
  timezone: <IANA timezone>
  social:
    facebook:
      default_time: "HH:MM"
    linkedin:
      default_time: "HH:MM"
```

Resolution priority:

```text
1. exact date/time explicitly selected for the post/platform
2. durable user profile platform time
3. generic recommended default
```

Changing a reusable preference does not silently move existing scheduled posts.

## Credential-validity horizon gate

Before finalizing a schedule or exact authorization, read the platform connection health from the active user profile.

If a known `effective_expiry_at` exists and:

```text
planned_at >= effective_expiry_at
```

then:

- persist the schedule if the user chose it;
- mark the post under `health.scheduled_after_expiry` through `social-connection-health`;
- surface that connection renewal is required before publication can be guaranteed;
- do not pretend current credentials cover that date.

A future credential renewal that preserves the exact remote identity clears this operational blocker without requiring reapproval of unchanged post content/schedule.

## Global editorial balance

Before fixing a slot, inspect neighbouring scheduled/published content across series and free posts.

Default behavior:

- avoid consecutive strong conversion/CTA posts when a reasonable alternative exists;
- prefer identification/expertise/positioning between strong commercial posts;
- never silently move a user-selected date;
- persist rationale for a deliberate exception.

## Current scheduling model

Neither LinkedIn nor Meta stores the future calendar for current adapters. GitHub Actions owns timing.

```text
approved final post
-> planned_at persisted
-> connection validity horizon evaluated
-> exact per-platform authorization materialized under active user policy
-> exact tmp-outbox delivery copy
-> platform scheduler every 10 minutes
-> dedicated OIDC relay
-> SEO Workflow Bridge
-> immediate remote publication when due
-> actual published_at / remote evidence persisted
```

`planned_at` is the earliest allowed time. Scheduler latency may make actual publication later, never earlier.

## Facebook Page target

```yaml
facebook:
  status: scheduled
  planned_at: <ISO 8601 + timezone>
  target_type: facebook_page
  connection_id: <active user-profile Facebook connection>
```

Before Facebook authorization require compatible Bridge, Page capability enabled, exact Page credential stored in WordPress, Page identity verified, scheduler/relay live validation complete and target connection resolving to the exact profile Page.

Facebook authorization binds at minimum post ID, planned time, target type, Page ID, text/ALT/image hashes, image MIME/size, delivery identity, publication-intent hash and authorization ID/time.

## Facebook standing scheduled-publication policy

The active user's Facebook `publication_policy.mode`, if configured, determines whether the exact authorization requires a one-off confirmation or may be materialized automatically after final content + schedule validation.

A standing policy is a **user profile value**, not a generic skill default.

Changing text, ALT, image, Page target or `planned_at` invalidates the exact authorization. A replacement may be materialized automatically only when the user's policy allows it and the revised state is final/approved again.

Immediate `publish_now` remains separate.

## LinkedIn target

LinkedIn uses the authenticated verified member-profile adapter. Authorization binds post ID, planned time, author URN, text/ALT/image/intent hashes, image MIME/size, delivery identity and authorization ID/time.

LinkedIn publication-consent policy is independent from Facebook and belongs to user/project state when configured.

## Exact authorization semantics

`status: scheduled` alone is never the runtime mutation grant.

Required unattended state:

```text
authorized_for_scheduled_publication
```

Authorization is platform-specific and post-specific.

## Media delivery

The private retained final remains canonical.

```text
private final
-> exact temporary public-read tmp-outbox copy
-> persisted delivery ID + expected SHA/MIME/size
-> Bridge downloads/re-verifies immediately before platform upload
```

The outbox copy is transport only and should be cleaned after verified publication when practical.

## Completion conditions

Scheduling is complete when exact `planned_at`, explicit timezone, target/connection, global balance result and final media identity are persisted.

Execution readiness additionally requires exact platform authorization + verified delivery state. Known connection expiry before the slot must be visible as an explicit renewal blocker rather than silently ignored.

## References

- `docs/architecture/user-profile-data-contract.md`
- `docs/architecture/capabilities/social-connection-health.md`
- `docs/architecture/capabilities/social-publish.md`
- `docs/architecture/facebook-page-standing-publication-policy.md`
- `docs/architecture/linkedin-scheduled-publication-bridge-0.8.0.md`
- `docs/architecture/facebook-page-scheduled-publication-bridge-0.9.0.md`
- `docs/architecture/facebook-github-actions-scheduler.md`
