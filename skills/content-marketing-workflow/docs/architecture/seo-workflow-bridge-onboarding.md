# SEO Workflow Bridge onboarding

Date: 2026-09-04
Status: normative generic onboarding contract

## Purpose

Defines how the installable Content / Marketing skill configures or resumes the SEO Workflow Bridge for one active user/project.

This contract contains **behavior and placeholders only**. Site URLs, repository identifiers, social account IDs, application IDs, publication preferences, notification preferences, expiry metadata and other concrete values are loaded from the active user profile/project data.

## User-data authority

Generic schema:

```text
docs/architecture/schemas/user-profile.schema.json
```

Normative boundary:

```text
docs/architecture/user-profile-data-contract.md
```

The skill must never copy pilot/example values into a new installation.

## Bridge baseline

Current companion release:

```text
SEO Workflow Bridge 0.11.0+
```

Install through the normal WordPress plugin UI using the directly installable artifact produced by CI.

After installation, verify the displayed plugin version before enabling dependent capabilities.

Capability minimums remain explicit: LinkedIn scheduled publication 0.8.0+, Facebook Page scheduled publication 0.9.0+, social connection-health 0.10.0+, Facebook Page post-publication read-back 0.11.0+.

## WordPress connection

Resolve from the active profile:

```text
project.wordpress.site_url
project.wordpress.bridge.connection_id
project.wordpress.bridge.endpoint
project.wordpress.bridge.audience
project.repository.*
```

The Bridge settings must bind GitHub Actions OIDC trust to the exact configured private repository, repository/owner IDs when available, audience and workflow reference.

Connection setup does not authorize article or social publication.

## Capability levels

The user/project profile owns durable capability choices such as:

```yaml
wordpress:
  enabled: true|false
  publish_enabled: true|false
social:
  enabled: true|false
```

These flags control availability only. They never replace exact publication authorization.

## Article workflow

When WordPress article support is enabled:

```text
validated repository article
-> Bridge-managed draft preparation
-> WordPress presentation review
-> exact post-validation candidate
-> separate publish_now gate when publication is enabled
```

Preparation and publication remain separate capabilities.

## LinkedIn onboarding

When LinkedIn publication is enabled or later requested, follow:

```text
docs/architecture/linkedin-publication-onboarding.md
```

The active profile stores non-secret connection metadata such as:

- enabled/configured state;
- expected member identity/URN;
- scopes/products as observed;
- preferred publication time;
- token expiration metadata;
- last verified health state.

LinkedIn Client Secret and access token remain in WordPress only.

After a definitive scheduled publication, the current member adapter records `provider_acknowledged`: LinkedIn returned the expected creation evidence, but current access does not support independent member-post read-back. This must not be labelled `remote_verified`.

## Facebook Page onboarding

When Facebook Page publication is enabled or later requested, follow:

```text
docs/architecture/facebook-page-publication-onboarding.md
```

The active profile stores non-secret metadata such as:

- `target_type = facebook_page`;
- exact Page ID/name;
- Meta application/configuration IDs when applicable;
- Graph API version;
- observed permissions/tasks;
- preferred publication time;
- non-secret token/data-access expiration metadata;
- standing publication-consent policy;
- last verified health state.

The Page Access Token remains in WordPress only.

Personal/professional Facebook profiles are not supported API publication targets.

With Bridge 0.11.0+, a successful Facebook relay also performs read-only post-publication verification against the exact Bridge-persisted publication evidence. The verifier checks the created post/media IDs and exact message hash. Successful read-back produces `remote_verified`; read-back failure after definitive creation does not make the publication retryable.

## Social connection health

Bridge `0.10.0+` exposes the bounded read-only relay operation:

```text
social_connection_health
```

The skill uses it to verify current provider credentials/identity without receiving the credential itself. The resulting non-secret health metadata is reconciled into the active user profile.

Health checks must also inspect scheduled social content and exact pending authorizations. If a planned publication occurs at or beyond the effective known validity boundary, the connection is surfaced for renewal before that publication.

Default warning thresholds are skill behavior:

```text
J-30
J-14
J-7
expired/invalid
```

Actual expiry dates belong to user/project data.

## Optional Telegram publication reports

Telegram reports are optional and independent of Bridge connectivity. During initial onboarding, when social publication is enabled, the skill may ask once whether the user wants a Telegram report after social publications. The answer is a user/project preference.

