# Internal capability: social-create-visual

Date: 2026-09-06
Status: current architecture contract

## Purpose

`social-create-visual` produces/reviews the visual component for one accepted social post after visual-source policy, user visual directives, branding policy and required source intake are resolved.

Global prerequisite/degradation behavior is owned by `docs/architecture/runtime-compatibility-matrix.md`. Generic creative defaults and user-directive precedence are owned by `docs/architecture/visual-generation-contract.md`. Brand/logo integrity is owned by `docs/architecture/brand-assets-contract.md`.

This capability must not invent alternative storage/publication fallbacks, synthesize a missing official logo, or let a generated approximation of the project logo enter a selectable human-review package.

## Core invariant: review-ready means finalizable-by-design

For generated/materially transformed social visuals, distinguish two artifact classes:

```text
base draft
= internal/generated visual before official branding
= may be inspected/discussed transiently
= never an A/B/C selectable review candidate when logo_application=always

review candidate
= persisted/recoverable visual shown for durable human selection
= bound to the frozen contract_revision
= already satisfies every visual invariant that can be satisfied before selection
```

When effective `logo_application=always`, **every A/B/C review candidate must already contain the exact verified official logo applied by deterministic composition**. There is no `when technically possible` exception for a durable/selectable review package.

If official-logo composition cannot be completed, base generation may continue for exploration, but the workflow must not persist/present the outputs as selectable A/B/C, must not record a durable visual selection, and must not set combined review to fully approved.

## Capability contract

```yaml
name: social-create-visual
purpose: Produce a policy-compliant, user-directive-compliant and brand-compliant reviewable visual package for one accepted social post and persist it through the configured cloud-media provider.
availability: optional
feature_gate: social.enabled
mode: mutating

prerequisites:
  - social.enabled is true
  - exact durable post/concept is resolved
  - master text/visual brief are ready
  - effective source policy and structured brand handoff were resolved by visual-source-resolve
  - complete effective visual contract is resolved and frozen
  - required user source is verified/inspected when source-dependent
  - selected cloud_media_storage provider is operational before any proposal/final is claimed durable
  - runtime image generation/editing is available OR manual image handoff is used

mandatory_context:
  - AGENTS.md
  - docs/architecture/runtime-compatibility-matrix.md
  - docs/architecture/persistence-contract.md
  - docs/architecture/user-provided-images.md
  - docs/architecture/visual-generation-contract.md
  - docs/architecture/brand-assets-contract.md
  - docs/architecture/google-drive-workspace.md
  - docs/architecture/dropbox-workspace.md
  - docs/architecture/media-delivery-architecture.md
  - docs/architecture/image-asset-ingestion.md
  - docs/architecture/capabilities/visual-source-resolve.md
  - docs/architecture/capabilities/asset-ingest.md
  - docs/architecture/social-post-review-loop.md
  - exact post/checklist/current visual brief
  - current effective visual/source/brand policy and source provenance
  - referenced user-owned strategy/visual-guidelines.md when present

reads:
  - exact master text/concept/function
  - visual brief/platform policy
  - resolved source policy/local override
  - resolved social logo application (`visual_identity.logo_policy.social` plus local override)
  - verified official logo asset references when branding may apply
  - user global/social rich visual directives
  - current visual review state and provider-backed artifacts

writes:
  - visual review round state
  - effective visual-contract snapshot/revision evidence
  - clean base-draft evidence when retained
  - provider-backed review candidates
  - deterministic logo-composition evidence when applied
  - selected final metadata through delegated asset-ingest

validation:
  - no proposal/final is called durable when cloud_media_storage is unavailable
  - generated/materially transformed workflows retain exactly three genuinely distinct reviewable A/B/C candidates
  - `visual_identity.logo_policy.article` never controls a social visual
  - effective social logo application is resolved from `logo_policy.social` plus content-local override only
  - logo_application=always requires exact official-logo composition before a candidate becomes reviewable/selectable
  - logo_application=never requires project logo absence
  - logo_application=auto may include only an official verified logo, never a generated approximation
  - generated/unverified project branding in a base draft causes rejection/regeneration/repair before review packaging
  - official logo proportions/colors/integrity are preserved
  - review candidate identity is bound to exact contract_revision and exact branded output hash
  - selected final is normalized/verified separately from source original
  - no publication side effect occurs

completion_conditions:
  - review package is persisted/recoverable in selected cloud provider
  - generated/materially transformed mode -> exactly three review-ready A/B/C identities exist
  - effective social visual/logo contract is recoverable for the active review round
  - after human selection, asset-ingest creates/reuses verified_final only when brand policy is satisfied
```

## Effective visual contract before generation

Before producing candidates, combine CMW social defaults with user project-global, social-specific and content-local directives, while workflow/integrity invariants remain authoritative.

The user-owned rich authority is normally `visual_identity.guidelines_path -> strategy/visual-guidelines.md`.

