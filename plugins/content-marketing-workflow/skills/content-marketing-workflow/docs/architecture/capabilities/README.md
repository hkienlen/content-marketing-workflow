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

### SEO/content

- `seo-plan-article.md`
- `seo-create-article.md`
- `seo-update-article.md`
- `article-inspect.md`

`/article create` remains exclusively backed by `seo-create-article`.

### Media

- `visual-source-resolve.md` - resolves project -> content-kind -> local visual policy, source intake/verification and truthful drafting readiness;
- `asset-ingest.md` - final-asset normalization/verification preserving source originals/provenance.

Normative media/source models:

```text
docs/architecture/runtime-compatibility-matrix.md
docs/architecture/user-provided-images.md
docs/architecture/media-delivery-architecture.md
docs/architecture/google-drive-workspace.md
docs/architecture/dropbox-workspace.md
```

Provider-neutral conceptual workspaces are `source-user/`, `proposals/`, `final/`, and temporary `tmp-outbox/`. Google Drive and Dropbox map those concepts through provider-specific adapters while durable asset identity remains provider-qualified.

There is no separate public `/visual source` command. Durable defaults are set through onboarding/natural language or `/strategy update`; `/status` exposes them read-only; local overrides are handled by owning content workflow.

### WordPress optional

- `wordpress-connect.md`
- `wordpress-prepare-article.md`
- `wordpress-publish-article.md`

WordPress authoring integration is optional, but current WordPress publication and current automated social publication require a verified WordPress-hosted SEO Workflow Bridge runtime.

### Social optional (`social.enabled`)

- `social-extract-posts.md`
- `social-create-post.md`
- `social-inspect.md`
- `social-create-visual.md`
- `social-check-before-publish.md`
- `social-connection-health.md`
- `social-schedule.md`
- `social-publish.md`
- `social-publication-verification.md`
- `telegram-publication-notifications.md`

LinkedIn and Facebook Page adapters are independently gated. Facebook personal/professional profile is not an API publication fallback.

## Current visual-source invariant

Before article/social drafting:

```text
project default -> article/social override -> per-content local override
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

## Provider abstraction and genericity

Provider adapters handle binary/media transport. Business capabilities depend on provider-qualified source/final asset identity + SHA-256 and explicit source roles/fidelity/treatment rather than provider-specific business rules.

Pilot-specific site/platform/business/visual preferences remain in user/project data; generic capability contracts remain profession-neutral and reusable.
