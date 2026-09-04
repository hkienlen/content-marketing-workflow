# Facebook Page token provisioning contract

Date: 2026-09-04
Status: normative current onboarding supplement - production path validated

## Purpose

This contract governs the Meta credential portion of the `facebook_page` adapter.

A token that works interactively is not automatically suitable for unattended publication. The skill distinguishes bootstrap User Access Tokens from the final Page Access Token stored in WordPress.

Concrete App/configuration/Page IDs, names, observed expiration timestamps and connection state are loaded from the active **user profile**. They are not constants in this skill contract.

Credential setup never authorizes or publishes a Facebook post by itself.

## Profile inputs

Resolve from `user-data/profile.json` using `active_project_id`:

```text
social.connections.facebook.meta_app_id
social.connections.facebook.login_configuration_id
social.connections.facebook.login_configuration_name
social.connections.facebook.remote_id
social.connections.facebook.remote_name
social.connections.facebook.scopes
social.connections.facebook.credential.*
```

Generic model: `docs/architecture/schemas/user-profile.schema.json`.

## Production credential chain

```text
existing Facebook Login for Business configuration
-> fresh short-lived User Access Token
-> read-only exact Page/task verification
-> long-lived User Access Token
-> exact Page Access Token
-> Meta debugger validation
-> direct WordPress handoff
-> read-only Bridge Page verification
```

Do not skip lifetime, identity or exposure checks.

## Secret-handling invariant

Never persist or request in chat/GitHub:

```text
short-lived User Access Token
long-lived User Access Token
Page Access Token
App Secret
client token
```

Allowed durable **user-profile** metadata includes:

```text
Meta App ID
Facebook Login for Business configuration ID/name
Graph API version
canonical Page ID/name
permission names
Page task names
token type
valid/invalid status
token expiration metadata
Data Access expiration metadata
last verified timestamps/health
```

Secrets move only between trusted Meta/local/server-side surfaces. The final Page token is pasted directly into WordPress and never rendered back in clear text.

## Screenshot safety

Once any raw token exists, do not request an uncropped screenshot displaying the token field.

If a raw token appears in chat, screenshot, GitHub or logs:

```text
treat as exposed
-> reject for production
-> invalidate/rotate
-> resume from the last safe non-secret milestone
```

Never persist the exposed raw value while documenting the incident.

## Meta configuration

The user profile supplies the actual Meta app and Facebook Login for Business configuration. The validated generic setup uses:

```text
Page content-management use case
Facebook Login for Business
Login variant: General
Token type: User Access Token
Asset scope: current Pages only
only the intended Page selected
```

Required publication permissions:

```text
pages_show_list
pages_read_engagement
pages_manage_posts
```

`public_profile` may appear as a standard Meta scope; it is not an extra publication capability implemented by the Bridge.

## Canonical Page identity gate

With a fresh User token, run read-only:

```text
GET /me/accounts?fields=id,name,tasks
```

Require:

```text
id == <profile facebook.remote_id>
name corresponds to the intended Page
CREATE_CONTENT task present
```

Broader administrator tasks do not widen the app's requested permission set.

If Meta exposes a different Page identifier than an older user-facing identifier, persist the newly verified Graph API ID in the **user profile** and mark the older value superseded in user/project history. Do not encode either identifier in the generic contract.

## Bootstrap User token gate

Graph API Explorer generates the bootstrap User token for the profile-selected configuration.

Require only non-secret metadata:

```text
valid = true
required scopes present
Graph domain = Facebook
expiration known
```

A short-lived bootstrap User token is not the WordPress credential.

If it expires, do not recreate the Meta app/configuration. Generate a new User token and repeat credential-sensitive identity/task checks.

## Long-lived User token

Validated Meta UI:

```text
Meta for Developers
-> Outils
-> Débogueur de token d'accès
-> paste short-lived User token into Meta only
-> Déboguer
-> Étendre le token d'accès
```

Exact observed French action:

```text
Étendre le token d'accès
```

After extension require:

```text
Valide: Vrai
required Page scopes present
long lifetime shown
raw value unexposed
```

Treat the debugger's current expiry as authoritative. Persist its non-secret expiration metadata in the user profile when it is operationally relevant; never hard-code a user's expiry date in this contract.

The App Secret, if a server-side exchange is ever needed, must never be pasted into chat/GitHub or used in untrusted client-side code.

## Exposed-token rotation gate - recovery only

This is a recovery path, not a normal onboarding step.

Any exposed raw token fails closed even if Meta reports it valid.

