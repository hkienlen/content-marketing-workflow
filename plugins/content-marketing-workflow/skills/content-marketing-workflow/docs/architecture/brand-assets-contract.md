# Brand assets and logo application contract

Date: 2026-09-06
Status: normative architecture contract

## Purpose

This contract defines how Content Marketing Workflow stores, resolves, applies and verifies user-owned brand assets, especially logos, without embedding one user's brand into the generic Skill.

The generic Skill owns behavior. Concrete logos, project choices and user directives are user/project data.

## Primary invariant

```text
skill package = generic brand/media rules
user project  = actual logo files + logo policy + rich visual directives
```

Never copy a pilot user's logo, palette, placement rule or identity into generic defaults.

## Independent article and social logo policy

```yaml
visual_identity:
  logo_policy:
    article: always|auto|never
    social: always|auto|never
```

Do not infer one channel from the other. A valid configuration is:

```yaml
logo_policy:
  article: never
  social: always
```

Semantics:

- `always`: official verified logo required unless a content-local user override changes that item;
- `auto`: owning workflow may include or omit branding, but any included logo must be official;
- `never`: project logo must be absent unless a content-local user override changes that item.

## Logo asset intake and workspace

Prefer original high-quality user files. Ask for `light` and `dark` variants when available while accepting one official logo.

Conceptual registry:

```yaml
visual_identity:
  logo_assets:
    primary: <optional verified asset>
    light: <optional verified asset>
    dark: <optional verified asset>
```

Each durable asset records provider-qualified identity, filename, SHA-256, MIME, dimensions and verification timestamp when available.

Brand assets stay private under the selected provider, conceptually:

```text
<provider-root>/<site-domain>/brand/
└── logos/
    ├── primary/
    ├── light/
    └── dark/
```

They are not `tmp-outbox` delivery material.

## Provider namespace compatibility

A logo asset belongs to its recorded provider namespace. When `cloud_media_storage.provider` is active, only logos verified in that provider namespace are immediately usable.

After a Google Drive/Dropbox switch:

- never reinterpret the old asset ID under the new provider;
- require explicit migration/rebinding and exact hash verification;
- expose a provider-rebinding blocker;
- never mark `always` ready merely because unrelated logo metadata exists.

## Integrity of official brand assets

An official logo is a composition asset, not a generative suggestion.

Never:

- redraw or recreate the logo approximately with image generation;
- ask the image model to invent missing letters/symbols;
- stretch or distort proportions;
- recolor unless explicitly authorized;
- separate/rearrange components unless explicitly authorized;
- overwrite the user-provided original.

A generated pseudo-logo that resembles the brand is not official branding and must not be accepted merely because a human liked the surrounding image.

## Clean-base invariant

When the effective policy requires official branding, the base visual used for deterministic composition must be clean of the project's logo and of generated/unverified substitutes intended to stand for that logo.

Generation briefs should explicitly request **no project logo, no project brand signature and no approximation of them** while optionally reserving composition space.

Before a generated base is retained for branding, inspect it. If it contains an accidental/generated project logo or plausible substitute:

- reject/regenerate it; or
- perform the narrowest safe repair when appropriate;
- do not call the contaminated base a selectable review candidate.

This is an integrity gate, not a creative preference.

## Deterministic composition implementation

CMW bundles:

```text
scripts/logo-compose.py
```

The helper:

- requires expected official logo SHA-256 from durable project state;
- refuses a different logo binary;
- never overwrites base or official source;
- resizes proportionally only;
- alpha-composites the exact official asset onto a separate derivative;
- requires explicit position/size resolved by the effective contract;
- emits base/logo/output hashes and exact composition coordinates.

A generative redraw or approximate image edit is not an equivalent fallback.

## Review-ready branding gate

For generated/materially transformed work, **human review is a brand-integrity gate, not only finalization**.

When `logo_application=always`:

```text
clean base
-> exact deterministic official-logo composition
-> hash/evidence validation
-> durable review candidate
-> human selection
-> finalization
```

The durable/selectable candidate shown to the user must already be the officially branded derivative. A raw generator output, an unbranded base or a base with generated branding may be discussed as an internal/concept draft, but it must not become selectable A/B/C, must not receive durable `selected` state, and must not make combined review `fully_approved`.

