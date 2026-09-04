# Internal capability - seo-create-article

Date: 2026-09-04
Status: architecture contract

## Purpose

`seo-create-article` is a core internal capability of the single installable Content / Marketing skill.

It executes a fully planned article from durable repository state through a review-ready article + applicable visual review package, using one production branch and one Pull Request.

It is not a separately installable skill.

Read together with `docs/architecture/github-transparency.md`: after onboarding, normal GitHub mechanics are internal and do not create separate user approval gates.

User-provided image sourcing is resolved **before drafting** when the effective visual policy requires or prioritizes it. The historical unconditional `draft first -> generate 3 x A/B/C` order is no longer universal.

## Contract

```yaml
name: seo-create-article
purpose: Execute a planned SEO article from durable task state through a review-ready article and policy-compliant visual review package.
availability: core
feature_gate: null
mode: mutating

prerequisites:
  - project onboarding completed sufficiently for article creation
  - Human Item exists
  - Work Item exists and points to a dedicated task prompt
  - dedicated task prompt exists and planning is complete
  - GitHub repository readable/writable
  - Google Drive workspace verified when media work is required
  - mandatory strategy/template files readable

mandatory_context:
  - AGENTS.md
  - docs/architecture/persistence-contract.md
  - docs/architecture/github-transparency.md
  - docs/architecture/user-profile-data-contract.md
  - docs/architecture/user-provided-images.md
  - docs/architecture/capability-contract-template.md
  - docs/architecture/prompt-as-contract.md
  - docs/architecture/article-execution-checklist.md
  - docs/architecture/capabilities/visual-source-resolve.md
  - Work Item state
  - dedicated task prompt
  - every authoritative directive referenced by that prompt
  - active user profile visual_preferences

optional_context:
  - Human Item parent
  - relevant existing/published articles
  - neighbouring active article branches/PRs
  - existing article file when resuming
  - PR discussion when resuming
  - current SERP/search results
  - authoritative external sources
  - verified user-provided source images/provenance
  - chat-uploaded images in the current creation request
  - current project media-library references when implemented/available
  - recent visual assets and briefs

reads:
  - current task prompt and authoritative references
  - per-article execution checklist when present
  - effective visual policy and local override state
  - verified/inspectable user source media when applicable
  - relevant articles/assets
  - branch/PR/issue state
  - configured Drive workspace state

writes:
  - target article file on intended work branch
  - per-article Markdown execution checklist
  - task-specific prompt/context when durable task constraints evolve
  - Work Item tracking/state
  - content-local visual override/source provenance state when applicable
  - private Drive source-user/proposal/final state through delegated media capabilities
  - PR description/state when needed

persists:
  - resolved visual-source checkpoint for exact review/resume when required
  - verified user source provenance/roles used as editorial context
  - review-ready article draft
  - per-article observable execution state
  - research/source evidence actually used
  - article-specific image briefs/prompts/roles
  - Drive review/source references required for resume
  - branch/PR/commit state
  - task-specific durable changes discovered during execution

external_side_effects:
  - current web/SERP/source research when required
  - create/reuse work branch automatically
  - create/reuse Pull Request automatically
  - create/reuse private Drive source-user/proposals/final article workspace
  - generate/treat image proposals when effective policy requires and generation is available
  - after later human content/media validation, ordinary GitHub synchronization/merge occurs automatically under seo-update-article/github-transparency

human_approval:
  - source role/fidelity/treatment clarification only when materially ambiguous
  - if required user images are absent under ask_before_drafting, wait for actual source placement/upload or explicit content-local override before drafting
  - final editorial validation
  - final image/source selection/validation
  - all downstream externally visible publication gates

validation:
  - no duplicate branch/PR created
  - effective visual policy resolved before drafting
  - if policy requires user images before drafting, actual sources are verified/inspected before source-visible facts influence prose
  - no source image is claimed without real file/bytes verification
  - no user original is overwritten
  - strict/high fidelity prevents invented subject appearance
  - target article persisted on intended branch when drafting is allowed
  - per-article checklist reflects observable state rather than inferred progress
  - article follows task prompt and authoritative directives
  - factual/source claims trace to real sources
  - no invented personal experience/case/testimonial/statistic/citation
  - article Markdown contains two blank lines immediately before final public ## Références heading when present
  - visual review package follows effective source role/treatment rules
  - generated/materially transformed review sets retain exactly three reviewable A/B/C candidates per required visual
  - exact use_as_is + no-material-treatment sources are not forced into fake synthetic A/B/C variants
  - proposal/source review files are outside GitHub binary storage in normal provider-backed mode
  - review files are persisted/recoverable in Drive before presentation
  - presentation checklist tasks remain unchecked until artifacts are actually shown
  - Work Item reflects real production state

completion_conditions:
  - intended branch exists exactly once and is reused/created correctly
  - effective visual policy is resolved
  - one truthful pre-draft visual-source state is reached
  - if awaiting_user_images, exact Drive source-user path + verified direct link or valid chat-upload instruction has been presented and drafting has not falsely begun
  - otherwise article and complete image briefs/roles are persisted before generated/materially treated visual production
  - required research/source verification completed
  - when visual generation/treatment is applicable and available, it starts automatically after article/brief persistence without another generic go
  - required visual review package is completed according to source role: exact source/final candidate for use_as_is, or exactly three reviewable A/B/C candidates for generated/materially transformed work
  - generated proposals are retained/recoverable in Drive
  - PR exists or is correctly reused
  - exact review source version is identifiable
  - full public-facing article is actually presented to user when drafting reached review
  - each visual group is actually presented with Emplacement / Objectif / Description / appropriate candidates
  - review explicitly asks for article feedback/validation and media selections/feedback
  - checklist presentation tasks become complete only after actual presentation
  - no externally visible publication performed

next_actions:
  - visual-source-resolve resume when awaiting_user_images
  - seo-update-article after review feedback
  - asset-ingest after explicit final image/source selection
  - automatic GitHub integration once complete article/media validation is satisfied
  - downstream WordPress/social only after their own gates
```

