# Single skill - SEO Workflow Bridge companion contract

Date: 2026-09-04
Status: normative skill companion contract

## Mandatory relationship

The single installable Content / Marketing skill treats `SEO Workflow Bridge` as its canonical mainstream WordPress companion component for WordPress and enabled WordPress-hosted social adapters.

The skill loads/follows the relevant subset of:

- `docs/architecture/seo-workflow-bridge-capabilities.md`
- `docs/architecture/seo-workflow-bridge-onboarding.md`
- `docs/architecture/seo-workflow-bridge-versioning.md`
- `docs/architecture/linkedin-publication-onboarding.md`
- `docs/architecture/linkedin-scheduled-publication-bridge-0.8.0.md`
- `docs/architecture/facebook-page-publication-onboarding.md`
- `docs/architecture/facebook-page-token-provisioning-contract.md`
- `docs/architecture/facebook-login-for-business-configuration.md`
- `docs/architecture/facebook-page-standing-publication-policy.md`
- `docs/architecture/facebook-page-scheduled-publication-bridge-0.11.0.md`
- `docs/architecture/facebook-github-actions-scheduler.md`
- `docs/architecture/capabilities/social-connection-health.md`
- `docs/architecture/capabilities/social-publication-verification.md`

according to the requested capability.

Historical Bridge/version documents may remain development history, but product runtime must select the newest compatible current contract rather than silently falling back to an older implementation path.

## Product behavior

Bridge is optional until a capability requiring it is enabled.

Offer install/upgrade:

1. initial onboarding when WordPress or a Bridge-hosted social adapter is selected;
2. when WordPress preparation/publication is later activated;
3. when LinkedIn publication is later activated;
4. when Facebook Page publication is later activated;
5. when live social connection-health probes or Facebook remote verification require a newer Bridge;
6. whenever installed Bridge version is below the requested capability minimum.

Ordinary path = WordPress ZIP installation. Do not require server administration, SSH, Python/WSGI, systemd, reverse-proxy changes or server cron.

After install/upgrade, verify active version through a safe available transport when possible.

## Capability minimums

Current minimums are capability-specific:

```text
WordPress bounded/preparation/publication features -> per their declared current minimums
LinkedIn runtime-media scheduled publication -> Bridge 0.8.0+
Facebook Page scheduled publication -> Bridge 0.9.0+
read-only social connection-health provider probes -> Bridge 0.10.0+
Facebook post-publication remote verification -> Bridge 0.11.0+
```

The current distributed companion target for the complete feature set is:

```text
SEO Workflow Bridge 0.11.0
```

A future version may supersede this; the skill must compare installed version to the capability actually requested rather than hard-code upgrade prompts unrelated to the user's enabled scope.

## LinkedIn adapter invariant

The current LinkedIn adapter:

- targets the authenticated verified member from active user/project connection state;
- keeps Client Secret/access token on WordPress;
- requires exact per-post scheduled authorization;
- verifies exact text/ALT/media/delivery/time/author;
- uploads runtime image through LinkedIn Images API;
- accepts definitive success only with HTTP `201` + `x-restli-id`;
- persists Bridge-side definitive-success evidence before GitHub reconciliation;
- reconciles successful creation as `published + provider_acknowledged` when independent member-post read-back is unavailable under the current permission scope;
- must never label that state `remote_verified` without a supported independent read-back path.

## Facebook Page adapter invariant

The current Facebook adapter uses:

```text
target_type = facebook_page
```

and never reinterprets a personal/professional Facebook profile as an API Page target.

Bridge owns WordPress-side:

- exact Page ID;
- Page Access Token;
- verified Page ID/name evidence;
- provider credential data needed for mutation/read-back.

GitHub may persist non-secret Page ID/name/configuration/policy/expiry/health state but never the Page token.

Provider API version and concrete application/configuration/Page values are active user/project data. They are not generic skill constants.

The granting Meta user/token must have sufficient Page task access to create content.

Page connection verification is read-only and does not create a post.

## Generic Meta/WordPress onboarding

The skill preserves the validated provider flow without shipping one installation's identity:

```text
Meta for Developers registration if needed
-> compatible app/use case
-> minimum Page permissions
-> Facebook Login for Business configuration when required
-> obtain/inspect User Access Token using provider tooling
-> GET /me/accounts?fields=id,name,tasks
-> obtain/extend long-lived user credential when required
-> GET /me/accounts?fields=id,name,access_token,tasks
-> select exact intended Page Access Token
-> verify token type/target/validity with provider tooling
-> Page token entered directly in WordPress
-> read-only Verify Facebook Page
-> scheduler/relay readiness
-> controlled first live publication
```

Raw User/Page tokens and App Secret never belong in GitHub or chat. Exposed-token revocation/rotation is recovery behavior, not a normal step to repeat during every onboarding.

## UI invariant

Ordinary users manage only useful configuration/connection state through the WordPress Bridge settings screens for enabled capabilities.

They must not operate internal diagnostic publication gates as part of normal use.

Stored platform secrets must never be rendered back in clear text. Secret fields must use a keep-existing/replace-only interaction rather than displaying stored values.

## Exact authorization invariant

Runtime publication authorization is per platform, per post and per exact revision/time.

Never infer an executable Bridge authorization merely from:

- post created/approved/final;
- visual approved;
- `status: scheduled`;
- `planned_at`;
- Bridge installed/active;
- LinkedIn OAuth connected;
- Facebook Page token configured/identity verified;
- a standing user publication-consent policy.

Every unattended execution still requires:

```text
authorized_for_scheduled_publication
```

