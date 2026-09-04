# Internal capability: social-create-visual

Date: 2026-09-04
Status: current architecture contract

## Purpose

`social-create-visual` produces/reviews the visual component for one accepted social post after the effective visual-source policy and any required user-source intake have been resolved.

It supports both:

- AI-first or materially transformed visual workflows with exactly three A/B/C review proposals;
- verified user-provided source workflows, including exact `use_as_is` and faithful enhancement/reference treatments.

It must never silently replace a real strict/high-fidelity subject with synthetic appearance.

## Capability contract

```yaml
name: social-create-visual
purpose: Produce a policy-compliant reviewable visual package for one accepted social post, using verified user sources when required and generating A/B/C only when alternatives/material transformation are appropriate.
availability: optional
feature_gate: social.enabled
mode: mutating

prerequisites:
  - social.enabled is true
  - exact durable post/concept is resolved
  - master text/visual brief are ready for current revision
  - effective visual policy was resolved by visual-source-resolve
  - required user source is verified/inspected when source-dependent
  - private Drive social workspace is available

mandatory_context:
  - AGENTS.md
  - docs/architecture/persistence-contract.md
  - docs/architecture/github-transparency.md
  - docs/architecture/user-provided-images.md
  - docs/architecture/google-drive-workspace.md
  - docs/architecture/media-delivery-architecture.md
  - docs/architecture/image-asset-ingestion.md
  - docs/architecture/capabilities/visual-source-resolve.md
  - docs/architecture/capabilities/asset-ingest.md
  - docs/architecture/social-post-review-loop.md
  - docs/architecture/social-execution-checklist.md
  - strategy/social-visual-guidelines.md
  - exact post/checklist/current visual brief
  - current effective visual policy/source provenance

reads:
  - exact current master text/concept/function
  - visual brief and required placement/platform policy
  - resolved source policy and local override
  - verified user source bytes/visual inspection/provenance when applicable
  - active visual review round and any frozen approved components
  - Drive source-user/proposals/final state

writes:
  - visual review round state
  - Drive proposal candidates for generated/materially transformed workflows
  - exact source/final review reference for use_as_is workflows
  - visual status/combined review references in durable post/checklist
  - selected final metadata through delegated asset-ingest after explicit human selection

external_side_effects:
  - read verified user source files from Drive/chat-retained source state
  - generate or edit images through the assistant image-generation capability when policy/role requires it
  - persist generated/treated proposal files in private Drive proposals workspace
  - no public sharing
  - no scheduling/publication

human_approval:
  - final exact visual selection/validation
  - source role/fidelity/treatment clarification only when materially ambiguous and not already explicit
  - targeted review/revision loop remains explicit

validation:
  - visual workflow mode matches effective visual_source + source_role + ai_treatment + source_fidelity
  - generated/materially transformed workflows retain exactly three genuinely distinct reviewable A/B/C proposals
  - use_as_is + no material treatment does not fabricate synthetic alternatives
  - every claimed user source is a real verified/inspected asset
  - source original is never overwritten
  - strict/high fidelity preserves real subject appearance and forbids misleading generation
  - proposals are persisted/recoverable before combined review
  - approved/frozen components remain unchanged unless explicitly reopened or materially invalidated
  - selected final is normalized/verified separately from source original
  - no publication side effect occurs

completion_conditions:
  - one visual review package appropriate to source role is ready and persisted/recoverable
  - generated/materially transformed mode -> exactly A/B/C proposal identities are durable
  - exact use_as_is mode -> exact source/final candidate identity is durable without fake A/B/C
  - visual package can be shown together with complete post text
  - after explicit human selection/validation, asset-ingest creates/reuses a verified final and preserves source provenance
```

## Input modes

### AI-first

Typical resolved policy:

```yaml
visual_source: ai_first
```

Create exactly three distinct A/B/C candidates from the current brief and persist/verify them before review.

### User source - enhance