## Entry conditions and routing

Use only after planning is durable/complete. If planning is incomplete, route to `seo-plan-article`. If article is already in human review and corrections are requested, route to `seo-update-article` rather than restart.

## Load durable state first

Before drafting/mutating content:

1. read repository-level contracts;
2. load `github-transparency.md`;
3. load `article-execution-checklist.md`;
4. load/create per-article checklist;
5. load Work Item;
6. load dedicated prompt;
7. read every authoritative directive referenced by prompt;
8. inspect relevant Human Item/content boundaries;
9. inspect real branch/PR state;
10. inspect configured Drive workspace state;
11. resolve effective visual policy from profile + article override + content-local override;
12. execute `visual-source-resolve` before drafting when user-source intake is required/prioritized.

Conversation context may supplement but never replaces durable state.

On resume, continue from first unchecked checklist task whose prerequisites are satisfied. Do not infer completion merely because an artifact exists somewhere.

## Pre-draft visual-source gate

Canonical decision:

```text
creation request
-> resolve visual policy
-> inspect any explicit local override
-> if relevant user sources are known: resolve + verify + inspect them
-> apply missing_user_images_behavior
```

Truthful states:

```text
source_ready
ai_generation_allowed
continue_without_visuals
awaiting_user_images
```

### `awaiting_user_images`

This is a real pre-draft stop when effective policy requires it.

For Google Drive, ensure/reuse:

```text
<drive-root>/<site-domain>/articles/<article-slug>/source-user/
```

Then show the user:

```text
exact canonical path
+ verified direct clickable Drive folder link
```

Do not draft first merely to preserve the old workflow order.

A direct chat upload is also valid when a real usable image attachment is present. Verify/inspect it, retain provenance and copy/retain the original in provider-backed source-user state when durable continuation requires it.

### One-off override

An explicit instruction such as:

```text
For this article, write first; I will provide the photos later.
```

may authorize a content-local sequence change. Persist it only with this task; never rewrite project `visual_preferences` unless the user explicitly asks to change the durable preference.

## Per-article execution checklist

Every article maintains:

```text
articles/<target>/<slug>.checklist.md
```

The checklist distinguishes policy resolved, source requested/verified/inspected, drafting, generated/treated proposals, presentation, selection and finalization.

Examples:

