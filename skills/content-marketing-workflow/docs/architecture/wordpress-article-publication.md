# WordPress article publication

Date: 2026-09-04
Status: authoritative publication architecture

## Authority

This document defines publication semantics for `docs/architecture/capabilities/wordpress-publish-article.md`.

SEO Workflow Bridge is the canonical WordPress-side application boundary. See `docs/architecture/wordpress-workflow-authority.md`.

Publication capability availability requires:

```yaml
wordpress:
  enabled: true
  publish_enabled: true
```

These feature flags do **not** authorize publication of a specific article.

## Scope

`wordpress-publish-article` is separate from draft preparation.

It never reconstructs or edits article content. It can only:

1. capture the exact Bridge-managed WordPress draft after required human presentation/editor validation;
2. persist that captured state as an immutable Git publication candidate, without publication authorization;
3. preflight the exact draft against the persisted candidate snapshot;
4. publish that exact unchanged draft after a separate runtime human authorization and while WordPress `Article publication` permission is actually persisted/enabled;
5. read back the published article against the same snapshot and verify its public permalink;
6. return the Bridge publication permission to least privilege after the publication window.

Any drift after capture blocks publication and routes back to preparation or to a new human validation/capture cycle when the change is intentional.

## Target environment semantics

`wordpress-publish-article` publishes directly to the WordPress connection selected by `connection_id`.

The capability must never infer environment semantics from a hostname, subdomain or connection identifier. Names containing `test`, `staging`, `preprod`, `prod` or similar are opaque unless explicit user/project configuration says otherwise.

The generic contract is **publish to the configured target**, not **publish to staging then promote to another site**.

Any clone, synchronization, promotion or deployment toward another WordPress instance is outside this capability.

## Why capture happens after human validation

Presentation editors may normalize or reserialize WordPress `post_content` when a human opens/saves a validated layout.

The publication fingerprint therefore must be captured from the real WordPress draft after required human visual/editor validation, not reconstructed from an earlier preparation response.

`publication_capture` is read-only. It calls Bridge-managed `article_read`, requires the post to remain a draft and computes SHA-256 over the exact current `post_content`.

It does not publish, modify or authorize anything.

## Independent gates

Publication requires all applicable conditions:

- `wordpress.enabled = true`;
- `wordpress.publish_enabled = true`;
- human editorial validation;
- required final image selection/verification;
- successful Bridge-managed draft preparation;
- human validation of the real WordPress presentation/editor state when required;
- read-only capture of that exact post-validation state;
- immutable publication candidate committed in Git;
- real WordPress draft still matching the candidate exactly;
- separate runtime `publish_now` authorization bound to the exact candidate ID;
- transport/Bridge-specific authorization requirements;
- WordPress `Article publication` permission enabled **and saved/persisted** only for the publication window.

GitHub merge approval, article validation, visual validation, `publish_enabled=true`, an enabled Bridge permission, or a previous publication approval are not substitutes for the current candidate-specific runtime gate.

## WordPress permission persistence

The Bridge stores the publication permission as:

```text
allow_article_publish
```

The WordPress admin UI exposes it as **Article publication**.

Changing the checkbox in the browser is not sufficient until the settings form is saved. A live Bridge response is authoritative for the request being executed.

If `article_publish` returns:

```text
article_publish_disabled
```

then publication was disabled for that request. The workflow must fail closed and must not infer success or retry silently.

## WordPress endpoints

Current SEO Workflow Bridge endpoints:

Preparation/read:

```text
/wp-json/seo-workflow-bridge/v1/prepare
```

Publication:

```text
/wp-json/seo-workflow-bridge/v1/publish
```

Bounded Bridge operations include:

```text
article_read
publication_preflight
article_publish
published_article_read
```

`publication_preflight` and `published_article_read` require content-read permission. `article_publish` additionally requires dedicated `Article publication` permission.

## Parent transport/orchestration operations

The relay exposes:

```text
publication_capture
publication_preflight
publish_article
published_article_read
```

`publication_capture` accepts a Bridge-managed WordPress post ID and returns a candidate snapshot. It never accepts runtime publication authorization.

The remaining operations resolve a candidate from an exact Git commit/path.

`publish_article` additionally requires runtime payload equivalent to:

```json
{
  "authorization": {
    "decision": "publish_now",
    "candidate_id": "<exact candidate id>"
  }
}
```

That authorization exists only in the runtime request. It is never written into the candidate.

## Publication candidate

Canonical path:

```text
wordpress/publish/candidates/<connection_id>/<article-slug>.json
```

Canonical schema:

```text
wordpress/publish/candidate-schema-v1.json
```

The candidate pins at least:

- `candidate_id`;
- connection/post identity;
- capture-after-human-validation state;
- explicit `authorization_included=false`;
- post type, slug, title and excerpt;
- exact `post_content` SHA-256;
- featured media ID;
- preparation manifest path;
- source commit/article path/article SHA-256;
- configured allowlisted post meta;
- configured allowlisted taxonomies.

