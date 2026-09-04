# Internal capability: wordpress-connect

Date: 2026-08-31
Status: recovered and adapted implementation contract

## Purpose

`wordpress-connect` is an optional internal capability of the single installable Content / Marketing skill.

It establishes and verifies a reusable connection to one explicitly selected WordPress site through the canonical WordPress companion boundary, **SEO Workflow Bridge**.

It does not prepare, publish or delete a real article.

## Capability contract

```yaml
name: wordpress-connect
purpose: Verify one reusable WordPress connection and the bounded SEO Workflow Bridge abilities required by later WordPress workflows.
availability: optional
feature_gate: wordpress.enabled
mode: mutating

prerequisites:
  - wordpress.enabled = true
  - exact target WordPress site is selected by the user/configuration
  - SEO Workflow Bridge can be installed/configured on that site
  - at least one secure transport can reach the Bridge

mandatory_context:
  - AGENTS.md
  - docs/architecture/persistence-contract.md
  - docs/architecture/capability-contract-template.md
  - docs/architecture/testing-policy.md
  - docs/architecture/wordpress-workflow-authority.md
  - docs/architecture/wordpress-generic-boundary.md
  - docs/architecture/wordpress-connection-transports.md
  - existing wordpress/config/connections/<connection_id>.json when present

reads:
  - non-secret connection profile
  - current transport/runtime capabilities
  - SEO Workflow Bridge site_info/content read responses
  - current connection verification state when persisted

writes:
  - non-secret connection profile/state
  - one temporary Bridge-marked connection-test draft only when functional write verification is explicitly authorized

persists:
  - connection_id
  - expected site URL/identity
  - selected transport and non-secret trust/routing metadata
  - Bridge endpoint identities
  - verified read capabilities
  - verified temporary draft create/read/delete capability state
  - verification timestamps/evidence identifiers
  - blockers when verification is incomplete

external_side_effects:
  - read the selected WordPress site through SEO Workflow Bridge
  - optionally create/read/permanently delete one Bridge-marked temporary test draft after explicit approval
  - use the selected secure transport to invoke bounded Bridge operations

human_approval:
  - selecting/enabling WordPress is durable configuration
  - read-only verification needs no additional publication approval
  - first temporary draft functional write test requires explicit approval
  - no article publication permission is granted by this capability

validation:
  - returned site identity exactly matches the configured target
  - Bridge authentication/trust checks succeed
  - content read succeeds when required
  - temporary test draft is created only as draft, read back, deleted and deletion verified
  - no real article is created/modified/published
  - no secret is persisted

completion_conditions:
  - durable non-secret profile exists
  - exact site identity is verified
  - required Bridge read abilities are verified
  - temporary draft create/read/delete has been verified when full connection verification is required
  - temporary artifact cleanup is verified
  - persisted state has been re-read

next_actions:
  - wordpress-prepare-article when an article and final assets are validated
  - reconfiguration when transport/site/Bridge trust materially changes
```

## Bridge-first model

The business-level connection is:

```text
skill
-> wordpress-connect
-> secure transport
-> SEO Workflow Bridge
-> selected WordPress site
```

The transport is replaceable. The Bridge ability contract is the stable WordPress boundary for the current product architecture.

Do not define successful WordPress connection as successful shell access, WP-CLI access, a Python importer run or access to a particular server filesystem.

## Exact target semantics

A connection represents exactly one WordPress site.

Never infer deployment semantics from names such as:

```text
test
staging
preprod
prod
www
```

A hostname containing `test` is not automatically a staging site from the generic capability's perspective.

Site cloning/promotion belongs to pilot/site-specific operations and is outside this capability.

## Canonical Bridge operations

Read verification uses bounded Bridge operations such as:

```text
site_info
content_list
```

Reference/profile onboarding may additionally use:

```text
reference_read
```

Functional connection write verification uses only:

```text
draft_create
draft_read
draft_delete
```

These test draft operations must remain hard-limited by the Bridge to Bridge-created `AI connection test` drafts.

They must never be reused as a back door to create or mutate production articles.

## Verification sequence

Preferred sequence:

```text
load/resume connection profile
-> verify available transport
-> site_info
-> exact site identity check
-> content_list/read verification
-> persist read_verified
-> explicit human approval for functional write test when needed
-> enable only Connection-test writes
-> draft_create
-> draft_read
-> draft_delete
-> verify deletion
-> disable Connection-test writes when no longer needed
-> persist full_connection_verified
```

Follow `docs/architecture/testing-policy.md`: do not create a temporary draft when read-only checks are sufficient for the current objective.

## Transport neutrality

Transport selection is defined in `docs/architecture/wordpress-connection-transports.md`.

The current pilot uses:

```text
github_actions_oidc_relay
```

through `.github/workflows/wordpress-relay.yml` and SEO Workflow Bridge.

This is an implementation choice, not a universal dependency of the capability contract.

A future transport may invoke the same bounded Bridge operations directly through another secure authenticated channel without changing the business contract.

## Secret handling

Never persist:

- WordPress passwords;
- Application Passwords;
- access/refresh tokens;
- authorization headers;
- session cookies;
- private keys;
- shared relay secrets.

Connection profiles may persist non-secret routing/trust identifiers such as endpoint URLs, audience, repository numeric IDs and workflow refs.

## Resumability

Connection onboarding is a state machine.

A later session must be able to resume from durable state and continue from the first incomplete checkpoint instead of repeating successful setup steps.

Material changes to any of the following invalidate relevant verification and require re-checking:

- target site URL/identity;
- Bridge installation/version when compatibility changes;
- trust policy;
- transport;
- repository/workflow identity;
- authentication mechanism;
- WordPress permissions required by later workflows.

## Separation from article preparation/publication

`wordpress-connect` must never:

- create the real SEO article;
- upload its production media;
- apply its SEO metadata;
- build its Divi/Gutenberg/other presentation;
- publish or schedule it.

Those responsibilities belong respectively to `wordpress-prepare-article` and `wordpress-publish-article`.
