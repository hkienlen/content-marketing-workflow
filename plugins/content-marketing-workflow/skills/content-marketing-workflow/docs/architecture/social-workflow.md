# Social workflow architecture

Date: 2026-09-04
Status: current architecture contract

## Purpose

This document defines the durable end-to-end social workflow of the single installable Content / Marketing skill.

It covers article-derived and free posts, source planning, strategic function, immutable IDs, pre-draft visual-source resolution, writing, visual review/finalization, scheduling, exact publication authorization, provider creation evidence, post-publication verification and optional notifications.

Read together with:

```text
docs/architecture/user-provided-images.md
docs/architecture/capabilities/visual-source-resolve.md
docs/architecture/social-creation-queue.md
docs/architecture/social-series-review-gate.md
docs/architecture/social-post-review-loop.md
docs/architecture/social-final-drive-package.md
docs/architecture/social-execution-checklist.md
docs/architecture/capabilities/social-create-post.md
docs/architecture/capabilities/social-create-visual.md
```

## Core invariants

```text
series planning/validation
!= post creation
!= visual-source intake
!= text approval
!= visual/source approval
!= scheduling
!= exact publication authorization
!= scheduler dispatch
!= provider creation evidence
!= post-publication verification
!= notification delivery
```

In particular:

```text
scheduler success
!= provider creation evidence
!= post-publication verification
```

A source image, selected image or successful visual review is never publication authorization.

## Generic social flow

For an article-derived post:

```text
validated source article
-> inventory/deduplicate/plan series
-> classify strategic functions + build balanced order
-> persist/re-read complete series plan
-> human validates complete new/materially revised series
-> select/resume next eligible concept
-> allocate/reuse immutable post_id
-> visual-source-resolve BEFORE master-text drafting when effective policy requires/prioritizes user media
-> source_ready | ai_generation_allowed | continue_without_visuals | awaiting_user_images
-> if allowed, draft complete master text from exact concept and verified source facts only
-> create visual brief/role
-> social-create-visual
-> combined human review
-> selected/final visual normalized/verified through asset-ingest
-> final coherent snapshot
-> scheduling when requested
-> exact authorization materialized when policy/gates permit
-> scheduler/relay when due
-> provider creation evidence
-> post-publication verification
-> optional notification report
```

If `awaiting_user_images`, drafting does not begin until actual source media is supplied/located/verified/inspected or an explicit compatible content-local override changes that item only.

For a free post, skip only the article-series planning/validation step. All source, text, visual, scheduling and publication gates remain.

## Strategic functions

Article-derived series use:

```text
identification
expertise
positioning
conversion
```

User-facing labels:

```text
Identification
Expertise / compréhension
Méthode / positionnement
Offre / conversion
```

The goal is coverage and balance, not a rigid quota. Never invent unsupported offers or commercial claims merely to fill a function. Default ordering avoids consecutive `conversion`/strong CTA posts when a reasonable alternative exists.

## Series planning and review

A new/materially revised article series must be fully generated/persisted before review and fully human-validated before first new post drafting.

The review shows at least proposed order, concept/title, angle, strategic function, concrete role/purpose, state, useful source/offer/link/deduplication notes, distribution/coverage summary and order rationale.

After exact list validation, continue automatically to first eligible post. Do not ask another generic `go`.

An unchanged already validated series is not re-presented before every subsequent post.

## Queue and ID semantics

`/social create` first resumes a started/incomplete eligible post, otherwise chooses first eligible not-yet-written concept in exact validated order. When active series is exhausted, roll deterministically to next eligible validated article and create/review its plan.

An immutable `post_id` is allocated only when a concept is accepted for production. Restart/resume reuses same ID. `deferred`/`rejected` concepts do not consume IDs.

## Pre-draft visual-source resolution

The active project profile may define:

```text
visual_preferences.default
visual_preferences.social
```

A post may add a local partial override without changing those durable project preferences.

`visual-source-resolve` resolves:

```text
project default
-> social override
-> post-local override
```

Supported source modes:

```text
ai_first
user_images_first
strict_user_images
hybrid_best_fit
```

When user media is relevant, the capability creates/reuses:

```text
<drive-root>/<site-domain>/social/<post-name>/source-user/
```

and verifies/inspects real files before their visible attributes influence master text or visual brief.

When asking the user to deposit images in Drive, always display:

```text
exact canonical source-user path
+ verified direct clickable Google Drive folder link
```

Never guess a folder link or claim files exist without resolving them.

A direct chat upload is valid when a real image attachment exists and is inspected. Retain/copy original into provider-backed `source-user/` when durable continuation requires it and preserve source provenance/hash when exact bytes are available.

User originals are never overwritten.

### Strict mode

`strict_user_images` and strict/high fidelity prohibit silent synthetic replacement of the real subject. A generic `allow_ai_generation` missing-source value does not override a strict truth requirement. A deliberately different one-off result requires an explicit compatible local override.

## Source roles

Durable source role may be:

```text
use_as_is
enhance
subject_reference
inspiration_reference
composition_input
```

If role is obvious from explicit instruction, do not ask again. Ask only when ambiguity materially changes fidelity/treatment/result.

## Master text

Draft only after all applicable series/source gates pass.

Master text must be complete publishable copy, derived from validated concept/source/article/free topic and current writing strategy. Do not include production notes/Markdown not intended for publication.

When verified user source is available, use only visible/verified facts. Never infer unsupported product material, dimensions, performance, identity or business claims from a photo.

