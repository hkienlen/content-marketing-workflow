# User help - Facebook Page publication onboarding

Date: 2026-09-04
Status: current user-help contract - complete flow live validated

## Purpose

Detailed guided procedure for enabling automated publication to one Facebook **Page**, during initial onboarding or later activation.

The procedure is resumable: read the active user profile and continue from the last verified milestone instead of repeating completed Meta setup.

A personal/professional Facebook profile is not an API publication target for this adapter.

Concrete application/configuration/Page IDs, names and expiry dates are user/project data. Resolve them from `user-data/profile.json`; do not hard-code them in the skill help.

## Secret rule

Never ask the user to paste into chat or GitHub:

```text
User Access Token
Page Access Token
App Secret
client token
```

Once a token exists, never request an uncropped screenshot containing its value. Ask for text metadata only, or a crop where the raw token is fully absent/masked.

If a raw token is exposed, reject it for production and rotate the credential chain before continuing.

## 1. Meta for Developers registration

If needed:

```text
Meta for Developers
-> Démarrer
-> verify the personal Facebook account that administers the target Page
-> Continuer
-> confirm primary email
-> developer/marketing emails: optional
-> About you: recommend Développeur when appropriate
-> Terminer l'inscription
```

Skip if already registered.

## 2. Create the Meta app

Validated UI:

```text
Mes applications
-> Créer une app
-> if prompted: Créer une application
-> Détails de l'application
```

Choose a clear application name and persist it/its App ID to the user's Facebook connection metadata.

Validated use case:

```text
Cas d'utilisation
-> Gestion du contenu
-> Tout gérer sur votre Page
```

Do not add Threads, Instagram, Live Video or oEmbed for the Page-only adapter.

If no relevant Business Portfolio exists and Meta permits continuation, it is acceptable to choose the no-portfolio path. Do not create a portfolio merely to advance onboarding.

Do not click `Publier` or `Devenez Fournisseur de technologies` merely to complete a simple own-Page setup.

## 3. Configure minimum Page permissions

Open:

```text
Cas d'utilisation
-> Personnaliser
-> Gérer des Pages
-> Autorisations et fonctionnalités
```

Require:

```text
pages_show_list
pages_read_engagement
pages_manage_posts
```

All three should be ready for test. Meta may also show `business_management` or `public_profile`; do not manually add unrelated capabilities merely because they are visible.

## 4. Meta test screen safety

Do not create a real Facebook post merely to satisfy Meta's test counter for `pages_manage_posts`. A mutating test is a publication and follows the publication gate.

## 5. Facebook Login for Business configuration

If Graph API Explorer reports no configuration available when asking for a User Access Token:

```text
Facebook Login for Business
-> Configurations
-> Créer la configuration
```

Validated choices:

```text
Name: <user/profile configuration name>
Login variant: General
Token type: User Access Token
Permissions:
  - pages_show_list
  - pages_read_engagement
  - pages_manage_posts
```

Persist the non-secret configuration ID/name in the user profile. Do not select `business_management` manually.

Once this configuration exists, token expiration/rotation does not require recreating it.

## 6. Generate bootstrap User Access Token

In Graph API Explorer:

```text
Application Meta: <user profile app>
Configuration: <user profile login configuration>
Type: User Access Token
-> Generate Access Token
```

During Facebook consent:

```text
verify the correct administrator account
-> choose current Pages only
-> select exactly the target Page
-> review access
-> Enregistrer / Continuer
```

Do not choose all current and future Pages for a single-Page connection unless the user's intended configuration explicitly requires that scope.

## 7. Verify exact Page identity and task access

With the fresh User Access Token run read-only:

```text
GET /me/accounts?fields=id,name,tasks
```

Require:

```text
id == <user profile facebook.remote_id>
name == intended Page
CREATE_CONTENT present in tasks
```

If the API returns a newly verified canonical Page ID, persist that user-specific value to the profile and supersede obsolete identifiers in user/project state rather than editing this help contract.

## 8. Inspect bootstrap token lifetime

Use Meta's token information/debugger view and retain only non-secret metadata:

```text
App ID
User ID
Valid
Expiration
Data Access expiration
Scopes
Granular Page scopes
Graph domain
```

The bootstrap User token may expire within hours and is not the WordPress credential.

## 9. Extend to a long-lived User token

Validated Meta-owned path:

```text
Meta for Developers
-> Outils
-> Débogueur de token d'accès
-> paste the short-lived User token only into Meta
-> Déboguer
-> Étendre le token d'accès
```

After extension require `Valide: Vrai`, expected Page scopes, a long lifetime and no token exposure. Persist only non-secret observed expiry metadata in user data.

