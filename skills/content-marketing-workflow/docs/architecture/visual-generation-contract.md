# Visual generation contract

Date: 2026-09-06
Status: normative architecture contract

## Purpose

This contract defines generic creative defaults, user-directive precedence and generation/review behavior for article and social visuals managed by Content Marketing Workflow.

## Authority layers and conflict resolution

```text
1. non-overridable workflow/integrity/safety invariants
2. explicit content-local user directives
3. channel-specific user directives
4. project-global user visual directives
5. generic CMW creative defaults
6. executor interpretation
```

User directives override conflicting creative defaults, but never integrity/truthfulness invariants such as exact provider identity, source preservation, human-selection truth, verified-final truth, exact official-logo identity or publication authorization.

## Durable user authority

Structured operational settings belong in `user-data/profile.json`, including `visual_preferences` and `visual_identity`. Rich project creative directives belong in the user-owned authority normally referenced as:

```text
strategy/visual-guidelines.md
```

One-off instructions stay local to the owning content item.

## Effective visual contract

Before durable generation/review, resolve and freeze at least:

```yaml
content_kind: article|social
source_policy: <resolved visual_preferences policy>
visual_guidelines_path: <user authority or null>
applied_user_directives:
  project_global: []
  channel: []
  content_local: []
logo_application: always|auto|never
logo_asset_identity: <when applicable>
generic_defaults_applied: []
contract_revision: sha256:<64 lowercase hex>
```

Every durably persisted proposal/review round and every `verified_final` must have a `contract_revision`; that revision is deterministic. Use `scripts/visual-contract-freeze.py` or an equivalent canonical implementation. Material contract changes create a new revision; unchanged A/B/C in one round share the same revision.

## Generator-input boundary

The complete effective visual contract is an orchestration/finalization authority. **It is not a generator prompt.**

For generated work, derive the smallest safe **base-generation brief** needed by the image model. When project branding will be applied later, the generator input must not expose or inherit:

- official logo bytes, filename, provider ID, asset ID or SHA-256;
- `logo_application` or logo-variant identity as a positive generation instruction;
- user/project wording such as “put our logo bottom-right”;
- deterministic-composition instructions that belong to the compositor stage.

Instead, translate brand-placement preferences into neutral `reserved_composition_space` guidance and add an explicit negative constraint excluding project logos, brand signatures, pseudo-logos and watermarks.

CMW bundles:

```text
scripts/base-generation-brief.py
```

Use it or an equivalent fail-closed derivation before sending a branded-social base to image generation. The helper intentionally carries the frozen `contract_revision` as traceability but does not copy logo identity/provider/hash data into generator input.

## Drafts are not automatically review candidates

Generated/materially transformed workflows distinguish:

```text
internal/base draft
= exploratory/generated artifact before all pre-review invariants are satisfied

review candidate
= persisted/recoverable artifact eligible for durable human selection
= already bound to exact contract_revision
= already satisfies every invariant that can be satisfied before selection
```

A user may discuss a draft, but the workflow must not record `selected`, `fully_approved` or equivalent durable visual approval against a draft that has not passed the relevant review-ready gates.

For social visuals with `logo_application=always`, exact official-logo composition is such a gate. Read `docs/architecture/brand-assets-contract.md` and `docs/architecture/capabilities/social-create-visual.md`.

## Generic article creative defaults

Unless overridden by user/project/article directives:

- prefer realistic, credible, professional visuals over generic synthetic-looking imagery;
- photography is a strong default, not mandatory;
- avoid repetitive AI clichés and literal over-explanation;
- support editorial idea/ambience instead of summarizing the whole article;
- enforce real diversity across subject, location, framing, people/no-people, action, objects, viewpoint, light and metaphor;
- do not put a person in every image;
- prefer natural credible people over caricatured stress/failure/enthusiasm;
- target 16:9 landscape, 1600 x 900 px and WebP final when compatible;
- do not embed marketing/headline text in photographic article images by default;
- generated/materially transformed work normally presents exactly three genuinely reviewable candidates per requested image.

## Generic social creative defaults

Unless overridden:

```text
visual = hook / immediate tension
post text = development
linked article = deeper treatment when relevant
```

Defaults:

