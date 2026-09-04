# Internal capability: telegram-publication-notifications

Date: 2026-09-04
Status: current capability contract

## Purpose

Send an optional Telegram report after social publication state has been reconciled, preferably after the strongest post-publication verification available for that platform.

The capability is optional and user-controlled.

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

report the existing configuration and do not recreate the bot. Offer a verification test only when useful.

### Configured but disabled

When `setup_status = verified` and `chat_id` exists but `enabled = false`, re-enable the existing configuration rather than forcing BotFather setup again. If the previous verification is old or the user reports a problem, run the verification workflow again first.

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

Modes:

```text
discover -> verify bot token and list candidate chat IDs after the user has messaged the bot
verify   -> verify exact chat, send a test message, persist enabled=true and non-secret bot/chat metadata
 disable -> set enabled=false while retaining verified non-secret configuration for easy re-enable
```

The workflow reads the repository secret at runtime. GitHub Actions masks the secret; scripts must not print the token or construct log messages containing the Bot API URL with the token.

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
