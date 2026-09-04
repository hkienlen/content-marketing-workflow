# Social creation queue and rollover policy

Date: 2026-09-02
Status: architecture decision

## Decision

The normal social-post creation entrypoint is queue-driven:

```text
/social create
```

It creates/resumes the next not-yet-written social post from durable repository state. The user is not required to name a concept already present in the durable queue.

A separate command creates intentionally standalone content:

```text
/social create free <topic>
```

`/article create` remains reserved for SEO articles.

## Canonical queue behavior

```text
read all durable series/post state
-> resume earliest incomplete eligible post if one exists
-> otherwise select first eligible not-yet-written concept from an already human-validated series according to its validated editorial order
-> draft + persist + visual workflow
-> when current series has no eligible not-yet-written concept:
   select next eligible validated article deterministically
   -> inventory/deduplicate article social opportunities automatically
   -> classify concepts by strategic function
   -> construct balanced editorial order
   -> persist complete series-plan.md automatically
   -> present complete list + functions + roles + coverage/order rationale to human
   -> apply corrections + persist exact validated series
   -> select first eligible concept
   -> allocate immutable post_id
   -> draft immediately without another generic go
```

The persisted `series-plan.md` is the queue authority. Conversation memory is never queue authority.

## Mandatory whole-series review

For a newly generated or materially revised article-derived series, complete human review is mandatory before the first new post from that series is drafted.

The review must include the strategic function of each concept and the proposed editorial order. See `social-series-review-gate.md`.

After list validation, no second generic `go` is required.

An unchanged series already durably human-validated does not require whole-list revalidation before each subsequent post.

## Stable next-concept selection

Within one already validated series:

1. resume an already-started incomplete post rather than duplicating it;
2. otherwise prefer the first `accepted` eligible concept with no materialized post;
3. otherwise select the first eligible concept in the exact human-validated persisted editorial order and move it to `accepted` immediately before production if needed;
4. never automatically select `deferred` or `rejected` concepts.

The validated editorial order is authoritative. It is intentionally allowed to differ from raw topic-generation order because it incorporates strategic-function alternation.

A `proposed` concept from an unvalidated/newly changed series is not production-eligible merely because it appears first.

## Strategic function invariant

Every new article-derived concept should persist one primary function:

```text
identification
expertise
positioning
conversion
```

Queue selection itself does not reshuffle a validated series on the fly. If later calendar context reveals that the next validated `conversion` post would create an undesirable commercial cluster with content from another series, the scheduling layer should propose spacing/reordering rather than silently violating the validated series order.

If a durable reorder is made, update the series plan and reapply the applicable human-validation rule when the editorial progression changes materially.

## Stable next-article selection

When no current validated series has an eligible not-yet-written concept, choose the next eligible article using:

1. explicit durable article/social priority, if present;
2. numeric Work Item/Human Item sequence, if present;
3. lexical repository article path only as deterministic fallback.

Eligible means durable article body exists, article is human-validated/approved sufficiently for reuse, exact source path is known, article is not blocked, social reuse is not disabled, and no still-actionable series for that article already exists.

Never choose from conversation order, chat recency or model preference.

## Free post policy

`/social create free <topic>` deliberately bypasses article-series selection, not production quality/safety.

A free post:

- is deduplicated against existing social inventory;
- receives a normal immutable `post_id`;
- has a normal checklist;
- uses normal writing/visual/Drive/review gates;
- has explicit `source_type: free` provenance;
- should persist a `series_function` when its editorial role can be determined, so scheduling can balance it globally;
- does not silently consume/modify an article-derived queue concept.

Because there is no article-derived series, the whole-series validation gate does not apply.

## Human gates retained

Human gates remain distinct:

- whole-series validation before first drafting from a new/materially revised article-derived series;
- editorial review/validation of produced post;
- visual selection/validation;
- scheduling authorization requirements;
- publication authorization requirements;
- external-write safety gates.

## Authoritative integration

Read together with:

```text
docs/architecture/social-series-review-gate.md
docs/architecture/capabilities/social-create-post.md
docs/architecture/capabilities/social-extract-posts.md
docs/architecture/social-workflow.md
strategy/social-media-strategy.md
strategy/social-scheduling.md
docs/architecture/user-command-interface.md
docs/architecture/user-command-catalog.yaml
```
