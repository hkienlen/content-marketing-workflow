# Safe testing policy for internal capabilities

Date: 2026-09-01
Status: architecture contract

## Purpose

This policy defines how the Content Marketing Workflow plugin, its single primary skill and its internal capabilities are tested in this canonical repository and, when necessary, in separately owned integration/pilot environments.

A real integration/pilot environment is not a disposable sandbox. It may contain real strategy, content, repository history, external-media state, WordPress state and social workflow state; none of that state belongs in this canonical generic repository.

Testing must therefore prove behavior while creating the smallest possible amount of synthetic durable state.

## Core rule

> A test must not create synthetic durable state when an existing real item, read-only inspection, idempotent no-op or dry-run can validate the same behavior.

A technically successful test is still a bad test if it pollutes issue numbering, branches, PR history, Drive folders, WordPress content, social queues or future AI reasoning unnecessarily.

## Preferred test order

For a mutating or external-side-effect capability, prefer this order:

1. read-only inspection of existing real state;
2. idempotency/no-op verification against already valid state;
3. useful refinement of an existing real pilot item when the refinement has real project value;
4. dry-run/probe/sandbox behavior when supported;
5. controlled temporary object only when creation/deletion itself is the behavior that must be tested;
6. new permanent project state only when it is legitimate real work, not merely a test artifact.

Do not skip directly to durable object creation merely because an API supports it.

## Test planning requirement

Before a test that can mutate GitHub, Drive, WordPress or a social platform, identify:

- capability under test;
- behavior being proven;
- safest test level from the preferred order;
- exact target environment/item;
- mutations that may occur;
- human gate required, if any;
- verification method;
- cleanup/rollback behavior;
- durable evidence that should remain after the test.

For high-risk or externally visible actions, the capability-specific approval contract remains authoritative.

## GitHub testing

Before creating an issue, branch, PR, content file or state object for testing:

1. search existing real Human Items, Work Items, prompts, branches, PRs and content;
2. use an existing suitable real object when possible;
3. prefer read-only or no-op tests;
4. do not create a fake Work Item/PR merely to prove connector write availability;
5. do not consume IDs/numbers unnecessarily;
6. never merge a test PR unless it is legitimate reviewed project work and the normal merge gate is satisfied.

If creation itself must be tested, use a legitimate architecture/test change whose result is useful, or a clearly marked controlled object with planned cleanup where the platform permits deletion.

## External-media / Google Drive testing

The configured media provider may contain temporary assets and retained real finals, but tests must avoid uncontrolled clutter.

For the current Google Drive provider:

- verify configured root/domain/article/social/tmp-outbox folders by listing/reusing before creating replacements;
- never create duplicate site-domain folders merely because the capability restarted;
- test per-content folder creation with a real content item when possible;
- temporary test assets use recognizable test names and must not be mistaken for selected/final assets;
- provider presence alone never changes lifecycle state to `selected`, `normalized` or `verified_final`;
- private final assets must never be made public merely for testing;
- public-link tests use only `tmp-outbox` delivery copies;
- verify anonymous delivery bytes against the expected SHA-256;
- clean temporary outbox/test files when continued retention has no debugging/audit value;
- never delete the retained private final while cleaning a delivery copy.

When testing stable media identity, explicitly verify that changing/recreating a temporary delivery object does not change the durable final `asset_id` or create a duplicate destination object when the stable asset and SHA-256 are unchanged.

## WordPress testing

WordPress connection and preparation tests may require external writes, but must remain narrowly bounded.

### Connection testing

When functional connection verification requires create/read/delete:

- obtain required human approval before the write test;
- create one clearly identifiable temporary draft;
- keep it in `draft` status;
- read it back and verify identity;
- delete/trash according to the connection contract;
- verify cleanup;
- persist only non-secret verified connection state.

A failed cleanup is a blocker and must report/persist the exact remaining WordPress object ID.

### Media-delivery testing

Preferred progression for provider-backed WordPress media:

1. unit-test provider descriptor/URL/identity validation;
2. private-outbox negative control when useful;
3. anonymous read of a temporary delivery copy;
4. exact SHA-256 match;
5. deliberate wrong-hash fail-closed test without WordPress mutation;
6. bounded `media_upsert` using a technical object only when real Bridge mutation itself must be proven;
7. repeat the same stable asset identity/hash to verify reuse/idempotence;
8. clean technical WordPress media and temporary delivery copies after durable evidence is recorded.

A media transport test never authorizes article publication.

### Article preparation testing

Prefer a real human-validated pilot article and actual managed-draft workflow over synthetic lorem ipsum when preparation/rendering behavior is what must be proven.

For provider-backed finals, verify stable private asset identity/hash, delivery-copy SHA and returned WordPress media identity/hash.

