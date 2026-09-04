# Internal capability: wordpress-publish-article

Date: 2026-09-01
Status: live end-to-end validated implementation contract

## Purpose

`wordpress-publish-article` is an optional internal capability of the single installable Content / Marketing skill.

It publishes one exact, previously prepared and human-validated SEO Workflow Bridge-managed WordPress draft.

It never reconstructs, rewrites or re-renders the article during publication.

This capability is **not entered merely because a draft received `WordPress OK`**. It is entered only when the user has actually requested publication now, or when the user explicitly requested an end-to-end workflow whose declared scope includes publication.

The generic human presentation gate is defined by `docs/architecture/wordpress-review-gate.md`. Adapter-specific technologies such as Divi, Gutenberg, Elementor or Bricks may have their own technical checks, but they do not rename the generic gate.

## Capability contract

```yaml
name: wordpress-publish-article
purpose: Publish one immutable validated WordPress draft candidate through SEO Workflow Bridge after a separate runtime publish_now authorization.
availability: optional
feature_gate: wordpress.publish_enabled
mode: external_write

prerequisites:
  - explicit current publication intent exists for this article/workflow
  - wordpress.enabled = true
  - wordpress.publish_enabled = true
  - wordpress-connect is verified
  - wordpress-prepare-article completed on the exact managed draft
  - editorial validation is complete
  - required WordPress presentation/editor validation is complete (`WordPress OK`)
  - exact post-validation WordPress draft was captured into an immutable publication candidate
  - current WordPress draft still matches that candidate exactly
  - WordPress Bridge Article publication permission is actually persisted/enabled for the publication window

mandatory_context:
  - AGENTS.md
  - docs/architecture/persistence-contract.md
  - docs/architecture/wordpress-review-gate.md
  - docs/architecture/wordpress-workflow-authority.md
  - docs/architecture/wordpress-article-publication.md
  - exact connection profile
  - exact preparation manifest/state
  - exact immutable publication candidate commit/path
  - exact human publication authorization when supplied

reads:
  - Bridge-managed WordPress draft
  - immutable candidate in GitHub
  - current Bridge permission state/result
  - public URL/readback after publication

writes:
  - WordPress post status transition draft -> publish only
  - durable published state/URL/evidence

persists:
  - immutable publication candidate without runtime authorization
  - candidate ID/hash/path/commit
  - publication result/status/URL/timestamp/evidence
  - failed/blocked publication attempts when relevant
  - no reusable publication authorization

external_side_effects:
  - publication_capture through SEO Workflow Bridge after publication intent is active
  - publication_preflight through SEO Workflow Bridge after publication intent is active
  - article_publish through SEO Workflow Bridge after explicit runtime authorization
  - published_article_read/public URL verification

human_approval:
  - explicit intent to enter the publication stage is required; WordPress OK alone is not that intent
  - wordpress.publish_enabled only exposes capability availability
  - every actual publication requires a new explicit publish_now authorization bound to the exact candidate_id
  - editorial/visual validation and automatic GitHub integration never imply publication approval
  - a publish_now authorization is single-attempt runtime authority and is not reusable after a blocked/failed publish request

validation:
  - candidate contains no persisted publication authorization
  - candidate matches the exact managed WordPress draft
  - required status is draft before mutation
  - all pinned content/source/media/meta/taxonomy identities match
  - runtime authorization decision is exactly publish_now and candidate_id matches
  - WordPress Bridge Article publication permission is persisted and accepted by the Bridge
  - post-publication readback still matches the candidate with status publish
  - public permalink is HTTPS and belongs to the configured target
  - external HTTP reachability is verified when the active runtime/network can perform that check; otherwise the limitation is persisted explicitly
  - Article publication permission returns to least privilege after the publication window

completion_conditions:
  - publication stage was explicitly requested
  - preflight passes
  - exact candidate-specific publish_now authorization was received for the current attempt
  - only draft -> publish mutation occurred
  - published readback passes
  - public permalink identity passes
  - external HTTP verification either passes or is explicitly recorded as unavailable due to runtime/network limitations
  - durable publication state is synchronized
  - publication permission window is closed/disabled again

next_actions:
  - published / seo-monitoring state
  - no implicit clone/promotion step in the generic capability
```

