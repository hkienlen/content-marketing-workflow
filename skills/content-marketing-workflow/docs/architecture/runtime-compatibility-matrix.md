# Runtime compatibility and prerequisite matrix

Date: 2026-09-05
Status: current architecture authority

## Purpose

This document is the central authority for runtime prerequisite discovery, integration eligibility, degraded-mode behavior and feature availability across Content Marketing Workflow (CMW).

Capability contracts may add task-specific gates, but they must not independently redefine the global missing-prerequisite behavior declared here.

## Runtime states

CMW uses three top-level readiness states:

```text
READY
DEGRADED
BLOCKED
```

- `READY`: every prerequisite required by the currently enabled/requested scope is operational.
- `DEGRADED`: core repository-backed work can continue, but one or more feature families are unavailable.
- `BLOCKED`: a hard prerequisite prevents initialization or safe continuation.

Readiness is computed from actual runtime/provider availability, not from assumptions about subscription names such as Free, Plus, Pro or Enterprise.

## Discovery rule

At `/start`, CMW must discover prerequisites immediately. It must not require a new user to know which plugins/integrations to install first.

For a plugin-backed integration, distinguish at least:

```text
not_visible_or_ineligible
visible_installable_not_installed
installed_not_connected
installed_connected_unverified
operational
```

When the active ChatGPT surface exposes plugin discovery/management, CMW should search the plugin catalogue for each implemented provider even when it is not installed. If a supported provider is installable, propose installation during onboarding. If installed but not connected, guide connection and verification during onboarding.

If runtime tooling cannot inspect plugin eligibility directly, report `eligibility_unknown` rather than guessing from the plan name.

## Prerequisite matrix

### `github_repository`

Severity: **fatal / BLOCKED**.

Required for:

- `/start` initialization/resume;
- durable user/project profile and strategy;
- articles and social text/state;
- media metadata/provenance/hashes;
- approval, scheduling and publication state;
- external-result evidence;
- GitHub Actions automation when enabled.

Missing behavior:

```text
CMW does not initialize or continue as a conversational-only substitute.
```

A usable repository must be accessible or creatable/resolvable through the active GitHub integration. Conversation memory is not a replacement.

### `cloud_media_storage`

Severity: **required for complete media workflow / DEGRADED when unavailable**.

Implemented providers for this version:

```text
google_drive
```

Reserved future adapters:

```text
dropbox
```

Only implemented providers may be proposed as usable choices. WordPress, GitHub and local filesystem are not fallback media providers.

Required for:

- durable user-source originals;
- generated/treated proposal retention;
- selected/final private media binaries;
- `verified_final` provider-backed media;
- temporary `tmp-outbox` delivery copies;
- media-dependent WordPress preparation/publication;
- media-dependent social publication.

When unavailable, CMW may still perform repository-only work that does not require durable media, including strategy, SEO planning, article drafting/review and social text drafting/review.

Strict publication invariant:

```text
no required verified final media
=> no WordPress publication/preparation-for-publication
=> no social publication
```

Do not silently switch to repository-backed binaries, WordPress media storage, local filesystem storage or text-only social publication.

### `image_generation`

Severity: **DEGRADED when unavailable**.

Detect separately when possible:

```text
generation_available
editing_available
direct_asset_output_available
```

When generation/editing required by the effective visual policy is unavailable but cloud storage is operational, use the manual image handoff:

1. produce a complete external-generation prompt;
2. include objective, format/dimensions, style, composition, branding, required/forbidden elements, source role/fidelity/treatment constraints and any text constraints;
3. tell the user to create/improve the image in an image-capable ChatGPT conversation or other compatible image AI;
4. request the resulting image back in the active workflow;
5. inspect it, retain it in the configured cloud provider, normalize/hash/verify it and resume from the exact owning content item.

If image generation is available but cloud media storage is unavailable, generated images may be preview/review artifacts only. They cannot become durable `verified_final` media or unlock publication.

### `wordpress_bridge_runtime`

Severity: **optional for authoring; required for current WordPress/social publication scope**.

This prerequisite means a configured/verified WordPress target hosting a compatible SEO Workflow Bridge runtime, not merely that a website uses WordPress.

Required for:

