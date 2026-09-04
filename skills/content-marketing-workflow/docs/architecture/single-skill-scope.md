# Single installable Content / Marketing skill - scope

Date: 2026-09-04
Status: architecture decision

## Decision

The product is distributed as the **Content Marketing Workflow plugin containing one primary installable skill**. This canonical repository contains only generic product source; user/project state and real pilot validation live outside the distributable source.

The skill orchestrates multiple internal capabilities while presenting one coherent user experience through natural language and the explicit command interface.

Concrete user/site/repository/account IDs, preferences, schedules, provider application IDs and credential-lifecycle dates are user/project data loaded from the active profile. They are never generic skill constants.

## Core scope

Core supports:

- resumable onboarding and durable user/project configuration;
- durable strategy persistence;
- SEO article planning, creation, update and inspection;
- current research when needed;
- grouped article + visual production/review;
- project-level visual-source preferences with article/social and per-content overrides;
- real user-provided image intake from chat/Google Drive before drafting when the effective policy requires it;
- source-image provenance, fidelity/treatment controls and non-overwrite guarantees;
- provider-backed asset handling;
- GitHub traceability;
- `/help`, `/status` and validated command/runtime contracts.

`/article create` remains exclusively SEO article creation.

The normative user-provided image behavior is defined in:

```text
docs/architecture/user-provided-images.md
docs/architecture/capabilities/visual-source-resolve.md
```

## Business-model extensibility

The generic product remains profession-neutral and composable. It must support services without structurally preventing ecommerce, physical/digital products, SaaS, licences, subscriptions, support or mixed models.

User-provided image handling must remain generic enough for product photos, craft/portfolio work, photographer images, places, portraits and other real-world subjects without encoding one pilot profession.

## User-profile boundary

The skill owns:

```text
schemas
capability contracts
generic runtime code
generic warning thresholds/state machines
visual policy enum/inheritance behavior
provider-specific procedures expressed with profile lookups/placeholders
```

User/project data owns:

```text
site/repository identity
business/editorial/SEO/social preferences
visual_preferences and project/article/social visual sourcing choices
content-local visual overrides and source provenance
WordPress connections
media workspace IDs
social account IDs/names/URNs
provider application/configuration IDs
preferred publication timezone/hours
publication-consent policies
credential expiry/data-access-expiry metadata
connection-health state
content/publication evidence
notification preferences and non-secret routing metadata
```

Raw credentials remain outside GitHub in their external credential owner.

See:

```text
docs/architecture/user-profile-data-contract.md
docs/architecture/skill-package-boundary.md
```

## Visual-source scope

Durable project visual preference uses the model:

```text
projects.<active_project>.visual_preferences.default
projects.<active_project>.visual_preferences.article
projects.<active_project>.visual_preferences.social
```

Per-content overrides stay with the content/task/post state and never silently rewrite project preferences.

Supported source modes:

```text
ai_first
user_images_first
strict_user_images
hybrid_best_fit
```

Supported missing-source behavior:

```text
ask_before_drafting
allow_ai_generation
continue_without_visuals
```

Supported fidelity:

```text
strict
high
moderate
flexible
```

Supported AI treatment:

```text
none
light_correction
natural_enhancement
marketing_enhancement
creative_transformation
```

The common `visual-source-resolve` capability is invoked before article/social drafting when source policy needs resolution. It may create/reuse private `source-user/` workspace state and verify/inspect real user source images. It never publishes and never substitutes source media for a publication authorization.

A `use_as_is` source with no material treatment is not forced through fake synthetic A/B/C alternatives. Generated/materially transformed workflows retain the normal reviewable-alternative behavior and all final human media gates.

## Optional WordPress scope

```yaml
wordpress:
  enabled: false
  publish_enabled: false
```

Connection/draft preparation and publication remain distinct capabilities. Enabling publication capability never replaces exact runtime publication authorization.

When WordPress support is enabled, `SEO Workflow Bridge` is the canonical mainstream companion plugin. Normal users must not need a server daemon, reverse-proxy route or other server-level component.

The same companion is the mainstream host for supported LinkedIn and Facebook Page connection/publication adapters and read-only social connection-health probes.

## Optional social scope

```yaml
social:
  enabled: false
  publication:
    linkedin:
      enabled: false
    facebook:
      enabled: false
      target_type: facebook_page
```

Social-content functionality and direct social-network publication are separate opt-ins.

During onboarding the user may configure an adapter now or later. `later` is a valid state and must not block content creation, review, Drive finals, scheduling metadata or another independently configured platform.

Later activation resumes the platform's dedicated onboarding from its last verified durable milestone rather than restarting global onboarding.

