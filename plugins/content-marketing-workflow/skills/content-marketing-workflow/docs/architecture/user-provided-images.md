# User-provided images workflow

Date: 2026-09-04
Status: normative architecture contract

## Purpose

The Content / Marketing skill must support real user-provided photos/images as first-class visual sources for SEO articles and social posts.

This is a generic product capability. It is required for workflows where the real product, work, place, photograph or other subject must be represented faithfully instead of being silently replaced by synthetic AI imagery.

Read this contract together with:

```text
docs/architecture/user-profile-data-contract.md
docs/architecture/persistence-contract.md
docs/architecture/google-drive-workspace.md
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

A local instruction such as:

```text
For this post, generate the image completely with AI.
For this article only, use my supplied photo without retouching.
Keep this product exact but replace only the background.
```

applies only to that content item unless the user explicitly asks to change the durable project preference.

Never silently mutate project/global preferences from one-off content instructions.

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

The source images may materially influence angle, wording and placement. Therefore they are collected and inspected before drafting rather than attached afterward.

A one-off instruction such as `write first, I will provide the photos later` is allowed. Persist it only as a content-local override/checkpoint; it does not alter the project preference.

## Missing-source decision table

After effective policy resolution:

### `ai_first`

Normal drafting may continue without user media. User-provided media is still allowed by local override.

### `user_images_first`

- relevant verified user images available -> inspect/use them first;
- none available + `ask_before_drafting` -> stop before drafting and request/locate sources;
- none available + `allow_ai_generation` -> drafting and AI generation may continue;
- none available + `continue_without_visuals` -> drafting may continue with no visual workflow unless later reopened.

### `strict_user_images`

Do not silently switch to fully synthetic replacement imagery.

- source available -> inspect/use it under fidelity/treatment rules;
- source missing + `ask_before_drafting` -> stop before drafting and request/locate it;
- source missing + another behavior -> continue only to the extent that behavior is compatible with the exact local/user intent; full AI replacement requires an explicit local override when the visual truth requirement would otherwise be violated.

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

Semantics:

- `use_as_is`: the source image itself is the intended visual; only explicitly allowed normalization/export operations may occur;
- `enhance`: improve the source within the effective fidelity/treatment limits;
- `subject_reference`: the represented product/person/object must be respected while composition may change within limits;
- `inspiration_reference`: mood/style reference only; not a claim that the depicted subject must be preserved;
- `composition_input`: integrate the supplied image into a broader composition.

Do not assume a photographer's image is merely inspiration. Do not assume a product photo may be redesigned freely.

When role ambiguity materially changes fidelity or allowed transformation, ask one concise business/content question.

## Intake channels

### Chat upload

Suitable for one-off or small sets.

Before relying on an uploaded image:

1. verify a real usable image attachment exists;
2. inspect the image itself;
3. when it becomes durable workflow input, copy/retain the original in the configured private `source-user/` workspace when provider access permits;
4. preserve original provenance/filename and a SHA-256 when exact bytes are available;
5. never overwrite the original upload/source.

### Google Drive

Suitable for recurring/professional workflows and larger sets.

The user may provide exact filenames, place files in the content `source-user/` folder, ask to use all images there, or request a relevant existing source be located.

The skill must verify the real files before claiming they exist or using them.

## Mandatory Google Drive request UX

Whenever the skill asks the user to place source images in Drive, the response must show both:

1. the exact human-readable canonical folder path/name;
2. a direct clickable Google Drive folder link resolved from the verified provider folder identity.

Article example:

```text
Déposez vos photos dans :
<drive-root>/<site-domain>/articles/<article-slug>/source-user/

Ouvrir le dossier : <resolved direct Drive folder link>
```

Social example:

```text
Déposez votre photo dans :
<drive-root>/<site-domain>/social/<post-name>/source-user/

