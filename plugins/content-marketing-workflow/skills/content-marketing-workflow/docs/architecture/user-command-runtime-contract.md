# User command runtime contract

Date: 2026-09-06
Status: architecture contract

## Purpose

This contract makes the explicit `/...` command layer implementable without inventing parser, dispatch, error-handling or response-shape rules during productization.

It complements:

```text
docs/architecture/user-command-interface.md
docs/architecture/user-command-catalog.yaml
docs/architecture/user-command-catalog.schema.json
docs/architecture/content-inspection-state-model.md
docs/architecture/user-provided-images.md
docs/architecture/visual-generation-contract.md
docs/architecture/brand-assets-contract.md
```

The command layer remains only a deterministic invocation/router surface above authoritative capability contracts.

## Runtime pipeline

Every explicit command must follow this order:

```text
raw user input
-> detect explicit command
-> normalize command prefix/family/subcommand only
-> match canonical catalogue entry
-> parse declared arguments
-> evaluate feature/configuration availability
-> resolve capability/operation
-> execute authoritative capability contract
-> render declared response shape
-> return normalized error if any stage fails
```

No stage may silently reinterpret an unknown slash command as a different mutating command.

Natural-language routing remains separate and may use semantic intent resolution, but once it resolves to a capability it must execute the same authoritative capability contract as the corresponding explicit command.

## Explicit-command detection

Treat a message as an explicit command when its first non-whitespace character is `/` and the following token matches the skill command namespace/families known to the catalogue.

Rules:

- ignore leading/trailing whitespace around the whole input;
- command family/subcommand matching is ASCII case-insensitive;
- preserve argument text exactly except for outer whitespace trimming;
- do not lowercase slugs, paths, IDs, quoted text or free-form user arguments before capability-level resolution;
- collapse repeated whitespace only between command-name tokens, not inside argument values;
- a slash appearing later in ordinary prose is not an explicit command;
- unknown commands fail closed with `COMMAND_NOT_FOUND` and may suggest close catalogue matches without executing them.

Examples that resolve to the same command:

```text
/article list
 /ARTICLE   LIST  
```

Example whose argument must remain intact:

```text
/article details articles/<audience>/<article-slug>.md
```

## Command matching precedence

Match from most specific canonical syntax to least specific:

1. exact full fixed command tokens;
2. fixed command tokens followed by declared positional arguments;
3. command-family help target;
4. no fallback to a sibling mutating command.

For example, `/article details foo` must never fall through to `/article update` or `/article create` if `foo` cannot be resolved.

`/logo` is a declared canonical alias entry for the `visual-configure` logo operation. It is not fuzzy matching for an unknown command.

## Arguments

The machine-readable catalogue declares each argument.

Supported argument kinds for the initial command layer:

- `positional`: value follows fixed command tokens;
- `trailing_text`: all remaining text is one value;
- `named_optional`: optional future extension, only when explicitly declared.

Initial implementation should prefer one `trailing_text` argument for natural-language-friendly commands and one exact positional identifier for `details` commands.

Argument rules:

- missing required argument -> `ARGUMENT_REQUIRED`;
- extra undeclared arguments -> `ARGUMENT_UNEXPECTED`, unless the command declares trailing free text;
- quoted and unquoted values are accepted where practical; quote removal must affect only one matching pair of outer quotes;
- argument parsing never performs entity resolution; entity resolution belongs to the target capability.

## Availability and feature gates

Availability is evaluated after parsing but before capability execution.

Possible runtime availability states:

```text
available
disabled
not_configured
unsupported
```

Feature gates are read from durable project configuration.

A disabled command may still appear in `/help`, but execution returns `FEATURE_DISABLED` or `NOT_CONFIGURED` with the blocking gate/configuration key.

A feature gate never acts as runtime authorization for an external side effect. Publication capabilities retain their separate exact human authorization contracts.

Core `/visual ...` commands have no social/WordPress feature gate. Mutating logo intake may still be blocked by missing active project/GitHub write access or unavailable cloud-media provider, while `/visual status` remains read-only.

## Dispatch

Each public catalogue entry must resolve to exactly one of:

- `capability` + optional `operation`;
- internal read-only `behavior` for `/help` or `/status`.

The dispatcher must not contain duplicated business rules from capability contracts.

Supporting capabilities that are intentionally internal are not dispatchable merely because they exist in the repository. In particular:

```text
visual-source-resolve
asset-ingest
```

are internal-only orchestration/support capabilities.

`visual-configure` is public through the catalogue operations:

```text
status
configure
logo
guidelines
```

