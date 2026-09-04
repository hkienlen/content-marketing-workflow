# User command productization checklist

Date: 2026-09-04
Status: implementation acceptance contract

## Purpose

This checklist defines when the distributable single Content / Marketing skill can be considered correctly implemented. It prevents productization from silently dropping or reinterpreting validated command, article, user-image, WordPress, social-publication, verification, connection-health and notification architecture.

## Packaging

- [ ] one installable skill package exists;
- [ ] generation is bound to one exact frozen source commit SHA;
- [ ] `SKILL.md` explains natural-language and explicit `/...` routing without duplicating the catalogue;
- [ ] canonical command catalogue/schema/runtime/system-behavior contracts are packaged;
- [ ] required capability contracts are packaged;
- [ ] user-provided-image contract, `visual-source-resolve` capability and visual policy resolver are packaged;
- [ ] content inspection state model is packaged;
- [ ] social queue/rollover contract is packaged;
- [ ] social whole-series review gate is packaged;
- [ ] publication verification and connection-health contracts are packaged;
- [ ] Telegram notification contract and exact guided user help are packaged;
- [ ] current social-media strategy is loaded/referenced as user/project authority rather than copied as one pilot's generic defaults;
- [ ] feature-gate configuration keys referenced by catalogue entries exist;
- [ ] SEO Workflow Bridge source and required generic relay/scheduler assets are present for enabled companion capabilities;
- [ ] the primary skill payload follows `skill-package-manifest.json`, while the root release follows `plugin-package-manifest.json`; repository-only CI/tests/tools are excluded;
- [ ] generic package authorities required for command/help/state/publication behavior are present and their critical references resolve;
- [ ] `user-data/**`, project strategy/content, live checkpoints, exact publication authorizations and pilot assets are not packaged;
- [ ] no raw credentials or user-specific repository/site/social/workspace IDs are present in the generic package.

## Source/package boundary acceptance

- [ ] `skill-package-manifest.json` exists and every listed include exists;
- [ ] excluded roots cannot be pulled into the package through an include root/file;
- [ ] the generic package does not contain known pilot identity markers;
- [ ] concrete profile instances are excluded while the generic profile schema is packaged;
- [ ] runtime user-owned strategy/content/visual preferences remain external user/project data and are loaded through profile/project state;
- [ ] development-only repository instructions/prompt scaffolding are not accidentally treated as generic payload;
- [ ] package checks run on the integration branch and again on `main` after merge.

## Catalogue / parser / safety baseline

- [ ] catalogue validates against schema;
- [ ] command IDs/syntax are unique and references resolve;
- [ ] every `help_source` resolves to a packaged generic authority;
- [ ] every public capability reference resolves to a packaged capability contract;
- [ ] `/social create free <topic>` wins precedence over `/social create`;
- [ ] `/article create` never routes to social creation;
- [ ] disabled social fails closed before mutation;
- [ ] publication authorization remains separate from all creation/planning/scheduling commands;
- [ ] unknown slash commands never fall through to sibling mutating commands.

## User-provided image acceptance

- [ ] profile schema supports `visual_preferences` with project default plus article/social overrides;
- [ ] source modes include `ai_first`, `user_images_first`, `strict_user_images`, `hybrid_best_fit`;
- [ ] missing-source behavior is modeled independently from source preference;
- [ ] `source_fidelity` and `ai_treatment` are separate axes;
- [ ] per-content local override is supported without mutating durable global preferences;
- [ ] when effective policy requires user media, `visual-source-resolve` runs before article/post drafting;
- [ ] missing required source media can produce durable/resumable `awaiting_user_images` instead of silently generating a synthetic replacement;
- [ ] ChatGPT upload and Google Drive source intake preserve provenance;
- [ ] Google Drive source originals live separately under private `source-user/` and are never overwritten;
- [ ] user placement guidance shows both the exact human-readable source folder path/name and the resolved direct clickable Drive link;
- [ ] source-image roles distinguish at least `use_as_is`, `enhance`, `subject_reference`, `inspiration_reference`, `composition_input`;
- [ ] strict/high-fidelity subjects/products are not silently invented or materially redesigned;
- [ ] `use_as_is` does not force fake A/B/C generation;
- [ ] transformed/generated proposal alternatives remain reviewable and final human selection remains explicit;
- [ ] source provenance is carried into final durable media metadata when applicable;
- [ ] source media never authorizes WordPress/social publication;
- [ ] `/status`, onboarding and durable strategy/settings behavior expose or guide the active visual preference without leaking pilot defaults.

