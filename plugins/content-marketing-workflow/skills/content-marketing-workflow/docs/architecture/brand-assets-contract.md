# Brand assets and logo application contract

Date: 2026-09-06
Status: normative architecture contract

## Purpose

This contract defines how Content Marketing Workflow stores, resolves, applies and verifies user-owned brand assets, especially logos, without embedding one user's brand into the generic Skill.

The generic Skill owns the behavior. Concrete logos, brand files, project choices and user directives are user/project data.

## Primary invariant

```text
skill package
= generic brand/media rules

user project
= actual logo files + logo policy + rich visual directives
```

Never copy a pilot user's logo, palette, identity, placement rule or brand-specific wording into generic defaults.

## Independent article and social logo policy

Logo use is an explicit project preference and **article and social are two independent choices**.

Canonical structured state:

```yaml
visual_identity:
  logo_policy:
    article: always|auto|never
    social: always|auto|never
```

Do not infer one channel from the other.

Valid examples include:

```yaml
# Articles without logo, social posts with logo.
logo_policy:
  article: never
  social: always
```

```yaml
# Logo chosen case by case for articles, never on social posts.
logo_policy:
  article: auto
  social: never
```

Semantics:

- `always`: every final visual in that channel must contain an official verified logo asset unless an explicit content-local user override changes that one item;
- `auto`: the owning visual workflow may use or omit the logo according to composition/context and user visual guidelines; a logo must never be invented when no official asset exists;
- `never`: the final visual must not contain the project's logo unless an explicit content-local user override changes that one item.

A change to `social` must not modify `article`, and a change to `article` must not modify `social`.

## Logo asset intake

When the user has a logo, prefer the original high-quality file. Ask for both variants when available:

```text
light -> intended for dark backgrounds
dark  -> intended for light backgrounds
```

A single logo is valid. Light/dark variants are recommended, not mandatory.

Supported conceptual registry:

```yaml
visual_identity:
  logo_assets:
    primary: <optional verified asset>
    light: <optional verified asset>
    dark: <optional verified asset>
```

Each durable logo asset records provider-qualified identity and verification metadata, for example:

```yaml
provider: google_drive|dropbox
asset_id: <provider identity/reference>
filename: <original/canonical filename>
sha256: <64 lowercase hex when exact bytes are available>
mime_type: image/png
width: <positive integer>
height: <positive integer>
verified_at: <timestamp>
```

PNG with transparency is preferred when appropriate, but the workflow must preserve a valid official source rather than convert merely for convention.

## Brand workspace

Brand assets are private provider-backed project assets.

Provider-neutral logical layout:

```text
<provider-root>/<site-domain>/brand/
└── logos/
    ├── primary/
    ├── light/
    └── dark/
```

Adapters may map this differently as long as stable provider identity is preserved. The active project profile may persist `brand_ref` and exact logo asset references.

Brand assets are not `tmp-outbox` delivery material and are not made public merely because they are used in public content.

## Provider namespace compatibility

A logo asset reference belongs to the provider namespace recorded in that asset.

When the project has an active `cloud_media_storage.provider`, only logo assets verified in that same provider namespace are considered immediately usable for finalization.

If the profile still points to Google Drive logo assets after switching the project to Dropbox, or vice versa:

- do not reinterpret the old asset ID under the new provider;
- return/persist a provider-rebinding blocker;
- migrate/rebind the official logo explicitly with exact hash verification;
- do not mark `logo_application=always` ready merely because some logo metadata exists.

The deterministic resolver exposes this distinction through compatible/mismatched logo assets and `provider_rebinding_required`.

## Integrity of official brand assets

An official logo is a composition asset, not a generative suggestion.

Never:

- redraw or recreate the logo approximately with image generation;
- ask the image model to invent missing letters/symbols;
- stretch or distort proportions;
- recolor unless the user explicitly supplies/authorizes a derived variant;
- separate or rearrange logo components unless explicitly authorized;
- overwrite the user-provided original.

Prefer exact composition from the verified logo bytes after or alongside base-image generation.

## Deterministic composition implementation

CMW bundles a credential-free deterministic compositor:

```text
scripts/logo-compose.py
```

When the runtime can execute the bundled helper, use it for official-logo composition. The helper:

- requires the expected official logo SHA-256 from durable project state;
- refuses a different logo binary;
- never overwrites the base image or the official logo source;
- resizes proportionally only;
- alpha-composites the exact verified logo asset onto a separate derivative;
- requires an explicit placement and size chosen by the effective visual contract rather than imposing one universal creative position;
- emits base/logo/output hashes and exact composition coordinates for durable evidence.

