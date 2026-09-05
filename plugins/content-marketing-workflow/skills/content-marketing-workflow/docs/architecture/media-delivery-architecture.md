# Media delivery architecture

Date: 2026-09-05
Status: current architecture

## Authority and compatibility

Global prerequisite/degradation behavior is owned by:

```text
docs/architecture/runtime-compatibility-matrix.md
```

This document owns media identity, retention and delivery semantics. It must not redefine provider eligibility or degraded-mode policy.

Implemented cloud-media adapters:

```text
google_drive
dropbox
```

Exactly one provider is active per project. Google Drive is the recommended/default selection when both providers are operational. Provider switching is explicit and must migrate/rebind durable provider identities rather than reinterpret existing IDs.

GitHub, WordPress and local filesystem are not normal media-storage providers. Existing `repository_file` media is legacy compatibility/migration only and is never an automatic fallback.

## Decision

CMW keeps editorial content, durable workflow state, media metadata, source provenance and exact media fingerprints in GitHub/user-project data, while source originals and validated media binaries remain in the configured `cloud_media_storage` provider in normal operation.

A provider-backed media workflow is complete only when the selected cloud provider is operational. If no implemented provider is available, media finalization/publication remains degraded according to the compatibility matrix.

## Three media identities

When user-provided images are involved, distinguish:

```text
1. source original identity
2. retained final identity
3. temporary delivery-copy identity
```

Never conflate them.

### Source original

Private provider object/file under `source-user/`, or verified chat-upload source before provider retention.

Purpose: preserve user input, support inspection/truth/fidelity, retain provenance, and provide deterministic source for allowed treatment. Never overwrite/destructively normalize it.

### Retained final

Private provider object/file under `final/`.

Purpose: stable selected/normalized binary used by destinations with durable provider `asset_id` + SHA-256 + filename/MIME/dimensions/ALT relationship.

### Temporary delivery copy

Disposable object under `tmp-outbox/`, anonymously readable only for exact active external delivery. It never becomes the durable source/final identity.

## Canonical provider-neutral layout

Conceptually:

```text
<provider-root>/<site-domain>/articles/<article-slug>/
├── source-user/
├── proposals/
└── final/

<provider-root>/<site-domain>/social/<post-name>/
├── source-user/
├── proposals/
└── final/

<provider-root>/<site-domain>/tmp-outbox/
```

Provider-specific mappings are defined in:

```text
docs/architecture/google-drive-workspace.md
docs/architecture/dropbox-workspace.md
```

Privacy invariant:

```text
source-user/ -> private
proposals/   -> private
final/       -> private
tmp-outbox/  -> public-link viewer only when configured
```

## Stable source provenance

Persist enough provenance in GitHub/content state to keep source truth and fidelity explicit, for example:

```yaml
source_type: user_provided
source_provider: google_drive|dropbox|chat_upload
source_asset_id: <provider source identity when available>
source_original_filename: <original filename>
source_sha256: <exact original bytes when available>
source_role: use_as_is|enhance|subject_reference|inspiration_reference|composition_input
source_fidelity: strict|high|moderate|flexible
ai_treatment: none|light_correction|natural_enhancement|marketing_enhancement|creative_transformation
ai_treatment_directive: <resolved directive or null>
```

Provider identity/hash drift fails closed.

## Stable final identity

Provider-backed final metadata:

```yaml
provider: google_drive|dropbox
asset_id: <private retained final provider identity>
filename: <canonical filename>
sha256: <exact normalized bytes>
mime_type: <image mime>
width: <pixels>
height: <pixels>
asset_status: verified_final
```

Canonical identity is provider + provider `asset_id` + SHA-256, not public URL/outbox copy ID. Provider identity is part of the durable identity namespace; a Google Drive ID and Dropbox reference must never be treated as interchangeable.

## Lifecycle

```text
source_discovered
-> source_verified
-> source_inspected
-> proposal/treatment when applicable
-> selected
-> normalized
-> verified_final
-> delivery_staged
-> destination_verified
```

