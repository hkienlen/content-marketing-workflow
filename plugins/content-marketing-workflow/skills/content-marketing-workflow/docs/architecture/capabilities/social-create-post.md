# Internal capability: social-create-post

Date: 2026-09-05
Status: current architecture contract

## Purpose

`social-create-post` is the normal production entrypoint for creating/resuming the next social post.

It backs:

```text
/social create
/social create free <topic>
```

The default operation is queue-driven. For article-derived content it preserves mandatory whole-series validation and strategic-function model. It also resolves the effective visual-source policy **before drafting the master text** when user-provided media is required or preferred.

The historical universal order `write -> generate exactly A/B/C` applies only to AI-generated/materially transformed visual workflows, not to exact `use_as_is` user sources.

## Capability contract

```yaml
name: social-create-post
purpose: Create/resume the next eligible social post from validated durable order, including pre-draft visual-source resolution and the appropriate combined text/media review workflow.
availability: optional
feature_gate: social.enabled
mode: mutating

prerequisites:
  - social.enabled is true
  - repository social/article state is readable/writable
  - social strategy/directives are readable
  - immutable ID registry is readable/writable
  - active user profile and visual_preferences are readable
  - selected cloud_media_storage provider is operational before user-source/proposal media work

mandatory_context:
  - AGENTS.md
  - docs/architecture/runtime-compatibility-matrix.md
  - docs/architecture/persistence-contract.md
  - docs/architecture/github-transparency.md
  - docs/architecture/user-provided-images.md
  - docs/architecture/google-drive-workspace.md
  - docs/architecture/dropbox-workspace.md
  - docs/architecture/social-workflow.md
  - docs/architecture/social-creation-queue.md
  - docs/architecture/social-series-review-gate.md
  - docs/architecture/social-post-review-loop.md
  - docs/architecture/social-final-drive-package.md
  - docs/architecture/social-execution-checklist.md
  - docs/architecture/capabilities/visual-source-resolve.md
  - docs/architecture/capabilities/social-extract-posts.md
  - docs/architecture/capabilities/social-create-visual.md
  - strategy/social-media-strategy.md
  - strategy/social-writing-style.md
  - strategy/social-visual-guidelines.md
  - strategy/social-scheduling.md
  - social/README.md
  - social/id-registry.json
  - active user-data/profile.json

reads:
  - relevant social/**/series-plan.md
  - materialized posts/checklists
  - social/id-registry.json
  - eligible validated article inventory/order
  - exact source article for derived mode
  - current social strategy/directives
  - effective visual policy and content-local override
  - verified user-provided source images/provenance when applicable
  - selected cloud-media provider/workspace state

writes:
  - series-plan.md when a new source article is opened for social reuse
  - series validation evidence after human validation
  - selected post file and checklist
  - social/id-registry.json when ID allocated
  - source/provenance, series_function and lifecycle state
  - content-local visual override/source provenance state
  - visual brief/proposal/source references according to downstream visual contract
  - combined-review state and review-round evidence
  - provider-appropriate final text artifact identity when cloud finalization applies

external_side_effects:
  - GitHub durable-state mutation
  - create/reuse private selected-provider source-user/proposals/final workspace
  - read/inspect real user source media when supplied
  - image generation/treatment through social-create-visual when applicable
  - provider-appropriate final text artifact creation/update after combined approval
  - no scheduling/publication implicitly

human_approval:
  - no generic approval to select next concept from unchanged validated series
  - mandatory detailed validation of newly generated/materially revised article-derived series before first drafting
  - if effective visual policy blocks on missing user media, actual source placement/upload or explicit compatible local override is required before master text drafting
  - mandatory guided combined review of post text + appropriate visual package
  - final text approval and exact visual/source selection/validation
  - scheduling/publication remain separate gates

completion_conditions:
  - exactly one production target selected/resumed or normalized blocking state returned
  - new/materially revised article series human-validated before first post drafting
  - source/provenance + series_function persisted correctly
  - immutable post_id allocated once only after applicable series gate passes
  - effective visual policy resolved before master text drafting
  - required user source is verified/inspected before drafting when policy says so, or truthful fallback/local override state permits drafting
  - post/checklist persisted/re-read
  - master copy + visual brief + appropriate reviewable visual package reach one combined guided review
  - generated/materially transformed visual workflow has exactly three distinct A/B/C proposals
  - exact use_as_is workflow presents exact source/final candidate without fake synthetic alternatives
  - targeted revisions preserve unaffected approved components
  - provider-appropriate final cloud package invariant is satisfied
  - no scheduling/publication occurs implicitly
```

## Queue-driven `/social create`

### Existing validated series

Priority:

1. resume already-started incomplete post;
2. otherwise first eligible concept from exact validated editorial order;
3. if none remains, roll to next eligible article.

Do not reorder a validated series ad hoc.

Every article-derived materialized post inherits:

```yaml
source_type: article
article: articles/<scope>/<article>.md
article_url: <canonical URL when known>
series_concept: <stable concept key>
series_function: identification|expertise|positioning|conversion
```

### Queue rollover

For next eligible article:

1. inventory/deduplicate existing territory;
2. derive complete candidate concepts;
3. classify strategic function;
4. evaluate activity/offer visibility coverage;
5. propose mixed editorial order avoiding commercial clustering;
6. persist/re-read `series-plan.md`;
7. present detailed series validation view;
8. receive corrections/validation;
9. persist exact validated revision;
10. select first eligible concept, allocate/reuse immutable ID and immediately continue to pre-draft visual-source resolution without another generic `go`.