Example execution shape:

```text
python3 scripts/logo-compose.py \
  --base <candidate> \
  --logo <verified-official-logo> \
  --expected-logo-sha256 <profile-sha256> \
  --position bottom-right \
  --margin-px <resolved-margin> \
  --logo-width-ratio <resolved-ratio> \
  --output <branded-derivative>
```

The example position is illustrative only; it is not a generic placement default.

If the helper is unavailable, another deterministic composition path is acceptable only if it preserves the same integrity guarantees and verifies the exact official asset identity/hash. A generative redraw or approximate image edit is not an equivalent fallback.

When `logo_application=always` and no safe deterministic composition path is available, finalization remains blocked rather than silently accepting an AI-recreated logo.

## Generation and composition order

Normal generated workflow:

```text
resolve effective visual contract
-> generate/select base visual candidates
-> compose exact official logo when effective policy requires/allows it
-> present reviewable candidate(s)
-> human selection
-> normalize/finalize
-> verify logo presence/absence against effective policy
-> verified_final
```

It is acceptable to reserve a safe logo area in the generation brief, but the logo itself should normally be applied deterministically from the official asset rather than rendered by the generative model.

When review requires seeing the branded result, compose the exact logo on review candidates before presentation. Do not call an unbranded candidate final when `logo_application=always`.

## Variant selection

When both `light` and `dark` variants exist, choose the one with the strongest legibility/contrast for the actual composition unless the user's visual guidelines specify another rule.

When only one valid variant exists, use it only when it remains legible and compliant. Do not synthesize the missing variant. If `always` cannot be satisfied legibly with available official assets, report a brand-asset blocker rather than fabricating a replacement.

## Placement defaults

Placement is a creative default and is overridable by user guidelines.

Absent a user rule, place the logo:

- with comfortable edge/safe-area margins;
- secondary to the principal message/subject;
- at a size readable on the target device without dominating the visual;
- in a stable position within a coherent short series when that improves recognition;
- without obscuring essential content.

Do not impose one universal bottom-right/bottom-center position as a generic product rule.

## Effective-policy states

For each content item resolve at least:

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

If `logo_application=always` and no usable official logo asset is available:

- content drafting may continue when otherwise allowed;
- base visual generation may continue when useful;
- the final visual must not reach `verified_final`;
- publication that requires that final remains blocked;
- ask for/locate/rebind the official logo instead of generating one.

For `auto`, lack of a compatible logo asset does not itself block finalization; the workflow simply cannot choose to apply a logo until an official asset exists in the active provider namespace.

For `never`, no logo asset is required for that content item.

## Content-local override

A user may override logo application for one article/post without changing project defaults, for example:

```text
"For this post only, no logo."
"For this article only, add my logo."
```

Persist the override with the owning content state and bind it to the visual review/final revision. Do not rewrite `visual_identity.logo_policy` unless the user clearly asks for future/permanent behavior.

## Replacement/versioning

Replacing a logo creates a new verified brand-asset identity/version. Do not silently rewrite already `verified_final` media.

New visual generations/revisions use the current effective brand contract. Existing validated or published media remain bound to their historical final hash unless the user explicitly requests a retroactive replacement workflow.

Persist enough contract/version evidence with a content review/final snapshot to explain which logo policy and asset identity produced that final.

## Final verification

Before `asset-ingest`/owning workflow declares a final visual `verified_final`, verify:

1. effective article/social logo policy was resolved independently;
2. any content-local override is persisted and applied;
3. any logo asset used belongs to the active provider namespace or was explicitly migrated/rebound and reverified;
4. `always` -> an exact official verified logo is visibly present and legible;
5. `never` -> project logo is absent;
6. `auto` -> any included logo is an official verified asset;
7. logo proportions/colors/integrity are preserved;
8. actual final bytes, dimensions and hash are verified;
9. logo asset identity/version used for the final is recoverable when a logo is present;
10. the durable effective visual `contract_revision` includes the selected logo application and logo asset identity.

## References

- `docs/architecture/visual-generation-contract.md`
- `docs/architecture/user-profile-data-contract.md`
- `docs/architecture/schemas/user-profile.schema.json`
- `docs/architecture/capabilities/visual-configure.md`
- `docs/architecture/capabilities/visual-source-resolve.md`
- `docs/architecture/capabilities/asset-ingest.md`
- `docs/architecture/google-drive-workspace.md`
- `docs/architecture/dropbox-workspace.md`
- `scripts/logo-compose.py`