## Detailed help acceptance

`/help`, `/help <command>` and `/status` remain read-only.

### `/help social create`

Must explicitly document:

- [ ] durable queue first / resume before duplicate creation;
- [ ] deterministic rollover to next eligible article;
- [ ] automatic inventory + deduplication + persistence before review;
- [ ] four functions: Identification, Expertise / compréhension, Méthode / positionnement, Offre / conversion;
- [ ] business-visibility coverage test: series must not remain merely educational when truthful durable activity/method/offer material supports the bridge;
- [ ] editorial order deliberately mixes functions;
- [ ] consecutive conversion/strong-CTA posts are avoided by default;
- [ ] validation view shows function + concrete role of every concept and coverage summary;
- [ ] no first drafting before exact new/materially revised series is human-validated;
- [ ] effective visual-source policy is resolved before master text when user-source intake is required;
- [ ] no second generic `go` after series validation;
- [ ] unchanged validated series is not revalidated before every post;
- [ ] scheduling performs a second global-calendar CTA adjacency check;
- [ ] creation never authorizes publication.

### `/help social plan`

- [ ] explains same four functions and coverage test;
- [ ] explains detailed series review projection;
- [ ] explains order/alternation rationale;
- [ ] explains persisted validation revision reused by later `/social create`.

### `/help social schedule`

- [ ] explains global neighbour check across series/free posts;
- [ ] avoids consecutive `conversion` or strong-CTA posts by default;
- [ ] proposes alternative timing rather than silently overriding explicitly chosen time;
- [ ] supports intentional durable exception rationale;
- [ ] clearly states scheduling != publication authorization;
- [ ] clearly states scheduler success != provider publication evidence.

### `/help social create free`

- [ ] explains standalone provenance/deduplication;
- [ ] explains optional `series_function` classification for global balance;
- [ ] explains absence of whole-series gate but retention of post/visual/scheduling/publication gates.

### `/help social health`

- [ ] explains that the capability is read-only and never publishes;
- [ ] reports live credential/identity probe state when available without exposing raw credentials;
- [ ] explains known expiry/data-access horizon and J-30/J-14/J-7 warning semantics;
- [ ] identifies scheduled posts or pending exact authorizations beyond known credential validity;
- [ ] guides user-driven renewal rather than claiming automatic provider credential renewal.

### `/help social notifications telegram`

- [ ] explains Telegram reporting is optional and a user preference;
- [ ] inspects existing profile state before starting configuration;
- [ ] reuses a verified configuration instead of forcing BotFather recreation;
- [ ] guides exact BotFather `/newbot` creation when setup is missing;
- [ ] tells the user to store `TELEGRAM_BOT_TOKEN` as a GitHub Actions Repository Secret and never paste it into chat;
- [ ] guides `/start`/message, `discover`, exact `chat_id` selection and `verify`;
- [ ] states that verification sends one explicit test message before `enabled=true`;
- [ ] covers disable, re-enable, destination change and token rotation/reconfiguration;
- [ ] explains success/failure/uncertain report preferences independently;
- [ ] states Telegram failure never changes publication state or causes republication.

## `/social list/details`

Fixtures must cover proposed/accepted/materialized/orphan/free posts and zero-write behavior.

New function visibility:

- [ ] `series_function` is visible for article-derived concepts/posts when persisted;
- [ ] free posts show strategic function when persisted;
- [ ] unknown legacy function is shown as unknown rather than guessed/mutated;
- [ ] provider publication evidence and verification state are visible when materialized/published;
- [ ] list/details remain read-only.

## `/social create` existing-series acceptance

Given identical durable state, independent runs select same target.

- [ ] partially started post resumes first;
- [ ] next concept follows exact human-validated editorial order;
- [ ] `deferred`/`rejected` never auto-selected;
- [ ] post inherits source provenance + `series_function`;
- [ ] exactly one immutable ID allocated/reused on restart;
- [ ] visual-source intake/resolution happens at the correct pre-draft point when required;
- [ ] visual workflow follows automatically when prerequisites pass;
- [ ] no scheduling/publication implicitly occurs.

## Queue rollover + whole-series review acceptance

When active queue is exhausted:

- [ ] deterministic next article selection works;
- [ ] exact article inventory/deduplication is automatic;
- [ ] every retained concept gets valid function `identification|expertise|positioning|conversion`;
- [ ] each concept persists a concise role/purpose;
- [ ] series coverage test is executed;
- [ ] unsupported commercial claims/offers are never invented merely to fill a function;
- [ ] missing function can be intentional only with explicit truthful rationale;
- [ ] proposed order avoids consecutive conversion/strong CTA posts when reasonably possible;
- [ ] complete `series-plan.md` with functions/order is persisted and re-read before human review;
- [ ] review begins with explanation of four functions;
- [ ] review shows order, concept, angle, function, role, state and useful provenance/note for every item;
- [ ] review shows count/distribution/coverage summary by function;
- [ ] review explicitly tells user order is designed to avoid commercial clustering and can be changed;
- [ ] no ID/first drafting before exact plan human validation;
- [ ] feedback including function/order changes is persisted before validation evidence;
- [ ] validation revision binds to concepts + functions + order;
- [ ] first drafting starts automatically after validation without another generic `go`, except a real `awaiting_user_images` source prerequisite can correctly block drafting;
- [ ] unchanged validated series is not repeatedly re-presented;
- [ ] material function/order changes trigger applicable revalidation.

## Scheduling balance acceptance

With approved posts from same/different series and free posts:

- [ ] scheduling reads neighbouring global calendar entries;
- [ ] `series_function: conversion` adjacency is detected;
- [ ] strong explicit CTA adjacency can also be detected when durably marked/derivable from post state;
- [ ] reasonable alternative slot is proposed when conflict exists;
- [ ] explicitly chosen time is not silently changed;
- [ ] deliberate exception can be persisted with rationale;
- [ ] scheduling still cannot publish;
- [ ] `planned_at` and scheduled state never substitute for exact runtime publication authorization.

## `/social create free` acceptance

- [ ] free topic/intent persisted;
- [ ] global deduplication occurs;
- [ ] immutable ID + standalone provenance used;
- [ ] `series_function` persisted when role is determined;
- [ ] no fake article/series provenance;
- [ ] whole-series gate not required;
- [ ] normal source-resolution/post/visual/scheduling/publication gates remain.

## Publication authorization and scheduler acceptance

- [ ] connection readiness, standing publication-consent policy and exact post authorization remain distinct;
- [ ] standing scheduled policy can remove repetitive prompts only by materializing an exact per-post authorization after all normal gates;
- [ ] changing bound text/image/ALT/author/target/time/hash invalidates the applicable exact authorization;
- [ ] scheduler success means due authorization detection + relay dispatch, not publication proof;
- [ ] relay/provider result must be bound to the current exact authorization before it can reconcile publication state;
- [ ] stale idempotency evidence from an older authorization cannot prove a new publication;
- [ ] uncertain external creation never triggers blind retry.

## Facebook publication verification acceptance

For the current Facebook Page adapter:

- [ ] definitive provider creation evidence persists before remote verification;
- [ ] the remote post/media object is read back through a bounded read-only verification path;
- [ ] expected Page/remote identifiers are checked;
- [ ] expected message hash/text matches when the API exposes it;
- [ ] expected media existence/identity is checked to the supported extent;
- [ ] successful read-back reconciles `status: published` + `verification_state: remote_verified`;
- [ ] a definite creation followed by failed read-back remains a publication-verification/reconciliation problem, not permission to republish;
- [ ] verification never creates or mutates a Facebook post.

## LinkedIn publication evidence acceptance

For the current member-profile adapter:

- [ ] HTTP 201 + `x-restli-id` remains definitive provider creation evidence;
- [ ] successful reconciliation uses `status: published` + `verification_state: provider_acknowledged`;
- [ ] `provider_acknowledged` is never described as independent remote verification;
- [ ] lack of current restricted read permission is surfaced as verification unavailable rather than silently inferred from a public webpage;
- [ ] no new restricted scope is assumed or requested merely to satisfy a generic acceptance label.

## Telegram publication-report acceptance

- [ ] notification setup is optional at onboarding and can be enabled later;
- [ ] profile-first inspection distinguishes active, verified-but-disabled and not-configured states;
- [ ] raw bot token exists only in the configured credential owner and never in profile/Git/SKILL/help/chat;
- [ ] `discover` verifies the bot and lists candidate chats only after Telegram has an update;
- [ ] `verify` checks the exact chat and sends the explicit setup test message before persisting `enabled=true`;
- [ ] `disable` preserves reusable non-secret configuration unless the user requests decommissioning;
- [ ] successful Facebook report reflects `remote_verified`;
- [ ] successful LinkedIn report reflects `provider_acknowledged` and its read-back limitation;
- [ ] failure and uncertain result reports honor user preferences;
- [ ] duplicate reporting for the same exact publication/verification state is suppressed;
- [ ] Telegram delivery failure is recorded separately and never retries/changes provider publication state.

## GitHub authentication compatibility acceptance

- [ ] GitHub bearer/installation tokens are treated as opaque strings;
- [ ] no runtime or validation rule assumes classic `ghs_` token length or a no-dot token format;
- [ ] stateless installation-token format changes do not affect GitHub Actions OIDC verification semantics;
- [ ] OIDC JWT handling remains distinct from GitHub API bearer-token handling;
- [ ] token values are never logged or persisted in user/project Git data.

## Natural-language parity

At minimum semantic equivalents route identically for article list, social list, “écris le prochain post”, “écris un post libre sur X”, social connection health, Telegram notification enable/disable/reconfiguration, changing durable visual-source/treatment preferences, and one-content visual overrides such as “pour ce post utilise uniquement ma photo”.

## Final pre-productization freeze

Before generating the clean installable skill:

- [ ] scope/capability indexes reflect every current capability, including `visual-source-resolve`;
- [ ] package manifest contains the complete critical generic authority set, including user-provided-image contracts/resolver;
- [ ] manifest/user-data boundary guard passes;
- [ ] source-package preflight validates command/capability/help references plus user-image and current verification/notification semantics;
- [ ] dedicated user-provided-image resolver/contract suite passes;
- [ ] social publisher/scheduler/health/Telegram/GitHub-token regression suites pass;
- [ ] WordPress Bridge contract and syntax suites pass;
- [ ] integration PR is merged to `main`;
- [ ] the same relevant user-image/package/social/Bridge suites are green on resulting `main`;
- [ ] exact resulting `main` SHA is recorded as the immutable generation source for that skill build.

## Definition of done

The skill is implementation-complete only when packaging, catalogue validation, parser/dispatcher, detailed help, article/social inspection, visual-source preference/intake/provenance/fidelity handling, strategic-function series planning/review, queue/rollover/free mode, scheduling balance, exact publication authorization, provider evidence binding, platform-appropriate post-publication verification, connection health, optional Telegram reporting, GitHub token compatibility and safety regression fixtures all pass against representative state.

A green scheduler alone is never a definition of publication success. A green notification alone is never publication evidence. The strongest durable provider/verification state remains authoritative.
