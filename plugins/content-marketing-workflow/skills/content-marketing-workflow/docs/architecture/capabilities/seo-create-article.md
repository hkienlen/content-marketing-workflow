# Internal capability - seo-create-article

Date: 2026-09-05
Status: architecture contract

## Purpose

`seo-create-article` executes a fully planned article from durable repository state through a review-ready article plus applicable visual review package, using one production branch and one Pull Request.

Global prerequisite/degradation behavior is owned by:

```text
docs/architecture/runtime-compatibility-matrix.md
```

GitHub is a hard prerequisite. Media-dependent completion additionally requires operational `cloud_media_storage`. Runtime image generation/editing may use the central manual handoff when unavailable.

## Contract

```yaml
name: seo-create-article
purpose: Execute a planned SEO article from durable task state through a review-ready article and policy-compliant visual review package.
availability: core
feature_gate: null
mode: mutating

prerequisites:
  - github_repository is operational; otherwise CMW is BLOCKED
  - project onboarding completed sufficiently for article creation
  - Human Item / Work Item / task prompt and planning exist
  - mandatory strategy/template files readable
  - cloud_media_storage is operational before any source/proposal/final is claimed durable
  - when image generation/editing is unavailable, manual image handoff is used instead of false generation success

mandatory_context:
  - AGENTS.md
  - docs/architecture/runtime-compatibility-matrix.md
  - docs/architecture/persistence-contract.md
  - docs/architecture/github-transparency.md
  - docs/architecture/user-profile-data-contract.md
  - docs/architecture/user-provided-images.md
  - docs/architecture/article-execution-checklist.md
  - docs/architecture/capabilities/visual-source-resolve.md
  - Work Item state
  - dedicated task prompt and referenced directives
  - active user profile visual_preferences

reads:
  - task prompt/authoritative references
  - per-article checklist
  - effective visual policy/local override
  - verified user source media when applicable
  - article/branch/PR state
  - configured cloud-media workspace state
  - current runtime image generation/editing availability

writes:
  - target article file on intended work branch
  - per-article execution checklist
  - Work Item/task-specific durable state
  - content-local visual/source provenance state
  - provider-backed source/proposal/final media through delegated capabilities
  - PR state

external_side_effects:
  - web/SERP/source research when required
  - create/reuse work branch and PR automatically
  - create/reuse configured cloud-media source/proposals/final workspace
  - generate/edit visual proposals when runtime allows
  - otherwise produce complete external-generation prompt and resume after user returns/uploads image

validation:
  - no duplicate branch/PR
  - effective visual policy resolved before drafting
  - GitHub hard prerequisite remains operational
  - no source/proposal/final is called durable without cloud_media_storage
  - if policy requires user images before drafting, actual sources are verified/inspected first
  - no source image claimed without real file/bytes verification
  - no user original overwritten
  - strict/high fidelity prevents invented subject appearance
  - article follows task prompt and authoritative directives
  - factual/source claims trace to real sources
  - generated/materially transformed review sets retain exactly three reviewable A/B/C candidates when generation/treatment applies
  - use_as_is does not fabricate A/B/C
  - provider-backed binaries remain outside GitHub binary storage in normal mode
  - no fallback to WordPress/local filesystem as media storage
  - Work Item/checklist reflect real observable state

completion_conditions:
  - intended branch exists exactly once
  - visual policy resolved
  - truthful pre-draft visual-source state reached
  - article/research/briefs persisted when drafting is allowed
  - applicable visual review package persisted/recoverable in cloud provider
  - if runtime generation unavailable, manual handoff completed before visual package is called ready
  - PR exists/reused
  - exact review version identifiable and presented
  - no externally visible publication performed
```

## Pre-draft visual-source gate

Canonical decision:

```text
creation request
-> resolve visual policy
-> inspect local override
-> resolve/verify relevant user sources
-> apply missing_user_images_behavior
```

Truthful states include:

```text
source_ready
ai_generation_allowed
continue_without_visuals
awaiting_user_images
manual_image_handoff_required
```

`continue_without_visuals` may allow editorial drafting/review only. It does not waive required-media publication gates downstream.

## Provider-neutral media workspace

Conceptually:

```text
<provider-root>/<site-domain>/articles/<article-slug>/
├── source-user/
├── proposals/
└── final/
```

The current implemented provider is Google Drive. If asking the user to place source images, show the exact provider path plus a verified direct link when the adapter supplies one.

GitHub, WordPress and local filesystem are not fallback media stores.

## Runtime image-generation fallback

When generation/editing required by effective policy is unavailable but cloud storage works:

1. freeze exact article revision + image brief + source policy;
2. produce a complete copy/paste prompt including objective, dimensions/format, style, composition, branding, required/forbidden elements, source role/fidelity/treatment and text constraints;
3. instruct user to generate/improve image in an image-capable ChatGPT conversation or compatible image AI;
4. ask user to return/upload result;
5. inspect it;
6. persist it in provider-backed proposals/source state as appropriate;
7. resume exact review/finalization workflow.

Do not silently substitute Canva or fake proposal state. The prompt itself is not a completed visual.

If cloud storage is also unavailable, generated/returned media cannot become durable `verified_final`; media-dependent completion/publication remains blocked.

## Article persistence and review

After pre-draft gate permits drafting:

```text
research + full article drafting
-> persist article + complete visual briefs/roles in GitHub
-> continue to normal generation or manual handoff
-> persist/verify media in cloud provider
-> present article + applicable visual review package
```

For generated/materially transformed work retain exactly three useful A/B/C candidates. For exact use_as_is show exact verified candidate instead.

## Branch/PR policy

Create/reuse exactly one work branch and PR. Normal Git mechanics are internal after onboarding and do not become extra user approval gates.

## Independent validation gates

Keep editorial, media and external publication validation separate. Article/media validation never implies WordPress/social publication authorization.

## Resume/failure

On interruption inspect checklist + durable article/media/PR state first, reuse valid progress and continue from first incomplete observable task. Never claim failed/unavailable provider or generation actions succeeded.
