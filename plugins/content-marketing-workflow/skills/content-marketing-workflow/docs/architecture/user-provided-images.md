# User-provided images workflow

Date: 2026-09-05
Status: normative architecture contract

## Purpose

The Content / Marketing skill must support real user-provided photos/images as first-class visual sources for SEO articles and social posts.

This is a generic product capability. It is required for workflows where the real product, work, place, photograph or other subject must be represented faithfully instead of being silently replaced by synthetic AI imagery.

Read this contract together with:

```text
docs/architecture/user-profile-data-contract.md
docs/architecture/persistence-contract.md
docs/architecture/runtime-compatibility-matrix.md
docs/architecture/google-drive-workspace.md
docs/architecture/dropbox-workspace.md
docs/architecture/media-delivery-architecture.md
docs/architecture/image-asset-ingestion.md
docs/architecture/capabilities/visual-source-resolve.md
```

## Core visual policy

The active project may persist one global visual policy, with optional article and social overrides.

Canonical sourcing modes:

```text
ai_first
user_images_first
strict_user_images
hybrid_best_fit
```

Semantics:

- `ai_first`: generate from scratch by default; a local user-image override remains possible;
- `user_images_first`: prefer relevant verified user images when available;
- `strict_user_images`: do not invent a replacement when a real user image is required;
- `hybrid_best_fit`: use verified user media when it materially improves truth/relevance, otherwise AI generation may be used.

Source preference and missing-source behavior are separate dimensions.

Canonical missing-source modes:

```text
ask_before_drafting
allow_ai_generation
continue_without_visuals
```

Canonical fidelity modes:

```text
strict
high
moderate
flexible
```

Canonical AI treatment modes:

```text
none
light_correction
natural_enhancement
marketing_enhancement
creative_transformation
```

A durable free-text `ai_treatment_directive` may refine the selected treatment without changing the enum model.

## Fidelity and treatment are separate axes

Never treat transformation intensity as equivalent to subject fidelity.

Examples:

```text
photographer -> strict/high fidelity + none/light_correction
real craft product -> high fidelity + marketing_enhancement may be valid
creative campaign -> moderate/flexible fidelity + creative_transformation may be valid
```

A stronger treatment mode never authorizes misleading changes to a subject whose effective fidelity is `strict` or `high`.

## Inheritance and local overrides

Resolve effective policy in this order:

```text
project visual default
-> article or social override
-> per-content local override
```

Only explicitly present fields override inherited fields.

A local instruction applies only to that content item unless the user explicitly asks to change the durable project preference. Never silently mutate project/global preferences from one-off content instructions.

## Mandatory pre-draft source resolution

Before writing an article or social post, resolve the effective visual policy.

When the effective mode requires or prioritizes user images and the missing-source behavior is `ask_before_drafting`, normal order is:

```text
creation request
-> load effective visual policy
-> create/reuse the content source-user workspace when needed
-> collect or locate candidate user images
-> verify the actual files/bytes exist
-> inspect the actual images
-> persist source identity/provenance/role
-> use only visible/verified attributes as editorial context
-> draft content + visual strategy
-> apply allowed treatment/generation behavior
-> human review/final selection
```

A one-off `write first` instruction may move drafting ahead for that content item only.

## Missing-source decision table

### `ai_first`

Normal drafting may continue without user media. User-provided media is still allowed by local override.

### `user_images_first`

- relevant verified user images available -> inspect/use them first;
- none available + `ask_before_drafting` -> stop before drafting and request/locate sources;
- none available + `allow_ai_generation` -> drafting and AI generation may continue;
- none available + `continue_without_visuals` -> drafting may continue with no visual workflow unless later reopened.

### `strict_user_images`

Do not silently switch to fully synthetic replacement imagery. Full AI replacement requires an explicit compatible local override when the visual truth requirement would otherwise be violated.

### `hybrid_best_fit`

Inspect relevant supplied/library media when known. Use it when it materially improves truth/relevance; otherwise AI generation may remain available according to the missing-source behavior.

## Source-image roles

Every user-provided source used durably should have an explicit role when it affects treatment:

```text
use_as_is
enhance
subject_reference
inspiration_reference
composition_input
```

Do not assume a photographer's image is merely inspiration. Do not assume a product photo may be redesigned freely. Ask only when role ambiguity materially changes fidelity or allowed transformation.

## Intake channels

### Chat upload

Suitable for one-off or small sets.

Before relying on an uploaded image:

1. verify a real usable image attachment exists;
2. inspect the image itself;
3. when it becomes durable workflow input, retain the original in the selected provider's private `source-user/` workspace when provider access permits;
4. preserve original provenance/filename and SHA-256 when exact bytes are available;
5. never overwrite the original upload/source.

