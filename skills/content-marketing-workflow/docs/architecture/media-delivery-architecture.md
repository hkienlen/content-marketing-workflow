# Media delivery architecture

Date: 2026-09-04
Status: current architecture

## Decision

The Content / Marketing skill keeps editorial content, durable workflow state, media metadata, **user-source provenance** and exact media fingerprints in GitHub/user-project data, while user-source originals and validated media binaries remain in the configured external media workspace in normal provider-backed mode.

Current provider implementation is Google Drive. Provider-neutral business contracts remain compatible with a future Dropbox adapter.

User-provided image sourcing/intake is governed by:

```text
docs/architecture/user-provided-images.md
docs/architecture/capabilities/visual-source-resolve.md
```

Final normalization/identity is governed by:

```text
docs/architecture/image-asset-ingestion.md
docs/architecture/capabilities/asset-ingest.md
```

## Three media identities

The architecture distinguishes at least three media identities when user-provided images are involved:

```text
1. source original identity
2. retained final identity
3. temporary delivery-copy identity
```

They must never be conflated.

### Source original

Private provider object/file under `source-user/` (or verified chat-upload source before provider retention).

Purpose:

- preserve what user actually supplied;
- support image inspection and subject truth/fidelity;
- retain provenance;
- provide deterministic source for allowed enhancement/transformation.

Never overwrite/destructively normalize source original.

### Retained final

Private provider object/file under `final/`.

Purpose:

- stable selected/normalized binary used by destinations;
- durable `asset_id` + SHA-256 identity;
- owns final filename/MIME/dimensions/ALT relationship.

A final may be byte-identical to source only when explicitly safe, but source provenance and final identity concepts remain distinct. Normal normalization/treatment creates a separate final object/file.

### Temporary delivery copy

Disposable object under `tmp-outbox/` made anonymously readable only for exact active external delivery.

It never becomes durable source/final identity.

## Canonical provider layout

Article:

```text
<drive-root>/<site-domain>/articles/<article-slug>/
├── source-user/
├── proposals/
└── final/
```

Social:

```text
<drive-root>/<site-domain>/social/<post-name>/
├── source-user/
├── proposals/
└── final/
```

Temporary public delivery:

```text
<drive-root>/<site-domain>/tmp-outbox/
```

Privacy invariant:

```text
source-user/ -> private
proposals/   -> private
final/       -> private
tmp-outbox/  -> public-link viewer only when configured
```

Do not broaden sharing on site/article/social/future media-library folders because outbox is public-link.

## Stable source provenance

When user source becomes durable workflow input, GitHub/content state persists enough provenance to avoid treating it later as synthetic/free-replacement material:

```yaml
source_type: user_provided
source_provider: google_drive|chat_upload
source_asset_id: <provider source identity when available>
source_original_filename: <original filename>
source_sha256: <exact original bytes when available>
source_role: use_as_is|enhance|subject_reference|inspiration_reference|composition_input
source_fidelity: strict|high|moderate|flexible
ai_treatment: none|light_correction|natural_enhancement|marketing_enhancement|creative_transformation
ai_treatment_directive: <resolved directive or null>
```

If source provider identity/hash drifts, fail closed before using it as faithful source.

Source provenance is content/workflow state, not publication authorization.

## Stable final identity

For provider-backed final:

```yaml
provider: google_drive
asset_id: <private retained final file id>
filename: <canonical filename>
sha256: <exact normalized bytes>
mime_type: <image mime>
width: <pixels>
height: <pixels>
asset_status: verified_final
```

plus ALT/title/caption/placement and applicable source provenance/reference.

Canonical stable identity is provider `asset_id` + SHA-256, not a public URL or outbox copy ID.

If same stable final `asset_id` resolves to changed bytes, fail closed.

## Source intake is not finalization

Conceptual lifecycle:

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

These states are intentionally distinct.

- source discovered does not mean verified;
- provider file existing does not mean inspected;
- source inspected does not mean selected/final;
- selected does not mean normalized;
- outbox copy does not mean destination succeeded;
- destination succeeded does not authorize another publication.

## Direct source intake UX

When user must place source image in Drive, owning workflow/`visual-source-resolve` must create/reuse/verify exact content `source-user/` folder and present:

```text
exact canonical human-readable path
+ direct clickable Drive folder link resolved from actual folder identity
```

Never guess URL or say only `put it in Drive`.

The direct link is an intake convenience, not public sharing. `source-user/` remains private.

## Chat uploads

A chat upload can be source only when actual usable image attachment is available and inspected.

When durable resume/provider use requires it, copy/retain original into private `source-user/` without destructive modification where technically possible and persist original provenance/hash when exact bytes are available.

If provider retention fails, report truthful incomplete state. Do not pretend chat preview or reconstructed screenshot is equivalent to original bytes.

## Proposals

Generated/materially transformed candidates live in private `proposals/` and are review state, not final.

The normal `exactly three A/B/C` rule applies to generated/materially transformed workflows.

An exact user source `use_as_is` with no material treatment must not generate synthetic variants merely to satisfy proposal count.

Rejected proposals may be cleaned according to review/retention policy. User source originals are not rejected proposal clutter and must not be deleted by generic proposal cleanup.

## Final normalization

`asset-ingest` resolves full-quality selected candidate/source, applies explicit output policy, writes/reuses a private `final/` object, computes SHA-256, persists metadata/provenance and re-verifies.

Normalization always writes a distinct output path/object from a user source original unless explicit safe byte-identical reuse is deliberately designed/verified. Never overwrite original.

Crop/transform policy must respect strict/high source fidelity even if technical transformation is possible.

## Delivery staging

When WordPress/social destination needs anonymous HTTP bytes:

```text
verified private final
-> copy to tmp-outbox
-> verify anonymous bytes SHA-256 == persisted final SHA-256
-> destination mutation
-> verify destination response/readback
-> delete temporary outbox copy when practical
```

Do not copy source-user original to outbox merely because it exists. Only exact verified final intended for destination is staged.

## Destination identity/idempotency

Destination idempotency binds to stable private final identity/hash and exact content/publication authorization, never outbox copy ID.

Recreating outbox copy does not create new logical final asset.

Wrong public bytes/hash fail before destination mutation.

A media delivery test never authorizes article/social publication.

## WordPress

WordPress preparation may use provider-backed finals by temporary outbox delivery. Bridge/destination metadata must bind to stable final identity/hash.

`WordPress OK` and `publish_now` gates remain unchanged by source provenance.

## Social

Social publication uses only exact `verified_final` media bound to approved text/ALT/platform/time/authorization.

User source intake, source role, enhancement review or source selection never substitute for exact social scheduling/publication authorization.

## Future reusable media library

Architecture remains compatible with private:

```text
<drive-root>/<site-domain>/media-library/
```

Future library assets still require provider resolution, real image inspection and provenance/usage/fidelity enforcement before content use. Library presence never implies unrestricted reuse or publication permission.

## Testing invariants

Validate:

- source original non-overwrite;
- source/final/outbox identities distinct;
- source/final hash drift fail-closed;
- outbox wrong-hash fail-closed;
- source-user remains private;
- direct source-user Drive path + link UX;
- generated A/B/C remains valid where applicable;
- use_as_is does not create fake A/B/C;
- existing destination idempotency/publication gates unchanged.
