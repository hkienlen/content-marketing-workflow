# LinkedIn scheduled publication - SEO Workflow Bridge 0.8.0

Date: 2026-09-03
Status: normative current contract

This contract supersedes `docs/architecture/linkedin-scheduled-publication-bridge-0.7.0.md` for the current unattended scheduled-publication path.

Canonical companion capability inventory:

```text
docs/architecture/seo-workflow-bridge-capabilities.md
```

Scheduler contract:

```text
docs/architecture/linkedin-github-actions-scheduler.md
```

Future-skill companion binding:

```text
docs/architecture/single-skill-bridge-companion-contract.md
```

## User-facing behavior

The normal WordPress LinkedIn settings screen is for useful connection/configuration state. The earlier technical pilot panels for identity/media probing, dry-run and manual live publication are internal diagnostics and are not registered in the ordinary UI.

Normal users do not configure server cron, systemd, daemons or a separate publisher service. Scheduling and exact per-post authorization are managed by the skill and durable GitHub state; GitHub Actions owns timing.

## Publication endpoint

Bridge `0.8.0` exposes:

```text
POST /wp-json/seo-workflow-bridge/v1/linkedin/publish-authorized
```

This endpoint is the actual publication path. It is not a non-publishing preflight endpoint.

It accepts only a fresh GitHub Actions OIDC-authenticated request carrying an exact candidate paired with an exact per-post authorization whose status is:

```text
authorized_for_scheduled_publication
```

## OIDC trust

The Bridge remains fail-closed on GitHub OIDC signature/time plus configured trust identity, including:

- issuer;
- audience;
- repository ID;
- repository owner ID when configured;
- repository name when configured;
- private-repository requirement;
- allowed event name;
- allowed workflow reference.

The dedicated scheduled publication relay uses `workflow_dispatch` and the trusted workflow:

```text
.github/workflows/linkedin-publish-relay.yml@refs/heads/main
```

The existing issue-driven WordPress article relay remains a separate flow.

## Exact authorization binding

The candidate contains the deterministic source state required to reconstruct the publication only after runtime media upload.

The authorization binds at minimum:

- immutable `post_id`;
- timezone-aware `planned_at`;
- LinkedIn `author_urn`;
- exact text SHA-256;
- exact ALT-text SHA-256;
- exact selected-final image SHA-256;
- image MIME type;
- exact image byte size;
- delivery provider;
- exact temporary Drive `tmp-outbox` delivery file ID;
- deterministic publication-intent SHA-256;
- authorization ID;
- authorization timestamp.

The exact text and ALT are also carried in the candidate and are rehashed by the Bridge immediately before publication.

A post being approved, final, scheduled, due, present in GitHub or associated with a connected LinkedIn account is never sufficient by itself.

Changing text, ALT, selected image bytes/metadata, author or `planned_at` invalidates the authorization.

## Why runtime payload hash is not an authorization field

Bridge `0.8.0` creates the LinkedIn image URN only at execution time. The final LinkedIn Posts API payload therefore cannot be deterministically hashed during human preauthorization.

Preauthorization binds the deterministic publication intent plus the exact source image bytes/metadata. After the runtime image upload, the Bridge builds the final payload and stores its SHA-256 as publication evidence.

The runtime `payload_sha256` is evidence, not a preauthorization identity field.

## Media delivery contract

The retained selected final remains private and canonical in the configured provider workspace.

For Google Drive:

```text
private final
-> exact temporary public-by-link read-only tmp-outbox copy
-> persist delivery file identity + expected hash/MIME/size
-> Bridge downloads the delivery copy at execution
-> Bridge verifies exact byte size
-> Bridge verifies SHA-256
-> Bridge detects/verifies PNG or JPEG MIME
-> only verified bytes may be uploaded to LinkedIn
```

The temporary delivery copy is transport only. It never replaces the retained private final identity.

No Google OAuth/service-account credential is introduced into GitHub Actions for this path.

## Due-time and connection checks

Before any LinkedIn media upload or post creation, Bridge verifies:

- request freshness and replay protection;
- exact authorization binding;
- current time is not before `planned_at`;
- the candidate is not more than 24 hours late;
- LinkedIn capability is enabled;
- access token exists and is unexpired;
- verified member identity exists;
- current member exactly matches the authorized `author_urn`;
- text and ALT hashes match;
- publication-intent hash matches;
- exact delivery image bytes/hash/MIME/size match.

A failure blocks publication.

## LinkedIn runtime sequence

After all deterministic checks pass, Bridge may:

1. initialize a LinkedIn Images API upload for the verified author;
2. upload the exact verified image bytes;
3. obtain the runtime `urn:li:image:...`;
4. build the final Posts API payload with the exact text, ALT and runtime image URN;
5. create the LinkedIn post with `lifecycleState: PUBLISHED`.

LinkedIn itself is not used as the future scheduler.

## Success evidence

A publication is successful only with:

```text
HTTP 201
x-restli-id: <remote post identifier>
```

Bridge persists successful evidence before returning success, including where available:

- `post_id`;
- `authorization_id`;
- remote post ID;
- actual `published_at`;
- `planned_at`;
- author URN;
- text/image/ALT/intent hashes;
- delivery provider/file ID;
- runtime LinkedIn image URN;
- runtime payload SHA-256;
- LinkedIn API version;
- HTTP status;
- GitHub Actions run ID.

GitHub synchronization then reconciles that evidence into the durable authorization/post state.

## Idempotency and historical pilot evidence

Blind retry after an uncertain external result is forbidden.

Scheduled-publication evidence is persisted separately from the historical manual live-pilot evidence. A historical manually published/deleted pilot post must not, by itself, block a later independently authorized scheduled publication.

For the scheduled path, if Bridge already has successful scheduled evidence for the same `post_id`, an exact recovery attempt returns the stored successful evidence instead of creating another LinkedIn post.

This protects the state:

```text
LinkedIn creation succeeded
-> GitHub synchronization failed
```

## Scheduler responsibility

The generic scheduler scans only durable exact authorization records and runs every 10 minutes:

```text
validated/final post
-> planned_at
-> explicit exact per-post authorization
-> exact tmp-outbox delivery copy
-> linkedin-scheduler.yml discovers due authorization
-> workflow_dispatch linkedin-publish-relay.yml
-> short-lived GitHub OIDC
-> Bridge final verification/media upload/publication
-> Bridge evidence
-> GitHub reconciliation
```

`planned_at` is the earliest allowed time. GitHub Actions may run a few minutes later; actual `published_at` must be persisted separately.

No post ID is hard-coded into the scheduler. If only posts `xx` and `yy` are authorized, only those exact records are eligible.

## Safe preflight before due time

Because `/linkedin/publish-authorized` is the real publication endpoint, do not invoke it merely to test readiness before the due time.

A non-publishing readiness check is limited to safe evidence such as:

- `site_info` confirms compatible Bridge version and LinkedIn connection/member state;
- exact authorization record validates and remains pending/retryable as appropriate;
- due-time calculation shows the post is not yet due;
- temporary delivery identity/hash/MIME/size and anonymous read permission are verified;
- trusted workflow/configuration files are present and contract tests are green.

## Cleanup

After verified publication and durable evidence reconciliation, the temporary `tmp-outbox` delivery copy should be removed when practical. The retained private final remains canonical.