CMW bundles:

```text
scripts/visual-review-gate.py
```

For `logo_application=always`, use it or an equivalent deterministic validator before claiming a review package is ready. The validator binds:

- frozen `contract_revision`;
- clean-base SHA-256 and inspection evidence;
- exact official-logo SHA-256;
- deterministic composition manifest;
- branded review-output SHA-256.

If a compatible official logo or deterministic composition path is unavailable, base exploration may continue, but durable/selectable visual review remains blocked. This closes the late-failure case where a user approves a generated logo and only later learns the visual cannot be finalized.

## Generation and composition order

Normal generated `always` workflow:

```text
resolve/freeze effective visual contract
-> generate internal bases with no project branding
-> inspect/reject contaminated bases
-> retain strong clean bases
-> compose exact official logo on each
-> validate review readiness
-> persist/present branded review candidates
-> human selection of branded candidate hash
-> normalize/finalize
-> verified_final
```

When both `light` and `dark` variants exist, choose the strongest legibility/contrast unless user guidelines say otherwise. Do not synthesize a missing variant.

## Placement defaults

Absent a user rule, place the logo with comfortable margins, secondary to the principal subject/message, readable on target device, coherent within a short series when useful, and without obscuring essential content.

Do not impose one universal bottom-right/bottom-center position as a generic product rule.

## Effective-policy states

Resolve at least:

```yaml
logo_application: always|auto|never
logo_policy_source: project_article|project_social|content_local_override|legacy_unconfigured
active_media_provider: google_drive|dropbox|null
compatible_logo_assets: {}
mismatched_logo_assets: {}
provider_rebinding_required: true|false
logo_asset_available: true|false
logo_status: ready|awaiting_brand_asset
```

For `always`, missing compatible logo blocks review-ready branding and finalization, though drafting/base exploration may continue. For `auto`, missing logo means branding cannot be chosen. For `never`, no logo asset is required.

## Content-local override

One-off instructions such as `For this post only, no logo` belong to the owning content item and do not rewrite project defaults.

## Recovery of a previously selected non-compliant visual

If a selected/review-approved visual is later found to contain generated/unverified branding:

1. preserve approved text and the user's conceptual visual preference;
2. remove only the durable technical claim that the visual is selectable/finalizable as-is;
3. use an exact clean pre-logo base if one really exists;
4. if no exact clean base exists, never claim the same image can be recovered exactly; repair/regenerate as narrowly as possible while preserving the selected concept;
5. because changed pixels create a new visual identity/hash, present the repaired officially branded result for targeted human confirmation;
6. do not force a full new A/B/C round unless the user requests it or the repair materially changes the creative concept.

This recovery is non-retroactive for already verified/published historical finals unless the user explicitly reopens them.

## Replacement/versioning

Replacing a logo creates a new verified brand-asset identity/version. Do not silently rewrite historical `verified_final` media or publication authorizations bound to exact hashes.

## Final verification

Before `verified_final`, verify:

1. article/social policy resolved independently;
2. content-local override persisted/applied;
3. logo provider namespace matches active provider or was explicitly rebound;
4. `always` uses an exact official verified logo;
5. `never` has no project logo;
6. `auto` includes only official branding if used;
7. logo integrity preserved;
8. actual final bytes/dimensions/hash verified;
9. logo identity/version recoverable when present;
10. exact `contract_revision` includes logo application and logo asset identity;
11. when `always`, selected review evidence already passed the review-ready branding gate or an equivalent verified migration/recovery path.

## References

- `docs/architecture/visual-generation-contract.md`
- `docs/architecture/user-profile-data-contract.md`
- `docs/architecture/capabilities/visual-configure.md`
- `docs/architecture/capabilities/visual-source-resolve.md`
- `docs/architecture/capabilities/social-create-visual.md`
- `docs/architecture/social-post-review-loop.md`
- `docs/architecture/capabilities/asset-ingest.md`
- `docs/architecture/google-drive-workspace.md`
- `docs/architecture/dropbox-workspace.md`
- `scripts/logo-compose.py`
- `scripts/visual-review-gate.py`
