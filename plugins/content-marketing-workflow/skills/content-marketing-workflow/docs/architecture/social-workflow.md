# Social workflow architecture

Date: 2026-09-05
Status: current architecture contract

## Purpose

This document defines the durable end-to-end social workflow of the single installable Content / Marketing skill.

It covers article-derived and free posts, source planning, strategic function, immutable IDs, pre-draft visual-source resolution, writing, visual review/finalization, scheduling, exact publication authorization, provider creation evidence, post-publication verification and optional notifications.

Read together with:

```text
docs/architecture/runtime-compatibility-matrix.md
docs/architecture/user-provided-images.md
docs/architecture/google-drive-workspace.md
docs/architecture/dropbox-workspace.md
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
-> provider-appropriate final text artifact stored with final visual
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

The goal is coverage and balance, not a rigid quota. Never invent unsupported offers or commercial claims merely to fill a function. Default ordering avoids consecutive `conversion`/strong CTA posts when a reasonable alternative exists.

## Series planning and review

A new/materially revised article series must be fully generated/persisted before review and fully human-validated before first new post drafting.

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

`visual-source-resolve` resolves project default -> social override -> post-local override.

When user media is relevant, the capability creates/reuses in the selected provider:

```text
<provider-root>/<site-domain>/social/<post-name>/source-user/
```

and verifies/inspects real files before their visible attributes influence master text or visual brief.

When asking the user to deposit images, display:

```text
exact canonical selected-provider source-user path
+ verified direct clickable provider folder link when available
```

Never guess a folder link or claim files exist without resolving them. Google Drive and Dropbox provider-specific behavior is governed by their workspace contracts.

A direct chat upload is valid when a real image attachment exists and is inspected. Retain/copy original into selected-provider `source-user/` when durable continuation requires it and preserve source provenance/hash when exact bytes are available.

User originals are never overwritten. Provider failure never silently switches the project to the other provider.

## Source roles and fidelity

Durable source role may be:

```text
use_as_is
enhance
subject_reference
inspiration_reference
composition_input
```

`strict_user_images` and strict/high fidelity prohibit silent synthetic replacement of the real subject. Ask only when ambiguity materially changes fidelity/treatment/result.

## Master text

Draft only after all applicable series/source gates pass.

Master text must be complete publishable copy, derived from validated concept/source/article/free topic and current writing strategy. Do not include production notes/Markdown not intended for publication.

Persist `text_status: in_review` before first combined review. Explicit human approval is required for `approved`.

## Visual workflow

### AI-first or materially transformed user-source workflow

```text
master text + visual brief + source/fidelity constraints
-> generate/treat candidates
-> inspect/regenerate off-brief outputs
-> retain exactly three genuinely distinct reviewable A/B/C
-> persist/verify in selected provider private proposals
-> combined review
```

### Exact `use_as_is`

```text
verified source
-> preserve original
-> prepare/reuse exact review/final candidate
-> combined review with exact visual
```

Do not generate fake A/B/C alternatives solely to satisfy the generated-proposal rule.

## Combined review

Normal first review presents one package: complete master text plus either A/B/C or the exact `use_as_is` visual. Approved components remain frozen unless explicitly reopened or materially invalidated by another requested change.

## Final media and provenance

`asset-ingest` normalizes/verifies human-selected candidate and persists provider-qualified final identity, filename, SHA-256, MIME, dimensions and `asset_status: verified_final`.

When user-provided source is involved, retain `source_type: user_provided`, provider/source identity/reference, original filename/hash when available, source role, fidelity and treatment.

Source original and final derivative are distinct durable concepts and source original is not destroyed during normalization.

## Final cloud package

For every supported cloud-media provider, finalization uses:

```text
<provider-root>/<site-domain>/social/<post-name>/
├── source-user/   # when applicable; private originals
├── proposals/
└── final/
    ├── selected normalized visual
    └── provider-appropriate copy/paste-ready final text artifact
```

Provider-specific final text artifact:

```text
google_drive -> one native Google Doc containing only exact approved publishable text
dropbox      -> one UTF-8 plain-text .txt file containing only exact approved publishable text
```

The final text artifact is canonical per post package and reused/updated on revised approval rather than duplicated. The historical filename `social-final-drive-package.md` remains the authority for this provider-neutral contract.

## Scheduling

Scheduling occurs only after complete text/media/final-package approval.

Keep distinct:

```text
planned_at
publication-consent policy
exact authorized_for_scheduled_publication record
```

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

## Post-publication verification

Facebook Page and LinkedIn verification rules remain platform-specific and independent of the selected cloud-media provider. A cloud provider is transport/storage, not social publication authority.

## Optional Telegram publication report

When verified/enabled in active profile, report only after durable publication/verification reconciliation. Notification failure never changes publication state and never triggers republication.

## Observable state invariant

```text
series generated != series validated
concept accepted != post drafted
visual policy resolved != source verified != source inspected
source inspected != master text approved
visual generated != visual stored != visual selected != verified_final
use_as_is source != synthetic proposal
combined review shown != fully approved
final visual != complete final cloud package
scheduled != exact publication authorization
scheduler success != provider creation evidence
provider creation evidence != post-publication verification
publication state != Telegram delivery state
```

## Resume/idempotency

On every resume read exact durable series/post/checklist/ID/source-policy/source-provenance/provider-media/final-package/schedule/authorization/publication/verification/notification state.

Continue from first incomplete task whose prerequisites are satisfied.

Do not duplicate IDs, series plans, selected-provider source-user folders, retained source copies, proposal rounds, final assets, final text artifacts, external posts or notifications merely because execution restarted.

A project provider change requires explicit migration/rebinding before old provider identities are treated as current.
