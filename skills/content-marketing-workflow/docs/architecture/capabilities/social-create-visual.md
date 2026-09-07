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
= internal implementation artifact before official branding
= may be rendered transiently by an image-generation surface when that surface automatically displays tool output
= transient tool rendering is not a review presentation, A/B/C identity, selection request or approval gate
= never an A/B/C selectable review candidate when logo_application=always

review candidate
= persisted/recoverable visual shown for durable human selection
= bound to the frozen contract_revision
= already satisfies every visual invariant that can be satisfied before selection
```

When effective `logo_application=always`, **every A/B/C review candidate must already contain the exact verified official logo applied by deterministic composition**. There is no `when technically possible` exception for a durable/selectable review package.

If official-logo composition cannot be completed, base generation may continue for exploration. A surface-imposed transient rendering of a base is allowed, but the workflow must not label or present that base as a normal review proposal, must not ask the user to choose/validate it, must not persist it as selectable A/B/C, must not record durable visual selection, and must not set combined review to fully approved. Transient visibility alone is not a blocker; inability to retain the exact generated asset for required downstream deterministic composition is a separate runtime-capability blocker.

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

## Generator-input boundary

The **effective visual contract is not the image-generator prompt**.

When a generated base will later receive deterministic project branding, derive a separate **base-generation brief**. The image model must not receive the full effective visual contract, official-logo asset identity, provider IDs, hashes, logo filenames, or instructions such as “put the logo bottom-right”. Brand-placement preferences are converted into neutral reserved composition space, not generator branding instructions.

CMW bundles:

```text
scripts/base-generation-brief.py
```

Use it or an equivalent fail-closed derivation. A base-generation brief contains only:

- exact content kind and frozen `contract_revision` reference;
- candidate identity;
- creative scene/composition prompt with project-brand instructions removed;
- explicit negative constraint excluding project branding, pseudo-logos, signatures and watermarks;
- optional neutral reserved composition-space guidance.

The generator must never be given the official logo asset bytes or identifying metadata merely because the final policy is `always`.

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
- derive a brand-isolated base-generation brief before invoking an image model;
- generate/select a **clean base** with no project logo, pseudo-logo, signature, watermark or generated approximation baked into the pixels;
- visually inspect each retained base before composition;
- for a disposable pure-AI base with no unique source-fidelity requirement, if project branding or a plausible generated approximation appears, **reject and regenerate the base by default** rather than starting a logo-removal edit cycle;
- reserve targeted repair for source-dependent, user-owned, or recovery cases where preserving the existing pixels has real value;
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
-> derive brand-isolated base-generation briefs A/B/C
-> generate internal clean-base drafts with explicit no-project-branding constraint
-> inspect bases and reject/regenerate contaminated pure-AI bases by default
-> retain three strong clean bases
-> deterministically compose exact official logo on each base
-> validate hashes/evidence with visual-review-gate.py
-> persist exactly three branded review candidates A/B/C
-> present combined human review
-> bind selection to exact branded candidate hash
-> asset-ingest / verified_final
```

A raw generator output is not automatically a review proposal. The executor may create or persist clean-base drafts as implementation detail. When the active generation surface automatically renders tool output in chat, that transient rendering may be visible, but it remains non-interactive implementation output: do not label it Visual A/B/C, do not ask for a choice or approval, and do not stop solely because it was rendered. Continue automatically through remaining base generation, exact-asset retention/inspection, deterministic official-logo composition, review-gate validation and persistence. Only gate-passing branded derivatives count as A/B/C when `logo_application=always`; the first human visual decision is on those branded A/B/C candidates.

## Surface-imposed transient rendering

Some direct conversational image-generation surfaces render each generated image immediately as part of the tool call. CMW distinguishes that **tool rendering** from a **workflow review presentation**.

Rules:

- automatic rendering of a clean base does not make it `review-ready`, `Visual A/B/C`, selected or approved;
- do not ask the user to validate, reject or choose a transiently rendered base;
- do not fail closed merely because the user can see the tool output;
- continue the same `/social create` execution automatically until three compliant branded review candidates are ready;
- retain/ingest the exact generated binary or exact runtime asset reference when the surface exposes one, then perform deterministic branding on that exact base;
- if the surface genuinely cannot expose/recover the exact generated asset for required deterministic downstream composition, report the precise `generated_base_retention_unavailable` capability blocker and use the documented manual/compatible-surface handoff; do not misreport the blocker as “base was visible”.

Transient tool rendering therefore has **zero approval semantics**.

## Provider layout

Implemented adapters are Google Drive and Dropbox. Use the selected project provider and preserve provider-qualified identities; GitHub, WordPress and local filesystem are not fallback media stores.

Provider-neutral layout may retain both base and review layers, for example:

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
2. derive a brand-isolated external base-generation brief rather than exposing the full brand contract;
3. request no project logo, brand signature, watermark or substitute mark while reserving neutral composition space if useful;
4. inspect the returned base; for disposable pure-AI output, reject/regenerate contamination by default;
5. persist clean base evidence;
6. deterministically compose the exact official logo when required;
7. validate the review package;
8. only then present/select the review candidate.

The external prompt or unbranded/raw returned image is not itself a durable selectable proposal under `always`.

## Combined review and selection

Generated/materially transformed mode shows full post text + exactly three review-ready A/B/C visuals.

For `logo_application=always`, the candidate shown and selected by the user is the actual official-logo composition. The visual state must not claim `selected`, `visual_approved_text_pending`, `fully_approved`, or an equivalent durable visual approval when the displayed candidate failed the review-ready brand gate.

The explicit selection of one review-ready branded A/B/C candidate is the human visual approval for that visual revision. Normal non-material finalization after that selection must proceed automatically and must not ask for a second visual approval. A targeted re-confirmation is required only when finalization would materially alter what the user selected, such as a meaningful crop, logo reposition/variant change, visible-text change, creative retouch or other perceptible composition change.

Text approval remains independently preservable during a branding repair.

## Recovery of an already selected non-compliant candidate

If a previously selected visual is later discovered to contain a generated/unverified logo baked into its pixels:

1. preserve the user's **conceptual preference** and any approved text;
2. revoke only the technical/durable visual-selection claim; do not call the non-compliant binary `verified_final`;
3. if an exact clean pre-logo base exists, compose the official logo on that base;
4. if no exact clean base exists, do not claim that the same image can be recovered exactly; perform the narrowest feasible repair/regeneration while preserving the selected concept/composition as closely as possible;
5. because pixels changed, present the repaired officially-branded candidate for targeted human confirmation before restoring durable visual approval;
6. do not require a full A/B/C restart unless the user requests it or the repair materially changes the concept.

This recovery path is for already-selected/historically valuable pixels. It does not make logo-removal editing the normal path for a newly generated disposable base.

## Finalization

After a compliant human selection, invoke `asset-ingest` automatically. Do not introduce another approval gate for normalization, encoding, naming, hashing, provider storage or metadata work that preserves the selected visible composition.

Before `verified_final` verify normalization, source fidelity/provenance, effective social logo rule, exact official logo identity/version, exact final bytes/hash and the same effective-contract revision. If finalization cannot preserve the reviewed visual materially, stop before `verified_final`, produce the narrowest required changed candidate and request targeted re-confirmation of that changed visual only.

## Resume/idempotency

Reuse exact selected-provider folders/source records/review rounds when recoverable. A compliant approved review/final remains bound to its recorded contract revision and branded asset hash. Do not regenerate solely because the conversation restarted. Source/final/logo hash drift fails closed. A provider change requires explicit migration/rebinding rather than silent reuse.
