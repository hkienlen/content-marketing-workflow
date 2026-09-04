# User command system behaviors

Date: 2026-09-04
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

## `/help`

`/help` is generated from the authoritative command catalogue plus current feature gates.

It should show:

- available commands;
- disabled/optional commands with useful explanation when relevant;
- concise descriptions;
- no invented command that lacks a catalogue/capability/behavior authority.

Detailed help follows each catalogue entry's `help_source` and current capability contract rather than conversation memory.

## `/help <command-or-family>`

Detailed help reports at least:

- canonical syntax;
- natural-language equivalents where useful;
- availability/feature gate;
- whether command is read-only, mutating or external-side-effecting;
- business/content approval gates;
- what durable state it may change;
- external side effects;
- important prerequisites/blockers;
- relevant next actions.

For visual-source-sensitive article/social creation help, it must explain that:

- active `visual_preferences` are resolved before drafting;
- user-provided images may be requested/located/verified/inspected before drafting under `user_images_first`, `strict_user_images` or applicable `hybrid_best_fit` behavior;
- when Drive placement is required, user gets exact `source-user/` path + direct verified Drive folder link;
- a content-local override changes only that article/post unless user explicitly updates durable strategy/preferences;
- exact `use_as_is` imagery is not forced into synthetic A/B/C variants;
- image/source intake or selection never authorizes publication.

## `/status`

`/status` is a read-only projection of durable current project/workflow state.

It may report:

- active profile/project/site/repository;
- configured media provider/workspace health;
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

`/status` must not:

- alter `visual_preferences`;
- create source-user folders merely to inspect status;
- upload/generate/treat images;
- schedule/publish;
- renew credentials;
- repair state silently through a write.

If a durable change is requested after status, route to proper mutating capability.

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

## Feature gates

Help/status use durable profile feature gates, including:

```text
wordpress.enabled
wordpress.publish_enabled
social.enabled
```

A feature gate means availability, not task-specific authorization.

## Secret boundary

Never expose raw credentials/tokens in help/status.

Safe outputs include non-secret connection IDs/names, platform target identity, scopes, expiry metadata, health state, Drive folder IDs/links, visual policy enums, source filenames/asset IDs/hashes when useful and not private-secret material.

## Source of truth

Read current repository/profile/content/external verified state as declared by owning contracts. Do not infer state from conversation memory when durable state disagrees or is missing.

## Failure behavior

If status cannot resolve exact active project/profile, report precise read-only blocker. Do not mutate to fix it.

If an active content item says `awaiting_user_images` but source folder is inaccessible, report discrepancy; do not silently switch to AI generation.
