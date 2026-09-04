# Internal capability: social-check-before-publish

Date: 2026-09-02
Status: current capability contract

## Purpose

`social-check-before-publish` is the read-only gate that determines whether one social post is technically and structurally ready for a targeted platform publication or native scheduling step.

It never publishes, schedules, confirms scheduling or mutates repository state.

## Capability contract

```yaml
name: social-check-before-publish
purpose: Validate one or more social posts against durable provenance, social data, accessibility, provider-backed asset and platform contracts before any publication-related action.
availability: optional
feature_gate: social.enabled
mode: read_only

prerequisites:
  - social.enabled is true
  - social production files are readable
  - immutable ID registry is readable

mandatory_context:
  - AGENTS.md
  - docs/architecture/social-workflow.md
  - docs/architecture/media-delivery-architecture.md
  - strategy/social-scheduling.md
  - strategy/social-writing-style.md
  - strategy/social-visual-guidelines.md
  - social/README.md
  - social/id-registry.json
  - social-publisher.py current implementation

reads:
  - social post front matter and master text
  - source article relationship for article-derived posts
  - source series-plan.md and series concept relationship when applicable
  - retained final visual identity/hash/metadata
  - explicit repository_file compatibility path when used
  - immutable post ID registry
  - targeted platform state

writes: []
persists: []
external_side_effects: []
human_approval: []

validation:
  - post_id format and uniqueness
  - post_id is present in durable assigned_ids registry
  - article-derived post has an explicit article source path
  - article-derived post has a stable series_concept that exists in the corresponding series-plan.md
  - series-plan entry maps back to the same post_id once materialized
  - obsolete fields absent
  - root/platform statuses valid and coherent
  - platform membership and platform block coherent
  - planned_at is timezone-aware ISO 8601
  - Facebook native scheduling metadata coherent when Facebook is targeted
  - visual_alt_text exists when visual exists
  - asset_status is verified_final before publication
  - normal final visual uses a supported provider with stable asset_id
  - exact final filename, SHA-256, MIME and dimensions are declared and valid
  - repository_file is accepted only when explicitly declared as compatibility mode and the referenced repository file exists
  - master text exists
  - master text contains no Markdown syntax
  - master text contains no more than two emojis
  - targeted platform is not already published
  - duplicate-publication hazards fail closed

completion_conditions:
  - every requested check completed
  - clear pass/fail result returned
  - no repository or external mutation occurred
```

## Provenance readiness

For article-derived posts, publish readiness includes durable provenance:

```yaml
article: articles/<scope>/<article>.md
article_url: <canonical/public URL when known>
series_concept: <stable concept key>
```

The corresponding `series-plan.md` must contain the same concept key and, once materialized, the same `post_id`.

Folder placement alone is not sufficient provenance.

## Canonical final-media readiness

Normal social finals are provider-backed and use:

```yaml
asset_status: verified_final
visual:
  provider: google_drive
  asset_id: <stable-private-final-file-id>
  filename: <canonical-filename>
  sha256: <64-lowercase-hex>
  mime_type: image/jpeg|image/png
  width: 1080
  height: 1350
visual_alt_text: "..."
```

The retained private final is the durable binary identity. A temporary delivery copy is never sufficient evidence of final readiness.

`repository_file` remains explicit compatibility only.

## CLI projection

Current CLI entrypoints remain:

```bash
./social-publisher.bash check-before-publish 2026-0001
./social-publisher.bash check-before-publish 2026-0001 --platform facebook
./social-publisher.bash check-before-publish 2026-0001 --platform linkedin
./social-publisher.bash check-before-publish --all
```

A passing result means the durable state is ready for the next publication-related step. It does not mean a public post has been created and it does not grant publication authorization.

Any implementation projection must converge on the full capability validations above; the capability contract is authoritative when a newer durable provenance requirement has not yet been projected into a specific CLI check.

## Duplicate protection

When a specific platform is targeted and its durable status is already `published`, the check must fail rather than treating the post as publishable again.

Future live adapters must add remote idempotency checks where the platform API allows them.

## Accessibility

When a visual exists, `visual_alt_text` is a blocking requirement. The check never invents replacement alt text at publication time because the validated GitHub value is the source of truth.