## Social logo policy

Resolve **only**:

```text
projects.<active>.visual_identity.logo_policy.social
```

then an explicit content-local post override. Never use `logo_policy.article` as a fallback.

A valid project can have:

```yaml
logo_policy:
  article: never
  social: always
```

### `always`

- use an official verified logo asset;
- choose the verified light/dark variant according to actual contrast when available;
- generate/select a **clean base** with no project logo, pseudo-logo, signature or generated approximation baked into the pixels;
- explicitly tell image generation not to render the project logo/brand signature; reserving logo space is allowed;
- visually inspect each retained base before composition; if project branding or a plausible generated approximation appears, reject/regenerate it or repair it before it can become reviewable;
- compose the exact logo deterministically from verified bytes;
- run `scripts/visual-review-gate.py` or equivalent validation before claiming the durable A/B/C package is review-ready;
- show the real branded output to the user for selection;
- bind the user's selection to that branded review-asset identity/hash, not to the clean base or a generative preview.

If no usable official logo or deterministic composition path is available, preserve the blocker. Drafting/base exploration may continue, but no durable/selectable visual review package exists yet.

### `never`

- do not apply the project logo;
- reject a generated base that accidentally contains the project's logo or a generated approximation intended to stand for it;
- verify absence before `verified_final`.

### `auto`

- decide include/omit according to current composition and user guidelines;
- any included project logo must be official and verified;
- never treat generated branding as an acceptable `auto` choice.

## Generated/materially transformed workflow

Normal `always` flow:

```text
freeze effective contract_revision
-> generate internal clean-base drafts with explicit no-project-logo instruction
-> inspect bases and reject accidental/generated branding
-> retain three strong clean bases
-> deterministically compose exact official logo on each base
-> validate hashes/evidence with visual-review-gate.py
-> persist exactly three branded review candidates A/B/C
-> present combined human review
-> bind selection to exact branded candidate hash
-> asset-ingest / verified_final
```

A raw generator output is not automatically a review proposal. The executor may create or persist internal drafts as implementation detail, but only gate-passing branded derivatives count as A/B/C when `logo_application=always`.

Provider-neutral layout may retain both layers, for example:

```text
<provider-root>/<site-domain>/social/<post-name>/
└── proposals/
    └── round-<NN>/
        ├── A/
        │   ├── base/<clean-base>
        │   ├── review/<officially-branded-candidate>
        │   └── logo-composition.json
        ├── B/
        └── C/
```

Adapters may map layout differently, but must preserve recoverable base/review identities and composition evidence.

## Manual image handoff

When generation/editing is unavailable in the current surface but cloud media is operational:

1. freeze post revision, visual brief and effective contract;
2. produce a complete external-generation prompt;
3. when logo may be required, explicitly request **no project logo or brand signature in the generated base**, while reserving safe composition space if useful;
4. inspect the returned base; reject/repair accidental generated branding;
5. persist clean base evidence;
6. deterministically compose the exact official logo when required;
7. validate the review package;
8. only then present/select the review candidate.

The external prompt or unbranded/raw returned image is not itself a durable selectable proposal under `always`.

## Combined review and selection

Generated/materially transformed mode shows full post text + exactly three review-ready A/B/C visuals.

For `logo_application=always`, the candidate shown and selected by the user is the actual official-logo composition. The visual state must not claim `selected`, `visual_approved_text_pending`, `fully_approved`, or an equivalent durable visual approval when the displayed candidate failed the review-ready brand gate.

Text approval remains independently preservable during a branding repair.

## Recovery of an already selected non-compliant candidate

If a previously selected visual is later discovered to contain a generated/unverified logo baked into its pixels:

1. preserve the user's **conceptual preference** and any approved text;
2. revoke only the technical/durable visual-selection claim; do not call the non-compliant binary `verified_final`;
3. if an exact clean pre-logo base exists, compose the official logo on that base;
4. if no exact clean base exists, do not claim that the same image can be recovered exactly; perform the narrowest feasible repair/regeneration while preserving the selected concept/composition as closely as possible;
5. because pixels changed, present the repaired officially-branded candidate for targeted human confirmation before restoring durable visual approval;
6. do not require a full A/B/C restart unless the user requests it or the repair materially changes the concept.

This recovery path prevents a late branding defect from discarding already approved text or the user's selected creative direction while still preserving truthfulness.

## Finalization

After a compliant human selection, invoke `asset-ingest`.

Before `verified_final` verify normalization, source fidelity/provenance, effective social logo rule, exact official logo identity/version, exact final bytes/hash and the same effective-contract revision.

## Resume/idempotency

Reuse exact selected-provider folders/source records/review rounds when recoverable. A compliant approved review/final remains bound to its recorded contract revision and branded asset hash. Do not regenerate solely because the conversation restarted. Source/final/logo hash drift fails closed. A provider change requires explicit migration/rebinding rather than silent reuse.
