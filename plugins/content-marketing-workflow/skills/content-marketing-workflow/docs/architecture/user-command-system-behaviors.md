# User command system behaviors

Date: 2026-09-05
Status: architecture contract

## Purpose

This contract defines built-in read-only behaviors used by:

```text
/help
/help <command-or-family>
/status
```

These are product-level behaviors, not separate installable capabilities.

They never mutate project/content state, never publish and never use read-only inspection as implicit authorization for a later mutation.

Runtime availability annotations are governed centrally by:

```text
docs/architecture/runtime-compatibility-matrix.md
```

## `/help`

`/help` is generated from the authoritative command catalogue plus current feature gates and runtime prerequisite state.

It is an exhaustive catalogue view, not a shortlist of "main commands".

Before answering `/help`, the skill MUST read the packaged current `docs/architecture/user-command-catalog.yaml` and `docs/architecture/runtime-compatibility-matrix.md`, then:

- enumerate every public command entry from that catalogue exactly once;
- preserve each canonical `command:` syntax exactly, including required placeholders such as `<topic>`;
- group commands by their declared `family`;
- show concise summaries from the catalogue;
- annotate current availability/feature-gate/prerequisite state after the complete catalogue has been loaded;
- keep disabled/optional/degraded commands visible with a useful explanation rather than silently omitting them;
- distinguish `available`, `degraded`, `blocked by prerequisite`, and `not configured` when the runtime/project state supports that distinction;
- never infer plugin eligibility from a subscription label when runtime discovery is available;
- never invent, rename, abbreviate or synthesize a command that lacks a catalogue authority;
- never substitute a capability name such as `check-before-publish` for the canonical public command that routes to it.

The help header should identify the loaded Content Marketing Workflow version/distribution when that metadata is available without guessing, for example:

```text
Content Marketing Workflow 0.x.y
Distribution: ChatGPT Skill
Compatibility: READY | DEGRADED | BLOCKED
```

Detailed help follows each catalogue entry's `help_source`, current capability contract and compatibility matrix rather than conversation memory.

## `/help <command-or-family>`

Detailed help reports at least:

- canonical syntax;
- natural-language equivalents where useful;
- availability/feature gate;
- current prerequisite status for the active runtime/project;
- whether command is read-only, mutating or external-side-effecting;
- business/content approval gates;
- what durable state it may change;
- external side effects;
- important prerequisites/blockers;
- supported degraded/manual fallback when one exists;
- relevant next actions.

For visual-source-sensitive article/social creation help, it must explain that:

- active `visual_preferences` are resolved before drafting;
- user-provided images may be requested/located/verified/inspected before drafting under `user_images_first`, `strict_user_images` or applicable `hybrid_best_fit` behavior;
- when cloud-provider placement is required, user gets exact `source-user/` path + direct verified provider folder link;
- Google Drive is the current implemented cloud-media provider; future providers are not offered until their adapter is implemented;
- if image generation/editing is unavailable in the current runtime, CMW can produce a complete external-generation prompt and resume after the user returns the generated image, provided cloud-media storage is operational;
- if cloud-media storage is unavailable, images cannot become durable `verified_final` media and media-dependent publication stays unavailable;
- a content-local override changes only that article/post unless user explicitly updates durable strategy/preferences;
- exact `use_as_is` imagery is not forced into synthetic A/B/C variants;
- image/source intake or selection never authorizes publication.

For WordPress/social publication help, state the strict current invariant:

```text
no required verified_final image -> no WordPress publication/preparation-for-publication and no social publication
```

Also state that current LinkedIn/Facebook automated publication depends on a verified WordPress-hosted SEO Workflow Bridge runtime.

For Telegram help, `/help` must expose both the configuration command and the explicit test command when the social feature is available:

```text
/social notifications telegram
/social notifications telegram test
```

The test command is an external notification side effect only: it sends one diagnostic message to the already configured Telegram destination and does not publish or retry any social content.

## `/status`

`/status` is a read-only projection of durable current project/workflow state plus current runtime prerequisite availability where it can be inspected without mutation.

It must begin with a compatibility summary derived from `runtime-compatibility-matrix.md`:

```text
Compatibility: READY | DEGRADED | BLOCKED
```

Then report, when resolvable:

- GitHub repository prerequisite health;
- configured cloud-media provider and workspace health;
- provider plugin state: not visible/ineligible, installable-not-installed, installed-not-connected, connected-unverified, operational, or eligibility unknown;
- image generation/editing availability in the current runtime and whether manual external-generation handoff is active;
- WordPress/SEO Workflow Bridge runtime health;
- GitHub Actions/scheduler readiness when unattended scheduling is enabled;
- LinkedIn and Facebook adapter health independently;
- exact unavailable/degraded feature list caused by each unmet prerequisite;
- active profile/project/site/repository;
- current **`visual_preferences`** summary:
  - project default source mode;
  - article override when present;
  - social override when present;
  - fidelity/treatment/missing-source behavior;
  - whether preferences are explicitly configured or only legacy compatibility is active;