## 10. Exposed-token recovery - only if needed

If any raw User/Page token is accidentally shared:

```text
Facebook account settings
-> Intégrations professionnelles
-> <the user's Meta application>
-> Supprimer cette app / Supprimer
```

Confirm the exposed credential is invalid in Meta's token debugger, then reuse the existing profile app/configuration and regenerate only the credential chain.

This is recovery, not a mandatory normal onboarding step.

## 11. Obtain the exact Page Access Token

Proceed only from a valid, unexposed long-lived User Access Token.

Run:

```text
GET /me/accounts?fields=id,name,access_token,tasks
```

Inside the object whose exact ID matches the user profile's Facebook Page ID, copy that object's `access_token`. Do not confuse it with the Explorer's top-level User token field.

Validate the Page token in Meta debugger. Require:

```text
Type: Page
ID de la Page: <user profile facebook.remote_id>
Valide: Vrai
expected Page scopes
```

`Expiration: Jamais` is acceptable, but also capture any separate **Data Access Expiration** as non-secret user credential-lifecycle metadata.

A debugger result `Type: User` is not accepted as the final Page credential.

## 12. WordPress handoff and verification

Go to:

```text
WordPress administration
-> Settings
-> SEO Workflow Bridge - Facebook Page
```

Enter:

```text
Enable Facebook Page connection support: checked
Page ID: <user profile facebook.remote_id>
Page Access Token: paste directly from trusted Meta flow
```

Save. After saving, the token field must show only:

```text
Stored - leave blank to keep
```

If credentials are stored but the capability checkbox is not enabled, check the capability, leave the token field blank, save again, then verify.

Click `Verify Facebook Page`. Verification is read-only and must match the exact user profile Page. Persist the non-secret result to user/project connection state.

## 13. Verify scheduler/relay readiness

After Page verification:

```text
verify compatible Bridge build
-> verify Facebook scheduler and relay are on the trusted branch
-> verify dedicated OIDC trust
-> verify media transport readiness
-> verify uncertain-result fail-closed behavior
```

Do not call the real publication endpoint merely as a connection preflight.

## 14. Controlled first live validation

For a newly implemented adapter/installation, select one exact fully approved post and obtain an explicit one-off live-test authorization. Persist user/project live-validation evidence outside the generic skill package.

## 15. Choose future publication behavior

Once the adapter is production-ready, ask once whether scheduled Facebook posts should:

```text
A. require a separate confirmation per post
B. publish automatically after normal post + schedule validation
```

Persist the user's choice under their Facebook connection profile. Option B may materialize exact per-post technical authorization automatically after final validation; it does not weaken exact runtime binding. Immediate `publish_now` remains separate and explicit.

## 16. Credential lifecycle and renewal

`social-connection-health` monitors non-secret Facebook credential metadata and performs daily read-only Page identity probes.

If renewal becomes due, **do not restart this onboarding from step 1**. Resume at the credential chain using the existing app/configuration:

```text
fresh User Access Token
-> /me/accounts exact Page + CREATE_CONTENT
-> Étendre le token d'accès
-> Page Access Token
-> debugger Type Page / exact Page / valid
-> replace directly in WordPress
-> Re-verify Facebook Page
-> update user-profile expiry/data-access metadata
```

If the exact Page ID stays unchanged, credential-only renewal does not require revalidating already approved posts/schedules.

## What the skill should do at each screen

```text
1. explain the current step and why it is needed
2. recommend the minimum safe option
3. ask for a screenshot only when the next choice cannot be safely inferred
4. never request an uncropped token-bearing screenshot
5. persist verified non-secret milestones to user data automatically
6. update generic help/contracts only when reusable Meta behavior/model changes
7. update concrete IDs/names/expiry only in the user profile/project state
8. resume from durable state rather than restarting completed setup
9. fail closed and rotate exposed credentials only when exposure actually occurred
10. honor user-specific publication policy without weakening exact runtime authorization
```

## Resume behavior

If the active user profile says the Facebook Page connection is production-ready, normal future sessions resume at scheduling/publication or connection-health renewal, not developer app creation.

## References

- `docs/architecture/user-profile-data-contract.md`
- `docs/architecture/capabilities/social-connection-health.md`
- `docs/architecture/facebook-page-publication-onboarding.md`
- `docs/architecture/facebook-login-for-business-configuration.md`
- `docs/architecture/facebook-page-token-provisioning-contract.md`
- `docs/architecture/facebook-page-standing-publication-policy.md`
- `docs/architecture/capabilities/social-publish.md`