### Selected cloud-media provider

Supported providers are:

```text
google_drive
dropbox
```

The user may provide exact filenames, place files in the content `source-user/` folder, ask to use all images there, or request a relevant existing source be located. The skill must verify the real files before claiming they exist or using them.

Exactly one provider is active per project. Never silently read/write from the non-selected provider as a fallback.

## Mandatory provider placement UX

Whenever the skill asks the user to place source images in the selected provider, the response must show:

1. the exact human-readable canonical folder path/name;
2. a direct clickable provider folder link resolved from the verified provider folder identity when the active integration exposes one.

Never guess a provider URL from a folder name/path alone. If the folder does not yet exist and the skill owns workspace setup, create/reuse it, resolve its provider identity/link, verify it, persist the non-secret identity, then present path + link.

Provider-specific details are governed by `google-drive-workspace.md` and `dropbox-workspace.md`.

## Provider-neutral workspace layout

Article:

```text
<provider-root>/<site-domain>/articles/<article-slug>/
├── source-user/     private originals
├── proposals/       private generated/treated candidates
└── final/           private selected/normalized finals
```

Social:

```text
<provider-root>/<site-domain>/social/<post-name>/
├── source-user/     private originals
├── proposals/       private generated/treated candidates
└── final/           private selected/normalized finals
```

Critical invariant:

> Never overwrite or destructively normalize the original user-provided file.

Only `tmp-outbox/` delivery material may be public-by-link temporarily. `source-user/` is always private.

## Reusable project media library extension point

The architecture remains compatible with a persistent provider media library such as:

```text
<provider-root>/<site-domain>/media-library/
```

Future use must still verify/inspect the real asset and respect provenance/usage/fidelity constraints.

## Provenance record

A user-provided source used by a durable content item must preserve enough metadata to avoid later treating it as freely synthetic content.

Minimum conceptual record:

```yaml
source_type: user_provided
source_provider: google_drive|dropbox|chat_upload
source_asset_id: <provider identity when available>
source_original_filename: <original filename>
source_sha256: <64 lowercase hex when exact bytes are available>
source_role: use_as_is|enhance|subject_reference|inspiration_reference|composition_input
source_fidelity: strict|high|moderate|flexible
ai_treatment: none|light_correction|natural_enhancement|marketing_enhancement|creative_transformation
ai_treatment_directive: <durable project directive or local override>
```

For provider-backed sources, also persist/recover the source folder identity/path/link when needed for resumption.

The final asset retains provider-qualified identity/hash/format/dimensions/ALT/title/caption/placement plus a reference or embedded provenance snapshot sufficient to trace its user-provided origin.

## Review behavior

The existing human final-image review gate remains mandatory.

The generic rule `exactly three A/B/C generated proposals` applies when the effective workflow is generating or materially transforming alternatives. It must not force synthetic alternatives when the user's exact source is intended `use_as_is` with `ai_treatment: none` or equivalent faithful documentary intent.

## Onboarding and changing preferences

When visual generation is relevant, `start` guides the user in plain language through source preference, strict-real subjects, treatment intensity, fidelity, channel overrides and missing-source behavior. The user may change durable preference later through natural language or `/strategy update` without reinstalling the skill.

## Provider switching

Switching between Google Drive and Dropbox is explicit migration work. Preserve exact source/final bytes and hashes, create destination-provider identities, update references, and never reinterpret an ID/path from one provider as belonging to the other.

## Safety and truthfulness invariants

- Never claim a source image exists without verifying the actual upload/provider asset.
- Never overwrite user originals.
- Never invent product/subject appearance when strict/high fidelity applies.
- Never silently switch to full AI generation when `strict_user_images` or an active `ask_before_drafting` blocker applies.
- Never infer a permanent preference from a one-off instruction.
- Never treat source media as publication authorization.
- Image intake, treatment, final selection, scheduling and publication are distinct states.
- User-specific preferences/directives stay in user/project data, not generic skill code.
- Provider failures do not authorize substitution with a different provider or binary.

## Testing requirements

Tests must cover at least:

- project default -> article/social override -> local override precedence;
- no mutation of project preference by local override;
- `ask_before_drafting` blocks drafting when required user media is absent;
- `allow_ai_generation` and `continue_without_visuals` behavior;
- strict mode never silently enables synthetic replacement;
- source-role handling;
- `use_as_is` does not require fake A/B/C generation;
- original/non-overwrite invariant;
- selected-provider exact path + direct-link UX requirement;
- Google Drive and Dropbox source provenance fields;
- explicit provider migration/rebinding;
- existing AI-first behavior remains valid;
- existing publication/scheduling gates remain unchanged.
