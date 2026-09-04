# Internal capability: visual-source-resolve

Date: 2026-09-04
Status: current implementation contract

## Purpose

`visual-source-resolve` resolves the effective visual-source policy for one article or social post and, when user-provided media is required or preferred, leaves verified/inspectable source-media state ready before drafting continues.

It is a core internal capability of the single installable Content / Marketing skill. It is invoked automatically by article/social creation workflows and is not a separate installable skill or publication action.

## Capability contract

```yaml
name: visual-source-resolve
purpose: Resolve inherited visual sourcing/treatment rules for one content item and verify/inspect any required or preferred user-provided sources before drafting.
availability: core
feature_gate: null
mode: mutating

prerequisites:
  - active project profile is readable
  - repository persistence contracts are readable
  - content kind is article or social
  - configured external-media provider is verified before provider-backed source intake is required

mandatory_context:
  - AGENTS.md
  - docs/architecture/persistence-contract.md
  - docs/architecture/user-profile-data-contract.md
  - docs/architecture/user-provided-images.md
  - docs/architecture/google-drive-workspace.md
  - docs/architecture/media-delivery-architecture.md
  - docs/architecture/schemas/user-profile.schema.json
  - active user-data/profile.json when present
  - active content/task/post state containing any local override

optional_context:
  - relevant existing project media-library source references
  - chat-uploaded images in the current task
  - exact Drive filenames supplied by the user
  - user-owned image/social visual strategy authorities

reads:
  - project default visual preference
  - article/social preference override
  - per-content local visual override
  - existing source-user workspace identity/state
  - actual uploaded/provider source images when supplied
  - existing durable source provenance records

writes:
  - content-local resolved policy/checkpoint when needed for resumability
  - source-user workspace folder/reference when provider-backed intake is needed
  - verified source-image provenance/role records in owning content state
  - provider-backed copy of a chat-uploaded original when durable retention is required and technically available

persists:
  - effective policy fields and inheritance origin when needed for exact resume/review
  - content-local override without mutating project defaults
  - source provider/asset identity/original filename/hash when available
  - source role/fidelity/treatment/directive
  - verified source folder ID/path/link when user placement is requested
  - truthful blocker/readiness state

external_side_effects:
  - create/reuse private source-user Drive folder when required
  - inspect/read actual provider files
  - copy a chat-uploaded original into private source-user workspace when durable retention is required
  - no public sharing
  - no image generation by this capability
  - no publication

human_approval:
  - ask only when source role/fidelity/treatment ambiguity materially changes the result
  - when required source media is missing under ask_before_drafting, ask/provide the exact placement method before drafting
  - a content-local override may be accepted from explicit user instruction without changing project preference
  - final visual selection/review remains owned by article/social visual workflow

validation:
  - effective policy is deterministic from project -> content-kind -> local override inheritance
  - local override does not mutate project/global preference
  - claimed user source resolves to a real usable image asset/file
  - source is inspected before visible attributes are used in drafting
  - strict/high fidelity never permits invented subject appearance
  - original source is not overwritten
  - source-user folder remains private
  - Drive placement request displays exact canonical path and resolved direct folder link
  - source provenance is persisted when source becomes durable workflow input
  - missing-source behavior is applied without silent fallback

completion_conditions:
  - effective visual policy is resolved
  - and one of these truthful terminal states is reached:
      - source_ready: required/preferred verified user media is available and inspected
      - ai_generation_allowed: policy permits continuing without user media
      - continue_without_visuals: policy permits drafting with no visuals
      - awaiting_user_images: drafting is blocked and exact source placement/intake instructions have been presented
  - persisted source/policy state is re-read and verified when mutation occurred

next_actions:
  - seo-create-article when content kind is article and drafting is allowed
  - social-create-post when content kind is social and drafting is allowed
  - owning article/social visual workflow after content/brief is ready
```

## Deterministic inheritance

Resolve only supported policy keys in this order:

```text
projects.<active>.visual_preferences.default
projects.<active>.visual_preferences.article|social
content-local visual override
```

The second and third layers are partial overrides. Missing fields inherit; `null` does not implicitly erase a durable rule unless the schema/explicit update semantics say so.

Supported resolved fields:

```text
visual_source
missing_user_images_behavior
source_fidelity
ai_treatment
ai_treatment_directive
```

The deterministic helper is:

```text
scripts/visual-policy-resolve.py
```

The helper performs policy resolution/validation only. It does not access Drive, inspect images or mutate GitHub.

## Intake decision

After resolution:

```text
ai_first
-> drafting may continue; user sources remain allowed by explicit local request

user_images_first / strict_user_images / hybrid_best_fit
-> inspect known supplied/relevant sources first when available
-> if absent, apply missing_user_images_behavior exactly
```

For `strict_user_images`, `allow_ai_generation` must not be interpreted as permission to fabricate a subject whose truth/fidelity requirement forbids replacement. Full synthetic replacement requires an explicit compatible local override.

## Source workspace

When content-level user media is involved, create/reuse:

```text
articles/<article-slug>/source-user/
```

or:

```text
social/<post-name>/source-user/
```

The folder is private and distinct from `proposals/` and `final/`.

If user placement is required, present both:

```text
exact canonical path
+ resolved direct clickable Drive folder link
```

Never construct a guessed link from a folder name alone.

## Chat-upload intake

A chat attachment does not count as a durable source merely because it was mentioned.

Before use:

1. confirm a usable image target actually exists in the current task;
2. inspect it;
3. when durable continuation requires provider-backed retention, copy/retain the original into `source-user/` without modifying its bytes where possible;
4. persist provenance and exact SHA-256 when exact bytes are available;
5. verify the retained provider source.

If provider retention fails, preserve truthful incomplete state rather than claiming source-ready durable intake.

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

`awaiting_user_images` is a real blocker for drafting when effective policy requires it.

The owning article/social capability must not draft first and request the source afterward merely to preserve the historical AI-first order.

An explicit content-local `write first` override may move drafting ahead for that item only. Persist it as local workflow state; never reinterpret it as a project preference change.

## Relationship to visual generation/review

This capability does not generate A/B/C and does not select a final image.

After content drafting:

- AI-first generation follows the existing proposal workflow;
- user-source enhancement/reference workflows generate compliant alternatives when appropriate;
- exact `use_as_is` + `ai_treatment: none` must not fabricate A/B/C alternatives solely to satisfy the historical generated-proposal count;
- human final media review/selection remains explicit;
- `asset-ingest` owns final normalization/verified final persistence.

## Idempotency and resume

On rerun:

- reuse the existing source-user folder;
- reuse already verified identical source assets/provenance;
- do not duplicate provider copies for the same retained source identity/hash;
- re-check a provider source before using it if durable state no longer proves accessibility/identity;
- preserve project preferences unchanged when a local override is resumed;
- return the existing truthful terminal state when nothing changed.

## Failure behavior

Fail closed when:

- required policy is invalid;
- a claimed source file cannot be verified;
- a source resolves to non-image/preview-only bytes when full source is required;
- source identity/hash drift is detected;
- exact Drive folder identity/link cannot be resolved for a placement request;
- strict/high-fidelity requirements conflict with the requested transformation.

Do not substitute another image, infer appearance or silently switch to full AI generation.
