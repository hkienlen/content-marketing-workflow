# Internal capability: asset-ingest

Date: 2026-09-05
Status: current implementation contract

## Purpose

`asset-ingest` is an internal capability of the single installable Content / Marketing skill.

It turns one explicitly human-selected visual candidate into one durable, verified final media asset without requiring the end user to manipulate files, Git, branches or image conversion manually.

A selected candidate may be:

- a generated/treated proposal;
- a verified user-provided source intended `use_as_is`;
- a compliant derivative generated from a verified user source.

In normal provider-backed mode, the final binary is retained in the configured private external-media `final/` workspace and GitHub stores its exact stable identity, SHA-256, metadata and source provenance when applicable. A Git binary commit is not required for normal completion.

It is not a separately installable skill and it does not choose/generate images or decide whether a user source is required before drafting. That earlier boundary is `visual-source-resolve`.

## Capability contract

```yaml
name: asset-ingest
purpose: Normalize one explicitly selected visual candidate, retain/reuse it in the configured provider final workspace, persist exact final identity/metadata/source provenance in GitHub, and verify durable state.
availability: core
feature_gate: null
mode: mutating

prerequisites:
  - GitHub repository access is verified
  - selected cloud_media_storage provider is operational
  - selected provider workspace is verified according to google-drive-workspace.md or dropbox-workspace.md
  - human selection of exact final candidate/source is explicit
  - selected candidate resolves to actual full-quality bytes/file
  - user-provided sources were verified/inspected through visual-source-resolve when applicable
  - active content item and canonical target filename are known
  - owning workflow supplies target dimensions/format policy
  - active content branch exists when content-specific metadata belongs there
  - replacement intent is explicit when a different final asset is already verified

mandatory_context:
  - AGENTS.md
  - docs/architecture/persistence-contract.md
  - docs/architecture/github-transparency.md
  - docs/architecture/capability-contract-template.md
  - docs/architecture/testing-policy.md
  - docs/architecture/runtime-compatibility-matrix.md
  - docs/architecture/google-drive-workspace.md
  - docs/architecture/dropbox-workspace.md
  - docs/architecture/media-delivery-architecture.md
  - docs/architecture/user-provided-images.md
  - docs/architecture/image-asset-ingestion.md
  - docs/architecture/capabilities/visual-source-resolve.md
  - active content/image brief and latest human review decision
  - active source provenance/policy state when applicable
  - active branch/PR state

reads:
  - selected provider proposal or verified user source bytes/reference
  - canonical image brief
  - effective source role/fidelity/treatment/provenance when applicable
  - existing private final provider asset when present
  - existing durable GitHub media metadata/state
  - active content branch/PR state

writes:
  - normalized selected final asset in selected provider private final workspace
  - owning content media metadata/source-provenance relationship in GitHub
  - tracking state when used by active workflow

persists:
  - human selection identity
  - provider (`google_drive` or `dropbox`)
  - stable private-final asset_id/reference in that provider namespace
  - canonical filename
  - normalized dimensions/format/size/quality/SHA-256
  - user-source provenance snapshot/reference when applicable
  - ALT/title/caption/placement when owned by content workflow
  - verified lifecycle state
  - Git commit identity for durable metadata/state mutation

external_side_effects:
  - read selected asset/source from configured provider workspace
  - write/reuse final binary in selected provider private final workspace
  - update GitHub durable content/state metadata
  - never overwrite user source original

human_approval:
  - explicit final candidate/source selection before finalization
  - explicit replacement intent before replacing a different verified final asset
  - no separate GitHub merge approval; owning workflow performs later GitHub integration automatically when business/content gates are satisfied

validation:
  - selected source/candidate bytes are intended full-quality input, not thumbnail/preview
  - source decodes successfully
  - user-source provenance resolves to verified inspected source when applicable
  - original user source object/file remains unchanged and distinct from derivative final unless explicit safe reuse is designed/verified
  - strict/high source fidelity constraints are not violated by crop/normalization/treatment
  - orientation is normalized
  - target ratio/dimensions conform or explicit reviewed exception/crop policy applies
  - output format matches owning workflow policy
  - canonical filename comes from durable metadata, not temporary generation/source name
  - rejected candidates never become verified finals
  - private final provider file is re-read/resolved and exact SHA-256 is verified
  - persisted GitHub final metadata/provenance is re-read and matches provider final/source relationship
  - persisted provider name matches the actual selected project provider and provider identity namespace

completion_conditions:
  - selected source/candidate resolved
  - normalization manifest produced or existing accepted final inspected
  - original user source remains preserved when applicable
  - private final provider asset exists in the selected provider
  - stable provider + asset_id/reference + exact SHA-256 + canonical metadata + applicable source provenance persisted in GitHub
  - provider final and GitHub metadata reverified
  - owning content/task tracking synchronized when required
  - lifecycle state reaches verified_final
  - this capability does not create a user merge gate; later merge is transparent owning-workflow plumbing

next_actions:
  - owning article/social review synchronization
  - automatic owning-workflow GitHub integration when required gates are satisfied
  - downstream delivery staging only when an external destination requires it
```

## Lifecycle

User source intake may precede this capability:

```text
source_discovered -> source_verified -> source_inspected
```

Finalization:

```text
proposal_or_source_ready -> selected -> normalized -> verified_final
```

Downstream delivery may add:

```text
verified_final -> delivery_staged -> destination_verified
```

`source_inspected`, `selected`, `verified_final` and `delivery_staged` are distinct states.

## Provider source and final identity

Normal providers are Google Drive and Dropbox. Use the provider selected in durable project state and never silently switch providers during ingest.

