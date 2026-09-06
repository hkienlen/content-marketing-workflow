# Internal capabilities

This directory contains business/workflow contracts for internal capabilities of the single installable Content Marketing Workflow Skill.

Every capability contract conforms to repository-wide persistence, testing, safety and single-skill architecture contracts.

## Runtime prerequisite authority

Global prerequisite discovery, severity, degraded-mode behavior and provider availability are owned centrally by:

```text
docs/architecture/runtime-compatibility-matrix.md
```

Individual capability contracts may add task-specific gates but must not invent conflicting fallback/degradation behavior.

Core rules include:

- GitHub repository access is fatal/hard prerequisite;
- implemented cloud-media providers are Google Drive and Dropbox;
- exactly one cloud-media provider is active per project, with Google Drive recommended/default when both are operational;
- provider switching is explicit migration/rebinding, never silent fallback;
- GitHub, WordPress and local filesystem are not media-storage fallbacks;
- required-media absence never becomes image-less WordPress publication or text-only social publication;
- current LinkedIn/Facebook automated publication depends on WordPress-hosted SEO Workflow Bridge;
- current unattended scheduled publication depends on GitHub Actions;
- image generation/editing may use the manual external-generation prompt/user-upload handoff when unavailable;
- Telegram remains optional/downstream.

## User command layer

Authoritative command assets:

```text
docs/architecture/user-command-interface.md
docs/architecture/user-command-catalog.yaml
docs/architecture/user-command-catalog.schema.json
docs/architecture/user-command-runtime-contract.md
docs/architecture/user-command-system-behaviors.md
docs/architecture/user-command-productization-checklist.md
```

A capability is an internal workflow contract. A `/...` command is a stable alias/router and does not redefine business rules.

## Integrated / current

### Core orchestration/persistence

- `start.md`
- `strategy-update.md`
- `visual-configure.md` - guided/read-only visual setup for source policy, official logos, independent article/social logo preferences and durable free-form visual directives.

### SEO/content

- `seo-plan-article.md`
- `seo-create-article.md`
- `seo-update-article.md`
- `article-inspect.md`

`/article create` remains exclusively backed by `seo-create-article`.

### Media and brand

- `visual-source-resolve.md` - resolves project -> content-kind -> local source/treatment policy plus structured article/social brand handoff, source intake/verification and truthful drafting/finalization readiness;
- `asset-ingest.md` - final-asset normalization/verification preserving source/logo originals, provenance and effective brand-contract evidence.

Normative media/source/creative/brand models:

```text
docs/architecture/runtime-compatibility-matrix.md
docs/architecture/user-provided-images.md
docs/architecture/visual-generation-contract.md
docs/architecture/brand-assets-contract.md
docs/architecture/media-delivery-architecture.md
docs/architecture/google-drive-workspace.md
docs/architecture/dropbox-workspace.md
```

Provider-neutral conceptual content workspaces are `source-user/`, `proposals/`, `final/`, and temporary `tmp-outbox/`. Reusable official project brand assets live separately under a private `brand/` workspace. Google Drive and Dropbox map those concepts through provider-specific adapters while durable asset identity remains provider-qualified.

## Public visual configuration

The visual command family is:

```text
/visual status
/visual configure
/visual logo
/visual guidelines
/logo
```

`/logo` aliases `/visual logo`.

`/visual status` is read-only. Other visual configuration operations persist only user/project state and verified private brand assets. They never put one user's brand or directives into generic Skill contracts.

Equivalent natural-language requests route to the same durable model. `/strategy update` remains valid for durable strategy requests, while provider-backed official logo intake/replacement is delegated to `visual-configure`.

There is no separate public `/visual source` command; source preferences are part of `/visual configure`, `/start`, natural-language durable updates or the structured visual profile.

## Current visual-source invariant

Before article/social drafting:

```text
project default -> article/social source override -> per-content local source override
```

Supported modes:

```text
ai_first
user_images_first
strict_user_images
hybrid_best_fit
```

When required source is absent under `ask_before_drafting`, state is `awaiting_user_images` and drafting stops. When provider intake is required, show the exact selected-provider source-user location plus a verified direct provider link where the adapter supports one.

Source originals are never overwritten. Strict/high fidelity cannot silently become synthetic subject replacement. Exact `use_as_is` is not forced into A/B/C; generated/materially transformed work retains A/B/C review.

When generation/editing is unavailable in the current runtime but cloud media is operational, use the central manual image handoff rather than reporting false generation success.

## Current visual creative invariant

Before generation/material editing, resolve the complete effective visual contract in this creative-precedence order beneath non-overridable workflow/integrity/safety rules:

```text
content-local user directive
> article/social-specific user directive
> project-global user directive
> generic CMW creative defaults
> executor interpretation
```

User creative directives therefore override conflicting generic CMW creative defaults. Generic defaults fill only dimensions the user did not specify.

Rich durable user directives live in the user-owned authority referenced by `visual_identity.guidelines_path`, normally `strategy/visual-guidelines.md`; they are never packaged into the generic Skill.

Generic article/social defaults are defined in `visual-generation-contract.md` and generalize reusable practices such as real visual diversity, avoidance of generic AI/stock clichés, mobile-aware social layout and exactly three strong review candidates for generated/materially transformed visual groups.

## Current logo/brand invariant

Article and social logo application are **independent durable preferences**:

```yaml
visual_identity:
  logo_policy:
    article: always|auto|never
    social: always|auto|never
```

A normal valid project configuration is:

```yaml
logo_policy:
  article: never
  social: always
```

The article workflow reads only the article field (plus article-local override). The social workflow reads only the social field (plus post-local override). Never infer one from the other.

Official logo variants (`primary`, `light`, `dark`) are verified private provider-backed brand assets. A single official logo is valid; light/dark variants are recommended when available.

Logo application rules:

```text
always -> exact official verified logo required before verified_final
auto   -> logo may be included/omitted; any included logo must be official verified asset
never  -> project logo must be absent from final
```

Never ask a generative image model to recreate a missing official logo. It may reserve composition space, but exact branding is applied from verified logo bytes and checked again before `verified_final`.

Older profiles with no `visual_identity` preserve historical no-logo behavior only as an unconfigured compatibility state; `/start` or `/visual configure` gathers article/social choices separately instead of silently converting absence into confirmed preferences.

## Social final-package invariant

After final text and visual approval, the selected provider's private `final/` package contains the verified visual plus one copy/paste-ready final text artifact:

```text
google_drive -> native Google Doc
dropbox      -> UTF-8 plain-text .txt
```

The artifact body is the exact approved publishable text only. The historical contract filename `social-final-drive-package.md` is retained for compatibility but is provider-neutral from 0.3.0 onward.

## Social strategic invariant

Article-derived series use four durable functions:

```text
identification
expertise
positioning
conversion
```

Series ordering should mix functions and avoid consecutive strong conversion/CTA posts by default.

## Publication completion semantics

```text
scheduler success
!= provider publication evidence
!= post-publication verification
!= notification delivery
```

Notification delivery failure never changes authoritative publication state or authorizes duplicate publication.

Changing visual guidelines, logo policy or logo asset does not silently rewrite an existing `verified_final` visual or publication authorization bound to its exact media hash. New/reopened work resolves the current contract; historical finals remain bound to their recorded effective contract.

## Provider abstraction and genericity

Provider adapters handle binary/media transport. Business capabilities depend on provider-qualified source/final/brand asset identity + SHA-256 and explicit source roles/fidelity/treatment rather than provider-specific business rules.

Pilot-specific site/platform/business/visual/logo preferences remain in user/project data; generic capability contracts remain profession-neutral and reusable.
