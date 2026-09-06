# Visual generation contract

Date: 2026-09-06
Status: normative architecture contract

## Purpose

This contract defines the generic creative defaults, user-directive precedence and generation/review behavior for article and social visuals managed by Content Marketing Workflow.

It generalizes proven project practice without packaging any user's brand, profession, palette, logo, wording or site-specific creative choices.

## Authority layers and conflict resolution

Resolve visual instructions in this order:

```text
1. non-overridable workflow/integrity/safety invariants
2. explicit content-local user directives for the current article/post/image
3. channel-specific user directives (article or social)
4. project-global user visual directives
5. generic CMW creative defaults from this contract
6. executor interpretation
```

User directives override conflicting **creative defaults** from the Skill.

User directives do not override integrity/truthfulness invariants such as:

- do not claim a file/provider object exists when it was not verified;
- do not overwrite a user source original;
- do not call a candidate selected without human selection when selection is required;
- do not call media `verified_final` before exact final verification;
- do not invent/recreate an official logo that is required;
- do not bypass source-fidelity or publication authorization gates.

When the user has no directive for a creative dimension, the generic defaults continue to apply.

## Durable user authority

Structured operational settings belong in `user-data/profile.json`, including:

- source preference/fidelity/treatment under `visual_preferences`;
- logo asset registry and independent article/social logo policy under `visual_identity`.

Rich prose directives belong in the user-owned project authority:

```text
strategy/visual-guidelines.md
```

The Skill package may provide a template/contract for this file but must never package one user's concrete values.

Recommended user-owned sections:

```text
Global visual direction
Article visuals
Social visuals
Brand/logo placement preferences
People and representation
Photography/illustration preferences
Text inside images
Required elements
Forbidden elements
Free permanent directives
```

Preserve useful original user wording. Do not force every creative nuance into enums.

## Scope classification

Before persisting a user instruction, classify it:

```text
"from now on", "always", "for my social posts", "for my articles"
-> durable project/channel directive

"for this post only", "for this article", "for image 2 only"
-> content-local directive
```

A local instruction never silently changes project defaults.

When scope is explicit, do not ask again.

## Effective visual contract

