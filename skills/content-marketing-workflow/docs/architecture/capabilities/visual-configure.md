# Capability: visual-configure

Date: 2026-09-06
Status: current capability contract

## Purpose

`visual-configure` lets a user inspect and change durable project visual configuration without needing to know repository paths or schema details.

It owns the user-facing configuration surface for:

- logo asset intake/replacement;
- independent article/social logo application preferences;
- rich permanent visual directives;
- guided visual setup/resume.

Equivalent natural-language requests route to the same behavior.

## Public operations

```text
/visual status
/visual configure
/visual logo
/visual guidelines
/logo
```

`/logo` is a convenience alias for `/visual logo`.

## Core model

Structured operational choices live in `user-data/profile.json`:

```yaml
visual_preferences:
  default: ...
  article: ...
  social: ...

visual_identity:
  guidelines_path: strategy/visual-guidelines.md
  logo_policy:
    article: always|auto|never
    social: always|auto|never
  logo_assets:
    primary: <optional>
    light: <optional>
    dark: <optional>
```

The article and social logo choices are always resolved independently. Never copy one answer to the other unless the user explicitly asks for the same policy.

Rich style/direction rules live in the user-owned project document referenced by `visual_identity.guidelines_path`, normally:

```text
strategy/visual-guidelines.md
```

The generic Skill does not package that project's concrete file.

## Operation: status

Read-only.

Show, when resolvable:

- whether structured `visual_preferences` are configured;
- visual-guidelines authority path/status;
- logo assets available (`primary`, `light`, `dark`) with no secret data;
- article logo policy;
- social logo policy;
- any unresolved brand-asset blocker;
- relevant next command.

Do not create folders/files, upload media or change preferences during status.

## Operation: configure

Guided mutating setup/resume.

Resolve only missing or requested decisions. Do not restart completed onboarding from zero.

Guide the user through, as applicable:

1. source preference/fidelity/treatment (`visual_preferences`);
2. whether the user has an official logo;
3. logo asset intake, ideally asking for light/dark variants when available while accepting a single official logo;
4. **article logo preference**: always / case-by-case / never;
5. **social logo preference**: always / case-by-case / never;
6. whether generic CMW visual defaults are acceptable where no user directive exists;
7. any permanent global/article/social visual directives in free natural language.

Ask article and social logo behavior as separate decisions. A valid result is, for example, articles without logo and social posts always with logo.

Summarize future behavior in plain language before first persistence/material replacement, then persist/re-read/verify.

## Operation: logo

Mutating when intake/replacement/policy change is requested; otherwise may inspect current logo state.

Supported intents include:

```text
add my logo
replace my logo
add light/dark variants
show current logo configuration
never put my logo on articles
always put my logo on social posts
use my logo case by case on social
```

Logo asset requirements follow `docs/architecture/brand-assets-contract.md`.

When the user supplies a logo through chat or provider storage:

1. confirm a usable file actually exists;
2. inspect/validate it as an image;
3. retain the official original in the active private cloud-media brand workspace when durable use is requested;
4. persist provider-qualified asset identity/hash/metadata when available;
5. never overwrite the previous official source during replacement;
6. re-read/verify durable profile/provider state.

Do not synthesize a light/dark variant unless the user explicitly asks for a derived asset and the transformation can preserve brand integrity. Default behavior is to ask for the official missing variant or continue with the available official logo where legible.

## Operation: guidelines

Persist or inspect rich visual directives.

When the user supplies a durable instruction such as:

```text
"From now on, avoid 3D illustrations."
"For articles, prefer concrete objects and gestures."
"For social posts, use less text in images."
```

classify scope and update `strategy/visual-guidelines.md` while preserving unrelated rules.

Recommended sections:

```text
# Visual guidelines

## Global
## Articles
## Social
## Brand and logo placement
## People and representation
## Photography and illustration
## Text in images
## Required elements
## Forbidden elements
## Free permanent directives
```

If the file does not exist and a durable directive is supplied, create it as user/project data. Do not create one inside the generic Skill package.

A one-off request such as `for this post only` belongs to content-local state and is routed to the owning article/social workflow instead of changing the durable guidelines.

## Precedence

Always apply `docs/architecture/visual-generation-contract.md`:

```text
workflow/integrity invariants
> content-local user directive
> channel-specific user directive
> project-global user directive
> generic CMW creative default
```

User creative directives win over conflicting generic creative defaults. Generic defaults still fill gaps.

## Capability contract

```yaml
name: visual-configure
purpose: Inspect or persist durable user/project visual identity, logo assets/policies and rich visual directives.
availability: core
feature_gate: null
mode: mixed_by_operation

prerequisites:
  - active project/profile can be resolved for mutating operations
  - GitHub user/project repository is readable; writable for mutations
  - active cloud-media provider is operational before provider-backed logo intake is called durable

mandatory_context:
  - AGENTS.md
  - docs/architecture/persistence-contract.md
  - docs/architecture/user-profile-data-contract.md
  - docs/architecture/visual-generation-contract.md
  - docs/architecture/brand-assets-contract.md
  - docs/architecture/google-drive-workspace.md
  - docs/architecture/dropbox-workspace.md
  - docs/architecture/schemas/user-profile.schema.json
  - active user-data/profile.json when present
  - referenced strategy/visual-guidelines.md when present

reads:
  - active project profile
  - structured visual_preferences
  - visual_identity/logo policy/logo asset registry
  - user visual-guidelines authority
  - active provider brand workspace when logo state is inspected

writes:
  - user-data/profile.json structured visual configuration
  - user-owned strategy/visual-guidelines.md
  - private provider-backed brand/logo assets when supplied

external_side_effects:
  - private cloud-media brand folder/file creation/reuse for logo intake/replacement
  - GitHub user/project-data mutations
  - no article/post generation unless routed to owning content workflow
  - no publication

human_approval:
  - explicit user intent required before replacing official logo or contradictory durable preference
  - article/social logo preferences are separately confirmed/resolved
  - summarize material future behavior before first durable persistence/replacement

validation:
  - profile validates against schema
  - article/social logo preferences remain independent
  - actual logo assets are verified before persisted as available
  - no user logo/directive enters generic Skill contracts
  - rich directives update one user authority rather than duplicate semantic authorities
  - local one-content directives are not promoted globally
  - writes are re-read/verified

completion_conditions:
  - requested status accurately reported OR
  - requested durable visual configuration is persisted and verified
  - any missing official asset required by `always` policy remains an explicit resumable blocker
```

## Failure behavior

If a required logo file is missing/unverifiable, do not invent it and do not claim the logo setup is complete.

If cloud storage is unavailable, structured logo policy may still be persisted, but no provider-backed logo asset is called configured/verified. Report the exact blocker.

If a user's scope is genuinely ambiguous between one-off and permanent behavior, ask one concise clarification; otherwise respect explicit scope without additional friction.
