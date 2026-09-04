# Internal capability: social-extract-posts

Date: 2026-09-02
Status: current implementation contract

## Purpose

`social-extract-posts` inventories a validated SEO article, derives the complete realistic set of distinct social concepts supported by it, deduplicates them against existing social content, evaluates strategic coverage, proposes a balanced editorial order, persists the durable `series-plan.md`, and supports mandatory whole-series human review before first production from a newly generated/materially revised article series.

It is used by both explicit `/social plan` requests and automatic rollover from `/social create` when the current social queue is exhausted.

## Authoritative series gate

Read together:

```text
docs/architecture/social-creation-queue.md
docs/architecture/social-series-review-gate.md
docs/architecture/capabilities/social-create-post.md
strategy/social-media-strategy.md
```

For article-derived content:

- inventory and complete series persistence happen automatically;
- each concept receives a durable strategic function;
- the series is checked for balance between awareness/value and business visibility;
- the order is designed to avoid clustering explicit commercial posts;
- the complete persisted series must be presented to the user before the first new post from that newly generated/materially revised series is drafted;
- user feedback is applied and persisted;
- after validation, the first eligible concept may proceed automatically without another generic `go`.

An unchanged series already durably human-validated does not require revalidation before each later queued post.

## Capability contract

```yaml
name: social-extract-posts
purpose: Audit one validated SEO article, derive/deduplicate its viable social reserve, classify each concept by strategic function, balance/order the series, persist it, and obtain whole-series human validation before first production.
availability: optional
feature_gate: social.enabled
mode: mutating

prerequisites:
  - social.enabled is true
  - source SEO article is human-validated/approved enough for social reuse
  - exact source article path/version is known
  - current social strategy/directives are loaded
  - validated durable business/offer/positioning context is readable when it is needed to complete the series
  - current social inventory and immutable ID registry are readable

mandatory_context:
  - AGENTS.md
  - docs/architecture/persistence-contract.md
  - docs/architecture/github-transparency.md
  - docs/architecture/social-workflow.md
  - docs/architecture/social-creation-queue.md
  - docs/architecture/social-series-review-gate.md
  - docs/architecture/social-execution-checklist.md
  - strategy/social-media-strategy.md
  - strategy/social-writing-style.md
  - strategy/social-scheduling.md
  - social/README.md
  - social/id-registry.json
  - exact validated source article
  - relevant existing social posts/concepts
  - validated durable activity/method/offer context when applicable

reads:
  - exact validated source article
  - existing social concepts/posts across relevant source articles and free posts
  - existing series plan for the source article
  - immutable ID registry
  - social editorial/style/link/visual/scheduling rules
  - validated durable activity/method/offer/CTA information relevant to the article

writes:
  - social/<scope>/<source-or-series>/series-plan.md
  - durable source relationship and concept lifecycle state
  - strategic function and editorial order for each retained concept
  - series human-validation evidence bound to exact reviewed plan revision

persists:
  - exact source article path and URL when known
  - complete candidate concept inventory
  - stable concept keys
  - series_function for every retained concept
  - concise role/purpose in the series
  - stable editorial order/priority
  - concept state
  - coverage summary when useful
  - series review/validation state and exact reviewed revision identity
  - post_id/path once later materialized
  - deduplication/reservation notes when useful

external_side_effects:
  - GitHub repository mutation only

human_approval:
  - no approval required for inventory/deduplication/classification/initial persistence
  - mandatory human review/validation of the complete newly generated or materially revised article-derived series before first-post drafting
  - review must expose each concept's strategic function and the intended alternation/order
  - user may accept/reorder/reject/defer/merge/split/reframe concepts or their role
  - produced post still requires normal editorial/visual gates
  - scheduling/publication remain separate gates

validation:
  - inventory covers existing posts and relevant overlapping concepts
  - every concept is grounded in the source article and/or explicitly allowed durable business/offer context
  - no invented personal experience/client/result/benefit/offer/CTA
  - candidate list is deduplicated against existing social inventory
  - candidate list favors materially distinct angles rather than quota filling
  - every retained concept has one valid series_function: identification|expertise|positioning|conversion
  - series is checked against the strategic coverage test from strategy/social-media-strategy.md
  - absence of a function is intentional/explained when source truth does not support it
  - editorial order avoids consecutive conversion/strong-CTA posts when reasonably possible
  - stable order is persisted
  - series plan is persisted and re-read before human presentation
  - user corrections are persisted before validation is recorded
  - validation evidence binds to the exact reviewed plan revision
  - no post_id is allocated merely by planning

completion_conditions:
  - automatic inventory audit completed
  - complete deduplicated/classified/balanced series persisted
  - series plan re-read/verified
  - complete series presented with functions, roles, order and coverage summary when review is required
  - user feedback applied and exact current plan durably validated before production handoff
  - no scheduling/publication occurred
```

## Mandatory sequence for a new/materially revised article series

### Phase 1 - inventory audit (automatic)

