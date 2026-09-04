# Facebook Page standing scheduled-publication policy

Date: 2026-09-04
Status: normative policy model

## Purpose

Defines the **model and semantics** for an optional durable user-level publication policy that removes repetitive per-post confirmation while preserving exact technical authorization and fail-closed execution.

Whether the policy is active, for which connection, and since when are **user/profile data**, not skill defaults.

Canonical user-data location:

```text
user-data/profile.json
-> projects[active_project_id].social.connections.facebook.publication_policy
```

Generic schema/model belongs to the skill; concrete policy values belong to the user.

## Policy mode

Supported mode:

```text
standing_auto_publish_scheduled
```

Example model only:

```yaml
publication_policy:
  mode: standing_auto_publish_scheduled
  active: true
```

Do not copy this example as a default for a new user. The user must explicitly choose/authorize such behavior during onboarding or later configuration.

## User-facing semantics

When this policy is active for a user's verified Facebook Page connection:

```text
post text + visual reach fully approved/final state
-> facebook.planned_at is durably fixed
-> exact Facebook publication authorization is materialized automatically
-> scheduler publishes when due
```

The user is not asked a second repetitive “authorize Facebook publication” question for every covered scheduled post.

This does **not** bypass editorial validation. Draft, review, unapproved or incomplete posts remain non-publishable.

## Exact authorization remains mandatory

Standing consent does not create a broad runtime token or wildcard mutation request.

Every executable Facebook publication still requires one exact record under:

```text
social/publication-authorizations/facebook/<post_id>.json
```

with state:

```text
authorized_for_scheduled_publication
```

The record binds exact post ID, Page ID, planned time, text hash, ALT hash, image hash/MIME/size, delivery identity and intent hash.

The standing policy changes **how that exact record is authorized/materialized**, not Bridge/scheduler security.

## Eligible posts

Automatic exact authorization is created only when all are true:

- platform includes Facebook;
- target is exactly `facebook_page`;
- active user-profile connection is verified and production-ready;
- connection health is not known expired/invalid;
- text is approved;
- selected visual is `verified_final`;
- combined review is fully approved;
- ALT exists;
- exact timezone-aware `facebook.planned_at` exists;
- exact temporary delivery copy is verified;
- no definitive-success/uncertain external state blocks execution.

## Revision and schedule changes

Changing any bound value invalidates current exact authorization.

With a user standing policy active:

```text
change occurs
-> old exact authorization becomes non-executable
-> revised post/schedule must return to final approved durable state
-> new exact authorization may be materialized automatically
```

Never silently publish a revision that has not passed normal human content review.

## Credential renewal

Credential-only renewal does not revoke this user policy when:

- same Facebook connection remains selected;
- exact Page ID remains unchanged;
- renewed credential is verified valid.

If the target Page identity changes, treat that as a connection/target change requiring appropriate user review before existing authorizations are reused or replaced.

## Immediate publication

This policy covers scheduled publication only.

It does not grant general `publish_now` permission. Immediate publication remains separate unless another explicit policy is designed and authorized.

## Platform separation

A Facebook standing policy does not alter LinkedIn authorization semantics. Each platform keeps its own user connection/policy, scheduler, relay, authorization records and evidence.

## Revocation

The user may revoke or pause their standing Facebook policy at any time.

On revocation:

- do not create new exact Facebook authorization records from schedules;
- review/disable pending exact records that have not executed unless the user explicitly says existing scheduled publications should remain active;
- connection/token state may remain configured independently.

Persist revocation/active state only in user/project data.

## Pilot/live evidence boundary

Concrete pilot activation timestamps, test-post IDs, schedules and live-validation evidence are user/project data and may remain in excluded project checkpoints/history. They are not part of this generic policy model and must not ship in the distributable skill.

## References

- `docs/architecture/user-profile-data-contract.md`
- `docs/architecture/capabilities/social-connection-health.md`
- `docs/architecture/capabilities/social-schedule.md`
- `docs/architecture/capabilities/social-publish.md`
- `docs/architecture/facebook-github-actions-scheduler.md`
- `docs/architecture/facebook-page-scheduled-publication-bridge-0.9.0.md`
