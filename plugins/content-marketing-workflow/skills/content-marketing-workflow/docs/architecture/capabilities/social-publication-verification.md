# Internal capability: social-publication-verification

Date: 2026-09-04
Status: current capability contract

## Purpose

Separate **remote creation acknowledgement** from **post-publication read-back verification** so a green scheduler is never treated as proof by itself that content was deployed correctly.

The publication lifecycle is platform-specific:

```text
Facebook Page
scheduled -> publication attempted -> published -> verification_state=remote_verified

LinkedIn member
scheduled -> publication attempted -> published -> verification_state=provider_acknowledged
```

`published` remains the provider-creation event/status. Verification is a separate dimension that records what can actually be proven with the permissions available to that connection.

## Scheduler versus relay semantics

The platform scheduler only finds due exact authorizations and dispatches the dedicated relay.

```text
scheduler success
= due detection + relay dispatch completed
!= remote publication proof
```

The relay owns publication evidence and final verification state.

For Facebook Page, relay success after Bridge 0.11.0 means publication evidence was persisted **and** the created remote post/media passed read-back verification. If publication is confirmed but read-back verification fails, the relay may finish red while durable publication status remains `published`; it must never re-publish merely to repair verification.

For LinkedIn, relay success means the provider accepted creation and returned definitive creation evidence. With the current member connection, direct post read-back is not available, so verification is `provider_acknowledged` rather than `remote_verified`.

## Exact publication-evidence binding

A provider/Bridge response with `published=true` is not sufficient by itself to mark the **current** exact authorization as published.

Before applying success, the relay reconciliation layer must verify that returned evidence still belongs to the exact current candidate/authorization. For Facebook this includes at minimum:

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
remote_post_id
remote_media_id
published_at
```

This protects against a legitimate historical idempotency replay for the same editorial post ID being mistaken for a new current publication.

If returned success evidence belongs to a different authorization/revision/schedule/intent, the current record must fail closed rather than inherit that evidence. Current Facebook behavior records:

```text
execution.state = uncertain_external_result
last_error.code = facebook_page_evidence_binding_mismatch
requires_human_reconciliation = true
```

It must not update current post frontmatter to `published`, and it must not blindly retry the publication mutation.

Post-publication verification evidence must likewise be rebound to the exact current post/authorization/Page and to the already-persisted remote post/media IDs before `remote_verified` is applied.

## Facebook Page: `remote_verified`

Prerequisites:

- definitive creation evidence from Meta;
- exact Page ID still matches the configured verified Page;
- current Page credential can read Page engagement/content;
- `remote_post_id` and `remote_media_id` exist;
- published message matches the exact authorized text hash.

Current read-back endpoint:

```text
POST /wp-json/seo-workflow-bridge/v1/facebook/verify-publication
```

The endpoint is authenticated with the same narrow GitHub Actions OIDC trust used by the Facebook publication relay. It performs no social mutation.

Read-back evidence may include:

```text
verification_state = remote_verified
checked_at
remote_post_id
remote_media_id
provider_http_status = 200
message_matches = true
media_exists = true
created_time
permalink_url
```

The raw Page Access Token is never returned.

### Eventual consistency

Immediately created provider objects may need a short propagation delay before a read succeeds. The relay may retry the **read-only verification** a small bounded number of times.

It must never retry the Facebook publication mutation solely because verification was delayed or failed.

If the provider confirms creation but read-back cannot be proven:

```text
publication_state = published
execution.state = published
verification.state = verification_failed
```

The operator/report must distinguish this from publication failure.

## LinkedIn member: `provider_acknowledged`

Definitive creation currently requires:

```text
HTTP 201
x-restli-id
published_at
exact member/content/media evidence
```

The connection currently has publication access but not the restricted member-social read-back permission required for an independent GET of member posts.

Therefore the final deployment verification state is:

```text
publication_state = published
execution.state = provider_acknowledged
verification.state = provider_acknowledged
verification.readback_available = false
```

This must not be presented as `remote_verified`.

If a future LinkedIn connection obtains a supported read permission, the skill may add a true read-back verification adapter without changing the meaning of existing historical `provider_acknowledged` evidence.

## Durable state

Exact authorization records keep publication and verification evidence separate:

```json
{
  "execution": {
    "publication_state": "published",
    "state": "remote_verified | provider_acknowledged | published | retryable_error | uncertain_external_result",
    "evidence": {},
    "verification": {}
  }
}
```

Materialized social post frontmatter keeps the platform publication status stable and exposes verification separately:

```yaml
facebook:
  status: published
  verification_state: remote_verified

linkedin:
  status: published
  verification_state: provider_acknowledged
```

`published_at` and remote IDs remain preserved independently of the verification label.

## Failure safety

- publication failure before definitive provider creation stays retryable only under the existing exact authorization/idempotency contract;
- uncertain external creation blocks blind retry;
- historical/mismatched idempotency evidence must never be applied as current publication success;
- verification failure after definitive publication never authorizes a second publication;
- Telegram/email/reporting failure never changes remote publication state;
- exact runtime gates remain mandatory before every publication mutation.

## Notification relationship

After publication/verification state is reconciled, an enabled notification adapter may send a human report.

Current generic optional adapter:

```text
docs/architecture/capabilities/telegram-publication-notifications.md
```

Notification preference belongs to user/project data. Notification credential values do not.

## References

- `docs/architecture/capabilities/social-publish.md`
- `docs/architecture/capabilities/social-schedule.md`
- `docs/architecture/user-profile-data-contract.md`
- `docs/architecture/facebook-page-scheduled-publication-bridge-0.11.0.md`
- `docs/architecture/capabilities/telegram-publication-notifications.md`