- WordPress draft preparation;
- WordPress article publication;
- current LinkedIn publication relay;
- current Facebook Page publication relay;
- current provider-side prepublication checks and publication evidence handled by the Bridge.

When unavailable:

- strategy/article/social creation may continue when their own prerequisites are satisfied;
- WordPress preparation/publication is unavailable;
- current automated LinkedIn/Facebook publication is unavailable.

### `github_actions_scheduler`

Severity: **DEGRADED for unattended scheduled-publication scope**.

Required for the current unattended scheduled WordPress/social relay flows that use GitHub Actions.

When unavailable:

- content creation/review remains available;
- schedule state may not be represented as operational unattended automation;
- do not claim scheduled publication is active.

### `linkedin_adapter`

Severity: **optional feature**.

Missing behavior: LinkedIn publication features unavailable only. Do not block Facebook or authoring.

### `facebook_page_adapter`

Severity: **optional feature**.

Missing behavior: Facebook Page publication features unavailable only. Personal/professional-profile publication is not a fallback.

### `telegram_notifications`

Severity: **optional feature**.

Missing behavior: publication notifications unavailable only. Telegram absence/failure must never change authoritative publication state or trigger a duplicate publication.

## Dependency graph

Current publication dependencies:

```text
WordPress publication
  -> github_repository
  -> cloud_media_storage
  -> required verified_final media
  -> wordpress_bridge_runtime

LinkedIn scheduled publication
  -> github_repository
  -> cloud_media_storage
  -> required verified_final media
  -> wordpress_bridge_runtime
  -> linkedin_adapter
  -> github_actions_scheduler

Facebook Page scheduled publication
  -> github_repository
  -> cloud_media_storage
  -> required verified_final media
  -> wordpress_bridge_runtime
  -> facebook_page_adapter
  -> github_actions_scheduler
```

Telegram is downstream/optional and never part of publication success authority.

## Onboarding algorithm

`/start` must:

1. inspect GitHub availability first;
2. block immediately if no usable GitHub repository path exists;
3. enumerate every cloud-media provider implemented by the installed CMW version;
4. discover each implemented provider's plugin visibility/eligibility/installation/connection state when runtime tooling permits;
5. install/connect/verify one supported provider during onboarding when possible;
6. if none is usable, persist/report cloud media as a resumable DEGRADED blocker and list affected features;
7. detect image generation/editing capabilities and establish normal vs manual-handoff visual mode;
8. when WordPress or social publication is enabled, verify WordPress + compatible SEO Workflow Bridge runtime;
9. verify GitHub Actions/scheduler prerequisites for unattended scheduling;
10. verify each enabled social adapter independently;
11. inspect Telegram only as an optional notification feature;
12. compute and persist/report overall readiness plus feature-level availability/blockers.

## Status/help projection

`/status` must show:

- overall `READY|DEGRADED|BLOCKED` state;
- GitHub repository health;
- cloud-media provider choice and discovery/connection/verification state;
- image generation/editing availability and whether manual handoff is active;
- WordPress/Bridge publication-runtime health;
- scheduler health when scheduled publication is enabled;
- social adapter health independently;
- optional Telegram state;
- exact impacted feature list for every unmet prerequisite.

`/help` remains exhaustive. It must keep canonical commands visible, but availability annotations must be derived from this prerequisite graph plus capability-specific gates.

## Persistence

Persist non-secret, future-relevant compatibility facts in user/project data when they affect future independent execution, for example:

- selected cloud-media provider;
- provider workspace references;
- latest verified provider availability state where meaningful;
- WordPress/Bridge runtime identity/verification state;
- enabled social adapter identities;
- scheduler/configuration health metadata;
- explicit runtime limitations that are durable enough to guide resume.

Do not persist raw plugin credentials or subscription assumptions.

Ephemeral surface capabilities such as whether the current conversation exposes image generation should be re-detected when needed and must not be treated as permanently true merely because an earlier conversation had them.

## Legacy repository-backed media

Existing `repository_file` media may remain readable only for explicit backward compatibility/migration where an owning contract still supports it.

Rules:

- never offer GitHub as a new media-storage provider;
- never automatically fall back from cloud storage to repository binaries;
- never mark cloud-media readiness from legacy repository-backed media;
- migration away from repository-backed media must be explicit and preserve exact hashes/provenance.
