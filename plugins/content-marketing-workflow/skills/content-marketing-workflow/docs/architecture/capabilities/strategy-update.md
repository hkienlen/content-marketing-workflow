# Internal capability: strategy-update

Date: 2026-09-06
Status: current capability contract

## Purpose

`strategy-update` persists durable project/site directives without requiring the user to know which repository file owns the rule.

It is also the normal natural-language mutating route for durable project visual changes. The dedicated `/visual ...` commands use `visual-configure`, but equivalent natural-language requests may route here and must produce the same durable model.

Structured source/fidelity/treatment preferences belong in `visual_preferences`. Structured logo assets/policies and the rich visual-guidelines pointer belong in `visual_identity`. Rich free visual directives belong in the user-owned `strategy/visual-guidelines.md` authority.

A one-off article/post visual or logo instruction is **not** a strategy update; it remains a content-local override owned by the relevant creation workflow.

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
  - docs/architecture/visual-generation-contract.md
  - docs/architecture/brand-assets-contract.md
  - docs/architecture/capabilities/visual-configure.md
  - docs/architecture/schemas/user-profile.schema.json
  - user-data/profile.json when present
  - relevant user-owned authority referenced by active profile

optional_context:
  - relevant existing strategy files
  - affected content when deciding whether rule is global or content-local
  - previous durable visual preference/identity when updating it
  - existing strategy/visual-guidelines.md

reads:
  - active profile/project
  - relevant current authoritative preference/strategy
  - structured visual_preferences and visual_identity
  - rich visual-guidelines authority when relevant
  - compatibility projections when present
  - affected user-owned content only when needed to classify scope

writes:
  - active user profile for structured project preferences/infrastructure metadata
  - richer user-owned strategy authority when it owns prose/strategy rule
  - required compatibility projection when documented
  - no generic skill contract merely to save one user's concrete value

persists:
  - durable preference/directive
  - scope (project/global, article, social or content-local route)
  - structured visual_preferences when applicable
  - structured visual_identity/logo policy when applicable
  - rich permanent visual directive in strategy/visual-guidelines.md when applicable
  - traceable Git mutation and verified resulting state

external_side_effects:
  - GitHub user/project data mutation
  - provider-backed logo intake/replacement is delegated to visual-configure rather than implemented here
  - no image generation
  - no publication

human_approval:
  - explicit user intent is required before replacing a contradictory durable strategy/preference
  - summarize materially changed future visual/logo behavior in plain language when helpful
  - no separate GitHub approval gate

validation:
  - request classified durable vs one-off correctly
  - exactly one semantic authority is updated per value
  - visual_preferences/visual_identity validate against profile schema when changed
  - article/social source-treatment overrides are partial and inherit project default
  - logo_policy.article and logo_policy.social remain independent; changing one preserves the other
  - local one-content instructions are not promoted globally
  - rich user directives override conflicting generic creative defaults but not workflow/integrity invariants
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

### Durable project visual preference

Examples:

```text
"From now on, prefer my own photos."
"For articles, ask me for photos before drafting."
"For social posts, enhance my photos naturally."
"My product photos must remain strictly faithful."
```

These belong under:

```text
projects.<active_project>.visual_preferences
```

### Durable logo preference

Examples:

```text
"Never put my logo on article images."
"Always put my logo on social-post images."
"Use my logo case by case on articles."
```

These belong under:

```text
projects.<active_project>.visual_identity.logo_policy
```

The two channel fields are independent:

```yaml
logo_policy:
  article: always|auto|never
  social: always|auto|never
```

When changing only social, preserve article exactly. When changing only article, preserve social exactly.

A user may explicitly choose:

```yaml
article: never
social: always
```

and this must be treated as a normal durable configuration.

Official logo file intake/replacement itself is routed to `visual-configure` / `/visual logo` because it includes provider-backed brand-asset verification.

### Durable rich visual directive

Examples:

```text
"From now on, avoid 3D illustrations."
"For articles, prefer concrete objects and gestures instead of abstract graphics."
"For social posts, keep visible text very short."
"Never show people with their head in their hands."
```

These belong in the user-owned project authority, normally:

```text
strategy/visual-guidelines.md
```

Classify as global/article/social and preserve the user's useful wording. Do not force arbitrary creative detail into unrelated enums.

If the file does not exist, create the user-owned authority and set/update:

```text
projects.<active_project>.visual_identity.guidelines_path
```

### Content-local override

Examples:

```text
"For this post only, generate everything with AI."
"For this article only, use this photo without retouching."
"For this social post only, no logo."
"For image 2 only, make it an illustration."
```

Do not update project preference/identity/guidelines. Route/persist with owning article/social content state.

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

## Structured visual identity updates

Canonical shape:

```yaml
visual_identity:
  guidelines_path: strategy/visual-guidelines.md # optional/null when no rich user directives yet
  logo_policy:
    article: always|auto|never
    social: always|auto|never
  logo_assets:
    primary: ... # optional
    light: ...
    dark: ...
```

For a new `visual_identity`, article and social logo choices must both be explicit before persisting a confirmed complete identity policy. Do not copy one answer into both fields unless the user asked for that.

For an existing `visual_identity`, a one-field update preserves all other fields/asset references exactly.

If an `always` policy has no verified official logo, preserve the user's confirmed preference and expose the brand-asset blocker; do not invent a logo and do not silently downgrade `always` to `auto` or `never`.

## Creative precedence

Apply `docs/architecture/visual-generation-contract.md`:

```text
workflow/integrity/safety invariants
> content-local user directives
> channel-specific user directives
> project-global user directives
> generic CMW creative defaults
> executor interpretation
```

User directives therefore override conflicting CMW **creative defaults**. CMW defaults continue to fill dimensions the user did not specify.

## No duplicate authority

Do not maintain the same value independently in multiple authorities.

- profile `visual_preferences` owns structured sourcing/fidelity/treatment/missing-source settings;
- profile `visual_identity.logo_policy` owns independent article/social logo application;
- profile `visual_identity.logo_assets` owns references/metadata for official brand assets;
- profile `visual_identity.guidelines_path` points to the rich user visual authority;
- user-owned `strategy/visual-guidelines.md` owns rich creative/style/brand-placement prose;
- content item owns local override and source/final/effective-contract provenance.

If existing prose strategy contradicts newly confirmed structured preference, reconcile the prose authority or add a clear pointer rather than leave two active conflicting rules.

## GitHub behavior

Routine branch/commit/PR/merge is internal plumbing under `github-transparency`. User approves business preference, not Git mechanics.

Reuse appropriate architecture/configuration work branch when active; otherwise create a dedicated one. Verify resulting commit/merge state according to current workflow.

## Failure behavior

If scope is ambiguous in a way that materially changes future behavior, ask one concise clarification.

If profile/schema validation fails or a required authority cannot be updated, do not claim preference changed and preserve previous valid state.

Never fall back to changing a generic package contract simply because user profile write failed.
