# Internal capability: social-inspect

Date: 2026-09-02
Status: current architecture contract

## Purpose

`social-inspect` provides read-only inventory and detail views for the complete social editorial reserve, including article-derived concepts/posts and standalone/free posts.

It backs:

```text
/social list
/social details <post-or-concept>
```

## Capability contract

```yaml
name: social-inspect
purpose: List the complete social reserve and materialized posts with provenance, strategic function and lifecycle state, or display one resolved post/concept with its durable content and metadata.
availability: optional
feature_gate: social.enabled
mode: read_only

prerequisites:
  - social.enabled is true
  - social durable state is readable

mandatory_context:
  - AGENTS.md
  - docs/architecture/user-command-runtime-contract.md
  - docs/architecture/content-inspection-state-model.md
  - docs/architecture/social-workflow.md
  - docs/architecture/social-creation-queue.md
  - strategy/social-media-strategy.md
  - social/README.md
  - social/id-registry.json when present

reads:
  - social/**/series-plan.md
  - materialized social post files/checklists, including social/free/**
  - social/id-registry.json
  - provider-backed visual metadata
  - platform scheduling/publication state

writes: []
persists: []
external_side_effects: []
human_approval: []

operations:
  list:
    - build article-derived inventory from all series-plan concepts
    - join materialized article-derived posts by exact series_concept/post_id/source provenance
    - add standalone/free materialized posts as first-class inventory entries
    - cross-check post_id registry
    - include orphan/mismatched posts instead of dropping them
    - expose source_type, source article/free topic, series_function when persisted, state, post_id and platform state
  details:
    - resolve exact post_id, exact series_concept key or exact post path
    - fail closed on ambiguity/not-found
    - show persisted series_function and series role/order when available
    - show full master text only when materialized
    - never invent article/series provenance or strategic function

validation:
  - no mutation
  - no post_id allocation
  - no drafting/scheduling/publication side effect
  - unmaterialized concepts remain visible
  - free posts remain visible without fake article relationships
  - persisted strategic function is displayed; legacy absence is shown as unknown/not-classified rather than guessed
  - mismatches are reported, not repaired
  - published requires durable verification evidence

completion_conditions:
  - requested inventory/details returned from durable state
  - no mutation occurred
```

## `/social list`

Minimum useful fields:

```text
post_id (or -) | source_type | concept/free_topic | function | source article | state | platforms/planning
```

User-facing function labels should render as:

```text
Identification
Expertise / compréhension
Méthode / positionnement
Offre / conversion
```

For legacy content with no durable `series_function`, show `-`/`unknown` rather than classifying it during inspection.

## `/social details <post-or-concept>`

For article-derived entries, show persisted `series_function`, role/order when present, article + series provenance, master text if materialized, visual/ALT and platform state.

For free posts, show `source_type: free`, `free_topic`, persisted strategic function when present, master text and media/platform state, with no invented article or `series_concept`.

For unmaterialized article-derived concepts, show only durable series-plan information.

Inspection never starts drafting or repairs missing classifications.

## Required productization tests

Tests must cover article-derived concepts, materialized posts, free posts, strategic-function visibility/legacy absence, stale plan projections, registry mismatches and orphan materialized posts.
