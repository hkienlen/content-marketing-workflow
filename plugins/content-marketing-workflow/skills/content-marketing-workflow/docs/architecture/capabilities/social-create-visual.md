# Internal capability: social-create-visual

Date: 2026-09-05
Status: current architecture contract

## Purpose

`social-create-visual` produces/reviews the visual component for one accepted social post after visual-source policy and required source intake are resolved.

Global prerequisite/degradation behavior is owned by:

```text
docs/architecture/runtime-compatibility-matrix.md
```

This capability must not invent alternative storage/publication fallbacks.

## Capability contract

```yaml
name: social-create-visual
purpose: Produce a policy-compliant reviewable visual package for one accepted social post and persist it through the configured cloud-media provider.
availability: optional
feature_gate: social.enabled
mode: mutating

prerequisites:
  - social.enabled is true
  - exact durable post/concept is resolved
  - master text/visual brief are ready
  - effective visual policy was resolved by visual-source-resolve
  - required user source is verified/inspected when source-dependent
  - selected cloud_media_storage provider is operational before any proposal/final is claimed durable
  - runtime image generation/editing is available OR manual image handoff is used

mandatory_context:
  - AGENTS.md
  - docs/architecture/runtime-compatibility-matrix.md
  - docs/architecture/persistence-contract.md
  - docs/architecture/user-provided-images.md
  - docs/architecture/google-drive-workspace.md
  - docs/architecture/dropbox-workspace.md
  - docs/architecture/media-delivery-architecture.md
  - docs/architecture/image-asset-ingestion.md
  - docs/architecture/capabilities/visual-source-resolve.md
  - docs/architecture/capabilities/asset-ingest.md
  - docs/architecture/social-post-review-loop.md
  - exact post/checklist/current visual brief
  - current effective visual policy/source provenance

reads:
  - exact master text/concept/function
  - visual brief/platform policy
  - resolved source policy/local override
  - verified user source when applicable
  - current visual review state
  - selected cloud-media source/proposals/final state

writes:
  - visual review round state
  - provider-backed proposal candidates
  - exact source/final review reference for use_as_is
  - visual status/combined review references
  - selected final metadata through delegated asset-ingest

external_side_effects:
  - read verified source files from selected cloud provider or usable chat upload
  - generate/edit images through current runtime when available
  - otherwise execute manual image handoff prompt workflow
  - persist returned/generated proposals in selected cloud provider
  - no public sharing, scheduling or publication

validation:
  - runtime/provider availability matches central compatibility matrix
  - no proposal/final is called durable when cloud_media_storage is unavailable
  - generated/materially transformed workflows retain exactly three genuinely distinct reviewable A/B/C proposals
  - use_as_is does not fabricate synthetic alternatives
  - every claimed user source is real verified/inspected media
  - source original is never overwritten
  - strict/high fidelity preserves real subject appearance
  - proposals are persisted/recoverable before combined review
  - selected final is normalized/verified separately from source original
  - provider identity matches the selected project provider
  - no publication side effect occurs

completion_conditions:
  - review package is persisted/recoverable in selected cloud provider
  - generated/materially transformed mode -> durable A/B/C identities exist
  - exact use_as_is mode -> exact source/final candidate identity exists
  - after human selection, asset-ingest creates/reuses verified_final
```

## AI-first/runtime generation

When runtime generation/editing is available, create exactly three distinct A/B/C candidates for generated/materially transformed workflows and persist them before review.

## Manual image handoff

When generation/editing is required but unavailable in the current ChatGPT/Codex surface and cloud media is operational:

1. freeze exact post revision + visual brief + visual policy;
2. produce a complete copy/paste prompt for an image-capable ChatGPT conversation or compatible image AI;
3. include objective, format/dimensions, style, composition, brand constraints, required/forbidden elements, source role/fidelity/treatment and text constraints;
4. ask the user to return/upload the generated result;
5. inspect returned image;
6. persist it in selected provider `proposals/`;
7. continue normal review and `asset-ingest` finalization.

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

## Provider layout

Conceptual provider-neutral path:

```text
<provider-root>/<site-domain>/social/<post-name>/
├── source-user/
├── proposals/
│   └── round-<NN>/
└── final/
```

Implemented adapters are Google Drive and Dropbox. Use the selected project provider and its provider-specific workspace contract. GitHub, WordPress and local filesystem are not fallback media stores.

## Combined review and revisions

Generated/materially transformed mode shows full post text + A/B/C. Exact use_as_is mode shows full post text + exact source/final candidate.

Preserve frozen components during targeted revisions. A new generation round keeps the approved text/source policy unless explicitly reopened.

## Finalization

After human selection/validation invoke `asset-ingest`. Result preserves source original and persists provider-qualified final identity/SHA-256/format/dimensions/ALT plus source relationship.

## Resume/idempotency

Reuse exact selected-provider folders/source records/review rounds when recoverable. Do not regenerate solely because conversation restarted. Source/final hash drift fails closed. A provider change requires explicit migration/rebinding rather than silent reuse.