Each state is distinct.

## Runtime image-generation fallback

When the active runtime cannot generate/edit an image required by the visual policy but cloud storage is operational, use the manual handoff from `runtime-compatibility-matrix.md`:

```text
exact visual brief
-> complete external-generation prompt
-> user generates/improves image externally
-> user returns/uploads image
-> inspect
-> persist in selected cloud provider
-> proposal/review/finalization
```

The prompt alone never completes the visual workflow.

If image generation is available but cloud storage is not, generated outputs may be reviewed as transient artifacts only. They cannot become durable `verified_final` media and cannot unlock publication.

## Chat uploads

A chat upload can be source only when an actual usable attachment is available and inspected. When durable resume/provider use requires it, retain the original in private `source-user/` of the selected provider and persist original provenance/hash where possible.

If provider retention fails, report incomplete state truthfully.

## Proposals and final normalization

Generated/materially transformed candidates live in private `proposals/`. Exact user-source `use_as_is` does not fabricate A/B/C.

`asset-ingest` resolves the selected source/candidate, applies output policy, writes/reuses a private final provider object, computes SHA-256, persists metadata/provenance and re-verifies. Never overwrite source originals.

## Delivery staging

When a destination requires anonymous HTTP bytes:

```text
verified private final
-> copy to selected provider tmp-outbox
-> establish provider-supported anonymous read-only delivery reference
-> verify anonymous bytes SHA-256 == persisted final SHA-256
-> destination mutation
-> verify destination response/readback
-> delete temporary outbox copy/link when practical
```

Only exact verified finals intended for the destination are staged.

For Google Drive, delivery sharing follows `google-drive-workspace.md`. For Dropbox, delivery sharing follows `dropbox-workspace.md`. Provider-specific public-link mechanics must not leak into the stable final identity.

## Strict publication invariant

```text
no required verified final media
=> no WordPress preparation-for-publication / publication
=> no social publication
```

Do not degrade to image-less WordPress publication, text-only social publication, repository binary fallback, WordPress-media-as-storage fallback or local filesystem fallback.

## WordPress

WordPress preparation uses exact provider-backed finals via temporary outbox delivery in normal operation. WordPress media library objects are derived publication representations, not CMW durable media storage.

`WordPress OK` and `publish_now` gates remain independent.

## Social

Social publication uses only exact `verified_final` media bound to approved text/ALT/platform/time/authorization. Current LinkedIn/Facebook publication additionally requires the WordPress-hosted SEO Workflow Bridge as declared by the compatibility matrix.

## Provider switching and migration

Switching the active project provider between Google Drive and Dropbox is never an implicit fallback.

A provider migration must:

1. preserve source originals and retained finals;
2. copy/recreate exact bytes in the destination provider;
3. verify SHA-256 after transfer;
4. persist new provider + asset identity while retaining provenance of the prior identity when needed;
5. update workspace/outbox references explicitly;
6. never claim `verified_final` merely because an old provider ID exists after the project selection changed.

## Legacy repository-backed media

`repository_file` may remain readable only for explicit backward compatibility/migration where an owning contract still supports it.

Rules:

- never offer GitHub as a new media provider;
- never automatically fall back to repository binaries;
- never mark `cloud_media_storage` ready from repository media;
- preserve exact hashes/provenance during explicit migration.

## Testing invariants

Validate at least:

- both `google_drive` and `dropbox` are recognized as implemented providers;
- exactly one active provider per project;
- provider-qualified source/final identity;
- explicit provider switching/migration semantics;
- source original non-overwrite;
- source/final/outbox identity separation;
- source/final/outbox hash drift fail-closed;
- private source/proposal/final boundary;
- runtime image-generation manual handoff semantics;
- no cloud provider -> no durable media finalization/publication;
- no image-less WordPress or text-only social fallback;
- legacy repository media never becomes automatic fallback;
- destination idempotency/publication gates unchanged.
