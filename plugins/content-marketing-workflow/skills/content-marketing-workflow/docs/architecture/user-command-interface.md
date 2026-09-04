# User command interface for the future Content / Marketing skill

Date: 2026-09-04
Status: architecture contract

## Purpose

The future single installable Content / Marketing skill supports both:

1. natural-language invocation routed to the appropriate internal capability;
2. an explicit `/...` user-command interface for discoverability and deterministic invocation.

The command interface is a user-facing router above capabilities. It is not a second execution engine and must never duplicate or weaken business-workflow contracts.

## Authoritative command documents

Implementation must read these documents together:

```text
docs/architecture/user-command-interface.md
docs/architecture/user-command-catalog.yaml
docs/architecture/user-command-catalog.schema.json
docs/architecture/user-command-runtime-contract.md
docs/architecture/user-command-system-behaviors.md
docs/architecture/user-command-productization-checklist.md
docs/architecture/content-inspection-state-model.md
docs/architecture/user-provided-images.md
docs/architecture/social-creation-queue.md
docs/architecture/social-series-review-gate.md
```

Capability-specific business rules remain authoritative in `docs/architecture/capabilities/`.

## Terminology

### Capability

An internal business/workflow unit such as:

- `seo-create-article`;
- `article-inspect`;
- `visual-source-resolve`;
- `asset-ingest`;
- `social-extract-posts`;
- `social-create-post`;
- `social-inspect`;
- `social-connection-health`;
- `wordpress-prepare-article`.

Capabilities own prerequisites, reads/writes, persistence, human gates, validation and completion conditions.

`visual-source-resolve` and `asset-ingest` are supporting internal capabilities. They are invoked by higher-level article/social workflows and do not imply separate public slash commands.

### User command

A stable user-facing invocation alias such as:

```text
/help
/article create
/article list
/article details <article>
/social create
/social create free <topic>
/social list
/social details <post-or-concept>
/social health
/wordpress prepare
```

A command resolves syntax/arguments/availability and delegates to the target capability or documented system behavior.

## Required discovery/status commands

The future skill must expose:

```text
/help
/help <command-or-family>
/status
```

`/help` and detailed help are generated from the catalogue + current durable feature gates + referenced contracts. They must not use a second hard-coded command list.

`/status` is strictly read-only and summarizes durable project/gate/workflow state. It includes configured `visual_preferences` and already-persisted visual-source blockers such as `awaiting_user_images` when resolvable. It may show an existing exact `source-user/` path/link but must not create the folder or mutate source state merely to render status.

When social is enabled `/status` also surfaces current social connection-health warnings from user/project data; it does not itself run a provider mutation or replace `/social health`.

## Canonical command surface

```text
/help
/help <command-or-family>
/status
/start
/strategy update
/article list
/article details <article>
/article plan
/article create
/article update
/social list
/social details <post-or-concept>
/social create
/social create free <topic>
/social plan
/social visual
/social check
/social health
/social schedule
/social publish
/wordpress connect
/wordpress prepare
/wordpress publish
```

There is intentionally no separate `/visual source` command in the current product surface. Durable visual defaults are changed through `/start`, `/strategy update` or equivalent natural language; one-off source/treatment instructions remain local to the owning content workflow.

The catalogue is the canonical machine-readable source for IDs, syntax, arguments, operation, availability, feature gates, execution mode, side effects, response contract and help source.

## Routing map

| User command | Internal capability / behavior |
|---|---|
| `/help` | `command-help` behavior |
| `/help <command-or-family>` | `command-help-detail` behavior |
| `/status` | `project-status` behavior |
| `/start` | `start` |
| `/strategy update` | `strategy-update` |
| `/article list` | `article-inspect` (`list`) |
| `/article details <article>` | `article-inspect` (`details`) |
| `/article plan` | `seo-plan-article` |
| `/article create` | `seo-create-article` |
| `/article update` | `seo-update-article` |
| `/social list` | `social-inspect` (`list`) |
| `/social details <post-or-concept>` | `social-inspect` (`details`) |
| `/social create` | `social-create-post` (`next`) |
| `/social create free <topic>` | `social-create-post` (`free`) |
| `/social plan` | `social-extract-posts` |
| `/social visual` | `social-create-visual` |
| `/social check` | `social-check-before-publish` |
| `/social health` | `social-connection-health` |
| `/social schedule` | `social-schedule` |
| `/social publish` | `social-publish` |
| `/wordpress connect` | `wordpress-connect` |
| `/wordpress prepare` | `wordpress-prepare-article` |
| `/wordpress publish` | `wordpress-publish-article` |