```yaml
source_role: enhance
source_fidelity: strict|high|moderate|flexible
ai_treatment: light_correction|natural_enhancement|marketing_enhancement|creative_transformation
```

Use verified source bytes as actual transformation input. Create A/B/C when materially distinct compliant treatment choices are useful.

For strict/high fidelity, preserve identity/appearance of required real subject and do not add/remove/change product features, face/body identity, work details or material characteristics merely for aesthetics.

### User source - subject reference

`source_role: subject_reference` means the real subject must be respected. Composition/background may vary only within fidelity/treatment rules. A/B/C can represent distinct compliant compositions when material transformation is desired.

### User source - inspiration reference

`source_role: inspiration_reference` means source provides mood/style inspiration rather than an exact subject claim. Generation may be more flexible, still subject to truthfulness and effective policy.

### User source - composition input

`source_role: composition_input` integrates the actual source into a broader composition. Generated composites belong in `proposals/`, selected derivative in `final/`; source original remains unchanged.

### User source - use as is

```yaml
source_role: use_as_is
ai_treatment: none
```

This mode is intentionally not A/B/C generation.

```text
verified/inspected source original
-> determine allowed non-material normalization/crop/format constraints
-> prepare/reuse exact review candidate without changing source original
-> persist/recover exact candidate identity
-> combined text + exact visual review
-> explicit human visual validation
-> asset-ingest to separate final derivative/object if normalization is required
```

If crop/format would materially alter a strict/high-fidelity source, surface the constraint rather than silently changing it.

## Proposal quality rules

When A/B/C applies, candidates must be genuinely distinct while serving same approved brief. Do not satisfy count by trivial crops/color shifts unless those are genuinely meaningful requested treatments.

Before review, inspect outputs and regenerate candidates that are off-brief, misleading relative to verified user source, visually defective, duplicate/near-duplicate, platform-incompatible or inconsistent with durable brand/visual directives.

Persist exactly final reviewable A/B/C, not every failed generation attempt.

## Source facts vs generation

A source image may inform text/visual design only after `visual-source-resolve` verified and inspected it.

Do not infer unsupported product composition, dimensions, performance or business facts from a photo alone. Never use a different synthetic object as if it were user's exact product/work under strict/high fidelity.

## Drive layout

```text
<drive-root>/<site-domain>/social/<post-name>/
├── source-user/
├── proposals/
│   └── round-<NN>/
└── final/
```

`source-user/` contains private originals and is never overwritten or publicized. `proposals/` contains generated/treated alternatives. `final/` contains selected normalized final media.

A later destination may use `tmp-outbox`; transport copy is separate from source/proposal/final identity.

## Combined review

Generated/materially transformed mode shows full post text plus Visual A/B/C.

Exact `use_as_is` mode shows full post text plus exact source/final visual candidate.

Guidance explains allowed actions relevant to mode, including text-only changes, visual-only changes, both, replacing source, changing treatment, or requesting new A/B/C round where applicable.

## Targeted revisions

Preserve frozen components:

- approved text stays frozen for visual-only work;
- approved/selected exact user source stays frozen unless user changes source/role or requested treatment materially requires reopening it;
- criticizing A does not alter B/C;
- changing only background under high-fidelity product instruction must not change product;
- new A/B/C round uses same approved text/source policy unless explicitly reopened.

Every material generated/treatment review round binds exact post revision + source provenance + proposal identities.

## Finalization

After human selection/validation invoke `asset-ingest` with selected proposal or exact source/final candidate, target dimensions/format, source provenance/role/fidelity/treatment where applicable and replacement intent when replacing an existing verified final.

Result preserves source original and persists final provider identity/SHA-256/format/dimensions/ALT plus source relationship.

## Resume/idempotency

On restart:

- reuse exact source-user folder and verified source records;
- reuse existing active proposal round when complete/recoverable;
- do not regenerate A/B/C merely because conversation restarted;
- do not convert use_as_is into generated mode;
- do not create duplicate final asset for same selected final identity/hash;
- if source/final identity hash drifts, fail closed.
