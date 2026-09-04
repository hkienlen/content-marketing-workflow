# Image asset ingestion architecture

Date: 2026-09-04
Status: current architecture for the pilot/future single skill

## Decision

The single Content / Marketing skill uses Google Drive as the mandatory current provider-backed workspace for:

- private user-provided source originals when a workflow uses them;
- generated/treated visual proposals;
- retained selected/final binaries.

GitHub is the durable source of truth for exact source provenance, final-media identity, SHA-256, metadata, lifecycle state and downstream evidence. The final binary itself does not need to be committed into GitHub in normal provider-backed mode.

The internal `visual-source-resolve` capability owns user-source policy/intake before drafting. The internal `asset-ingest` capability remains the boundary that turns one explicitly human-selected final candidate/source into a durable, verified final asset.

Read together with:

```text
docs/architecture/user-provided-images.md
docs/architecture/capabilities/visual-source-resolve.md
docs/architecture/capabilities/asset-ingest.md
```

## Canonical flows

### Generated/treated candidate

```text
proposal generated/treated
-> stored in private Google Drive proposals workspace
-> human selection
-> selected proposal retrieved as real bytes
-> deterministic normalization
-> normalized final written/reused in private Drive final/
-> exact provider asset_id + SHA-256 + metadata persisted in GitHub
-> persisted state re-read/verified
```

### Exact user source / faithful derivative

```text
user source discovered/uploaded
-> original retained in private source-user/ when provider-backed retention is used
-> source verified + inspected
-> source role/fidelity/treatment/provenance persisted
-> human final choice/review
-> selected source or allowed derivative normalized without overwriting original
-> normalized final written/reused in private Drive final/
-> exact provider asset_id + SHA-256 + source provenance + metadata persisted in GitHub
-> persisted state re-read/verified
```

When a destination later needs anonymous delivery:

```text
private retained final
-> temporary copy in tmp-outbox
-> public bytes verified against persisted SHA-256
-> destination mutation
-> destination readback
-> tmp-outbox cleanup when practical
```

The end user must not manipulate Git, manually convert files or operate the outbox as part of the normal workflow.

## Source-of-truth boundary

### Google Drive

Contains:

- private user source originals;
- generated/review material;
- retained selected/final binary media;
- temporary `tmp-outbox` delivery copies.

Canonical roots:

```text
<drive-root>/<site-domain>/articles/<article-slug>/source-user/
<drive-root>/<site-domain>/articles/<article-slug>/proposals/
<drive-root>/<site-domain>/articles/<article-slug>/final/
<drive-root>/<site-domain>/social/<post-name>/source-user/
<drive-root>/<site-domain>/social/<post-name>/proposals/
<drive-root>/<site-domain>/social/<post-name>/final/
<drive-root>/<site-domain>/tmp-outbox/
```

`source-user/`, `proposals/` and `final/` remain private.

Never overwrite a user source original during treatment, crop, normalization or finalization.

### GitHub

For a durable user source, store enough provenance to recover intent/truth constraints:

```yaml
source_type: user_provided
source_provider: google_drive|chat_upload
source_asset_id: <source provider identity when available>
source_original_filename: <original filename>
source_sha256: <source bytes when available>
source_role: use_as_is|enhance|subject_reference|inspiration_reference|composition_input
source_fidelity: strict|high|moderate|flexible
ai_treatment: none|light_correction|natural_enhancement|marketing_enhancement|creative_transformation
ai_treatment_directive: <resolved directive or null>
```

For provider-backed finals:

```yaml
provider: google_drive
asset_id: <private final file id>
filename: <canonical filename>
sha256: <exact normalized bytes>
mime_type: image/webp
width: 1600
height: 900
```

plus owning ALT/title/caption/placement, validation state and source provenance/reference when applicable.

Rejected/intermediate proposals must not be mistaken for final assets merely because they exist in Drive. Source originals must not be mistaken for generated proposals or disposable intermediates.

Repository-backed binary assets remain supported through explicit `repository_file` mode.

## Lifecycle state model

Source intake:

```text
source_discovered
source_verified
source_inspected
```

Final lifecycle:

```text
proposed_or_source_ready
selected
normalized
verified_final
delivery_staged
destination_verified
```

Meanings:

- `source_discovered`: candidate user source reference/upload exists;
- `source_verified`: real full-quality usable image bytes/provider object were resolved;
- `source_inspected`: actual visual content was inspected before relying on visible facts;
- `selected`: human explicitly chose the candidate/source as the final basis;
- `normalized`: selected bytes passed validation/normalization and a deterministic manifest/hash exists;
- `verified_final`: private retained final file exists and exact provider identity/hash/metadata/provenance is persisted and reverified;
- `delivery_staged`: temporary public delivery copy exists and resolves to same expected bytes;
- `destination_verified`: external destination accepted/reused expected media and returned state was verified.

`delivery_staged` is transient and never part of stable final identity.

## Separation of concerns

### `visual-source-resolve`

Owns:

- visual policy inheritance resolution;
- pre-draft user source requirement decision;
- source-user folder create/reuse/link UX;
- actual source verification/inspection;
- source role/fidelity/treatment/provenance persistence;
- truthful `awaiting_user_images` / `source_ready` / fallback state.

It does not generate/select/finalize media.

### Owning article/social workflow

Owns:

- visual brief and placement;
- generation/treatment proposal strategy;
- whether A/B/C alternatives are appropriate under the effective source role;
- human review/selection;
- canonical final filename and content-specific output policy.

`use_as_is` with no material treatment must not be forced into synthetic A/B/C alternatives.

### `scripts/asset-ingest.py`

Owns deterministic image processing only:

- image decoding;
- EXIF orientation;
- transparency handling appropriate to output format;
- ratio validation or explicitly authorized crop;
- dimension normalization;
- WebP/JPEG/PNG encoding according to requested output extension;
- bounded quality optimization;
- SHA-256/manifest creation;
- optional base64 payload generation for compatibility paths.

It owns no credentials, provider mutations or source-policy decisions. It always writes to a distinct output path and must never overwrite the user source original.

## Output format contract

Canonical output extension selects production format:

```text
.webp        -> WEBP
.jpg/.jpeg   -> JPEG
.png         -> PNG
```

### Article defaults

Unless an article image brief declares a justified exception:

```text
1600 x 900 px
16:9 landscape
WebP
quality starts at 88
quality floor 80 for automatic optimization
soft target around 250 KiB
avoid > 300 KiB when practical, but quality wins over arbitrary hard cap
```

A near-matching human-approved file must not be silently rewritten merely because a default exists. If dimensions differ, record observed dimensions and either accept explicit exception or run authorized normalization/review.

### Social defaults

Normal standalone post:

```text
1080 x 1350 px
4:5
photo / scene humaine      -> high-quality JPEG
infographic / text / flat  -> PNG
```

Article WebP defaults must not silently override social JPG/PNG policy.

## Ratio/crop policy

- `strict` remains helper default;
- material ratio drift is rejected by default;
- `cover` is explicit, not automatic fallback;
- before `cover`, owning workflow verifies centered crop preserves composition/subject;
- strict/high source fidelity may make a crop invalid even if technically possible;
- if selected source/proposal cannot survive crop, use an allowed alternative/treatment or review exception rather than silently damaging the subject.

## Upscale policy

Do not finalize from an undersized preview/thumbnail.

Current automatic maximum upscale remains 1.25x unless owning workflow explicitly changes it.

## Size/quality policy

A universal hard byte ceiling is rejected.

1. encode at configured initial quality for lossy formats;
2. if above soft target, reduce quality gradually;
3. stop at configured quality floor;
4. if still above target, preserve acceptable quality and record `target_bytes_met=false`;
5. for PNG, optimize losslessly;
6. fail only when explicit hard maximum was configured and exceeded.

## Stable provider identity and source identity

The retained final private file ID is stable final `asset_id`.

For unchanged final bytes:

```text
same asset_id + same sha256 -> same final asset
```

A user source's `source_asset_id` is a distinct provenance identity and never substitutes for final `asset_id` unless the provider object itself is explicitly reused as final and that behavior is safe/verified. Normal provider-backed processing keeps source original and final derivative as distinct objects.

If the same persisted source/final provider identity resolves to changed bytes, fail closed.

A temporary outbox copy ID is transport identity only.

## Replacement protection

Before replacing verified final:

- same stable final identity + same SHA-256 -> verified no-op;
- different selected final + explicit human replacement intent -> normalize/write new final and persist new identity/hash/provenance;
- different final without explicit replacement intent -> stop.

Never mutate an already validated final or a user source original behind existing durable state.

## `tmp-outbox` staging

`asset-ingest` does not need public delivery during finalization.

Downstream WordPress/social workflows may request:

```text
verified_final
-> copy to tmp-outbox
-> anonymous fetch
-> SHA-256 verification
-> external destination
```

The outbox copy is disposable. Source originals and retained private finals are not.

## Drive retention

Rejected generated proposals may be retained during active review/debugging and later cleaned. User source originals used as durable provenance are not rejected proposal clutter and must not be deleted by generic proposal cleanup.

Temporary outbox copies should be cleaned after verified delivery when practical.

## Generic reuse

Normalization is content-type neutral. Owning article/social capability supplies filename, dimensions, format and quality policy. Visual-source intake remains profession-neutral and supports user sources for products, craft work, portraits, places, portfolios or other real subjects.

Provider interface remains open to current `google_drive` and future `dropbox` without changing article/social semantic contracts.

## Validation status

As of 2026-09-04:

- deterministic WebP/JPEG/PNG normalization remains the existing tested basis;
- Google Drive public-link transport through `tmp-outbox` remains validated end to end;
- wrong-hash behavior remains fail-closed;
- WordPress Bridge `media_upsert` creation/idempotent reuse remain validated;
- provider-backed final media remains normal architecture;
- user-provided source policy/provenance/pre-draft workflow is now a generic architecture requirement and must pass its dedicated resolver/static tests before the next productization freeze;
- repository-backed binary mode remains compatibility only.