Before generation/review, the owning article/social workflow resolves a reviewable effective contract containing at least:

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
contract_revision: <durable identifier/hash/commit when available>
```

The effective contract is tied to the exact content/review revision so later preference changes do not silently reinterpret an already approved visual.

## Generic article creative defaults

Unless the user/project/article brief says otherwise:

- prefer a realistic, credible, professional visual direction rather than generic synthetic-looking imagery;
- photography is a strong default when it supports the concept, but it is not mandatory;
- avoid repetitive AI clichés and literal over-explanation;
- support the editorial idea/ambience instead of trying to summarize the whole article in one image;
- enforce real diversity across an article and recent related visuals by varying several dimensions such as subject, location, framing, camera distance, presence/absence of people, action, object, composition, viewpoint, lighting or metaphor;
- do not place a person in every image; objects, places, gestures, details and concrete metaphors are encouraged when stronger;
- when people appear, prefer natural credible posture/expression over caricatured stress, failure or enthusiasm and avoid obvious stock-photo staging;
- absent another project rule, plan article visuals as 16:9 landscape, target 1600 x 900 px and finalize as WebP when compatible with the owning article workflow;
- by default do not embed marketing/headline text into a photographic article image; short realistic in-scene text may be used when the exact brief justifies it;
- generated/materially transformed visuals normally retain exactly three genuinely reviewable candidates per requested image after internal rejection/regeneration of poor outputs.

These are defaults, not a mandatory visual style. A user's durable/local direction such as illustration, vector art, collage, monochrome photography or another coherent style overrides them.

## Generic social creative defaults

Unless user/project/platform directives say otherwise:

```text
visual = hook / attention / immediate tension
post text = development
linked article = deeper treatment when relevant
```

The social visual should not mechanically reproduce the SEO title or attempt to summarize every point in the post.

Defaults for an autonomous LinkedIn/Facebook image post:

- design for mobile readability;
- target 4:5, 1080 x 1350 px when one master format is appropriate for the enabled channels;
- use a short visible hook only when the concept benefits from it;
- keep one principal visible idea rather than a paragraph of text;
- JPEG is a good default for photographic scenes; PNG is a good default for infographics, flat graphics and text-heavy designs;
- prefer credible people/places/objects and avoid generic corporate stock aesthetics;
- alternate visual families across a campaign when useful: photography, professional environment without people, illustration, simple infographic, typographic visual, concrete metaphor, objects/documents/workspace or hybrid composition;
- campaign consistency does not mean near-duplicate images; either intentionally maintain a coherent short sub-series or vary several dimensions so the difference is perceptible;
- no generic palette, accent color or logo placement is imposed by CMW;
- generated/materially transformed social work normally retains exactly three genuinely distinct A/B/C candidates for combined human review.

Platform-specific requirements, when current and authoritative, override these format defaults without changing unrelated user directives.

## Diversity and repetition control

Before generating a new visual set, inspect recoverable recent final visuals/briefs in the relevant project scope when available and useful.

Avoid false variety where only one superficial element changes while decor, lighting, pose, composition and visual family remain effectively identical.

Either:

- repetition is deliberately part of a coherent short series; or
- the new visual is materially different in multiple dimensions.

Do not impose demographic quotas image by image. When people are useful, vary profiles naturally across the broader content set when that improves realism and diversity.

## Text in images

Text is optional, not automatic.

When text is used:

- keep it short and readable on the target device;
- preserve exact spelling and user-approved wording;
- avoid sensationalist/clickbait phrasing unless explicitly part of the user's strategy;
- do not invent third-party brands/logos;
- ensure important factual information also exists in accessible page/post text when required.

## Brand/logo integration

Logo behavior is not a generic creative default. It is resolved from `visual_identity.logo_policy` independently for `article` and `social`, then any content-local override.

Read and apply:

```text
docs/architecture/brand-assets-contract.md
```

The generative model may reserve composition space, but an official logo should normally be applied deterministically from the verified brand asset rather than recreated by generation.

## Proposal workflow

For generated/materially transformed visuals:

```text
resolve effective visual contract
-> prepare exact brief(s)
-> generate internally as needed
-> inspect/reject off-brief, generic, duplicated or malformed outputs
-> retain exactly three strong reviewable candidates per visual group
-> persist/recover candidates through configured cloud-media provider
-> present grouped human review
```

The executor may generate more internal drafts to obtain three good review candidates; extra rejected drafts are not review candidates.

For exact `use_as_is + ai_treatment:none`, present the exact source/final candidate instead of fabricating A/B/C.

## Targeted review and freeze

Human review may approve/reject/revise text and visuals independently.

- preserve approved components during targeted revisions;
- criticizing one candidate does not alter the others;
- changing only a background under strict/high source fidelity must preserve the real subject as required;
- a new generation round preserves unaffected approved source/text/logo policy unless explicitly reopened;
- a permanent directive change affects future/new revisions, not already final media automatically.

## Free user directives

Users may provide arbitrary visual instructions in natural language. Examples of supported categories include:

- preferred/forbidden artistic styles;
- people/no-people preferences;
- preferred environments, objects or metaphors;
- palette/color restrictions;
- realism level;
- text density;
- brand tone;
- prohibited clichés;
- accessibility/readability preferences;
- placement preferences;
- seasonal/campaign exceptions.

When the user explicitly makes a directive permanent, persist it in the project visual-guidelines authority with its scope and apply it to all future affected generation/revision until changed.

When a directive is one-off, persist it only with the owning content item.

## Finalization and historical binding

A selected final records enough effective-contract evidence to reproduce/explain the decision, including the logo application outcome and logo asset identity when present.

Changing project visual guidelines or replacing a logo does not silently mutate historical `verified_final` assets or scheduled/publication authorizations bound to exact media hashes.

## References

- `docs/architecture/brand-assets-contract.md`
- `docs/architecture/user-profile-data-contract.md`
- `docs/architecture/user-provided-images.md`
- `docs/architecture/capabilities/visual-configure.md`
- `docs/architecture/capabilities/visual-source-resolve.md`
- `docs/architecture/capabilities/asset-ingest.md`
- `docs/architecture/article-execution-checklist.md`
- `docs/architecture/social-execution-checklist.md`
