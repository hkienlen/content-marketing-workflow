# User profile data contract

Date: 2026-09-04
Status: normative architecture contract

## Purpose

The installable Content / Marketing skill owns **models and behavior**, not one user's durable values.

All durable values that describe a user, one of the user's projects/sites, preferences, repositories, storage workspaces, WordPress connections, social accounts, visual sourcing preferences, social publication preferences, credential-expiration metadata, connection-health state or notification preferences belong to **user/project data**.

The skill may know the schema and the algorithms needed to read, validate, migrate and update those values. It must not ship pilot values as defaults or hard-code them into generic behavior.

## Primary invariant

```text
skill package
= generic contracts + schemas + capability logic + reusable companion code

user data
= actual user/site/repository/preferences/connections/IDs/health/expiry/notification/workflow state
```

A new installation must start from an empty/default schema instance and gather or discover values. It must never inherit values from the pilot user.

## Canonical profile model

Generic schema:

```text
docs/architecture/schemas/user-profile.schema.json
```

A separate integration/pilot repository may use a convention such as:

```text
user-data/profile.json
```

The profile is the canonical registry for user/project-level infrastructure and preference metadata that must be quickly recoverable across capabilities.

It may point to richer authoritative user-project documents rather than duplicate them. For example, detailed SEO/editorial rules can remain in user-owned `strategy/**` documents while the profile records the authoritative paths.

## User-data categories

The following are user/project data, never skill defaults:

- profile/project IDs;
- GitHub repository full name, repository ID, owner ID and branch;
- site domain/name/URLs;
- WordPress site/connection IDs and non-secret relay endpoints/audience;
- media-provider choice and Drive/Dropbox workspace/folder IDs;
- target audiences, offers, vocabulary and editorial/SEO preferences;
- **project visual sourcing/fidelity/treatment preferences**, including article/social overrides;
- content-local visual policy overrides and source-image provenance when attached to durable content state;
- social enablement and platform accounts;
- remote social IDs/names/URNs;
- social platform application/configuration IDs when they belong to the user's own integration;
- requested/granted scopes as observed for the user's connection;
- preferred publication timezone/hours;
- standing publication-consent preferences;
- token type and **non-secret** expiration/data-access-expiration metadata;
- last verified connection state and health status;
- renewal history/checkpoints;
- notification-channel enablement/preferences;
- non-secret notification routing such as Telegram `chat_id`, bot username and the configured secret **name/reference**;
- notification setup/verification timestamps and report preferences;
- content/post/article state, publication evidence and post-publication verification evidence.

## Visual preference model

The generic schema supports an optional project-level structure:

```yaml
visual_preferences:
  default:
    visual_source: ai_first|user_images_first|strict_user_images|hybrid_best_fit
    missing_user_images_behavior: ask_before_drafting|allow_ai_generation|continue_without_visuals
    source_fidelity: strict|high|moderate|flexible
    ai_treatment: none|light_correction|natural_enhancement|marketing_enhancement|creative_transformation
    ai_treatment_directive: <string-or-null>
  article: <partial override, optional>
  social: <partial override, optional>
  configured_at: <optional timestamp>
  updated_at: <optional timestamp>
```

The full generic behavior is normative in:

```text
docs/architecture/user-provided-images.md
```

A content-local override belongs to that article/task/post state, not to `visual_preferences`. It must not silently mutate the user's project preference.

Older profile instances that predate `visual_preferences` remain schema-compatible. The resolver may preserve the historical AI-first behavior for compatibility while reporting the preference as not yet explicitly configured. `start` should offer/resume guided configuration rather than silently treating the compatibility path as a newly confirmed preference.

## User-provided source provenance

When a user-provided image becomes durable content input, persist its provenance in the owning content state rather than as a project-global preference, for example:

```yaml
source_type: user_provided
source_provider: google_drive|chat_upload
source_asset_id: <provider identity when available>
source_original_filename: <original filename>
source_sha256: <exact bytes when available>
source_role: use_as_is|enhance|subject_reference|inspiration_reference|composition_input
source_fidelity: strict|high|moderate|flexible
ai_treatment: none|light_correction|natural_enhancement|marketing_enhancement|creative_transformation
ai_treatment_directive: <resolved directive or local override>
```

Provider folder IDs/links used to resume a content-specific `source-user/` intake are also non-secret user/project content state.

## Skill-owned data

The skill may ship:

- JSON/YAML schemas;
- generic capability contracts;
- visual-policy enum/inheritance algorithms;
- default warning thresholds such as J-30/J-14/J-7;
- provider-independent state names;
- provider-specific renewal procedures expressed with placeholders/profile lookups;
- generic notification procedures and a conventional secret name such as `TELEGRAM_BOT_TOKEN`;
- generic tests/fixtures using synthetic identities;
- WordPress Bridge/plugin source;
- scheduler/runtime/notification code.

