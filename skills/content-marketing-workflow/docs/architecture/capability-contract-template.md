# Internal capability contract template

Date: 2026-09-04
Status: architecture contract

## Purpose

This document defines the semantic contract for every internal capability of the single installable Content / Marketing skill.

A capability is an internal workflow boundary, not a separately installable skill.

Examples include:

- onboarding/start;
- strategy-update;
- seo-plan-article;
- seo-create-article;
- seo-update-article;
- asset-ingest;
- wordpress-connect;
- wordpress-prepare-article;
- wordpress-publish-article;
- social-extract-posts;
- social-create-visual;
- social-check-before-publish;
- social-publish.

The exact catalogue may evolve. The contract semantics below remain stable unless an explicit architecture revision replaces them.

Read this template together with `docs/architecture/github-transparency.md`. After onboarding, routine GitHub branch/commit/PR/merge operations are internal plumbing and must not become separate user approval gates.

## Canonical semantic fields

Each internal capability specification must declare at least:

```yaml
name: <stable-capability-name>
purpose: <one clear business outcome>
availability: core | optional
feature_gate: <config.path | null>
mode: read_only | mutating | external_side_effect

prerequisites: []
mandatory_context: []
optional_context: []
reads: []
writes: []
persists: []
external_side_effects: []
human_approval: []
validation: []
completion_conditions: []
next_actions: []
```

Provider-specific adapters may add technical metadata, but they must preserve these semantics and must not silently widen the business contract.

## Name and purpose

A capability name describes a stable internal business function, not one pilot site, profession, vendor or implementation detail.

Good examples:

```text
seo-create-article
asset-ingest
wordpress-prepare-article
```

Avoid names tied to:

- a concrete user/site domain;
- one profession;
- a specific WordPress builder;
- one AI provider;
- one temporary transport mechanism.

The purpose must state one principal business outcome. If one capability begins owning unrelated outcomes, split the workflow internally rather than growing an ambiguous all-purpose operation.

## Availability and feature gates

`availability` distinguishes core capabilities from optional modules of the single skill.

### Core

Core capabilities are available whenever the skill prerequisites are satisfied.

Examples:

- onboarding;
- SEO planning/content production;
- image workflow;
- GitHub persistence;
- Google Drive staging.

### Optional

Optional capabilities require an explicit persistent feature gate.

Examples:

```yaml
feature_gate: wordpress.enabled
```

for WordPress connection/preparation, or:

```yaml
feature_gate: wordpress.publish_enabled
```

for the capability to expose WordPress publication.

Social capabilities may use:

```yaml
feature_gate: social.enabled
```

until a later validated product requirement justifies a more granular social permission model.

A feature gate only makes a capability available. It never substitutes for task-specific human approval.

Example:

`wordpress.publish_enabled = true` allows the publication capability to be used, but does not authorize publishing any particular article.

## Modes

### `read_only`

May inspect repository/external state but must not mutate durable state or perform external writes.

### `mutating`

May modify durable repository/Drive state within its explicit write/persistence contract.

Must apply `docs/architecture/persistence-contract.md` and `docs/architecture/github-transparency.md`.

### `external_side_effect`

May perform externally meaningful writes such as WordPress draft creation or social/WordPress publication.

An external-side-effect capability is generally also responsible for synchronizing resulting durable metadata back into GitHub.

If the implementation supports multiple mode flags, use them. If it supports only one mode field, `external_side_effects` remains authoritative for the exact external mutation boundary.

## Prerequisites

A capability must declare and verify every condition that must be true before unsafe or irreversible work begins.

Examples:

```yaml
prerequisites:
  - Google Drive workspace verified
  - canonical article prompt exists
  - article is human validated
  - final selected assets are committed and verified
  - WordPress connection is functionally verified
```

If a prerequisite is missing:

1. stop before the unsafe step;
2. identify the exact missing condition;
3. route to the appropriate preceding internal capability when possible;
4. do not fabricate or bypass the prerequisite merely because the next action seems expected.

## Mandatory context

`mandatory_context` lists the authoritative files/data that must be reloaded for every invocation.

Rules:

