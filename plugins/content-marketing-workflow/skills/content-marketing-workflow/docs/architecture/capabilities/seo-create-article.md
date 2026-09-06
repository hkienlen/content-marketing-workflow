# Internal capability - seo-create-article

Date: 2026-09-06
Status: architecture contract

## Purpose

`seo-create-article` executes a fully planned article from durable repository state through a review-ready article plus applicable visual review package, using one production branch and one Pull Request.

Global prerequisite/degradation behavior is owned by:

```text
docs/architecture/runtime-compatibility-matrix.md
```

Generic creative defaults/user-directive precedence and brand/logo behavior are owned by:

```text
docs/architecture/visual-generation-contract.md
docs/architecture/brand-assets-contract.md
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
  - selected cloud_media_storage provider is operational before any source/proposal/final is claimed durable
  - when image generation/editing is unavailable, manual image handoff is used instead of false generation success

mandatory_context:
  - AGENTS.md
  - docs/architecture/runtime-compatibility-matrix.md
  - docs/architecture/persistence-contract.md
  - docs/architecture/github-transparency.md
  - docs/architecture/user-profile-data-contract.md
  - docs/architecture/user-provided-images.md
  - docs/architecture/visual-generation-contract.md
  - docs/architecture/brand-assets-contract.md
  - docs/architecture/google-drive-workspace.md
  - docs/architecture/dropbox-workspace.md
  - docs/architecture/article-execution-checklist.md
  - docs/architecture/capabilities/visual-source-resolve.md
  - Work Item state
  - dedicated task prompt and referenced directives
  - active user profile visual_preferences + visual_identity
  - referenced user-owned strategy/visual-guidelines.md when present

reads:
  - task prompt/authoritative references
  - per-article checklist
  - effective visual source policy/local override
  - effective article logo policy (`visual_identity.logo_policy.article` plus local override)
  - user global/article rich visual directives
  - verified official logo assets when article branding may apply
  - verified user source media when applicable
  - article/branch/PR state
  - selected cloud-media workspace state
  - current runtime image generation/editing availability

writes:
  - target article file on intended work branch
  - per-article execution checklist
  - Work Item/task-specific durable state
  - content-local visual/source/brand provenance state
  - effective visual-contract snapshot/revision evidence
  - provider-backed source/proposal/final media through delegated capabilities
  - PR state

external_side_effects:
  - web/SERP/source research when required
  - create/reuse work branch and PR automatically
  - create/reuse selected cloud-media source/proposals/final workspace
  - read official project logo assets when article policy requires/allows branding
  - generate/edit visual proposals when runtime allows
  - compose exact official logo onto article visuals when effective article policy requires/allows it
  - otherwise produce complete external-generation prompt and resume after user returns/uploads image

validation:
  - no duplicate branch/PR
  - effective source policy and structured brand handoff resolved before drafting
  - complete visual contract resolved before visual generation
  - GitHub hard prerequisite remains operational
  - no source/proposal/final is called durable without cloud_media_storage
  - if policy requires user images before drafting, actual sources are verified/inspected first
  - no source image claimed without real file/bytes verification
  - no user original overwritten
  - strict/high fidelity prevents invented subject appearance
  - article follows task prompt and authoritative directives
  - factual/source claims trace to real sources
  - user article/global visual directives override conflicting generic creative defaults
  - `visual_identity.logo_policy.social` never controls article visuals
  - effective article logo application is resolved from `logo_policy.article` plus content-local override only
  - logo_application=always requires an exact official verified logo before final can reach verified_final
  - logo_application=never requires project logo absence in article final
  - logo_application=auto may include only an official verified logo, never a generated approximation
  - generated/materially transformed review sets retain exactly three reviewable A/B/C candidates when generation/treatment applies
  - use_as_is does not fabricate A/B/C
  - provider-backed binaries remain outside GitHub binary storage in normal mode
  - no fallback to WordPress/local filesystem as media storage
  - Work Item/checklist reflect real observable state

completion_conditions:
  - intended branch exists exactly once
  - visual source policy and structured brand handoff resolved
  - truthful pre-draft visual-source state reached
  - article/research/briefs persisted when drafting is allowed
  - applicable visual review package persisted/recoverable in selected cloud provider
  - effective article visual/logo contract is recoverable for review/finalization
  - if runtime generation unavailable, manual handoff completed before visual package is called ready
  - PR exists/reused
  - exact review version identifiable and presented
  - no externally visible publication performed
```

## Pre-draft visual-source and brand handoff gate

Canonical decision:

```text
creation request
-> resolve source policy
-> resolve article logo application independently
-> inspect local override
-> resolve/verify relevant user sources
-> apply missing_user_images_behavior
```