## Invocation boundary

The preparation workflow and the publication workflow are separate product actions.

Canonical behavior:

```text
prepared draft
-> human WordPress/editor validation (`WordPress OK`)
-> STOP successfully if publication was not requested
```

Only after a current publication request exists may the workflow proceed to:

```text
publication_capture
-> persist immutable candidate
-> publication_preflight
-> request/verify publication permission window
-> exact publish_now gate
-> publish
```

Do not proactively create a publication candidate, run publication preflight, ask the user to enable `Article publication`, or ask for `publish_now` merely because `WordPress OK` was received.

A later publication request may resume from the validated draft. At that time, capture the current exact draft and run a fresh preflight as required.

## Independent gates

These states are separate:

```text
article editorial validation
!= image selection
!= WordPress presentation validation (`WordPress OK`)
!= GitHub integration state
!= explicit intent to enter publication stage
!= wordpress.publish_enabled
!= Bridge Article publication permission
!= publish_now
```

GitHub integration is internal plumbing and not a user approval gate.

`wordpress.publish_enabled = true` means only that the publication capability is available.

It does not authorize publication of any article.

The WordPress Bridge `Article publication` checkbox is another independent permission. A checkbox changed in the WordPress admin UI is not considered active until the settings form has actually been saved and the Bridge accepts it.

Do not infer permission state from the user's UI description alone when a live Bridge result contradicts it.

## Capture after presentation validation

Page builders or WordPress editors may normalize serialized `post_content` when a human opens/saves a prepared draft.

Therefore, once the publication stage is actually invoked, publication identity must be captured from the **actual WordPress draft after required `WordPress OK` validation**, not reconstructed from the earlier preparation response.

Canonical read-only operation:

```text
publication_capture
```

It reads the Bridge-managed draft and derives the immutable candidate snapshot. It must not carry or persist publication authorization.

## Publication candidate

Canonical path:

```text
wordpress/publish/candidates/<connection_id>/<article-slug>.json
```

Current schema authority:

```text
wordpress/publish/candidate-schema-v1.json
```

The candidate pins at least:

- candidate ID;
- connection ID;
- WordPress post ID;
- post type/title/slug/excerpt;
- exact post_content SHA-256;
- featured media ID;
- preparation manifest identity;
- source article path/commit/SHA-256;
- allowlisted post meta;
- allowlisted taxonomies;
- evidence that capture occurred after human validation;
- explicit absence of publication authorization.

The candidate is eligibility evidence, not authorization.

Never edit a candidate to set `publication_authorized=true`.

## Runtime authorization

The only accepted publication authorization is ephemeral runtime input bound to the exact candidate:

```json
{
  "authorization": {
    "decision": "publish_now",
    "candidate_id": "<exact candidate id>"
  }
}
```

A different candidate ID, a generic `go`, earlier article validation or WordPress feature enablement does not satisfy this gate unless the current user message unambiguously refers to publishing that exact candidate now.

### Single-attempt rule

`publish_now` is authority for **one publication attempt**, not a reusable token.

Once a `publish_article` request carrying that authorization has been sent, treat that runtime authorization as consumed even if the Bridge rejects the request before mutation, for example because `Article publication` was disabled.

After the blocking cause is corrected:

1. run a fresh read-only preflight;
2. require a new explicit user `publish_now` authorization;
3. send a new publication request with a new request ID.

Never silently retry a failed/blocked publication using an earlier authorization.

## Drift preflight

Before publication, run read-only preflight against the immutable candidate.

Any drift fails closed, including changes to:

- managed marker/status;
- title/slug/excerpt/post type;
- exact content SHA-256;
- featured media;
- preparation/source identities;
- declared allowlisted metadata;
- declared allowlisted taxonomies.

Intentional post-capture edits require a new validation/capture/candidate cycle.

Do not silently refresh the candidate from current WordPress state merely to make preflight pass.

A retry after a blocked publication must also run a fresh preflight even when the previous attempt was rejected before mutation.

## WordPress mutation boundary

Publication may perform exactly one content mutation:

```text
draft -> publish
```

It must not during publication:

- change article content;
- change title/slug/excerpt;
- upload/replace media;
- change featured media;
- change taxonomies/meta;
- rebuild a presentation profile;
- trash/delete content;
- mutate unmanaged posts.

If any of those are required, route back to preparation/review first.

## Bridge operations

Parent relay/application operations:

```text
publication_capture
publication_preflight
publish_article
published_article_read
```

Bounded SEO Workflow Bridge operations:

```text
article_read
publication_preflight
article_publish
published_article_read
```

`article_publish` requires the dedicated Bridge `Article publication` permission in addition to the runtime gate enforced by the parent workflow.

The current Bridge stores this permission as `allow_article_publish`. In the WordPress admin UI, changing the checkbox is insufficient until **Save Changes / Enregistrer les modifications** persists the settings form.

A Bridge error such as:

```text
article_publish_disabled
```

must be treated as authoritative evidence that the permission was inactive for that request. It is a fail-closed result and does not imply that the article was mutated.

## Verification after publication

After mutation:

1. read the same post again against the same candidate;
2. require `status = publish`;
3. verify all pinned identities/hashes/meta/taxonomies still match;
4. obtain the public permalink;
5. verify it is HTTPS and belongs to the expected configured WordPress target;
6. attempt independent external HTTP reachability verification when the active runtime/network supports it;
7. if that external check cannot run because of DNS/network/runtime limitations, persist that limitation explicitly instead of pretending it passed;
8. persist status/URL/timestamp/evidence;
9. return `Article publication` to disabled/least privilege.

Bridge `published_article_read` is mandatory post-publication evidence. External HTTP reachability is an additional verification layer, not a reason to rewrite or re-publish an otherwise exact candidate when the assistant runtime itself cannot reach the hostname.

Do not report success from an HTTP 2xx publication request alone.

## Least-privilege closure

For the current Bridge integration, the user may control the `Article publication` checkbox manually.

After successful publication and readback:

- explicitly instruct the user to disable `Article publication` again when the capability cannot change that Bridge setting itself;
- wait for confirmation if the workflow contract requires a verified least-privilege closure;
- persist that the permission was reported disabled after publication;
- keep `publication_authorized = false` in durable article state.

The capability must never leave a reusable runtime publication authorization in Git or treat the enabled Bridge permission as standing authority to publish future articles.

## Validated retry safety behavior

The retry contract is intentionally fail-closed and preserves the following generic sequence once publication is actually requested:

1. prepare provider-backed media and a Bridge-managed draft;
2. complete human presentation validation;
3. receive explicit publication-stage continuation;
4. run `publication_capture` after any editor normalization;
5. persist an immutable candidate;
6. run preflight;
7. if the Bridge reports `article_publish_disabled`, treat the attempt as blocked with no mutation;
8. treat the runtime authorization used by that request as consumed;
9. after the blocking permission is corrected, run a fresh preflight;
10. require a new explicit publication authorization;
11. allow `article_publish` to transition exactly `draft -> publish`;
12. verify the same candidate through `published_article_read` and all pinned checks;
13. return publication permission to least privilege after publication.

This is the canonical safety behavior for future retries once publication is actually requested.

## Environment boundary

Publication is complete on the explicitly selected WordPress connection.

Do not infer that a hostname named `test` must later be cloned/promoted elsewhere.

Pilot-specific cloning/deployment remains outside this generic capability.