Do not publish merely to test preparation.

### Publication testing

Do not publish a synthetic public article merely to prove the publication endpoint works.

Publication must use the real publication workflow, exact candidate/drift controls and separate explicit human `publish_now` authorization.

Read-only preflight is preferred before the publication permission window is opened.

## Social testing

- prefer parser/list/check/dry-run behavior before platform writes;
- do not create fake public posts merely to prove API access;
- preserve immutable real post IDs;
- verify provider-backed final visual identity/hash before live destination actions;
- do not use `tmp-outbox` staging as publication authorization;
- use real approved queued content for end-to-end publication tests only when the publication itself is legitimate and explicitly authorized;
- never treat a platform request as success without returned/readback evidence required by the capability contract;
- avoid contaminating the production queue with synthetic schedule entries.

## Controlled temporary external objects

A temporary object is allowed only when no safer equivalent can prove the required behavior.

Before creating it, define:

```text
why it is necessary
unique recognizable name/marker
expected target
expected lifecycle
cleanup action
cleanup verification
durable evidence that remains after cleanup
```

Examples include:

- one WordPress connection-test draft;
- one temporary Drive file used to validate delivery/read/delete behavior;
- a `tmp-outbox` transport copy;
- one bounded technical WordPress media attachment when `media_upsert` itself must be proven.

Temporary objects must never be confused with production content.

## Idempotency testing

Every mutating capability should be tested for safe restart behavior where practical.

Run or reason through at least:

1. nothing exists;
2. partial state exists;
3. intended state already exists;
4. stale/conflicting state exists;
5. previous external mutation succeeded but repository synchronization did not;
6. repository state exists but external object drifted;
7. provider final is unchanged but temporary delivery copy was recreated;
8. provider stable identity is unchanged but bytes/hash drifted.

Expected result: no duplicate IDs/folders/branches/PRs/posts/media are created merely because execution resumed or a delivery copy changed.

## Failure injection / safe-failure checks

For important mutating or publication capabilities, validate fail-closed behavior for representative conditions when feasible without harmful state.

Examples:

- missing mandatory context;
- wrong branch/PR identity;
- Drive folder ambiguity;
- inaccessible selected/final asset bytes;
- private/public delivery confusion;
- delivery response is HTML rather than an image;
- SHA-256 mismatch;
- same stable asset identity resolving to changed bytes;
- WordPress unmanaged slug collision;
- WordPress candidate drift;
- feature gate disabled;
- missing human approval;
- permission disabled;
- external response does not match request identity.

A failure-path test succeeds when the capability refuses the unsafe action and preserves valid state.

## Verification evidence

A capability is not `live-tested` merely because its files exist or a static review passed.

Distinguish at least:

```text
designed
implemented
static/readiness tested
live tested
```

`live tested` requires a representative real execution that verifies declared completion conditions.

Store useful durable test evidence in `docs/architecture/tests/` or an authoritative architecture test record when it will help future maintenance, but do not turn every routine run into a verbose permanent report.

Evidence should record:

- date;
- capability/version/commit;
- target used;
- behavior verified;
- important non-secret inputs;
- expected vs actual result;
- cleanup outcome;
- known remaining limitations.

Never store secrets in test evidence.

## Accidental mutation handling

If testing accidentally creates or changes durable state:

1. acknowledge the mutation immediately;
2. stop further dependent mutation until impact is understood;
3. reverse/delete/neutralize it where safe;
4. do not disguise it as legitimate project work;
5. document residual artifacts that cannot be removed and ensure future reasoning ignores them appropriately;
6. update test method/architecture rule when needed to avoid repetition.

The correct response to a testing mistake is cleanup plus learning, not reuse of the accidental artifact as if intended state.

## No background assumptions

Tests must complete within actual execution capabilities available to the skill.

Do not promise background checks unless an explicit supported scheduled/conditional mechanism is being used.

When a remote workflow is asynchronous and cannot be observed to completion in the current supported flow, record truthful pending state rather than claiming success.

## Human approval gates during tests

Testing does not bypass normal human gates.

Examples:

- no merge solely because a test branch exists;
- no final image selection by the system when human selection is required;
- no WordPress publication without exact publication authorization;
- no social publication without its exact state-bound authorization;
- no destructive external cleanup beyond the controlled test object without appropriate authorization.

A test may prepare everything up to a gate and verify that the gate blocks the action.

## Completion of a capability test

A test is complete only when:

- target behavior was actually verified or falsified;
- resulting durable/external state is known;
- temporary objects were cleaned up when required;
- cleanup itself was verified;
- remaining limitations are stated accurately;
- any durable architecture lesson has been persisted in the authoritative contract;
- no unaccounted test artifact remains that could mislead future executions.
