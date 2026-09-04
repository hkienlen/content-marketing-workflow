# Internal capability: strategy-update

Date: 2026-09-04
Status: current capability contract

## Purpose

`strategy-update` persists durable project/site directives without requiring the user to know which repository file owns the rule.

It is also the normal mutating route for durable project visual-preference changes such as `visual_source`, missing-source behavior, source fidelity and AI treatment. Concrete visual preferences are user/project data and belong in the active profile's structured `visual_preferences`, not in generic skill code.

A one-off article/post visual instruction is **not** a strategy update; it remains a content-local override owned by the relevant creation workflow.

## Contract

```yaml
name: strategy-update
purpose: Persist a durable user/project strategy, preference or directive in its authoritative user-data location and keep required projections consistent.
availability: core
feature_gate: null
mode: mutating

prerequisites:
  - active project/profile can be resolved
  - GitHub user/project repository is readable/writable
  - repository-wide persistence/user-profile contracts are readable

mandatory_context:
  - AGENTS.md
  - docs/architecture/persistence-contract.md
  - docs/architecture/user-profile-data-contract.md
  - docs/architecture/github-transparency.md
  - docs/architecture/business-model-extensibility.md
  - docs/architecture/user-provided-images.md
  - docs/architecture/schemas/user-profile.schema.json
  - user-data/profile.json when present
  - relevant user-owned authority referenced by active profile

optional_context:
  - relevant existing strategy files
  - affected content when deciding whether rule is global or content-local
  - previous durable visual preference when updating it

reads:
  - active profile/project
  - relevant current authoritative preference/strategy
  - compatibility projections when present
  - affected user-owned content only when needed to classify scope

writes:
  - active user profile for structured project preferences/infrastructure metadata
  - richer user-owned strategy authority when it owns prose/strategy rule
  - required compatibility projection when documented
  - no generic skill contract merely to save one user's concrete value

persists:
  - durable preference/directive
  - scope (project/global vs content-specific)
  - structured visual_preferences when applicable
  - traceable Git mutation and verified resulting state

external_side_effects:
  - GitHub user/project data mutation only
  - no image generation/intake
  - no publication

human_approval:
  - explicit user intent is required before replacing a contradictory durable strategy/preference
  - summarize materially changed visual behavior in plain language when helpful
  - no separate GitHub approval gate

validation:
  - request classified durable vs one-off correctly
  - exactly one semantic authority is updated
  - visual_preferences validate against profile schema when changed
  - article/social overrides are partial and inherit project default
  - local one-content instructions are not promoted globally
  - no pilot-specific value enters generic skill contract
  - required compatibility projections stay consistent
  - write is re-read/verified

completion_conditions:
  - intended durable value exists in authoritative user/project data
  - affected profile/schema validation passes
  - dependent projection updated when required
  - Git mutation verified
  - user is told the future behavior changed and any relevant next action
```

## Classification before mutation

Classify user statement before writing.

### Durable project preference

Examples:

```text
"À partir de maintenant, privilégie mes propres photos."
"Pour les articles, demande-moi les photos avant de rédiger."
"Pour les réseaux sociaux, améliore mes photos naturellement."
"Mes photos de produits doivent rester strictement fidèles."
```

These belong under:

```text
projects.<active_project>.visual_preferences
```

### Content-local override

Examples:

```text
"Pour ce post seulement, génère tout avec l'IA."
"Pour cet article uniquement, utilise cette photo sans retouche."
```

Do not update project preference. Route/persist with owning article/social content state.

If current command is explicitly `/strategy update` but request itself clearly says `for this post only`, explain that it is a local content instruction and route it rather than silently making it global.

## Structured visual preference updates

Canonical shape:

```yaml
visual_preferences:
  default:
    visual_source: ai_first|user_images_first|strict_user_images|hybrid_best_fit
    missing_user_images_behavior: ask_before_drafting|allow_ai_generation|continue_without_visuals
    source_fidelity: strict|high|moderate|flexible
    ai_treatment: none|light_correction|natural_enhancement|marketing_enhancement|creative_transformation
    ai_treatment_directive: <string-or-null>
  article: <optional partial override>
  social: <optional partial override>
```

When changing only one field/channel, preserve unaffected fields exactly. Do not rewrite the whole policy to guessed defaults.

If project has no explicit `visual_preferences` yet and user supplies enough information to establish only one partial aspect, gather only genuinely required missing fields needed to create a valid `default` policy; do not infer profession/site-specific assumptions.

## No duplicate authority

Do not maintain the same structured visual sourcing fields independently in `strategy/image-guidelines.md` and profile.

- profile `visual_preferences` owns structured sourcing/fidelity/treatment/missing-source settings;
- user-owned image/brand strategy may own richer prose constraints/style/brand rules;
- content item owns local override and source provenance.

If existing prose strategy contradicts newly confirmed structured preference, reconcile the prose authority or add a clear pointer rather than leave two active conflicting rules.

## GitHub behavior

Routine branch/commit/PR/merge is internal plumbing under `github-transparency`. User approves business preference, not Git mechanics.

Reuse appropriate architecture/configuration work branch when active; otherwise create a dedicated one. Verify resulting commit/merge state according to current workflow.

## Failure behavior

If scope is ambiguous in a way that materially changes future behavior, ask one concise clarification.

If profile/schema validation fails or a required authority cannot be updated, do not claim preference changed and preserve previous valid state.

Never fall back to changing a generic package contract simply because user profile write failed.