- never depend only on conversation memory for mandatory directives;
- keep the list task-specific;
- use the packaged execution contract plus relevant architecture/strategy contracts;
- include `docs/architecture/github-transparency.md` for mutating capabilities that use GitHub;
- do not load the entire repository by default;
- use indexes/search/actual branch state to identify relevant content;
- fetch deeper context only when needed.

Missing mandatory context is a real blocker unless the capability explicitly owns its initialization.

## Optional context

Optional context improves quality but is not universally required.

Examples:

- Search Console exports;
- Google Ads terms;
- recent social performance;
- related articles;
- current SERP research;
- existing image assets;
- representative WordPress reference articles;
- user-provided examples or field material.

Load it when relevant, not mechanically.

## Read contract

`reads` defines the expected/authorized data areas the capability may inspect.

A read contract is a context boundary, not a prohibition against following an explicit authoritative reference needed to execute correctly.

Prefer the narrowest useful context.

## Write contract

`writes` defines durable areas the capability may modify.

A capability must not modify unrelated files or external objects simply because it has technical access.

If a required durable change falls outside its write contract, the orchestrator must:

- delegate to the appropriate internal capability/sub-workflow; or
- explicitly extend the current authorized workflow through an established contract; or
- report that persistence remains incomplete.

The user must not be expected to discover which file or index needs to be edited.

## Persistence contract

`persists` declares the durable information the capability owns.

For every persisted item, successful completion requires:

1. identify the authoritative target;
2. write the change;
3. synchronize required dependent state;
4. validate consistency;
5. record Git traceability where applicable;
6. verify persistence;
7. integrate/merge the GitHub state automatically when the current workflow's required business/content gates permit it;
8. report the useful outcome.

See `docs/architecture/persistence-contract.md` and `docs/architecture/github-transparency.md`.

## Durable vs transient decisions

Every mutating capability must classify user input and generated decisions according to the persistence contract.

Examples:

Permanent:

> From now on, never use this expression in articles.

Expected: persist in the authoritative editorial strategy.

One-off:

> For this article only, use this example.

Expected: keep it in the article/task-specific context only.

When scope is materially ambiguous and cannot be inferred safely, ask one concise clarification.

## External side-effect contract

Every external mutation must be explicitly declared.

For each external side effect, define:

- feature gate;
- prerequisite;
- exact target identity;
- expected input;
- allowed mutation boundary;
- verification method;
- durable metadata to synchronize afterward;
- rollback/recovery or safe-failure behavior when practical.

Do not expose broad shell/filesystem/database execution merely as a generic extension mechanism when a bounded adapter/API can perform the required operation.

## Human approval contract

`human_approval` lists **business/content/external-side-effect gates** the capability must never bypass.

Examples:

```yaml
human_approval:
  - final article validation
  - final image selection
  - WordPress publish_now authorization
  - destructive overwrite/delete when the intended content outcome is ambiguous
```

Routine GitHub mechanics are **not** human-approval items after onboarding. Do not add `merge authorization`, `branch approval`, `commit approval` or `PR approval` as user gates unless a later architecture decision explicitly overrides `docs/architecture/github-transparency.md`.

Approval is state-specific.

A previous business/content approval cannot be reused silently after a material change to the item being acted upon.

A feature gate such as `wordpress.publish_enabled` never replaces the task-specific publication approval.

## Validation contract

`validation` defines objective checks required before completion.

Examples:

- persisted file exists at the intended path;
- article front matter is valid;
- immutable post ID is unique;
- selected image exists in the expected Drive folder;
- final asset exists in the configured provider workspace and matches required dimensions/format/hash;
- branch/PR/merge state matches the intended task;
- WordPress returned the expected managed post ID and status;
- publication URL is on the expected host and returns the required state.

Verify actual persisted/external state whenever possible, not merely the in-memory output that was intended to be written.

## Completion conditions

A capability must explicitly define when it is complete.

Example for a review-ready article production step:

```yaml
completion_conditions:
  - intended article branch reused or created exactly once
  - article persisted and verified
  - required image proposals stored in Drive
  - review state persisted
  - one PR exists
  - review batch presented to the user
```

A later validation/integration step may complete with:

```yaml
completion_conditions:
  - article and required media are human validated
  - final snapshot requirements satisfied
  - PR technically verified
  - merge performed automatically
  - merge verified
```