Supporting capabilities `visual-source-resolve` and `asset-ingest` remain internal-only and need no public command.

## Visual-source routing invariant

For content-producing commands, command routing and visual-source resolution are separate layers:

```text
/article create or /social create
-> owning creation capability
-> resolve effective visual policy
-> visual-source-resolve when applicable
-> source_ready | ai_generation_allowed | continue_without_visuals | awaiting_user_images
-> drafting only when the returned state allows it
```

The effective policy inherits:

```text
project default
-> article/social override
-> per-content local override
```

When the policy requires/preferentially requests real user media and missing behavior is `ask_before_drafting`, the owning workflow must collect/locate, verify and inspect the actual image before drafting. A direct chat upload and the configured Google Drive `source-user/` folder are both valid intake paths.

When asking for Google Drive placement, the response must contain both the exact human-readable canonical `source-user/` path and the verified direct clickable Drive folder link resolved from provider identity.

Source media, source inspection, visual selection, scheduling and publication authorization remain separate states. Supplying/selecting an image never authorizes publication.

## Article creation remains article-only

`/article create` creates an SEO article through `seo-create-article`.

It must never select or create a social post. Article and social creation remain separate command families so the skill cannot silently confuse an SEO article with a platform post.

If `seo-create-article` resolves `awaiting_user_images`, `/article create` is blocked before drafting and returns the exact source intake next action rather than silently switching to synthetic imagery when the active policy forbids that fallback.

## Social creation commands

### `/social create`

This is the normal queue-driven social production entrypoint.

It must inspect durable repository state and create/resume the next not-yet-written post without asking the user to identify a concept that is already queued.

For an existing unchanged human-validated series:

```text
existing durable validated series queue
-> resume earliest started/incomplete eligible post, if any
-> otherwise first eligible not-yet-written concept in persisted series order
-> resolve effective visual source policy/intake before drafting when applicable
-> draft + persist + visual workflow
```

When no current series contains an eligible not-yet-written concept:

```text
select next eligible validated article deterministically
-> inventory/deduplicate social opportunities automatically
-> persist complete series-plan.md automatically
-> present complete persisted list to human
-> human validates/corrects list
-> persist revised exact list + validation evidence
-> select first eligible concept
-> accept it for production
-> allocate immutable post_id
-> resolve effective visual source policy/intake when applicable
-> start drafting immediately when the source gate allows, without another generic go
```

The exact next-concept/next-article ordering and rollover rules are authoritative in:

```text
docs/architecture/social-creation-queue.md
docs/architecture/social-series-review-gate.md
docs/architecture/capabilities/social-create-post.md
```

The complete human review of a newly generated or materially revised article-derived series is mandatory before its first new post is drafted.

The list itself is generated and persisted automatically before that human gate. Once the user validates/corrects the list, that validation authorizes immediate continuation to the first eligible post, but it does not bypass a required visual-source intake gate. Do not ask for another generic `go` after source readiness is satisfied.

An unchanged series already durably human-validated is not re-presented before every subsequent post.

### `/social create free <topic>`

Creates a deliberately standalone social post, not derived from an article or `series-plan.md`.

It still must:

- deduplicate against current social inventory;
- allocate a normal immutable ID;
- persist a normal per-post checklist;
- resolve effective visual-source preference and any required user-image intake before drafting;
- follow the normal writing/visual/Drive/review gates;
- preserve explicit standalone provenance (`source_type: free`);
- never invent an article relationship.

The whole-series validation gate does not apply because no article-derived series exists.

If the requested topic materially duplicates an already queued article-derived concept, the skill surfaces that overlap and defaults to the existing durable concept unless the user explicitly asks for a separate treatment.

### `/social plan`

`/social plan` remains the explicit planning/replanning command. It can inventory, derive, persist, present and revise an article's social series without requiring immediate creation of a post.

When it produces a new/materially revised plan, the complete list must be human-validated before production from that revision. If the user validates it during `/social plan`, the durable validation evidence is reused by a later `/social create`.

It is not the normal command for “write the next post”; that is `/social create`.

### `/social visual`

`/social visual` invokes `social-create-visual` for an already-resolved post/content workflow. It must respect the effective source role/fidelity/treatment rather than assume full AI generation.

Review shape depends on the visual workflow:

```text
generated or materially transformed -> A/B/C proposals
exact use_as_is with no material treatment -> exact source review, no fake synthetic variants
```

Strict/high source fidelity must not be weakened merely because `/social visual` was invoked explicitly.

## Read-only article commands

### `/article list`

Lists known materialized articles and, when exact durable planning relationships exist, planned articles not yet materialized. Shows concise derived editorial/WordPress/verified publication state.