Generic contracts must use placeholders such as `<page_id>`, `<project_id>`, `<connection_id>` or values loaded from the active profile. They must not depend on one pilot user's IDs, name, domain, account URNs, chat IDs or notification destination.

## Secrets

Raw credentials remain outside the user profile and outside committed GitHub content:

- access tokens;
- refresh tokens;
- app/client secrets;
- passwords;
- OAuth authorization codes;
- cookies/private keys;
- Telegram bot tokens;
- SMTP/API mail credentials.

The profile may retain a non-secret pointer to the credential owner/name, for example:

```yaml
notifications:
  telegram:
    enabled: true
    setup_status: verified
    chat_id: "<numeric-chat-id>"
    bot_username: "<bot-username>"
    secret_name: TELEGRAM_BOT_TOKEN
```

When GitHub Actions sends Telegram reports, the **value** of `TELEGRAM_BOT_TOKEN` belongs in GitHub Actions Repository Secrets. The skill/profile may know the conventional secret name but never the value.

The profile may safely retain non-secret metadata needed to manage social credential lifecycle:

```yaml
kind: oauth_access_token
secret_location: wordpress_seo_workflow_bridge
token_expires_at: <provider-returned-expiry-or-null>
data_access_expires_at: <provider-returned-data-access-expiry-or-null>
last_observed_valid: true
last_observed_at: <observation-timestamp>
```

## Compatibility projections

A pre-existing integration/pilot project may already have useful user-specific operational files such as:

```text
strategy/**
wordpress/config/connections/**
wordpress/presentation/profiles/**
social/**
articles/**
```

These remain **user/project data**, not skill data.

Where the profile mirrors a value required by existing runtime code, one source must be declared canonical and the other a compatibility/derived projection. New capabilities should read the profile first for user/project identity and preferences, then follow its authority pointers for richer data.

Do not create silent divergent copies.

For the visual-source feature, `visual_preferences` is the canonical structured project registry. Rich user-owned image/social visual strategy may add prose/brand rules referenced by the profile, but must not independently carry a conflicting second copy of the same structured sourcing policy.

## Packaging boundary

A distributable skill must not package the pilot instance or pilot content.

Exclude at least:

```text
user-data/**
strategy/**
articles/**
social/**
wordpress/config/**
wordpress/presentation/profiles/**
wordpress/prepare/manifests/**
wordpress/publish/**
work-context/**
project-specific checkpoints/handoffs/live-validation evidence
```

The reusable WordPress Bridge source under `wordpress/bridge-plugin/**` remains skill companion code.

Historical pilot documents remain outside this canonical repository for traceability; the release boundary must never import them into the installable skill.

## Persistence behavior

When a capability discovers or receives a durable user value:

1. classify it as user/project data;
2. write it to the active profile instance or to the richer user-owned authority referenced by the profile;
3. update required compatibility projections atomically when applicable;
4. verify consistency;
5. never modify generic skill contracts merely to save that user's value.

For a durable visual preference change, update `projects.<active_project>.visual_preferences` (or the richer authority only if explicitly designed as canonical) and re-read it. For one content item's visual override/source role, update only that content state.

A real product lesson that changes the **model or behavior** updates the skill contract/schema. The user's concrete value updates only the user profile/project data.

## Notification-preference rule

Notification enablement is a user preference, not an integration-wide default.

For Telegram:

```text
enabled / disabled
chat_id
bot_username
publication report categories
last verification state
```

belong in user/project data.

The Bot API token itself remains only in the credential owner (currently GitHub Actions Repository Secrets). Disabling Telegram reports does not require deleting the secret; it only stops runtime use. Reconfiguration must inspect existing non-secret profile state before forcing the user through bot creation again.

## Multi-project rule

The schema supports multiple projects under one profile. A site-specific preference, visual policy, social connection or notification destination belongs under its project; do not promote it to a global user preference unless the user explicitly says it should apply to all projects.

## References

- `docs/architecture/persistence-contract.md`
- `docs/architecture/capabilities/start.md`
- `docs/architecture/business-model-extensibility.md`
- `docs/architecture/schemas/user-profile.schema.json`
- `docs/architecture/user-provided-images.md`
- `docs/architecture/capabilities/visual-source-resolve.md`
- `docs/architecture/capabilities/social-connection-health.md`
- `docs/architecture/capabilities/social-publication-verification.md`
- `docs/architecture/capabilities/telegram-publication-notifications.md`
- `docs/architecture/skill-package-boundary.md`
