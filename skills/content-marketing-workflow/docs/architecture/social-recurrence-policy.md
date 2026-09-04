# Social thematic recurrence and deduplication policy

Date: 2026-09-02
Status: architecture decision / superseding contract

## Purpose

This contract defines how social planning must distinguish a harmful duplicate from a useful recurrence of a theme across different article-derived series, free posts, or publication periods.

It refines and supersedes any older wording that could be interpreted as reserving a broad theme permanently to one source article or forbidding future posts merely because they address a similar subject.

The authoritative principle is:

```text
Deduplicate executions, not themes.
```

A social content system may intentionally revisit the same broad topic over time when the angle, context, function, example, audience situation, or editorial purpose is meaningfully different.

## Why recurrence is allowed

Social-network audiences do not see every publication. A core idea may therefore need to be repeated over time to establish positioning, reinforce recognition, and reach people who missed an earlier post.

A recurring theme such as perfectionism, fear of selling, legitimacy, procrastination, difficulty showing oneself, avoidance, or training-as-delay is not owned forever by the first article that mentions it.

The existence of a related post in another series is therefore a comparison signal, not an automatic rejection rule.

## Three classes

### 1. Harmful duplicate

Treat as a duplicate when the proposed post substantially repeats the same combination of:

- core claim or conclusion;
- angle / framing;
- concrete example or reasoning path;
- strategic function;
- CTA / offer argument when commercial;
- and publication timing is close enough that the repetition would feel accidental or lazy.

Typical action:

- merge;
- reframe materially;
- defer;
- or reject.

Changing only vocabulary, hook wording, or visual style is not sufficient differentiation.

### 2. Related but distinct treatment

Allow when the broad subject overlaps but the post serves a materially different purpose.

Examples:

- perfectionism as an identification post in one series vs perfectionism as a mechanism explored during accompaniment in another;
- fear of selling as a business observation vs selling-without-pressure as positioning/method;
- procrastination as a symptom vs a case/example vs a practical self-observation tool;
- the same offer mentioned from two different problems or audience situations.

Persist the relationship as related/overlapping when useful, but do not reject it merely because the theme is shared.

### 3. Intentional recurrence

A core idea may be deliberately revisited after a suitable interval, especially when it is central to the professional positioning.

The later post should normally vary at least one meaningful dimension:

- hook;
- example;
- audience situation;
- depth;
- format;
- strategic function;
- CTA;
- article/source context;
- or lesson drawn.

Intentional recurrence is legitimate and can be beneficial. It should be recognized as such rather than mislabeled as a duplicate.

## Timing principle

Do not define a rigid universal waiting period.

Instead assess recency together with similarity and calendar density:

- near-identical posts close together -> usually avoid;
- related posts with clearly different angles -> may coexist in the same broader campaign;
- deliberate resurfacing of a core message after weeks/months -> acceptable when editorially useful;
- recurring evergreen positioning themes may appear multiple times over the year.

Scheduling must still avoid heavy clustering of strong conversion/CTA posts according to the global calendar-balance rules.

## Cross-series review requirement

When a new article-derived series is generated or materially revised, inspect relevant existing series/posts across the repository before human validation.

The purpose of this review is to classify overlaps, not to eliminate all repetition.

For each meaningful overlap, choose one of:

```text
harmful_duplicate
related_distinct
intentional_recurrence
no_material_overlap
```

Only `harmful_duplicate` normally blocks or forces rework.

`related_distinct` and `intentional_recurrence` are valid outcomes and may remain in the proposed series.

## Human validation presentation

At series-validation time, surface only overlaps that materially help the decision.

Do not burden the user with every semantic similarity.

Useful notes include:

- "related to post 2026-00XX, but different function/angle";
- "same core theme revisited intentionally after a longer interval";
- "too close to an existing post; recommend merge/reframe/defer".

The user must be able to approve an intentional recurrence explicitly when useful.

## Commercial recurrence

The same service or offer can legitimately appear in multiple series because different source articles lead to different entry problems.

Do not treat every repeated mention of the offer or discovery call as a duplicate.

Differentiate by the problem-to-offer bridge, objection, use case, or reason the next step is relevant.

However, avoid repeated posts that present essentially the same offer, same argument, same CTA, and same framing within a short period.

Calendar alternation rules for `conversion` remain mandatory.

## Persistence

When useful, a series concept may store recurrence metadata such as:

```yaml
overlap_class: related_distinct|intentional_recurrence|harmful_duplicate|no_material_overlap
related_posts:
  - 2026-0007
recurrence_note: "Same core theme, different angle and strategic function."
```

These fields are optional unless an overlap materially affects review or scheduling.

Do not create a second global registry solely for recurrence while the repository inventory can provide sufficient evidence.

## Integration

This contract must be applied by:

- `social-extract-posts` during cross-series inventory and deduplication;
- `/social plan` during series generation/replanning;
- `/social create` during rollover planning;
- human whole-series validation;
- `social-schedule` when recurrence and timing together could create a repetitive sequence.

It must be read together with:

```text
strategy/social-media-strategy.md
docs/architecture/social-workflow.md
docs/architecture/social-series-review-gate.md
docs/architecture/capabilities/social-extract-posts.md
docs/architecture/capabilities/social-schedule.md
```

If those documents contain older language suggesting that a broad theme must be reserved permanently to one source article, this contract supersedes that interpretation.

## Productization acceptance cases

Future implementation must demonstrate that:

1. a near-identical post with same angle/function/CTA can be detected as `harmful_duplicate`;
2. the same broad theme with a different function/angle is allowed as `related_distinct`;
3. an evergreen core theme can be deliberately reused later as `intentional_recurrence`;
4. repeated mention of the same offer is not automatically rejected when the problem-to-offer bridge differs;
5. close repeated conversion posts remain controlled by calendar-balance rules;
6. the series review surfaces meaningful overlap notes without overwhelming the user with superficial similarities.