The candidate schema intentionally excludes reusable publication authorization fields.

The parent publication relay rejects persisted authorization-like keys such as:

```text
authorization
publish_authorized
authorized
publish_now
```

The candidate is eligibility evidence only.

## Runtime authorization is single-attempt

The runtime `publish_now` authorization is bound to one candidate **and one publication attempt**.

Once a `publish_article` request carrying that authorization has been sent, treat the authorization as consumed even if the Bridge rejects the request before mutation.

For a retry after any blocked/failed publication attempt:

1. resolve the blocking cause;
2. run a fresh read-only preflight;
3. obtain a new explicit `publish_now` authorization from the user;
4. send a new request with a new request ID.

Never reuse an earlier runtime authorization automatically.

## Drift verification

Before publication, `publication_preflight` compares the current Bridge-managed draft to the immutable candidate.

Drift in any pinned field fails closed, including:

- required status/managed identity;
- post type/title/slug/excerpt;
- content SHA-256;
- featured media;
- manifest/source identities;
- declared allowlisted metadata;
- declared allowlisted taxonomies.

Intentional change after capture requires a new human validation/capture/candidate cycle.

Do not silently rebuild or update the candidate from current WordPress state simply to make preflight pass.

A retry after a permission/configuration failure must still run a fresh preflight even when the previous attempt did not mutate the post.

## Mutation boundary

After successful preflight and exact runtime authorization, the only article mutation performed by publication is:

```text
draft -> publish
```

Publication must not:

- re-render content;
- modify title/slug/excerpt;
- upload/replace media;
- change featured media;
- change taxonomy/meta;
- rebuild presentation profiles;
- trash/delete the article;
- mutate unmanaged content.

Any required content/presentation change returns to preparation/review first.

## Verification after publication

Mandatory publication evidence is:

1. successful `article_publish` result with `status = publish`;
2. independent `published_article_read` against the same immutable candidate;
3. all pinned content/source/media/meta/taxonomy checks still passing;
4. public permalink returned by WordPress, HTTPS and on the configured target.

When the assistant/runtime has network access to the public target, additionally perform an external HTTP reachability check.

If DNS/network/runtime restrictions prevent that external check, record the limitation explicitly. Do not pretend it passed, but do not re-publish an exact already-read-back candidate solely because the runtime cannot resolve the hostname.

## Least-privilege closure

`Article publication` must be disabled again after the publication window.

When the capability cannot directly change that WordPress setting:

1. instruct the user to disable it;
2. receive/record the user's confirmation when closure is part of the workflow;
3. persist the post-publication least-privilege state;
4. keep durable `publication_authorized = false`.

The enabled Bridge permission is never standing authority for future publications.

## Live-validation evidence boundary

The full capture/preflight/publish/read-back/releast-privilege flow must be validated for a new installation before it is treated as production-ready.

Installation-specific article slugs, post IDs, candidate IDs, connection IDs, URLs, hashes and human validation records belong to user/project evidence and are excluded from the generic skill package.

Reusable safety lessons remain normative:

- an unsaved WordPress permission change may still yield `article_publish_disabled`;
- a failed/blocked attempt consumes its runtime authorization;
- retry requires cause resolution + fresh preflight + new explicit `publish_now`;
- post-publication read-back must bind to the same immutable candidate;
- least privilege must be restored after the publication window.

## Safe test/publication order

1. Complete required editorial and WordPress presentation validation.
2. Keep `Article publication` disabled.
3. Run read-only `publication_capture` on the validated draft.
4. Validate/persist the exact candidate in Git with no publication authorization.
5. Run `publication_preflight` from that exact candidate commit.
6. Confirm every check passes and status remains `draft`.
7. Do not run `publish_article` until the user explicitly authorizes publication now for the exact candidate.
8. Enable WordPress `Article publication` only for that publication window **and save the WordPress settings page**.
9. Run another fresh preflight if any time/configuration step occurred after the previous one.
10. Run `publish_article` with runtime `publish_now` authorization bound to the candidate ID.
11. If that attempt is blocked or fails, consume the authorization and require a new preflight + new explicit `publish_now` before retrying.
12. On success, run `published_article_read` against the same candidate.
13. Verify the public permalink and perform external HTTP reachability when possible from the current runtime.
14. Disable `Article publication` again / return to least privilege.
15. Persist publication evidence/state and permission closure.
16. Stop: cloning/promotion/synchronization to another WordPress instance is outside this generic capability.

## Completion

Publication is complete only after:

- exact candidate-specific authorization was used for the successful attempt;
- only the intended draft -> publish mutation occurred;
- post-publication readback matches the same immutable candidate;
- public permalink identity is verified;
- external HTTP verification either succeeds or its runtime limitation is explicitly persisted;
- durable publication state is synchronized;
- publication permission is returned to least privilege.

A successful HTTP publication request alone is never sufficient evidence of publication completion.
