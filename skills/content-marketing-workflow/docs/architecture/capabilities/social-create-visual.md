# Internal capability: social-create-visual

Date: 2026-09-06
Status: current architecture contract

## Purpose

`social-create-visual` produces/reviews the visual component for one accepted social post after visual-source policy, user visual directives, branding policy and required source intake are resolved.

Global prerequisite/degradation behavior is owned by:

```text
docs/architecture/runtime-compatibility-matrix.md
```

Generic creative defaults and user-directive precedence are owned by:

```text
docs/architecture/visual-generation-contract.md
```

Brand/logo integrity and application are owned by:

```text
docs/architecture/brand-assets-contract.md
```

This capability must not invent alternative storage/publication fallbacks or synthesize a missing official logo.

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
  - complete effective visual contract is resolved from generic defaults + user global/social directives + content-local directives
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
  - verified user source when applicable
  - current visual review state
  - selected cloud-media source/proposals/final state

writes:
  - visual review round state
  - effective visual-contract snapshot/revision evidence
  - provider-backed proposal candidates
  - exact source/final review reference for use_as_is
  - brand composition metadata/logo asset identity when applied
  - visual status/combined review references
  - selected final metadata through delegated asset-ingest

external_side_effects:
  - read verified source files from selected cloud provider or usable chat upload
  - read verified official logo asset from private provider brand workspace when applicable
  - generate/edit base images through current runtime when available
  - deterministically compose exact official logo when effective social logo policy requires/allows it
  - otherwise execute manual image handoff prompt workflow
  - persist returned/generated proposals in selected cloud provider
  - no public sharing, scheduling or publication

validation:
  - runtime/provider availability matches central compatibility matrix
  - no proposal/final is called durable when cloud_media_storage is unavailable
  - generic creative defaults are applied only where user directives do not override them
  - content-local user directives override social/global creative directives as defined by visual-generation-contract
  - generated/materially transformed workflows retain exactly three genuinely distinct reviewable A/B/C proposals
  - social candidates are materially varied or intentionally coherent as a short sub-series rather than falsely near-duplicate
  - use_as_is does not fabricate synthetic alternatives
  - every claimed user source is real verified/inspected media
  - source original is never overwritten
  - strict/high fidelity preserves real subject appearance
  - `visual_identity.logo_policy.article` never controls a social visual
  - effective social logo application is resolved from `logo_policy.social` plus content-local override only
  - logo_application=always requires an exact official verified logo before final can reach verified_final
  - logo_application=never requires project logo absence in final
  - logo_application=auto may include only an official verified logo, never a generated approximation
  - official logo proportions/colors/integrity are preserved
  - proposals are persisted/recoverable before combined review
  - selected final is normalized/verified separately from source original
  - provider identity matches the selected project provider
  - no publication side effect occurs

completion_conditions:
  - review package is persisted/recoverable in selected cloud provider
  - generated/materially transformed mode -> durable A/B/C identities exist
  - exact use_as_is mode -> exact source/final candidate identity exists
  - effective social visual/logo contract is recoverable for the active review round
  - after human selection, asset-ingest creates/reuses verified_final only when brand policy is satisfied
```

## Effective visual contract before generation

Before producing candidates, combine:

```text
CMW social creative defaults
<- user project-global visual directives
<- user social-specific visual directives
<- content-local post directives
```

with workflow/integrity invariants remaining authoritative.

The user-owned authority is normally referenced by:

```text
visual_identity.guidelines_path -> strategy/visual-guidelines.md
```

Do not silently convert one successful historical social visual style into a permanent rule unless the user adopted it durably.

## Generic social defaults

When the user has not specified otherwise, follow `visual-generation-contract.md`, including:

- visual as hook rather than full post summary;
- mobile-first readability;
- 4:5 / 1080 x 1350 master target when appropriate for enabled channels;
- short visible hook when useful, not automatic paragraphs;
- JPEG for photographic scenes, PNG for infographic/flat/text-heavy designs when appropriate;
- credible people/environments/objects and avoidance of generic corporate stock aesthetics;
- real diversity across campaigns and exactly three genuinely distinct A/B/C candidates for generated/materially transformed work.

These are creative defaults. A user's social-specific direction overrides them where it conflicts.

## Social logo policy

Resolve **only**:

```text
projects.<active>.visual_identity.logo_policy.social
```

then an explicit content-local post override.

Never use `logo_policy.article` as a fallback.

For example, the project may legitimately have:

```yaml
logo_policy:
  article: never
  social: always
