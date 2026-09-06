# Internal capability: visual-source-resolve

Date: 2026-09-06
Status: current implementation contract

## Purpose

`visual-source-resolve` resolves the effective visual-source policy for one article or social post and, when user-provided media is required or preferred, leaves verified/inspectable source-media state ready before drafting continues.

The same deterministic helper also resolves the structured **brand handoff** required by later visual generation/finalization: independent article/social logo application, available official logo references, rich-guidelines pointer and content-local visual/logo overrides.

It is a core internal capability of the single installable Content / Marketing skill. It is invoked automatically by article/social creation workflows and is not a separate installable skill or publication action.

## Capability contract

```yaml
name: visual-source-resolve
purpose: Resolve inherited visual sourcing/treatment plus structured brand handoff for one content item and verify/inspect any required or preferred user-provided sources before drafting.
availability: core
feature_gate: null
mode: mutating

prerequisites:
  - active project profile is readable
  - repository persistence contracts are readable
  - content kind is article or social
  - selected cloud_media_storage provider is operational before provider-backed source intake is required

mandatory_context:
  - AGENTS.md
  - docs/architecture/persistence-contract.md
  - docs/architecture/user-profile-data-contract.md
  - docs/architecture/runtime-compatibility-matrix.md
  - docs/architecture/user-provided-images.md
  - docs/architecture/visual-generation-contract.md
  - docs/architecture/brand-assets-contract.md
  - docs/architecture/google-drive-workspace.md
  - docs/architecture/dropbox-workspace.md
  - docs/architecture/media-delivery-architecture.md
  - docs/architecture/schemas/user-profile.schema.json
  - active user-data/profile.json when present
  - active content/task/post state containing any local override
  - referenced user-owned strategy/visual-guidelines.md when present

optional_context:
  - relevant existing project media-library source references
  - chat-uploaded images in the current task
  - exact provider filenames/paths supplied by the user

reads:
  - project default visual preference
  - article/social visual-preference override
  - project visual_identity including independent article/social logo policy
  - user visual-guidelines authority pointer
  - per-content local visual/logo override
  - existing source-user workspace identity/state
  - actual uploaded/provider source images when supplied
  - existing durable source provenance records

writes:
  - content-local resolved policy/brand checkpoint when needed for resumability
  - source-user workspace folder/reference when provider-backed intake is needed
  - verified source-image provenance/role records in owning content state
  - provider-backed copy of a chat-uploaded original when durable retention is required and technically available

persists:
  - effective source-policy fields and inheritance origin when needed for exact resume/review
  - effective logo application and structured brand handoff when needed for exact review/finalization
  - content-local override without mutating project defaults
  - source provider/asset identity/original filename/hash when available
  - source role/fidelity/treatment/directive
  - verified source folder identity/path/link when user placement is requested
  - truthful blocker/readiness state

external_side_effects:
  - create/reuse private source-user folder in selected cloud provider when required
  - inspect/read actual provider files
  - copy a chat-uploaded original into private source-user workspace when durable retention is required
  - no public sharing
  - no image generation or logo composition by this capability
  - no publication

human_approval:
  - ask only when source role/fidelity/treatment ambiguity materially changes the result
  - when required source media is missing under ask_before_drafting, ask/provide the exact selected-provider placement method before drafting
  - a content-local visual/logo override may be accepted from explicit user instruction without changing project preference
  - final visual selection/review remains owned by article/social visual workflow

validation:
  - effective source policy is deterministic from project -> content-kind -> local override inheritance
  - article/social logo policy is resolved independently from visual_identity.logo_policy
  - local override does not mutate project/global preference
  - claimed user source resolves to a real usable image asset/file
  - source is inspected before visible attributes are used in drafting
  - strict/high fidelity never permits invented subject appearance
  - original source is not overwritten
  - source-user folder remains private
  - provider placement request displays exact canonical path and resolved direct folder link when available
  - source provenance is persisted when source becomes durable workflow input
  - source provider identity matches the selected project provider
  - missing-source behavior is applied without silent fallback
  - logo_application=always with no official logo produces awaiting_brand_asset for finalization rather than synthesized branding

completion_conditions:
  - effective visual source policy is resolved
  - structured brand handoff is resolved (configured or truthful legacy-unconfigured state)
  - and one source terminal state is reached:
      - source_ready: required/preferred verified user media is available and inspected
      - ai_generation_allowed: policy permits continuing without user media
      - continue_without_visuals: policy permits drafting with no visuals
      - awaiting_user_images: drafting is blocked and exact source placement/intake instructions have been presented
  - persisted source/policy/brand state is re-read and verified when mutation occurred

next_actions:
  - seo-create-article when content kind is article and drafting is allowed
  - social-create-post when content kind is social and drafting is allowed
  - owning article/social visual workflow after content/brief is ready
  - visual-configure when durable brand/visual preferences are missing or user asks to change them
```

## Deterministic source-policy inheritance

Resolve source/treatment keys in this order:

```text
projects.<active>.visual_preferences.default
projects.<active>.visual_preferences.article|social
content-local visual override
```

The second and third layers are partial overrides. Missing fields inherit; `null` does not implicitly erase a durable rule unless the schema/explicit update semantics say so.

Supported source/treatment fields:

```text
visual_source
missing_user_images_behavior
source_fidelity
ai_treatment
ai_treatment_directive
```

## Structured brand handoff

Resolve the content kind independently:

```text
article -> projects.<active>.visual_identity.logo_policy.article
social  -> projects.<active>.visual_identity.logo_policy.social
```