Provider-neutral article workspace:

```text
<provider-root>/<site-domain>/articles/<article-slug>/
├── source-user/
├── proposals/
└── final/
```

Provider-neutral social workspace:

```text
<provider-root>/<site-domain>/social/<post-name>/
├── source-user/
├── proposals/
└── final/
```

Provider-specific mappings and delivery semantics are defined by `google-drive-workspace.md` and `dropbox-workspace.md`.

Do not ingest a UI screenshot, thumbnail or reconstructed chat preview when full generated/user-source asset exists.

If provider cannot supply selected full-quality bytes, preserve highest truthful state and report finalization blocked. Do not silently substitute another binary source or another provider.

## User-source provenance

When selected/final candidate is based on a user-provided source, persist at least the fields that are known/required from the source workflow:

```yaml
source:
  source_type: user_provided
  source_provider: google_drive|dropbox|chat_upload
  source_asset_id: <provider source id/reference when available>
  source_original_filename: <original filename>
  source_sha256: <original bytes when available>
  source_role: use_as_is|enhance|subject_reference|inspiration_reference|composition_input
  source_fidelity: strict|high|moderate|flexible
  ai_treatment: none|light_correction|natural_enhancement|marketing_enhancement|creative_transformation
  ai_treatment_directive: <resolved directive or null>
```

The final asset record remains separate:

```yaml
media:
  provider: google_drive|dropbox
  asset_id: <private-final-provider-identity>
  filename: <canonical filename>
  sha256: <64 lowercase hex>
  mime_type: image/webp
  width: 1600
  height: 900
  asset_status: verified_final
```

Provider is part of the identity namespace. A persisted asset reference from one provider must never be interpreted as an equivalent reference in the other provider.

For `use_as_is`, normalization/export may create a derivative final. Preserve original source identity/provenance and never overwrite its bytes merely to match final format/dimensions.

## Canonical filename

Article final names remain SEO-oriented. Social filenames follow social policy. Do not derive final names from temporary proposal/source filenames, while retaining `source_original_filename` separately for provenance.

## Normalization helper

Use:

```text
scripts/asset-ingest.py
```

The helper is credential-free and deterministic. Destination filename extension selects WEBP/JPEG/PNG.

### Article defaults

```text
1600 x 900
16:9
WebP
initial quality 88
minimum automatic quality 80
soft target 250 KiB
strict ratio by default
maximum automatic upscale 1.25x
```

### Social policy input

```text
1080 x 1350
4:5
photo -> JPEG
text/infographic/flat -> PNG
```

Social JPG/PNG must not become WebP merely because WebP is article default.

## Crop/fidelity safety

Default `--crop strict` rejects material ratio mismatch.

`--crop cover` may be used only after owning workflow verifies centered crop does not damage composition/content/real subject. Strict/high source fidelity is an additional veto: a technically valid crop is not allowed if it materially misrepresents or removes required subject information.

If selected source/candidate cannot survive required output policy, review an exception or select/generate another compliant candidate. Never silently rewrite the original.

## Size policy

`--target-bytes` is soft. JPEG/WebP quality reduces only to configured minimum; PNG is losslessly optimized. If still above soft target, valid output may remain with `target_bytes_met=false` unless explicit hard maximum exists.

## Idempotency and replacement protection

Before mutating verified final:

1. resolve existing durable media/source state;
2. if same provider + final `asset_id` + SHA-256 is already verified, no-op;
3. if same source provenance is reused and final bytes are unchanged, reuse existing final when valid;
4. if different final was explicitly selected as replacement, write/reuse new final and persist new identity/hash/provenance;
5. if the selected project provider differs from the existing final provider, require explicit provider migration/rebinding rather than silent reuse;
6. otherwise stop instead of silently replacing validated final.

If persisted source or final provider object resolves to different bytes than its stored SHA-256, fail closed.

A source original is immutable workflow input: final replacement never modifies it.

## GitHub mutation

Normal provider-backed `asset-ingest` writes textual durable metadata/state to GitHub, not media binary. Use existing active branch/PR. Persist smallest coherent state update and verify it after write. Do not ask user to approve commit/PR/merge.

`repository_file` remains compatibility mode.

## Delivery staging is separate

Do not make `source-user/` or private final public.

When WordPress/social requires anonymous HTTP bytes:

```text
verified private final
-> copy to selected provider tmp-outbox
-> create/use provider-supported public read-only delivery reference
-> verify public bytes match persisted SHA-256
-> perform exact destination operation using stable final identity
-> verify destination result
-> remove temporary outbox copy/link when practical
```

Source media is not publication authorization.

## Testing

Existing deterministic normalization tests remain, plus user-source/provider workflow tests cover:

- both Google Drive and Dropbox provider identities;
- source provenance retention;
- source original non-overwrite invariant;
- strict/high fidelity crop/treatment guards at owning workflow boundary;
- source/final identity separation;
- `use_as_is` finalization without fake generated alternatives;
- provider identity/hash drift fail-closed behavior;
- provider switching requires explicit migration/rebinding.

## User-facing invariant

Normal experience may be:

```text
user photo supplied/located
-> source verified + inspected
-> user sees exact source or compliant alternatives/treatments
-> user selects/approves final basis
-> system normalizes/verifies to separate private final in selected cloud provider
-> source original remains intact
-> system persists provider-qualified source provenance + final identity/hash/metadata
-> user reviews result
```

The user is never asked to download, convert, rename, `git add`, commit, push, approve PR/merge or manually move media into WordPress/social destinations.