Current generic onboarding entry points are provider-owned developer portals, with detailed guidance defined in:

```text
docs/architecture/linkedin-publication-onboarding.md
docs/architecture/facebook-page-publication-onboarding.md
```

## Social-content capabilities

When social is enabled, support:

- durable inventory/deduplication;
- article-derived `series-plan.md` creation/replanning;
- strategic classification of retained concepts as `identification`, `expertise`, `positioning` or `conversion`;
- persisted role/purpose for each concept;
- series-level coverage checking;
- a human-reviewable editorial order that normally avoids consecutive strong commercial/CTA posts;
- queue-driven next-post creation through `/social create`;
- deterministic rollover to the next eligible validated article;
- mandatory detailed human review of a new/materially revised series before its first new post;
- automatic continuation to the first eligible post after series validation without another generic `go`;
- standalone/free posts through `/social create free <topic>`;
- immutable post IDs allocated only at durable production start;
- read-only `/social list` and `/social details`;
- visual-source resolution before master-text drafting when effective user-image policy requires/prioritizes it;
- visual creation/review/final asset ingestion;
- global-calendar scheduling balance across series and free posts;
- connection-health inspection through `/social health`;
- publication only through verified platform adapter + exact runtime authorization;
- platform-appropriate post-publication verification and durable verification state;
- optional Telegram publication reports through `/social notifications telegram`;
- durable publication-consent policies that may remove repetitive prompts without weakening exact per-post technical authorization;
- independent platform adapters so adding a network does not redesign the common post/review/scheduling model.

## Social connection health

Credential lifecycle monitoring is part of the product, but concrete expiry dates remain user/project data.

Generic behavior:

```text
read active profile expiry/data-access metadata
+ optionally run bounded read-only Bridge provider probe
+ inspect scheduled post metadata
+ inspect pending exact authorizations
-> healthy / J-30 / J-14 / J-7 / expired-or-invalid
-> identify scheduled posts beyond known validity
-> guide platform-specific renewal
```

The health monitor never returns raw credentials and never publishes.

Bridge `0.10.0+` is the current minimum for live read-only provider health probes.

## Post-publication verification semantics

Scheduler success, provider creation evidence and post-publication verification are separate states.

Current generic provider semantics are:

```text
Facebook
published
-> read-only remote post/media read-back
-> remote_verified when the expected remote object, message and media evidence match

LinkedIn
published
-> definitive HTTP 201 + x-restli-id creation evidence
-> provider_acknowledged when independent member-post read-back is unavailable with the current permission scope
```

A Facebook post that was definitively created but whose remote verification fails must not be blindly republished. Verification/reconciliation failure is handled separately from creation retry safety.

`provider_acknowledged` must never be presented as `remote_verified`.

## Optional publication notifications

Telegram publication reports are optional and user-controlled even when social publication is enabled.

User/project data owns the enablement preference, `chat_id`, bot username, setup state, verification timestamps and report preferences. The raw bot token remains in the runtime credential owner; for the current GitHub Actions adapter the conventional Repository Secret is:

```text
TELEGRAM_BOT_TOKEN
```

Onboarding or a later `/social notifications telegram` request must inspect the current profile first:

```text
verified + enabled
-> reuse current setup

verified + disabled
-> re-enable/reverify when appropriate without recreating the bot

not configured / missing destination
-> guide BotFather + secret storage + chat discovery + verification
```

The setup flow sends one explicit test message before setting the notification channel to verified/enabled.

Publication-report semantics follow the strongest durable publication evidence available:

```text
Facebook success -> published + remote_verified
LinkedIn success -> published + provider_acknowledged
failure/uncertain -> reported only when the corresponding user preference is enabled
```

Telegram delivery failure is independent from social publication state. It must never turn a successful publication into a retryable publication and must never authorize a duplicate social post.

Detailed generic help is authoritative in:

```text
docs/architecture/user-help-telegram-notifications.md
```

## Social publication rollout invariant

The implementation order used during pilot validation does not define permanent network scope.

Current generic adapters are:

```text
LinkedIn -> authenticated member-profile publication
Facebook -> facebook_page publication
other networks -> future adapters after explicit implementation and validation
```

Facebook personal/professional profiles are not automated API targets.

The skill must distinguish:

```text
platform known by content/scheduling model
!=
platform publication adapter enabled/ready
```

Disabled adapters fail closed and do not block another independently enabled platform unless the user explicitly requires an all-platform atomic workflow.

Adding a new network must not require changing:

- immutable `post_id`;
- validated master text;
- grouped text + visual review;
- provider-backed final visual/hash;
- common `planned_at` semantics;
- exact publication authorization record;
- common published-state evidence/idempotency rules.

