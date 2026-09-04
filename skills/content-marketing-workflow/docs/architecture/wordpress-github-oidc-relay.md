# WordPress GitHub Actions OIDC relay

Date: 2026-08-31
Status: current pilot transport architecture

## Role

`github_actions_oidc_relay` is the current pilot **transport** used to invoke bounded SEO Workflow Bridge operations.

It is not the WordPress business capability boundary itself.

```text
internal WordPress capability
-> GitHub connector/control plane
-> private relay request
-> GitHub-hosted Actions
-> short-lived GitHub OIDC token
-> SEO Workflow Bridge
-> bounded WordPress operation
```

A future secure transport may replace this relay without changing the semantic contracts of `wordpress-connect`, `wordpress-prepare-article` or `wordpress-publish-article`.

## Why OIDC

The transport avoids a long-lived shared WordPress credential in GitHub.

GitHub Actions obtains a short-lived token from:

```text
https://token.actions.githubusercontent.com
```

SEO Workflow Bridge verifies the token and configured trust policy before executing an operation.

## Current trust checks

The recovered Bridge implementation verifies:

- RS256 signature against GitHub OIDC keys;
- issuer exactly `https://token.actions.githubusercontent.com`;
- exact configured audience;
- token expiration/not-before/issue-time bounds;
- stable numeric repository ID;
- stable numeric repository owner ID when configured;
- repository name when configured;
- `event_name = issues`;
- exact allowed workflow ref;
- private repository visibility when configured.

The relay workflow additionally requires Bridge endpoints to use HTTPS and the same hostname as the configured expected WordPress site.

## Audience convention

Current convention:

```text
wordpress-relay:<connection_id>
```

The audience is non-secret. It scopes a token to one configured WordPress connection and must match the connection profile and Bridge settings exactly.

## Request/response channel

The current internal request envelope is a private GitHub issue whose title starts with:

```text
[wordpress-relay]
```

The body is machine-readable JSON containing bounded routing data such as:

```text
schema_version
request_id
connection_id
operation
issued_at
payload
```

The workflow posts a machine-readable response comment correlated by `request_id` and closes the issue.

Relay issues/comments/workflow runs are implementation plumbing. They are not the normal human editorial review UI.

## Canonical workflow

```text
.github/workflows/wordpress-relay.yml
```

The workflow currently accepts parent operations for:

Connection/profile:

```text
site_info
content_list
reference_read
draft_create
draft_read
draft_delete
```

Preparation/presentation:

```text
prepare_article
article_read
presentation_probe
```

Publication:

```text
publication_capture
publication_preflight
publish_article
published_article_read
```

Publication parent operations require repository `OWNER` issue-author association in the current workflow in addition to the downstream publication gates.

## Preparation entrypoint

The stable workflow currently calls:

```text
scripts/wordpress-relay-prepare-v3.py
```

`v3` is intentionally only a compatibility entrypoint and delegates to:

```text
scripts/wordpress-relay-prepare-v5.py
```

The v5 implementation provides the current presentation-profile adapter mechanism. Keep the profile configuration aligned with the actual v3 entrypoint unless/until an explicit migration replaces this compatibility layer.

Do not expose these implementation version numbers as user-facing capability names.

## Publication entrypoint

Current publication orchestration:

```text
scripts/wordpress-relay-publish-v1.py
```

It enforces parent-side publication rules including:

- capture is read-only;
- immutable candidate is loaded from an exact Git commit/path;
- persisted authorization keys are rejected;
- `publish_article` requires runtime `authorization.decision = publish_now`;
- authorization candidate ID must match exactly;
- read-only preflight/readback must not carry publication authorization.

SEO Workflow Bridge independently enforces the WordPress-side publication permission and exact candidate drift checks.

## Least privilege phases

Bridge permissions are separated:

```text
Read content
Connection-test writes
Article draft preparation
Article publication
```

Normal principle:

- connection-test writes are enabled only for an explicitly approved temporary connection test;
- article draft preparation does not imply publication;
- article publication stays disabled except for an explicitly authorized publication window;
- capability feature flags do not replace runtime human approval.

## Security boundary

The relay must not evolve into remote shell/server execution.

Do not add as normal transport mechanisms:

- arbitrary shell commands;
- arbitrary PHP execution;
- filesystem/database command endpoints;
- a self-hosted runner with broad repository-driven shell access to the WordPress host.

New WordPress behavior must be exposed as a narrowly reviewed Bridge operation/adapter with explicit validation and permissions.

## Failure behavior

A relay failure is a transport failure.

Do not silently fall back to historical direct-import scripts to bypass it.

Persist the truthful checkpoint/blocker and either repair the relay or select another secure transport that preserves the same Bridge/business invariants.
