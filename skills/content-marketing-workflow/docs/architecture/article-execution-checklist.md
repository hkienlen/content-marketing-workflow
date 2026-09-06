# Article execution checklist

Date: 2026-09-06
Status: architecture contract

## Purpose

Every SEO article execution maintains a durable Markdown checklist on the article work branch.

The checklist prevents an executor from confusing planning, visual-source/brand resolution, production, human review, media finalization, WordPress preparation and publication.

A task is checked only when its expected result is actually observable and verified.

Read together with:

```text
docs/architecture/runtime-compatibility-matrix.md
docs/architecture/user-provided-images.md
docs/architecture/visual-generation-contract.md
docs/architecture/brand-assets-contract.md
docs/architecture/google-drive-workspace.md
docs/architecture/dropbox-workspace.md
docs/architecture/capabilities/visual-source-resolve.md
docs/architecture/github-transparency.md
docs/architecture/wordpress-review-gate.md
```

## Canonical per-article file

For `articles/<target>/<slug>.md`, maintain `articles/<target>/<slug>.checklist.md` on the same article branch.

## Required task groups

### Planning and pre-draft visual/source/brand resolution

- Work Item exists;
- dedicated branch exists/reused;
- research/context persisted;
- selected `cloud_media_storage` provider resolved from durable project state when media is in scope;
- selected provider is `google_drive` or `dropbox` and operational before provider-backed source/proposal/final state is claimed durable;
- active project `visual_preferences` and `visual_identity` loaded when present;
- effective visual source policy resolved through `visual-source-resolve` **before drafting**;
- effective article logo application resolved from `visual_identity.logo_policy.article` plus any article-local override; social logo policy is not used;
- referenced user-owned `strategy/visual-guidelines.md` located/read when present;
- project-global, article-specific and content-local user visual directives identified with correct precedence;
- content-local visual/logo override persisted when applicable without mutating project preference/identity;
- if effective policy prioritizes/requires user images, exact candidate sources are located/uploaded or missing-source behavior is applied;
- any required selected-provider `source-user/` folder exists/reused and its exact canonical path + verified direct provider link are shown when the active adapter exposes one and user placement is required;
- actual user source files/bytes are verified before claiming them;
- relevant user source images are inspected before visible facts are used in drafting;
- source provider/role/fidelity/treatment/provenance is persisted when source becomes durable input;
- user source original remains unchanged;
- one truthful source state is recorded: `source_ready`, `ai_generation_allowed`, `continue_without_visuals` or `awaiting_user_images`;
- one truthful brand state is recorded/recoverable: `ready` or `awaiting_brand_asset` when applicable.

If source state is `awaiting_user_images`, **full article drafting remains unchecked and must not begin** until source intake completes or the user explicitly supplies a compatible content-local override.

`awaiting_brand_asset` is different: it may allow drafting/base-candidate work, but a final requiring `logo_application=always` cannot become `verified_final`.

### Drafting

Only after pre-draft source gate permits it:

- full article drafted and persisted;
- image briefs/roles persisted;
- image briefs reflect applicable user global/article/local visual directives;
- full article actually presented in ChatGPT for human review;
- editorial feedback processed;
- explicit `Article OK` received.

`article drafted` is not `article presented`, source intake is not editorial validation, and resolved logo preference is not media validation.

### Visual workspace and review

When article requires visuals:

- selected-provider article workspace exists;
- private `source-user/`, `proposals/`, `final/` are created/reused as applicable;
- official project logo, when required/allowed, is read from private provider brand workspace rather than content source folder;
- user and logo originals remain unchanged;
- complete effective visual contract is resolved from workflow invariants + local user directives + article directives + global user directives + generic CMW defaults;
- visual production mode is derived from effective source role/treatment;
- generic CMW creative defaults are applied only where user directives do not override them;
- article image families are materially varied unless deliberate short-series coherence is documented;
- for generated/materially transformed visuals, proposal round is generated and exactly three reviewable A/B/C candidates per required visual are retained;
- when runtime image generation/editing is unavailable, documented manual handoff is used rather than false generation success;
- manual/external generation prompt includes user visual directives and reserves brand space when needed but does not ask the generator to recreate an official logo;
- for exact `use_as_is` + no-material-treatment visuals, exact source/final review candidate is prepared instead of fake synthetic A/B/C alternatives;
- effective article logo policy is applied correctly to review candidates/final intent;
- `always` branding uses exact official verified logo bytes and does not accept an AI-redrawn approximation;
- `never` branding keeps project logo absent;
- `auto` may include only an official verified logo;
- proposal/review files are persisted in selected provider;
- provider recoverability is verified;
- each visual group is actually presented in ChatGPT with Emplacement / Objectif / Description / source role or A-B-C as applicable;
- explicit human selection/validation or targeted rejection is recorded;
- selected finals normalized and verified;
- source provenance, effective-contract revision and provider-qualified final identity/reference/hash are persisted/re-read.

No provider failure silently switches to another provider.

### Final visual verification

For each selected article image before `verified_final`:

- exact selected full-quality bytes resolved;
- target article dimensions/format applied unless an explicit reviewed exception exists;
- source fidelity remains satisfied;
- effective `logo_policy.article` plus local override is rechecked;
- `logo_application=always` -> official verified logo visibly present, legible and integrity-preserving;
- `logo_application=never` -> project logo absent;
- `logo_application=auto` -> any included project logo maps to a verified official asset;
- official logo original is not overwritten/distorted/recolored/recreated;
- final provider object + SHA-256/dimensions/MIME/filename verified;
- source and brand/effective-contract evidence persisted where applicable;
- ALT/title/caption/placement metadata remains coherent with actual final.

### Final snapshot and GitHub integration

- complete article + selected media snapshot presented when applicable workflow requires it;
- human validation of content/media snapshot received when required;
- effective visual-contract/logo evidence for finals is recoverable;
- PR technically reviewed;
- branch/PR synchronized automatically when needed;
- merge performed automatically once required content/media gates are satisfied;
- merge verified.

There is no separate `go merge` task.

### WordPress preparation

When `wordpress.enabled = true` and draft preparation is in scope:

- manifest built from exact merged commit;
- temporary delivery copies staged from exact selected-provider `verified_final` assets only when needed;
- public read-only delivery bytes verified against persisted SHA-256;
- managed draft prepared;
- technical readback verified;
- temporary delivery copy/link cleaned when practical;
- draft presented for WordPress/editor review;
- explicit `WordPress OK` received.

A workflow may terminate successfully here with article remaining a validated draft.

### Publication - conditional group

This group exists only if user actually requested publication now or end-to-end workflow explicitly includes it.

`WordPress OK`, source-image intake, image selection, logo resolution or GitHub merge never activate publication by themselves.

When publication stage is active:

- post-validation candidate captured;
- immutable candidate persisted;
- publication preflight verified;
- publication permission enabled/saved;
- explicit one-shot `publish_now` received for exact candidate;
- publication verified by readback;
- public URL checked when technically possible;
- publication permission disabled again;
- final published state persisted.

## Automatic continuation invariant

### Before drafting

```text
creation request
-> visual-source-resolve
-> effective article logo policy + rich-guideline pointer/local directives
-> source_ready | ai_generation_allowed | continue_without_visuals | awaiting_user_images
```

If `awaiting_user_images`, stop before drafting and present the actual selected-provider source-intake action. If drafting is allowed, continue automatically.

A simultaneous `awaiting_brand_asset` only blocks later brand-compliant finalization when article logo application is `always`.

### After drafting/brief persistence

When visual generation/treatment is applicable and available:

```text
article + image briefs persisted
-> resolve complete effective article visual contract
-> create/reuse selected-provider review workspace
-> generate/treat all required proposal families
-> apply exact official logo composition when effective article policy requires/allows it
-> visually reject/regenerate off-brief outputs internally
-> persist exactly three reviewable candidates per generated/materially transformed visual
-> verify provider recoverability
-> present complete article and all visual groups
```

When generation/editing is unavailable but selected cloud storage is operational, use the documented external-generation/manual-handoff path and resume from the same review state after returned asset inspection/retention/required exact brand composition.

For `use_as_is`, replace fake proposal-generation steps with exact source/final verification and presentation.

## Observable-result invariant

A checkbox may become `[x]` only when result exists.

In particular:

- source policy resolved != source verified != source inspected;
- logo policy resolved != logo asset available != logo composed != logo verified in final;
- article logo policy != social logo policy;
- user visual directive persisted != applied to a specific review round;
- source inspected != article drafted;
- article drafted != article presented;
- visual generated != stored != presented != selected != verified_final;
- `use_as_is` source presented != article approved;
- selected image/source != `Article OK`;
- `Article OK` + all required media/brand validation permits remaining internal GitHub integration automatically;
- `WordPress OK` != publication-stage invocation;
- publication-stage invocation != `publish_now`.

## Review-response gate

For first normal review after drafting, response is complete only when:

```text
full article persisted
+ full article displayed
+ required visual review package persisted/recoverable in selected provider
+ effective user visual/logo directives applied to presented candidates
+ each visual group displayed with Emplacement / Objectif / Description / appropriate candidate(s)
+ explicit request for article feedback and media selections
```

Generated/materially transformed visuals normally show A/B/C. Exact `use_as_is` source shows exact candidate and must not invent variants.

## Resume behavior

On every resume/retry, read checklist first together with article, selected provider/workspace, effective source policy/local override, visual_identity/article logo policy, referenced user visual guidelines, user-source provenance/media/brand state, Work Item and PR.

Continue from first incomplete task whose prerequisites are satisfied and within requested scope.

Do not infer completion from conversation memory. Do not enter drafting while truthful source state is `awaiting_user_images`. Do not call an `always`-branded image verified_final while brand state is `awaiting_brand_asset`. Do not enter optional publication merely because later tasks exist.

A provider change requires explicit migration/rebinding before old provider identities are treated as current.