This prevents stopping after producing text while required persistence, verification or external synchronization remains undone, without introducing a GitHub-only user gate.

## Git mutation policy

Every mutating capability must define one of the allowed Git patterns for its work, such as:

- dedicated work branch + PR;
- continuation of an existing branch/PR;
- dedicated architecture/configuration branch + PR;
- another explicitly validated low-friction operational-state policy.

General rules:

- inspect real branch/PR state before creating anything;
- reuse existing active task branches/PRs;
- do not create duplicate PRs;
- perform routine branch creation, commit, PR update/synchronization and merge automatically when workflow prerequisites are satisfied;
- never use GitHub mechanics as a separate user approval gate;
- involve the user only when a repository conflict requires choosing between materially different business/content outcomes or when permissions/setup are missing;
- do not rewrite immutable IDs;
- verify resulting Git state.

## Idempotency and resumability

Mutating and external-side-effect capabilities should be restartable when practical.

On invocation, inspect existing durable state before creating new state.

Examples:

- onboarding asks only unresolved questions;
- Drive workspace setup reuses existing folders;
- SEO article creation reuses an existing branch/PR;
- `asset-ingest` does not duplicate an already verified final asset needlessly;
- WordPress connect recognizes an already verified connection;
- WordPress preparation reuses the same managed draft identity;
- social workflows do not allocate duplicate immutable IDs.

Never assume a prior run fully succeeded or fully failed.

## Failure behavior

Minimum failure rules:

- do not claim success;
- do not fabricate missing data;
- stop before dependent destructive/external steps;
- preserve valid existing state;
- record the highest truthful durable checkpoint when useful;
- state the exact completion condition that remains unsatisfied;
- keep enough durable state to resume safely;
- never substitute conversation memory for failed persistence;
- repair ordinary GitHub bookkeeping automatically when safe instead of asking the user to operate Git.

## User interaction rule

The user supplies business intent, choices and approvals.

The skill handles operational mechanics.

The user should not normally need to know:

- which file stores a strategy decision;
- which index must be synchronized;
- which Git command would be needed;
- which branch/PR/commit/merge operation is required;
- which Drive folder ID is used internally;
- which metadata field stores a platform state;
- whether a routine commit is needed.

Ask only for information, business choices or genuine human gates that cannot be derived or safely decided by the system.

## Reporting contract

At completion, report compactly:

- meaningful result;
- durable state changed;
- external action performed and verified when relevant;
- remaining business/content/publication gate or blocker;
- recommended next action.

Do not make GitHub/Drive plumbing the primary end-user interface unless the user explicitly requests technical details.

## Canonical capability skeleton

````markdown
# Capability: <name>

## Purpose
<one principal business outcome>

## Contract

```yaml
name: <name>
purpose: <purpose>
availability: core|optional
feature_gate: null|<config.path>
mode: read_only|mutating|external_side_effect

prerequisites:
  - ...
mandatory_context:
  - ...
optional_context:
  - ...
reads:
  - ...
writes:
  - ...
persists:
  - ...
external_side_effects:
  - ...
human_approval:
  - ...
validation:
  - ...
completion_conditions:
  - ...
next_actions:
  - ...
```

## Workflow
1. ...
2. ...

## Durable vs transient decisions
...

## Git / Drive / external mutation policy
...

## Failure and resume behavior
...

## User-facing completion report
...
````

## Acceptance test for a capability design

Before considering an internal capability contract mature, verify:

1. Can it execute correctly in a fresh conversation after loading only its declared mandatory context plus resolved task input?
2. Does it know exactly which durable information it owns?
3. Does it persist durable user decisions automatically?
4. Does it avoid turning one-off instructions into global rules?
5. Are its read/write/external mutation boundaries explicit?
6. Are optional feature gates explicit where relevant?
7. Does it verify external actions rather than infer success from requests?
8. Does it preserve required business/content/publication human gates while keeping routine GitHub mechanics transparent?
9. Can it resume without duplicating IDs, folders, branches, PRs or external objects?
10. Does it avoid pilot-site/provider assumptions in its generic business contract?
11. Does it remain an internal capability of one installable skill rather than becoming an independent product by accident?

If any answer is no, revise the contract before calling the capability production-ready.