## Pre-draft visual-source resolution

After concept is accepted/selected and before master text is drafted:

```text
select/resume post
-> resolve project default -> social override -> local override
-> invoke visual-source-resolve
-> source_ready | ai_generation_allowed | continue_without_visuals | awaiting_user_images
```

### `awaiting_user_images`

Do not draft master text yet.

Create/reuse and verify in the selected cloud provider:

```text
<provider-root>/<site-domain>/social/<post-name>/source-user/
```

Then show the user:

```text
exact canonical provider folder path
+ verified direct clickable provider folder link when the active adapter exposes one
```

A real chat image upload may satisfy intake when it is verified/inspected and retained/provenance-recorded as required.

### Local override

Explicit instructions such as:

```text
For this post only, generate the visual entirely with AI.
Use this photo exactly, no retouching.
Keep the product exact; change only the background.
```

may override project/social visual policy for this post only. Persist with post state; do not mutate project `visual_preferences`.

## Draft + visual + combined review continuation

Once series/source gates permit drafting:

```text
draft complete publishable master text using only verified source facts
-> persist text/checklist/source provenance
-> create visual brief/role
-> invoke social-create-visual
```

### Generated/materially transformed visual

```text
-> create exactly 3 distinct compliant proposals A/B/C
-> persist/verify A/B/C in selected cloud provider
-> ONE combined review: full text + A/B/C + guidance
```

### Exact `use_as_is` user source

```text
-> preserve original source
-> prepare/verify exact source/final candidate (normalization only as allowed)
-> ONE combined review: full text + exact visual + guidance
```

Do not generate synthetic A/B/C merely to satisfy the historical count.

No extra generic `go` exists between master-text drafting and permitted visual production.

First normal review explicitly tells user they may:

- validate text and choose/validate visual candidate(s);
- request text-only changes;
- request visual-only changes/treatment;
- request both;
- request a new A/B/C round where alternatives are applicable;
- replace/provide a different user source when source workflow is active.

Detailed freeze/revision semantics: `social-post-review-loop.md`.

## Final cloud package invariant

After combined approval, create/reuse in the selected provider's private `final/` folder:

```text
final/
├── selected normalized visual
└── one provider-appropriate copy/paste-ready final text artifact
```

Provider-specific text artifact:

```text
google_drive -> native Google Doc with exact approved publishable text only
dropbox      -> UTF-8 plain-text .txt file with exact approved publishable text only
```

The source original remains under `source-user/` and is never replaced by finalization.

Persist `final_post_document` provider/identity/folder/body_policy/format/status and reuse/update the canonical artifact on revised approval rather than creating duplicates. Details: `social-final-drive-package.md` (historical filename, provider-neutral contract from 0.3.0).

## Targeted correction invariant

Once component is approved, preserve it unless explicitly reopened or another requested change materially invalidates it.

Examples:

```text
"Texte OK, refais les images"
-> freeze text; regenerate/re-treat only visual package

"Je garde cette photo, raccourcis le texte"
-> preserve source/final visual unless text change materially breaks visual relation

"B est trop chargé"
-> revise B only; preserve A/C

"Garde le produit exact mais remplace le fond"
-> preserve verified source/fidelity; reopen only allowed composition/treatment
```

Never overwrite original user source during corrections.

## `/social create free <topic>`

Free post is deliberately not derived from article/series.

Requirements:

- topic/intent required unless unambiguous;
- global deduplication;
- normal immutable post_id;
- standalone namespace;
- `source_type: free`, no fake article/series provenance;
- assign/persist `series_function` when determinable;
- same pre-draft visual-source resolution;
- same master-text/visual/combined review rules;
- same provider-neutral final package, scheduling and publication gates.

Whole-series gate does not apply.

If topic materially duplicates queued article-derived concept, surface overlap and default to durable queued concept unless independent treatment is explicit.

## Detailed help contract

`/help social create` must explain:

- queue/resume/rollover/series validation semantics;
- first post continues automatically after series validation;
- before master text, active visual preference is resolved and required/preferred user images may be requested/verified/inspected;
- if provider intake is needed, exact source-user path + direct link are given when available;
- content-local visual override does not rewrite project preference;
- generated/materially transformed visual uses A/B/C;
- exact use_as_is source does not require fake A/B/C;
- combined review/freeze behavior remains mandatory;
- final cloud package includes final visual + provider-appropriate copy/paste-ready final text artifact;
- source intake/selection never authorizes scheduling/publication.

`/help social create free` explains same visual sourcing rules plus standalone provenance/deduplication/no series gate.

## Resume/idempotency

Before creating anything inspect whether selected concept already has ID/post/checklist/visual policy/source folder/source provenance/review round.

Reuse valid state; never allocate second ID or duplicate source-user folder/provider copy merely because execution restarted.

Material editorial reset keeps immutable post_id and marks old text/media superseded. Source originals remain preserved. Final text artifact is canonical per post package and reused/updated.

A provider change requires explicit migration/rebinding; do not silently reuse provider identities from the previous provider.

## Separation from `/article create`

`/article create` remains exclusively SEO article production and never creates social posts.