```

and every social final should then be branded while article finals remain unbranded.

### `always`

- use an official verified logo asset;
- prefer light/dark variant according to actual contrast when available;
- compose the exact logo deterministically rather than asking the generative model to recreate it;
- branded review candidates should show the real logo when review depends on final composition;
- no unbranded final can become `verified_final`.

If no usable official logo is available, preserve `awaiting_brand_asset`; base generation may continue but finalization blocks.

### `never`

- do not apply the project logo;
- verify absence before `verified_final`;
- a historical logo on a previous post does not override the current preference.

### `auto`

- include/omit according to current composition and user guidelines;
- any included logo must be an official verified asset;
- lack of a logo asset does not force synthetic recreation.

## AI-first/runtime generation

When runtime generation/editing is available, create exactly three distinct A/B/C candidates for generated/materially transformed workflows and persist them before review.

The base-generation prompt/brief includes applicable user directives and may reserve safe logo space, but it must not ask the image model to invent an official logo.

## Manual image handoff

When generation/editing is required but unavailable in the current ChatGPT/Codex surface and cloud media is operational:

1. freeze exact post revision + visual brief + effective visual/source/brand policy;
2. produce a complete copy/paste prompt for an image-capable ChatGPT conversation or compatible image AI;
3. include objective, format/dimensions, style, composition, user global/social/local directives, source role/fidelity/treatment, required/forbidden elements and text constraints;
4. if branding is required/possible, instruct the external generator to reserve composition space but not recreate the official logo;
5. ask the user to return/upload the generated result;
6. inspect returned image;
7. persist it in selected provider `proposals/`;
8. apply exact official logo composition locally/through an appropriate image-edit/composition capability when required;
9. continue normal review and `asset-ingest` finalization.

The prompt itself is not a visual proposal and never completes the capability.

If cloud storage is unavailable, returned/generated images may be inspected transiently but cannot become durable proposals/finals and social publication remains blocked.

## User source modes

Supported roles remain:

```text
use_as_is
enhance
subject_reference
inspiration_reference
composition_input
```

Strict/high fidelity never silently replaces a real subject with synthetic appearance. `use_as_is + ai_treatment:none` intentionally skips A/B/C generation.

Brand composition never overwrites the original user source. The branded social final is a separate derivative/final object.

## Provider layout

Conceptual provider-neutral content path:

```text
<provider-root>/<site-domain>/social/<post-name>/
├── source-user/
├── proposals/
│   └── round-<NN>/
└── final/
```

Official project logos are separately retained under the private brand workspace defined by `brand-assets-contract.md`.

Implemented adapters are Google Drive and Dropbox. Use the selected project provider and its provider-specific workspace contract. GitHub, WordPress and local filesystem are not fallback media stores.

## Combined review and revisions

Generated/materially transformed mode shows full post text + A/B/C. Exact use_as_is mode shows full post text + exact source/final candidate.

When effective social logo policy is `always`, reviewable candidates should reflect the actual official-logo composition when technically possible so the user is selecting the intended final visual, not an incomplete approximation.

Preserve frozen components during targeted revisions. A new generation round keeps the approved text/source/user directives/logo policy unless explicitly reopened.

## Finalization

After human selection/validation invoke `asset-ingest`.

Before `verified_final`:

- normalize to current social dimensions/format policy;
- verify source fidelity/provenance;
- verify effective social logo rule;
- if logo present, verify exact official logo asset identity/version and integrity;
- persist effective-contract evidence so later project preference changes do not reinterpret this final;
- persist provider-qualified final identity/SHA-256/format/dimensions/ALT plus source/brand relationship.

## Resume/idempotency

Reuse exact selected-provider folders/source records/review rounds when recoverable. Re-resolve current project visual configuration only for new/reopened work; an existing approved review/final remains bound to its recorded effective contract/revision.

Do not regenerate solely because conversation restarted. Source/final/logo hash drift fails closed. A provider change requires explicit migration/rebinding rather than silent reuse.
