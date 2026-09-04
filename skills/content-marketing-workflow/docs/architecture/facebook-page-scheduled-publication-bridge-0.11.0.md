# Facebook Page scheduled publication - SEO Workflow Bridge 0.11.0

Date: 2026-09-04
Status: normative current generic runtime contract; live read-back path validated

## Scope

Bridge 0.11.0 retains the 0.9.0 exact scheduled Facebook Page publication contract and adds a **read-only post-publication verification endpoint**.

It does not weaken publication authorization, idempotency or credential handling.

## Publication endpoint

```text
POST /wp-json/seo-workflow-bridge/v1/facebook/publish-authorized
```

Publication still requires exact per-post scheduled authorization, due/stale checks, exact verified Page identity, exact text/ALT/intent/media hashes and definitive provider evidence.

## Publication-result reconciliation

Bridge idempotency may legitimately return durable evidence from an already processed publication identity rather than create a second remote object.

Therefore the GitHub relay must not treat `published=true` alone as proof that evidence belongs to the current exact authorization. Before applying success it rebinds returned evidence to the current:

```text
post_id
authorization_id
target_type
page_id
planned_at
text_sha256
image_sha256
alt_text_sha256
delivery_provider
delivery_file_id
intent_sha256
```

and requires definitive `remote_post_id`, `remote_media_id` and `published_at`.

A historical/mismatched idempotent replay fails closed as `facebook_page_evidence_binding_mismatch`; it does not update the current post to published and does not authorize a blind publication retry.

This reconciliation layer is deliberately separate from Bridge-side idempotency: Bridge remains responsible for avoiding duplicate Meta mutations; GitHub remains responsible for proving that returned evidence belongs to the exact current authorization before projecting durable current state.

## Verification endpoint

```text
POST /wp-json/seo-workflow-bridge/v1/facebook/verify-publication
```

Operation:

```text
facebook_page_verify_publication
```

The request is authenticated by the same narrow GitHub Actions OIDC trust as the dedicated Facebook publication relay.

The verification endpoint has no social mutation path.

## Verification request binding

The relay derives verification input only from the already-persisted exact authorization and definitive publication evidence:

```text
post_id
authorization_id
page_id
remote_post_id
remote_media_id
exact authorized text
text_sha256
```

The endpoint rejects Page-ID drift, malformed/unbound remote IDs and local text/hash drift before querying Meta.

The GitHub reconciliation layer additionally requires returned verification evidence to match the exact current post/authorization/Page and the already-persisted remote post/media IDs before applying `remote_verified`.

## Meta read-back

Using the WordPress-side Page Access Token, Bridge reads:

```text
/<remote_post_id>?fields=id,message,created_time,permalink_url
/<remote_media_id>?fields=id
```

with the configured Graph API version and Authorization Bearer header.

`remote_verified` requires:

- HTTP 200 read-back;
- exact remote post ID returned;
- exact authorized message SHA-256 match;
- exact remote media ID returned;
- configured/verified Page still equals the authorized Page.

The token is never returned to GitHub.

## Eventual consistency

The GitHub relay may repeat only the read-back request for a short bounded window when Meta has not yet exposed the newly created object.

Publication mutation is never repeated because read-back is delayed.

## Durable states

Successful read-back:

```text
execution.publication_state = published
execution.state = remote_verified
execution.verification.verification_state = remote_verified
facebook.status = published
facebook.verification_state = remote_verified
```

Definitive publication with failed read-back:

```text
execution.publication_state = published
execution.state = published
execution.verification.state = verification_failed
facebook.status = published
```

The latter is not retryable publication state.

Mismatched/historical success evidence for the current authorization:

```text
execution.state = uncertain_external_result
last_error.code = facebook_page_evidence_binding_mismatch
requires_human_reconciliation = true
```

This state is fail-closed and is not a publication retry instruction.

## Relay conclusion

A fully green Facebook publication relay now means:

```text
definitive provider creation evidence
+ exact current-authorization evidence binding
+ durable evidence persistence
+ successful remote read-back verification
```

A green **scheduler** still means only that due authorization discovery/relay dispatch succeeded.

## Notifications

After reconciliation, the relay may invoke the optional Telegram publication reporter. Notification failure never changes the publication/verification state and never causes publication retry.

## Backward compatibility

Bridge 0.11.0 preserves the 0.10.0 connection-health endpoint and the 0.9.0 publication endpoint semantics. Existing Page credentials/settings are retained on plugin upgrade.

The additional evidence-binding hardening is implemented in the generic GitHub reconciliation layer and does not require another WordPress plugin upgrade after 0.11.0.

## Live-validation evidence boundary

The generic contract records only that the 0.11.0 Facebook read-back path has been validated end to end. Concrete test post IDs, Page IDs, remote IDs, run IDs and permalinks remain in excluded user/project checkpoint state, not in the distributable skill package.

## References

- `docs/architecture/facebook-page-scheduled-publication-bridge-0.9.0.md`
- `docs/architecture/capabilities/social-publication-verification.md`
- `docs/architecture/capabilities/social-publish.md`
- `docs/architecture/capabilities/telegram-publication-notifications.md`
