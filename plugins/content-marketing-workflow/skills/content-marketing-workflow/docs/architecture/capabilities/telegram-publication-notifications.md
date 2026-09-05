# Internal capability: telegram-publication-notifications

Date: 2026-09-05
Status: current capability contract

## Purpose

Send optional Telegram reports after social publication state has been reconciled, and support explicit setup, status/configuration and diagnostic test operations for the notification channel.

The capability is optional and user-controlled.

## Public operations

The public command catalogue exposes this capability through:

```text
/social notifications telegram
  operation: configure

/social notifications telegram test
  operation: test
```

The `test` operation is diagnostic notification delivery only. It must never publish, schedule, retry or modify Facebook/LinkedIn content.

## Ownership boundary

User/project profile owns the preference and non-secret destination metadata:

```yaml
notifications:
  telegram:
    enabled: false
    setup_status: not_configured | verified
    chat_id: <numeric chat id or null>
    bot_username: <bot username or null>
    secret_name: TELEGRAM_BOT_TOKEN
    configured_at: <timestamp or null>
    last_verified_at: <timestamp or null>
    publication_reports:
      success: true
      failure: true
      uncertain: true
```

The bot token is a secret and must never be stored in the user profile, repository content, skill package or chat.

Current GitHub Actions secret convention:

```text
TELEGRAM_BOT_TOKEN
```

## Activation policy

Telegram notifications may be:

- offered during onboarding;
- enabled later on explicit request;
- disabled later on explicit request;
- explicitly tested later;
- reconfigured when bot/token/chat changes.

Before starting a fresh setup, the skill must inspect the active user profile.

### Already configured and enabled

When all are true:

```text
enabled = true
setup_status = verified
chat_id exists
bot_username exists
```

report the existing configuration and do not recreate the bot. Offer `/social notifications telegram test` when useful.

### Configured but disabled

When `setup_status = verified` and `chat_id` exists but `enabled = false`, re-enable the existing configuration rather than forcing BotFather setup again. If the previous verification is old or the user reports a problem, the explicit test operation may be run first without changing `enabled`.

### Not configured

Guide the user through the exact BotFather + GitHub Secret + chat discovery/verification procedure in:

```text
docs/architecture/user-help-telegram-notifications.md
```

Do not ask the user to paste the bot token into chat.

## Setup workflow

Generic workflow:

```text
.github/workflows/telegram-notification-setup.yml
```

Supported semantics:

```text
discover -> verify bot token and list candidate chat IDs after the user has messaged the bot
verify   -> verify exact chat, send one test message, persist enabled=true and non-secret bot/chat metadata
disable  -> set enabled=false while retaining verified non-secret configuration for easy re-enable
test     -> use existing persisted destination to verify the bot/chat and send one diagnostic message without changing enabled
```

If the packaged GitHub workflow does not yet expose a literal `test` input mode, the command may reuse the safe verification path with the persisted chat ID, provided the implementation preserves the existing `enabled` preference and records only non-secret verification evidence. It must not require the user to recreate the bot or re-enter routing metadata that is already durably known.

The workflow reads the repository secret at runtime. GitHub Actions masks the secret; scripts must not print the token or construct log messages containing the Bot API URL with the token.

## Explicit test contract

`operation: test` requires durable non-secret configuration sufficient to identify the existing destination:

```text
setup_status = verified
chat_id exists
secret_name exists
```

The runtime must:

1. resolve the active project repository and persisted Telegram configuration;
2. use the configured secret reference without exposing the token;
3. verify bot/chat reachability through the supported runtime;
4. send exactly one diagnostic Telegram message;
5. update `last_verified_at` and other supported non-secret verification metadata on success;
6. preserve the existing `enabled` value unless the user separately requested enable/disable;
7. report failure separately from all social publication state.

A test failure must never cause a social publication retry or duplicate publication.

## Publication report workflow

Current reporter:

```text
scripts/telegram-publication-report.py
```

It is invoked by the platform publication relay after durable publication/verification state has been updated.

Typical success reports:

```text
Facebook: published + remote_verified
LinkedIn: published + provider_acknowledged; read-back unavailable with current access
```

Failure reports distinguish:

```text
retryable publication failure
uncertain external publication result
published but Facebook remote verification failed
notification delivery failure
```

A Telegram failure must **never** change a successful social publication into a retryable publication and must never trigger a duplicate social post.

## Secret handling

The token belongs in GitHub Actions repository secrets when GitHub Actions is the notification runtime:

```text
Repository -> Settings -> Secrets and variables -> Actions -> Repository secrets
TELEGRAM_BOT_TOKEN
```

If a future runtime moves Telegram sending to WordPress, the credential owner should move with it; the profile still keeps only non-secret preference/destination metadata.

## Security rules

- never commit the bot token;
- never paste the bot token into chat;
- never print the token in workflow output;
- rotate/revoke the token if exposed;
- chat ID is non-secret routing metadata but still belongs to user data, not the generic skill;
- disabling notifications does not need to delete the secret; it only prevents use;
- deletion/rotation of the secret is a separate credential-management action.

## References

- `docs/architecture/user-help-telegram-notifications.md`
- `docs/architecture/user-profile-data-contract.md`
- `docs/architecture/capabilities/social-publication-verification.md`
- `docs/architecture/schemas/user-profile.schema.json`
