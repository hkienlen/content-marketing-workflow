# User help - Telegram publication notifications

Date: 2026-09-04
Status: current guided onboarding/reconfiguration help

## Purpose

Guide a user through enabling, disabling or reconfiguring optional Telegram publication reports without ever exposing the bot token in chat or repository content.

## What the user gets

When enabled, the publication relay sends a short report after durable publication state is known:

```text
Facebook -> published + remote_verified when read-back succeeds
LinkedIn -> provider_acknowledged with explicit note that direct read-back is unavailable with current access
```

Failures/uncertain results can also be reported when those user preferences remain enabled.

## Before configuring anything

The skill must first inspect the active user profile at:

```text
projects.<active_project>.notifications.telegram
```

Interpret it as follows:

```text
enabled=true + setup_status=verified + chat_id present
-> already active; do not recreate the bot

setup_status=verified + chat_id present + enabled=false
-> configuration already exists; re-enable it rather than starting over

setup_status=not_configured or chat_id missing
-> run initial setup below
```

The skill cannot infer that a GitHub secret still exists merely from profile metadata. If there is doubt, use the verification workflow before declaring the configuration healthy.

## Initial setup - exact procedure

### 1. Create a Telegram bot with BotFather

On Telegram:

1. Search for the official **BotFather** account: `@BotFather`.
2. Open the conversation.
3. Send:

```text
/newbot
```

4. BotFather asks for a display name. Choose any useful name, for example `Social Publisher Notifications`.
5. BotFather asks for a bot username. Telegram bot usernames normally end in `bot`, for example `my_social_reports_bot`.
6. BotFather creates the bot and returns an **HTTP API token**.

Treat that token like a password.

Do **not** paste it into ChatGPT, an issue, a Markdown file, a commit, a workflow input or the user profile.

### 2. Store the token as a GitHub Actions repository secret

In the repository used by the active project:

```text
Settings
-> Secrets and variables
-> Actions
-> Repository secrets
-> New repository secret
```

Create exactly:

```text
Name: TELEGRAM_BOT_TOKEN
Secret: <token returned by BotFather>
```

Save it.

The secret value stays in GitHub's secret store. The user profile records only the conventional secret name, never the token value.

### 3. Start a conversation with the new bot

In Telegram:

1. Open the bot using the link/user name supplied by BotFather.
2. Press **Start** or send:

```text
/start
```

Telegram must have at least one update involving the desired chat before the discovery workflow can find it.

### 4. Discover the chat ID safely

In GitHub:

```text
Actions
-> Telegram notification setup
-> Run workflow
```

Choose:

```text
mode: discover
chat_id: leave empty
branch: main
```

Run the workflow.

The workflow:

- reads `TELEGRAM_BOT_TOKEN` without printing it;
- calls Telegram `getMe` to verify the bot;
- calls `getUpdates`;
- lists candidate chat IDs in the workflow summary.

If it reports no candidate chat, return to Telegram, send `/start` (or a normal message) to the bot, then rerun `discover`.

For a private one-to-one bot conversation, choose the candidate with `type=private` that corresponds to the intended user.

The numeric `chat_id` is routing metadata, not an authentication credential. It may be persisted in user/project data.

### 5. Verify the exact chat and enable notifications

Run the same workflow again:

```text
Actions
-> Telegram notification setup
-> Run workflow
```

Choose:

```text
mode: verify
chat_id: <candidate numeric ID selected above>
branch: main
```

The workflow then:

1. verifies the bot with `getMe`;
2. verifies that exact chat with `getChat`;
3. sends one test message to that chat;
4. records non-secret configuration in the active user profile;
5. sets `notifications.telegram.enabled = true` only after the test succeeds.

Expected Telegram test message:

```text
✅ Notifications de publication configurées. Ce message confirme que le bot Telegram peut envoyer les rapports de publication.
```

After success, the profile contains non-secret fields such as:

```yaml
enabled: true
setup_status: verified
chat_id: <numeric id>
bot_username: <bot username>
secret_name: TELEGRAM_BOT_TOKEN
configured_at: <timestamp>
last_verified_at: <timestamp>
```

## Disable later

A user request such as:

```text
Désactive les notifications Telegram
```

must set:

```text
notifications.telegram.enabled = false
```

The existing bot username/chat ID/configuration may be retained so re-enabling does not force BotFather setup again.

The setup workflow also supports:

```text
mode: disable
```

Deleting the repository secret is optional when merely disabling notifications. It is required only when the user wants to remove/rotate credentials or decommission the bot.

## Re-enable an existing configuration

If the profile still says:

```text
setup_status = verified
chat_id exists
bot_username exists
```

then do not recreate the bot.

If the configuration was recently verified and no credential problem is reported, re-enable the preference. If the secret may have been removed/rotated, run `verify` again with the stored chat ID first.

## Reconfigure bot or chat

Use reconfiguration when:

- the user wants another Telegram conversation/group;
- the bot changed;
- the token was rotated;
- the stored setup no longer verifies.

### Change only the destination chat

1. Send `/start` or a message to the bot from the new destination chat.
2. Run `discover`.
3. Select the new candidate chat ID.
4. Run `verify` with that ID.

The verified workflow replaces the active profile's chat routing metadata.

### Rotate/revoke an exposed bot token

If the bot token was exposed, treat it as compromised.

In Telegram, use the official `@BotFather` management flow for that bot, typically:

```text
/mybots
-> select the bot
-> API Token
-> revoke/regenerate the token
```

BotFather's exact buttons may vary; the objective is to invalidate the old token and obtain a new one.

Then:

1. replace the value of the GitHub repository secret `TELEGRAM_BOT_TOKEN`;
2. do not commit the new token anywhere;
3. run `Telegram notification setup` in `verify` mode with the existing intended `chat_id`;
4. confirm the test message arrives;
5. only then treat the configuration as verified again.

## Publication-report preference

The user profile may independently control which Telegram reports are desired:

```yaml
publication_reports:
  success: true
  failure: true
  uncertain: true
```

These are user preferences and may be changed later without changing the bot token.

## Failure behavior

A Telegram send failure must never:

- retry a Facebook/LinkedIn publication;
- convert a successful publication into a retryable social publication;
- authorize a duplicate post.

The social publication state remains authoritative. Notification failure is recorded/reported separately.

## Onboarding prompt

During initial Content/Marketing skill onboarding, when social publication is enabled, the skill may ask once:

```text
Souhaites-tu recevoir sur Telegram un rapport après les publications sociales ?
```

If no, persist `enabled=false` and continue onboarding.

If yes, inspect the existing profile configuration before deciding whether to re-enable an existing setup or start the exact BotFather/GitHub procedure above.

## References

- `docs/architecture/capabilities/telegram-publication-notifications.md`
- `docs/architecture/capabilities/social-publication-verification.md`
- `docs/architecture/user-profile-data-contract.md`
- `.github/workflows/telegram-notification-setup.yml`
