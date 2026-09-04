# Internal capabilities

This directory contains business/workflow contracts for internal capabilities of the **single installable Content / Marketing skill**. These files are not separate installable skills.

Every capability contract conforms to repository-wide persistence, testing, safety and single-skill architecture contracts.

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

A capability is an internal workflow contract. A `/...` command is only a stable alias/router and must not redefine business rules.

## Integrated / current

### Core orchestration/persistence

- `start.md`
- `strategy-update.md`

### SEO/content

- `seo-plan-article.md`
- `seo-create-article.md`
- `seo-update-article.md`
- `article-inspect.md`

`/article create` remains exclusively backed by `seo-create-article` and never creates social post.

### Media

- `visual-source-resolve.md` - internal shared pre-draft policy/source-intake capability for article/social workflows; resolves project -> content-kind -> local visual policy, creates/reuses private `source-user/` intake when needed, verifies/inspects real user sources and returns truthful drafting readiness without publishing;
- `asset-ingest.md` - internal final-asset normalization/verification capability that preserves source originals/provenance when user-provided media is involved.

Normative source-image model:

```text
docs/architecture/user-provided-images.md
```

There is no separate public `/visual source` command. Durable defaults are set through onboarding/natural language or `/strategy update`; `/status` exposes them read-only; local overrides are handled by owning content workflow.

### WordPress optional

- `wordpress-connect.md`
- `wordpress-prepare-article.md`
- `wordpress-publish-article.md`

### Social optional (`social.enabled`)

- `social-extract-posts.md` - inventories/deduplicates source article, classifies retained concepts by strategic function, checks coverage, builds balanced order, persists/presents complete series for human validation;
- `social-create-post.md` - queue-driven `/social create` and standalone `/social create free <topic>` orchestrator, including pre-draft `visual-source-resolve` when policy requires it;
- `social-inspect.md` - read-only `/social list` and `/social details`;
- `social-create-visual.md` - creates A/B/C for generated/materially transformed workflows or exact source review for `use_as_is` without fake variants;
- `social-check-before-publish.md`;
- `social-connection-health.md` - read-only provider/credential health and expiry-horizon monitoring;
- `social-schedule.md` - schedules approved posts while checking global calendar commercial/CTA clustering;
- `social-publish.md` - exact authorized publication/provider evidence reconciliation;
- `social-publication-verification.md` - platform-appropriate post-publication verification (`remote_verified` where available, `provider_acknowledged` otherwise);
- `telegram-publication-notifications.md` - optional user-controlled reports, with setup/reconfiguration that never exposes bot token.

## Current visual-source invariant

Before article/social drafting, owning creation capability resolves effective policy:

```text
project default -> article/social override -> per-content local override
```

Supported source modes:

```text
ai_first
user_images_first
strict_user_images
hybrid_best_fit
```

When required source is absent under `ask_before_drafting`, state is `awaiting_user_images` and drafting stops. When asking for Drive input, show exact `source-user/` path + verified direct Drive folder link.

Source original is never overwritten. Strict/high fidelity cannot silently become synthetic subject replacement. Exact `use_as_is` is not forced into A/B/C; generated/materially transformed work retains A/B/C review.

## Current social strategic invariant

Article-derived series use four durable functions:

```text
identification
expertise
positioning
conversion
```

User-facing labels:

```text
Identification
Expertise / compréhension
Méthode / positionnement
Offre / conversion
```

Goal is not rigid funnel/quota. Repeated exposure should clarify problem, expertise/approach and, when truthfully supported, offer/next step. Series order should mix functions and avoid consecutive conversion/strong-CTA posts by default.

## Current social creation invariant

For unchanged validated series:

```text
/social create
-> resume/select next eligible concept
-> visual-source-resolve before drafting when applicable
-> draft + visual workflow
```

When exhausted:

```text
next eligible validated article
-> inventory/deduplicate
-> classify functions + assess coverage + balanced order
-> persist/re-read complete plan
-> present detailed list
-> human validates/corrects
-> persist exact validated revision
-> immediately start first eligible post
-> visual-source-resolve before drafting when applicable
```

Whole-series gate is mandatory before first drafting from new/materially revised article-derived series and is not repeated before every post from unchanged series.

Free posts skip only whole-series gate, not visual-source/text/media/scheduling/publication gates.

## Publication completion semantics

Publication scheduling, provider creation evidence, post-publication verification and notification remain separate:

```text
scheduler success
!= provider publication evidence
!= post-publication verification
!= notification delivery
```

Current platform result semantics:

```text
Facebook -> published + remote_verified after successful read-back
LinkedIn -> published + provider_acknowledged when creation evidence is definitive but independent read-back unavailable
```

Notification delivery failure never changes authoritative provider publication state or authorizes duplicate publication.

## Public invocation expectation

During productization, every capability is classified as directly user-invokable, reachable through higher-level command, semantic-only or internal/supporting.

`visual-source-resolve` and `asset-ingest` are internal/supporting. Their behavior is surfaced through article/social help/status rather than new public slash commands.

## Provider abstraction and genericity

Provider adapters handle binary/media transport. Business capabilities depend on generic stable source/final asset identity + SHA-256 semantics and explicit source roles/fidelity/treatment rather than provider-specific business rules.

Pilot-specific site/platform/business/visual preferences remain in profile/strategy/content user data; generic capability contracts remain profession-neutral and reusable.
