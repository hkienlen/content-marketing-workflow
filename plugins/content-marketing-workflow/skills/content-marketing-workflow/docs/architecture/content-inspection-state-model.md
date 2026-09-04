# Content inspection state model

Date: 2026-09-02
Status: architecture contract

## Purpose

This contract defines how read-only inspection commands derive concise user-facing states for articles and social content from existing durable sources.

The inspection layer must never become a second workflow-state authority. It reads authoritative files/checklists/platform state, derives a display state, and returns it without mutation.

## General invariant

`list` and `details` operations are read-only.

They must not:

- change article/post status;
- allocate IDs;
- update checklists;
- create WordPress drafts;
- schedule or publish anything;
- infer completion from conversation memory when durable state disagrees.

When sources conflict or are incomplete, expose the ambiguity rather than silently choosing the most optimistic state.

## Evidence classes and precedence

Inspection must distinguish durable evidence by strength rather than trusting one convenient field.

For state derivation, use this general precedence from strongest to weakest:

1. verified remote/readback evidence bound to the exact managed object/candidate;
2. exact durable workflow checklist/gate evidence;
3. exact persisted managed-object metadata/manifest/candidate state;
4. canonical object front matter/body metadata;
5. related Work Item/Human Item/backlog state;
6. conversation memory only as a clue to locate durable evidence, never as final authority when durable state exists.

A weaker source cannot upgrade a state contradicted by a stronger source.

Example: article front matter `status: published` plus a `published_url` on a test hostname does not establish production publication when no verified production readback exists.

## Article identity resolution

`/article details <article>` must resolve an article by the strongest unambiguous identifier available, including:

1. exact repository path, e.g. `articles/<audience>/<article-slug>.md`;
2. exact filename, e.g. `<article-slug>.md`;
3. exact front-matter slug;
4. exact filename stem as a convenience identifier.

Do not treat approximate/fuzzy title similarity as identity resolution for an explicit `details` command.

If more than one article matches a non-path identifier, return `IDENTITY_AMBIGUOUS` with matching candidates rather than guessing.

If no article body exists, an exact planned Work Item/Human Item may appear in `/article list` as `planned`, but `/article details` must not fabricate article content. It may return the durable planning record only if the command implementation explicitly represents it as a non-materialized planned article and makes clear that no Markdown article exists yet.

## Article inspection sources

Use, as applicable:

- article Markdown/front matter;
- `articles/<target>/<slug>.checklist.md` or exact article-linked checklist;
- related Work Item/Human Item state when needed;
- WordPress preparation/presentation state persisted by the WordPress workflow;
- immutable WordPress publication candidate/readback evidence;
- `published_url`, `published_at` only as supporting metadata, not sufficient publication proof by themselves;
- verified production publication/readback evidence when available.

The mere existence of a rendered Divi file, WordPress config file, manifest template or test-site page is not sufficient to claim a managed WordPress draft or production publication state unless the authoritative WordPress workflow records that state.

## Article display states

The following are synthetic display states only. They summarize authoritative durable evidence and do not replace it.

```text
planned
created
drafting
review
approved
wordpress_draft
wordpress_validated
published
blocked
unknown
```

## Deterministic article state derivation

Evaluate in the following order. The first state whose conditions are satisfied wins, except that contradictory evidence may force `unknown` with an evidence note.

### 1. `published`

Require all applicable conditions:

- verified production/public readback or equivalent authoritative publication evidence exists for the exact article/candidate;
- evidence identifies the production/public environment rather than test/preprod;
- durable workflow state does not explicitly say the publication was reverted/invalidated;
- public URL is consistent with the configured production/public site identity when that identity is known.

A front-matter `status: published` alone is insufficient.

### 2. `blocked`

Use when the authoritative current workflow explicitly records a blocking condition that prevents the next required step.

Do not turn a merely awaiting-human review into `blocked` unless the workflow marks it blocked.

### 3. `wordpress_validated`

Require durable evidence that:

- the managed WordPress draft exists for the exact article/version;
- technical readback has passed;
- required WordPress/editor presentation validation (`WordPress OK` or equivalent) is durably recorded;
- production publication is not verified.

### 4. `wordpress_draft`

Require durable evidence that:

- the controlled managed draft exists;
- required technical preparation/readback has succeeded to the point defined by `wordpress-prepare-article`;
- WordPress/editor validation is not yet durably complete;
- production publication is not verified.

### 5. `approved`

Require durable evidence that the article/content-media workflow has passed its final required human content/media validation and internal integration gate, while no stronger WordPress state applies.

### 6. `review`

Use when durable checklist/gate evidence shows the article or required media has been presented for human review and one or more required human review decisions remain.

### 7. `drafting`

Use when an article body exists and durable workflow evidence shows required drafting/research/media preparation is still underway before the human-review gate.

### 8. `created`

Use when the article body exists but there is not enough positive workflow evidence to classify it as `drafting`, `review`, `approved` or a stronger state.

### 9. `planned`

Use when an exact durable planned/backlog/work record exists but no materialized article body exists.

### 10. `unknown`

Use when evidence is materially inconsistent or insufficient to make one of the above claims. Include the conflicting/missing evidence in `evidence_notes`.

## Article WordPress/publication substate

The list/details renderer should keep the synthetic overall state separate from explicit WordPress/publication facts, e.g.:

```yaml
wordpress:
  managed_draft: true|false|unknown
  technical_readback: passed|failed|unknown
  human_validated: true|false|unknown
publication:
  verified: true|false|unknown
  environment: production|preprod|test|unknown
  url: <verified production URL|null>
```