- mobile-first readability;
- 4:5 / 1080 x 1350 when one master format is appropriate;
- short visible hook only when useful;
- one principal visible idea, not a paragraph;
- JPEG for photographic scenes, PNG for infographic/flat/text-heavy designs when appropriate;
- credible people/places/objects rather than generic corporate stock aesthetics;
- alternate visual families across a campaign;
- real rather than superficial variation;
- no generic palette or logo placement imposed by CMW;
- generated/materially transformed social work presents exactly three genuinely distinct **review-ready** A/B/C candidates.

## Diversity and repetition control

Inspect recoverable recent finals/briefs when useful. Either repetition is intentional as a short coherent series or the new visual differs materially on several dimensions. Do not impose demographic quotas image by image.

## Text in images

Text is optional. When used, keep it short/readable, preserve exact wording, avoid sensationalist phrasing, do not invent third-party branding, and ensure important factual information also exists in accessible page/post text when required.

## Brand/logo integration

Logo behavior is resolved from `visual_identity.logo_policy` independently for article/social plus any local override.

The generative model may reserve space, but official branding must not be recreated by generation. For `logo_application=always`, generation uses a brand-isolated base-generation brief; contaminated pure-AI bases are rejected/regenerated before official deterministic composition.

## Proposal workflow

For generated/materially transformed visuals:

```text
resolve effective visual contract
-> freeze mandatory contract_revision
-> prepare exact creative briefs
-> derive brand-isolated base-generation briefs when branding will be composed later
-> generate internal/base drafts as needed
-> inspect/reject off-brief, duplicate, malformed or integrity-incompatible drafts
-> satisfy channel-specific pre-review gates
-> retain exactly three strong review-ready candidates
-> persist/recover candidates through configured cloud provider
-> present grouped human review
```

For social `logo_application=always`, the channel-specific pre-review gate is:

```text
brand-isolated base-generation brief
-> clean base with no generated project branding
-> deterministic exact official-logo composition
-> visual-review-gate validation
-> review candidate
```

For a newly generated disposable pure-AI base, accidental pseudo-branding is normally handled by **reject/regenerate**, not a multi-step generative logo-removal edit. Targeted repair is reserved for cases where preserving source pixels has real value, such as user-owned/source-dependent media or recovery of an already selected concept.

Use `scripts/visual-review-gate.py` or an equivalent deterministic validator before claiming a durable/selectable review package is ready.

For exact `use_as_is + ai_treatment:none`, present the exact source/final candidate instead of fabricating A/B/C, subject to applicable branding policy.

## Targeted review and freeze

Human review may approve/reject/revise text and visuals independently. Preserve approved components during targeted revisions. A new generation round preserves unaffected approved source/text/logo policy unless reopened. Effective-contract changes require a new frozen revision.

When a previously selected visual later fails a pre-review invariant (for example a generated logo was baked into the pixels), preserve approved text and conceptual creative preference but revoke the technical durable visual-selection claim. Repair/regenerate only what is necessary and ask for targeted re-confirmation when pixels change. Do not falsely claim exact pixel recovery when no clean source exists.

## Free user directives

Arbitrary permanent or local visual instructions are supported, including styles, people/no-people, environments, objects/metaphors, palette restrictions, realism, text density, placement, prohibited clichés, readability and campaign exceptions. Persist permanent directives in project visual guidelines; keep one-off directives local.

A branding directive may shape the final composition, but only its **creative non-brand consequence** (for example “keep the lower-right area clear”) crosses into the base-generation brief. The image model is not given the actual project-logo instruction.

## Finalization and historical binding

A selected final records enough effective-contract evidence to explain source, directives, logo outcome and logo identity when present. Every durable final re-verifies its exact `contract_revision`.

Changing project guidelines or replacing a logo does not silently mutate historical `verified_final` assets or scheduled/publication authorizations bound to exact media hashes.

## References

- `docs/architecture/brand-assets-contract.md`
- `docs/architecture/user-profile-data-contract.md`
- `docs/architecture/user-provided-images.md`
- `docs/architecture/capabilities/visual-configure.md`
- `docs/architecture/capabilities/visual-source-resolve.md`
- `docs/architecture/capabilities/asset-ingest.md`
- `docs/architecture/capabilities/social-create-visual.md`
- `docs/architecture/social-post-review-loop.md`
- `docs/architecture/article-execution-checklist.md`
- `docs/architecture/social-execution-checklist.md`
- `scripts/base-generation-brief.py`
- `scripts/visual-contract-freeze.py`
- `scripts/visual-review-gate.py`
