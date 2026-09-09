# Internal capability: social-check-before-publish

Date: 2026-09-09
Status: current capability contract

## Purpose

`social-check-before-publish` is the read-only diagnostic gate for one social post. It reports three independent readiness layers instead of collapsing them into one generic publication result:

```text
content_readiness
schedule_readiness
unattended_execution_readiness
```

It never publishes, schedules, creates authorization, confirms scheduling or mutates repository state.

## Capability contract

```yaml
name: social-check-before-publish
purpose: Validate durable content and schedule state, then separately report unattended execution infrastructure/authorization readiness without publishing or mutating state.
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
  - exact publication-authorization presence/state when available
  - scheduler/runtime verification state when available
  - active social Bridge capability/connection health when available

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

## Readiness layers

`/social check` must report these layers independently. A failure or unknown state in a later layer must not rewrite an earlier passing layer as failed.

### 1. Content readiness

Covers immutable identity/provenance, approved master text, ALT, verified final visual/provider identity, hashes/dimensions/MIME, platform membership/status coherence and duplicate-publication hazards.

Typical result:

```text
content_readiness: PASS|FAIL
```

### 2. Schedule readiness

Covers exact timezone-aware `planned_at`, target/connection identity and scheduling metadata coherence. It answers whether the approved post has a valid durable plan, not whether the unattended runtime can execute it right now.

Typical result:

```text
schedule_readiness: PASS|FAIL|NOT_SCHEDULED
```

### 3. Unattended execution readiness

Covers the infrastructure/security state needed for automatic execution: exact scheduled-publication authorization, verified delivery copy, compatible social adapter, actual SEO Workflow Bridge **social** runtime, credential health and GitHub Actions scheduler.

Typical result:

```text
unattended_execution_readiness: READY|PENDING|BLOCKED|UNKNOWN
```

Important classification rules:

- absence of an exact authorization does **not** make `content_readiness` or `schedule_readiness` fail; report it only in unattended execution readiness;
- an unverified/missing GitHub Actions scheduler is an unattended-execution infrastructure issue, not a content defect and not a reason to invalidate a coherent persisted `planned_at`;
- `wordpress.publish_enabled` controls **WordPress article publication only** and MUST NOT be used as a Facebook/LinkedIn blocker;
- for social publication, inspect the actual `wordpress_bridge_runtime` and required social Bridge capability/adapter state independently from WordPress article publication permission;
- `wordpress.publish_enabled=false` may be a deliberate least-privilege/user preference while Facebook/LinkedIn scheduled publication remains fully operational;
- `/social check` is read-only: it reports that an authorization is missing but does not materialize one. `/social schedule` owns authorization materialization when policy/prerequisites permit.

## Exact authorization timing

For scheduled social publication, exact authorization is normally materialized **before the due date**, during `/social schedule` once final content, schedule, delivery and policy gates are satisfied. The scheduler later ignores that dormant authorization until `planned_at` becomes due.

Therefore:

```text
authorization created before planned_at
!= publish now
```

The day/time gate remains enforced by the scheduler/Bridge prepublication checks. Authorization must not be deferred to the day of publication merely to keep the post dormant.

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
./social-publisher.bash check-before-publish <post-id>
./social-publisher.bash check-before-publish <post-id> --platform facebook
./social-publisher.bash check-before-publish <post-id> --platform linkedin
./social-publisher.bash check-before-publish --all
```

A passing content/schedule result means the durable post is ready for the next relevant workflow step. Only `unattended_execution_readiness: READY` means the current automatic execution path is complete; even then no public post has been created until the due scheduler/relay actually succeeds.

Any implementation projection must converge on the full capability validations above; the capability contract is authoritative when a newer durable provenance requirement has not yet been projected into a specific CLI check.

## Duplicate protection

When a specific platform is targeted and its durable status is already `published`, the check must fail rather than treating the post as publishable again.

Future live adapters must add remote idempotency checks where the platform API allows them.

## Accessibility

When a visual exists, `visual_alt_text` is a blocking requirement. The check never invents replacement alt text at publication time because the validated GitHub value is the source of truth.
