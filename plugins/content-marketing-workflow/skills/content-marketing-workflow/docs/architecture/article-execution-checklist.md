# Article execution checklist

Date: 2026-09-05
Status: architecture contract

## Purpose

Every SEO article execution maintains a durable Markdown checklist on the article work branch.

The checklist prevents an executor from confusing planning, visual-source intake, production, human review, media finalization, WordPress preparation and publication.

A task is checked only when its expected result is actually observable and verified.

Read together with:

```text
docs/architecture/runtime-compatibility-matrix.md
docs/architecture/user-provided-images.md
docs/architecture/google-drive-workspace.md
docs/architecture/dropbox-workspace.md
docs/architecture/capabilities/visual-source-resolve.md
docs/architecture/github-transparency.md
docs/architecture/wordpress-review-gate.md
```

## Canonical per-article file

For `articles/<target>/<slug>.md`, maintain `articles/<target>/<slug>.checklist.md` on the same article branch.

## Required task groups

### Planning and pre-draft visual-source resolution

- Work Item exists;
- dedicated branch exists/reused;
- research/context persisted;
- selected `cloud_media_storage` provider resolved from durable project state when media is in scope;
- selected provider is `google_drive` or `dropbox` and operational before provider-backed source/proposal/final state is claimed durable;
- effective visual policy resolved through `visual-source-resolve` **before drafting**;
- content-local visual override persisted when applicable without mutating project preference;
- if effective policy prioritizes/requires user images, exact candidate sources are located/uploaded or missing-source behavior is applied;
- any required selected-provider `source-user/` folder exists/reused and its exact canonical path + verified direct provider link are shown when the active adapter exposes one and user placement is required;
- actual user source files/bytes are verified before claiming them;
- relevant user source images are inspected before visible facts are used in drafting;
- source provider/role/fidelity/treatment/provenance is persisted when source becomes durable input;
- one truthful state is recorded: `source_ready`, `ai_generation_allowed`, `continue_without_visuals` or `awaiting_user_images`.

If state is `awaiting_user_images`, **full article drafting remains unchecked and must not begin** until source intake completes or the user explicitly supplies a compatible content-local override.

### Drafting

Only after pre-draft source gate permits it:

- full article drafted and persisted;
- image briefs/roles persisted;
- full article actually presented in ChatGPT for human review;
- editorial feedback processed;
- explicit `Article OK` received.

`article drafted` is not `article presented` and source intake is not editorial validation.

### Visual workspace and review

When article requires visuals:

- selected-provider article workspace exists;
- private `source-user/`, `proposals/`, `final/` are created/reused as applicable;
- user originals remain unchanged;
- visual production mode is derived from effective source role/treatment;
- for generated/materially transformed visuals, proposal round is generated and exactly three reviewable A/B/C candidates per required visual are retained;
- when runtime image generation/editing is unavailable, documented manual handoff is used rather than false generation success;
- for exact `use_as_is` + no-material-treatment visuals, exact source/final review candidate is prepared instead of fake synthetic A/B/C alternatives;
- proposal/review files are persisted in selected provider;
- provider recoverability is verified;
- each visual group is actually presented in ChatGPT with Emplacement / Objectif / Description / source role or A-B-C as applicable;
- explicit human selection/validation or targeted rejection is recorded;
- selected finals normalized and verified;
- source provenance and provider-qualified final identity/reference/hash are persisted/re-read.

No provider failure silently switches to another provider.

### Final snapshot and GitHub integration

- complete article + selected media snapshot presented when applicable workflow requires it;
- human validation of content/media snapshot received when required;
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

`WordPress OK`, source-image intake, image selection or GitHub merge never activate publication by themselves.

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
-> source_ready | ai_generation_allowed | continue_without_visuals | awaiting_user_images
```

If `awaiting_user_images`, stop before drafting and present the actual selected-provider source-intake action. If drafting is allowed, continue automatically.

### After drafting/brief persistence

When visual generation/treatment is applicable and available:

```text
article + image briefs persisted
-> create/reuse selected-provider review workspace
-> generate/treat all required proposal families
-> visually reject/regenerate off-brief outputs internally
-> persist exactly three reviewable candidates per generated/materially transformed visual
-> verify provider recoverability
-> present complete article and all visual groups
```

When generation/editing is unavailable but selected cloud storage is operational, use the documented external-generation/manual-handoff path and resume from the same review state after returned asset inspection/retention.

For `use_as_is`, replace fake proposal-generation steps with exact source/final verification and presentation.

## Observable-result invariant

A checkbox may become `[x]` only when result exists.

In particular:

- policy resolved != source verified != source inspected;
- source inspected != article drafted;
- article drafted != article presented;
- visual generated != stored != presented != selected != verified_final;
- `use_as_is` source presented != article approved;
- selected image/source != `Article OK`;
- `Article OK` + all required media validation permits remaining internal GitHub integration automatically;
- `WordPress OK` != publication-stage invocation;
- publication-stage invocation != `publish_now`.

## Review-response gate

For first normal review after drafting, response is complete only when:

```text
full article persisted
+ full article displayed
+ required visual review package persisted/recoverable in selected provider
+ each visual group displayed with Emplacement / Objectif / Description / appropriate candidate(s)
+ explicit request for article feedback and media selections
```

Generated/materially transformed visuals normally show A/B/C. Exact `use_as_is` source shows exact candidate and must not invent variants.

## Resume behavior

On every resume/retry, read checklist first together with article, selected provider/workspace, effective visual policy/local override, user-source provenance/media state, Work Item and PR.

Continue from first incomplete task whose prerequisites are satisfied and within requested scope.

Do not infer completion from conversation memory. Do not enter drafting while truthful source state is `awaiting_user_images`. Do not enter optional publication merely because later tasks exist. A provider change requires explicit migration/rebinding before old provider identities are treated as current.
