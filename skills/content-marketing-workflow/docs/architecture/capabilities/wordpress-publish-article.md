# Internal capability: wordpress-publish-article

Date: 2026-09-05
Status: live end-to-end validated implementation contract

## Purpose

`wordpress-publish-article` publishes one exact previously prepared and human-validated SEO Workflow Bridge-managed WordPress draft. It never reconstructs, rewrites or re-renders the article during publication.

Global prerequisite/degradation behavior is owned by:

```text
docs/architecture/runtime-compatibility-matrix.md
```

Strict product invariant:

```text
required verified final media missing
=> publication unavailable
```

There is no image-less WordPress publication fallback.

## Capability contract

```yaml
name: wordpress-publish-article
purpose: Publish one immutable validated WordPress draft candidate through SEO Workflow Bridge after a separate runtime publish_now authorization.
availability: optional
feature_gate: wordpress.publish_enabled
mode: external_write

prerequisites:
  - github_repository is operational
  - cloud_media_storage remains operational for required media identity/delivery evidence
  - wordpress_bridge_runtime is operational
  - explicit current publication intent exists
  - wordpress.enabled = true
  - wordpress.publish_enabled = true
  - wordpress-prepare-article completed on exact managed draft using required verified final media
  - editorial validation complete
  - required WordPress presentation/editor validation complete (`WordPress OK`)
  - exact post-validation draft captured into immutable publication candidate
  - current draft still matches candidate exactly
  - WordPress Bridge Article publication permission actually persisted/enabled for publication window

mandatory_context:
  - AGENTS.md
  - docs/architecture/runtime-compatibility-matrix.md
  - docs/architecture/persistence-contract.md
  - docs/architecture/wordpress-review-gate.md
  - docs/architecture/wordpress-workflow-authority.md
  - docs/architecture/wordpress-article-publication.md
  - exact connection profile
  - exact preparation manifest/state
  - exact immutable publication candidate
  - exact current human publication authorization when supplied

validation:
  - central runtime prerequisites still pass
  - required media identities remain pinned and exact
  - candidate contains no persisted publication authorization
  - candidate matches exact managed WordPress draft
  - status is draft before mutation
  - all pinned content/source/media/meta/taxonomy identities match
  - runtime authorization is exactly publish_now and candidate_id matches
  - Bridge Article publication permission is persisted/accepted
  - post-publication readback matches candidate with status publish
  - public permalink belongs to configured target
  - Article publication permission returns to least privilege after window

completion_conditions:
  - publication stage explicitly requested
  - preflight passes
  - exact candidate-specific publish_now received for current attempt
  - only draft -> publish mutation occurred
  - published readback passes
  - durable publication evidence synchronized
  - publication permission window closed/disabled again
```

## Invocation boundary

A validated draft does not imply publication intent.

```text
prepared draft
-> human WordPress/editor validation (`WordPress OK`)
-> STOP if publication was not requested
```

Only after current publication intent:

```text
publication_capture
-> immutable candidate
-> publication_preflight
-> permission window
-> exact publish_now gate
-> publish
```

Do not create candidate/preflight/publish requests merely because `WordPress OK` was received.

## Independent gates

These states are separate:

```text
article editorial validation
!= image selection / verified_final
!= cloud-media readiness
!= WordPress presentation validation
!= explicit publication-stage intent
!= wordpress.publish_enabled
!= Bridge Article publication permission
!= publish_now
```

No missing runtime prerequisite may be bypassed by approval state.

## Candidate and runtime authorization

Candidate pins exact WordPress/content/media/source identities and contains no reusable publication authority.

Runtime authorization is ephemeral and bound to exact candidate:

```json
{
  "authorization": {
    "decision": "publish_now",
    "candidate_id": "<exact candidate id>"
  }
}
```

`publish_now` is single-attempt authority. After any blocked/failed request, rerun read-only preflight and require a new explicit authorization. Never silently retry using old authority.

## Drift preflight

Any drift in managed status, title/slug/excerpt/post type, content hash, featured media, preparation/source identities, allowlisted metadata or taxonomies fails closed.

Intentional edits require a fresh validation/capture/candidate cycle. Do not refresh candidate merely to make preflight pass.

## WordPress mutation boundary

Publication may perform exactly:

```text
draft -> publish
```

It must not change content/title/slug/excerpt/media/taxonomies/meta, rebuild presentation, trash/delete content or mutate unmanaged posts. Required changes route back to preparation/review.

## Bridge operations

Current bounded operations:

```text
article_read
publication_preflight
article_publish
published_article_read
```

`article_publish` requires dedicated Bridge permission plus runtime gate. An `article_publish_disabled` response is authoritative fail-closed evidence with no implied mutation.

## Verification after publication

After mutation:

1. read same post against same candidate;
2. require `status=publish`;
3. verify pinned identities/hashes/meta/taxonomies/media;
4. obtain/validate permalink;
5. attempt external reachability when runtime supports it, otherwise record limitation truthfully;
6. persist result/evidence;
7. return Article publication permission to least privilege.

Do not report success from HTTP 2xx request alone.

## Media/storage boundary

WordPress media library is a derived publication representation, not CMW durable media storage. If the configured cloud-media provider or required final media is unavailable/drifted before publication, fail closed rather than falling back to WordPress/GitHub/local storage or publishing without image.

## Environment boundary

Publication is complete on explicitly selected WordPress connection. Pilot-specific cloning/deployment is outside this generic capability.