Natural-language equivalents must execute the same capability contract and persistence rules.

## Normalized errors

The implementation must expose at least these semantic error codes:

```text
COMMAND_NOT_FOUND
COMMAND_AMBIGUOUS
ARGUMENT_REQUIRED
ARGUMENT_UNEXPECTED
FEATURE_DISABLED
NOT_CONFIGURED
IDENTITY_NOT_FOUND
IDENTITY_AMBIGUOUS
STATE_INCONSISTENT
PREREQUISITE_MISSING
AUTHORIZATION_REQUIRED
ADAPTER_UNAVAILABLE
EXECUTION_BLOCKED
INTERNAL_CONTRACT_ERROR
```

The user-facing response should remain conversational, but code/tests may assert these semantic classes.

A visual-source gate such as `awaiting_user_images` and a brand gate such as `awaiting_brand_asset` are normally durable workflow blocker/states, not command parser errors. The owning capability may render the command result as `blocked` with the exact next action.

### Identity errors

`IDENTITY_NOT_FOUND` means no durable object matches the declared resolution rules.

`IDENTITY_AMBIGUOUS` means more than one durable object matches. Return candidate identifiers/paths and do not guess.

### State inconsistency

For read-only inspection, conflicting durable evidence should normally produce the requested result with a warning/evidence note and synthetic `unknown`/appropriate conservative state rather than mutate state.

Use `STATE_INCONSISTENT` when the conflict prevents a trustworthy requested answer.

## Response envelope semantics

The skill is conversational, so it need not emit literal JSON to the user. Internally, every command result should be representable by this conceptual envelope:

```yaml
command: /article list
status: ok|blocked|error
availability: available|disabled|not_configured|unsupported
capability: article-inspect
operation: list
summary: <short human-readable result>
data: <command-specific structured result>
warnings: []
next_actions: []
error:
  code: null
  message: null
  candidates: []
```

This gives implementation/tests a stable semantic target while allowing natural ChatGPT rendering.

## Required response shapes

### `/help`

Data must be representable as:

```yaml
families:
  - family: visual
    commands:
      - command: /visual status
        summary: ...
        availability: available
        blocked_by: null
```

### `/help <target>`

Include:

```yaml
command_or_family: <resolved target>
syntax: ...
summary: ...
availability: ...
arguments: []
feature_gate: ...
mode: read_only|mutating|external_side_effect
prerequisites: []
human_gates: []
side_effects: []
help_sources: []
```

For article/social creation and visual commands, detailed help must be able to surface:

- source preference, missing-source behavior, fidelity/treatment;
- selected cloud provider/chat intake behavior;
- exact-source `use_as_is` review versus generated/transformed A/B/C review;
- independent article/social logo application (`always|auto|never`);
- official logo asset availability/variants and `awaiting_brand_asset` when relevant;
- rich visual-guidelines authority and user-directive precedence;
- the fact that source/logo media never constitutes publication authorization.

### `/status` and `/visual status`

At minimum the visual portion must be representable as:

```yaml
project: <identity when configured>
feature_gates: {}
visual_preferences:
  configured: true|false
  default: <effective durable default or compatibility summary|null>
  article: <partial override|null>
  social: <partial override|null>
visual_identity:
  configured: true|false
  guidelines_path: <path|null>
  logo_policy:
    article: always|auto|never|null
    social: always|auto|never|null
  logo_assets:
    primary: <non-secret provider-qualified summary|null>
    light: <non-secret provider-qualified summary|null>
    dark: <non-secret provider-qualified summary|null>
  compatibility_behavior: <legacy no-logo summary|null>
visual_source_blockers:
  - content: <identity>
    state: awaiting_user_images
    source_path: <persisted exact path|null>
    source_link: <persisted verified direct link|null>
visual_brand_blockers:
  - content: <identity>
    state: awaiting_brand_asset
    content_kind: article|social
    logo_application: always
active_or_resumable_work: []
awaiting_human: []
blocked: []
```

`/status` and `/visual status` remain read-only. They may display only already persisted source/brand path/link/provider metadata; they must not create folders, ingest files, generate imagery, alter `visual_preferences`/`visual_identity`, or synthesize logo assets while rendering status.

No status field may be inferred solely from conversation memory when durable state is available. A legacy compatibility fallback must be labeled as compatibility behavior, not as a confirmed user preference.

### `/visual configure`

Mutating result must be able to report:

```yaml
visual_preferences_configured: true|false
visual_identity_configured: true|false
article_logo_policy: always|auto|never|null
social_logo_policy: always|auto|never|null
guidelines_path: <path|null>
logo_variants: [primary|light|dark]
blockers: []
next_actions: []
```