- current content-local visual blockers such as `awaiting_user_images` when a specific active workflow is resolvable;
- WordPress enablement/connection/publication-capability state;
- social enablement/connections/credential health;
- optional notification state;
- current article/social workflow counts or blockers when recoverable from durable state;
- pending review/scheduling/publication-verification state where useful.

### Compatibility projection examples

Cloud storage unavailable:

```text
Stockage média cloud : indisponible
État : DEGRADED
Impact :
- images générées/non générées impossibles à finaliser durablement
- pas de préparation/publication WordPress nécessitant les médias
- pas de publication sociale
```

WordPress/Bridge unavailable while social is enabled:

```text
Runtime WordPress / SEO Workflow Bridge : indisponible
Impact :
- publication WordPress indisponible
- publication LinkedIn/Facebook automatisée indisponible
- création/révision des contenus GitHub reste disponible
```

Image generation unavailable with cloud storage operational:

```text
Génération d'images : indisponible dans ce runtime
Mode : DEGRADED / handoff manuel
CMW fournira le prompt complet et reprendra après téléversement de l'image créée ailleurs.
```

### Telegram status projection

When `notifications.telegram` exists in the active profile, `/status` must include a non-secret Telegram section.

When notifications are enabled, include at least:

```text
Telegram notifications: enabled
- setup: verified | not_configured | inconsistent
- bot: <persisted bot_username or unknown>
- destination: configured | missing
- secret reference: configured | unknown
- last verified: <persisted timestamp or unknown>
- reports: success=<on/off>, failure=<on/off>, uncertain=<on/off>
```

Never expose the bot token or attempt to read/print secret values.

Status must distinguish profile evidence from live verification. A persisted `setup_status=verified` does not prove that the GitHub secret still exists or that Telegram is currently reachable. If live health has not been tested, say `not tested in this status check` or equivalent rather than claiming connectivity.

When Telegram notifications are enabled and a verified destination is present, `/status` should offer this explicit next action:

```text
/social notifications telegram test
```

When configuration is incomplete or inconsistent, point to:

```text
/social notifications telegram
```

`/status` must never send the test message automatically because `/status` is read-only.

`/status` must not:

- install/connect plugins;
- alter `visual_preferences`;
- create source-user folders merely to inspect status;
- upload/generate/treat images;
- schedule/publish;
- renew credentials;
- send Telegram messages;
- repair state silently through a write.

If a durable change, provider installation/connection or diagnostic send is requested after status, route to the proper onboarding/mutating/external-side-effect capability.

## Changing visual preferences

`/status` is read-only. Durable visual preference changes route to:

```text
/strategy update <request>
```

or an equivalent natural-language request, which uses `strategy-update`/profile persistence rules.

Examples:

```text
"À partir de maintenant, privilégie mes propres photos pour les articles."
"Pour les réseaux sociaux seulement, tu peux améliorer mes photos naturellement."
"Je veux une fidélité stricte pour les photos de mes produits."
```

A one-off instruction such as `pour ce post seulement, génère l'image avec l'IA` is not a durable strategy update; it is persisted as content-local override by the owning workflow.

## Visual status projection

Prefer a concise human-readable summary, for example:

```text
Images : préférence configurée
- défaut projet : user_images_first
- articles : hérite du défaut
- social : hybrid_best_fit
- fidélité : high
- traitement : natural_enhancement
- image manquante : ask_before_drafting
```

When older profile lacks explicit visual preference:

```text
Images : préférence non encore configurée explicitement
- compatibilité actuelle : AI-first
- prochaine action possible : /start ou /strategy update
```

Do not call compatibility fallback a confirmed user preference.

When an active item is blocked:

```text
Visuel du contenu actif : awaiting_user_images
```

Status may show the already persisted exact source folder/path/link if it exists, but must not guess or create one during this read-only command.

## Feature gates and prerequisites

Help/status combine durable profile feature gates such as:

```text
wordpress.enabled
wordpress.publish_enabled
social.enabled
```

with the runtime prerequisite graph from `runtime-compatibility-matrix.md`.

A feature gate means configured availability, not task-specific authorization. A satisfied feature gate does not override a missing prerequisite, and a satisfied prerequisite does not authorize a publication.

## Secret boundary

Never expose raw credentials/tokens in help/status.

Safe outputs include non-secret connection IDs/names, platform target identity, scopes, expiry metadata, health state, Drive folder IDs/links, Telegram bot username/chat-routing presence/verification timestamps, visual policy enums, source filenames/asset IDs/hashes when useful and not private-secret material.

## Source of truth

Read current repository/profile/content/external verified state as declared by owning contracts. Do not infer state from conversation memory when durable state disagrees or is missing.

For ephemeral runtime abilities such as image generation or plugin discovery support, inspect the active runtime when possible and report unknown when it cannot be determined.

## Failure behavior

If status cannot resolve exact active project/profile, report precise read-only blocker. Do not mutate to fix it.

If GitHub repository access is unavailable, report `BLOCKED`; do not imply that CMW can safely continue from chat memory alone.

If an active content item says `awaiting_user_images` but source folder is inaccessible, report discrepancy; do not silently switch to AI generation.

If Telegram is enabled but its durable configuration is incomplete or contradictory, report that inconsistency and route the user to `/social notifications telegram`; do not claim the notification channel is healthy.