### `/article details <article>`

Accepted exact identity forms include an exact slug, exact filename or exact repository path.

Resolution is deterministic and fails closed on ambiguity. A materialized article returns durable metadata/evidence plus the complete current Markdown source. When present, durable visual source/provenance/blocker state may be shown read-only.

## Read-only social commands

### `/social list`

Shows the unified social editorial inventory, including concepts present only in `series-plan.md`, materialized posts, source provenance, IDs and platform state.

### `/social details <post-or-concept>`

Resolves exact immutable `post_id`, exact `series_concept` or exact post path. For an unmaterialized concept, it returns only persisted plan information and never fabricates post copy. For materialized content, existing visual source provenance/treatment/final-asset state may be shown read-only.

### `/social health`

Shows the current read-only health state of configured social connections from the active user/project profile and, when invoked interactively with a compatible Bridge, may refresh that state through the bounded read-only provider probes defined by `social-connection-health`.

It reports at least:

- live credential validity when known;
- effective known expiry/data-access-expiry;
- J-30/J-14/J-7/expired-or-invalid state;
- scheduled posts whose planned time is at or beyond credential validity;
- the next renewal action when required.

It never returns a raw token and never publishes.

All list/details/health commands are read-only from the user's business/content point of view. Detected mismatches are reported, not silently repaired. The automated daily health workflow may persist only the narrow non-secret operational fields authorized by `docs/architecture/skill-package-boundary.md`.

## Natural language remains first-class

Users never need slash commands. Natural-language requests must route to the same contracts when intent is equivalent.

Examples:

```text
Écris le prochain post
```

routes to `/social create`, while:

```text
Vérifie si mes connexions sociales seront encore valides pour mes prochaines publications
```

routes to `/social health`.

Likewise `Écris un nouvel article sur ...` routes to `/article create`, not to social creation.

Durable visual preference requests such as:

```text
À partir de maintenant, privilégie mes propres photos pour les articles.
```

route to `strategy-update`/profile persistence, while a one-off instruction such as:

```text
Pour ce post seulement, utilise cette photo telle quelle.
```

remains a content-local override handled by the owning social workflow. Neither requires a new public command.

## Parsing, arguments and errors

All implementation details are authoritative in `user-command-runtime-contract.md`.

Key invariants:

- family/subcommand tokens are matched case-insensitively;
- argument text/path/IDs are preserved;
- exact command matching is fail-closed;
- missing/extra arguments produce normalized errors;
- unknown explicit commands never fall through to mutating siblings;
- entity resolution happens inside the target capability, not the parser;
- ambiguity returns candidates rather than a guess.

For overlapping syntaxes, the parser must prefer the longest exact command prefix.

## Machine-readable catalogue

`user-command-catalog.yaml` is schema version 2 and must validate against `user-command-catalog.schema.json`.

Build/test validation must check catalogue schema, unique IDs/syntax, references, help sources, feature gates, execution modes and internal-only classifications.

`visual-source-resolve` must remain classified as internal-only while it has no public slash command.

## Safety and approval invariants

A slash command never bypasses capability gates.

In particular:

- `/article create`, `/social create` and `/social create free` cannot bypass a required `awaiting_user_images` source gate;
- source media cannot be treated as publication authorization;
- strict/high real-subject fidelity cannot silently fall back to a synthetic replacement;
- `/social visual` cannot force fake A/B/C alternatives for an exact `use_as_is` source;
- `/social create` cannot bypass mandatory whole-series validation for a new/materially revised article-derived series;
- `/social create` and `/social create free` do not authorize scheduling or publication;
- `/social health` never publishes and never exposes raw credentials;
- `/social publish` does not override exact social publication authorization requirements;
- `/wordpress publish` does not override `wordpress.publish_enabled` or exact runtime authorization;
- `/article list/details` and `/social list/details/health` cannot approve, allocate, prepare, schedule or publish;
- `/help` and `/status` are read-only;
- parser/dispatch failures fail closed before a side effect.

## Productization requirement

The future clean distributable skill must carry forward the current authoritative command assets, not reconstruct them from conversation memory.

Its `SKILL.md` must load/validate the packaged command catalogue and route to packaged capability contracts without duplicating the whole catalogue as handwritten prose.

The package boundary must also ensure the command/help layer contains no pilot user identity, concrete visual preference, source-user media/provenance or other user data.

## Evolution

Any new public command requires synchronized updates to the catalogue, relevant help/capability contracts, schema if needed, package-boundary tests and productization tests.

Changes to internal source orchestration such as `visual-source-resolve` require synchronized capability/index/runtime/help/testing updates even when the public command surface remains unchanged.