```text
[x] effective visual policy resolved
[x] required source photos verified and inspected
[x] article drafted and persisted
[ ] article displayed in ChatGPT for human review

[x] generated proposal set stored and verified in Drive
[ ] proposal group displayed in ChatGPT
```

For `use_as_is`, the checklist records exact source/final review rather than fictitious `A/B/C generated` steps.

## Branch and Pull Request policy

Before creating anything, verify intended branch/PR. Create/reuse exactly one and never create replacement Git objects merely because a new session starts. Do not ask the user to authorize branch creation, commits, PR updates or merge as separate actions.

## Research and drafting

Research matches task/freshness requirements. Verify search intent/SERP when required, identify recurring formulations and useful gaps, and verify material factual claims with suitable sources. Distinguish sourced evidence from practitioner observations and framework-specific concepts.

Never invent search volume, ranking positions, studies, quotes, URLs, personal experience or client evidence.

### Using user images as editorial evidence

When a verified/inspected user source is available before drafting:

- use only attributes actually visible/verified;
- do not infer materials, dimensions, performance, provenance, identity or product properties not established by image/user data;
- let relevant visual facts influence angle/description/placement when useful;
- preserve source fidelity constraints in the resulting visual brief.

## Persist article before visual production

After the pre-draft source gate permits drafting:

```text
research + full article drafting
-> article + complete image briefs/roles persisted and committed in GitHub
-> checklist records drafting complete but review presentation incomplete
-> Drive article folder/source state reused
-> immediately continue to applicable visual production when available
```

There is no extra human gate between article/brief persistence and visual production when effective policy already permits that production.

### Generated/materially transformed visuals

1. read exact image brief + source provenance/fidelity when applicable;
2. prepare distinct compliant concepts/treatments;
3. generate all required families without pausing for generic confirmation;
4. inspect outputs;
5. reject/regenerate off-brief, duplicate, misleading or low-quality outputs;
6. retain exactly three reviewable A/B/C candidates per generated/materially transformed visual;
7. persist/verify in Drive;
8. then present.

### Exact `use_as_is` source

When role is `use_as_is` and treatment is `none`/non-material normalization only:

- do not generate synthetic alternatives merely to satisfy an historical count;
- preserve original;
- prepare/verify the exact review/final candidate according to output policy;
- present that exact visual for human media validation.

If generation capability is unavailable where required, report the real blocker. Do not silently substitute Canva or fake proposal state.

## Review projection/version binding

Normal first review shows:

- complete public-facing article;
- useful SEO metadata;
- for each required visual: context, placement, objective, description/concept/source role and relevant fidelity/treatment constraints;
- A/B/C where alternatives were actually generated/treated;
- exact source/final candidate where `use_as_is` applies;
- remaining independent business/content/publication gates;
- clear request for article feedback/validation and media selection/feedback.

Bind review internally to at least:

```text
article_path
article_commit_sha
review_round
source provenance identities shown when applicable
Drive proposal/final references shown
```

Normal state after presentation is `awaiting_human_validation`.

## Independent validation gates

Keep editorial, source/media and external publication validation separate:

- article may be accepted while one image needs work;
- image/source may be selected while article corrections remain;
- image/source selection is not article validation;
- source intake is not final image selection;
- article/media validation is not WordPress publication approval;
- GitHub merge is not a separate user gate.

Once required article/media gates and final snapshot are satisfied, GitHub integration is automatic under `github-transparency`/`seo-update-article`.

Silence never means content validation.

## Task-specific durable discoveries

Persist article-specific constraints in dedicated task prompt/context: revised title/meta, source rigor, visual duplication boundary, local visual override, source role/fidelity or claim to avoid. Global reusable visual preference changes belong to active profile/appropriate global authority instead.

## Completion/failure/resume

A run is not complete merely because prose/images were generated/uploaded.

On interruption/retry:

- inspect checklist first;
- inspect persisted article/source/media/PR state;
- reuse valid progress;
- continue from first incomplete observable task;
- do not regenerate accepted/persisted work unnecessarily;
- do not claim unavailable/failed source/generation operation succeeded;
- do not infer `presented` from `generated`/`stored`;
- do not shift GitHub operations to user;
- do not draft when truthful state remains `awaiting_user_images`.

Do not merge before required content/media validation is complete. Once complete, merge automatically and verify rather than asking for `go merge`.
