# Internal capability: article-inspect

Date: 2026-09-02
Status: current architecture contract

## Purpose

`article-inspect` provides read-only inventory and detail views for SEO articles without mutating article, checklist, WordPress or publication state.

It backs:

```text
/article list
/article details <article>
```

Command parsing/error/response-envelope semantics are defined in `docs/architecture/user-command-runtime-contract.md`. State/identity derivation is defined in `docs/architecture/content-inspection-state-model.md`.

## Capability contract

```yaml
name: article-inspect
purpose: List articles and derive their current editorial/WordPress/publication state, or display one resolved article with its complete current content and durable workflow metadata.
availability: core
mode: read_only

prerequisites:
  - repository article/workflow state is readable

mandatory_context:
  - AGENTS.md
  - docs/architecture/user-command-runtime-contract.md
  - docs/architecture/content-inspection-state-model.md
  - docs/architecture/article-execution-checklist.md
  - docs/architecture/wordpress-review-gate.md
  - docs/architecture/capabilities/wordpress-prepare-article.md
  - docs/architecture/capabilities/wordpress-publish-article.md

reads:
  - articles/**/*.md excluding checklist/support files when enumerating article bodies
  - exact matching article checklists
  - exact related Work Item/Human Item planning state when needed
  - persisted WordPress managed draft/presentation/publication evidence
  - verified production publication/readback evidence when available

writes: []
persists: []
external_side_effects: []
human_approval: []

operations:
  list:
    - enumerate materialized article bodies
    - optionally include exact planned records with no materialized body
    - join exact durable workflow/WordPress/publication evidence
    - derive synthetic display state using the deterministic state contract
    - return stable identity, state, WordPress/publication facts and evidence notes
  details:
    - resolve exact path, exact filename, exact front-matter slug or exact filename stem
    - fail closed on ambiguity/not-found
    - derive state/evidence summary
    - display complete current Markdown article content when materialized

validation:
  - no repository mutation
  - no WordPress mutation
  - no workflow resume/repair
  - test/preprod technical publication is never treated as production published
  - front-matter status alone cannot establish production publication
  - mere Divi/config/support-file existence cannot establish WordPress managed-draft state
  - display state is derived according to content-inspection-state-model.md
  - ambiguous identifier resolution returns candidates instead of guessing
  - missing/inconsistent evidence is surfaced conservatively

completion_conditions:
  - requested inventory/details are returned from durable state
  - result is representable by the runtime `article-list` or `article-details` response contract
  - no mutation occurred
```

## `/article list`

Minimum useful fields:

```text
title/slug | path/planned identity | display state | WordPress state | verified publication/public URL
```

The view may add target, Work Item, keyword, next gate and evidence warning when useful.

The enumeration/join/order algorithm is authoritative in `content-inspection-state-model.md`.

## `/article details <article>`

Accepted identity forms include:

```text
/article details <article-slug>
/article details <article-slug>.md
/article details articles/<audience>/<article-slug>.md
```

Return useful metadata/state/evidence first, followed by the complete current article Markdown content for a materialized article.

This operation does not create a missing article and does not resume its workflow. If the user wants work to continue, route separately to `/article create`, `/article update`, WordPress preparation, or the appropriate natural-language equivalent.

## Required tests at productization

The future implementation must satisfy the article cases in `docs/architecture/user-command-productization-checklist.md`, including the regression case where `status: published` plus only a test-site URL must not produce verified production `published`.