Persist `text_status: in_review` before first combined review. Explicit human approval is required for `approved`.

## Visual workflow

### AI-first or materially transformed user-source workflow

```text
master text + visual brief + source/fidelity constraints
-> generate/treat candidates
-> inspect/regenerate off-brief outputs
-> retain exactly three genuinely distinct reviewable A/B/C
-> persist/verify in private Drive proposals
-> combined review
```

### Exact `use_as_is`

When exact verified user source is intended unchanged and `ai_treatment: none`/only non-material normalization applies:

```text
verified source
-> preserve original
-> prepare/reuse exact review/final candidate
-> combined review with exact visual
```

Do **not** generate fake A/B/C alternatives solely to satisfy the old generated-proposal rule.

### Other user-source roles

Enhance/reference/composition modes may produce A/B/C when materially distinct compliant choices are useful. Strict/high fidelity remains a hard constraint on subject truth.

## Combined review

Normal first review presents one package.

Generated/materially transformed:

```text
post ID/concept/function
complete master text
Visual A
Visual B
Visual C
explicit guidance
```

Exact `use_as_is`:

```text
post ID/concept/function
complete master text
exact source/final candidate
explicit guidance
```

Guidance allows text-only changes, visual-only changes, both, new visual round where applicable, changing treatment/source, or validating text + exact visual choice.

Approved components remain frozen unless explicitly reopened or materially invalidated by another requested change.

## Final media and provenance

`asset-ingest` normalizes/verifies human-selected candidate and persists final provider identity, filename, SHA-256, MIME, dimensions and `asset_status: verified_final`.

When user-provided source is involved, retain source provenance including `source_type: user_provided`, provider/source asset identity/original filename/hash when available, source role, fidelity and treatment.

Source original and final derivative are distinct durable concepts and source original is not destroyed during normalization.

## Final Drive package

For Drive-backed social post finalization:

```text
social/<post-name>/
├── source-user/   # when applicable; private originals
├── proposals/
└── final/
    ├── selected normalized visual
    └── one native Google Doc containing only exact approved publishable text
```

The Google Doc is canonical per post final package and reused/updated on revised approval rather than duplicated.

## Scheduling

Scheduling occurs only after complete text/media approval.

Before fixing `planned_at`, inspect neighbouring global scheduled/published content and avoid unnecessary consecutive conversion/strong-CTA posts. Never silently override an exact user-selected time; propose alternative or persist deliberate exception rationale.

Keep distinct:

```text
planned_at
publication-consent policy
exact authorized_for_scheduled_publication record
```

Active per-platform user profile policy may be `one_off_exact_confirmation` or `standing_auto_publish_scheduled`.

Standing scheduled policy may eliminate repetitive confirmation only after final content/visual/ALT/schedule validation and by materializing an exact per-post authorization. It never becomes wildcard permission.

Any bound text/ALT/media/target/time/hash change invalidates exact authorization and requires reconciliation/revalidation.

## Provider execution

Current scheduler pattern:

```text
planned_at durable state
-> platform GitHub Actions scheduler
-> dedicated relay
-> SEO Workflow Bridge
-> exact target/content/media/time checks
-> provider mutation
```

Execution may occur later than `planned_at` within adapter tolerance, never earlier.

A green scheduler run proves only due-record handling/relay dispatch. It does **not** prove remote post creation.

## Publication evidence

Provider creation evidence must match exact current authorization/revision/schedule/target/content/media intent before it becomes current durable publication state.

Historical/mismatched idempotency evidence must never be projected as a new publication.

If external creation may have occurred but result is not definitive, use `uncertain_external_result` and stop blind automatic retry.

Current platform evidence:

```text
LinkedIn -> HTTP 201 + x-restli-id
Facebook -> definitive remote post/media IDs + HTTP success + exact current authorization binding
```

## Post-publication verification

### Facebook Page

After definitive creation with current supported Bridge, read back exact remote post/media; verify Page identity, remote IDs and expected message hash; bind verification to current authorization and persisted IDs; persist `verification_state: remote_verified` on success.

If definite creation succeeded but read-back fails, publication remains `published`; do not republish solely because verification failed.

### LinkedIn member

Current access persists definitive provider creation evidence and:

```text
verification_state: provider_acknowledged
readback_available: false
```

Do not label it `remote_verified` without future supported independent read-back.

## Optional Telegram publication report

When verified/enabled in active profile, report only after durable publication/verification reconciliation. Use `TELEGRAM_BOT_TOKEN` only from GitHub Actions Repository Secrets, never expose token in profile/Git/chat/logs, honor success/failure/uncertain preferences and suppress duplicate exact reports.

Notification failure never changes publication state and never triggers republication.

## Observable state invariant

```text
series generated != series validated
concept accepted != post drafted
visual policy resolved != source verified != source inspected
source inspected != master text approved
visual generated != visual stored != visual selected != verified_final
use_as_is source != synthetic proposal
combined review shown != fully approved
scheduled != exact publication authorization
scheduler success != provider creation evidence
provider creation evidence != post-publication verification
publication state != Telegram delivery state
```

## Resume/idempotency

On every resume read exact durable series/post/checklist/ID/source-policy/source-provenance/provider-media/schedule/authorization/publication/verification/notification state.

Continue from first incomplete task whose prerequisites are satisfied.

Do not duplicate IDs, series plans, source-user folders, retained source copies, proposal rounds, final assets, external posts or notifications merely because execution restarted.

Once provider creation is definitive, editorial reset is not a retry mechanism. Verification/notification repair remains separate from publication mutation.