This prevents a single label from hiding useful distinctions.

## Article list output

`/article list` should return a compact table/list with at least:

- title or slug;
- repository path or planned-record identity;
- synthetic article state;
- WordPress state when applicable;
- publication state/public URL when verified.

Optional useful columns include target, Work Item, primary keyword and last known next gate.

Enumeration rules:

1. enumerate materialized article bodies under configured article roots, excluding checklist/media/support files;
2. join exact article-linked workflow/checklist/WordPress evidence;
3. optionally add exact planned Work Items/Human Items that identify a future article and have no materialized body;
4. deduplicate planned/materialized records by exact durable relationship, never fuzzy title similarity;
5. sort deterministically by configured editorial priority when available, otherwise by stable path/identifier.

## Article details output

`/article details <article>` must return at least:

- resolved article identity/path;
- title/slug/target and useful SEO metadata;
- synthetic article state with evidence summary;
- current editorial/media gate;
- WordPress draft/validation/publication state when applicable;
- public URL when verified;
- complete current article Markdown content when materialized.

Do not modify the article merely because it is displayed.

## Social identity resolution

`/social details <post-or-concept>` must resolve by:

1. exact immutable `post_id` when materialized, e.g. `<post-id>`;
2. exact `series_concept` key from an article `series-plan.md`;
3. exact social post path when supplied.

`post_id` uniqueness must also be cross-checked against `social/id-registry.json` when present.

If a loose identifier is ambiguous, return `IDENTITY_AMBIGUOUS` with candidates rather than guessing.

## Social inspection sources

Use, as applicable:

- all relevant `series-plan.md` files;
- materialized `social/**/post-*.md` files;
- per-post `.checklist.md` files;
- `social/id-registry.json`;
- provider-backed final visual metadata;
- per-platform scheduling/publication state;
- verified remote publication evidence when available.

## Social display states

For concepts/posts, preserve the canonical series/post lifecycle where possible:

```text
proposed
accepted
drafting
review
approved
scheduled
published
deferred
rejected
blocked
unknown
```

## Deterministic social join and state derivation

Build the unified inventory from the `series-plan.md` concept set first, then join materialized posts by exact durable provenance.

For every concept:

1. read `series_concept`, source article, plan state and optional `post_id`/post path;
2. if materialized, resolve the exact post by `post_id`/path and verify its `series_concept` + source article back-reference;
3. verify the `post_id` against the ID registry when present;
4. read post checklist and per-platform state;
5. read verified remote publication evidence when present;
6. report mismatches in `evidence_notes`.

Also discover materialized posts that are not reachable from a series plan. Include them with `unknown`/mismatch evidence rather than silently dropping them.

For a materialized post, derive state using this precedence:

1. `published` only with verified required publication evidence according to the social publication contract;
2. `blocked` when authoritative workflow explicitly records a blocker;
3. `scheduled` when durable platform scheduling state is valid and publication is not verified;
4. `approved` when required text/visual review is durably complete but not scheduled;
5. `review` when human text/visual review remains active;
6. `drafting` when materialized production is underway before review;
7. `accepted` when concept acceptance is durable but materialized production has not advanced;
8. otherwise use conservative `unknown` with mismatch/missing-evidence notes.

For an unmaterialized concept, preserve its canonical plan state (`proposed`, `accepted`, `deferred`, `rejected`) unless contradictory evidence requires `unknown`.

A stale `series-plan.md` projection must not downgrade or upgrade a stronger exact post/platform/checklist state; report the mismatch for later repair.

## Social list output

`/social list` is a unified inventory, not merely a list of files already carrying `post_id`.

It must include:

- unmaterialized concepts from every relevant `series-plan.md`;
- materialized posts;
- immutable `post_id` when allocated;
- `series_concept` key;
- source article;
- current synthetic/canonical state;
- target platforms when known;
- planned/publication information when relevant;
- evidence/mismatch notes when needed.

This ensures that proposed/accepted/deferred concepts remain visible before post materialization.

Sort deterministically by series/source order when explicitly persisted; otherwise by source article + series-plan order, placing orphan/mismatched materialized posts after their closest exact source group without inventing a relationship.

## Social details output

For a materialized post, return at least:

- `post_id`;
- `series_concept`;
- source article/path;
- current state and per-platform state;
- planned/published times and URLs when available;
- visual final identity/alt text when present;
- full master post text;
- relevant concept/source context;
- evidence notes for any mismatch.

For an unmaterialized series concept, return:

- `series_concept`;
- source article;
- concept title/angle/notes;
- current series-plan state;
- whether an immutable `post_id` has been allocated;
- why it has not yet materialized when that information is durable.

Never fabricate post copy for an unmaterialized concept in response to `details`.

## Inconsistency handling

Inspection is conservative and read-only.

Examples:

- front matter says `published` but only test-site URL exists -> not production `published`; show inconsistency;
- series plan says `scheduled` but post has verified publication evidence -> show `published` plus stale-plan warning;
- ID registry maps one `post_id` to a different post -> `STATE_INCONSISTENT`/`unknown`, no repair;
- checklist claims review complete but required final asset metadata is absent -> do not upgrade to `approved` if the capability contract requires that asset.

A separate mutating workflow may repair stale durable state after the user asks to continue/fix it. The inspection command itself never repairs.

## Help/documentation integration

The command catalogue and `/help` must describe these inspection commands as read-only and make clear that their display states are derived views rather than workflow authorities.

Implementation/parser/response rules are defined in `docs/architecture/user-command-runtime-contract.md`.