Truthful source states include:

```text
source_ready
ai_generation_allowed
continue_without_visuals
awaiting_user_images
manual_image_handoff_required
```

Structured brand state may additionally include:

```text
ready
awaiting_brand_asset
```

`continue_without_visuals` may allow editorial drafting/review only. It does not waive required-media publication gates downstream.

`awaiting_brand_asset` does not by itself prevent article text drafting or unbranded base-candidate exploration, but an article visual with `logo_application=always` cannot reach `verified_final` until an official logo is available and applied.

## Effective article visual contract

Before generating image proposals, combine:

```text
CMW generic article creative defaults
<- user project-global visual directives
<- user article-specific visual directives
<- content/image-local directives
```

with workflow/integrity/safety invariants remaining authoritative.

Generic article defaults are defined in `visual-generation-contract.md` and include, only where the user has not overridden them:

- realistic/credible professional visual direction as a strong default;
- real diversity across an article/recent related content;
- avoidance of repetitive AI clichés;
- not placing a person in every image;
- objects, places, gestures/details and concrete metaphors when stronger;
- 16:9 / 1600 x 900 / WebP article target by default;
- no marketing/headline text inside photographic article images by default;
- exactly three reviewable candidates for generated/materially transformed image groups.

These are not immutable artistic requirements. The user's global/article/local creative direction overrides them where it conflicts.

## Article logo policy

Resolve **only**:

```text
projects.<active>.visual_identity.logo_policy.article
```

then any explicit content-local article/image override.

Never use `logo_policy.social` as a fallback.

The following project preference is fully valid:

```yaml
logo_policy:
  article: never
  social: always
```

In that configuration, article image finals remain unbranded while social finals use the logo.

For article `always`, apply the exact official verified logo asset deterministically; do not ask the generative model to recreate it. For `never`, verify logo absence. For `auto`, any included logo must still be an official verified asset.

## Provider-neutral media workspace

Conceptually:

```text
<provider-root>/<site-domain>/articles/<article-slug>/
├── source-user/
├── proposals/
└── final/
```

Official project logos are stored separately in the private brand workspace defined by `brand-assets-contract.md`.

Implemented adapters are Google Drive and Dropbox. Use the provider selected in durable project state. If asking the user to place source images, show the exact provider path plus a verified direct folder link when the active adapter exposes one. Never silently switch providers during the article workflow.

GitHub, WordPress and local filesystem are not fallback media stores.

## Runtime image-generation fallback

When generation/editing required by effective policy is unavailable but cloud storage works:

1. freeze exact article revision + image brief + effective visual/source/brand contract;
2. produce a complete copy/paste prompt including objective, dimensions/format, style, composition, user global/article/local directives, source role/fidelity/treatment and required/forbidden elements;
3. when branding is required/possible, reserve safe composition space but do not ask the external generator to recreate the official logo;
4. instruct user to generate/improve image in an image-capable ChatGPT conversation or compatible image AI;
5. ask user to return/upload result;
6. inspect it;
7. persist it in provider-backed proposals/source state as appropriate;
8. apply exact official logo composition when required;
9. resume exact review/finalization workflow.

Do not silently substitute Canva or fake proposal state. The prompt itself is not a completed visual.

If cloud storage is also unavailable, generated/returned media cannot become durable `verified_final`; media-dependent completion/publication remains blocked.

## Article persistence and review

After pre-draft gate permits drafting:

```text
research + full article drafting
-> persist article + complete visual briefs/roles
-> resolve effective article visual contract
-> continue to normal generation or manual handoff
-> apply exact branding according to article policy when applicable
-> persist/verify media in selected cloud provider
-> present article + applicable visual review package
```

For generated/materially transformed work retain exactly three useful A/B/C candidates. For exact use_as_is show exact verified candidate instead.

When article logo policy is `always`, review candidates should reflect the real official-logo composition when technically possible before user selection of the intended final.

## Branch/PR policy

Create/reuse exactly one work branch and PR. Normal Git mechanics are internal after onboarding and do not become extra user approval gates.

## Independent validation gates

Keep editorial, media and external publication validation separate. Article/media validation never implies WordPress/social publication authorization.

## Finalization/historical binding

Before an article image reaches `verified_final`, `asset-ingest`/owning workflow verifies the effective article logo rule and records enough contract/brand evidence to identify what produced the final.

Changing project visual guidelines/logo policy/logo asset later does not silently rewrite already approved article media or publication candidates bound to exact hashes.

## Resume/failure

On interruption inspect checklist + durable article/media/brand/PR state first, reuse valid progress and continue from first incomplete observable task. Never claim failed/unavailable provider, generation or logo-composition actions succeeded.