Ouvrir le dossier : <resolved direct Drive folder link>
```

Never guess a folder URL from a name alone. If the folder does not yet exist and the skill owns workspace setup, create/reuse it, resolve its provider ID/link, verify it, persist the non-secret identity, then present path + link.

## Drive workspace layout

Article:

```text
<drive-root>/<site-domain>/articles/<article-slug>/
├── source-user/     private originals
├── proposals/       private generated/treated candidates
└── final/           private selected/normalized finals
```

Social:

```text
<drive-root>/<site-domain>/social/<post-name>/
├── source-user/     private originals
├── proposals/       private generated/treated candidates
└── final/           private selected/normalized finals
```

Critical invariant:

> Never overwrite or destructively normalize the original user-provided file.

A final derivative uses a different object/file, for example:

```text
source-user/source-image.jpg
final/final-social-image.jpg
```

Only `tmp-outbox/` may be public-by-link for temporary delivery. `source-user/` is always private.

## Reusable project media library extension point

The architecture must remain compatible with a persistent project media library such as:

```text
<drive-root>/<site-domain>/media-library/
```

Possible assets include portraits, locations, products, brand assets and portfolio images.

Full media-library search/index implementation is not required for the first user-image feature. Future use must still verify/inspect the real asset and respect its provenance/usage/fidelity constraints.

## Provenance record

A user-provided source used by a durable content item must preserve enough metadata to avoid later treating it as freely synthetic content.

Minimum conceptual record:

```yaml
source_type: user_provided
source_provider: google_drive|chat_upload
source_asset_id: <provider identity when available>
source_original_filename: <original filename>
source_sha256: <64 lowercase hex when exact bytes are available>
source_role: use_as_is|enhance|subject_reference|inspiration_reference|composition_input
source_fidelity: strict|high|moderate|flexible
ai_treatment: none|light_correction|natural_enhancement|marketing_enhancement|creative_transformation
ai_treatment_directive: <durable project directive or local override>
```

For Drive-backed sources, also persist/recover the source folder identity/path/link when needed for resumption.

The final asset retains the normal provider identity/hash/format/dimensions/ALT/title/caption/placement plus a reference or embedded provenance snapshot sufficient to trace its user-provided origin.

## Review behavior

The existing human final-image review gate remains mandatory.

The generic rule `exactly three A/B/C generated proposals` applies when the effective workflow is generating or materially transforming alternatives.

It must **not** force synthetic alternatives when the user's exact source is intended `use_as_is` with `ai_treatment: none` (or equivalent faithful documentary intent). In that case the review presents/verifies the exact source/final candidate and asks for the normal content/media validation without inventing two unnecessary variants.

For enhancement/transformation workflows, A/B/C may represent distinct compliant treatments/compositions. All variants must preserve the effective fidelity constraints.

## Onboarding and changing preferences

When visual generation is relevant, `start` guides the user in plain language through:

1. whether their own photos should normally be preferred;
2. whether some real subjects must never be synthetically replaced;
3. acceptable AI treatment intensity;
4. required fidelity;
5. whether article and social behavior should differ;
6. what to do when a user image is missing;
7. confirmation that content-local overrides remain possible.

The skill summarizes the resulting policy in plain language before persisting it when a durable preference is being set.

The user may change the durable preference later through natural language or `/strategy update` without reinstalling the skill.

`/status` exposes the active resolved project visual preference and any blocking missing-source state, but never mutates it.

## Safety and truthfulness invariants

- Never claim a source image exists without verifying the actual upload/provider asset.
- Never overwrite user originals.
- Never invent product/subject appearance when strict/high fidelity applies.
- Never silently switch to full AI generation when `strict_user_images` or an active `ask_before_drafting` blocker applies.
- Never infer a permanent preference from a one-off instruction.
- Never treat source media as publication authorization.
- Image intake, treatment, final selection, scheduling and publication are distinct states.
- User-specific preferences/directives stay in user/project data, not generic skill code.
- Provider failures do not authorize substitution with a different binary.

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
- exact Drive path + direct-link UX requirement;
- source provenance fields;
- existing AI-first behavior remains valid;
- existing publication/scheduling gates remain unchanged.