Article and social logo preferences must be resolved separately. One may be `never` while the other is `always`.

### `/visual logo` and `/logo`

Mutating/inspection result must be able to report:

```yaml
article_logo_policy: always|auto|never|null
social_logo_policy: always|auto|never|null
logo_assets:
  primary: <verified non-secret asset summary|null>
  light: <verified non-secret asset summary|null>
  dark: <verified non-secret asset summary|null>
brand_workspace: <persisted provider reference|null>
blockers: []
```

A policy update for only article must preserve social exactly; an update for only social must preserve article exactly.

An asset may be reported configured only after real provider-backed verification according to `brand-assets-contract.md`.

### `/visual guidelines`

Result must be able to distinguish read-only inspection from actual durable mutation and report:

```yaml
guidelines_path: strategy/visual-guidelines.md|null
scopes_changed: [global|article|social]
directives_summary: []
content_local_routed: true|false
```

A directive explicitly limited to one article/post/image must route to the owning content workflow instead of mutating the durable project guideline file.

### `/article list`

Each row must be representable as:

```yaml
identity:
  path: articles/<target>/<file>.md
  slug: <slug when known>
  title: <title when known>
target: <target when known>
display_state: <synthetic state>
wordpress_state: <state|null>
publication:
  verified: true|false
  url: <verified production URL|null>
evidence_notes: []
next_gate: <string|null>
```

### `/article details <article>`

Return the same identity/state fields plus:

```yaml
seo_metadata: {}
workflow_evidence: []
media_state: <state|null>
visual_source: <durable source/provenance/blocker summary|null>
visual_contract: <effective/historical user-directive + article-logo summary|null>
markdown_content: <complete current source text>
```

### `/social list`

Each row must be representable as:

```yaml
series_concept: <stable key>
post_id: <immutable ID|null>
source_article: <path>
concept: <title/angle>
state: <canonical/synthetic state>
materialized: true|false
platforms: {}
evidence_notes: []
```

### `/social details <post-or-concept>`

Return list-row identity plus, when materialized:

```yaml
post_path: <path>
master_text: <complete current text>
visual_source: <durable user/generated source provenance and treatment summary|null>
visual_contract: <effective/historical user-directive + social-logo summary|null>
visual: <final durable visual metadata|null>
alt_text: <text|null>
platforms: {}
```

For an unmaterialized concept, `master_text` must be absent/null and no copy may be invented.

## Read-only guarantee

Commands/catalogue entries marked `mode: read_only` must not invoke any tool/action that can mutate:

- GitHub repository state;
- cloud-provider assets;
- WordPress;
- social platforms;
- durable workflow state.

If stale state is discovered, return the mismatch and a possible next action. Repair requires a separately invoked mutating capability.

This includes visual/brand state: `/status`, `/visual status`, `/article list/details` and `/social list/details` may report persisted source/logo/directive metadata/blockers but must not create source/brand folders, copy chat uploads, alter source roles, change visual preferences/logo policy or replace assets.

## Help generation

`/help` and `/help <target>` must be generated from:

1. `user-command-catalog.yaml`;
2. current durable feature/configuration state;
3. referenced capability/help contracts.

The implementation must not keep a second hard-coded command list in `SKILL.md` or runtime code. `SKILL.md` may explain how to load/use the catalogue but must not become a divergent catalogue authority.

## Catalogue validation at skill build/test time

Before a distributable skill is considered valid:

- validate `user-command-catalog.yaml` against `user-command-catalog.schema.json`;
- every public capability reference must resolve to an existing packaged capability contract;
- every `help_source` must resolve;
- each public command ID/syntax must be unique;
- every `internal_only_capability` must resolve to an existing packaged capability contract and must not also be directly dispatchable unless explicitly reclassified;
- `visual-source-resolve` remains internal-only; public durable visual configuration uses `visual-configure`;
- feature gates must refer to documented configuration keys;
- read-only commands must declare `mode: read_only` and `side_effects: none`;
- external-side-effect commands must point to capability contracts with explicit human authorization gates.

## Productization mapping

When the future clean skill package is created, package locations may change, but these semantic assets must be carried over:

```text
SKILL.md
command catalogue
catalogue schema
runtime contract
capability contracts
visual-generation contract
brand-assets contract
user-provided image/source policy contract
state-derivation contract
tests/fixtures for command dispatch and inspection
```

`SKILL.md` should load the command catalogue/runtime contract progressively when explicit command discovery or execution is needed rather than duplicating their full contents.