## Publication-consent policy invariant

Connection readiness, user publication policy and exact runtime authorization are different layers:

```text
adapter connected/verified
!=
publication-consent policy
!=
exact authorized_for_scheduled_publication record
```

A supported platform may use:

```text
one_off_exact_confirmation
standing_auto_publish_scheduled
```

The concrete selected policy belongs to the active user profile.

A standing scheduled policy allows automatic materialization of the exact per-post authorization only after normal content/visual/ALT/schedule approval. It never permits a wildcard Bridge/scheduler request.

Changing a bound value invalidates exact authorization. Immediate `publish_now` remains separate unless a future explicit policy says otherwise.

## Publication onboarding invariant

Each direct-publication adapter is optional and has an enablement preference independent from general social-content support.

Onboarding must represent at least:

```text
not configured
configured now
postponed by user
configuration in progress
connected
live verified
production automation active
```

When later activation occurs:

```text
natural-language request or /social publish
-> identify platform
-> read durable onboarding state
-> resume only missing steps
```

LinkedIn and Facebook Page onboarding remain governed by their dedicated contracts. All provider application/configuration/account IDs are user/project values; raw credentials remain external.

## Series functions and validation

User-facing labels:

```text
Identification
Expertise / compréhension
Méthode / positionnement
Offre / conversion
```

Durable values:

```text
identification
expertise
positioning
conversion
```

The distribution is guidance, not a quota. Never invent commercial claims or an offer merely to fill a function.

Every new/materially revised article-derived series review must show proposed order, concept/title, angle, strategic function, concrete role, state and useful source/offer/link/deduplication notes plus a coverage/order rationale.

A bare list of topics is insufficient.

## Queue invariant

For an already validated series:

```text
/social create
-> resume incomplete post or next eligible concept in validated order
-> resolve visual source policy/intake before drafting when required
-> draft + visual workflow
```

When exhausted:

```text
next eligible validated article
-> inventory/deduplicate/classify/balance
-> persist/re-read complete series
-> detailed human series validation
-> first eligible concept + immutable ID
-> resolve visual source policy/intake when required
-> drafting starts automatically when source gate allows
```

## Scheduling balance invariant

Before fixing a schedule, inspect neighbouring global calendar entries. By default avoid consecutive `conversion`/strong-CTA posts when a reasonable alternative exists. Never silently override an explicitly chosen date; propose an alternative or persist a deliberate exception rationale.

Scheduling metadata and exact runtime authorization remain distinct.

## Free posts

Free posts skip only the article-series gate. They retain global deduplication, immutable ID, optional strategic-function classification, source-policy resolution, post/visual review, scheduling-balance checks and publication gates.

## Internal capability model

Current boundaries include:

```text
start
strategy-update
seo-plan-article
seo-create-article
seo-update-article
article-inspect
visual-source-resolve
asset-ingest
wordpress-connect
wordpress-prepare-article
wordpress-publish-article
social-extract-posts
social-create-post
social-inspect
social-create-visual
social-check-before-publish
social-connection-health
social-schedule
social-publish
social-publication-verification
telegram-publication-notifications
```

They are internal capabilities of one installable skill.

## User-facing command model

Required invariants:

1. natural language routes to the same capabilities as explicit commands;
2. `/help` is generated from the real catalogue + gates;
3. `/status` and list/details/health inspection are read-only from the user's content/publication point of view;
4. `/article create` cannot route to social creation;
5. `/social create` cannot bypass new/materially revised series validation;
6. after exact list validation, first post proceeds without another generic start approval once any required visual-source gate is satisfied;
7. `/social create free <topic>` has parser precedence over `/social create`;
8. `/social health` never exposes credentials or publishes;
9. no command bypasses persistence, validation, scheduling or exact runtime publication gates;
10. `/strategy update` or equivalent natural language may update durable visual preferences; one-off content instructions remain local;
11. `/status` may report `visual_preferences` and `awaiting_user_images` but never mutates them.

## Development repository vs future distribution

Future distribution is created separately with clean history and generic-only contracts/code built from current authoritative state, not conversation memory or an older branch.

The package manifest/CI boundary must exclude user/project content, profile instances and project-specific live-validation evidence.

## Design principles

Keep automatic durable persistence, durable/transient distinction, one authority per rule/data class, progressive context loading, restartable/idempotent workflows, explicit contracts, verification-based completion, safe testing, GitHub durable backend, provider-backed asset identity/hash/provenance and transport-neutral WordPress/social integration.

Do not reintroduce older broad multi-skill architecture or superseded workflow rules.