1. read the exact validated article;
2. read its existing `series-plan.md` if present;
3. identify existing posts already derived from it and their functions/states when known;
4. inspect relevant concepts/posts from other articles/free posts for duplication;
5. identify source territories already consumed, available, reserved or duplicated;
6. load durable activity/method/offer information only when needed to create a truthful bridge from article content to the professional's service.

### Phase 2 - derive complete candidate reserve (automatic)

1. derive the strongest materially distinct concepts supported by the article;
2. exclude weak subdivisions/paraphrases;
3. preserve existing materialized concepts instead of proposing them again;
4. assign each new candidate a stable `series_concept` key;
5. assign each retained concept one `series_function`:
   - `identification`;
   - `expertise`;
   - `positioning`;
   - `conversion`;
6. add a concise `series_role` explaining what the post contributes to the reader journey;
7. evaluate the series as a whole: does repeated exposure make the professional/activity/offer understandable, not merely the subject area?;
8. when coverage is weak and durable source truth supports it, add/replace/reframe concepts so method/positioning and offer/conversion are represented without making every post promotional;
9. propose a durable order that alternates functions naturally and avoids consecutive conversion/strong CTA posts;
10. do not allocate `post_id` during planning.

Indicative balance is defined in `strategy/social-media-strategy.md`; it is not a quota.

### Phase 3 - persist and verify (automatic)

Persist to:

```text
social/<scope>/<source-or-series>/series-plan.md
```

Recommended concept shape:

```yaml
series_concept: strategie-ou-frein-interieur
series_function: positioning
series_role: "Montrer que l'approche commence par distinguer les causes concrètes d'un éventuel frein intérieur."
order: 8
state: proposed
```

Equivalent tabular Markdown fields are acceptable if they carry the same durable semantics.

Then re-read before presentation.

### Phase 4 - present whole series (human gate)

The presentation is not a bare brainstorming list.

Before the table/list, explain the four functions in user-facing language:

```text
Identification -> se reconnaître
Expertise / compréhension -> apprendre/comprendre
Méthode / positionnement -> comprendre qui vous êtes et comment vous travaillez
Offre / conversion -> comprendre ce que vous proposez et la prochaine étape
```

Explicitly explain that the order is intentionally mixed so commercial/CTA posts do not appear as a heavy consecutive block.

For every concept show at least:

- proposed order;
- concept/title;
- angle/territory;
- strategic function;
- concrete role in the series;
- state;
- source/offer/link note when useful.

Also show a coverage summary by function and flag any intentional gap.

Ask the user to validate or request changes to concepts, functions, roles or order.

### Phase 5 - apply feedback and persist validation

Apply additions/removals/merges/splits/reframes/defer/reject/function/order changes immediately to the same `series-plan.md`, re-read it, then persist durable evidence that the exact revised plan was human validated.

After validation, `social-create-post` may immediately select the first eligible concept, allocate its ID and start drafting without another generic `go`.

## Existing validated series

If the exact current series revision is already durably human-validated, subsequent `/social create` calls may consume the next eligible concept directly.

Do not re-present an unchanged validated list for every post.

A material series change includes adding/removing/merging/splitting/reframing concepts, materially changing a concept's function/role, or changing ordering in a way that changes the validated editorial progression. Such a change invalidates the applicable validation and requires renewed review before newly affected production.

## Series-plan state model

Use:

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
```

`proposed` = persisted but not production-authorized; `accepted` = eligible after applicable series gate; later states retain their existing meanings.

## Source relationship invariant

Each series plan records at least:

```yaml
source_article: articles/<scope>/<article>.md
source_article_url: <canonical/public URL when known>
```

Every new article-derived materialized post keeps:

```yaml
source_type: article
article: articles/<scope>/<article>.md
article_url: <canonical/public URL when known>
series_concept: <stable concept key>
series_function: identification|expertise|positioning|conversion
```

Folder placement is never sufficient provenance.

## Concept extraction and business bridge

Do not mechanically turn H2/H3 headings into posts.

Useful concepts include identification, misconception correction, observation, question, supported case, mini-tool, distinction, metaphor, practical advice, explanation of method/limits, service relevance, objection handling and legitimate next step.

The article remains thematic master content. A post may additionally use validated durable project information about activity, method or offer when needed to make the professional connection explicit. That must never become permission to invent claims or distort the article.

## Deduplication

Compare concepts with existing content across articles and free posts. Changing wording alone is not distinction.

Deduplicate commercial territory too: repeated near-identical service pitches, CTAs or benefits from different articles should normally be merged, spaced or differentiated materially.

## ID allocation boundary

No ID during planning. ID allocation occurs only after the applicable whole-series human gate has passed and production begins.

## Explicit `/social plan`

`/social plan [article]` may inventory/rebuild/classify/reorder/persist a series, present the detailed validation view and persist human validation. It does not have to draft a post.

## Integration with `/social create`

When invoked by queue rollover, return either:

- `awaiting_human_series_validation` after persistence/presentation of a new/materially revised plan; or
- a verified already-validated queue-ready series.

Once the user validates the detailed presented series, persist that validation and continue directly to the first eligible post without a second generic `go`.