Then apply an explicit content-local `logo_application` override when present.

The article choice never inherits from the social choice and the social choice never inherits from the article choice.

The helper returns a structured `brand` block containing at least:

```text
configured
guidelines_path
logo_application
logo_policy_source
logo_assets
logo_asset_available
logo_required_for_final
logo_allowed
logo_status
local_visual_directives
inheritance
```

For older profiles with no `visual_identity`, compatibility behavior is:

```text
logo_application = never
configured = false
logo_policy_source = legacy_unconfigured_no_logo
```

This preserves the historical no-logo generic behavior while keeping the missing configuration visible for onboarding. It must not be rewritten as a confirmed user preference until the user chooses it.

If `logo_application=always` and no official logo asset is available, return `logo_status=awaiting_brand_asset`. This does not necessarily block text drafting/base-image generation, but it blocks a branded final from reaching `verified_final`.

## Content-local visual override

The deterministic helper accepts source-policy fields plus:

```yaml
logo_application: always|auto|never
visual_directives:
  - <one-off free directive>
```

These extra fields are content-local only. They are not project `visual_preferences` fields and must never be promoted to permanent profile/strategy state without explicit user intent.

## Helper

Use:

```text
scripts/visual-policy-resolve.py
```

The helper performs structured policy/brand resolution and validation only. It does not access cloud storage, inspect images, interpret rich Markdown guidelines, compose logos or mutate GitHub.

The owning visual workflow reads `visual-generation-contract.md`, `brand-assets-contract.md` and the referenced user-owned `strategy/visual-guidelines.md` to resolve the complete semantic creative contract.

## Intake decision

After source resolution:

```text
ai_first
-> drafting may continue; user sources remain allowed by explicit local request

user_images_first / strict_user_images / hybrid_best_fit
-> inspect known supplied/relevant sources first when available
-> if absent, apply missing_user_images_behavior exactly
```

For `strict_user_images`, `allow_ai_generation` must not be interpreted as permission to fabricate a subject whose truth/fidelity requirement forbids replacement. Full synthetic replacement requires an explicit compatible local override.

## Source workspace

When content-level user media is involved, create/reuse under the selected provider:

```text
<provider-root>/<site-domain>/articles/<article-slug>/source-user/
```

or:

```text
<provider-root>/<site-domain>/social/<post-name>/source-user/
```

The folder is private and distinct from `proposals/` and `final/`.

Brand/logo sources do not belong in these content source folders. Official project logos live in the private brand workspace defined by `brand-assets-contract.md`.

If user placement is required, present both exact canonical provider path and a resolved direct clickable provider folder link when available. Never construct a guessed link from a folder name/path alone.

## Chat-upload intake

A chat attachment does not count as a durable source merely because it was mentioned.

Before use:

1. confirm a usable image target actually exists in the current task;
2. inspect it;
3. when durable continuation requires provider-backed retention, copy/retain the original into selected-provider `source-user/` without modifying its bytes where possible;
4. persist provenance and exact SHA-256 when exact bytes are available;
5. verify the retained provider source.

Official logo uploads follow the separate brand asset intake contract and are retained in the project brand workspace, not content `source-user/`.

## Source roles

Persist one of:

```text
use_as_is
enhance
subject_reference
inspiration_reference
composition_input
```

If the role is obvious from an explicit instruction, do not ask again. Ask one concise question only when choosing the role would materially alter fidelity or transformation.

## Drafting boundary

`awaiting_user_images` is a real blocker for drafting when effective source policy requires it.

The owning article/social capability must not draft first and request the source afterward merely to preserve the historical AI-first order.

An explicit content-local `write first` override may move drafting ahead for that item only. Persist it as local workflow state; never reinterpret it as a project preference change.

`awaiting_brand_asset` is different: it blocks brand-compliant finalization when the effective logo rule is `always`, but it does not by itself prohibit editorial drafting or unbranded base-candidate exploration.

## Relationship to visual generation/review

This capability does not generate A/B/C, compose logos or select a final image.

After content drafting:

- load the complete effective visual contract from generic defaults + user global/channel directives + local directives;
- AI-first generation follows the existing proposal workflow;
- user-source enhancement/reference workflows generate compliant alternatives when appropriate;
- exact `use_as_is` + `ai_treatment: none` must not fabricate A/B/C alternatives solely to satisfy the historical generated-proposal count;
- apply exact official branding according to independent article/social policy before a branded final is accepted;
- human final media review/selection remains explicit;
- `asset-ingest` owns final normalization/verified final persistence.

## Idempotency and resume

On rerun:

- reuse existing selected-provider source-user folder;
- reuse already verified identical source assets/provenance;
- reuse current visual_identity/logo assets by provider-qualified identity/hash when verified;
- do not duplicate provider copies for the same retained source identity/hash;
- re-check a provider source before using it if durable state no longer proves accessibility/identity;
- preserve project preferences unchanged when a local override is resumed;
- return the existing truthful terminal state when nothing changed.

If durable project provider changes, require explicit provider migration/rebinding before treating old provider identities as source-ready or brand-ready in the new provider.

## Failure behavior

Fail closed when:

- required source/brand policy is invalid;
- a claimed source file cannot be verified;
- a source resolves to non-image/preview-only bytes when full source is required;
- source identity/hash drift is detected;
- exact selected-provider folder identity/link cannot be resolved when the active adapter requires it for placement UX;
- strict/high-fidelity requirements conflict with the requested transformation.

Do not substitute another image, infer appearance, silently switch providers, silently switch to full AI generation or synthesize an official logo.