Validated recovery pattern:

```text
Facebook settings
-> Intégrations professionnelles
-> <profile Meta application>
-> Supprimer
```

Then prove the exposed token invalid in Meta debugger and resume using the **existing profile app/configuration**:

```text
regenerate User token
-> reverify exact profile Page + CREATE_CONTENT
-> extend again
-> continue only with an unexposed credential chain
```

Do not restart completed developer registration/app/permission setup unless Meta actually removed those durable objects.

## Page Access Token acquisition

Proceed only from a valid, unexposed long-lived User token.

Run:

```text
GET /me/accounts?fields=id,name,access_token,tasks
```

Select only the object whose exact ID equals the active profile's Facebook `remote_id`.

The object's `access_token` is the Page token candidate. Do not confuse it with Graph API Explorer's top-level User token field.

The Page token raw value is secret and must never be pasted into chat/GitHub.

## Final Page-token validation gate

Validate the Page token in Meta's token debugger and require:

```text
Type: Page
ID de la Page: <profile facebook.remote_id>
Valide: Vrai
correct Meta app context
expected Page scopes
raw token unexposed
```

`Expiration: Jamais` / `Never` is acceptable for the Page token but does **not** erase a separate Data Access Expiration when Meta exposes one.

A result `Type: User` is not accepted as the final Page credential.

Persist only non-secret observations to the active user profile, for example:

```yaml
credential:
  kind: page_access_token
  secret_location: wordpress_seo_workflow_bridge
  token_expires_at: null
  data_access_expires_at: <observed timestamp or null>
  last_observed_valid: true
  last_observed_at: <timestamp>
```

## WordPress handoff gate

Only the validated, unexposed Page token belongs in the Bridge:

```text
WordPress administration
-> Settings
-> SEO Workflow Bridge - Facebook Page
-> Enable Facebook Page connection support
-> Page ID: <profile facebook.remote_id>
-> Page Access Token: paste directly from trusted Meta flow
-> Save Facebook Page settings
```

After saving, the token input must no longer display the raw value. Current UI uses:

```text
Stored - leave blank to keep
```

Then run `Verify Facebook Page`. The action is read-only and must return exact `id,name` matching the profile target. Store only verification metadata in user/project data.

No post is published by credential installation or Page verification.

## Credential lifecycle and renewal

A Page token marked `Never` can still have a Data Access expiration or be invalidated by Meta/account/configuration changes.

`social-connection-health` therefore uses the active user profile's non-secret credential metadata plus a daily read-only Bridge identity probe.

If renewal is due, resume only the credential-sensitive path from the existing profile Meta app/configuration. After replacement, re-verify the same Page ID in WordPress and update the profile metadata.

Credential-only renewal does not invalidate approved content/schedules/authorizations when the exact remote Page ID remains unchanged.

See `docs/architecture/capabilities/social-connection-health.md`.

## Production readiness after credential handoff

A valid Page token is necessary but not sufficient. Also require:

```text
compatible Bridge installed
Page capability enabled
Page read-only verified
scheduler/relay active
OIDC trust exact
media delivery verified
controlled live scheduler validation completed for that installation
```

Installation-specific live evidence belongs to user/project checkpoints/state and is excluded from the generic skill package.

## Fail-closed rules

Do not mark Facebook publication ready when any of these is true:

```text
bootstrap/source token missing, expired or invalid
required scope missing
profile Page absent from /me/accounts
CREATE_CONTENT absent
credential exposed
final token Type != Page
final Page ID mismatch
Page credential invalid
WordPress Page verification mismatch
scheduler/relay readiness not verified
```

## Publication policy separation

```text
valid connected/verified Facebook Page credential
!=
exact runtime authorization
```

A user-specific standing scheduled-publication policy, if selected, belongs in the active user profile. It may allow automatic creation of exact authorization records after normal content/schedule validation; it never turns the Page token into blanket permission.

## References

- `docs/architecture/user-profile-data-contract.md`
- `docs/architecture/schemas/user-profile.schema.json`
- `docs/architecture/capabilities/social-connection-health.md`
- `docs/architecture/facebook-page-publication-onboarding.md`
- `docs/architecture/facebook-login-for-business-configuration.md`
- `docs/architecture/user-help-facebook-page-onboarding.md`
- `docs/architecture/facebook-page-standing-publication-policy.md`
- `docs/architecture/capabilities/social-publish.md`
- `docs/architecture/facebook-page-scheduled-publication-bridge-0.9.0.md`