Common binding includes exact post/time/text/ALT/image/delivery/intent. Platform-specific target identity is bound as well:

```text
LinkedIn -> author/member identity
Facebook -> facebook_page + exact Page ID
```

Changing a bound value invalidates that platform's authorization.

Authorizing/configuring one platform never authorizes another.

## Publication-consent policy invariant

The skill may determine **how the exact authorization record is materialized** from an explicitly user-approved policy:

```text
one_off_exact_confirmation
standing_auto_publish_scheduled
```

The selected policy belongs to user/project data.

When `standing_auto_publish_scheduled` is active, a fully approved post with exact durable schedule may materialize its exact per-post authorization automatically after final text/visual/ALT/schedule validation. This removes repetitive prompts but does not weaken runtime binding.

The policy never bypasses:

- exact authorization record;
- target/time/content/media binding;
- Bridge prepublication verification;
- due-time/stale-window gates;
- duplicate/idempotency handling;
- uncertain-result blocking.

Immediate `publish_now` remains a separate explicit decision unless a future dedicated policy explicitly changes that rule.

## Media-delivery invariant

The retained provider-backed final remains canonical.

Unattended publication may use an exact public-by-link read-only `tmp-outbox` copy only as transport. The Bridge re-downloads and verifies exact bytes immediately before remote mutation.

No Google service-account/OAuth secret is required in GitHub Actions merely for the current public-link tmp-outbox scheduler transport.

## Scheduler invariant

GitHub Actions owns timing.

LinkedIn:

```text
validated/final post
-> planned_at + exact LinkedIn authorization
-> linkedin-scheduler.yml
-> linkedin-publish-relay.yml
-> Bridge
-> LinkedIn
```

Facebook Page:

```text
validated/final post
-> planned_at
-> applicable publication-consent policy materializes exact Facebook authorization
-> facebook-scheduler.yml
-> facebook-publish-relay.yml
-> Bridge
-> Meta Page
```

Schedulers contain no hard-coded post IDs. Only due exact authorization records are eligible.

`planned_at` is the earliest allowed time; actual `published_at` may be later and must be persisted.

Scheduler success means due-selection/dispatch succeeded. It is not provider publication evidence.

## Provider evidence and post-publication verification

Definitive provider creation evidence must first be proven to belong to the current exact authorization.

Facebook:

```text
provider creation acknowledged
-> durable published state
-> bounded read-only remote post/media verification
-> remote_verified only when supported checks pass
```

If provider creation is definitive but read-back fails, do not republish. Preserve the truthful published/verification-failed state for reconciliation.

LinkedIn:

```text
HTTP 201 + x-restli-id
-> durable published state
-> provider_acknowledged
```

Current member publication permissions do not provide the independent post read-back needed to claim `remote_verified`. A future adapter/scope may add that capability only through an explicit contract change.

## Live-validation evidence boundary

A new adapter/installation requires controlled live validation before production readiness.

Concrete test post IDs, workflow run IDs, Page/member IDs, remote publication/media IDs, timestamps and human confirmation are user/project evidence and remain outside the generic skill package.

The generic contract contains only reusable safety semantics learned from those validations.

Future sessions for a configured project must resume from its durable verified checkpoint rather than restarting provider onboarding unless an actual connection/credential/configuration problem is detected.

## Relay/OIDC separation

Keep platform publication relays separate from the bounded WordPress relay and from each other.

Bridge trust remains pinned to configured repository/owner/audience/private-repository/workflow claims. Enabling another adapter may add only its explicit dedicated workflow identity; it must not introduce wildcard workflow trust.

Real `publish-authorized` endpoints are not preflight endpoints.

## Idempotency / ambiguous results

Definitive success evidence must be persisted Bridge-side before GitHub synchronization so later exact requests reconcile rather than duplicate.

Evidence from a previous exact authorization must not be accepted for a new authorization unless the full current binding matches.

Blind retry after uncertain external creation is forbidden.

Facebook uncertain external creation reconciles to an `uncertain_external_result`-equivalent state requiring reconciliation and excluded from automatic retry.

## Social connection health

Bridge 0.10.0+ provides bounded read-only provider identity/credential probes used by the generic connection-health capability.

Health probing:

- never publishes;
- never returns raw provider credentials;
- compares observed provider identity with active profile identity;
- records non-secret validity/expiry/next-action metadata only within the narrow machine-maintained fields allowed by the user-profile contract.

Credential renewal remains provider/user-driven unless a future explicit credential-rotation capability is implemented.

## Telegram boundary

Telegram publication reporting is not a Bridge credential responsibility in the current GitHub Actions notification adapter.

The bot token remains in the configured GitHub Actions secret owner. Bridge publication success/failure evidence may feed the GitHub-side reporter only after durable reconciliation.

Notification delivery failure never changes provider publication state and never causes republication.

## Upgrade behavior

The skill compares installed Bridge version against the requested capability minimum and provides a directly installable compatible ZIP when required.

Every distributed code change receives a distinct plugin version and no nested archive.

Installing/upgrading Bridge or connecting a social account does not itself create runtime publication authorizations.

## References

- `docs/architecture/seo-workflow-bridge-capabilities.md`
- `docs/architecture/seo-workflow-bridge-onboarding.md`
- `docs/architecture/seo-workflow-bridge-versioning.md`
- `docs/architecture/capabilities/social-publish.md`
- `docs/architecture/capabilities/social-publication-verification.md`
- `docs/architecture/capabilities/social-connection-health.md`
- `docs/architecture/facebook-github-actions-scheduler.md`