Before configuring anything, inspect:

```text
projects.<active_project>.notifications.telegram
```

If an existing verified configuration is present, reuse/re-enable it rather than recreating a bot. If configuration is missing or needs repair, follow the exact guided procedure in:

```text
docs/architecture/user-help-telegram-notifications.md
```

Credential boundary:

```text
TELEGRAM_BOT_TOKEN -> GitHub Actions Repository Secret only
chat_id / bot_username / enabled / report preferences -> user profile
```

The skill must never ask the user to paste the bot token into chat or repository files.

Telegram reports are sent only after durable publication/verification state has been reconciled. Notification failure never authorizes or retries a social publication.

## Resume-first behavior

On every setup or reconnect request:

1. load the active user profile;
2. inspect current Bridge/notification state read-only where applicable;
3. compare it with durable non-secret metadata;
4. resume from the last verified milestone;
5. ask only for missing values/actions that cannot be discovered safely;
6. never request raw access tokens/bot tokens in chat;
7. persist newly verified non-secret metadata immediately;
8. re-read the resulting state before reporting completion.

Do not restart OAuth/Meta/BotFather setup from zero merely because the conversation is new.

## Secret boundary

Never store in GitHub/user profile:

```text
access token
refresh token
Page Access Token
App Secret
client secret
OAuth authorization code
Telegram bot token
password/private key
```

The profile may store only lifecycle/routing metadata needed to manage those secrets, for example:

```yaml
secret_location: wordpress_seo_workflow_bridge
token_expires_at: <timestamp|null>
data_access_expires_at: <timestamp|null>
last_observed_valid: true|false|null
last_observed_at: <timestamp|null>
```

and for Telegram:

```yaml
notifications:
  telegram:
    enabled: false
    setup_status: not_configured|verified
    chat_id: <numeric string|null>
    bot_username: <string|null>
    secret_name: TELEGRAM_BOT_TOKEN
```

## OIDC scheduled-health trust

The daily social-health workflow may authenticate to the Bridge with a scheduled GitHub OIDC token, but only when the exact workflow reference resolves to:

```text
.github/workflows/social-connection-health.yml@refs/heads/main
```

The `schedule` event must not implicitly authorize LinkedIn or Facebook publication relay workflows.

The Facebook publication relay may call the 0.11 read-only verification endpoint using the same exact relay OIDC trust. This does not broaden the relay to arbitrary Bridge reads: the verifier is additionally bound to definitive Bridge publication evidence for that post.

## GitHub token format compatibility

GitHub-provided installation/runtime tokens are opaque and variable-length. Workflows must not parse `ghs_...`, assume legacy fixed lengths, or confuse those tokens with GitHub Actions OIDC JWTs.

Normative compatibility contract:

```text
docs/architecture/github-app-installation-token-compatibility.md
```

## Validation order

Use the safest proof first:

```text
configuration/schema validation
-> read-only Bridge/site_info
-> read-only social credential health where relevant
-> temporary/idempotent tests only when necessary
-> externally visible mutation only under the applicable publication gate
-> read-only post-publication verification when supported
-> optional notification test/report after user opt-in
```

Connection onboarding must never publish merely to prove connectivity.

## Completion

Bridge/onboarding is complete for the enabled scope only when:

- compatible Bridge version is installed;
- exact repository/OIDC configuration is verified;
- required enabled capabilities are configured;
- non-secret user/project metadata is persisted in the profile/declared authority;
- secrets remain outside GitHub content/profile;
- social connections, when enabled, have a resumable verified health state;
- optional Telegram preference/configuration is either explicitly disabled or verified when enabled;
- blockers are explicit rather than silently ignored.

## References

- `docs/architecture/user-profile-data-contract.md`
- `docs/architecture/persistence-contract.md`
- `docs/architecture/capabilities/wordpress-connect.md`
- `docs/architecture/capabilities/social-connection-health.md`
- `docs/architecture/capabilities/social-publication-verification.md`
- `docs/architecture/capabilities/telegram-publication-notifications.md`
- `docs/architecture/linkedin-publication-onboarding.md`
- `docs/architecture/facebook-page-publication-onboarding.md`
- `docs/architecture/facebook-page-scheduled-publication-bridge-0.11.0.md`
- `docs/architecture/user-help-telegram-notifications.md`
- `docs/architecture/github-app-installation-token-compatibility.md`
- `docs/architecture/testing-policy.md`
